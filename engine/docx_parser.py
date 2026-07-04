import json, os, re
from pathlib import Path
import docx
from engine.textbook_optimizer import optimize_textbook_content

DATA_DIR = Path(__file__).parent.parent / "data" / "textbooks_content"
IMG_DIR = Path(__file__).parent.parent / "static" / "textbook_images"
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百千万0-9]+[章节篇讲单元编].{0,40}$")
SECTION_RE = re.compile(r"^[（(]?[一二三四五六七八九十百0-9]+[)）][\s\S]{0,40}$")
SUBSECTION_RE = re.compile(r"^[一二三四五六七八九十百0-9]+[、.．][\s\S]{0,40}$")


def infer_heading_level(text, style_name="Normal", bold=False):
    text = (text or "").strip()
    style_name = style_name or "Normal"
    if not text:
        return 0
    if "Heading 1" in style_name:
        return 1
    if "Heading 2" in style_name:
        return 2
    if "Heading 3" in style_name:
        return 3
    if CHAPTER_RE.match(text):
        return 1
    if SECTION_RE.match(text):
        return 2
    if SUBSECTION_RE.match(text):
        return 3
    if bold and len(text) <= 26 and not any(mark in text for mark in "。；;？！?!"):
        return 2
    return 0

def parse_docx(filepath, book_id):
    doc = docx.Document(filepath)
    structure = {"id": book_id, "title": os.path.basename(filepath).replace(".docx",""), "chapters": []}
    current_chapter = None
    current_section = None
    title_candidates = []

    for para in doc.paragraphs:
        text = para.text.strip()
        style_name = para.style.name if para.style else "Normal"
        is_bold = any(r.bold for r in para.runs if r.text.strip())
        if not text and "Heading" not in style_name:
            continue
        entry = {"text": text, "style": style_name, "level": 0,
                 "bold": is_bold,
                 "italic": any(r.italic for r in para.runs if r.text.strip())}
        inferred_level = infer_heading_level(text, style_name, is_bold)

        if not structure["title"] or ".docx" in structure["title"]:
            if text and len(text) <= 40:
                title_candidates.append(text)
        if inferred_level == 1:
            entry["level"] = 1
            ch = {"heading": text, "level": 1, "sections": []}
            structure["chapters"].append(ch)
            current_chapter = ch
            current_section = None
            if title_candidates:
                structure["title"] = title_candidates[0]
            elif not structure["title"] or ".docx" in structure["title"]:
                structure["title"] = text
        elif inferred_level == 2:
            entry["level"] = 2
            sec = {"heading": text, "level": 2, "content": []}
            if current_chapter:
                current_chapter["sections"].append(sec)
            else:
                ch = {"heading": "", "level": 1, "sections": [sec]}
                structure["chapters"].append(ch)
                current_chapter = ch
            current_section = sec
        elif inferred_level >= 3:
            entry["level"] = 3
            sec = {"heading": text, "level": 3, "content": []}
            if current_chapter:
                current_chapter["sections"].append(sec)
            else:
                ch = {"heading": "", "level": 1, "sections": [sec]}
                structure["chapters"].append(ch)
                current_chapter = ch
            current_section = sec
        else:
            if current_section:
                current_section["content"].append(entry)
            elif current_chapter:
                sec = {"heading": "", "level": 2, "content": [entry]}
                current_chapter["sections"].append(sec)
                current_section = sec
            else:
                sec = {"heading": "", "level": 2, "content": [entry]}
                ch = {"heading": "", "level": 1, "sections": [sec]}
                structure["chapters"].append(ch)
                current_chapter = ch
                current_section = sec

    if (not structure["title"] or ".docx" in structure["title"]) and title_candidates:
        structure["title"] = title_candidates[0]

    images = []
    for i, rel in enumerate(doc.part.rels.values()):
        if "image" in rel.reltype:
            try:
                img_data = rel.target_part.blob
                ext = Path(rel.target_ref).suffix if rel.target_ref else ".png"
                if ext.lower() not in (".png",".jpg",".jpeg",".gif",".bmp"): ext = ".png"
                img_name = f"{book_id}_img_{i}{ext}"
                (IMG_DIR / img_name).write_bytes(img_data)
                images.append({"name": img_name, "src": f"/static/textbook_images/{img_name}", "size": len(img_data)})
            except:
                pass

    structure = optimize_textbook_content(structure)
    (DATA_DIR / f"{book_id}.json").write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
    if images:
        (DATA_DIR / f"{book_id}_images.json").write_text(json.dumps(images, ensure_ascii=False, indent=2), encoding="utf-8")

    layout = {"id": book_id, "title": structure["title"], "chapters": []}
    for ch in structure["chapters"]:
        layout["chapters"].append({
            "heading": ch["heading"], "level": ch["level"],
            "sections": [{"heading": s["heading"], "level": s["level"], "content": s["content"]} for s in ch["sections"]]
        })
    return layout, images

def get_content(book_id):
    fp = DATA_DIR / f"{book_id}.json"
    if not fp.exists(): return None
    return optimize_textbook_content(json.loads(fp.read_text(encoding="utf-8")))

def save_content(book_id, title, chapters):
    structure = {"id": book_id, "title": title, "chapters": chapters}
    structure = optimize_textbook_content(structure)
    (DATA_DIR / f"{book_id}.json").write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")
    return structure
