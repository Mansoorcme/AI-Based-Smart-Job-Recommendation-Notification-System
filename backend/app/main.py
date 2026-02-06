"""
Main FastAPI application entry point for AI-Based Smart Job Recommendation & ATS Matching System.
This module initializes the FastAPI app, includes routers, and sets up middleware.
"""

from fastapi import FastAPI # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware # pyright: ignore[reportMissingImports]
from app.core.config import settings
from app.core.logger import setup_logger
from app.api.v1.api import api_router
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]
load_dotenv()

# Setup logger
logger = setup_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Smart Job Recommendation & ATS Matching System",
    version="1.0.0",
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

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn # pyright: ignore[reportMissingImports]
    uvicorn.run(app, host="0.0.0.0", port=8000)
