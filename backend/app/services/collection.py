"""Imports and review persistence. Each config dispatches its supported cases."""

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
from app.schemas.automation import ManualRequired, campaign_information, stored_page
from app.scraping.dispatcher import scrape_campaign, scraping_support
from app.auto_labeling.dispatcher import auto_label_campaign
from app.schemas.features import FeatureRead
from app.services.campaigns import get_campaign, validate_project
from app.services.features import locked_campaign, save_features
from app.services.source_catalog import find_source

logger = logging.getLogger(__name__)


def normalized_url(url):
    parts = urlsplit(str(url))
    # Preserve case/path/query semantics; fragments do not identify another page.
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, "")
    )


def allow_engine(is_demo):
    if is_demo and settings.data_mode != "demo":
        raise HTTPException(
            409,
            "Demo automation requires DATA_MODE=demo. Switch databases before running this tool.",
        )


def scrape_batch(db, sources, source_ids):
    results = []
    for source_id in dict.fromkeys(source_ids):
        source = find_source(sources, source_id)
        if source is None:
            results.append(
                dict(source_id=source_id, status="failed", error="Unknown source ID")
            )
            continue
        support = scraping_support(source)
        if not support["supported"]:
            results.append(
                dict(
                    source_id=source_id,
                    status="manual_required",
                    supported=False,
                    message="Automatic scraping is not available. Manual scraping required.",
                )
            )
            continue
        identity = normalized_url(source.url)
        record = db.get(SourceImport, source_id) or db.scalar(
            select(SourceImport).where(SourceImport.source_url == identity)
        )
        if record and record.campaign_id:
            results.append(
                dict(
                    source_id=source_id,
                    status="existing",
                    supported=True,
                    campaign_id=record.campaign_id,
                )
            )
            continue
        # Also protect manually entered campaigns, without attaching fabricated scraped data.
        existing = next(
            (
                c
                for c in db.scalars(select(Campaign))
                if normalized_url(c.campaign_url) == identity
            ),
            None,
        )
        if existing:
            results.append(
                dict(
                    source_id=source_id,
                    status="existing",
                    supported=True,
                    campaign_id=existing.id,
                )
            )
            continue
        try:
            page = scrape_campaign(source)
            if isinstance(page, ManualRequired):
                results.append(dict(source_id=source_id, **page.model_dump()))
                continue
            allow_engine(page.is_demo)
            if not page.success:
                raise ValueError(page.error or "Scraper reported failure")
            validate_project(db, source.product_category)
            campaign = Campaign(
                bank_name=source.bank,
                project=source.product_category,
                campaign_url=str(source.url),
            )
            db.add(campaign)
            db.flush()
            if not record:
                record = SourceImport(source_id=source_id, source_url=identity)
                db.add(record)
            record.campaign_id = campaign.id
            record.status = "Scraped"
            record.engine = "demo" if page.is_demo else "configured"
            record.is_demo = page.is_demo
            record.page = page.model_dump(mode="json")
            record.error = None
            record.attempted_at = datetime.now(timezone.utc)
            campaign_id = campaign.id
            db.commit()
            results.append(
                dict(
                    source_id=source_id,
                    status="success",
                    supported=True,
                    campaign_id=campaign_id,
                )
            )
        except IntegrityError:
            db.rollback()
            winner = db.get(SourceImport, source_id) or db.scalar(
                select(SourceImport).where(SourceImport.source_url == identity)
            )
            if winner and winner.campaign_id:
                results.append(
                    dict(
                        source_id=source_id,
                        status="existing",
                        supported=True,
                        campaign_id=winner.campaign_id,
                    )
                )
            else:
                results.append(
                    dict(
                        source_id=source_id,
                        status="failed",
                        supported=True,
                        error="Concurrent import conflict; retry this source.",
                    )
                )
        except Exception as exc:
            db.rollback()
            logger.exception("Import failed for source %s", source_id)
            message = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
            message = message[:1000] or "Scraping failed"
            # Keep only the latest failure, not a job/event history.
            failed = db.get(SourceImport, source_id) or db.scalar(
                select(SourceImport).where(SourceImport.source_url == identity)
            )
            if not failed:
                failed = SourceImport(source_id=source_id, source_url=identity)
                db.add(failed)
            if not failed.campaign_id:
                failed.status = "Failed"
                failed.engine = "demo" if support["is_demo"] else "configured"
                failed.is_demo = support["is_demo"]
                failed.error = message
                failed.attempted_at = datetime.now(timezone.utc)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
            results.append(
                dict(
                    source_id=source_id, status="failed", supported=True, error=message
                )
            )
    return {"results": results}


def baseline(campaign):
    return {
        "url": campaign.campaign_url,
        "features": FeatureRead.model_validate(campaign.features).model_dump(
            mode="json"
        )
        if campaign.features
        else None,
    }


def generate_suggestions(db, campaign_id):
    campaign = locked_campaign(db, campaign_id)
    page = stored_page(campaign)
    try:
        suggestions = auto_label_campaign(campaign_information(campaign), page)
        if isinstance(suggestions, ManualRequired):
            return suggestions
        allow_engine(suggestions.is_demo or page.is_demo)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Auto labeling failed for campaign %s", campaign_id)
        raise HTTPException(
            422,
            "Automatic labeling failed or returned invalid suggestions. Check server logs.",
        ) from exc
    proposal = campaign.proposal
    if proposal is None:
        proposal = FeatureProposal(campaign_id=campaign_id)
        campaign.proposal = proposal
    proposal.token = str(uuid4())
    proposal.engine = "demo" if suggestions.is_demo else "configured"
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
        raise HTTPException(
            409,
            "Suggestions changed or were already reviewed. Reload the labeling page.",
        )
    allow_engine(proposal.is_demo)
    if proposal.baseline != baseline(campaign):
        raise HTTPException(
            409,
            "Manual labels or the source changed. Generate fresh suggestions before reviewing.",
        )
    proposal.reviewed = True
    from app.models.features import CampaignFeature

    if campaign.features is None:
        campaign.features = CampaignFeature()
    campaign.features.source = "manual_override"
    # An explicit human save, never an automatic completion or silent overwrite.
    result = save_features(db, campaign_id, data.values)
    return result
