from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/batch")
def ingest_evidence_pack():
    """Import the synthetic multi-source incident evidence pack into MongoDB Atlas."""
    return {"status": "ready", "message": "Ingestion pipeline initialized"}

@router.get("/sources")
def list_ingested_sources():
    """List all ingested sources, counts, and metadata."""
    return {"sources": []}
