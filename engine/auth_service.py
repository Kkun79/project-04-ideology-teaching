import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from engine import db
from engine import storage


USERS_FILE = "users.json"
TOKEN_TTL_HOURS = 12
_SESSIONS: dict[str, dict[str, Any]] = {}
_DB_INITIALIZED = False
_DB_MIGRATED = False
_INVITE_CODES_SYNC_SIGNATURE = ""
_USED_INVITE_CODES: set[str] = set()

MSG_USERNAME_RULE = "\u8d26\u53f7\u957f\u5ea6\u9700\u8981\u5728 3 \u5230 24 \u4e2a\u5b57\u7b26\u4e4b\u95f4"
MSG_USERNAME_CHARS = "\u8d26\u53f7\u53ea\u80fd\u5305\u542b\u4e2d\u6587\u3001\u5b57\u6bcd\u3001\u6570\u5b57\u3001\u4e0b\u5212\u7ebf\u6216\u77ed\u6a2a\u7ebf"
MSG_PASSWORD_RULE = "\u5bc6\u7801\u957f\u5ea6\u9700\u8981\u5728 6 \u5230 64 \u4e2a\u5b57\u7b26\u4e4b\u95f4"
MSG_USER_EXISTS = "\u8be5\u8d26\u53f7\u5df2\u7ecf\u5b58\u5728"
MSG_BAD_CREDENTIALS = "\u8d26\u53f7\u6216\u5bc6\u7801\u4e0d\u6b63\u786e"
MSG_REGISTER_CLOSED = "\u5f53\u524d\u4e0d\u5f00\u653e\u516c\u5f00\u6ce8\u518c"
MSG_INVITE_REQUIRED = "\u8be5\u6ce8\u518c\u901a\u9053\u9700\u8981\u9080\u8bf7\u7801"
MSG_INVITE_INVALID = "\u9080\u8bf7\u7801\u65e0\u6548\u6216\u5df2\u88ab\u4f7f\u7528"
MSG_ADMIN_ONLY = "\u4ec5\u7ba1\u7406\u5458\u53ef\u4ee5\u6267\u884c\u8be5\u64cd\u4f5c"
MSG_ADMIN_PROTECT = "\u7ba1\u7406\u5458\u8d26\u53f7\u4e0d\u80fd\u88ab\u505c\u7528"
MSG_STATUS_INVALID = "\u8d26\u53f7\u72b6\u6001\u53ea\u80fd\u8bbe\u4e3a active \u6216 disabled"
MSG_DELETE_CONFIRM = "\u8bf7\u8f93\u5165\u201c\u6ce8\u9500\u8d26\u53f7\u201d\u786e\u8ba4\u64cd\u4f5c"
MSG_DELETE_ADMIN_PROTECT = "\u7ba1\u7406\u5458\u8d26\u53f7\u4e0d\u80fd\u5728\u8fd9\u91cc\u6ce8\u9500\uff0c\u8bf7\u5148\u8bbe\u7f6e\u65b0\u7ba1\u7406\u5458\u540e\u518d\u5904\u7406"
MSG_DELETED_ACCOUNT = "\u8be5\u8d26\u53f7\u5df2\u6ce8\u9500\uff0c\u4e0d\u80fd\u7ee7\u7eed\u64cd\u4f5c"
MSG_USER_NOT_FOUND = "\u7528\u6237\u4e0d\u5b58\u5728"


def _now() -> datetime:
    return datetime.now()


def _db_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_username(username: str) -> str:
    return " ".join(str(username or "").strip().lower().split())


def _format_public_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value or "")


def _admin_username() -> str:
    return _normalize_username(_config_value("ADMIN_USERNAME"))


def is_admin_username(username: str) -> bool:
    admin_name = _admin_username()
    return bool(admin_name) and _normalize_username(username) == admin_name


def is_admin_user(user: dict | None) -> bool:
    return bool(user and is_admin_username(str(user.get("username", ""))))


