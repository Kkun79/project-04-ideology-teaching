# Hugging Face Spaces deployment

Use this path when Render asks for a billing card.

## Create the database

1. Create a Neon PostgreSQL project.
2. Copy the PostgreSQL connection string.
3. Keep the connection string private. It will be used as `DATABASE_URL`.

## Create the Space

1. Open Hugging Face Spaces.
2. Create a new Space.
3. Choose `Docker` as the SDK.
4. Keep the Space private while testing.
5. Upload or sync this repository.

The Docker image runs:

```bash
python scripts/init_postgres.py && python scripts/create_admin.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}
```

## Required secrets

Add these as Space secrets:

- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEEPSEEK_API_KEY`
- `APP_REGISTRATION_INVITE_CODES`
- `APP_REGISTRATION_REUSABLE_INVITE_CODES` for permanent reusable invite codes

The Docker image now uses invite-only registration by default:

```text
APP_REGISTRATION_MODE=invite_only
```

One-time invite codes:

```text
class2026-a1,class2026-a2
```

Permanent reusable invite codes:

```text
student-a01,student-a02,student-a03
```

## Verify after deploy

- Open the Space public URL.
- Check `/api/auth/db-health`.
- Log in with the admin account.
- Check `/api/auth/config` and confirm `registration_mode` is `invite_only`.
- Confirm registration without an invite code is rejected.
