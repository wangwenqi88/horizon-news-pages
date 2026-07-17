# Horizon AI 新闻雷达 — 使用说明

## 简介

[Horizon](https://github.com/Thysrael/Horizon) 是一个 AI 驱动的开源新闻聚合工具。
本配置聚焦 **AI Agent / 自动化解决方案** 领域。

## 工作流定位

本项目只负责 **自动采集、AI 初筛、日报生成**。资讯进入知识库后，按以下 Wiki 工作流继续处理：

- 工作流标准：`G:\ai-workspace\wiki\学习\资讯\AI资讯工作流.md`
- 信源清单：`G:\ai-workspace\wiki\学习\资讯\AI资讯信源清单.md`
- 当日采集页：`G:\ai-workspace\wiki\学习\资讯\YYYY-MM-DD-采集.md`
- 选题池：`G:\ai-workspace\wiki\生活\创作\选题\`
- 来源摘要：`G:\ai-workspace\wiki\学习\来源\`

每条资讯不再只判断“重要不重要”，而是同时判断：

| 字段 | 用途 |
|:-----|:-----|
| `topic_score` | 是否适合做自媒体选题，0-5 分 |
| `learning_score` | 是否值得深度学习沉淀，0-5 分 |
| `domain` | 内容领域，如 AI Agent、AI 工具、Obsidian+AI、开源生态 |
| `source_tier` | 信源等级：S 原始/官方，A 专业，B 聚合/社区，C 线索 |

## 使用方式

### 方式一：本地运行

只采集并生成 Markdown，不发布：

```bash
cd G:\ai-workspace\code\horizon-news
set HORIZON_AI_API_KEY=sk-你的key
set HORIZON_AI_BASE_URL=https://你的模型网关/v1
set HORIZON_AI_MODEL=你的模型名
uv run horizon --hours 24
```

完整执行“采集 -> HTML -> GitHub 同步 -> Cloudflare 自动发布”：

```bash
cd G:\ai-workspace\code\horizon-news
uv run python scripts/publish_daily.py
```

只生成本地提交、不推送 GitHub：

```bash
uv run python scripts/publish_daily.py --no-push
```

### 方式二：服务器定时运行

服务器脚本为 `scripts/daily-run.sh`。它执行完整链路：采集、生成 HTML、提交 `docs/` 公开产物并推送到 GitHub。

### 方式三：由 Claude 代为运行

在对话中告知「跑一下新闻雷达」，我会在服务器上执行。

### 方式四：GitHub Actions + Cloudflare Pages 自动发布

GitHub Actions 每天北京时间 08:30 执行一次采集和生成：

1. 复制 `data/config.github.json` 为运行配置。
2. 执行 `uv run horizon --hours 24` 生成中英文日报 Markdown。
3. 执行 `scripts/build_static_pages.py` 生成 `docs/index.html` 和 `docs/daily/*.html`。
4. 自动提交 `docs/` 变化到 GitHub。
5. Cloudflare Pages 监听 GitHub 更新，发布 `docs/` 目录。

## 配置说明

运行配置文件：`data/config.json`。根目录 `config.json` 只作为人工维护副本，CLI 默认不读取。

| 配置项 | 说明 |
|:-------|:-----|
| `ai.provider` | 默认使用 `custom`，支持自由模型/自有模型/OpenAI-compatible 网关 |
| `ai.model` | 从 `.env` 的 `HORIZON_AI_MODEL` 读取 |
| `ai.base_url` | 从 `.env` 的 `HORIZON_AI_BASE_URL` 读取 |
| `ai.api_key_env` | 默认读取 `HORIZON_AI_API_KEY` |
| `sources.hackernews` | HN Top 10 热门，最低 100 分 |
| `sources.reddit` | 当前默认停用，保留 6 个 AI 相关 subreddit 配置 |
| `sources.rss` | 当前启用 TechCrunch AI、ArXiv ML、OpenAI Blog、智谱AI；其余源保留但停用 |
| `sources.github` | 10 个热门 AI 仓库 Release |
| `sources.rss[].max_items` | 单个 RSS 源最多进入分析的条数，ArXiv 当前限 5 条 |
| `filtering.ai_score_threshold` | Horizon 重要性评分阈值，当前为 7 分 |
| `filtering.time_window_hours` | 每次采集窗口，当前为 24 小时 |
| `filtering.max_items` | 每期最多进入日报的条目数 |
| `filtering.category_groups` | 按“深度学习优先 / 选题优先 / 工具观察”做配额 |

## 信息源覆盖

**国外**：HN、TechCrunch AI、OpenAI Blog、ArXiv AI、GitHub AI 仓库 Release

**国内**：智谱AI

**重点领域**：AI Agent 框架、LLM 新模型、自动化工具链、行业动态

## 公开发布链路

- 运行配置：`data/config.github.json`
- GitHub Action：`.github/workflows/daily-summary.yml`
- 本地/服务器手动发布脚本：`scripts/publish_daily.py`、`scripts/daily-run.sh`
- Markdown 源文件：`docs/_posts/YYYY-MM-DD-summary-{zh,en}.md`
- HTML 主页：`docs/index.html`
- 每日 HTML：`docs/daily/YYYY-MM-DD-{zh,en}.html`
- Cloudflare Pages 输出目录：`docs`

GitHub 仓库 Secrets 需要配置：

```env
HORIZON_AI_API_KEY=你的自由模型key
HORIZON_AI_BASE_URL=https://你的模型网关/v1
HORIZON_AI_MODEL=你的模型名
```

可选配置 `HORIZON_GITHUB_TOKEN`，用于提高 GitHub API 访问额度；不配置时 workflow 使用 GitHub Actions 内置 token。

日常口径：

- 用户说“收集资讯”时，默认执行完整发布链路。
- 如果只想本地生成、不发布，需要明确说“只本地收集”。
- GitHub 只提交公开产物：`docs/index.html`、`docs/daily/`、`docs/data/`、`docs/_posts/`。
- `.env`、`data/config.json` 和真实密钥永远不提交。

## 维护规则

1. 新增信源先登记到 `AI资讯信源清单.md`，标注等级、用途偏向和优先级。
2. 只有 `source_type = rss/github_repo/community` 且抓取方式已支持的信源，才同步到运行配置 `data/config.json`。
3. 聚合源只做线索发现；进入学习笔记或正式内容前，要追溯到官方、论文、仓库或一手发布。
4. 每周复盘一次低质量/失效信源，连续 4 周无有效条目可降级或停用。

## 自由模型接入

当前 `data/config.json` 已使用通用 `custom` 模式，适用于任何 OpenAI-compatible `/v1/chat/completions` 网关。

在 `.env` 中配置：

```env
HORIZON_AI_API_KEY=你的key
HORIZON_AI_BASE_URL=https://你的模型网关/v1
HORIZON_AI_MODEL=你的模型名
```

例如使用本地或内网网关时，只需要替换 `HORIZON_AI_BASE_URL` 和 `HORIZON_AI_MODEL`，不用改代码。
