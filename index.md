---
layout: default
title: AI 资讯精读
---

# AI 资讯精读

<div id="lang-zh" class="lang-section" markdown="1">

每天自动收集 AI Agent、开发者工具、开源生态和工程实践资讯，筛选后生成可追溯来源的精读页面。

<section class="news-hero" markdown="1">
  <div>
    <p class="eyebrow">Daily AI Reading</p>
    <h2>按日期查看每日精读</h2>
    <p>点击日期进入当天页面，查看重点资讯、背景解释、社区讨论和参考链接。</p>
  </div>
  <div class="news-hero-stats">
    <span>{{ site.posts | where: "lang", "zh" | size }}</span>
    <small>中文精读</small>
  </div>
</section>

## 资讯主页 <a class="rss-icon" href="{{ '/feed-zh.xml' | relative_url }}" aria-label="订阅中文"><svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M128.081 415.959c0 35.369-28.672 64.041-64.041 64.041S0 451.328 0 415.959s28.672-64.041 64.041-64.041 64.04 28.673 64.04 64.041zm175.66 47.25c-8.354-154.6-132.185-278.587-286.95-286.95C7.656 175.765 0 183.105 0 192.253v48.069c0 8.415 6.49 15.472 14.887 16.018 111.832 7.284 201.473 96.702 208.772 208.772.547 8.397 7.604 14.887 16.018 14.887h48.069c9.149.001 16.489-7.655 15.995-16.79zm144.249.288C439.596 229.677 251.465 40.445 16.503 32.01 7.473 31.686 0 38.981 0 48.016v48.068c0 8.625 6.835 15.645 15.453 15.999 191.179 7.839 344.627 161.316 352.465 352.465.353 8.618 7.373 15.453 15.999 15.453h48.068c9.034-.001 16.329-7.474 16.005-16.504z"/></svg></a>

<ul class="digest-list">
  {% assign zh_posts = site.posts | where: "lang", "zh" %}
  {% for post in zh_posts %}
    <li class="digest-item">
      <a class="digest-date" href="{{ post.url | relative_url }}">{{ post.date | date: "%Y-%m-%d" }}</a>
      <span class="digest-title">{{ post.title | default: "AI 资讯精读" }}</span>
    </li>
  {% else %}
    <li><em>暂无内容</em></li>
  {% endfor %}
</ul>

## 维护入口

- [配置指南](configuration) — AI 提供商、信息源、过滤规则与环境变量替换
- [信息源采集器](scrapers) — Horizon 如何从 GitHub、Hacker News、RSS、Reddit 采集内容
- [评分系统](scoring) — 基于 AI 的内容分析与 0-10 评分体系
- [GitHub Pages 部署](github-pages-deploy) — 仓库、Secrets、定时任务和发布分支配置

</div>

<div id="lang-en" class="lang-section" markdown="1">

Daily AI reading list for agents, developer tools, open-source ecosystems, and engineering practice.

<section class="news-hero" markdown="1">
  <div>
    <p class="eyebrow">Daily AI Reading</p>
    <h2>Browse by Date</h2>
    <p>Open a date to read the curated digest, background context, discussion summary, and references.</p>
  </div>
  <div class="news-hero-stats">
    <span>{{ site.posts | where: "lang", "en" | size }}</span>
    <small>English digests</small>
  </div>
</section>

## Daily Digest <a class="rss-icon" href="{{ '/feed-en.xml' | relative_url }}" aria-label="Subscribe English"><svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M128.081 415.959c0 35.369-28.672 64.041-64.041 64.041S0 451.328 0 415.959s28.672-64.041 64.041-64.041 64.04 28.673 64.04 64.041zm175.66 47.25c-8.354-154.6-132.185-278.587-286.95-286.95C7.656 175.765 0 183.105 0 192.253v48.069c0 8.415 6.49 15.472 14.887 16.018 111.832 7.284 201.473 96.702 208.772 208.772.547 8.397 7.604 14.887 16.018 14.887h48.069c9.149.001 16.489-7.655 15.995-16.79zm144.249.288C439.596 229.677 251.465 40.445 16.503 32.01 7.473 31.686 0 38.981 0 48.016v48.068c0 8.625 6.835 15.645 15.453 15.999 191.179 7.839 344.627 161.316 352.465 352.465.353 8.618 7.373 15.453 15.999 15.453h48.068c9.034-.001 16.329-7.474 16.005-16.504z"/></svg></a>

<ul class="digest-list">
  {% assign en_posts = site.posts | where: "lang", "en" %}
  {% for post in en_posts %}
    <li class="digest-item">
      <a class="digest-date" href="{{ post.url | relative_url }}">{{ post.date | date: "%Y-%m-%d" }}</a>
      <span class="digest-title">{{ post.title | default: "AI Digest" }}</span>
    </li>
  {% else %}
    <li><em>No posts yet</em></li>
  {% endfor %}
</ul>

## Maintenance

- [Configuration Guide](configuration) — AI providers, information sources, filtering, and environment variable substitution
- [Source Scrapers](scrapers) — How Horizon collects content from GitHub, Hacker News, RSS, and Reddit
- [Scoring System](scoring) — AI-based content analysis and the 0-10 scoring scale
- [GitHub Pages Deploy](github-pages-deploy) — repository, secrets, schedule, and publishing branch setup

</div>
