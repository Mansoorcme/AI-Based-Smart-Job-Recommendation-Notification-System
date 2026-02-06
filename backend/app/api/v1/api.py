"""
Main API router that includes all v1 endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.match import router as match_router
from app.api.v1.resume import router as resume_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.role import router as role_router

# Create the main FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(match_router, prefix="/match", tags=["match"])
app.include_router(resume_router, prefix="/resume", tags=["resume"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
app.include_router(role_router, prefix="/role", tags=["role"])
