import json
import os
import re
import uuid
from collections import Counter
from datetime import datetime
from typing import Any

from engine import storage

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
AUTO_POLITICS_ORIGINS = {"gnews-auto", "xinhua-auto"}


def _ensure_file(filename: str):
   return str(storage.ensure_list_file(filename))


def _read_json(filename: str) -> list:
   return storage.read_json_list(filename)


def _write_json(filename: str, data: list):
   storage.write_json_list(filename, data)


def _make_id() -> str:
   return datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6]


def _normalize_identity(value: str) -> str:
   return " ".join(str(value or "").strip().lower().split())


def _find_first(filename: str, predicate):
   return storage.find_first(filename, predicate)


def _clean_text(value: Any) -> str:
   return str(value or "").strip()


def _clean_multiline_text(value: Any) -> str:
   text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
   lines = [line.rstrip() for line in text.split("\n")]
   return "\n".join(lines).strip()


def _clean_list(values: Any) -> list[str]:
   if not isinstance(values, list):
      return []
   cleaned = []
   seen = set()
   for value in values:
      text = _clean_text(value)
      key = _normalize_identity(text)
      if not text or not key or key in seen:
         continue
      seen.add(key)
      cleaned.append(text)
   return cleaned


def _looks_like_placeholder(text: Any) -> bool:
   raw = _clean_text(text)
   needle = _normalize_identity(raw)
   if not needle:
      return True
   if needle in {"test", "测试", "t", "demo", "示例", "todo", "tbd", "n/a", "na", "none", "null"}:
      return True
   if re.fullmatch(r"[\?\uff1f_./\\\-*xX]+", raw):
      return True
   if "??" in raw or "？？" in raw or "xxx" in needle:
      return True
   bad_markers = [
      "此处为ai生成",
      "ai 生成内容",
      "建议进一步润色",
      "建议根据实际需要修改完善",
      "根据实际情况调整",
      "待补充",
      "待完善",
      "待填写",
      "占位",
      "示意内容",
   ]
   return any(marker in needle for marker in bad_markers)


def _sort_items_by_date(data: list, published_key: str = "published_at", date_key: str = "date") -> list:
   return sorted(
      data,
      key=lambda item: (
         str(item.get(published_key, "")),
         str(item.get(date_key, "")),
         int(item.get("sync_rank") or 0),
         str(item.get("id", "")),
      ),
      reverse=True,
   )


def _same_identity(left: str, right: str) -> bool:
   return bool(_normalize_identity(left)) and _normalize_identity(left) == _normalize_identity(right)


def _ensure_current_politics_ids(data: list) -> tuple[list, bool]:
   changed = False
   for item in data:
      if not _clean_text(item.get("id")):
         item["id"] = _make_id()
         changed = True
   return data, changed


# ── 课内知识 ──

def get_textbooks() -> list:
   return _read_json("textbooks.json")

def find_textbook_by_name(name: str) -> dict | None:
   needle = _normalize_identity(name)
   if not needle:
      return None
   return _find_first("textbooks.json", lambda item: _normalize_identity(item.get("name", "")) == needle)

def add_textbook(item: dict) -> dict:
   data = get_textbooks()
   item["id"] = item.get("id") or _make_id()
   data.append(item)
   _write_json("textbooks.json", data)
   return item

def delete_textbook(item_id: str):
   data = get_textbooks()
   _write_json("textbooks.json", [d for d in data if d["id"] != item_id])


def get_courseware() -> list:
   return _read_json("courseware.json")

def find_courseware_by_file_name(file_name: str) -> dict | None:
   needle = _normalize_identity(file_name)
   if not needle:
      return None
   return _find_first("courseware.json", lambda item: _normalize_identity(item.get("file_name", "")) == needle)

def find_courseware_by_title(title: str) -> dict | None:
   needle = _normalize_identity(title)
   if not needle:
      return None
   return _find_first("courseware.json", lambda item: _normalize_identity(item.get("title", "")) == needle)

def add_courseware(item: dict) -> dict:
   data = get_courseware()
   item["id"] = item.get("id") or _make_id()
   data.append(item)
   _write_json("courseware.json", data)
   return item

