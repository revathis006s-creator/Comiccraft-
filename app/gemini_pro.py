import json
import logging
import re
import time
from typing import List, Union
from google import genai
from google.genai import types

from app.config import settings
from app.schemas import PanelOutline, PanelStory, PromptRequest

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
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

def generate_story(
    req_or_outline: Union[PromptRequest, List[Union[PanelOutline, dict]]],
    outlines_or_char: Union[List[Union[PanelOutline, dict]], str] = None,
    tone: str = "",
) -> List[PanelStory]:
    if isinstance(req_or_outline, PromptRequest):
        req = req_or_outline
        raw_outlines = outlines_or_char or []
    else:
        raw_outlines = req_or_outline
        char_name = str(outlines_or_char) if outlines_or_char else "Hero"
        req = PromptRequest(
            story_prompt="Comic story",
            character_name=char_name,
            setting="Comic setting",
            tone=tone or "Adventure",
            art_style="Comic Book",
        )

    validated_outlines: List[PanelOutline] = []
    for item in raw_outlines:
        if isinstance(item, PanelOutline):
            validated_outlines.append(item)
        elif isinstance(item, dict):
            validated_outlines.append(PanelOutline.model_validate(item))

    client = get_client()
    outline_json = json.dumps([p.model_dump() for p in validated_outlines], indent=2, ensure_ascii=False)

    prompt = f"""
Expand this {len(validated_outlines)}-panel comic outline into complete comic narration, captions, and dialogue.

Story Idea: {req.story_prompt}
Main Character: {req.character_name}
Setting: {req.setting}
Tone: {req.tone}
Art Style: {req.art_style}

Outline:
{outline_json}

For each panel provide:
- panel_number (1 to {len(validated_outlines)})
- title (panel title)
- scene_description (short visual description)
- caption (brief atmospheric caption)
- narration (short storytelling narration)
- dialogue (spoken dialogue in format "Character: text")
- image_prompt (detailed image generation prompt)

Return only valid JSON matching the schema.
"""
    # Build list of models to try in order
    candidate_models = []
    if settings.gemini_pro_model:
        candidate_models.append(settings.gemini_pro_model)
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
                    temperature=0.85,
                    response_mime_type="application/json",
                    response_schema=list[PanelStory],
                ),
            )
            if response and response.text:
                break
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
            continue

    if not response or not response.text:
        raise RuntimeError(f"Gemini Pro generation failed: {last_error}")

    raw_text = _clean_json_text(response.text)
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "panels" in data:
            data = data["panels"]
        stories = [PanelStory.model_validate(item) for item in data]
    except Exception as exc:
        raise RuntimeError(f"Failed to parse Gemini story: {exc}. Response was: {raw_text[:200]}") from exc

    if len(stories) != len(validated_outlines):
        raise RuntimeError(f"Expected {len(validated_outlines)} panels but received {len(stories)}.")

    return stories
