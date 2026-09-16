from fastapi import APIRouter
from app.api.campaigns import DB
from app.schemas.features import CompleteInput, FeatureInput, FeatureResponse
from app.services import features

router = APIRouter(prefix="/api/campaigns/{campaign_id}/features", tags=["campaign features"])

@router.get("", response_model=FeatureResponse)
def get(campaign_id: int, db: DB):
    return features.feature_response(db, campaign_id)

@router.put("", response_model=FeatureResponse)
def save(campaign_id: int, data: FeatureInput, db: DB):
    return features.save_features(db, campaign_id, data)

@router.post("/complete", response_model=FeatureResponse)
def complete(campaign_id: int, data: CompleteInput, db: DB):
    return features.complete_features(db, campaign_id, data.confirm_incomplete)