def delete_courseware(item_id: str):
   data = get_courseware()
   _write_json("courseware.json", [d for d in data if d["id"] != item_id])


def get_syllabus() -> list:
   return _read_json("syllabus.json")

def find_syllabus_by_title(title: str) -> dict | None:
   needle = _normalize_identity(title)
   if not needle:
      return None
   return _find_first("syllabus.json", lambda item: _normalize_identity(item.get("title", "")) == needle)

def _sanitize_syllabus_item(item: dict, *, validate: bool = True) -> dict:
   clean = {
      "title": _clean_text(item.get("title")),
      "semester": _clean_text(item.get("semester")),
      "total_hours": int(item.get("total_hours") or 0),
      "content": _clean_multiline_text(item.get("content")),
   }
   if validate:
      content = clean["content"]
      required_markers = ["课程目标", "教学内容", "考核方式"]
      chapter_markers = ["第一章", "第二章", "第三章", "第四章", "第五章", "第六章"]
      if not clean["title"] or _looks_like_placeholder(clean["title"]):
         raise ValueError("大纲标题无效，未写入教学大纲")
      if not clean["semester"]:
         raise ValueError("适用学期不能为空")
      if clean["total_hours"] <= 0:
         raise ValueError("总学时必须大于 0")
      if len(content) < 800 or _looks_like_placeholder(content):
         raise ValueError("大纲内容过短或不完整，未写入教学大纲")
      if any(marker not in content for marker in required_markers):
         raise ValueError("大纲缺少课程目标、教学内容或考核方式，未写入教学大纲")
      if sum(1 for marker in chapter_markers if marker in content) < 5:
         raise ValueError("大纲章节不完整，未写入教学大纲")
   return clean

def add_syllabus(item: dict) -> dict:
   data = get_syllabus()
   clean = _sanitize_syllabus_item(item)
   for index, current in enumerate(data):
      if _same_identity(current.get("title"), clean["title"]):
         clean["id"] = current.get("id") or _make_id()
         data[index] = clean
         _write_json("syllabus.json", data)
         return clean
   clean["id"] = _clean_text(item.get("id")) or _make_id()
   data.append(clean)
   _write_json("syllabus.json", data)
   return clean

def delete_syllabus(item_id: str):
   data = get_syllabus()
   _write_json("syllabus.json", [d for d in data if d["id"] != item_id])


def get_references() -> list:
   return _read_json("references.json")

def find_reference_by_title(title: str) -> dict | None:
   needle = _normalize_identity(title)
   if not needle:
      return None
   return _find_first("references.json", lambda item: _normalize_identity(item.get("title", "")) == needle)

def add_reference(item: dict) -> dict:
   data = get_references()
   item["id"] = _make_id()
   data.append(item)
   _write_json("references.json", data)
   return item

def delete_reference(item_id: str):
   data = get_references()
   _write_json("references.json", [d for d in data if d["id"] != item_id])


# ── 时政 ──

def get_current_politics(
   keyword: str = "",
   origin: str = "",
   tag: str = "",
   source: str = "",
   date_from: str = "",
   date_to: str = "",
) -> list:
   raw = _read_json("current_politics.json")
   data, changed = _ensure_current_politics_ids(raw)
   if changed:
      data = _sort_items_by_date(data)
      _write_json("current_politics.json", data)
   else:
      data = _sort_items_by_date(data)
   if origin == "auto":
      data = [d for d in data if d.get("origin") in AUTO_POLITICS_ORIGINS]
   elif origin == "manual":
      data = [d for d in data if d.get("origin") not in AUTO_POLITICS_ORIGINS]
   if tag:
      data = [d for d in data if tag in (d.get("tags") or [])]
   if source:
      source_key = _normalize_identity(source)
      data = [d for d in data if source_key in _normalize_identity(d.get("source", ""))]
   if date_from or date_to:
      filtered = []
      for item in data:
         item_date = _clean_text(item.get("date")) or _clean_text(item.get("published_at"))[:10]
         if date_from and item_date < date_from:
            continue
         if date_to and item_date > date_to:
            continue
         filtered.append(item)
      data = filtered
   if keyword:
      needle = keyword.strip().lower()
      data = [
         d for d in data
         if needle in " ".join([
            str(d.get("title", "")),
            str(d.get("source", "")),
            str(d.get("summary", "")),
            str(d.get("content", "")),
            " ".join(d.get("tags", []) or []),
         ]).lower()
      ]
   return data


