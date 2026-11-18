import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import router as api_router
from app.utils.logger import logger

app = FastAPI(
    title="NexusRAG API",
    description="A locally runnable, reliable Retrieval-Augmented Generation platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Include API Router
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = _STATIC_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(f.read())
        except Exception:
            pass

    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Locally runnable Enterprise RAG Platform",
        "docs": "/docs",
        "health": "/api/health",
        "status": "/api/status",
        "ui": "/"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )
