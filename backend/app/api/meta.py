from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/runtime")
async def get_runtime_info():
    """
    Return runtime configuration information.
    Used by frontend to display security badge (local vs external AI provider).
    """
    # Determine if provider is local/on-prem
    llm_provider = settings.llm_provider.lower()
    embedding_provider = settings.embedding_provider.lower()
    
    return {
        "llm_provider": llm_provider,
        "embedding_provider": embedding_provider,
    }
