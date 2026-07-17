---
layout: default
title: GitHub Pages 部署
---

# GitHub Pages 部署

本项目的公开阅读站点由 `docs/` 目录生成，日报精读由 GitHub Actions 每天运行后发布到 `gh-pages` 分支。

## 发布方式

1. GitHub 仓库启用 Actions。
2. 仓库 Settings -> Pages：
   - Source: Deploy from a branch
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. 仓库 Secrets 配置：
   - `OPENAI_API_KEY`：默认 GitHub Actions 配置读取的模型密钥。
   - `ANTHROPIC_API_KEY`、`GOOGLE_API_KEY`、`LWN_KEY`：按需配置。
4. 手动运行一次 `Daily Horizon Summary` workflow。
5. 访问 `https://wangwenqi88.github.io/horizon-news-pages/`。

## 每日更新

`.github/workflows/daily-summary.yml` 已配置为每天北京时间 08:30 运行：

```yaml
schedule:
  - cron: '30 0 * * *'
```

任务会执行 `uv run horizon --hours 48`，生成 `docs/_posts/YYYY-MM-DD-summary-{lang}.md`，再发布整个 `docs/` 到 `gh-pages`。

## 内容结构

- `docs/index.md`：资讯主页，按日期列出精读页面。
- `docs/_posts/`：每日精读内容，运行时生成。
- `docs/assets/css/horizon.css`：阅读主页和日报样式。
- `docs/_config.yml`：Jekyll Pages 配置。

## 注意事项

- `docs/_config.yml` 的 `baseurl` 需要和 GitHub 仓库名一致；当前默认是 `/horizon-news-pages`。
- `docs/_posts/*.md` 被 `.gitignore` 忽略，日报历史主要保存在 `gh-pages` 发布分支。
- 不要把 `.env`、`data/config.json` 或任何真实密钥提交到 GitHub。
