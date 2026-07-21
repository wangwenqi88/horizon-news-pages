"""Build static HTML pages for Cloudflare Pages.

The Horizon pipeline writes Markdown posts to docs/_posts. This script turns
those posts into plain HTML files that can be committed to GitHub and published
directly by Cloudflare Pages without a Jekyll build step.
"""

from __future__ import annotations

import html
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
POSTS_DIR = DOCS_DIR / "_posts"
DAILY_DIR = DOCS_DIR / "daily"
DATA_DIR = DOCS_DIR / "data"
DETAIL_DIR = DATA_DIR / "news-detail"
READ_DIR = DOCS_DIR / "read"
ALLOWED_HTML_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "details",
    "em",
    "h2",
    "h3",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "summary",
    "ul",
}
ALLOWED_HTML_ATTRS = {
    "a": {"href", "target", "rel"},
    "span": {"class", "data-tier"},
}
SAFE_URL_PREFIXES = ("http://", "https://", "mailto:", "#", "../", "/")
SAFE_SOURCE_URL_PREFIXES = ("http://", "https://")


@dataclass(frozen=True)
class Post:
    title: str
    date: str
    lang: str
    source_path: Path
    output_name: str
    body_markdown: str
    body_html: str


@dataclass(frozen=True)
class NewsItem:
    id: str
    date: str
    lang: str
    title: str
    category: str
    source: str
    source_url: str
    source_tier: str
    group: str
    score: str
    summary: str
    manager_takeaway: str
    actions: list[str]
    risks: list[str]
    tags: list[str]
    detail_url: str
    html_url: str
    read_url: str
    section_markdown: str
    section_html: str
    audio_url: str = ""


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    raw_meta = text[4:end].strip()
    body = text[end + len("\n---\n") :]
    meta: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def post_from_markdown(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    date = meta.get("date") or path.name[:10]
    lang = meta.get("lang") or ("zh" if "-zh" in path.stem else "en")
    title = meta.get("title") or f"Horizon Summary: {date} ({lang.upper()})"

    body_html = markdown.markdown(
        body,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )
    return Post(
        title=title,
        date=date,
        lang=lang,
        source_path=path,
        output_name=f"{date}-{lang}.html",
        body_markdown=body,
        body_html=body_html,
    )


def sanitize_html_fragment(value: str) -> str:
    """Keep readable Markdown HTML while removing executable/raw HTML risk."""
    soup = BeautifulSoup(value, "html.parser")
    for tag in list(soup.find_all(True)):
        if tag.name not in ALLOWED_HTML_TAGS:
            tag.unwrap()
            continue

        allowed_attrs = ALLOWED_HTML_ATTRS.get(tag.name, set())
        for attr in list(tag.attrs):
            if attr not in allowed_attrs:
                del tag.attrs[attr]

        if tag.name == "a":
            href = str(tag.get("href", "")).strip()
            if not href or not href.lower().startswith(SAFE_URL_PREFIXES):
                tag.unwrap()
                continue
            if href.startswith(("http://", "https://")):
                tag["target"] = "_blank"
                tag["rel"] = "noopener noreferrer"
    return str(soup)


def sanitize_source_url(value: str) -> str:
    value = value.strip()
    if value.lower().startswith(SAFE_SOURCE_URL_PREFIXES):
        return value
    return ""


def load_posts() -> list[Post]:
    if not POSTS_DIR.exists():
        return []
    posts = [post_from_markdown(path) for path in POSTS_DIR.glob("*.md")]
    return sorted(posts, key=lambda post: (post.date, post.lang), reverse=True)


def page_shell(
    title: str,
    body: str,
    css_href: str,
    js_src: str,
    *,
    active: str = "",
    body_attr: str = "",
    prefix: str = "",
) -> str:
    escaped_title = html.escape(title)
    root = prefix

    def nav_class(name: str) -> str:
        return ' class="active"' if name == active else ""

    daily_link = ""
    if active != "daily":
        daily_link = f'<a class="header-daily-link" href="{root}daily/{html.escape(latest_daily_output())}">完整日报</a>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="description" content="AI 资讯精读">
  <link rel="stylesheet" href="{css_href}">
</head>
<body{body_attr}>
  <header class="site-header">
    <div class="nav-shell">
      <a class="brand" href="{root}index.html"><span class="brand-mark">H</span><span><strong>Horizon News</strong><small>AI 资讯精读</small></span></a>
      <nav class="primary-nav" aria-label="主导航">
        <a{nav_class("home")} href="{root}index.html">今日</a>
        <a{nav_class("firsthand")} href="{root}firsthand.html">一手资讯</a>
        <a{nav_class("insights")} href="{root}insights.html">专家洞察</a>
        <a href="{root}index.html#history">历史日报</a>
      </nav>
      <div class="header-actions">{daily_link}<span class="saved-counter" title="收藏数量"><span aria-hidden="true">☆</span><span data-saved-count>0</span></span></div>
    </div>
  </header>
  <main>
{body}
  </main>
  <script src="{js_src}" defer></script>
</body>
</html>
"""


def latest_daily_output() -> str:
    posts = load_posts()
    latest = next((post for post in posts if post.lang == "zh"), posts[0] if posts else None)
    return latest.output_name if latest else ""


def build_post_page(post: Post, all_posts: list[Post]) -> str:
    other_lang = "en" if post.lang == "zh" else "zh"
    sibling = next(
        (item for item in all_posts if item.date == post.date and item.lang == other_lang),
        None,
    )
    sibling_link = ""
    if sibling:
        label = "English" if sibling.lang == "en" else "中文"
        sibling_link = f'<a href="{html.escape(sibling.output_name)}">{label}</a>'

    body = f"""    <nav class="static-nav">
      <a href="../index.html">返回首页</a>
      {sibling_link}
    </nav>
    <article class="digest-page" data-lang="{html.escape(post.lang)}">
      <p class="eyebrow">{html.escape(post.date)} · {html.escape(post.lang.upper())}</p>
      <h1>{html.escape(post.title)}</h1>
      {post.body_html}
    </article>
"""
    return page_shell(post.title, body, "../assets/css/horizon.css", "../assets/js/horizon.js", active="daily", prefix="../")


def post_count(posts: list[Post], lang: str) -> int:
    return sum(1 for post in posts if post.lang == lang)


def build_history_list(posts: list[Post], latest: Post) -> str:
    zh_posts = [post for post in posts if post.lang == "zh" and post.output_name != latest.output_name]
    if not zh_posts:
        return '<p class="history-empty">暂无历史日报。</p>'

    entries = []
    for post in zh_posts:
        entries.append(
            f"""        <li>
          <a href="daily/{html.escape(post.output_name)}">
            <span>{html.escape(post.date)}</span>
            <strong>{html.escape(post.title)}</strong>
          </a>
        </li>"""
        )
    return "      <ul class=\"history-list\">\n" + "\n".join(entries) + "\n      </ul>"


def build_recent_reports(posts: list[Post], latest: Post) -> str:
    zh_posts = [post for post in posts if post.lang == "zh" and post.output_name != latest.output_name][:3]
    if not zh_posts:
        return '<p class="history-empty">暂无历史日报。</p>'
    entries = []
    for post in zh_posts:
        month_day = post.date[5:].replace("-", ".")
        title = post.title.replace("Horizon Summary:", "").strip()
        entries.append(
            f'<a href="daily/{html.escape(post.output_name)}"><time>{html.escape(month_day)}</time><span>{html.escape(title)}</span></a>'
        )
    return "\n".join(entries)


def weekday_label(date_value: str) -> str:
    try:
        return datetime.fromisoformat(date_value).strftime("%a").upper()
    except ValueError:
        return "TODAY"


def dotted_date(date_value: str) -> str:
    return date_value.replace("-", ".")


def build_index(posts: list[Post]) -> str:
    """Render a homepage with selected content and historical navigation."""
    latest = next((post for post in posts if post.lang == "zh"), None)
    if latest is None and posts:
        latest = posts[0]
    if latest is None:
        body = """    <h1>AI 资讯精读</h1>
    <p>暂无内容。</p>
"""
        return page_shell("AI 资讯精读", body, "assets/css/horizon.css", "assets/js/horizon.js")

    sibling = next(
        (item for item in posts if item.date == latest.date and item.lang == "en"),
        None,
    )
    sibling_link = ""
    if sibling:
        sibling_link = f'<a href="daily/{html.escape(sibling.output_name)}">English</a>'

    items = [item for item in extract_news_items([latest]) if item.lang == latest.lang]
    news_items = [item for item in items if item.group == "first_hand_news"]
    insight_items = [item for item in items if item.group == "practice_insight"]
    highlights = sorted(
        items,
        key=lambda item: float(item.score or 0),
        reverse=True,
    )[:3]
    recent_html = build_recent_reports(posts, latest)
    history_count = max(post_count(posts, "zh") - 1, 0)
    body = f"""    <section class="briefing" id="today">
      <div class="section-shell briefing-grid">
        <div>
          <div class="date-line"><span>{html.escape(weekday_label(latest.date))}</span><time>{html.escape(dotted_date(latest.date))}</time><span>第 {history_count + 1} 期</span>{sibling_link}</div>
          <p class="kicker">今日编辑判断</p>
          <h1>AI 系统的竞争，正在从“信息更新”转向“可信实操”。</h1>
          <p class="standfirst">今天的 Horizon News 用两条轨道处理资讯：一手资讯帮助快速掌握行业变化，实战与专家洞察沉淀可复用方法、项目经验和技术判断。</p>
        </div>
        <div class="briefing-stats">
          <div><strong>{len(items)}</strong><span>入选</span></div>
          <div><strong>{len(news_items)}</strong><span>一手</span></div>
          <div><strong>{len(insight_items)}</strong><span>洞察</span></div>
          <div><strong>{history_count}</strong><span>历史</span></div>
        </div>
      </div>
    </section>
    <section class="recent-reports" id="history">
      <div class="section-shell recent-shell">
        <div class="recent-label"><p class="kicker">Recent reports</p><h2>近期日报</h2></div>
        <div class="recent-list">{recent_html}</div>
        <a class="all-history-link" href="daily/{html.escape(latest.output_name)}">查看完整日报 →</a>
      </div>
    </section>
    <section class="must-read section-shell">
      <div class="section-heading">
        <div><p class="kicker">Editor’s pick</p><h2>今日必读</h2></div>
        <p>先读这 3 条，掌握今日主线</p>
      </div>
      {render_highlight_cards(highlights)}
    </section>
    <section class="intelligence section-shell">
      <div class="section-heading">
        <div><p class="kicker">Selected intelligence</p><h2>一手资讯精选</h2></div>
        <p>精选 4 / {len(news_items)} · 每条含可展开 AI 总结</p>
      </div>
      <div class="firsthand-list compact-list">{render_firsthand_cards(news_items, limit=4)}</div>
      <a class="track-more-link" href="firsthand.html">查看全部 {len(news_items)} 条一手资讯 →</a>
      <div class="section-heading home-insight-heading">
        <div><p class="kicker">Practitioner insight</p><h2>专家洞察精选</h2></div>
        <p>精选 2 / {len(insight_items)}</p>
      </div>
      <div class="insights-grid">{render_expert_cards(insight_items, limit=2)}</div>
      <a class="track-more-link" href="insights.html">查看全部 {len(insight_items)} 条专家洞察 →</a>
      <div class="daily-cta"><div><span>FULL DAILY</span><strong>查看当日完整日报和原始分组</strong></div><a href="daily/{html.escape(latest.output_name)}">进入完整日报 →</a></div>
    </section>
"""
    return page_shell("Horizon News | 今日", body, "assets/css/horizon.css", "assets/js/horizon.js", active="home", body_attr=' data-page="home"')


def root_href(url: str) -> str:
    return url.lstrip("/") if url.startswith("/") else url


def render_item_cards(items: list[NewsItem], *, limit: int, compact: bool = False) -> str:
    if not items:
        return '<p class="history-empty">暂无内容。</p>'
    cards = []
    for item in items[:limit]:
        summary = html.escape(item.summary)
        score = html.escape(item.score or "?")
        detail = ""
        if not compact:
            detail = f"""          <details>
            <summary>AI 总结</summary>
            <p>{summary}</p>
          </details>"""
        else:
            detail = f"          <p>{summary}</p>"
        cards.append(
            f"""        <article class="portal-card">
          <div class="portal-card-meta">
            <span>{html.escape(item.source)}</span>
            <strong>{score}/10</strong>
          </div>
          <h3><a href="{html.escape(root_href(item.read_url))}">{html.escape(item.title)}</a></h3>
{detail}
          <div class="portal-card-actions">
            <a href="{html.escape(root_href(item.read_url))}">AI 精读</a>
            <a href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">原文</a>
          </div>
        </article>"""
        )
    return "\n".join(cards)


def score_value(score: str) -> int:
    try:
        return max(0, min(100, int(float(score) * 10)))
    except ValueError:
        return 60


def render_value_pair(item: NewsItem) -> str:
    score = score_value(item.score or "")
    learning = min(100, score + (8 if item.group == "practice_insight" else 0))
    return f"""<div class="value-pair">
          <div class="value-row"><span>选题</span><div class="value-bar"><span style="width:{score}%"></span></div><b>{score}</b></div>
          <div class="value-row learning"><span>学习</span><div class="value-bar"><span style="width:{learning}%"></span></div><b>{learning}</b></div>
        </div>"""


def render_highlight_cards(items: list[NewsItem]) -> str:
    if not items:
        return '<p class="history-empty">暂无内容。</p>'
    lead = items[0]
    side_items = items[1:3]
    visuals = ["visual-robot", "visual-review", "visual-system"]
    side_html = []
    for index, item in enumerate(side_items, start=1):
        side_html.append(
            f"""<article class="side-story">
          <div class="story-visual {visuals[index]}"><div class="mini-chart"><span style="height:86%"></span><span style="height:64%"></span><span style="height:38%"></span><span style="height:52%"></span></div><small>{html.escape(item.source_tier)} TIER / {html.escape(item.category.upper())}</small></div>
          <div class="side-story-body">
            <div class="story-meta"><span>{html.escape(item.category)}</span><span>{html.escape(item.score or "?")} 分</span></div>
            <h3>{html.escape(item.title)}</h3>
            <p>{html.escape(item.summary)}</p>
            <a href="{html.escape(root_href(item.read_url))}" aria-label="进入 AI 精读">→</a>
          </div>
        </article>"""
        )
    while len(side_html) < 2:
        side_html.append("")
    return f"""<div class="must-grid">
        <article class="lead-story">
          <div class="story-visual {visuals[0]}"><div class="visual-label"><span>{html.escape(lead.category.upper())}</span><strong>{html.escape(lead.source_tier)}</strong></div><div class="motion-map"><span></span><span></span><span></span><span></span><span></span><span></span></div></div>
          <div class="story-overlay">
            <div class="story-meta"><span>{html.escape(lead.category)}</span><span>{html.escape(lead.score or "?")} 分</span></div>
            <h3>{html.escape(lead.title)}</h3>
            <p>{html.escape(lead.summary)}</p>
            <div class="story-actions"><a href="{html.escape(root_href(lead.read_url))}">进入 AI 精读 →</a><button class="icon-button" data-save-id="{html.escape(lead.id)}" type="button" aria-label="收藏"><span class="icon-bookmark">☆</span></button></div>
          </div>
        </article>
        {side_html[0]}
        {side_html[1]}
      </div>"""


def render_firsthand_cards(items: list[NewsItem], *, limit: int | None = None) -> str:
    selected = items if limit is None else items[:limit]
    if not selected:
        return '<p class="history-empty">暂无内容。</p>'
    rendered = []
    for index, item in enumerate(selected, start=1):
        rendered.append(
            f"""<article class="firsthand-card" data-topic="{html.escape(item.category)}">
          <div class="firsthand-number">{index:02d}</div>
          <div class="firsthand-content">
            <div class="card-meta"><span>{html.escape(item.source)}</span><span>{html.escape(item.source_tier)} 级信源</span><span class="score-chip">{html.escape(item.score or "?")} 分</span></div>
            <h2><a href="{html.escape(root_href(item.read_url))}">{html.escape(item.title)}</a></h2>
            {render_value_pair(item)}
            <details class="ai-summary"><summary class="summary-toggle">AI 总结 <b>⌄</b></summary><div class="summary-panel"><p>{html.escape(item.summary)}</p></div></details>
            <div class="card-actions"><a class="primary-action" href="{html.escape(root_href(item.read_url))}">AI 精读 →</a><a class="secondary-action" href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">原文</a><button class="item-save" data-save-id="{html.escape(item.id)}" type="button" aria-label="收藏">☆</button></div>
          </div>
        </article>"""
        )
    return "\n".join(rendered)


def render_expert_cards(items: list[NewsItem], *, limit: int | None = None) -> str:
    selected = items if limit is None else items[:limit]
    if not selected:
        return '<p class="history-empty">暂无内容。</p>'
    rendered = []
    for index, item in enumerate(selected, start=1):
        actions = item.actions[:3] or ["结合自己的项目场景复盘是否可用。"]
        risks = item.risks[:2] or ["关键判断仍需回看原文验证。"]
        rendered.append(
            f"""<article class="expert-card">
          <div class="expert-top"><span class="expert-number">{index:02d}</span><div class="card-meta"><span>{html.escape(item.source)}</span><span class="score-chip">{html.escape(item.score or "?")} 分</span></div></div>
          <h2><a href="{html.escape(root_href(item.read_url))}">{html.escape(item.title)}</a></h2>
          <p class="expert-summary">{html.escape(item.summary)}</p>
          <blockquote><strong>Horizon 判断</strong>{html.escape(item.manager_takeaway)}</blockquote>
          <div class="expert-grid"><div><h3>行动建议</h3><ol>{"".join(f"<li>{html.escape(action)}</li>" for action in actions)}</ol></div><div><h3>风险提醒</h3><ol>{"".join(f"<li>{html.escape(risk)}</li>" for risk in risks)}</ol></div></div>
          <div class="card-actions"><a class="primary-action" href="{html.escape(root_href(item.read_url))}">AI 精读 →</a><a class="secondary-action" href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">原文</a><button class="item-save" data-save-id="{html.escape(item.id)}" type="button" aria-label="收藏">☆</button></div>
        </article>"""
        )
    return "\n".join(rendered)


def build_track_page(post: Post, group: str, title: str, subtitle: str) -> str:
    items = [
        item for item in extract_news_items([post])
        if item.lang == post.lang and item.group == group
    ]
    if group == "first_hand_news":
        list_html = f"""<div class="list-toolbar" role="search"><label><span aria-hidden="true">⌕</span><input id="news-search" type="search" placeholder="搜索标题、来源、专题或 AI 总结"></label><select id="topic-filter" aria-label="专题筛选"><option value="all">全部专题</option></select><strong id="list-count">显示 {len(items)} / {len(items)} 条</strong></div><div id="firsthand-list" class="firsthand-list">{render_firsthand_cards(items)}</div>"""
        active = "firsthand"
        hero_class = "list-hero"
    else:
        list_html = f'<div id="insights-list" class="insights-grid full-insights">{render_expert_cards(items)}</div>'
        active = "insights"
        hero_class = "list-hero insight-hero"
    body = f"""    <section class="{hero_class}">
      <div class="section-shell">
        <p class="kicker">{html.escape(post.date)} · {html.escape(post.lang.upper())}</p>
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(subtitle)}</p>
      </div>
    </section>
    <section class="section-shell list-page">
      {list_html}
      <div class="daily-cta"><div><span>FULL DAILY</span><strong>查看当日完整日报和原始分组</strong></div><a href="daily/{html.escape(post.output_name)}">进入完整日报 →</a></div>
    </section>
