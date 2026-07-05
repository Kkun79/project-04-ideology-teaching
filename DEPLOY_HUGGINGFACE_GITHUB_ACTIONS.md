# Sync GitHub to Hugging Face Spaces

Use this path when the local computer cannot push to `huggingface.co`.

## 1. Create a Hugging Face token

1. Open Hugging Face.
2. Go to Settings -> Access Tokens.
3. Create a token with write access.
4. Copy the token once.

## 2. Add the token to GitHub

1. Open the GitHub repository.
2. Go to Settings -> Secrets and variables -> Actions.
3. Add a new repository secret:
   - Name: `HF_TOKEN`
   - Value: the Hugging Face token

## 3. Run the sync workflow

1. Open the repository's Actions tab.
2. Select `Sync to Hugging Face Space`.
3. Click `Run workflow`.
4. Choose branch `main`.

The workflow uploads the repository contents to:

```text
https://huggingface.co/spaces/shenjiankun/project-04-ideology-teaching
```

This workflow uses Hugging Face's official `hub-sync` action instead of a raw
`git push`, which is more reliable for Spaces containing static assets.

## 4. Add Space secrets

In the Hugging Face Space settings, add these secrets:

- `DATABASE_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEEPSEEK_API_KEY`
- `APP_REGISTRATION_INVITE_CODES`
- `APP_REGISTRATION_REUSABLE_INVITE_CODES`

Optional override:

- `APP_REGISTRATION_MODE=invite_only`

Example invite codes:

```text
student-a01,student-a02,student-a03
```

If you want these three codes to stay permanent and reusable, put them in
`APP_REGISTRATION_REUSABLE_INVITE_CODES` instead of the one-time code variable.
