import base64
import binascii
import re
from pathlib import Path

from fastapi import HTTPException

from engine import data_manager as dm


def sanitize_upload_name(filename: str, fallback: str) -> str:
    raw = Path(str(filename or fallback)).name.strip()
    safe = raw.replace("\x00", "")
    safe = re.sub(r"[\\/]+", "_", safe)
    safe = re.sub(r"[^0-9A-Za-z._\-\u4e00-\u9fff()\[\] ]+", "_", safe)
    safe = safe.strip(" .") or fallback
    if "." not in safe and "." in raw:
        safe = safe + Path(raw).suffix
    return safe[:180]


def decode_base64_payload(content_b64: str) -> bytes:
    try:
        return base64.b64decode(content_b64 or "", validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid file content: {exc}") from exc


def resolve_upload_path(
    base_dir: Path,
    filename: str,
    fallback: str,
    *,
    overwrite: bool = False,
) -> tuple[Path, str]:
    resolved_base = base_dir.resolve()
    resolved_base.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_upload_name(filename, fallback)
    candidate = (resolved_base / safe_name).resolve()
    if resolved_base not in candidate.parents and candidate != resolved_base:
        raise HTTPException(status_code=400, detail="Illegal upload path")

    if overwrite:
        return candidate, safe_name

    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix
    counter = 1
    while candidate.exists():
        safe_name = f"{stem}_{counter}{suffix}"
        candidate = (resolved_base / safe_name).resolve()
        counter += 1
    return candidate, safe_name


def require_meaningful_text(value: str, label: str) -> str:
    text = dm._clean_text(value)
    if not text or dm._looks_like_placeholder(text):
        raise HTTPException(status_code=422, detail=f"{label}不能为空或占位文本")
    return text
