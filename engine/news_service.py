import hashlib
import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

from engine import data_manager as dm

try:
    import certifi
except Exception:  # pragma: no cover
    certifi = None


NEWS_SYNC_MINUTES = int(os.getenv("CURRENT_POLITICS_SYNC_MINUTES", "30"))
DOMESTIC_MAX = int(os.getenv("CURRENT_POLITICS_DOMESTIC_MAX", "8"))
WORLD_MAX = int(os.getenv("CURRENT_POLITICS_WORLD_MAX", "4"))
REQUEST_RETRIES = max(1, int(os.getenv("CURRENT_POLITICS_REQUEST_RETRIES", "5")))
REQUEST_RETRY_DELAY = max(0.2, float(os.getenv("CURRENT_POLITICS_REQUEST_RETRY_DELAY", "1.0")))
ALLOW_INSECURE_SSL_FALLBACK = os.getenv("CURRENT_POLITICS_ALLOW_INSECURE_SSL_FALLBACK", "1").strip().lower() not in {
    "0",
    "false",
    "no",
}
USER_AGENT = os.getenv(
    "CURRENT_POLITICS_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 project_04-current-politics/1.0",
).strip()
ARTICLE_TIMEOUT = int(os.getenv("CURRENT_POLITICS_ARTICLE_TIMEOUT", "25"))
DETAIL_MAX_PER_CHANNEL = max(1, int(os.getenv("CURRENT_POLITICS_DETAIL_MAX_PER_CHANNEL", "10")))
XINHUA_AUTO_ORIGIN = "xinhua-auto"
LEGACY_AUTO_ORIGINS = {"gnews-auto", XINHUA_AUTO_ORIGIN}
XINHUA_HOME_URL = "https://www.news.cn/"
XINHUA_POLITICS_LIST_URL = "https://www.xinhuanet.com/politics/szlb/index.html"
TEACHING_PRIORITY_KEYWORDS = [
    "习近平",
    "中国共产党",
    "共产党",
    "总书记",
    "党中央",
    "重要讲话",
    "复兴",
    "红色",
    "革命",
    "烈士",
    "强军",
    "改革",
    "发展",
    "高质量",
    "民生",
    "治理",
    "法治",
    "生态",
    "科技",
    "文化",
    "青年",
    "基层",
    "乡村",
    "民族",
    "香港",
]
LOW_PRIORITY_KEYWORDS = [
    "天气",
    "预警",
    "暴雨",
    "高温",
    "台风",
    "航班",
    "机场",
    "食谱",
    "皮肤",
    "不良反应",
    "手机",
    "原油出口",
]

CHANNELS = [
    {
        "name": "国内时政",
        "url": "https://www.news.cn/politics/",
        "source_urls": ["https://www.news.cn/politics/", XINHUA_POLITICS_LIST_URL, XINHUA_HOME_URL],
        "path_keywords": ["/politics/"],
        "exclude_keywords": ["/politics/xxjxs/", "/politics/leaders/"],
        "title_exclude_keywords": [
            "新华健康",
            "世界杯",
            "哈兰德",
            "食谱",
            "皮肤",
            "不良反应",
            "天气预报",
            "气象预警",
            "航班运行",
            "追光",
            "C罗",
        ],
        "tags": ["实时更新", "国内时政", "新华网"],
        "limit": DOMESTIC_MAX,
    },
    {
        "name": "国际时政",
        "url": "https://www.news.cn/world/",
        "source_urls": ["https://www.news.cn/world/", XINHUA_HOME_URL],
        "path_keywords": ["/world/"],
        "exclude_keywords": ["/world/zltx/", "/world/zhzt/"],
        "title_exclude_keywords": ["追光", "比赛", "球星"],
        "tags": ["实时更新", "国际时政", "新华网"],
        "limit": WORLD_MAX,
    },
]

DATA_DIR = Path(__file__).parent.parent / "data"
META_FILE = DATA_DIR / "current_politics_meta.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_meta() -> dict:
    if not META_FILE.exists():
        return {}
    try:
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_meta(data: dict) -> None:
    META_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _within_sync_window(last_sync: str) -> bool:
    if not last_sync:
        return False
    try:
        parsed = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
    except ValueError:
        return False
    return datetime.now(timezone.utc) - parsed < timedelta(minutes=NEWS_SYNC_MINUTES)