"""
    return page_shell(title, body, "assets/css/horizon.css", "assets/js/horizon.js", active=active)


def render_full_item_list(items: list[NewsItem]) -> str:
    if not items:
        return '<p class="history-empty">暂无内容。</p>'
    rendered = []
    for item in items:
        rendered.append(
            f"""      <article class="full-item">
        <div class="portal-card-meta">
          <span>{html.escape(item.source)}</span>
          <strong>{html.escape(item.score or "?")}/10</strong>
        </div>
        <h2><a href="{html.escape(root_href(item.read_url))}">{html.escape(item.title)}</a></h2>
        <p>{html.escape(item.summary)}</p>
        <div class="portal-card-actions">
          <a href="{html.escape(root_href(item.read_url))}">AI 精读</a>
          <a href="{html.escape(root_href(item.html_url))}">日报定位</a>
          <a href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">原文</a>
        </div>
      </article>"""
        )
    return "\n".join(rendered)


def extract_read_text(item: NewsItem, label: str) -> str:
    return extract_labeled_text(item.section_markdown, label)


def build_read_page(item: NewsItem) -> str:
    ai_view = extract_read_text(item, "AI 观点") or extract_read_text(item, "AI View") or item.manager_takeaway
    practical = (
        extract_read_text(item, "可复用方法")
        or extract_read_text(item, "Practical Takeaways")
        or ""
    )
    implementation = (
        extract_read_text(item, "实操要点")
        or extract_read_text(item, "Implementation Notes")
        or ""
    )
    application = (
        extract_read_text(item, "我可以怎么用")
        or extract_read_text(item, "How I Can Use This")
        or ""
    )
    risks = item.risks or ["该内容由 AI 基于公开资料转译和分析，关键事实仍应以原文和官方资料为准。"]
    tags = "、".join(item.tags) if item.tags else "AI"
    sections = [
        ("guide", "内容导读", f"<p>{html.escape(item.summary)}</p>"),
        (
            "facts",
            "核心事实",
            f"<ul><li>来源：{html.escape(item.source)}</li><li>评分：{html.escape(item.score or '?')}/10</li><li>标签：{html.escape(tags)}</li></ul>",
        ),
        ("translation", "完整 AI 转译", item.section_html),
        ("context", "背景与上下文", f"<p>{html.escape(item.manager_takeaway)}</p>"),
        ("importance", "为什么重要", f"<p>{html.escape(item.manager_takeaway)}</p>"),
        ("view", "AI 观点", f"<p>{html.escape(ai_view)}</p>"),
        (
            "actions",
            "可执行建议",
            "<ul>"
            + "".join(f"<li>{html.escape(action)}</li>" for action in item.actions)
            + "</ul>"
            + (f"<p>{html.escape(practical)}</p>" if practical else "")
            + (f"<p>{html.escape(implementation)}</p>" if implementation else "")
            + (f"<p>{html.escape(application)}</p>" if application else ""),
        ),
        ("risks", "风险与限制", "<ul>" + "".join(f"<li>{html.escape(risk)}</li>" for risk in risks) + "</ul>"),
        (
            "source",
            "来源信息",
            f'<p><a href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">查看原文</a></p>'
            f'<p><a href="../{html.escape(root_href(item.html_url))}">返回当日日报定位</a></p>',
        ),
    ]
    nav = "\n".join(
        f'        <a href="#{section_id}">{html.escape(label)}</a>'
        for section_id, label, _ in sections
    )
    body_sections = "\n".join(
        f"""        <section id="{section_id}" class="read-section">
          <h2>{html.escape(label)}</h2>
          {content}
        </section>"""
        for section_id, label, content in sections
    )
    body = f"""    <article class="section-shell read-article">
      <section class="read-hero">
        <p class="kicker">{html.escape(item.date)} · Horizon News AI 精读</p>
        <h1>{html.escape(item.title)}</h1>
        <p class="read-disclaimer">Horizon News 的完整 AI 转译、结构化整理与分析，不等同于原作者全文；引用、研究和决策请回看原文。</p>
        <div class="read-meta"><span>{html.escape(item.source)}</span><span>{html.escape(item.source_tier)} 级信源</span><span>{html.escape(item.score or "?")} 分</span><span>{html.escape(tags)}</span></div>
        <a class="source-cta" href="{html.escape(item.source_url)}" target="_blank" rel="noopener noreferrer">查看原文 →</a>
      </section>
      <div class="read-layout">
        <aside class="read-toc read-nav" aria-label="本页内容">
          <strong>本页内容</strong>
{nav}
        </aside>
        <div class="read-body">
{body_sections}
        </div>
      </div>
    </article>
