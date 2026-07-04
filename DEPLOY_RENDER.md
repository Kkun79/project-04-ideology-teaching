# Render deployment

This project deploys as a Render Web Service plus Render PostgreSQL.

## Render Blueprint

Use `render.yaml` in the repository root.

Render will prompt for these secret values:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEEPSEEK_API_KEY`

The public registration endpoint is disabled on Render by:

```text
APP_REGISTRATION_ENABLED=false
```

## Commands

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python scripts/init_postgres.py && python scripts/create_admin.py && uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Verify after deploy

- Open the public Render URL.
- Check `/api/auth/db-health`.
- Log in with the admin account.
- Confirm `/api/auth/register` returns a closed-registration message.
