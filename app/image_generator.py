from __future__ import annotations
import hashlib
from pathlib import Path
from threading import Lock
from PIL import Image, ImageDraw, ImageFont

from app.config import BASE_DIR, settings

PANEL_DIR = BASE_DIR / "static" / "panels"
PANEL_DIR.mkdir(parents=True, exist_ok=True)

_PIPELINE = None
_PIPELINE_LOCK = Lock()

def create_filename(prompt: str, panel_number: int) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    return f"panel_{panel_number}_{digest}.png"

def create_placeholder(prompt: str, panel_number: int, output_path: Path):
    width = settings.image_width
    height = settings.image_height
    image = Image.new("RGB", (width, height), color="#1e1e2f")
    draw = ImageDraw.Draw(image)

    try:
        font_large = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw panel border
    draw.rectangle(
        [(16, 16), (width - 16, height - 16)],
        outline="#5b45e8",
        width=4,
    )

    # Draw header badge
    draw.rectangle(
        [(24, 24), (200, 60)],
        fill="#5b45e8",
    )
    draw.text((34, 30), f"PANEL {panel_number}", fill="white", font=font_large)

    # Draw prompt text preview
    prompt_text = prompt[:350] + ("..." if len(prompt) > 350 else "")
    draw.text((34, 80), "Scene Prompt:", fill="#a0aec0", font=font_small)
    draw.multiline_text((34, 110), prompt_text, fill="#e2e8f0", font=font_small, spacing=6)

    draw.text((34, height - 50), "🎨 ComicCraft AI Illustration Placeholder", fill="#718096", font=font_small)

    image.save(output_path, "PNG")

def get_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE

    with _PIPELINE_LOCK:
        if _PIPELINE is not None:
            return _PIPELINE

        import torch
        from diffusers import StableDiffusionPipeline

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        kwargs = {"torch_dtype": dtype, "use_safetensors": True}
        if settings.hf_api_key:
            kwargs["token"] = settings.hf_api_key

        pipeline = StableDiffusionPipeline.from_pretrained(settings.image_model, **kwargs)
        pipeline = pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
        if torch.cuda.is_available():
            try:
                pipeline.enable_attention_slicing()
            except Exception:
                pass
        _PIPELINE = pipeline

    return _PIPELINE

def generate_image(prompt: str, panel_number: int) -> str:
    filename = create_filename(prompt, panel_number)
    output_path = PANEL_DIR / filename

    if settings.image_provider.lower() == "placeholder":
        create_placeholder(prompt, panel_number, output_path)
        return f"/static/panels/{filename}"

    if settings.image_provider.lower() != "diffusers":
        raise RuntimeError("IMAGE_PROVIDER must be 'placeholder' or 'diffusers'.")

    pipeline = get_pipeline()
    result = pipeline(
        prompt=(
            "comic book illustration, high quality, detailed environment, "
            "expressive character, cinematic composition, consistent character design, "
            f"clean line art, {prompt}"
        ),
        negative_prompt=(
            "blurry, low quality, distorted face, bad anatomy, extra fingers, "
            "malformed hands, watermark, logo, text, letters"
        ),
        width=settings.image_width,
        height=settings.image_height,
        num_inference_steps=settings.image_steps,
        guidance_scale=settings.image_guidance_scale,
    )
    result.images[0].save(output_path)
    return f"/static/panels/{filename}"