def _public_user(user: dict) -> dict:
    created_at = _format_public_datetime(user.get("created_at", ""))
    last_login_at = _format_public_datetime(user.get("last_login_at", ""))
    username = user.get("username", "")
    return {
        "id": user.get("id", ""),
        "username": username,
        "created_at": created_at,
        "last_login_at": last_login_at,
        "status": user.get("status", "active"),
        "is_admin": is_admin_username(str(username)),
    }


def _read_users() -> list:
    return storage.read_json_list(USERS_FILE)


def _write_users(users: list) -> None:
    storage.write_json_list(USERS_FILE, users)


def _write_local_users(users: list) -> None:
    normalized = []
    for user in users:
        item = dict(user)
        item["status"] = item.get("status", "active") or "active"
        item["last_login_at"] = item.get("last_login_at", "")
        normalized.append(item)
    _write_users(normalized)


def _password_hash(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 160000)
    return digest.hex()


def _token_hash(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def _find_user(username: str) -> dict | None:
    key = _normalize_username(username)
    if not key:
        return None
    for user in _read_users():
        if _normalize_username(user.get("username", "")) == key:
            return user
    return None


def _find_user_by_id(user_id: str) -> dict | None:
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        return None
    for user in _read_users():
        if str(user.get("id", "")).strip() == clean_user_id:
            return user
    return None


def _db_enabled() -> bool:
    return db.is_database_configured()


def _config_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    return db._load_env_file().get(name, "").strip()


def registration_mode() -> str:
    mode = _config_value("APP_REGISTRATION_MODE").lower()
    if mode in {"open", "closed", "invite_only"}:
        return mode
    enabled = _config_value("APP_REGISTRATION_ENABLED").lower()
    return "closed" if enabled in {"0", "false", "no", "off"} else "open"


def registration_enabled() -> bool:
    return registration_mode() != "closed"


def registration_config() -> dict[str, Any]:
    try:
        _ensure_database()
    except Exception:
        pass
    mode = registration_mode()
    return {
        "registration_mode": mode,
        "registration_enabled": mode != "closed",
        "invite_required": mode == "invite_only",
    }


def _clean_invite_code(invite_code: str) -> str:
    return str(invite_code or "").strip()


def _invite_code_hash(invite_code: str) -> str:
    return hashlib.sha256(_clean_invite_code(invite_code).encode("utf-8")).hexdigest()


def _invite_code_hint(invite_code: str) -> str:
    code = _clean_invite_code(invite_code)
    if len(code) <= 4:
        return "*" * len(code)
    return code[:2] + "*" * max(2, len(code) - 4) + code[-2:]


def _configured_code_list(env_name: str) -> list[str]:
    raw_value = _config_value(env_name)
    if not raw_value:
        return []
    parts = []
    seen = set()
    normalized = raw_value.replace("\r", "\n").replace(";", "\n").replace(",", "\n")
    for piece in normalized.split("\n"):
        code = _clean_invite_code(piece)
        if not code or code in seen:
            continue
        seen.add(code)
        parts.append(code)
    return parts


def _configured_invite_codes() -> list[str]:
    return _configured_code_list("APP_REGISTRATION_INVITE_CODES")


def _configured_reusable_invite_codes() -> list[str]:
    return _configured_code_list("APP_REGISTRATION_REUSABLE_INVITE_CODES")


def _is_reusable_invite_code(invite_code: str) -> bool:
    code = _clean_invite_code(invite_code)
    return bool(code) and code in _configured_reusable_invite_codes()


def _invite_codes_signature(codes: list[str]) -> str:
    return "|".join(sorted(_invite_code_hash(code) for code in codes))


def _sync_invite_codes_to_db() -> None:
    global _INVITE_CODES_SYNC_SIGNATURE
    if not _db_enabled():
        return
    codes = _configured_invite_codes()
    code_hashes = [_invite_code_hash(code) for code in codes]
    signature = _invite_codes_signature(codes)
    if signature == _INVITE_CODES_SYNC_SIGNATURE:
        return
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            if code_hashes:
                cur.execute(
                    "DELETE FROM invite_codes WHERE used_at IS NULL AND NOT (code_hash = ANY(%s))",
                    (code_hashes,),
                )
            else:
                cur.execute("DELETE FROM invite_codes WHERE used_at IS NULL")
            for code in codes:
                cur.execute(
                    """
                    INSERT INTO invite_codes (code_hash, code_hint)
                    VALUES (%s, %s)
                    ON CONFLICT (code_hash) DO NOTHING
                    """,
                    (_invite_code_hash(code), _invite_code_hint(code)),
                )
        conn.commit()
    _INVITE_CODES_SYNC_SIGNATURE = signature


def _ensure_database() -> None:
    global _DB_INITIALIZED, _DB_MIGRATED
    if not _db_enabled():
        return
    if not _DB_INITIALIZED:
        db.initialize_schema()
        _DB_INITIALIZED = True
    if not _DB_MIGRATED:
        _migrate_json_users_to_db()
        _DB_MIGRATED = True
    _sync_invite_codes_to_db()


def _migrate_json_users_to_db() -> None:
    users = _read_users()
    if not users:
        return
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            for user in users:
                user_id = str(user.get("id") or "").strip()
                username = str(user.get("username") or "").strip()
                password_hash = str(user.get("password_hash") or "").strip()
                salt = str(user.get("salt") or "").strip()
                if not user_id or not username or not password_hash or not salt:
                    continue
                cur.execute(
                    """
                    INSERT INTO users (id, username, password_hash, salt, status, created_at)
                    VALUES (%s, %s, %s, %s, 'active', COALESCE(%s::timestamptz, now()))
                    ON CONFLICT (username) DO NOTHING
                    """,
                    (user_id, username, password_hash, salt, user.get("created_at") or None),
                )
        conn.commit()


def _db_find_user(username: str) -> dict | None:
    _ensure_database()
    key = _normalize_username(username)
    if not key:
        return None
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, salt, status, created_at, last_login_at
                FROM users
                WHERE lower(username) = lower(%s)
                """,
                (key,),
            )
            row = cur.fetchone()
    return _row_to_user(row)


def _db_find_user_by_id(user_id: str) -> dict | None:
    _ensure_database()
    if not user_id:
        return None
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, password_hash, salt, status, created_at, last_login_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
    return _row_to_user(row)


def _row_to_user(row) -> dict | None:
    if not row:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "salt": row[3],
        "status": row[4],
        "created_at": row[5],
        "last_login_at": row[6],
    }


def _write_audit(action: str, user_id: str = "", detail: dict | None = None) -> None:
    if not _db_enabled():
        return
    try:
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, target_type, detail)
                    VALUES (%s, %s, 'auth', %s::jsonb)
                    """,
                    (user_id or None, action, json.dumps(detail or {}, ensure_ascii=False)),
                )
            conn.commit()
    except Exception:
        pass


