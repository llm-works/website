#!/usr/bin/env python3
"""Build blog posts from markdown sources to HTML."""

import re
import shutil
from datetime import datetime
from html import escape
from pathlib import Path

import markdown
import yaml
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension

ROOT = Path(__file__).parent
STYLES_CSS = ROOT.parent / "styles.css"

POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — LLM Works</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="https://www.llm-works.ai/blog/{slug}/">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://www.llm-works.ai/blog/{slug}/">
  <meta property="og:site_name" content="LLM Works">
  <meta property="article:published_time" content="{date_iso}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">
  <link rel="alternate" type="application/rss+xml" title="LLM Works Blog" href="/blog/feed.xml">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x2588;</text></svg>">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PLTFCVZQ8R"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-PLTFCVZQ8R');
  </script>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js"></script>
</head>
<body class="blog-post">
  <a class="skip-link" href="#main">Skip to content</a>

  <nav aria-label="Primary">
    <div class="container">
      <a href="/" class="logo">llm-works<span>.ai</span></a>
      <ul class="nav-links">
        <li><a href="/platform/">Platform</a></li>
        <li><a href="/agents/">Agents</a></li>
        <li><a href="/story/">Story</a></li>
        <li><a href="/blog/" aria-current="page">Blog</a></li>
        <li><a href="/about/">About</a></li>
      </ul>
    </div>
  </nav>

  <label class="theme-toggle" aria-label="Toggle dark/light mode" title="Toggle dark/light mode">
    <input type="checkbox" id="theme-switch">
    <span class="slider"></span>
  </label>

  <main id="main" tabindex="-1">

  <article class="post">
    <header class="post-header">
      <div class="container">
        <p class="post-date">{date_display}</p>
        <h1>{title}</h1>
        <p class="post-byline">LLM Works</p>
      </div>
    </header>

    <div class="post-content">
      <div class="container">
{content}
      </div>
    </div>
  </article>

  </main>

  <footer>
    <div class="container">
      <span>&copy; 2026 LLM Works LLC</span>
      <div class="footer-links">
        <a href="/blog/feed.xml">RSS</a>
        <a href="/llms.txt">llms.txt</a>
        <a href="/terms.html">Terms</a>
      </div>
    </div>
  </footer>

</body>
</html>
"""

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — LLM Works</title>
  <meta name="description" content="Technical writing on AI infrastructure, agent development, and fine-tuning.">
  <link rel="canonical" href="https://www.llm-works.ai/blog/">
  <meta property="og:title" content="Blog — LLM Works">
  <meta property="og:description" content="Technical writing on AI infrastructure, agent development, and fine-tuning.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://www.llm-works.ai/blog/">
  <meta property="og:site_name" content="LLM Works">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="Blog — LLM Works">
  <meta name="twitter:description" content="Technical writing on AI infrastructure, agent development, and fine-tuning.">
  <link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">
  <link rel="alternate" type="application/rss+xml" title="LLM Works Blog" href="/blog/feed.xml">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x2588;</text></svg>">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-PLTFCVZQ8R"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-PLTFCVZQ8R');
  </script>
  <link rel="stylesheet" href="/styles.css">
  <script src="/script.js"></script>
</head>
<body class="blog-index">
  <a class="skip-link" href="#main">Skip to content</a>

  <nav aria-label="Primary">
    <div class="container">
      <a href="/" class="logo">llm-works<span>.ai</span></a>
      <ul class="nav-links">
        <li><a href="/platform/">Platform</a></li>
        <li><a href="/agents/">Agents</a></li>
        <li><a href="/story/">Story</a></li>
        <li><a href="/blog/" aria-current="page">Blog</a></li>
        <li><a href="/about/">About</a></li>
      </ul>
    </div>
  </nav>

  <label class="theme-toggle" aria-label="Toggle dark/light mode" title="Toggle dark/light mode">
    <input type="checkbox" id="theme-switch">
    <span class="slider"></span>
  </label>

  <main id="main" tabindex="-1">

  <section class="hero">
    <div class="container">
      <h1>Blog</h1>
      <p>Technical writing on AI infrastructure, agent development, and fine-tuning.</p>
    </div>
  </section>

  <section class="blog-list">
    <div class="container">
      <div class="post-grid">
{posts}
      </div>
    </div>
  </section>

  </main>

  <footer>
    <div class="container">
      <span>&copy; 2026 LLM Works LLC</span>
      <div class="footer-links">
        <a href="/blog/feed.xml">RSS</a>
        <a href="/llms.txt">llms.txt</a>
        <a href="/terms.html">Terms</a>
      </div>
    </div>
  </footer>

</body>
</html>
"""

POST_CARD_TEMPLATE = """\
        <a href="/blog/{slug}/" class="post-card">
          <img src="/blog/{slug}/assets/{teaser}" alt="" class="blog-dark-only">
          <img src="/blog/{slug}/assets/{teaser_light}" alt="" class="blog-light-only">
          <div class="post-card-content">
            <time datetime="{date_iso}">{date_display}</time>
            <h2>{title}</h2>
          </div>
        </a>"""

RSS_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LLM Works Blog</title>
    <link>https://www.llm-works.ai/blog/</link>
    <description>Technical writing on AI infrastructure, agent development, and fine-tuning.</description>
    <language>en-us</language>
    <lastBuildDate>{build_date}</lastBuildDate>
    <atom:link href="https://www.llm-works.ai/blog/feed.xml" rel="self" type="application/rss+xml"/>
{items}
  </channel>
