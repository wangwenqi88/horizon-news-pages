"""Build static HTML pages for Cloudflare Pages.

The Horizon pipeline writes Markdown posts to docs/_posts. This script turns
those posts into plain HTML files that can be committed to GitHub and published
directly by Cloudflare Pages without a Jekyll build step.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

import markdown


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
POSTS_DIR = DOCS_DIR / "_posts"
DAILY_DIR = DOCS_DIR / "daily"


@dataclass(frozen=True)
class Post:
    title: str
    date: str
    lang: str
    source_path: Path
    output_name: str
    body_html: str


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
    def section(lang: str, title: str, description: str, empty: str) -> str:
        items = [post for post in posts if post.lang == lang]
        count = post_count(posts, lang)
        if items:
            entries = "\n".join(
                f"""      <li class="digest-item">
        <a class="digest-date" href="daily/{html.escape(post.output_name)}">{html.escape(post.date)}</a>
        <span class="digest-title">{html.escape(post.title)}</span>
      </li>"""
                for post in items
            )
        else:
            entries = f"      <li><em>{html.escape(empty)}</em></li>"

        return f"""    <div id="lang-{lang}" class="lang-section">
      <section class="news-hero">
        <div>
          <p class="eyebrow">Daily AI Reading</p>
          <h2>{html.escape(title)}</h2>
          <p>{html.escape(description)}</p>
        </div>
        <div class="news-hero-stats">
          <span>{count}</span>
          <small>{'中文精读' if lang == 'zh' else 'English digests'}</small>
        </div>
      </section>
      <h2>{'资讯主页' if lang == 'zh' else 'Daily Digest'}</h2>
      <ul class="digest-list">
{entries}
      </ul>
    </div>"""

    body = f"""    <h1>AI 资讯精读</h1>
    <p>每天自动收集 AI Agent、开发者工具、开源生态和工程实践资讯，筛选后生成可追溯来源的精读页面。</p>
{section('zh', '按日期查看每日精读', '点击日期进入当天页面，查看重点资讯、背景解释、社区讨论和参考链接。', '暂无内容')}
{section('en', 'Browse by Date', 'Open a date to read the curated digest, background context, discussion summary, and references.', 'No posts yet')}
"""
    return page_shell("AI 资讯精读", body, "assets/css/horizon.css", "assets/js/horizon.js")


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
    print(f"Built {len(posts)} static posts into {DAILY_DIR}")


if __name__ == "__main__":
    build()
