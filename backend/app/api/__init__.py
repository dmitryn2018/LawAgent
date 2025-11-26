from fastapi import APIRouter

from app.api import auth, users, documents, chat, templates, due_diligence, clauses, analysis, meta

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(due_diligence.router, prefix="/dd-checks", tags=["Due Diligence"])
api_router.include_router(clauses.router, prefix="/clauses", tags=["Clauses"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(meta.router, prefix="/meta", tags=["Meta"])

