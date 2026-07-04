import copy
import re
from typing import Any


CHINESE_NUM = "\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e0-9"
INTRO_TITLE = "\u5bfc\u8bfb"
EXTENDED_TITLE = "\u5ef6\u4f38\u9605\u8bfb"


MAIN_CHAPTER_RE = re.compile(rf"^(\u7eea\s*\u8bba|\u7b2c\s*[{CHINESE_NUM}]+\s*\u7ae0)(.*)$")
SECTION_RE = re.compile(rf"^\u7b2c\s*([{CHINESE_NUM}]+)\s*\u8282\s*(.*)$")
NUMBERED_SUBHEADING_RE = re.compile(rf"^([{CHINESE_NUM}]+)[\u3001.．]\s*(.+)$")
PAREN_SUBHEADING_RE = re.compile(rf"^[\uff08(]([{CHINESE_NUM}]+)[\uff09)]\s*(.+)$")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_heading(value: Any) -> str:
    text = _clean_text(value)
    text = re.sub(r"\s*/\s*\d{1,3}\s*$", "", text)
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)
    text = re.sub(r"^[ivxlcdm]+\s+", "", text, flags=re.IGNORECASE)
    return text.strip()


def _is_noise_line(text: str) -> bool:
    compact = _compact(text)
    if not compact:
        return True
    if re.fullmatch(r"\d{1,3}", compact):
        return True
    if compact in {
        "\u76ee\u5f55",
        "\u540e\u8bb0",
        "\u56fe\u8bf4",
        "\u660e\u8fa8",
        "\u8fa8\u6790",
        "\u6587\u732e\u9605\u8bfb",
    }:
        return False
    if re.fullmatch(r"[\-—_]+", compact):
        return True
    # Page headers such as "44 第二章 追求远大理想坚定崇高信念".
    if re.match(rf"^\d{{1,3}}\s*\u7b2c\s*[{CHINESE_NUM}]+\s*\u7ae0", text):
        return True
    if re.match(rf"^\u7b2c\s*[{CHINESE_NUM}]+\s*\u7ae0.*\d{{1,3}}$", text) and len(compact) < 28:
        return True
    return False


def _is_main_chapter(text: str) -> bool:
    text = _clean_heading(text)
    compact = _compact(text)
    if compact.startswith("\u7eea\u8bba"):
        return True
    match = MAIN_CHAPTER_RE.match(text)
    if not match:
        return False
    if "\u8282" in compact:
        return False
    # Ignore bare OCR/page fragments like "第1章".
    suffix = _compact(match.group(2))
    return len(suffix) >= 2


def _normalize_main_chapter(text: str) -> str:
    text = _clean_heading(text)
    text = re.sub(r"^(\u7b2c\s*[" + CHINESE_NUM + r"]+\s*\u7ae0)\s*", lambda m: _compact(m.group(1)) + " ", text)
    text = re.sub(r"^(\u7eea\s*\u8bba)\s*", "\u7eea\u8bba ", text)
    return text.strip()


def _section_ordinal(text: str) -> str:
    match = SECTION_RE.match(_clean_heading(text))
    return _compact(match.group(1)) if match else ""


def _is_section(text: str) -> bool:
    return bool(SECTION_RE.match(_clean_heading(text)))


def _normalize_section(text: str) -> str:
    text = _clean_heading(text)
    match = SECTION_RE.match(text)
    if not match:
        return text
    ordinal = _compact(match.group(1))
    title = _clean_text(match.group(2))
    return f'\u7b2c{ordinal}\u8282 {title}'.strip()


def _is_subheading(text: str) -> bool:
    text = _clean_heading(text)
    compact = _compact(text)
    if not compact or _is_main_chapter(text) or _is_section(text):
        return False
    if compact in {"\u601d\u8003\u8ba8\u8bba", "\u6587\u732e\u9605\u8bfb", "\u56fe\u8bf4", "\u660e\u8fa8", "\u8fa8\u6790"}:
        return True
    if NUMBERED_SUBHEADING_RE.match(text) or PAREN_SUBHEADING_RE.match(text):
        return True
    return len(text) <= 24 and not re.search(r"[\u3002\uff1b;!?！？]", text)


