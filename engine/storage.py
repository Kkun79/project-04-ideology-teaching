import json
from pathlib import Path
from typing import Callable


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def data_path(filename: str) -> Path:
    return DATA_DIR / filename


def ensure_list_file(filename: str) -> Path:
    path = data_path(filename)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")
    return path


def read_json_list(filename: str) -> list:
    path = ensure_list_file(filename)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_list(filename: str, data: list) -> None:
    path = data_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def find_first(filename: str, predicate: Callable[[dict], bool]):
    for item in read_json_list(filename):
        if predicate(item):
            return item
    return None


def update_item(filename: str, item_id: str, updates: dict) -> dict | None:
    data = read_json_list(filename)
    for index, item in enumerate(data):
        if item.get("id") != item_id:
            continue
        merged = dict(item)
        merged.update(updates)
        merged["id"] = item_id
        data[index] = merged
        write_json_list(filename, data)
        return merged
    return None