def _iter_ssl_contexts() -> list[tuple[str, ssl.SSLContext]]:
    contexts = [("system", _build_system_ssl_context())]
    if certifi is not None:
        contexts.append(("certifi", ssl.create_default_context(cafile=certifi.where())))
    if ALLOW_INSECURE_SSL_FALLBACK:
        contexts.append(("insecure", ssl._create_unverified_context()))
    return contexts


def _build_system_ssl_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_default_certs()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def _request_text(url: str) -> str:
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    errors = []
    for attempt in range(1, REQUEST_RETRIES + 1):
        for label, context in _iter_ssl_contexts():
            try:
                with urllib.request.urlopen(req, timeout=ARTICLE_TIMEOUT, context=context) as resp:
                    charset = resp.headers.get_content_charset() or "utf-8"
                    return resp.read().decode(charset, errors="ignore")
            except Exception as exc:
                errors.append(f"{label}#{attempt}: {type(exc).__name__}: {exc}")
        if attempt < REQUEST_RETRIES:
            time.sleep(REQUEST_RETRY_DELAY)
    tail = " | ".join(errors[-4:]) if errors else "unknown transport error"
    raise RuntimeError(f"新华网请求失败，已重试 {REQUEST_RETRIES} 次：{tail}")


def _clean_html_text(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_url(url: str, base_url: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    return urllib.parse.urljoin(base_url, value)


def _extract_meta(html: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']{re.escape(name)}["\']',
        rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
        rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{re.escape(name)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I)
        if match:
            return unescape(match.group(1).strip())
    return ""


def _extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>([\s\S]*?)</title>", html, flags=re.I)
    if not match:
        return ""
    title = _clean_html_text(match.group(1))
    title = re.sub(r"\s*-\s*新华网\s*$", "", title)
    return title.strip(" -")


def _extract_image(html: str, article_url: str) -> str:
    blacklist = ("detail2020/images/ewm", "qrcode-app", "zxcode_", "sharelogo.jpg", "ewm.png")
    for key in ("og:image", "image", "twitter:image"):
        value = _extract_meta(html, key)
        if value:
            candidate = _normalize_url(value, article_url)
            if candidate and not any(flag in candidate for flag in blacklist):
                return candidate
    for raw in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, flags=re.I):
        candidate = _normalize_url(raw, article_url)
        if not candidate:
            continue
        if any(flag in candidate for flag in blacklist):
            continue
        return candidate
    return ""


def _extract_paragraphs(html: str) -> list[str]:
    paragraphs = []
    for raw in re.findall(r"<p[^>]*>([\s\S]*?)</p>", html, flags=re.I):
        text = _clean_html_text(raw)
        if not text:
            continue
        if text.startswith("责任编辑"):
            continue
        if text.startswith("分享到"):
            continue
        paragraphs.append(text)
    return paragraphs


def _extract_article_from_page(article_url: str, html: str, stream_tag: str, fallback_title: str) -> dict:
    title = _extract_meta(html, "description").rstrip("-").strip() or _extract_title(html) or fallback_title
    title = title.rstrip("-").strip()
    publish_date = _extract_meta(html, "publishdate")
    publish_at = f"{publish_date}T00:00:00Z" if publish_date else ""
    source = _extract_meta(html, "source") or "新华网"
    image = _extract_image(html, article_url)
    paragraphs = _extract_paragraphs(html)
    if not paragraphs:
        raise ValueError("正文提取失败")
    content = "\n".join(paragraphs)
    summary = paragraphs[0]
    digest = hashlib.sha1(article_url.encode("utf-8")).hexdigest()[:16]
    return {
        "id": f"cp_auto_{digest}",
        "title": title,
        "source": source,
        "date": publish_date,
        "summary": summary[:280],
        "content": content,
        "url": article_url,
        "tags": ["实时更新", stream_tag, "新华网"],
        "origin": XINHUA_AUTO_ORIGIN,
        "published_at": publish_at,
        "image": image,
    }


def _is_valid_article_link(link: str, channel: dict) -> bool:
    if not link:
        return False
    if not any(keyword in link for keyword in channel["path_keywords"]):
        return False
    if any(keyword in link for keyword in channel["exclude_keywords"]):
        return False
    return bool(re.search(r"/20\d{6,8}/[0-9a-f]{16,}/c\.html", link, flags=re.I))


def _article_date_from_url(url: str) -> str:
    match = re.search(r"/(20\d{6})/", url)
    if not match:
        return ""
    raw = match.group(1)
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def _is_excluded_by_title(title: str, channel: dict) -> bool:
    clean_title = title or ""
    return any(keyword in clean_title for keyword in channel.get("title_exclude_keywords", []))


def _teaching_priority(text: str) -> int:
    value = text or ""
    score = sum(2 for keyword in TEACHING_PRIORITY_KEYWORDS if keyword in value)
    score -= sum(1 for keyword in LOW_PRIORITY_KEYWORDS if keyword in value)
    return score


def _extract_candidates_from_source(channel: dict, source_url: str) -> list[tuple[str, str]]:
    html = _request_text(source_url)
    href_pattern = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
        flags=re.I,
    )
    candidates = []
    seen = set()
    for href, inner_html in href_pattern.findall(html):
        url = _normalize_url(href, source_url)
        if not _is_valid_article_link(url, channel):
            continue
        title = _clean_html_text(inner_html)
        if _is_excluded_by_title(title, channel):
            continue
        if url in seen:
            continue
        seen.add(url)
        candidates.append((url, title))
        if len(candidates) >= max(channel["limit"] * 3, DETAIL_MAX_PER_CHANNEL):
            break
    return candidates


def _extract_channel_candidates(channel: dict) -> tuple[list[tuple[str, str]], list[str]]:
    candidates = []
    warnings = []
    seen = set()
    for source_url in channel.get("source_urls") or [channel["url"]]:
        try:
            for url, title in _extract_candidates_from_source(channel, source_url):
                if url in seen:
                    continue
                seen.add(url)
                candidates.append((url, title))
        except Exception as exc:
            warnings.append(f"{channel['name']}：{source_url} 候选链接读取失败（{exc}）")
    candidates.sort(
        key=lambda item: (_article_date_from_url(item[0]), _teaching_priority(item[1]), item[0]),
        reverse=True,
    )
    return candidates, warnings


def _fetch_channel(channel: dict) -> dict:
    items = []
    candidates, warnings = _extract_channel_candidates(channel)
    for url, fallback_title in candidates[:DETAIL_MAX_PER_CHANNEL]:
        try:
            article_html = _request_text(url)
            item = _extract_article_from_page(url, article_html, channel["name"], fallback_title)
            if _is_excluded_by_title(item["title"], channel):
                continue
            if len(item["summary"]) < 8 or len(item["content"]) < 24:
                raise ValueError("正文长度不足")
            item["sync_rank"] = _teaching_priority(
                " ".join([item.get("title", ""), item.get("summary", ""), item.get("content", "")[:500]])
            )
            items.append(item)
        except Exception as exc:
            warnings.append(f"{channel['name']}：{url} 提取失败（{exc}）")
        if len(items) >= channel["limit"]:
            break
    return {"items": items, "warnings": warnings}


def _merge_unique_items(items: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for item in items:
        key = item.get("url") or item.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return sorted(
        merged,
        key=lambda item: (
            str(item.get("published_at", "")),
            str(item.get("date", "")),
            int(item.get("sync_rank") or 0),
            str(item.get("id", "")),
        ),
        reverse=True,
    )


def _cached_sync_response(meta: dict) -> dict:
    current = dm.get_current_politics()
    latest = _latest_item(current)
    return {
        "ok": True,
        "configured": True,
        "updated": False,
        "message": _build_success_message(latest, cached=True, warnings=[]),
        "last_sync": meta.get("last_sync", ""),
        "source": "\u65b0\u534e\u7f51",
        "count": len(current),
        "latest_date": latest.get("date", ""),
        "latest_title": latest.get("title", ""),
    }


def _collect_channel_results() -> tuple[list[dict], list[str]]:
    all_items = []
    warnings = []
    for channel in CHANNELS:
        result = _fetch_channel(channel)
        all_items.extend(result["items"])
        warnings.extend(result["warnings"])
    return all_items, warnings


def _latest_item(items: list[dict]) -> dict:
    if not items:
        return {}
    return max(
        items,
        key=lambda item: (
            str(item.get("published_at", "")),
            str(item.get("date", "")),
            int(item.get("sync_rank") or 0),
            str(item.get("id", "")),
        ),
    )


def _build_success_message(latest: dict, cached: bool, warnings: list[str]) -> str:
    prefix = "\u5df2\u4f7f\u7528\u6700\u8fd1\u4e00\u6b21\u65b0\u534e\u7f51\u540c\u6b65\u7ed3\u679c" if cached else "\u65b0\u534e\u7f51\u65f6\u653f\u540c\u6b65\u5b8c\u6210"
    latest_date = latest.get("date", "")
    latest_title = latest.get("title", "")
    suffix = ""
    if latest_date and latest_title:
        suffix = f"\uff0c\u6700\u65b0\u4e00\u6761\u4e3a {latest_date}\u300a{latest_title}\u300b"
    elif latest_date:
        suffix = f"\uff0c\u6700\u65b0\u65e5\u671f\u4e3a {latest_date}"
    notice = "\uff0c\u4e2a\u522b\u9875\u9762\u672a\u80fd\u63d0\u53d6" if warnings else ""
    return f"{prefix}{suffix}{notice}\u3002"


def _persist_success_meta(last_sync: str, merged: list[dict], warnings: list[str]) -> None:
    latest = _latest_item(merged)
    _write_meta(
        {
            "last_sync": last_sync,
            "source": "\u65b0\u534e\u7f51",
            "count": len(merged),
            "configured": True,
            "latest_date": latest.get("date", ""),
            "latest_title": latest.get("title", ""),
            "last_error": "",
            "last_notice": "；".join(warnings[:6]),
        }
    )


def _success_response(last_sync: str, merged: list[dict], warnings: list[str]) -> dict:
    latest = _latest_item(merged)
    return {
        "ok": True,
        "configured": True,
        "updated": True,
        "message": _build_success_message(latest, cached=False, warnings=warnings),
        "last_sync": last_sync,
        "source": "\u65b0\u534e\u7f51",
        "count": len(merged),
        "latest_date": latest.get("date", ""),
        "latest_title": latest.get("title", ""),
        "warnings": warnings[:6],
        "provider": "xinhua",
    }


def _persist_failure_meta(meta: dict, error: str) -> None:
    _write_meta(
        {
            "last_sync": meta.get("last_sync", ""),
            "source": "\u65b0\u534e\u7f51",
            "count": meta.get("count", 0),
            "configured": True,
            "last_error": error,
        }
    )


def _failure_response(meta: dict, error: str) -> dict:
    return {
        "ok": False,
        "configured": True,
        "updated": False,
        "error": error,
        "last_sync": meta.get("last_sync", ""),
        "source": "\u65b0\u534e\u7f51",
        "provider": "xinhua",
    }


def refresh_current_politics(force: bool = False) -> dict:
    meta = _read_meta()
    if not force and _within_sync_window(meta.get("last_sync", "")):
        return _cached_sync_response(meta)

    try:
        all_items, warnings = _collect_channel_results()
        merged = _merge_unique_items(all_items)
        if not merged:
            detail = "；".join(warnings[:4]) if warnings else "\u672a\u83b7\u53d6\u5230\u65b0\u534e\u7f51\u65b0\u95fb\u6570\u636e"
            raise RuntimeError(detail)
        dm.replace_auto_current_politics(merged)
        last_sync = _utc_now_iso()
        _persist_success_meta(last_sync, merged, warnings)
        return _success_response(last_sync, merged, warnings)
    except Exception as exc:
        error = f"\u65b0\u534e\u7f51\u65f6\u653f\u540c\u6b65\u5931\u8d25\uff1a{exc}"
        _persist_failure_meta(meta, error)
        return _failure_response(meta, error)