def _sanitize_current_politics_item(item: dict) -> dict:
   clean = {
      "id": _clean_text(item.get("id")),
      "title": _clean_text(item.get("title")),
      "source": _clean_text(item.get("source")) or "手动录入",
      "date": _clean_text(item.get("date"))[:10],
      "summary": _clean_multiline_text(item.get("summary")),
      "content": _clean_multiline_text(item.get("content")) or _clean_multiline_text(item.get("summary")),
      "url": _clean_text(item.get("url")),
      "tags": _clean_list(item.get("tags") or []),
      "origin": _clean_text(item.get("origin")) or "manual",
      "published_at": _clean_text(item.get("published_at")),
      "image": _clean_text(item.get("image")),
      "sync_rank": int(item.get("sync_rank") or 0),
   }
   if not clean["title"]:
      raise ValueError("时政标题不能为空")
   if not clean["summary"]:
      raise ValueError("时政摘要不能为空")
   if _looks_like_placeholder(clean["title"]) or _looks_like_placeholder(clean["summary"]):
      raise ValueError("时政内容存在占位文本，未写入时政库")
   return clean


def add_current_politics(item: dict) -> dict:
   data = _read_json("current_politics.json")
   clean = _sanitize_current_politics_item(item)
   for index, current in enumerate(data):
      same_url = clean["url"] and _same_identity(current.get("url", ""), clean["url"])
      same_title_date = _same_identity(current.get("title", ""), clean["title"]) and _clean_text(current.get("date")) == clean["date"]
      if same_url or same_title_date:
         clean["id"] = clean.get("id") or current.get("id") or _make_id()
         data[index] = clean
         data = _sort_items_by_date(data)
         _write_json("current_politics.json", data)
         return clean
   clean["id"] = clean.get("id") or _make_id()
   data.append(clean)
   data = _sort_items_by_date(data)
   _write_json("current_politics.json", data)
   return clean

def delete_current_politics(item_id: str):
   data = get_current_politics()
   _write_json("current_politics.json", [d for d in data if d["id"] != item_id])


def replace_auto_current_politics(items: list) -> list:
   data = _read_json("current_politics.json")
   manual = [d for d in data if d.get("origin") not in AUTO_POLITICS_ORIGINS]
   auto_items = []
   for item in items:
      try:
         clean = _sanitize_current_politics_item(item)
         clean["id"] = clean.get("id") or _make_id()
         auto_items.append(clean)
      except ValueError:
         continue
   if items and not auto_items:
      raise ValueError("自动同步新闻均未通过校验，未写入时政库")
   merged = manual + auto_items
   merged = _sort_items_by_date(merged)
   _write_json("current_politics.json", merged)
   return merged


def get_current_politics_facets() -> dict:
   data = _sort_items_by_date(_read_json("current_politics.json"))
   tag_counts = Counter()
   source_counts = Counter()
   auto_count = 0
   manual_count = 0
   min_date = ""
   max_date = ""
   for item in data:
      if item.get("origin") in AUTO_POLITICS_ORIGINS:
         auto_count += 1
      else:
         manual_count += 1
      for tag in _clean_list(item.get("tags") or []):
         tag_counts[tag] += 1
      source = _clean_text(item.get("source"))
      if source:
         source_counts[source] += 1
      item_date = _clean_text(item.get("date")) or _clean_text(item.get("published_at"))[:10]
      if item_date:
         if not min_date or item_date < min_date:
            min_date = item_date
         if not max_date or item_date > max_date:
            max_date = item_date
   return {
      "summary": {
         "total": len(data),
         "auto": auto_count,
         "manual": manual_count,
         "domestic": sum(1 for item in data if "国内时政" in (item.get("tags") or [])),
         "world": sum(1 for item in data if "国际时政" in (item.get("tags") or [])),
      },
      "tags": [{"label": label, "count": count} for label, count in tag_counts.most_common(12)],
      "sources": [{"label": label, "count": count} for label, count in source_counts.most_common(12)],
      "date_range": {"min": min_date, "max": max_date},
   }


