from fastapi import FastAPI, Depends, Request
from app.core.auth import authorize
from app.core.permissions import load_policy
from fastapi.middleware.cors import CORSMiddleware
from app.api.campaigns import router
from app.core.config import settings
from app.api.catalog import router as catalog_router
from app.api.features import router as features_router
from app.api.compare import router as compare_router

from app.api.scraping import router as scraping_router
from app.api.auto_label import router as auto_label_router

# Validate the role policy before serving requests.
load_policy()

app = FastAPI(title="Banking campaigns comparator", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(scraping_router, dependencies=[Depends(authorize)])
app.include_router(auto_label_router, dependencies=[Depends(authorize)])
app.include_router(compare_router, dependencies=[Depends(authorize)])
app.include_router(features_router, dependencies=[Depends(authorize)])
app.include_router(router, dependencies=[Depends(authorize)])
app.include_router(catalog_router, dependencies=[Depends(authorize)])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/permissions", dependencies=[Depends(authorize)])
def effective_permissions(request: Request):
    return {"permissions": sorted(request.state.permissions)}
