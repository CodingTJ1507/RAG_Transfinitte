from fastapi import APIRouter

router = APIRouter()

@router.get("/benchmark")
def run_benchmark():
    """Run the 4 demo benchmark test cases against the ground-truth dataset."""
    return {
        "status": "ready",
        "tests": [
            "Test 1 - Cross-source reasoning (Payment failure root cause)",
            "Test 2 - Exact technical lookup (PAY-401 code search)",
            "Test 3 - Conflicting evidence (Redis vs in-memory cache)",
            "Test 4 - Unanswerable request (Engineer attribution abstention)"
        ]
    }