# ── 案例 ──

def _sanitize_case_item(item: dict, *, validate: bool = True) -> dict:
   clean = {
      "title": _clean_text(item.get("title")),
      "category": _clean_text(item.get("category")),
      "era": _clean_text(item.get("era")),
      "summary": _clean_multiline_text(item.get("summary")),
      "content": _clean_multiline_text(item.get("content")),
      "teaching_value": _clean_multiline_text(item.get("teaching_value")),
      "recommended_usage": _clean_multiline_text(item.get("recommended_usage")),
      "teaching_topics": _clean_list(item.get("teaching_topics")),
      "discussion_questions": _clean_list(item.get("discussion_questions")),
      "tags": _clean_list(item.get("tags")),
      "source": _clean_multiline_text(item.get("source")),
      "sync_origin": _clean_text(item.get("sync_origin")),
      "synced_at": _clean_text(item.get("synced_at")),
      "case_rank": int(item.get("case_rank") or 0),
   }
   if validate:
      if not clean["title"] or _looks_like_placeholder(clean["title"]):
         raise ValueError("案例标题无效，未写入案例库")
      if not clean["category"] or _looks_like_placeholder(clean["category"]):
         raise ValueError("案例分类不能为空或占位文本")
      if not clean["era"] or _looks_like_placeholder(clean["era"]):
         raise ValueError("案例时代不能为空或占位文本")
      if not clean["summary"] or len(clean["summary"]) < 20 or _looks_like_placeholder(clean["summary"]):
         raise ValueError("案例简介过短或包含占位文本")
      if not clean["content"] or len(clean["content"]) < 60 or _looks_like_placeholder(clean["content"]):
         raise ValueError("案例正文不完整，未写入案例库")
      if not clean["teaching_value"] or len(clean["teaching_value"]) < 16 or _looks_like_placeholder(clean["teaching_value"]):
         raise ValueError("教学价值说明不完整")
      if not clean["recommended_usage"] or len(clean["recommended_usage"]) < 16 or _looks_like_placeholder(clean["recommended_usage"]):
         raise ValueError("课堂使用建议不完整")
      if not clean["source"] or len(clean["source"]) < 6 or _looks_like_placeholder(clean["source"]):
         raise ValueError("案例来源不能为空或占位文本")
      if not clean["teaching_topics"]:
         raise ValueError("请至少填写一个教学主题")
      if not clean["discussion_questions"]:
         raise ValueError("请至少填写一个讨论问题")
      if not clean["tags"]:
         raise ValueError("请至少填写一个案例标签")
   return clean


def _normalize_cases(data: list) -> tuple[list, bool]:
   normalized = []
   changed = False
   for item in data:
      current = _sanitize_case_item(item, validate=False)
      current["id"] = _clean_text(item.get("id")) or _make_id()
      normalized.append(current)
      if current != item:
         changed = True
   return normalized, changed

def get_cases(category: str = "", era: str = "", keyword: str = "") -> list:
   data, changed = _normalize_cases(_read_json("cases.json"))
   if changed:
      _write_json("cases.json", data)
   data = sorted(
      data,
      key=lambda item: (
         1 if item.get("sync_origin") == "current-politics-auto" else 0,
         str(item.get("synced_at", "")),
         int(item.get("case_rank") or 0),
         str(item.get("id", "")),
      ),
      reverse=True,
   )
   if category:
        data = [d for d in data if d.get("category", "") == category]
   if era:
        data = [d for d in data if d.get("era", "") == era]
   if keyword:
       needle = keyword.strip().lower()
       def _matches(item: dict) -> bool:
           haystacks = [
               item.get("title", ""),
               item.get("summary", ""),
               item.get("content", ""),
               item.get("teaching_value", ""),
               item.get("recommended_usage", ""),
               " ".join(item.get("tags", []) or []),
               " ".join(item.get("teaching_topics", []) or []),
               " ".join(item.get("discussion_questions", []) or []),
           ]
           return any(needle in str(text).lower() for text in haystacks)
       data = [d for d in data if _matches(d)]
   return data