</rss>
"""

RSS_ITEM_TEMPLATE = """\
    <item>
      <title>{title}</title>
      <link>https://www.llm-works.ai/blog/{slug}/</link>
      <guid isPermaLink="true">https://www.llm-works.ai/blog/{slug}/</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>"""


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    raw = yaml.safe_load(parts[1])
    if not raw:
        return {}, parts[2].strip()

    frontmatter = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                frontmatter[f"{key}_{nested_key}"] = nested_value
        else:
            frontmatter[key] = value

    return frontmatter, parts[2].strip()


def transform_content(body: str) -> str:
    """Transform markdown content for new site structure."""
    # Fix internal blog links: /slug/ -> /blog/slug/
    body = re.sub(r'\]\(/([a-z0-9-]+)/\)', r'](/blog/\1/)', body)
    # Fix image paths: /assets/images/ -> assets/
    body = body.replace('src="/assets/images/', 'src="assets/')
    # Fix GitHub org: serendip-ml -> llm-works
    body = body.replace('github.com/serendip-ml', 'github.com/llm-works')
    body = body.replace('serendip-ml', 'llm-works')
    # Rename Jekyll theme classes to blog- prefix
    body = body.replace('class="example-meta"', 'class="blog-example-meta"')
    body = body.replace('class="scaling-chart"', 'class="blog-chart"')
    body = body.replace('class="scaling-chart-light"', 'class="blog-chart-light"')
    body = body.replace('class="dark-only"', 'class="blog-dark-only"')
    body = body.replace('class="light-only"', 'class="blog-light-only"')
    body = body.replace('class="pos"', 'class="blog-pos"')
    body = body.replace('class="neg"', 'class="blog-neg"')
    return body


def render_markdown(md_content: str) -> str:
    """Convert markdown to HTML."""
    md = markdown.Markdown(extensions=[
        TableExtension(),
        FencedCodeExtension(),
    ])
    return md.convert(md_content)


def build_post(src_dir: Path) -> dict | None:
    """Build a single post from its source directory."""
    post_md = src_dir / "post.md"
    if not post_md.exists():
        return None

    slug = src_dir.name
    content = post_md.read_text()
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter.get("title") or not frontmatter.get("date"):
        print(f"  Skipping {slug}: missing title or date")
        return None

    raw_date = frontmatter["date"]
    if isinstance(raw_date, str):
        date = datetime.strptime(raw_date, "%Y-%m-%d")
    else:
        date = datetime.combine(raw_date, datetime.min.time())
    body = transform_content(body)
    html_content = render_markdown(body)

    # Indent content for template
    html_content = "\n".join(f"        {line}" if line else "" for line in html_content.split("\n"))

    # Extract teaser filename from header_teaser path
    teaser_path = frontmatter.get("header_teaser", "")
    teaser = teaser_path.split("/")[-1] if teaser_path else ""
    # Derive light mode teaser filename (e.g., scaling-curve.png -> scaling-curve-light.png)
    if "." in teaser:
        name, ext = teaser.rsplit(".", 1)
        teaser_light = f"{name}-light.{ext}"
    else:
        teaser_light = teaser

    post_data = {
        "slug": slug,
        "title": frontmatter["title"],
        "description": frontmatter.get("description", ""),
        "date": date,
        "date_iso": date.strftime("%Y-%m-%d"),
        "date_display": date.strftime("%B %d, %Y"),
        "content": html_content,
        "teaser": teaser,
        "teaser_light": teaser_light,
    }

    # Write HTML to same directory as post.md
    out_dir = src_dir

    # Write HTML (escape title/description for HTML attributes)
    html = POST_TEMPLATE.format(
        **{**post_data, "title": escape(post_data["title"]),
           "description": escape(post_data["description"])}
    )
    (out_dir / "index.html").write_text(html)
    print(f"  Built: /blog/{slug}/")

    return post_data


def build_index(posts: list[dict]) -> None:
    """Build the blog index page."""
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)

    cards = "\n".join(
        POST_CARD_TEMPLATE.format(
            slug=p["slug"],
            title=escape(p["title"]),
            description=escape(p["description"]),
            date_iso=p["date_iso"],
            date_display=p["date_display"],
            teaser=p["teaser"],
            teaser_light=p["teaser_light"],
        )
        for p in posts_sorted
    )

    html = INDEX_TEMPLATE.format(posts=cards)
    (ROOT / "index.html").write_text(html)
    print("  Built: /blog/")


def build_rss(posts: list[dict]) -> None:
    """Build the RSS feed."""
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)

    items = "\n".join(
        RSS_ITEM_TEMPLATE.format(
            slug=p["slug"],
            title=escape(p["title"]),
            description=escape(p["description"]),
            pub_date=p["date"].strftime("%a, %d %b %Y 00:00:00 +0000"),
        )
        for p in posts_sorted
    )

    rss = RSS_TEMPLATE.format(
        build_date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
        items=items,
    )
    (ROOT / "feed.xml").write_text(rss)
    print("  Built: /blog/feed.xml")


def main() -> None:
    print("Building blog...")

    posts = []
    for post_dir in ROOT.iterdir():
        if post_dir.is_dir() and (post_dir / "post.md").exists():
            post = build_post(post_dir)
            if post:
                posts.append(post)

    if posts:
        build_index(posts)
        build_rss(posts)

    print(f"Done. {len(posts)} posts built.")


if __name__ == "__main__":
    main()
