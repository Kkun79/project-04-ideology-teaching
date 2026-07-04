import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import db  # noqa: E402


def main() -> int:
    if not db.is_database_configured():
        print("DATABASE_URL is not configured. Add it to .env first.")
        return 2

    result = db.initialize_schema()
    if result.get("ok"):
        print("PostgreSQL schema is ready.")
        print("Tables: " + ", ".join(name for name, exists in result["tables"].items() if exists))
        return 0

    print("PostgreSQL schema initialization did not complete.")
    print(result.get("message", "Unknown error"))
    print(result)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