def add_case(item: dict) -> dict:
   data = _read_json("cases.json")
   clean = _sanitize_case_item(item)
   title = clean["title"]
   for current in data:
      if _same_identity(current.get("title"), title):
         clean["id"] = current.get("id")
         data[data.index(current)] = clean
         _write_json("cases.json", data)
         return clean
   clean["id"] = _clean_text(item.get("id")) or _make_id()
   data.append(clean)
   _write_json("cases.json", data)
   return clean

def replace_auto_cases(items: list[dict]) -> list[dict]:
   if not items:
      return []
   data = _read_json("cases.json")
   manual = [item for item in data if item.get("sync_origin") != "current-politics-auto"]
   existing_ids = {
      _normalize_identity(item.get("title")): item.get("id")
      for item in data
      if item.get("sync_origin") == "current-politics-auto"
   }
   auto_items = []
   for item in items:
      clean = _sanitize_case_item(item)
      clean["id"] = _clean_text(item.get("id")) or existing_ids.get(_normalize_identity(clean["title"])) or _make_id()
      auto_items.append(clean)
   if items and not auto_items:
      raise ValueError("自动同步案例均未通过校验，未写入案例库")
   _write_json("cases.json", manual + auto_items)
   return auto_items

def delete_case(item_id: str):
   data = _read_json("cases.json")
   _write_json("cases.json", [d for d in data if d["id"] != item_id])


# ── 关键词条 ──

def get_key_terms() -> list:
   data = _read_json("key_terms.json")
   return sorted(
      data,
      key=lambda item: (
         1 if item.get("sync_origin") == "current-politics-auto" else 0,
         str(item.get("synced_at", "")),
         str(item.get("id", "")),
      ),
      reverse=True,
   )

UNSUITABLE_KEY_TERM_MARKERS = [
   "仇恨",
   "歧视",
   "色情",
   "赌博",
   "毒品",
   "诈骗",
   "传销",
   "极端主义",
   "恐怖主义",
   "自残",
   "低俗",
   "饭圈",
   "炫富",
   "恶意炒作",
   "网络暴力",
   "封建迷信",
]

def _sanitize_key_term_item(item: dict) -> dict:
   clean = {
      "term": _clean_text(item.get("term")),
      "book": _clean_text(item.get("book")),
      "proposer": _clean_text(item.get("proposer")),
      "proposed_time": _clean_text(item.get("proposed_time")),
      "proposed_context": _clean_text(item.get("proposed_context")),
      "meaning": _clean_multiline_text(item.get("meaning")),
      "significance": _clean_multiline_text(item.get("significance")),
      "source_publication": _clean_text(item.get("source_publication")),
      "url": _clean_text(item.get("url")),
      "related_terms": _clean_list(item.get("related_terms") or []),
      "sync_origin": _clean_text(item.get("sync_origin")),
      "synced_at": _clean_text(item.get("synced_at")),
      "source_scope": _clean_text(item.get("source_scope")),
   }
   if not clean["term"] or _looks_like_placeholder(clean["term"]):
      raise ValueError("词条名称不能为空或占位文本")
   if not clean["book"] or _looks_like_placeholder(clean["book"]):
      raise ValueError("词条来源书目或文献不能为空")
   if not clean["meaning"] or len(clean["meaning"]) < 20 or _looks_like_placeholder(clean["meaning"]):
      raise ValueError("词条内涵不完整，未写入词条库")
   if not clean["significance"] or len(clean["significance"]) < 20 or _looks_like_placeholder(clean["significance"]):
      raise ValueError("词条意义不完整，未写入词条库")
   if not clean["source_publication"] or _looks_like_placeholder(clean["source_publication"]):
      raise ValueError("词条来源不能为空")
   combined = "\n".join(str(value) for value in clean.values())
   if any(marker in combined for marker in UNSUITABLE_KEY_TERM_MARKERS):
      raise ValueError("词条内容不适合沉淀到课堂词条库，未写入")
   return clean

def add_key_term(item: dict) -> dict:
   data = get_key_terms()
   clean = _sanitize_key_term_item(item)
   term = clean["term"]
   for current in data:
      if _same_identity(current.get("term"), term):
         clean["id"] = current.get("id")
         data[data.index(current)] = clean
         _write_json("key_terms.json", data)
         return clean
   clean["id"] = _clean_text(item.get("id")) or _make_id()
   data.append(clean)
   _write_json("key_terms.json", data)
   return clean

