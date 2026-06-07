# Render Deployment

This repo is configured for one Render web service. The public service runs nginx on Render's `$PORT`, proxies the dashboard at `/`, and proxies the FastAPI backend at `/api`.

## Recommended: Blueprint

1. Push this repo to GitHub.
2. In Render, choose **New > Blueprint**.
3. Select this repository and the `main` branch.
4. Render will read `render.yaml` and create one service named `solonoi-airhack`.

After deploy:

- Dashboard: `https://<your-service>.onrender.com/`
- API health: `https://<your-service>.onrender.com/api/health`
- API docs: `https://<your-service>.onrender.com/api/docs`

## Manual Web Service Settings

If you create it from **New > Web Service** instead of Blueprint, use:

| Setting | Value |
|---|---|
| Source | This GitHub repository |
| Branch | `main` |
| Language / Runtime | `Docker` |
| Dockerfile Path | `./Dockerfile` |
| Docker Context | `.` |
| Docker Command | leave blank |
| Region | `Frankfurt`, or your nearest region |
| Instance Type | `Free` for demos, `Starter` or higher for persistence |
| Health Check Path | `/api/health` |
| Auto Deploy | Yes |

Environment variables:

| Key | Value |
|---|---|
| `API_BASE` | `http://127.0.0.1:8000` |
| `PUBLIC_API_BASE` | `/api` |
| `FASTAPI_ROOT_PATH` | `/api` |
| `PERSISTENT_STORAGE_DIR` | `/var/data` |
| `API_KEY_HASH_ALGO` | `sha256` |
| `JWT_ALGORITHM` | `HS256` |
| `SECRET_KEY` | generate a secret value |
| `API_KEY` | generate a secret value |
| `ANTHROPIC_API_KEY` | optional, only for AI Insights |

Do not set a build command or start command for the manual Docker service. The Dockerfile uses `docker/start.sh`.

## Persistence

Render Free web services have an ephemeral filesystem, so uploaded CSVs, trained models, auth users, alerts, and threshold edits reset after restarts or redeploys. For persistence, use a paid web service and attach a persistent disk:

| Disk Setting | Value |
|---|---|
| Mount Path | `/var/data` |
| Size | `1 GB` or larger |

The start script stores runtime files under that mount when `PERSISTENT_STORAGE_DIR=/var/data` is set.

## Public API Notes

The single external base URL is:

```text
https://<your-service>.onrender.com/api
```

Most API routes require the `X-API-Key` header using the Render `API_KEY` value. Public routes are `/api/health`, `/api/docs`, `/api/openapi.json`, `/api/redoc`, `/api/auth/login`, and `/api/auth/register`.
