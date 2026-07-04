# Render deployment

This project deploys as a Render Web Service plus an external PostgreSQL database.
Use Neon for the database when Render asks for a billing card before creating
Render PostgreSQL.

## Render Blueprint

Use `render.yaml` in the repository root.

Render will prompt for these secret values:

- `DATABASE_URL` - paste the Neon PostgreSQL connection string
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEEPSEEK_API_KEY`
- `APP_REGISTRATION_INVITE_CODES`

Render defaults to invite-only registration:

```text
APP_REGISTRATION_MODE=invite_only
```

Use `APP_REGISTRATION_INVITE_CODES` to define who can register, for example:

```text
teacher-a01,teacher-a02
```

## Neon database

1. Create a Neon project.
2. Copy the pooled PostgreSQL connection string.
3. Use that value as Render's `DATABASE_URL`.

The app will create these tables automatically on startup:

- `users`
- `sessions`
- `audit_logs`
- `sync_runs`

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
- Check `/api/auth/config` and confirm `registration_mode` is `invite_only`.
- Confirm registration without an invite code is rejected.
