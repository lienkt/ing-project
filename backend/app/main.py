from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.campaigns import router
from app.core.config import settings
from app.api.catalog import router as catalog_router

app = FastAPI(title="Banking campaigns comparator", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type"])
app.include_router(router)
app.include_router(catalog_router)

@app.get("/health")
def health():
    return {"status": "ok"}
