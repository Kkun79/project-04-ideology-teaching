import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

TABLES = ("users", "sessions", "audit_logs", "sync_runs")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id BIGSERIAL PRIMARY KEY,
    sync_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_sync_runs_type_started ON sync_runs(sync_type, started_at);
"""


def _load_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        return values
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", "").strip() or _load_env_file().get("DATABASE_URL", "").strip()


def is_database_configured() -> bool:
    return bool(get_database_url())


def _load_psycopg():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is not installed. Run: pip install -r requirements.txt") from exc
    return psycopg


@contextmanager
def get_connection():
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured in .env or environment variables.")

    psycopg = _load_psycopg()
    conn = psycopg.connect(database_url, connect_timeout=5)
    try:
        yield conn
    finally:
        conn.close()


def initialize_schema() -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    return health_check(check_tables=True)


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        (table_name,),
    )
    row = cur.fetchone()
    return bool(row and row[0])


def health_check(check_tables: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "configured": is_database_configured(),
        "dependency": False,
        "connected": False,
        "ok": False,
        "tables": {name: False for name in TABLES},
        "message": "",
    }
    try:
        _load_psycopg()
        result["dependency"] = True
    except Exception as exc:
        result["message"] = str(exc)
        if not result["configured"]:
            return result

    if not result["configured"]:
        result["message"] = "DATABASE_URL is not configured."
        return result

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result["connected"] = cur.fetchone() == (1,)
                if check_tables:
                    result["tables"] = {name: _table_exists(cur, name) for name in TABLES}
        result["ok"] = bool(result["connected"] and all(result["tables"].values()))
        result["message"] = "PostgreSQL is ready." if result["ok"] else "PostgreSQL is reachable, but schema is incomplete."
        return result
    except Exception as exc:
        result["message"] = str(exc)
        return result
