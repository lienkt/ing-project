from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.campaigns import DB
from app.core.config import settings
from app.models.collection import SourceImport, UserSource, DeletedSource
from app.schemas.automation import SourceDefinition, build_case_key
from app.scraping import config as scraping_config
from app.schemas.collection import SourceCreate
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from app.models.campaign import Campaign
from app.schemas.collection import (
    CatalogResponse,
    SourceView,
    ScrapeInput,
    BatchResponse,
)
from app.scraping.dispatcher import scraping_support
from app.services import source_catalog, collection

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


def catalog(db):
    try:
        deleted = set(db.scalars(select(DeletedSource.source_id)))
        configured = [
            source for source in source_catalog.load_sources()
            if source.source_id not in deleted
        ]
        return configured + [
            SourceDefinition.model_validate(row.definition)
            for row in db.scalars(select(UserSource))
        ]
    except source_catalog.CatalogError as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/sources", response_model=CatalogResponse)
def sources(db: DB, bank: str | None = None, product_category: str | None = None):
    all_sources = catalog(db)
    records = list(db.scalars(select(SourceImport)))
    campaigns = {
        collection.normalized_url(c.campaign_url): c.id
        for c in db.scalars(select(Campaign))
    }
    views = []
    for source in source_catalog.filter_sources(all_sources, bank, product_category):
        record = next(
            (
                r
                for r in records
                if r.source_id == source.source_id
                or r.source_url == collection.normalized_url(source.url)
            ),
            None,
        )
        existing_id = (
            record.campaign_id
            if record and record.campaign_id
            else campaigns.get(collection.normalized_url(source.url))
        )
        views.append(
            SourceView(
                **source.model_dump(exclude={"campaign_id"}),
                scraping=scraping_support(source),
                auto_labeling_supported=build_case_key(
                    source.bank,
                    source.product_category,
                    source.product_name,
                    source.language,
                )
                in scraping_config.AUTO_LABEL_SUPPORT,
                capture_available=(
                    scraping_support(source)["available"]
                    if scraping_support(source)["supported"]
                    else not source.is_example
                ),
                import_status="Already in Dataset"
                if existing_id and not (record and record.campaign_id)
                else record.status
                if record
                else "Ready",
                campaign_id=existing_id,
                error=record.error if record else None,
                attempted_at=record.attempted_at if record else None,
            )
        )
    return CatalogResponse(
        sources=views,
        banks=source_catalog.banks(all_sources),
        categories=sorted({s.product_category for s in all_sources}),
        data_mode=settings.data_mode,
    )


@router.post("/sources", response_model=SourceDefinition, status_code=201)
def create_source(data: SourceCreate, db: DB):
    collection.validate_project(db, data.product_category)
    from app.models.catalog import Bank
    from app.scraping.public_urls import validate_public_url

    try:
        validate_public_url(str(data.url))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    bank = next(
        (
            b
            for b in db.scalars(select(Bank))
            if b.name.casefold() == data.bank.strip().casefold()
        ),
        None,
    )
    if bank is None:
        raise HTTPException(422, "Choose an existing bank from Settings")
    identity = collection.normalized_url(data.url)
    if any(collection.normalized_url(s.url) == identity for s in catalog(db)):
        raise HTTPException(409, "This URL is already in the source list")
    if not data.product_name.strip():
        raise HTTPException(422, "Product name cannot be blank")
    source = SourceDefinition(
        **data.model_dump(exclude={"bank", "product_name"}),
        bank=bank.name,
        product_name=data.product_name.strip(),
        source_id="custom-" + uuid4().hex,
        page_type="Product Page",
    )
    db.add(
        UserSource(
            source_id=source.source_id,
            source_url=identity,
            definition=source.model_dump(mode="json"),
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This URL is already in the source list") from exc
    return source


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: str, db: DB):
    if not any(source.source_id == source_id for source in catalog(db)):
        raise HTTPException(404, "Source not found")
    custom = db.get(UserSource, source_id)
    if custom:
        db.delete(custom)
    else:
        db.add(DeletedSource(source_id=source_id))
    db.commit()


@router.post("/run", response_model=BatchResponse)
def run(data: ScrapeInput, db: DB):
    return collection.scrape_batch(
        db, catalog(db), data.source_ids, recapture=data.recapture, mode=data.mode
    )


@router.get("/campaigns/{campaign_id}/captures")
def captures(campaign_id: int, db: DB):
    from app.models.collection import PageCapture

    collection.get_campaign(db, campaign_id)
    rows = db.scalars(
        select(PageCapture)
        .where(PageCapture.campaign_id == campaign_id)
        .order_by(PageCapture.created_at.desc())
    )
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "page": row.page,
            "has_screenshot": bool(row.page.get("metadata", {}).get("artifact_id")),
        }
        for row in rows
    ]


@router.get("/captures/{capture_id}/{artifact}")
def capture_artifact(capture_id: str, artifact: str, db: DB):
    from fastapi.responses import FileResponse
    from app.models.collection import PageCapture
    from app.scraping.capture import artifact_path

    row = db.get(PageCapture, capture_id)
    if not row or artifact not in {"screenshot.png", "dom.json"}:
        raise HTTPException(404, "Capture artifact not found")
    artifact_id = row.page.get("metadata", {}).get("artifact_id")
    if not artifact_id:
        raise HTTPException(404, "This capture has no browser artifacts")
    path = artifact_path(artifact_id, artifact)
    if not path.is_file():
        raise HTTPException(404, "Capture file is missing")
    return FileResponse(
        path, media_type="image/png" if artifact.endswith("png") else "application/json"
    )


@router.get("/campaigns/{campaign_id}/content")
def scraped_content(campaign_id: int, db: DB):
    """Latest collected content, including imports predating capture history."""
    campaign = collection.get_campaign(db, campaign_id)
    return campaign.source_import.page if campaign.source_import else None