def delete_key_term(item_id: str):
   data = get_key_terms()
   _write_json("key_terms.json", [d for d in data if d["id"] != item_id])


# ── 研学规划 ──

def get_study_tours() -> list:
   return _read_json("study_tours.json")

def _sanitize_study_tour_item(item: dict) -> dict:
   clean = {
      "title": _clean_text(item.get("title")),
      "destination": _clean_text(item.get("destination")),
      "duration": _clean_text(item.get("duration")),
      "objectives": _clean_multiline_text(item.get("objectives")),
      "itinerary": _clean_multiline_text(item.get("itinerary")),
      "budget": _clean_text(item.get("budget")),
      "notes": _clean_multiline_text(item.get("notes")),
     "theme": _clean_text(item.get("theme")),
     "ai_generated": bool(item.get("ai_generated")),
  }
   # 新增教学化字段（选填）
   clean["target_grade"] = _clean_text(item.get("target_grade"))
   clean["related_courses"] = _clean_list(item.get("related_courses") or [])
   clean["core_competencies"] = _clean_multiline_text(item.get("core_competencies"))
   clean["preparation"] = _clean_multiline_text(item.get("preparation"))
   clean["tasks"] = _clean_multiline_text(item.get("tasks"))
   clean["evaluation"] = _clean_multiline_text(item.get("evaluation"))
   clean["safety"] = _clean_multiline_text(item.get("safety"))
   clean["expected_outcomes"] = _clean_multiline_text(item.get("expected_outcomes"))
   clean["resources"] = _clean_multiline_text(item.get("resources"))
   if not clean["title"] or _looks_like_placeholder(clean["title"]):
      raise ValueError("研学方案标题无效，未写入研学库")
   if not clean["destination"] or _looks_like_placeholder(clean["destination"]):
      raise ValueError("研学目的地不能为空，未写入研学库")
   if not clean["duration"]:
      raise ValueError("研学时长不能为空")
   if not clean["objectives"] or len(clean["objectives"]) < 12 or _looks_like_placeholder(clean["objectives"]):
      raise ValueError("研学目标过短，未写入研学库")
   if not clean["itinerary"] or len(clean["itinerary"]) < 24 or _looks_like_placeholder(clean["itinerary"]):
      raise ValueError("研学行程不完整，未写入研学库")
   if "第1天" not in clean["itinerary"] and "第一天" not in clean["itinerary"]:
      raise ValueError("研学行程缺少分天安排，未写入研学库")
   if clean["ai_generated"]:
      if not clean["theme"] or _looks_like_placeholder(clean["theme"]):
         raise ValueError("研学主题无效，未写入研学库")
      if len(clean["objectives"]) < 24:
         raise ValueError("AI 研学目标过短，未写入研学库")
   return clean


def _is_duplicate_study_tour(current: dict, clean: dict) -> bool:
   same_title = _same_identity(current.get("title", ""), clean["title"])
   same_destination = _same_identity(current.get("destination", ""), clean["destination"])
   same_theme = _same_identity(current.get("theme", ""), clean["theme"])
   same_objectives = _same_identity(current.get("objectives", ""), clean["objectives"])
   same_itinerary = _same_identity(current.get("itinerary", ""), clean["itinerary"])
   if same_title and same_destination:
      return True
   if same_destination and same_objectives and same_itinerary:
      return True
   if clean["ai_generated"] and current.get("ai_generated") and same_destination and same_theme:
      return same_title or same_itinerary
   return False


def add_study_tour(item: dict) -> dict:
   data = _read_json("study_tours.json")
   clean = _sanitize_study_tour_item(item)
   for index, current in enumerate(data):
      if _is_duplicate_study_tour(current, clean):
         clean["id"] = current.get("id") or _make_id()
         data[index] = clean
         _write_json("study_tours.json", data)
         return clean
   clean["id"] = item.get("id") or _make_id()
   data.append(clean)
   _write_json("study_tours.json", data)
   return clean

def delete_study_tour(item_id: str):
   data = get_study_tours()
   _write_json("study_tours.json", [d for d in data if d["id"] != item_id])


# ── 情景剧 / 演讲稿 ──

