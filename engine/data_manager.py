import json
import os
import uuid
from datetime import datetime
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _ensure_file(filename: str):
   path = os.path.join(DATA_DIR, filename)
   if not os.path.exists(path):
       os.makedirs(DATA_DIR, exist_ok=True)
       with open(path, "w", encoding="utf-8") as f:
           json.dump([], f, ensure_ascii=False, indent=2)
   return path


def _read_json(filename: str) -> list:
   path = _ensure_file(filename)
   with open(path, "r", encoding="utf-8") as f:
       return json.load(f)


def _write_json(filename: str, data: list):
   path = os.path.join(DATA_DIR, filename)
   with open(path, "w", encoding="utf-8") as f:
       json.dump(data, f, ensure_ascii=False, indent=2)


def _make_id() -> str:
   return datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6]


# ── 课内知识 ──

def get_textbooks() -> list:
   return _read_json("textbooks.json")

def add_textbook(item: dict) -> dict:
   data = get_textbooks()
   item["id"] = _make_id()
   data.append(item)
   _write_json("textbooks.json", data)
   return item

def delete_textbook(item_id: str):
   data = get_textbooks()
   _write_json("textbooks.json", [d for d in data if d["id"] != item_id])


def get_courseware() -> list:
   return _read_json("courseware.json")

def add_courseware(item: dict) -> dict:
   data = get_courseware()
   item["id"] = _make_id()
   data.append(item)
   _write_json("courseware.json", data)
   return item

def delete_courseware(item_id: str):
   data = get_courseware()
   _write_json("courseware.json", [d for d in data if d["id"] != item_id])


def get_syllabus() -> list:
   return _read_json("syllabus.json")

def add_syllabus(item: dict) -> dict:
   data = get_syllabus()
   item["id"] = _make_id()
   data.append(item)
   _write_json("syllabus.json", data)
   return item

def delete_syllabus(item_id: str):
   data = get_syllabus()
   _write_json("syllabus.json", [d for d in data if d["id"] != item_id])


def get_references() -> list:
   return _read_json("references.json")

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

def get_current_politics() -> list:
   return _read_json("current_politics.json")

def add_current_politics(item: dict) -> dict:
   data = get_current_politics()
   item["id"] = _make_id()
   data.append(item)
   _write_json("current_politics.json", data)
   return item

def delete_current_politics(item_id: str):
   data = get_current_politics()
   _write_json("current_politics.json", [d for d in data if d["id"] != item_id])


# ── 案例 ──

def get_cases(category: str = "", era: str = "", keyword: str = "") -> list:
   data = _read_json("cases.json")
   if category:
       data = [d for d in data if d.get("category", "") == category]
   if era:
       data = [d for d in data if d.get("era", "") == era]
   if keyword:
       data = [d for d in data if keyword in d.get("title", "") or keyword in d.get("summary", "")]
   return data

def add_case(item: dict) -> dict:
   data = _read_json("cases.json")
   item["id"] = _make_id()
   data.append(item)
   _write_json("cases.json", data)
   return item

def delete_case(item_id: str):
   data = _read_json("cases.json")
   _write_json("cases.json", [d for d in data if d["id"] != item_id])


# ── 关键词条 ──

def get_key_terms() -> list:
   return _read_json("key_terms.json")

def add_key_term(item: dict) -> dict:
   data = get_key_terms()
   item["id"] = _make_id()
   data.append(item)
   _write_json("key_terms.json", data)
   return item

def delete_key_term(item_id: str):
   data = get_key_terms()
   _write_json("key_terms.json", [d for d in data if d["id"] != item_id])


# ── 研学规划 ──

def get_study_tours() -> list:
   return _read_json("study_tours.json")

def add_study_tour(item: dict) -> dict:
   data = get_study_tours()
   item["id"] = _make_id()
   data.append(item)
   _write_json("study_tours.json", data)
   return item

def delete_study_tour(item_id: str):
   data = get_study_tours()
   _write_json("study_tours.json", [d for d in data if d["id"] != item_id])


# ── 情景剧 / 演讲稿 ──

def get_scripts(script_type: str = "") -> list:
   data = _read_json("scripts.json")
   if script_type:
       data = [d for d in data if d.get("type", "") == script_type]
   return data

def add_script(item: dict) -> dict:
   data = get_scripts()
   item["id"] = _make_id()
   data.append(item)
   _write_json("scripts.json", data)
   return item

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


def update_textbook(item_id: str, updates: dict) -> dict | None:
   return _update_item("textbooks.json", item_id, updates)

def update_courseware(item_id: str, updates: dict) -> dict | None:
   return _update_item("courseware.json", item_id, updates)

def update_syllabus(item_id: str, updates: dict) -> dict | None:
   return _update_item("syllabus.json", item_id, updates)

def update_reference(item_id: str, updates: dict) -> dict | None:
   return _update_item("references.json", item_id, updates)

def update_current_politics(item_id: str, updates: dict) -> dict | None:
   return _update_item("current_politics.json", item_id, updates)

def update_case(item_id: str, updates: dict) -> dict | None:
   return _update_item("cases.json", item_id, updates)

def update_key_term(item_id: str, updates: dict) -> dict | None:
   return _update_item("key_terms.json", item_id, updates)

def update_study_tour(item_id: str, updates: dict) -> dict | None:
   return _update_item("study_tours.json", item_id, updates)

def update_script(item_id: str, updates: dict) -> dict | None:
   return _update_item("scripts.json", item_id, updates)

def update_exhibit(item_id: str, updates: dict) -> dict | None:
   return _update_item("exhibits.json", item_id, updates)
def _update_item(filename: str, item_id: str, updates: dict) -> dict | None:
   """通用更新：按 ID 查找并合并字段，返回更新后的对象或 None"""
   data = _read_json(filename)
   for i, d in enumerate(data):
      if d["id"] == item_id:
         d.update(updates)
         d["id"] = item_id
         data[i] = d
         _write_json(filename, data)
         return d
   return None

 
