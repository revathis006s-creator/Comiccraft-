from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.routes import router

STATIC_DIR = BASE_DIR / "static"
(STATIC_DIR / "panels").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "exports").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    description="AI Comic Story Creator using Gemini and Stable Diffusion",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)

@app.get("/health")
async def health():
    key_configured = bool(settings.gemini_api_key and settings.gemini_api_key != "YOUR_GEMINI_API_KEY")
    return {
        "status": "ok",
        "application": settings.app_name,
        "image_provider": settings.image_provider,
        "gemini_configured": key_configured,
    }