"""
    return page_shell(item.title, body, "../assets/css/horizon.css", "../assets/js/horizon.js", prefix="../")


def strip_markdown(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def slugify(value: str) -> str:
    ascii_value = re.sub(r"[^a-z0-9-]+", "-", value.lower())
    ascii_value = re.sub(r"-+", "-", ascii_value).strip("-")
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    if ascii_value:
        return f"{ascii_value[:40]}-{digest}"
    return f"item-{digest}"


def extract_heading(markdown_text: str) -> tuple[str, str]:
    heading = markdown_text.splitlines()[0].strip()
    match = re.match(r"#{2,3}\s+\[([^\]]+)\]\(([^)]+)\)(?:\s+⭐️\s*([0-9.]+)\/10)?", heading)
    if match:
        return strip_markdown(match.group(1)), match.group(2).strip()
    return strip_markdown(heading.lstrip("# ")), ""


def extract_score(markdown_text: str) -> str:
    heading = markdown_text.splitlines()[0].strip()
    match = re.search(r"⭐️\s*([0-9.]+)\/10", heading)
    if match:
        return match.group(1)
    return ""


def extract_labeled_text(section: str, label: str) -> str:
    pattern = rf"\*\*{re.escape(label)}\*\*\s*[:：]\s*(.*?)(?=\n\n\*\*|\n\n<details|\n\n---|\Z)"
    match = re.search(pattern, section, flags=re.S)
    if not match:
        return ""
    return strip_markdown(match.group(1))


def extract_tags(section: str) -> list[str]:
    text = extract_labeled_text(section, "标签") or extract_labeled_text(section, "Tags")
    if not text:
        return []
    raw_tags = re.split(r"[,，、]+", text)
    tags = []
    for raw_tag in raw_tags:
        tag = raw_tag.strip().strip("`").lstrip("#").strip()
        if tag:
            tags.append(tag)
    return tags


def extract_source(section: str) -> str:
    for line in section.splitlines():
        stripped = strip_markdown(line)
        if "·" in stripped and re.match(r"^(rss|reddit|github|hackernews|hn|telegram|twitter)\b", stripped, re.I):
            return stripped.split("·", 1)[0].strip()
    return "unknown"


def infer_source_tier(source: str, source_url: str) -> str:
    if any(domain in source_url for domain in ("github.com", "arxiv.org", "openai.com", "anthropic.com")):
        return "S"
    if source.lower() in {"hackernews", "hn", "reddit"}:
        return "B"
    if source.lower() == "rss":
        return "A"
    return "B"


def extract_summary(section: str) -> str:
    lines = section.splitlines()
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("<") or stripped.startswith("**") or stripped.startswith("---"):
            continue
        return strip_markdown(stripped)
    return ""


def build_actions(lang: str, tags: list[str]) -> list[str]:
    if lang == "zh":
        subject = "、".join(tags[:2]) if tags else "这个方向"
        return [
            f"判断团队近期是否有和{subject}相关的试用场景。",
            "核对数据安全、权限边界和成本变化。",
            "如果价值明确，安排一次小范围验证并记录复盘。"
        ]
    subject = ", ".join(tags[:2]) if tags else "this topic"
    return [
        f"Check whether the team has a near-term pilot scenario for {subject}.",
        "Review data security, permission boundaries, and cost impact.",
        "Run a small validation and capture lessons if the value is clear."
    ]


def group_from_prefix(prefix: str) -> str:
    group = "first_hand_news"
    for match in re.finditer(r"^##\s+(.+)$", prefix, flags=re.M):
        heading = strip_markdown(match.group(1))
        if "实战" in heading or "Practice" in heading:
            group = "practice_insight"
        elif "一手" in heading or "First-Hand" in heading:
            group = "first_hand_news"
    return group


def split_news_sections(post: Post) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^#{2,3}\s+\[", post.body_markdown))
    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(post.body_markdown)
        section = post.body_markdown[start:end].strip()
        if section:
            sections.append((group_from_prefix(post.body_markdown[:start]), section))
    return sections


def extract_news_items(posts: list[Post]) -> list[NewsItem]:
    items: list[NewsItem] = []
    for post in posts:
        for index, (group, section) in enumerate(split_news_sections(post), start=1):
            title, source_url = extract_heading(section)
            source_url = sanitize_source_url(source_url)
            score = extract_score(section)
            tags = extract_tags(section)
            category = tags[0] if tags else "AI"
            source = extract_source(section)
            item_id = f"{post.date}-{post.lang}-{index:02d}-{slugify(title)}"
            detail_url = f"/data/news-detail/{item_id}.json"
            html_url = f"/daily/{post.output_name}#item-{index}"
            read_url = f"/read/{item_id}.html"
            summary = extract_summary(section)
            manager_takeaway = (
                extract_labeled_text(section, "背景")
                or extract_labeled_text(section, "Background")
                or summary
            )
            risks = []
            discussion = extract_labeled_text(section, "社区讨论") or extract_labeled_text(section, "Discussion")
            if discussion:
                risks.append(discussion)
            items.append(
                NewsItem(
                    id=item_id,
                    date=post.date,
                    lang=post.lang,
                    title=title,
                    category=category,
                    source=source,
                    source_url=source_url,
                    source_tier=infer_source_tier(source, source_url),
                    group=group,
                    score=score,
                    summary=summary,
                    manager_takeaway=manager_takeaway,
                    actions=build_actions(post.lang, tags),
                    risks=risks,
                    tags=tags,
                    detail_url=detail_url,
                    html_url=html_url,
                    read_url=read_url,
                    section_markdown=section,
                    section_html=sanitize_html_fragment(
                        markdown.markdown(
                            section,
                            extensions=["extra", "sane_lists"],
                            output_format="html5",
                        )
                    ),
                )
            )
    return items


def clean_old_data_files() -> None:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    for path in DETAIL_DIR.glob("*.json"):
        path.unlink()


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_data_files(posts: list[Post]) -> None:
    clean_old_data_files()
    items = extract_news_items(posts)
    now = datetime.now(timezone.utc).isoformat()
    index_payload = {
        "updated_at": now,
        "source": "horizon-news",
        "items": [
            {
                "id": item.id,
                "date": item.date,
                "lang": item.lang,
                "title": item.title,
                "category": item.category,
                "source": item.source,
                "source_tier": item.source_tier,
                "group": item.group,
                "score": item.score,
                "summary": item.summary,
                "manager_takeaway": item.manager_takeaway,
                "detail_url": item.detail_url,
                "html_url": item.html_url,
                "read_url": item.read_url,
                "audio_url": item.audio_url,
                "tags": item.tags,
            }
            for item in items
        ],
    }
    write_json(DATA_DIR / "news-index.json", index_payload)
    for item in items:
        write_json(
            DETAIL_DIR / f"{item.id}.json",
            {
                "id": item.id,
                "date": item.date,
                "lang": item.lang,
                "title": item.title,
                "source": item.source,
                "source_url": item.source_url,
                "source_tier": item.source_tier,
                "published_at": item.date,
                "category": item.category,
                "group": item.group,
                "score": item.score,
                "summary": item.summary,
                "what_happened": item.summary,
                "why_it_matters": item.manager_takeaway,
                "manager_takeaway": item.manager_takeaway,
                "actions": item.actions,
                "risks": item.risks,
                "audio_url": item.audio_url,
                "html_url": item.html_url,
                "read_url": item.read_url,
                "tags": item.tags,
            },
        )


def clean_old_daily_pages() -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    for path in DAILY_DIR.glob("*.html"):
        path.unlink()


def clean_old_read_pages() -> None:
    READ_DIR.mkdir(parents=True, exist_ok=True)
    for path in READ_DIR.glob("*.html"):
        path.unlink()


def build() -> None:
    posts = load_posts()
    clean_old_daily_pages()
    clean_old_read_pages()
    for post in posts:
        (DAILY_DIR / post.output_name).write_text(
            build_post_page(post, posts),
            encoding="utf-8",
            newline="\n",
        )
    (DOCS_DIR / "index.html").write_text(
        build_index(posts),
        encoding="utf-8",
        newline="\n",
    )
    latest_zh = next((post for post in posts if post.lang == "zh"), None)
    if latest_zh:
        (DOCS_DIR / "firsthand.html").write_text(
            build_track_page(
                latest_zh,
                "first_hand_news",
                "一手资讯速递",
                "15 条一手动态、发布、论文和产品更新，保留原文入口和 AI 摘要。",
            ),
            encoding="utf-8",
            newline="\n",
        )
        (DOCS_DIR / "insights.html").write_text(
            build_track_page(
                latest_zh,
                "practice_insight",
                "实战与专家洞察",
                "5 条偏实操、项目经验、专家观点和方法沉淀的深读内容。",
            ),
            encoding="utf-8",
            newline="\n",
        )
    for item in extract_news_items(posts):
        (READ_DIR / f"{item.id}.html").write_text(
            build_read_page(item),
            encoding="utf-8",
            newline="\n",
        )
    build_data_files(posts)
    print(
        f"Built {len(posts)} static posts into {DAILY_DIR}, "
        f"read pages into {READ_DIR}, and JSON into {DATA_DIR}"
    )


if __name__ == "__main__":
    build()
