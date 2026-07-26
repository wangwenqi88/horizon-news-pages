# Horizon News Server Deployment

This document standardizes the server deployment path for Horizon News. The server should run one command every day:

```bash
./scripts/server_run.sh
```

The command performs the full workflow:

1. Load `.env`.
2. Sync dependencies with `uv`.
3. Collect news for the configured time window.
4. Build static HTML pages.
5. Commit public artifacts under `docs/`.
6. Push to the GitHub repository watched by Cloudflare Pages.

## Server Requirements

- Linux server with `bash`, `git`, `ssh`, and `uv`.
- Python version supported by the project, installed through `uv`.
- SSH access to the GitHub repository used by the `pages` remote.
- Cloudflare Pages connected to the GitHub repository and configured to publish the `docs` directory.

## First-Time Setup

Clone the project to a stable server path:

```bash
cd /opt
git clone git@github.com:wangwenqi88/horizon-news-pages.git horizon-news
cd /opt/horizon-news
```

If the code repository and publish repository are separate on your server, keep the code repository as the working directory and add the publish remote:

```bash
git remote add pages git@github.com:wangwenqi88/horizon-news-pages.git
git fetch pages
```

Run the bootstrap script:

```bash
./deploy/install.sh
```

Then edit `.env` on the server:

```env
HORIZON_AI_API_KEY=your-key
HORIZON_AI_BASE_URL=https://your-openai-compatible-gateway/v1
HORIZON_AI_MODEL=your-model
HORIZON_GITHUB_TOKEN=
HORIZON_PUBLISH_REMOTE=pages
HORIZON_PUBLISH_BRANCH=main
HORIZON_PUBLISH_HOURS=24
HORIZON_AUTO_PULL=0
HORIZON_UV_SYNC=1
```

`.env` is ignored by Git and must never be committed.

## Manual Test

Run once without pushing:

```bash
./scripts/server_run.sh --no-push
```

Run the full publish flow:

```bash
./scripts/server_run.sh
```

Logs are written to:

```text
logs/horizon-YYYY-MM-DD.log
```

The runner uses `.run/horizon-news.lock` to avoid overlapping runs.

## Crontab Deployment

Edit `deploy/crontab.example` and replace `/opt/horizon-news` if your project path is different.

Install:

```bash
crontab deploy/crontab.example
crontab -l
```

Check logs after the next run:

```bash
tail -n 200 logs/horizon-$(date '+%Y-%m-%d').log
```

## systemd Deployment

Copy the service and timer:

```bash
sudo cp deploy/systemd/horizon-news.service /etc/systemd/system/
sudo cp deploy/systemd/horizon-news.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now horizon-news.timer
```

Check status:

```bash
systemctl list-timers horizon-news.timer
journalctl -u horizon-news.service -n 200 --no-pager
```

Run manually through systemd:

```bash
sudo systemctl start horizon-news.service
```

## Updates

For controlled updates:

```bash
git pull --ff-only
uv sync
./scripts/server_run.sh --no-push
```

If you want the runner to pull automatically before every run, set:

```env
HORIZON_AUTO_PULL=1
```

Keep it disabled if the server should only run a reviewed version.

## Troubleshooting

- RSS 403 or 410: the source may block automated fetching or have moved. Disable or replace it in `data/config.json` or the tracked server config.
- Model call failed: check `HORIZON_AI_API_KEY`, `HORIZON_AI_BASE_URL`, and `HORIZON_AI_MODEL`. The base URL should normally end with `/v1` for OpenAI-compatible gateways.
- Git index already has staged changes: review and commit/unstage them before running the publish workflow.
- Git push failed: check the `pages` remote, branch name, deploy key, and GitHub permissions.
- Cloudflare page did not change: check whether the GitHub push succeeded first, then inspect Cloudflare Pages deployment logs. Deployment may lag for a short time after push.
- Empty or weak daily content: review source health and scoring rules, then run with a larger window, for example `./scripts/server_run.sh --hours 48`.
