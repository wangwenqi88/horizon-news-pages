---
layout: default
title: GitHub Pages 部署
---

# Cloudflare Pages 部署

本项目的公开阅读站点由 `docs/` 承载。Horizon 先生成日报内容，再把静态 HTML 和结构化数据写入 `docs/`，最后由 Cloudflare Pages 直接从 GitHub 仓库自动发布。

标准链路是：

1. Horizon 采集最近 24 小时资讯。
2. AI 按双轨结构输出日报内容。
3. `scripts/build_static_pages.py` 生成 `docs/index.html`、`docs/daily/` 和 `docs/data/`。
4. `scripts/publish_daily.py` 或 GitHub Actions 把 `docs/` 相关产物提交回 GitHub。
5. Cloudflare Pages 监听仓库 `main` 分支并自动部署。

## 发布方式

1. 在 Cloudflare Dashboard 打开 Workers & Pages。
2. Create application -> Pages -> Connect to Git。
3. 选择 `wangwenqi88/horizon-news-pages`。
4. 构建配置：
   - Framework preset: None
   - Build command: 留空
   - Build output directory: `docs`
5. GitHub 仓库启用 Actions。
6. GitHub 仓库 Secrets 配置：
   - `HORIZON_AI_API_KEY`：自由模型或自有模型网关密钥。
   - `HORIZON_AI_BASE_URL`：OpenAI-compatible 模型网关地址，例如 `https://example.com/v1`。
   - `HORIZON_AI_MODEL`：模型名称。
   - `HORIZON_GITHUB_TOKEN`：可选，用于提高 GitHub API 访问额度；不配置时 workflow 使用 GitHub Actions 内置 token。
7. 手动运行一次 `Daily Horizon Summary` workflow。
8. 等待 workflow 把 `docs/index.html`、`docs/daily/*.html` 和 `docs/data/*` 提交到 `main` 后，Cloudflare 会自动部署。

## 每日更新

`.github/workflows/daily-summary.yml` 已配置为每天北京时间 08:30 运行：

```yaml
schedule:
  - cron: '30 0 * * *'
```

任务会复制 `data/config.github.json` 为运行配置，执行 `uv run horizon --hours 24`，生成 `docs/_posts/YYYY-MM-DD-summary-{lang}.md`，再执行 `scripts/build_static_pages.py` 生成：

- `docs/index.html`
- `docs/firsthand.html`
- `docs/insights.html`
- `docs/daily/YYYY-MM-DD-zh.html`
- `docs/daily/YYYY-MM-DD-en.html`
- `docs/read/*.html`

这些 HTML 文件会提交回 `main`，Cloudflare Pages 监听 GitHub 更新后自动发布。

## 手动发布

本地手动跑资讯时，应使用完整发布脚本：

```bash
uv run python scripts/publish_daily.py
```

该脚本会依次执行：

- `python -m src.main --hours 24`
- `python scripts/build_static_pages.py`
- `git add docs/index.html docs/firsthand.html docs/insights.html docs/daily docs/read docs/data docs/_posts`
- `git commit -m "Daily HTML summary: YYYY-MM-DD"`
- `git push pages HEAD:main`

如果只想验证生成效果，不推送 GitHub：

```bash
uv run python scripts/publish_daily.py --no-push
```

## 内容结构

- `docs/index.html`：Cloudflare 发布入口，只展示当天精选内容和历史日报入口。
- `docs/firsthand.html`：最新中文一手资讯完整列表。
- `docs/insights.html`：最新中文实战与专家洞察完整列表。
- `docs/daily/`：Cloudflare 发布的每日精读 HTML 页面。
- `docs/read/`：每条资讯的 AI 精读页面。
- `docs/index.md`：Jekyll 兼容入口，保留作备用。
- `docs/_posts/`：每日精读 Markdown 源文件，运行时生成并强制提交。
- `docs/assets/css/horizon.css`：阅读主页和日报样式。
- `scripts/build_static_pages.py`：Markdown 到静态 HTML 和结构化数据的生成器。

## 注意事项

- `docs/_posts/*.md` 会随生成的 HTML 一起提交，方便回看每日 Markdown 源文件。
- `docs/data/` 会随 HTML 一起提交，供后续小程序或轻量前端读取结构化资讯。
- 不要把 `.env`、`data/config.json` 或任何真实密钥提交到 GitHub。
- GitHub Actions 使用 `data/config.github.json`，本地运行使用 `data/config.json`；两者应保持信源、阈值和模型接入方式一致。
