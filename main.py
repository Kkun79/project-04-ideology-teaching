from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from engine import auth_service
from web.routes import register_routes

ROOT = Path(__file__).parent
UPLOAD_ROOT = ROOT / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="思政教学程序", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")


@app.middleware("http")
async def require_api_login(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and not path.startswith("/api/auth/"):
        token = auth_service.token_from_authorization(request.headers.get("Authorization", ""))
        if not auth_service.get_user_by_token(token):
            return JSONResponse({"detail": "请先登录后再使用程序"}, status_code=401)
    return await call_next(request)


register_routes(app, ROOT, UPLOAD_ROOT)


if __name__ == "__main__":
    import socket

    import uvicorn

    port = 28200
    for candidate in range(28200, 28299):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(("127.0.0.1", candidate))
        sock.close()
        if result != 0:
            port = candidate
            break

    print(f"server on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
