---
title: project-04-ideology-teaching
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# project_04 ideology teaching app

This Space runs the `project_04` ideology teaching application with Docker.

## Runtime secrets

Configure these secrets in the Space settings:

- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEEPSEEK_API_KEY`
- `APP_REGISTRATION_INVITE_CODES`
- `APP_REGISTRATION_REUSABLE_INVITE_CODES` if you want permanent reusable codes

Optional override:

- `APP_REGISTRATION_MODE`

## Notes

- The container defaults to `APP_REGISTRATION_MODE=invite_only`.
- `APP_REGISTRATION_INVITE_CODES` stays one-time use.
- `APP_REGISTRATION_REUSABLE_INVITE_CODES` stays reusable and will not be consumed.
- The app listens on port `7860`.
