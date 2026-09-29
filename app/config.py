from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "ComicCraft"
    debug: bool = True
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-3.1-flash-lite"
    gemini_pro_model: str = "gemini-3.1-flash-lite"
    hf_api_key: str = ""
    image_provider: str = "placeholder"
    image_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    image_steps: int = 20
    image_width: int = 512
    image_height: int = 512
    image_guidance_scale: float = 7.5
    max_panels: int = 5

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()

# Backwards compatibility aliases
GEMINI_API_KEY = settings.gemini_api_key
GEMINI_FLASH_MODEL = settings.gemini_flash_model
GEMINI_PRO_MODEL = settings.gemini_pro_model
HF_API_KEY = settings.hf_api_key
SD_MODEL_ID = settings.image_model
IMAGE_WIDTH = settings.image_width
IMAGE_HEIGHT = settings.image_height
NUM_INFERENCE_STEPS = settings.image_steps
