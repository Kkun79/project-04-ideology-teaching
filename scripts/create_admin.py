import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import auth_service  # noqa: E402


def main() -> int:
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username or not password:
        print("ADMIN_USERNAME or ADMIN_PASSWORD is not configured. Skipping admin initialization.")
        return 0

    auth_service.upsert_user(username, password)
    print("Admin account is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
