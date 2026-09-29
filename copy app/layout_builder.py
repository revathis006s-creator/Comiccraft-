from typing import List, Union
from app.schemas import ComicLayout, PanelOutline, PanelStory

def build_comic_layout(
    stories_or_outline: Union[List[PanelStory], List[dict], List[PanelOutline]],
    image_urls_or_story: Union[List[str], List[dict], List[PanelStory]] = None,
) -> List[ComicLayout]:
    # Case 1: stories list and image_urls list
    if image_urls_or_story and isinstance(image_urls_or_story, list) and len(image_urls_or_story) > 0 and isinstance(image_urls_or_story[0], str):
        stories = stories_or_outline
        image_urls = image_urls_or_story
        return [
            ComicLayout(
                panel_number=getattr(story, "panel_number", story.get("panel_number") if isinstance(story, dict) else i + 1),
                title=getattr(story, "title", story.get("title") if isinstance(story, dict) else f"Panel {i+1}"),
                image_url=image_url,
                scene_description=getattr(story, "scene_description", story.get("scene_description", "") if isinstance(story, dict) else ""),
                caption=getattr(story, "caption", story.get("caption", "") if isinstance(story, dict) else ""),
                narration=getattr(story, "narration", story.get("narration", "") if isinstance(story, dict) else ""),
                dialogue=getattr(story, "dialogue", story.get("dialogue", "") if isinstance(story, dict) else ""),
                image_prompt=getattr(story, "image_prompt", story.get("image_prompt", "") if isinstance(story, dict) else ""),
            )
            for i, (story, image_url) in enumerate(zip(stories, image_urls))
        ]

    # Case 2: outline list (with image_path) and story list
    outline = stories_or_outline
    story_list = image_urls_or_story or []
    story_by_panel = {}
    for p in story_list:
        p_num = getattr(p, "panel_number", p.get("panel_number") if isinstance(p, dict) else 0)
        story_by_panel[int(p_num)] = p

    layout = []
    for i, panel in enumerate(outline):
        p_num = getattr(panel, "panel_number", panel.get("panel_number", i + 1) if isinstance(panel, dict) else i + 1)
        story_panel = story_by_panel.get(int(p_num), {})

        dialogue = getattr(story_panel, "dialogue", story_panel.get("dialogue", "") if isinstance(story_panel, dict) else "")
        if isinstance(dialogue, list):
            dialogue = "\n".join(dialogue)

        image_url = getattr(panel, "image_url", panel.get("image_url", panel.get("image_path", "")) if isinstance(panel, dict) else "")

        layout.append(
            ComicLayout(
                panel_number=int(p_num),
                title=getattr(panel, "title", panel.get("title", f"Panel {p_num}") if isinstance(panel, dict) else f"Panel {p_num}"),
                image_url=image_url,
                scene_description=getattr(panel, "scene_description", panel.get("scene_description", "") if isinstance(panel, dict) else ""),
                caption=getattr(story_panel, "caption", story_panel.get("caption", "") if isinstance(story_panel, dict) else ""),
                narration=getattr(story_panel, "narration", story_panel.get("narration", "") if isinstance(story_panel, dict) else ""),
                dialogue=str(dialogue),
                image_prompt=getattr(panel, "image_prompt", panel.get("image_prompt", "") if isinstance(panel, dict) else ""),
            )
        )
    return layout
