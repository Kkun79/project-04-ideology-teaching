from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from engine import auth_service
from engine import db as database
from engine import ai_service as ai
from engine import data_manager as dm
from engine import news_service
from engine import teaching_sync
from engine.docx_parser import get_content as get_parsed_content
from engine.smart_importer import save_categorized, smart_import

from .helpers import decode_base64_payload, require_meaningful_text, resolve_upload_path


def _current_user_from_request(request: Request) -> dict:
    token = auth_service.token_from_authorization(request.headers.get("Authorization", ""))
    user = auth_service.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录后再使用程序")
    return user


def _require_admin_user(request: Request) -> dict:
    user = _current_user_from_request(request)
    if not auth_service.is_admin_user(user):
        raise HTTPException(status_code=403, detail=auth_service.MSG_ADMIN_ONLY)
    return user


def _crud_router(prefix, name, get_fn, add_fn, update_fn, delete_fn):
    router = APIRouter(prefix="/api/" + prefix, tags=[name])

    @router.get("")
    async def list_items():
        try:
            return get_fn()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("")
    async def create_item(item: dict):
        try:
            return add_fn(item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.put("/{item_id}")
    async def update_item(item_id: str, item: dict):
        try:
            result = update_fn(item_id, item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not result:
            raise HTTPException(status_code=404, detail="Not found")
        return result

    @router.delete("/{item_id}")
    async def remove_item(item_id: str):
        try:
            delete_fn(item_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router


def register_routes(app: FastAPI, root: Path, upload_root: Path) -> None:
    @app.get("/favicon.ico")
    async def favicon():
        return HTMLResponse(status_code=204)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        try:
            html = (root / "templates" / "index.html").read_text(encoding="utf-8")
            return HTMLResponse(html)
        except Exception as exc:
            return HTMLResponse(f"<h1>加载失败</h1><p>{exc}</p>", status_code=500)

    @app.post("/api/auth/register")
    async def register_account(data: dict):
        try:
            user = auth_service.register_user(
                data.get("username", ""),
                data.get("password", ""),
                data.get("invite_code", ""),
            )
            return auth_service.create_session(user)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/auth/config")
    async def auth_config():
        return auth_service.registration_config()

    @app.post("/api/auth/login")
    async def login_account(data: dict):
        try:
            user = auth_service.authenticate(data.get("username", ""), data.get("password", ""))
            return auth_service.create_session(user)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/auth/me")
    async def current_account(request: Request):
        user = _current_user_from_request(request)
        if not user:
            raise HTTPException(status_code=401, detail="登录状态已失效")
        return {"user": user}

    @app.post("/api/auth/logout")
    async def logout_account(request: Request):
        token = auth_service.token_from_authorization(request.headers.get("Authorization", ""))
        auth_service.revoke_token(token)
        return {"ok": True}

    @app.get("/api/auth/db-health")
    async def database_health():
        return database.health_check()

    @app.get("/api/admin/users")
    async def admin_list_users(request: Request):
        _require_admin_user(request)
        return {"items": auth_service.list_users()}

    @app.post("/api/admin/users/{user_id}/password")
    async def admin_reset_password(user_id: str, data: dict, request: Request):
        _require_admin_user(request)
        try:
            user = auth_service.admin_reset_user_password(user_id, data.get("password", ""))
            return {"ok": True, "user": user}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/admin/users/{user_id}/status")
    async def admin_update_status(user_id: str, data: dict, request: Request):
        current_user = _require_admin_user(request)
        if str(current_user.get("id", "")) == str(user_id) and str(data.get("status", "")).strip().lower() != "active":
            raise HTTPException(status_code=422, detail="当前登录管理员账号不能被停用")
        try:
            user = auth_service.admin_update_user_status(user_id, data.get("status", ""))
            return {"ok": True, "user": user}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/upload")
    async def upload_file(data: dict):
        try:
            filename = data.get("filename", "unnamed.bin")
            content = decode_base64_payload(data.get("content", ""))
            dest, safe_name = resolve_upload_path(upload_root, filename, "upload.bin")
            dest.write_bytes(content)
            return {"file_path": f"/uploads/{safe_name}", "file_name": safe_name}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"上传失败: {exc}") from exc

    resources = [
        ("textbooks", dm.get_textbooks, dm.add_textbook, dm.update_textbook, dm.delete_textbook),
        ("courseware", dm.get_courseware, dm.add_courseware, dm.update_courseware, dm.delete_courseware),
        ("syllabus", dm.get_syllabus, dm.add_syllabus, dm.update_syllabus, dm.delete_syllabus),
        ("references", dm.get_references, dm.add_reference, dm.update_reference, dm.delete_reference),
        ("key-terms", dm.get_key_terms, dm.add_key_term, dm.update_key_term, dm.delete_key_term),
        ("study-tours", dm.get_study_tours, dm.add_study_tour, dm.update_study_tour, dm.delete_study_tour),
        ("exhibits", dm.get_exhibits, dm.add_exhibit, dm.update_exhibit, dm.delete_exhibit),
    ]
    for prefix, get_fn, add_fn, update_fn, delete_fn in resources:
        app.include_router(_crud_router(prefix, prefix, get_fn, add_fn, update_fn, delete_fn))

    @app.get("/api/scripts")
    async def list_scripts(type: str = "", keyword: str = "", source: str = ""):
        try:
            return dm.get_scripts(type, keyword, source)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/scripts")
    async def create_script(item: dict):
        try:
            return dm.add_script(item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.put("/api/scripts/{item_id}")
    async def update_script(item_id: str, item: dict):
        try:
            result = dm.update_script(item_id, item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not result:
            raise HTTPException(status_code=404, detail="Not found")
        return result

    @app.delete("/api/scripts/{item_id}")
    async def remove_script(item_id: str):
        try:
            dm.delete_script(item_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/cases")
    async def list_cases(category: str = "", era: str = "", keyword: str = ""):
        try:
            return dm.get_cases(category, era, keyword)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/cases")
    async def create_case(item: dict):
        try:
            return dm.add_case(item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.put("/api/cases/{item_id}")
    async def update_case(item_id: str, item: dict):
        try:
            result = dm.update_case(item_id, item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not result:
            raise HTTPException(status_code=404)
        return result

    @app.delete("/api/cases/{item_id}")
    async def remove_case(item_id: str):
        try:
            dm.delete_case(item_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/current-politics")
    async def list_current_politics(
        auto_refresh: int = 0,
        keyword: str = "",
        origin: str = "",
        tag: str = "",
        source: str = "",
        date_from: str = "",
        date_to: str = "",
    ):
        del auto_refresh
        try:
            return dm.get_current_politics(keyword, origin, tag, source, date_from, date_to)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/current-politics")
    async def create_current_politics(item: dict):
        try:
            return dm.add_current_politics(item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.put("/api/current-politics/{item_id}")
    async def update_current_politics(item_id: str, item: dict):
        try:
            result = dm.update_current_politics(item_id, item)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not result:
            raise HTTPException(status_code=404, detail="Not found")
        return result

    @app.delete("/api/current-politics/{item_id}")
    async def remove_current_politics(item_id: str):
        try:
            dm.delete_current_politics(item_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/current-politics-sync")
    async def sync_current_politics():
        try:
            result = news_service.refresh_current_politics(force=True)
            status = 200 if result.get("ok") else 503
            return JSONResponse(result, status_code=status)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/current-politics-facets")
    async def current_politics_facets():
        try:
            return dm.get_current_politics_facets()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/cases-sync")
    async def sync_cases():
        try:
            return JSONResponse(teaching_sync.sync_cases_from_current_politics(force=True), status_code=200)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/cases-sync/auto")
    async def auto_sync_cases():
        try:
            return JSONResponse(teaching_sync.auto_sync_cases_if_due(), status_code=200)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/key-terms-sync")
    async def sync_key_terms():
        try:
            return JSONResponse(teaching_sync.sync_key_terms_from_current_politics(force=True), status_code=200)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/key-terms-sync/auto")
    async def auto_sync_key_terms():
        try:
            return JSONResponse(teaching_sync.auto_sync_key_terms_if_due(), status_code=200)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/teaching-sync-status")
    async def teaching_sync_status():
        try:
            return teaching_sync.get_sync_status()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/textbooks/{book_id}/content")
    async def textbook_content(book_id: str):
        content = get_parsed_content(book_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Not found")
        return content

    @app.post("/api/study-tours/generate")
    async def generate_tour(data: dict):
        destination = require_meaningful_text(data.get("destination", ""), "研学目的地")
        duration = dm._clean_text(data.get("duration", "")) or "3天"
        theme = require_meaningful_text(data.get("theme", ""), "研学主题")
        plan = ai.generate_study_plan(destination, duration, theme)
        try:
            return dm.add_study_tour(plan)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/scripts/generate")
    async def generate_script(data: dict):
        script_type = dm._clean_text(data.get("type", "")) or "演讲稿"
        theme = require_meaningful_text(data.get("theme", ""), "脚本主题")
        characters = dm._clean_text(data.get("characters", ""))
        script = ai.generate_script(
            script_type,
            theme,
            characters,
            usage=dm._clean_text(data.get("usage", "")),
            audience=dm._clean_text(data.get("audience", "")),
            duration=dm._clean_text(data.get("duration", "")),
            style=dm._clean_text(data.get("style", "")),
            keywords=dm._clean_text(data.get("keywords", "")),
        )
        try:
            return dm.add_script(script)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/ancestor-dialogue")
    async def ancestor_dialogue(data: dict):
        try:
            leader = require_meaningful_text(data.get("leader", ""), "对话对象")
            question = require_meaningful_text(data.get("question", ""), "追问内容")
            history = data.get("history", [])
            return ai.generate_ancestor_dialogue(leader, question, history)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/ancestor-dialogue/opening")
    async def ancestor_dialogue_opening(data: dict):
        try:
            leader = require_meaningful_text(data.get("leader", ""), "对话对象")
            return ai.generate_ancestor_opening(leader)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/data-assist")
    async def get_data_assist():
        try:
            return dm.get_data_assist_snapshot()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/exhibits/hierarchy")
    async def get_hierarchy():
        all_items = dm.get_exhibits()
        provinces = [item for item in all_items if item.get("type") == "province"]
        sites = [item for item in all_items if item.get("type") == "site"]
        result = []
        for province in provinces:
            province_name = province["title"].split("\u2014")[0].strip()
            province_sites = [site for site in sites if site.get("province") == province_name]
            result.append({"province": province, "sites": province_sites})
        return result

    @app.post("/api/smart-import")
    async def smart_import_endpoint(data: dict):
        tmp_path = None
        try:
            filename = data.get("filename", "unnamed.docx")
            content = decode_base64_payload(data.get("content", ""))
            tmp_dir = upload_root / "smart_import"
            tmp_path, _ = resolve_upload_path(tmp_dir, filename, "smart_import.docx")
            tmp_path.write_bytes(content)

            book_id = "tb_" + dm._make_id()
            result = smart_import(str(tmp_path), book_id)
            if not result.get("ok"):
                return result

            summary = save_categorized(result["categorized"], result["title"], result["book_id"])
            final_book_id = summary.get("items", {}).get("textbook", result["book_id"])
            return {
                "ok": True,
                "book_id": final_book_id,
                "title": result["title"],
                "chapters": result["chapters"],
                "summary": summary,
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Import failed: " + str(exc)) from exc
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    @app.post("/api/courseware/upload")
    async def upload_courseware(data: dict):
        try:
            filename = data.get("filename", "courseware.pptx")
            if not filename.lower().endswith((".ppt", ".pptx")):
                raise HTTPException(status_code=400, detail="Only .ppt or .pptx is supported")

            content = decode_base64_payload(data.get("content", ""))
            upload_dir = upload_root / "courseware"
            dest, safe_name = resolve_upload_path(
                upload_dir,
                filename,
                "courseware.pptx",
                overwrite=True,
            )
            dest.write_bytes(content)

            stem = Path(safe_name).stem
            payload = {
                "title": stem,
                "chapter": "PPT课件",
                "description": "已导入课件文件",
                "file_path": f"/uploads/courseware/{safe_name}",
                "file_name": safe_name,
                "file_type": Path(safe_name).suffix.lower(),
            }
            existing = dm.find_courseware_by_file_name(safe_name) or dm.find_courseware_by_title(stem)
            action = "created"
            if existing:
                item = dm.update_courseware(existing["id"], payload)
                action = "replaced"
            else:
                item = dm.add_courseware(payload)
            return {"ok": True, "item": item, "action": action}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Courseware upload failed: " + str(exc)) from exc
