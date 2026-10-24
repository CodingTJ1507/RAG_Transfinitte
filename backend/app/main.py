from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes_investigate import router as investigate_router
from app.api.routes_ingest import router as ingest_router
from app.api.routes_eval import router as eval_router
from app.core.database import close_database, get_db, vector_index_status


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_database()


app = FastAPI(
    title=settings.APP_NAME,
    description="Evidence-grounded engineering incident investigator powered by MongoDB Vector Search & LangChain",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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

@app.get("/ready", tags=["Health"])
def readiness_check():
    try:
        get_db().command("ping")
        database_ready = True
        database_error = None
    except Exception:
        database_ready = False
        database_error = "MongoDB is unavailable or not configured"
    vector_status = None
    if database_ready:
        vector_status = vector_index_status()
    ready = database_ready and bool(vector_status and vector_status.get("ready"))
    return {
        "status": "ready" if ready else "degraded",
        "database": {"ready": database_ready, "error": database_error},
        "vector_search": vector_status,
        "llm_configured": bool(
            settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here"
        ),
        "dataset_exists": (settings.dataset_path / "metadata" / "source_manifest.json").is_file(),
    }

app.include_router(ingest_router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(investigate_router, prefix="/api/investigate", tags=["Investigation"])
app.include_router(eval_router, prefix="/api/eval", tags=["Evaluation"])
