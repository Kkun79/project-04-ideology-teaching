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

## Notes

- Public registration is disabled in the container by default.
- The app listens on port `7860`.