def _revoke_local_user_sessions(user_id: str) -> None:
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        return
    expired = [token for token, session in _SESSIONS.items() if str(session.get("user_id", "")).strip() == clean_user_id]
    for token in expired:
        _SESSIONS.pop(token, None)


def validate_username(username: str) -> str:
    clean = str(username or "").strip()
    if len(clean) < 3 or len(clean) > 24:
        raise ValueError(MSG_USERNAME_RULE)
    if not all(ch.isalnum() or ch in "_-" for ch in clean):
        raise ValueError(MSG_USERNAME_CHARS)
    return clean


def validate_password(password: str) -> str:
    raw = str(password or "")
    if len(raw) < 6 or len(raw) > 64:
        raise ValueError(MSG_PASSWORD_RULE)
    return raw


def upsert_user(username: str, password: str) -> dict:
    clean_username = validate_username(username)
    clean_password = validate_password(password)
    if not _db_enabled():
        existing = _find_user(clean_username)
        salt = secrets.token_hex(16)
        user = {
            "id": existing.get("id") if existing else "u_" + secrets.token_hex(8),
            "username": clean_username,
            "salt": salt,
            "password_hash": _password_hash(clean_password, salt),
            "status": "active",
            "last_login_at": existing.get("last_login_at", "") if existing else "",
            "created_at": existing.get("created_at") if existing else _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        users = [item for item in _read_users() if _normalize_username(item.get("username", "")) != _normalize_username(clean_username)]
        users.append(user)
        _write_local_users(users)
        return _public_user(user)

    _ensure_database()
    salt = secrets.token_hex(16)
    user_id = "u_" + secrets.token_hex(8)
    password_hash = _password_hash(clean_password, salt)
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, username, password_hash, salt, status, created_at)
                VALUES (%s, %s, %s, %s, 'active', now())
                ON CONFLICT (username)
                DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    salt = EXCLUDED.salt,
                    status = 'active'
                RETURNING id
                """,
                (user_id, clean_username, password_hash, salt),
            )
            saved_id = cur.fetchone()[0]
        conn.commit()
    _write_audit("admin_upsert", saved_id, {"username": clean_username})
    saved_user = _db_find_user(clean_username)
    return _public_user(saved_user or {"id": saved_id, "username": clean_username, "status": "active"})


def _require_valid_invite(invite_code: str) -> str:
    code = _clean_invite_code(invite_code)
    if not code:
        raise ValueError(MSG_INVITE_REQUIRED)
    return code


def _consume_local_invite_code(invite_code: str) -> str:
    code = _require_valid_invite(invite_code)
    if code not in _configured_invite_codes() or _invite_code_hash(code) in _USED_INVITE_CODES:
        raise ValueError(MSG_INVITE_INVALID)
    _USED_INVITE_CODES.add(_invite_code_hash(code))
    return code


def register_user(username: str, password: str, invite_code: str = "") -> dict:
    mode = registration_mode()
    if mode == "closed":
        raise ValueError(MSG_REGISTER_CLOSED)
    clean_username = validate_username(username)
    clean_password = validate_password(password)
    clean_invite_code = _require_valid_invite(invite_code) if mode == "invite_only" else ""
    reusable_invite_code = mode == "invite_only" and _is_reusable_invite_code(clean_invite_code)
    if _db_enabled():
        _ensure_database()
        salt = secrets.token_hex(16)
        user = {
            "id": "u_" + secrets.token_hex(8),
            "username": clean_username,
            "salt": salt,
            "password_hash": _password_hash(clean_password, salt),
            "status": "active",
        }
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE lower(username) = lower(%s)", (clean_username,))
                if cur.fetchone():
                    raise ValueError(MSG_USER_EXISTS)
                if mode == "invite_only" and not reusable_invite_code:
                    cur.execute(
                        """
                        SELECT code_hash
                        FROM invite_codes
                        WHERE code_hash = %s AND used_at IS NULL
                        FOR UPDATE
                        """,
                        (_invite_code_hash(clean_invite_code),),
                    )
                    if not cur.fetchone():
                        raise ValueError(MSG_INVITE_INVALID)
                cur.execute(
                    """
                    INSERT INTO users (id, username, password_hash, salt, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, now())
                    """,
                    (
                        user["id"],
                        user["username"],
                        user["password_hash"],
                        user["salt"],
                        user["status"],
                    ),
                )
                if mode == "invite_only" and not reusable_invite_code:
                    cur.execute(
                        """
                        UPDATE invite_codes
                        SET used_at = now(), used_by = %s
                        WHERE code_hash = %s
                        """,
                        (user["id"], _invite_code_hash(clean_invite_code)),
                    )
            conn.commit()
        saved_user = _db_find_user(clean_username) or user
        _write_audit("register", saved_user["id"], {"username": clean_username, "mode": mode})
        return _public_user(saved_user)

    if _find_user(clean_username):
        raise ValueError(MSG_USER_EXISTS)
    if mode == "invite_only" and not reusable_invite_code:
        _consume_local_invite_code(clean_invite_code)

    salt = secrets.token_hex(16)
    user = {
        "id": "u_" + secrets.token_hex(8),
        "username": clean_username,
        "salt": salt,
        "password_hash": _password_hash(clean_password, salt),
        "status": "active",
        "last_login_at": "",
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    users = _read_users()
    users.append(user)
    _write_local_users(users)
    return _public_user(user)


def authenticate(username: str, password: str) -> dict:
    if _db_enabled():
        _ensure_database()
        user = _db_find_user(username)
        if not user or user.get("status") != "active":
            raise ValueError(MSG_BAD_CREDENTIALS)
        candidate = _password_hash(str(password or ""), str(user.get("salt", "")))
        if not hmac.compare_digest(candidate, str(user.get("password_hash", ""))):
            raise ValueError(MSG_BAD_CREDENTIALS)
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET last_login_at = now() WHERE id = %s", (user["id"],))
            conn.commit()
        _write_audit("login", user["id"], {"username": user.get("username", "")})
        return user

    user = _find_user(username)
    if not user:
        raise ValueError(MSG_BAD_CREDENTIALS)
    if user.get("status", "active") != "active":
        raise ValueError(MSG_BAD_CREDENTIALS)
    candidate = _password_hash(str(password or ""), str(user.get("salt", "")))
    if not hmac.compare_digest(candidate, str(user.get("password_hash", ""))):
        raise ValueError(MSG_BAD_CREDENTIALS)
    users = _read_users()
    now_text = _now().strftime("%Y-%m-%d %H:%M:%S")
    for item in users:
        if str(item.get("id", "")).strip() == str(user.get("id", "")).strip():
            item["last_login_at"] = now_text
            item["status"] = item.get("status", "active") or "active"
            break
    _write_local_users(users)
    user["last_login_at"] = now_text
    return user


def _require_delete_confirmation(confirmation: str) -> None:
    if str(confirmation or "").strip() != "\u6ce8\u9500\u8d26\u53f7":
        raise ValueError(MSG_DELETE_CONFIRM)


def cancel_user_account(user_id: str, password: str, confirmation: str) -> dict:
    _require_delete_confirmation(confirmation)
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        raise ValueError(MSG_BAD_CREDENTIALS)

    if _db_enabled():
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, password_hash, salt, status, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (clean_user_id,),
                )
                row = cur.fetchone()
                user = _row_to_user(row)
                if not user or user.get("status") != "active":
                    raise ValueError(MSG_BAD_CREDENTIALS)
                if is_admin_user(user):
                    raise ValueError(MSG_DELETE_ADMIN_PROTECT)
                candidate = _password_hash(str(password or ""), str(user.get("salt", "")))
                if not hmac.compare_digest(candidate, str(user.get("password_hash", ""))):
                    raise ValueError(MSG_BAD_CREDENTIALS)
                cur.execute("UPDATE users SET status = 'deleted' WHERE id = %s", (clean_user_id,))
                cur.execute("DELETE FROM sessions WHERE user_id = %s", (clean_user_id,))
            conn.commit()
        _write_audit("delete_account", clean_user_id, {"username": user.get("username", "")})
        user["status"] = "deleted"
        return _public_user(user)

    users = _read_users()
    target = None
    for item in users:
        if str(item.get("id", "")).strip() == clean_user_id:
            target = item
            break
    if not target or target.get("status", "active") != "active":
        raise ValueError(MSG_BAD_CREDENTIALS)
    if is_admin_user(target):
        raise ValueError(MSG_DELETE_ADMIN_PROTECT)
    candidate = _password_hash(str(password or ""), str(target.get("salt", "")))
    if not hmac.compare_digest(candidate, str(target.get("password_hash", ""))):
        raise ValueError(MSG_BAD_CREDENTIALS)
    target["status"] = "deleted"
    _write_local_users(users)
    _revoke_local_user_sessions(clean_user_id)
    return _public_user(target)


def admin_cancel_user_account(user_id: str) -> dict:
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        raise ValueError(MSG_USER_NOT_FOUND)

    if _db_enabled():
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, password_hash, salt, status, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (clean_user_id,),
                )
                row = cur.fetchone()
                target = _row_to_user(row)
                if not target:
                    raise ValueError(MSG_USER_NOT_FOUND)
                if target.get("status") == "deleted":
                    raise ValueError(MSG_DELETED_ACCOUNT)
                if is_admin_user(target):
                    raise ValueError(MSG_DELETE_ADMIN_PROTECT)
                cur.execute("UPDATE users SET status = 'deleted' WHERE id = %s", (clean_user_id,))
                cur.execute("DELETE FROM sessions WHERE user_id = %s", (clean_user_id,))
            conn.commit()
        saved_user = _db_find_user_by_id(clean_user_id)
        if saved_user:
            _write_audit("admin_delete_account", clean_user_id, {"username": saved_user.get("username", "")})
            return _public_user(saved_user)
        raise ValueError(MSG_USER_NOT_FOUND)

    users = _read_users()
    target = None
    for item in users:
        if str(item.get("id", "")).strip() == clean_user_id:
            if item.get("status") == "deleted":
                raise ValueError(MSG_DELETED_ACCOUNT)
            if is_admin_user(item):
                raise ValueError(MSG_DELETE_ADMIN_PROTECT)
            item["status"] = "deleted"
            target = item
            break
    if not target:
        raise ValueError(MSG_USER_NOT_FOUND)
    _write_local_users(users)
    _revoke_local_user_sessions(clean_user_id)
    return _public_user(target)


def create_session(user: dict) -> dict:
    token = secrets.token_urlsafe(32)
    if _db_enabled():
        _ensure_database()
        expires_at = _db_now() + timedelta(hours=TOKEN_TTL_HOURS)
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE expires_at <= now()")
                cur.execute(
                    """
                    INSERT INTO sessions (token_hash, user_id, expires_at, created_at)
                    VALUES (%s, %s, %s, now())
                    """,
                    (_token_hash(token), user.get("id"), expires_at),
                )
            conn.commit()
        return {
            "token": token,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "user": _public_user(user),
        }

    expires_at = _now() + timedelta(hours=TOKEN_TTL_HOURS)
    _SESSIONS[token] = {
        "user_id": user.get("id"),
        "username": user.get("username"),
        "expires_at": expires_at,
    }
    return {
        "token": token,
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        "user": _public_user(user),
    }


def _cleanup_sessions() -> None:
    now = _now()
    expired = [token for token, session in _SESSIONS.items() if session.get("expires_at") <= now]
    for token in expired:
        _SESSIONS.pop(token, None)


def get_user_by_token(token: str) -> dict | None:
    if _db_enabled():
        clean_token = str(token or "").strip()
        if not clean_token:
            return None
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE expires_at <= now()")
                cur.execute(
                    """
                    SELECT user_id
                    FROM sessions
                    WHERE token_hash = %s AND expires_at > now()
                    """,
                    (_token_hash(clean_token),),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            return None
        user = _db_find_user_by_id(row[0])
        if not user or user.get("status") != "active":
            return None
        return _public_user(user)

    _cleanup_sessions()
    session = _SESSIONS.get(str(token or "").strip())
    if not session:
        return None
    user = _find_user(str(session.get("username", "")))
    if not user or user.get("status", "active") != "active":
        return None
    return _public_user(user)


def revoke_token(token: str) -> None:
    if _db_enabled():
        clean_token = str(token or "").strip()
        if not clean_token:
            return
        _ensure_database()
        user_id = None
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM sessions WHERE token_hash = %s", (_token_hash(clean_token),))
                row = cur.fetchone()
                if row:
                    user_id = row[0]
                cur.execute("DELETE FROM sessions WHERE token_hash = %s", (_token_hash(clean_token),))
            conn.commit()
        if user_id:
            _write_audit("logout", user_id)
        return

    _SESSIONS.pop(str(token or "").strip(), None)


def token_from_authorization(value: str) -> str:
    text = str(value or "").strip()
    if text.lower().startswith("bearer "):
        return text[7:].strip()
    return ""


def list_users() -> list[dict]:
    if _db_enabled():
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, password_hash, salt, status, created_at, last_login_at
                    FROM users
                    ORDER BY created_at DESC, username ASC
                    """
                )
                rows = cur.fetchall()
        return [_public_user(_row_to_user(row) or {}) for row in rows]

    users = [_public_user(user) for user in _read_users()]
    users.sort(key=lambda item: (item.get("created_at", ""), item.get("username", "")), reverse=True)
    return users


