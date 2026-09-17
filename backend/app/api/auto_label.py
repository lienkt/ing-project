from fastapi import APIRouter
from app.api.campaigns import DB
from app.schemas.automation import ManualRequired
from app.schemas.collection import ProposalRead, ReviewInput
from app.schemas.features import FeatureResponse
from app.services import collection

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}", tags=["automatic suggestions"]
)


@router.post("/auto-label", response_model=ProposalRead | ManualRequired)
def generate(campaign_id: int, db: DB):
    return collection.generate_suggestions(db, campaign_id)


@router.get("/suggestions", response_model=ProposalRead | None)
def suggestions(campaign_id: int, db: DB):
    return collection.get_proposal(db, campaign_id)


@router.post("/suggestions/review", response_model=FeatureResponse)
def review(campaign_id: int, data: ReviewInput, db: DB):
    return collection.review_suggestions(db, campaign_id, data)
