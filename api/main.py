from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers 
from api.routers.rss_feeds import router as rss_feeds_router
from api.routers.rss_articles import router as rss_articles_router

# Environment configuration
API_VERSION = os.getenv("API_VERSION", "0.1.0")
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Forager Stream API",
    description="API for accessing RSS feed metadata and articles",
    version=API_VERSION,
)

# Configure CORS settings to allow frontend access
origins = [
    "http://localhost",
    "http://localhost:3000",
]

# Add production origins if configured
production_origins = os.getenv("ALLOWED_ORIGINS", "")
if production_origins:
    origins.extend(production_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if ENVIRONMENT == "development" else None},
    )

# register rss feeds router
app.include_router(
    rss_feeds_router,
    prefix="/rss-feeds",
    tags=["rss-feeds"],
)
# register rss articles router
app.include_router(
    rss_articles_router,
    prefix="/rss-articles",
    tags=["rss-articles"],
)

@app.get("/", summary="Health check endpoint")
def root() -> dict:
    """
    Root endpoint for basic health check and API info.
    """
    return {
        "message": "Welcome to Forager Stream API",
        "version": API_VERSION,
        "status": "healthy",
        "environment": ENVIRONMENT
    }

# If running via `python -m api.main`, enable Uvicorn server
if __name__ == "__main__":
    import uvicorn  # Imported here to avoid requiring uvicorn when imported as module

    uvicorn.run(
        "api.main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development",
    )
