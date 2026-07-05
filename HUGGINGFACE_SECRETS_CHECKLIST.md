# Hugging Face Space secrets checklist

Space:

- `https://huggingface.co/spaces/shenjiankun/project-04-ideology-teaching/settings`

Add these in `Settings -> Variables and secrets` or `Settings -> Secrets`.

## Required

- `DATABASE_URL`
  - Neon or PostgreSQL connection string
- `ADMIN_USERNAME`
  - Example: `admin`
- `ADMIN_PASSWORD`
  - Your admin password
- `DEEPSEEK_API_KEY`
  - DeepSeek API key
- `APP_REGISTRATION_INVITE_CODES`
  - Invite codes separated by commas, semicolons, or new lines
  - Example: `student-a01,student-a02,student-a03`

## Optional permanent reusable invite codes

- `APP_REGISTRATION_REUSABLE_INVITE_CODES`
  - These codes can be used permanently and repeatedly
  - Invite codes separated by commas, semicolons, or new lines
  - Example: `student-a01,student-a02,student-a03`

## Recommended

- `APP_REGISTRATION_MODE`
  - Value: `invite_only`

## How to verify

After saving, wait for the Space to restart, then check:

- `/api/auth/config`
  - should return `registration_mode=invite_only`
- `/api/auth/db-health`
  - should return `ok=true`
- Register without an invite code
  - should be rejected