def get_scripts(script_type: str = "", keyword: str = "", source: str = "") -> list:
   data = _read_json("scripts.json")
   if script_type:
       data = [d for d in data if d.get("type", "") == script_type]
   source = _clean_text(source)
   if source == "ai":
       data = [d for d in data if d.get("ai_generated")]
   elif source == "manual":
       data = [d for d in data if not d.get("ai_generated")]
   keyword = _clean_text(keyword).lower()
   if keyword:
       def matched(item: dict) -> bool:
          haystack = "\n".join(str(item.get(key, "")) for key in ("title", "type", "theme", "usage", "audience", "style", "characters", "content", "notes"))
          return keyword in haystack.lower()
       data = [d for d in data if matched(d)]
   return data

def _sanitize_script_item(item: dict) -> dict:
   clean = {
      "title": _clean_text(item.get("title")),
      "type": _clean_text(item.get("type")),
      "theme": _clean_text(item.get("theme")),
      "usage": _clean_text(item.get("usage")),
      "audience": _clean_text(item.get("audience")),
      "duration": _clean_text(item.get("duration")),
      "style": _clean_text(item.get("style")),
      "keywords": _clean_text(item.get("keywords")),
      "characters": _clean_multiline_text(item.get("characters")),
      "content": _clean_multiline_text(item.get("content")),
      "notes": _clean_multiline_text(item.get("notes")),
      "ai_generated": bool(item.get("ai_generated")),
   }
   if not clean["title"] or _looks_like_placeholder(clean["title"]):
      raise ValueError("脚本标题无效，未写入脚本库")
   if not clean["type"]:
      raise ValueError("脚本类型不能为空")
   if clean["type"] not in {"情景剧", "演讲稿"}:
      raise ValueError("脚本类型不受支持")
   if not clean["content"] or len(clean["content"]) < 40 or _looks_like_placeholder(clean["content"]):
      raise ValueError("脚本内容不完整，未写入脚本库")
   if clean["ai_generated"] and len(clean["content"]) < 120:
      raise ValueError("AI 生成内容过短，未写入脚本库")
   if not clean["theme"]:
      clean["theme"] = clean["title"]
   if clean["ai_generated"] and _looks_like_placeholder(clean["theme"]):
      raise ValueError("脚本主题无效，未写入脚本库")
   return clean


def _is_duplicate_script(current: dict, clean: dict) -> bool:
   same_title = _same_identity(current.get("title", ""), clean["title"])
   same_type = _same_identity(current.get("type", ""), clean["type"])
   same_theme = _same_identity(current.get("theme", ""), clean["theme"])
   same_content = _same_identity(current.get("content", ""), clean["content"])
   if same_title and same_type:
      return True
   if same_type and same_content:
      return True
   if clean["ai_generated"] and current.get("ai_generated") and same_type and same_theme:
      return True
   return False


def add_script(item: dict) -> dict:
   data = _read_json("scripts.json")
   clean = _sanitize_script_item(item)
   for index, current in enumerate(data):
      if _is_duplicate_script(current, clean):
         clean["id"] = current.get("id") or _make_id()
         data[index] = clean
         _write_json("scripts.json", data)
         return clean
   clean["id"] = item.get("id") or _make_id()
   data.append(clean)
   _write_json("scripts.json", data)
   return clean

def delete_script(item_id: str):
   data = get_scripts()
   _write_json("scripts.json", [d for d in data if d["id"] != item_id])


# ── 虚拟展馆 ──

def get_exhibits() -> list:
   return _read_json("exhibits.json")

def add_exhibit(item: dict) -> dict:
   data = get_exhibits()
   item["id"] = _make_id()
   data.append(item)
   _write_json("exhibits.json", data)
   return item

def delete_exhibit(item_id: str):
   data = get_exhibits()
   _write_json("exhibits.json", [d for d in data if d["id"] != item_id])


