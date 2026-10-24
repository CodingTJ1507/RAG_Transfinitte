from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes_investigate import router as investigate_router
from app.api.routes_ingest import router as ingest_router
from app.api.routes_eval import router as eval_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Evidence-grounded engineering incident investigator powered by MongoDB Vector Search & LangChain",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }

app.include_router(ingest_router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(investigate_router, prefix="/api/investigate", tags=["Investigation"])
app.include_router(eval_router, prefix="/api/eval", tags=["Evaluation"])
