from typing import List
from pydantic import BaseModel, Field, field_validator

class PromptRequest(BaseModel):
    story_prompt: str = Field(..., min_length=3, max_length=2000)
    character_name: str = Field(..., min_length=1, max_length=100)
    setting: str = Field(..., min_length=1, max_length=200)
    tone: str = Field(..., min_length=1, max_length=100)
    art_style: str = Field(..., min_length=1, max_length=100)

    @field_validator("*")
    @classmethod
    def clean_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty.")
        return value

class PanelOutline(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str

class PanelStory(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    caption: str = ""
    narration: str = ""
    dialogue: str = ""
    image_prompt: str

class ComicLayout(BaseModel):
    panel_number: int
    title: str
    image_url: str
    scene_description: str
    caption: str = ""
    narration: str = ""
    dialogue: str = ""
    image_prompt: str

class ComicResponse(BaseModel):
    title: str
    layout: List[ComicLayout]
    pdf_url: str