def _require_supported_status(status: str) -> str:
    clean_status = str(status or "").strip().lower()
    if clean_status not in {"active", "disabled"}:
        raise ValueError(MSG_STATUS_INVALID)
    return clean_status


def admin_reset_user_password(user_id: str, new_password: str) -> dict:
    clean_password = validate_password(new_password)
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        raise ValueError("用户不存在")

    if _db_enabled():
        _ensure_database()
        salt = secrets.token_hex(16)
        password_hash = _password_hash(clean_password, salt)
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username, status FROM users WHERE id = %s", (clean_user_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("用户不存在")
                if row[1] == "deleted":
                    raise ValueError(MSG_DELETED_ACCOUNT)
                cur.execute(
                    """
                    UPDATE users
                    SET password_hash = %s, salt = %s
                    WHERE id = %s
                    """,
                    (password_hash, salt, clean_user_id),
                )
                cur.execute("DELETE FROM sessions WHERE user_id = %s", (clean_user_id,))
            conn.commit()
        saved_user = _db_find_user_by_id(clean_user_id)
        if saved_user:
            _write_audit("admin_reset_password", clean_user_id, {"username": saved_user.get("username", "")})
            return _public_user(saved_user)
        raise ValueError("用户不存在")

    users = _read_users()
    target = None
    for item in users:
        if str(item.get("id", "")).strip() == clean_user_id:
            if item.get("status") == "deleted":
                raise ValueError(MSG_DELETED_ACCOUNT)
            salt = secrets.token_hex(16)
            item["salt"] = salt
            item["password_hash"] = _password_hash(clean_password, salt)
            item["status"] = item.get("status", "active") or "active"
            target = item
            break
    if not target:
        raise ValueError("用户不存在")
    _write_local_users(users)
    _revoke_local_user_sessions(clean_user_id)
    return _public_user(target)


