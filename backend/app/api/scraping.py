from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.campaigns import DB
from app.core.config import settings
from app.models.collection import SourceImport
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


def catalog():
    try:
        return source_catalog.load_sources()
    except source_catalog.CatalogError as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/sources", response_model=CatalogResponse)
def sources(db: DB, bank: str | None = None, product_category: str | None = None):
    all_sources = catalog()
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


@router.post("/run", response_model=BatchResponse)
def run(data: ScrapeInput, db: DB):
    return collection.scrape_batch(
        db, catalog(), data.source_ids, recapture=data.recapture
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
