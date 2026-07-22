# Deploy WorkTaskMe on Railway (step-by-step)

1. Open https://railway.app and sign in with **GitHub**.
2. **New Project** → **Deploy from GitHub repo** → choose `Abdo-Nayel/WTM`.
3. Add a database: **+ New** → **Database** → **PostgreSQL**.
4. Open the **web service** (the app from the repo) → **Variables** → **Add variable**:

| Variable | Value |
|----------|--------|
| `DEBUG` | `False` |
| `SECRET_KEY` | long random string (any 40+ chars) |
| `ALLOWED_HOSTS` | `*` |
| `CSRF_TRUSTED_ORIGINS` | `https://${{RAILWAY_PUBLIC_DOMAIN}}` |
| `FRONTEND_URL` | `https://${{RAILWAY_PUBLIC_DOMAIN}}` |
| `CORS_ALLOW_ALL_ORIGINS` | `True` |
| `USE_INMEMORY_CHANNELS` | `True` |
| `SEED_DEMO` | `True` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |

5. **Settings** → **Networking** → **Generate Domain**.
6. Wait for deploy (green). Open the public URL.
7. Login: `demo@worktaskme.com` / `Demo1234!`

Optional later: add Redis and set `REDIS_URL`, then set `USE_INMEMORY_CHANNELS=False`.
