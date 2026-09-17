"""Workflow orchestration. Algorithms live behind the two engine protocols."""
from datetime import datetime, timezone
import logging
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.models.campaign import Campaign
from app.models.collection import SourceImport, FeatureProposal
from app.scraping.contracts import ScrapedPage
from app.feature_extraction.contracts import FeatureSuggestions
from app.schemas.features import FeatureRead
from app.services.campaigns import get_campaign, validate_project
from app.services.features import locked_campaign, save_features
from app.services.source_catalog import find_source

logger = logging.getLogger(__name__)


def normalized_url(url):
    parts = urlsplit(str(url))
    # Preserve case/path/query semantics; fragments do not identify another page.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def allow_engine(is_demo):
    if is_demo and settings.data_mode != "demo":
        raise HTTPException(409, "Demo engines require DATA_MODE=demo. Switch databases before running this tool.")


def scrape_batch(db, sources, source_ids, engine):
    allow_engine(engine.is_demo)
    results = []
    for source_id in dict.fromkeys(source_ids):
        source = find_source(sources, source_id)
        if source is None:
            results.append(dict(source_id=source_id, status="failed", error="Unknown source ID"))
            continue
        identity = normalized_url(source.url)
        record = db.get(SourceImport, source_id) or db.scalar(select(SourceImport).where(SourceImport.source_url == identity))
        if record and record.campaign_id:
            results.append(dict(source_id=source_id, status="existing", campaign_id=record.campaign_id))
            continue
        # Also protect manually entered campaigns, without attaching fabricated scraped data.
        existing = next((c for c in db.scalars(select(Campaign)) if normalized_url(c.campaign_url) == identity), None)
        if existing:
            results.append(dict(source_id=source_id, status="existing", campaign_id=existing.id))
            continue
        try:
            if source.is_example and not engine.is_demo:
                raise ValueError("Example catalog URLs require a demo engine; replace them with verified sources.")
            page = ScrapedPage.model_validate(engine.scrape(source).model_dump())
            allow_engine(page.is_demo)
            if page.is_demo != engine.is_demo or page.source != source:
                raise ValueError("Scraper returned inconsistent source or demo provenance")
            if not page.success:
                raise ValueError(page.error or "Scraper reported failure")
            validate_project(db, source.product_category)
            campaign = Campaign(bank_name=source.bank, project=source.product_category, campaign_url=str(source.url))
            db.add(campaign)
            db.flush()
            if not record:
                record = SourceImport(source_id=source_id, source_url=identity)
                db.add(record)
            record.campaign_id = campaign.id
            record.status = "Scraped"
            record.engine = engine.name
            record.is_demo = page.is_demo
            record.page = page.model_dump(mode="json")
            record.error = None
            record.attempted_at = datetime.now(timezone.utc)
            campaign_id = campaign.id
            db.commit()
            results.append(dict(source_id=source_id, status="success", campaign_id=campaign_id))
        except IntegrityError:
            db.rollback()
            winner = db.get(SourceImport, source_id) or db.scalar(select(SourceImport).where(SourceImport.source_url == identity))
            if winner and winner.campaign_id:
                results.append(dict(source_id=source_id, status="existing", campaign_id=winner.campaign_id))
            else:
                results.append(dict(source_id=source_id, status="failed", error="Concurrent import conflict; retry this source."))
        except Exception as exc:
            db.rollback()
            logger.exception("Import failed for source %s", source_id)
            message = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
            message = message[:1000] or "Scraping failed"
            # Keep only the latest failure, not a job/event history.
            failed = db.get(SourceImport, source_id) or db.scalar(select(SourceImport).where(SourceImport.source_url == identity))
            if not failed:
                failed = SourceImport(source_id=source_id, source_url=identity)
                db.add(failed)
            if not failed.campaign_id:
                failed.status = "Failed"
                failed.engine = engine.name
                failed.is_demo = engine.is_demo
                failed.error = message
                failed.attempted_at = datetime.now(timezone.utc)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
            results.append(dict(source_id=source_id, status="failed", error=message))
    return {"results": results}


def baseline(campaign):
    return {"url": campaign.campaign_url,
            "features": FeatureRead.model_validate(campaign.features).model_dump(mode="json") if campaign.features else None}


def generate_suggestions(db, campaign_id, engine):
    allow_engine(engine.is_demo)
    campaign = locked_campaign(db, campaign_id)
    imported = campaign.source_import
    if not imported or not imported.page:
        raise HTTPException(409, "This campaign has no scraped page. Import a source before using Auto Label.")
    page = ScrapedPage.model_validate(imported.page)
    if normalized_url(page.source.url) != normalized_url(campaign.campaign_url):
        raise HTTPException(409, "The campaign URL changed since import; scraped content is stale.")
    allow_engine(page.is_demo)
    try:
        suggestions = FeatureSuggestions.model_validate(engine.extract(page).model_dump(exclude_unset=True))
        if suggestions.is_demo != engine.is_demo:
            raise ValueError("Extractor returned inconsistent demo provenance")
    except Exception as exc:
        logger.exception("Extraction failed for campaign %s", campaign_id)
        raise HTTPException(422, "Feature engine failed or returned invalid suggestions. Check server logs.") from exc
    proposal = campaign.proposal
    if proposal is None:
        proposal = FeatureProposal(campaign_id=campaign_id)
        campaign.proposal = proposal
    proposal.token = str(uuid4())
    proposal.engine = engine.name
    proposal.is_demo = suggestions.is_demo or page.is_demo
    proposal.values = suggestions.values.model_dump(mode="json", exclude_unset=True)
    proposal.warnings = suggestions.warnings
    proposal.baseline = baseline(campaign)
    proposal.reviewed = False
    proposal.created_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(proposal)
    return proposal


def get_proposal(db, campaign_id):
    return get_campaign(db, campaign_id).proposal


def review_suggestions(db, campaign_id, data):
    campaign = locked_campaign(db, campaign_id)
    proposal = campaign.proposal
    if not proposal or proposal.reviewed or proposal.token != data.token:
        raise HTTPException(409, "Suggestions changed or were already reviewed. Reload the labeling page.")
    allow_engine(proposal.is_demo)
    if proposal.baseline != baseline(campaign):
        raise HTTPException(409, "Manual labels or the source changed. Generate fresh suggestions before reviewing.")
    proposal.reviewed = True
    from app.models.features import CampaignFeature
    if campaign.features is None:
        campaign.features = CampaignFeature()
    campaign.features.source = "manual_override"
    # An explicit human save, never an automatic completion or silent overwrite.
    result = save_features(db, campaign_id, data.values)
    return result
