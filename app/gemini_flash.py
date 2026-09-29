import json
import logging
import re
import time
from typing import List, Union
from google import genai
from google.genai import types

from app.config import settings
from app.schemas import PanelOutline, PromptRequest

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
]

def get_client() -> genai.Client:
    key = settings.gemini_api_key.strip() if settings.gemini_api_key else ""
    if not key or key == "YOUR_GEMINI_API_KEY":
        raise RuntimeError(
            "GEMINI_API_KEY is missing or invalid. Please configure a valid Gemini API key in your .env file."
        )
    return genai.Client(api_key=key)

def _clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def generate_outline(
    story_or_request: Union[PromptRequest, str],
    character_name: str = "",
    setting: str = "",
    tone: str = "",
    art_style: str = "",
) -> List[PanelOutline]:
    if isinstance(story_or_request, PromptRequest):
        req = story_or_request
    else:
        req = PromptRequest(
            story_prompt=story_or_request,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

    client = get_client()
    prompt = f"""
Create exactly {settings.max_panels} connected comic panels.

Story idea: {req.story_prompt}
Main character: {req.character_name}
Setting: {req.setting}
Tone: {req.tone}
Art style: {req.art_style}

For each panel, provide:
- panel_number (1 to {settings.max_panels})
- title (short title)
- scene_description (concise visual description of what is happening)
- image_prompt (detailed description for generating the comic artwork without dialogue or speech bubbles)

Return only valid JSON.
"""
    # Build list of models to try in order
    candidate_models = []
    if settings.gemini_flash_model:
        candidate_models.append(settings.gemini_flash_model)
    for m in FALLBACK_MODELS:
        if m not in candidate_models:
            candidate_models.append(m)

    last_error = None
    response = None

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json",
                    response_schema=list[PanelOutline],
                ),
            )
            if response and response.text:
                break
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
            continue

    if not response or not response.text:
        raise RuntimeError(f"Gemini Flash generation failed: {last_error}")

    raw_text = _clean_json_text(response.text)
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "panels" in data:
            data = data["panels"]
        outlines = [PanelOutline.model_validate(item) for item in data]
    except Exception as exc:
        raise RuntimeError(f"Failed to parse Gemini outline: {exc}. Response was: {raw_text[:200]}") from exc

    if len(outlines) != settings.max_panels:
        raise RuntimeError(f"Expected {settings.max_panels} panels but received {len(outlines)}.")

    return outlines