def _new_chapter(title: str) -> dict:
    return {"heading": title, "level": 1, "sections": [], "_section_by_no": {}}


def _ensure_section(chapter: dict, heading: str = "", show_in_toc: bool = False) -> dict:
    heading = _normalize_section(heading) if show_in_toc else (_clean_heading(heading) or INTRO_TITLE)
    ordinal = _section_ordinal(heading) if show_in_toc else ""
    if show_in_toc and ordinal:
        existing = chapter["_section_by_no"].get(ordinal)
        if existing is not None:
            return existing
    if not show_in_toc and chapter["sections"]:
        last = chapter["sections"][-1]
        if not last.get("showInToc") and last.get("heading") == heading:
            return last
    section = {
        "heading": heading,
        "level": 2 if show_in_toc else 3,
        "showInToc": bool(show_in_toc),
        "content": [],
    }
    chapter["sections"].append(section)
    if show_in_toc and ordinal:
        chapter["_section_by_no"][ordinal] = section
    return section


def _append_content(section: dict, item: dict) -> None:
    text = _clean_text(item.get("text", ""))
    if _is_noise_line(text):
        return
    clean = {
        "text": text,
        "style": item.get("style", "Normal"),
        "level": item.get("level", 0),
        "bold": bool(item.get("bold")),
        "italic": bool(item.get("italic")),
    }
    if item.get("kind"):
        clean["kind"] = item["kind"]
    section["content"].append(clean)


def _iter_blocks(raw: dict):
    for chapter in raw.get("chapters", []) or []:
        heading = _clean_heading(chapter.get("heading", ""))
        if heading:
            yield "heading", {"text": heading, "level": chapter.get("level", 1)}
        for section in chapter.get("sections", []) or []:
            sec_heading = _clean_heading(section.get("heading", ""))
            if sec_heading:
                yield "heading", {"text": sec_heading, "level": section.get("level", 2)}
            for item in section.get("content", []) or []:
                yield "content", item


def optimize_textbook_content(raw_content: dict) -> dict:
    raw = copy.deepcopy(raw_content or {})
    result = {
        "id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "optimized": True,
        "chapters": [],
    }
    current_chapter = None
    current_section = None
    started = False

    for block_type, item in _iter_blocks(raw):
        text = _clean_heading(item.get("text", "")) if block_type == "heading" else _clean_text(item.get("text", ""))
        if _is_noise_line(text):
            continue

        if block_type == "heading" and _is_main_chapter(text):
            title = _normalize_main_chapter(text)
            if result["chapters"] and _compact(result["chapters"][-1]["heading"]) == _compact(title):
                current_chapter = result["chapters"][-1]
            else:
                current_chapter = _new_chapter(title)
                result["chapters"].append(current_chapter)
            current_section = None
            started = True
            continue

        if not started or current_chapter is None:
            continue

        if block_type == "heading" and _is_section(text):
            current_section = _ensure_section(current_chapter, text, True)
            continue

        if block_type == "heading" and _is_subheading(text):
            if current_section is None:
                current_section = _ensure_section(current_chapter, INTRO_TITLE, False)
            current_section["content"].append({"text": text, "kind": "subheading"})
            continue

        if current_section is None:
            current_section = _ensure_section(current_chapter, INTRO_TITLE, False)
        _append_content(current_section, item if block_type == "content" else {"text": text, "kind": "subheading"})

    cleaned_chapters = []
    for chapter in result["chapters"]:
        sections = []
        for section in chapter["sections"]:
            if section.get("content"):
                sections.append(section)
        if sections:
            chapter.pop("_section_by_no", None)
            chapter["sections"] = sections
            cleaned_chapters.append(chapter)
    result["chapters"] = cleaned_chapters

    if not result["chapters"]:
        raw["optimized"] = False
        return raw
    return result