def admin_update_user_status(user_id: str, status: str) -> dict:
    clean_status = _require_supported_status(status)
    clean_user_id = str(user_id or "").strip()
    if not clean_user_id:
        raise ValueError("用户不存在")

    if _db_enabled():
        _ensure_database()
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, password_hash, salt, status, created_at, last_login_at
                    FROM users
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (clean_user_id,),
                )
                row = cur.fetchone()
                target = _row_to_user(row)
                if not target:
                    raise ValueError("用户不存在")
                if target.get("status") == "deleted":
                    raise ValueError(MSG_DELETED_ACCOUNT)
                if is_admin_user(target) and clean_status != "active":
                    raise ValueError(MSG_ADMIN_PROTECT)
                cur.execute("UPDATE users SET status = %s WHERE id = %s", (clean_status, clean_user_id))
                if clean_status != "active":
                    cur.execute("DELETE FROM sessions WHERE user_id = %s", (clean_user_id,))
            conn.commit()
        saved_user = _db_find_user_by_id(clean_user_id)
        if saved_user:
            _write_audit("admin_set_status", clean_user_id, {"username": saved_user.get("username", ""), "status": clean_status})
            return _public_user(saved_user)
        raise ValueError("用户不存在")

    users = _read_users()
    target = None
    for item in users:
        if str(item.get("id", "")).strip() == clean_user_id:
            if item.get("status") == "deleted":
                raise ValueError(MSG_DELETED_ACCOUNT)
            if is_admin_user(item) and clean_status != "active":
                raise ValueError(MSG_ADMIN_PROTECT)
            item["status"] = clean_status
            target = item
            break
    if not target:
        raise ValueError("用户不存在")
    _write_local_users(users)
    if clean_status != "active":
        _revoke_local_user_sessions(clean_user_id)
    return _public_user(target)