def get_data_assist_snapshot() -> dict:
   textbooks = get_textbooks()
   courseware = get_courseware()
   syllabus = get_syllabus()
   references = get_references()
   politics = get_current_politics()
   cases = _read_json("cases.json")
   study_tours = get_study_tours()
   scripts = get_scripts()
   exhibits = get_exhibits()

   case_category_counts = Counter(_clean_text(item.get("category")) for item in cases if _clean_text(item.get("category")))
   case_era_counts = Counter(_clean_text(item.get("era")) for item in cases if _clean_text(item.get("era")))
   hot_tags = Counter()
   for item in politics:
      hot_tags.update(_clean_list(item.get("tags") or []))
   for item in cases:
      hot_tags.update(_clean_list(item.get("tags") or []))
      hot_tags.update(_clean_list(item.get("teaching_topics") or []))

   auto_politics = [item for item in politics if item.get("origin") in AUTO_POLITICS_ORIGINS]
   manual_politics = [item for item in politics if item.get("origin") not in AUTO_POLITICS_ORIGINS]
   site_count = len([item for item in exhibits if item.get("type") == "site"])
   artifact_count = sum(len(item.get("artifacts", []) or []) for item in exhibits if item.get("type") == "site")

   return {
      "resource_counts": {
         "textbooks": len(textbooks),
         "courseware": len(courseware),
         "syllabus": len(syllabus),
         "references": len(references),
         "cases": len(cases),
         "politics": len(politics),
         "study_tours": len(study_tours),
         "scripts": len(scripts),
         "sites": site_count,
         "artifacts": artifact_count,
      },
      "politics": {
         "auto_count": len(auto_politics),
         "manual_count": len(manual_politics),
         "domestic_count": sum(1 for item in auto_politics if "国内时政" in (item.get("tags") or [])),
         "world_count": sum(1 for item in auto_politics if "国际时政" in (item.get("tags") or [])),
      },
      "cases": {
         "categories": [{"label": label, "count": count} for label, count in case_category_counts.most_common(6)],
         "eras": [{"label": label, "count": count} for label, count in case_era_counts.most_common(6)],
      },
      "ai_assets": {
         "study_tours": sum(1 for item in study_tours if item.get("ai_generated")),
         "scripts": sum(1 for item in scripts if item.get("ai_generated")),
      },
      "hot_tags": [{"label": label, "count": count} for label, count in hot_tags.most_common(10)],
      "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
   }


def _update_item(filename: str, item_id: str, updates: dict) -> dict | None:
   """通用更新：按 ID 查找并合并字段，返回更新后的对象或 None"""
   return storage.update_item(filename, item_id, updates)


def update_textbook(item_id: str, updates: dict) -> dict | None:
   return _update_item("textbooks.json", item_id, updates)

def update_courseware(item_id: str, updates: dict) -> dict | None:
   return _update_item("courseware.json", item_id, updates)

def update_syllabus(item_id: str, updates: dict) -> dict | None:
   current = _find_first("syllabus.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_syllabus_item(merged)
   clean["id"] = item_id
   return _update_item("syllabus.json", item_id, clean)

def update_reference(item_id: str, updates: dict) -> dict | None:
   return _update_item("references.json", item_id, updates)

def update_current_politics(item_id: str, updates: dict) -> dict | None:
   current = _find_first("current_politics.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_current_politics_item(merged)
   clean["id"] = item_id
   return _update_item("current_politics.json", item_id, clean)

def update_case(item_id: str, updates: dict) -> dict | None:
   current = _find_first("cases.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_case_item(merged)
   clean["id"] = item_id
   return _update_item("cases.json", item_id, clean)

def update_key_term(item_id: str, updates: dict) -> dict | None:
   current = _find_first("key_terms.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_key_term_item(merged)
   clean["id"] = item_id
   return _update_item("key_terms.json", item_id, clean)

def update_study_tour(item_id: str, updates: dict) -> dict | None:
   current = _find_first("study_tours.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_study_tour_item(merged)
   clean["id"] = item_id
   return _update_item("study_tours.json", item_id, clean)

def update_script(item_id: str, updates: dict) -> dict | None:
   current = _find_first("scripts.json", lambda item: item.get("id") == item_id)
   if not current:
      return None
   merged = dict(current)
   merged.update(updates)
   clean = _sanitize_script_item(merged)
   clean["id"] = item_id
   return _update_item("scripts.json", item_id, clean)

def update_exhibit(item_id: str, updates: dict) -> dict | None:
   return _update_item("exhibits.json", item_id, updates)
