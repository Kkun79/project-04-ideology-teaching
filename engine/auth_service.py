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

MSG_USERNAME_RULE = "\u8d26\u53f7\u957f\u5ea6\u9700\u8981\u5728 3 \u5230 24 \u4e2a\u5b57\u7b26\u4e4b\u95f4"
MSG_USERNAME_CHARS = "\u8d26\u53f7\u53ea\u80fd\u5305\u542b\u4e2d\u6587\u3001\u5b57\u6bcd\u3001\u6570\u5b57\u3001\u4e0b\u5212\u7ebf\u6216\u77ed\u6a2a\u7ebf"
MSG_PASSWORD_RULE = "\u5bc6\u7801\u957f\u5ea6\u9700\u8981\u5728 6 \u5230 64 \u4e2a\u5b57\u7b26\u4e4b\u95f4"
MSG_USER_EXISTS = "\u8be5\u8d26\u53f7\u5df2\u7ecf\u5b58\u5728"
MSG_BAD_CREDENTIALS = "\u8d26\u53f7\u6216\u5bc6\u7801\u4e0d\u6b63\u786e"
MSG_REGISTER_CLOSED = "\u5f53\u524d\u4e0d\u5f00\u653e\u516c\u5f00\u6ce8\u518c"


def _now() -> datetime:
    return datetime.now()


def _db_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_username(username: str) -> str:
    return " ".join(str(username or "").strip().lower().split())


def _public_user(user: dict) -> dict:
    created_at = user.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "id": user.get("id", ""),
        "username": user.get("username", ""),
        "created_at": created_at,
        "status": user.get("status", "active"),
    }


def _read_users() -> list:
    return storage.read_json_list(USERS_FILE)


def _write_users(users: list) -> None:
    storage.write_json_list(USERS_FILE, users)


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


def _db_enabled() -> bool:
    return db.is_database_configured()


def registration_enabled() -> bool:
    value = os.environ.get("APP_REGISTRATION_ENABLED", "").strip().lower()
    return value not in {"0", "false", "no", "off"}


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
            "created_at": existing.get("created_at") if existing else _now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        users = [item for item in _read_users() if _normalize_username(item.get("username", "")) != _normalize_username(clean_username)]
        users.append(user)
        _write_users(users)
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


def register_user(username: str, password: str) -> dict:
    if not registration_enabled():
        raise ValueError(MSG_REGISTER_CLOSED)

    clean_username = validate_username(username)
    clean_password = validate_password(password)
    if _db_enabled():
        _ensure_database()
        if _db_find_user(clean_username):
            raise ValueError(MSG_USER_EXISTS)

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
            conn.commit()
        saved_user = _db_find_user(clean_username) or user
        _write_audit("register", saved_user["id"], {"username": clean_username})
        return _public_user(saved_user)

    if _find_user(clean_username):
        raise ValueError(MSG_USER_EXISTS)

    salt = secrets.token_hex(16)
    user = {
        "id": "u_" + secrets.token_hex(8),
        "username": clean_username,
        "salt": salt,
        "password_hash": _password_hash(clean_password, salt),
        "created_at": _now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    users = _read_users()
    users.append(user)
    _write_users(users)
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
    candidate = _password_hash(str(password or ""), str(user.get("salt", "")))
    if not hmac.compare_digest(candidate, str(user.get("password_hash", ""))):
        raise ValueError(MSG_BAD_CREDENTIALS)
    return user


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
    return _public_user(user) if user else None


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
