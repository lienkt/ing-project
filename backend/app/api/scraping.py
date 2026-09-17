from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.campaigns import DB
from app.core.config import settings
from app.models.collection import SourceImport
from app.models.campaign import Campaign
from app.schemas.collection import CatalogResponse, SourceView, ScrapeInput, BatchResponse
from app.scraping.engine import get_scraping_engine, ScrapingEngine
from app.feature_extraction.engine import get_feature_extraction_engine, FeatureExtractionEngine
from app.services import source_catalog, collection

router = APIRouter(prefix="/api/scraping", tags=["scraping"])
Scraper = Annotated[ScrapingEngine, Depends(get_scraping_engine)]
Extractor = Annotated[FeatureExtractionEngine, Depends(get_feature_extraction_engine)]


def catalog():
    try:
        return source_catalog.load_sources()
    except source_catalog.CatalogError as exc:
        raise HTTPException(500, str(exc)) from exc


@router.get("/sources", response_model=CatalogResponse)
def sources(db: DB, scraper: Scraper, extractor: Extractor, bank: str | None = None, product_category: str | None = None):
    all_sources = catalog()
    records = list(db.scalars(select(SourceImport)))
    campaigns = {collection.normalized_url(c.campaign_url): c.id for c in db.scalars(select(Campaign))}
    views = []
    for source in source_catalog.filter_sources(all_sources, bank, product_category):
        record = next((r for r in records if r.source_id == source.source_id or r.source_url == collection.normalized_url(source.url)), None)
        existing_id = record.campaign_id if record and record.campaign_id else campaigns.get(collection.normalized_url(source.url))
        views.append(SourceView(**source.model_dump(), import_status="Already in Dataset" if existing_id and not (record and record.campaign_id) else record.status if record else "Ready",
                                campaign_id=existing_id,
                                error=record.error if record else None, attempted_at=record.attempted_at if record else None))
    return CatalogResponse(sources=views, banks=source_catalog.banks(all_sources),
        categories=sorted({s.product_category for s in all_sources}),
        scraping_engine=scraper.name, scraping_is_demo=scraper.is_demo,
        extraction_engine=extractor.name, extraction_is_demo=extractor.is_demo, data_mode=settings.data_mode)


@router.post("/run", response_model=BatchResponse)
def run(data: ScrapeInput, db: DB, scraper: Scraper):
    return collection.scrape_batch(db, catalog(), data.source_ids, scraper)
