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


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
POSTS_DIR = DOCS_DIR / "_posts"
DAILY_DIR = DOCS_DIR / "daily"
DATA_DIR = DOCS_DIR / "data"
DETAIL_DIR = DATA_DIR / "news-detail"


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
    summary: str
    manager_takeaway: str
    actions: list[str]
    risks: list[str]
    tags: list[str]
    detail_url: str
    html_url: str
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


def load_posts() -> list[Post]:
    if not POSTS_DIR.exists():
        return []
    posts = [post_from_markdown(path) for path in POSTS_DIR.glob("*.md")]
    return sorted(posts, key=lambda post: (post.date, post.lang), reverse=True)


def page_shell(title: str, body: str, css_href: str, js_src: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="description" content="AI 资讯精读">
  <link rel="stylesheet" href="{css_href}">
</head>
<body>
  <header class="page-header">
    <h1 class="project-name">AI 资讯精读</h1>
    <h2 class="project-tagline">Daily AI reading, committed as static HTML.</h2>
  </header>
  <main class="main-content">
{body}
  </main>
  <script src="{js_src}" defer></script>
</body>
</html>
"""


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
    return page_shell(post.title, body, "../assets/css/horizon.css", "../assets/js/horizon.js")


def post_count(posts: list[Post], lang: str) -> int:
    return sum(1 for post in posts if post.lang == lang)


def build_index(posts: list[Post]) -> str:
    """Render the latest Chinese digest as the public homepage."""
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

    body = f"""    <nav class="static-nav">
      {sibling_link}
    </nav>
    <article class="digest-page" data-lang="{html.escape(latest.lang)}">
      <p class="eyebrow">{html.escape(latest.date)} · {html.escape(latest.lang.upper())}</p>
      <h1>{html.escape(latest.title)}</h1>
      {latest.body_html}
    </article>
"""
    return page_shell(latest.title, body, "assets/css/horizon.css", "assets/js/horizon.js")


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
    match = re.match(r"##\s+\[([^\]]+)\]\(([^)]+)\)", heading)
    if match:
        return strip_markdown(match.group(1)), match.group(2).strip()
    return strip_markdown(heading.lstrip("# ")), ""


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


def split_news_sections(post: Post) -> list[str]:
    sections = re.split(r"\n(?=##\s+\[)", post.body_markdown)
    return [section.strip() for section in sections if section.strip().startswith("## [")]


def extract_news_items(posts: list[Post]) -> list[NewsItem]:
    items: list[NewsItem] = []
    for post in posts:
        for index, section in enumerate(split_news_sections(post), start=1):
            title, source_url = extract_heading(section)
            tags = extract_tags(section)
            category = tags[0] if tags else "AI"
            source = extract_source(section)
            item_id = f"{post.date}-{post.lang}-{index:02d}-{slugify(title)}"
            detail_url = f"/data/news-detail/{item_id}.json"
            html_url = f"/daily/{post.output_name}#item-{index}"
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
                    summary=summary,
                    manager_takeaway=manager_takeaway,
                    actions=build_actions(post.lang, tags),
                    risks=risks,
                    tags=tags,
                    detail_url=detail_url,
                    html_url=html_url,
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
                "summary": item.summary,
                "manager_takeaway": item.manager_takeaway,
                "detail_url": item.detail_url,
                "html_url": item.html_url,
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
                "summary": item.summary,
                "what_happened": item.summary,
                "why_it_matters": item.manager_takeaway,
                "manager_takeaway": item.manager_takeaway,
                "actions": item.actions,
                "risks": item.risks,
                "audio_url": item.audio_url,
                "html_url": item.html_url,
                "tags": item.tags,
            },
        )


def clean_old_daily_pages() -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    for path in DAILY_DIR.glob("*.html"):
        path.unlink()


def build() -> None:
    posts = load_posts()
    clean_old_daily_pages()
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
    build_data_files(posts)
    print(f"Built {len(posts)} static posts into {DAILY_DIR} and JSON into {DATA_DIR}")


if __name__ == "__main__":
    build()
