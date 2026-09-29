from __future__ import annotations
import asyncio
import re
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR, settings
from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.schemas import PromptRequest, ComicLayout

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def create_title(prompt: str) -> str:
    words = re.findall(r"[A-Za-z0-9']+", prompt)
    return " ".join(words[:6]).title() if words else "My Comic"

async def generate_complete_comic(request_data: PromptRequest):
    outlines = await asyncio.to_thread(generate_outline, request_data)
    stories = await asyncio.to_thread(generate_story, request_data, outlines)
    image_urls = [
        await asyncio.to_thread(generate_image, panel.image_prompt, panel.panel_number)
        for panel in stories
    ]
    layout = build_comic_layout(stories, image_urls)
    title = create_title(request_data.story_prompt)
    pdf_url = await asyncio.to_thread(save_pdf, layout, title)
    return title, layout, pdf_url

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": settings.app_name, "error": None},
    )

@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )
        title, layout, pdf_url = await generate_complete_comic(data)
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": title,
                "layout": layout,
                "pdf_url": pdf_url,
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": settings.app_name,
                "error": str(exc),
            },
            status_code=400 if "API_KEY" in str(exc) or "validation" in str(exc).lower() else 500,
        )

@router.post("/generate-comic/json")
async def generate_comic_json(data: PromptRequest):
    try:
        title, layout, pdf_url = await generate_complete_comic(data)
        return {
            "success": True,
            "title": title,
            "layout": [item.model_dump() for item in layout],
            "pdf_url": pdf_url,
        }
    except Exception as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

@router.post("/test-image")
async def test_image_post(payload: dict):
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return JSONResponse(status_code=422, content={"error": "prompt is required"})
    try:
        image_url = await asyncio.to_thread(generate_image, prompt, 0)
        return {"success": True, "image_url": image_url}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

@router.get("/test-image")
async def test_image_get(prompt: str = "A brave fox in an enchanted forest"):
    try:
        image_url = await asyncio.to_thread(generate_image, prompt, 0)
        return {"success": True, "image_url": image_url, "prompt": prompt}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})

@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_url: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={"pdf_url": pdf_url},
    )

@router.get("/health")
async def health():
    key_configured = bool(settings.gemini_api_key and settings.gemini_api_key != "YOUR_GEMINI_API_KEY")
    return {
        "status": "ok",
        "application": settings.app_name,
        "image_provider": settings.image_provider,
        "gemini_configured": key_configured,
    }
