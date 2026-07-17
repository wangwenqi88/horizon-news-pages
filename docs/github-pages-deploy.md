---
layout: default
title: GitHub Pages 部署
---

# Cloudflare Pages 部署

本项目的公开阅读站点由 `docs/` 目录承载，日报精读会生成真实 HTML 文件并提交到 GitHub。Cloudflare Pages 只需要从 GitHub 仓库发布 `docs/` 目录。

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
   - `OPENAI_API_KEY`：默认 GitHub Actions 配置读取的模型密钥。
   - `ANTHROPIC_API_KEY`、`GOOGLE_API_KEY`、`LWN_KEY`：按需配置。
7. 手动运行一次 `Daily Horizon Summary` workflow。
8. 等待 workflow 把 `docs/index.html` 和 `docs/daily/*.html` 提交到 `main` 后，Cloudflare 会自动部署。

## 每日更新

`.github/workflows/daily-summary.yml` 已配置为每天北京时间 08:30 运行：

```yaml
schedule:
  - cron: '30 0 * * *'
```

任务会执行 `uv run horizon --hours 48`，生成 `docs/_posts/YYYY-MM-DD-summary-{lang}.md`，再执行 `scripts/build_static_pages.py` 生成：

- `docs/index.html`
- `docs/daily/YYYY-MM-DD-zh.html`
- `docs/daily/YYYY-MM-DD-en.html`

这些 HTML 文件会提交回 `main`，Cloudflare Pages 监听 GitHub 更新后自动发布。

## 内容结构

- `docs/index.html`：Cloudflare 发布的资讯主页。
- `docs/daily/`：Cloudflare 发布的每日精读 HTML 页面。
- `docs/index.md`：Jekyll 兼容入口，保留作备用。
- `docs/_posts/`：每日精读 Markdown 源文件，运行时生成并强制提交。
- `docs/assets/css/horizon.css`：阅读主页和日报样式。
- `scripts/build_static_pages.py`：Markdown 到静态 HTML 的生成器。

## 注意事项

- `docs/_posts/*.md` 会随生成的 HTML 一起提交，方便回看每日 Markdown 源文件。
- 不要把 `.env`、`data/config.json` 或任何真实密钥提交到 GitHub。
