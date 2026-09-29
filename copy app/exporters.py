from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from fpdf import FPDF

from app.config import BASE_DIR
from app.schemas import ComicLayout

def get_image_path(image_url: str) -> Path:
    parsed = urlparse(image_url)
    relative_path = parsed.path.lstrip("/").replace("/", str(Path("/")))
    if not relative_path.startswith("static"):
        return BASE_DIR / "static" / relative_path
    return BASE_DIR / relative_path

def pdf_text(text: str) -> str:
    if not text:
        return ""
    # Normalize unicode to Latin-1 for standard FPDF fonts
    clean = str(text).replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return clean.encode("latin-1", "replace").decode("latin-1")

def save_pdf(layout: list[ComicLayout | dict], title: str = "ComicCraft Comic") -> str:
    export_dir = BASE_DIR / "static" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(title)).strip("_") or "comic"
    filename = f"{safe_title}_{timestamp}.pdf"
    output_path = export_dir / filename

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    for panel in layout:
        p_num = getattr(panel, "panel_number", panel.get("panel_number", "") if isinstance(panel, dict) else "")
        p_title = getattr(panel, "title", panel.get("title", "") if isinstance(panel, dict) else "")
        image_url = getattr(panel, "image_url", panel.get("image_url", panel.get("image_path", "")) if isinstance(panel, dict) else "")
        scene = getattr(panel, "scene_description", panel.get("scene_description", "") if isinstance(panel, dict) else "")
        caption = getattr(panel, "caption", panel.get("caption", "") if isinstance(panel, dict) else "")
        narration = getattr(panel, "narration", panel.get("narration", "") if isinstance(panel, dict) else "")
        dialogue = getattr(panel, "dialogue", panel.get("dialogue", "") if isinstance(panel, dict) else "")

        pdf.add_page()
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(180, 8, pdf_text(f"Panel {p_num}: {p_title}"))

        curr_y = 28
        if image_url:
            image_path = get_image_path(image_url)
            if image_path.exists():
                pdf.image(str(image_path), x=15, y=curr_y, w=100, h=100)
                curr_y += 105
            else:
                curr_y += 10
        else:
            curr_y += 10

        pdf.set_xy(15, curr_y)

        sections = [
            ("Scene", scene),
            ("Caption", caption),
            ("Narration", narration),
            ("Dialogue", dialogue),
        ]

        for label, content in sections:
            if content:
                pdf.set_x(15)
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(180, 5, pdf_text(label))
                pdf.set_x(15)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(180, 4.5, pdf_text(content))
                pdf.set_y(pdf.get_y() + 2)

    pdf.output(str(output_path))
    return f"/static/exports/{filename}"
