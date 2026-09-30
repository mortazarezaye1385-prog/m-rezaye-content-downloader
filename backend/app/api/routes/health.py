from fastapi import APIRouter, Depends

from app.api.deps import get_state
from app.api.state import AppState

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(state: AppState = Depends(get_state)) -> dict:
    try:
        import yt_dlp  # noqa: F401  # type: ignore[import-not-found]

        engine = True
    except ImportError:
        engine = False
    return {
        "status": "ok",
        "retrieval_engine": engine,
        "instagram_api": state.settings.instagram_graph_enabled,
        "active_jobs": state.jobs.active_count(),
    }
