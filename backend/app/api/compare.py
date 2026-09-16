from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.compare import ComparisonRead
from app.services.compare import compare_campaigns

router = APIRouter(prefix="/api/compare", tags=["comparison"])
DB = Annotated[Session, Depends(get_db)]


@router.get("", response_model=ComparisonRead)
def compare(
    db: DB,
    product_category: Annotated[str, Query(min_length=1, max_length=40)],
    campaign_ids: Annotated[list[int] | None, Query()] = None,
    bank_names: Annotated[list[str] | None, Query()] = None,
):
    return compare_campaigns(db, product_category, campaign_ids, bank_names)
