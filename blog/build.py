#!/usr/bin/env python3
"""Build blog posts from markdown sources to HTML."""

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlparse

import markdown
import yaml
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension, TocTreeprocessor

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

SITE_URL = "https://www.llm-works.ai"
ORG_ID = f"{SITE_URL}/#organization"

ROOT = Path(__file__).parent
SITE_ROOT = ROOT.parent
STYLES_CSS = SITE_ROOT / "styles.css"
SCRIPT_JS = SITE_ROOT / "script.js"

# Static assets get a ?v=<content-hash> suffix so a deploy immediately
# invalidates the upstream CDN cache instead of waiting out its 4h TTL.
HASHED_ASSETS = {"/styles.css": STYLES_CSS, "/script.js": SCRIPT_JS}
_asset_pattern = "|".join(re.escape(url) for url in HASHED_ASSETS)
_ASSET_REF_RE = re.compile(rf'(?<![\w./-])({_asset_pattern})(\?v=[^"\'\s#>)]*)?(?=["\'\s#>)])')

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
  <meta property="og:site_name" content="LLM Works">{og_image_meta}
  <meta property="article:published_time" content="{date_iso}">
  <meta property="article:modified_time" content="{modified_iso}">
  <meta property="article:author" content="https://www.llm-works.ai/">
  <meta name="twitter:card" content="{twitter_card}">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">{twitter_image_meta}
  <link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">
  <link rel="alternate" type="application/rss+xml" title="LLM Works Blog" href="/blog/feed.xml">
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
  <script type="application/ld+json">
{post_jsonld}
  </script>
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
        <li><a href="/#agents">Agents</a></li>
        <li><a href="/platform/">Platform</a></li>
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
        <div class="post-meta-row">
          <p class="post-date">{date_display}</p>{kicker_meta}
        </div>
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
        <a href="/terms/">Terms</a>
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
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png">
  <script type="application/ld+json">
{index_jsonld}
  </script>
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
        <li><a href="/#agents">Agents</a></li>
        <li><a href="/platform/">Platform</a></li>
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
      <div class="section-label">Blog</div>
      <h1>Technical writing</h1>
      <p>On AI infrastructure, agent development, and fine-tuning.</p>
    </div>
  </section>

  <section class="blog-list">
    <div class="container">
      <div class="blog-hero" hidden></div>
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
        <a href="/terms/">Terms</a>
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
            <div class="post-card-meta-row">
              <time datetime="{date_iso}">{date_display}</time>{card_kicker_meta}
            </div>
            <h2>{title}</h2>
          </div>
        </a>"""

RSS_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
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
      <description>{description}</description>{enclosure}
    </item>"""

REDIRECT_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="canonical" href="{target}">
  <title>Redirecting...</title>
</head>
<body>
  <p>Redirecting to <a href="{target}">{target}</a></p>
</body>
</html>
"""


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


TOP_LEVEL_ROUTES = frozenset({"platform", "about", "story", "blog", "terms", "agents"})


def transform_content(body: str) -> str:
    """Transform markdown content for new site structure."""
    # Legacy blog cross-links used `/slug/` — rewrite to `/blog/slug/`.
    # Top-level site routes (/platform/, /about/, …) must pass through unchanged.
    def _rewrite_internal(m: re.Match) -> str:
        slug = m.group(1)
        if slug in TOP_LEVEL_ROUTES:
            return m.group(0)
        return f'](/blog/{slug}/)'
    body = re.sub(r'\]\(/([a-z0-9-]+)/\)', _rewrite_internal, body)
    # Fix image paths: /assets/images/ -> assets/ (HTML and Markdown)
    body = body.replace('src="/assets/images/', 'src="assets/')
    body = body.replace('](/assets/images/', '](assets/')
    body = body.replace('![/assets/images/', '![assets/')
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


HTTP_LINK_RE = re.compile(r'<a\s+href="(https?://[^"]+)"([^>]*)>')
_TARGET_ATTR_RE = re.compile(r'\s+target="[^"]*"')
_REL_ATTR_RE = re.compile(r'\s+rel="[^"]*"')


def _is_internal(href: str) -> bool:
    u = urlparse(href)
    host = u.netloc.lower()
    if host == "llm-works.ai" or host.endswith(".llm-works.ai"):
        return True
    path_lower = u.path.lower()
    if host == "github.com" and (path_lower.startswith("/llm-works/") or path_lower == "/llm-works"):
        return True
    return False


def normalize_link_targets(html: str) -> str:
    """Strip any existing target/rel from http(s) links, then add target=_blank
    to external links only. llm-works family stays in-tab."""
    def repl(m: re.Match) -> str:
        href, rest = m.group(1), m.group(2)
        rest = _TARGET_ATTR_RE.sub("", rest)
        rest = _REL_ATTR_RE.sub("", rest)
        if _is_internal(href):
            return f'<a href="{href}"{rest}>'
        return f'<a href="{href}"{rest} target="_blank" rel="noopener noreferrer">'
    return HTTP_LINK_RE.sub(repl, html)


_HEADER_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})


class _NoTocAwareTreeprocessor(TocTreeprocessor):
    """TOC processor that skips headings tagged {: .no_toc }."""

    def run(self, doc):
        muted = []
        for el in doc.iter():
            if el.tag in _HEADER_TAGS and "no_toc" in el.get("class", "").split():
                muted.append((el, el.tag))
                el.tag = "p"
        try:
            super().run(doc)
        finally:
            for el, tag in muted:
                el.tag = tag


class _NoTocAwareExtension(TocExtension):
    TreeProcessorClass = _NoTocAwareTreeprocessor


def render_markdown(md_content: str) -> str:
    """Convert markdown to HTML."""
    md = markdown.Markdown(extensions=[
        TableExtension(),
        FencedCodeExtension(),
        AttrListExtension(),
        _NoTocAwareExtension(toc_depth="2-3", permalink=False, marker="[TOC]"),
    ])
    return normalize_link_targets(md.convert(md_content))


_IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def _asset_path(slug: str, teaser_filename: str) -> Path:
    """Filesystem path to a post's teaser asset."""
    return ROOT / slug / "assets" / teaser_filename


def _resolve_og_teaser(slug: str, teaser_filename: str) -> str:
    """Prefer a PNG counterpart for og:image when the frontmatter names an SVG.
    Most social crawlers don't render SVG previews; PNG is the safe default."""
    if not teaser_filename or not teaser_filename.lower().endswith(".svg"):
        return teaser_filename
    stem = teaser_filename[:-4]
    png_alt = _asset_path(slug, stem + ".png")
    if png_alt.exists():
        return stem + ".png"
    return teaser_filename


def _image_dims(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for a raster teaser, else None. SVG dims are
    intentionally not read — declaring width/height on a scalable image is
    misleading, and social crawlers ignore SVG anyway."""
    if not _HAS_PIL or not path.exists():
        return None
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def _org_node() -> dict:
    """Minimal Organization node for inclusion in per-page @graph blocks.
    The full Organization declaration lives on the Home page; other pages
    only need enough for validators to resolve author/publisher refs."""
    return {
        "@type": "Organization",
        "@id": ORG_ID,
        "name": "LLM Works",
        "url": f"{SITE_URL}/",
        "logo": f"{SITE_URL}/assets/favicon-32x32.png",
    }


def _post_jsonld(post: dict) -> str:
    """BlogPosting + Organization @graph for a single post page."""
    slug = post["slug"]
    url = f"{SITE_URL}/blog/{slug}/"
    image_url = (f"{SITE_URL}/blog/{slug}/assets/{post['og_teaser']}"
                 if post.get("og_teaser") else None)
    posting = {
        "@type": "BlogPosting",
        "@id": f"{url}#post",
        "url": url,
        "mainEntityOfPage": {"@id": url},
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["date_iso"],
        "dateModified": post["modified_iso"],
        "inLanguage": "en",
        "author": {"@id": ORG_ID},
        "publisher": {"@id": ORG_ID},
    }
    if image_url:
        posting["image"] = image_url
    graph = {"@context": "https://schema.org", "@graph": [_org_node(), posting]}
    return _indent_json(graph)


def _index_jsonld(posts: list[dict]) -> str:
    """Blog + ItemList + Organization @graph for the blog index page."""
    blog_url = f"{SITE_URL}/blog/"
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)
    blog_posts = [{"@id": f"{SITE_URL}/blog/{p['slug']}/#post"} for p in posts_sorted]
    item_list = [
        {"@type": "ListItem", "position": i + 1,
         "url": f"{SITE_URL}/blog/{p['slug']}/", "name": p["title"]}
        for i, p in enumerate(posts_sorted)
    ]
    blog_node = {
        "@type": "Blog",
        "@id": f"{blog_url}#blog",
        "url": blog_url,
        "name": "LLM Works Blog",
        "description": "Technical writing on AI infrastructure, agent development, and fine-tuning.",
        "publisher": {"@id": ORG_ID},
        "inLanguage": "en",
        "blogPost": blog_posts,
    }
    itemlist_node = {
        "@type": "ItemList",
        "@id": f"{blog_url}#itemlist",
        "itemListElement": item_list,
    }
    graph = {"@context": "https://schema.org",
             "@graph": [_org_node(), blog_node, itemlist_node]}
    return _indent_json(graph)


def _indent_json(obj: dict) -> str:
    """JSON dump indented for the template. `</script>` in string values must
    be escaped so it can't terminate the surrounding <script> tag."""
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    text = text.replace("</", "<\\/")
    return "\n".join("  " + line for line in text.split("\n"))


def _indent_html(html: str, indent: str = "        ") -> str:
    """Indent rendered HTML for the page template while leaving lines inside
    <pre> blocks untouched, since they render leading whitespace as content."""
    out = []
    in_pre = False
    for line in html.split("\n"):
        if in_pre:
            out.append(line)
            if "</pre>" in line:
                in_pre = False
        else:
            out.append(f"{indent}{line}" if line else "")
            if "<pre" in line and "</pre>" not in line:
                in_pre = True
    return "\n".join(out)


def build_post(src_dir: Path) -> dict | None:
    """Build a single post from its source directory."""
    post_md = src_dir / "post.md"
    if not post_md.exists():
        return None

    slug = src_dir.name
    content = post_md.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter.get("title") or not frontmatter.get("date"):
        print(f"  Skipping {slug}: missing title or date")
        return None

    raw_date = frontmatter["date"]
    if isinstance(raw_date, str):
        date = datetime.strptime(raw_date, "%Y-%m-%d")
    else:
        date = datetime.combine(raw_date, datetime.min.time())
    raw_modified = frontmatter.get("modified_date") or frontmatter.get("date")
    if isinstance(raw_modified, str):
        modified = datetime.strptime(raw_modified, "%Y-%m-%d")
    else:
        modified = datetime.combine(raw_modified, datetime.min.time())
    html_content = _indent_html(render_markdown(transform_content(body)))

    # Extract teaser filename from header_teaser path
    teaser_path = frontmatter.get("header_teaser", "")
    teaser = teaser_path.split("/")[-1] if teaser_path else ""
    # Derive light mode teaser filename (e.g., scaling-curve.png -> scaling-curve-light.png)
    if "." in teaser:
        name, ext = teaser.rsplit(".", 1)
        teaser_light = f"{name}-light.{ext}"
    else:
        teaser_light = teaser

    # The card can use the (potentially SVG) teaser; og:image switches to a PNG
    # counterpart when available, since social crawlers don't render SVG.
    og_teaser = _resolve_og_teaser(slug, teaser)

    if teaser and og_teaser:
        image_url = f"https://www.llm-works.ai/blog/{slug}/assets/{og_teaser}"
        dims = _image_dims(_asset_path(slug, og_teaser))
        dims_meta = ""
        if dims:
            w, h = dims
            dims_meta = (
                f'\n  <meta property="og:image:width" content="{w}">'
                f'\n  <meta property="og:image:height" content="{h}">'
            )
        og_image_meta = (
            f'\n  <meta property="og:image" content="{image_url}">'
            f'{dims_meta}'
        )
        twitter_image_meta = f'\n  <meta name="twitter:image" content="{image_url}">'
        twitter_card = "summary_large_image"
    else:
        og_image_meta = ""
        twitter_image_meta = ""
        twitter_card = "summary"

    kicker_raw = frontmatter.get("kicker", "")
    if isinstance(kicker_raw, str):
        kicker_raw = kicker_raw.strip()
    else:
        kicker_raw = ""

    post_data = {
        "slug": slug,
        "title": frontmatter["title"],
        "description": (frontmatter.get("description") or "").strip(),
        "date": date,
        "date_iso": date.strftime("%Y-%m-%d"),
        "date_display": date.strftime("%B %d, %Y"),
        "modified": modified,
        "modified_iso": modified.strftime("%Y-%m-%d"),
        "content": html_content,
        "teaser": teaser,
        "teaser_light": teaser_light,
        "og_teaser": og_teaser,
        "og_image_meta": og_image_meta,
        "twitter_image_meta": twitter_image_meta,
        "twitter_card": twitter_card,
        "kicker": kicker_raw,
    }

    # Write HTML to same directory as post.md
    out_dir = src_dir

    # Render kicker meta at template-fill time (consistent with card rendering)
    kicker_meta = ""
    if kicker_raw:
        kicker_meta = f'\n          <div class="section-label post-kicker">{escape(kicker_raw)}</div>'

    # Write HTML (escape title/description for HTML attributes; JSON-LD gets
    # the raw values via json.dumps which handles quoting).
    html = POST_TEMPLATE.format(
        **{**post_data, "title": escape(post_data["title"]),
           "description": escape(post_data["description"]),
           "kicker_meta": kicker_meta,
           "post_jsonld": _post_jsonld(post_data)}
    )
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  Built: /blog/{slug}/")

    # Generate redirects from old URLs
    redirects = frontmatter.get("redirect_from", [])
    if isinstance(redirects, str):
        redirects = [redirects]
    for redirect_path in redirects:
        redirect_path = redirect_path.strip("/")
        redirect_dir = ROOT.parent / redirect_path
        redirect_dir.mkdir(parents=True, exist_ok=True)
        redirect_html = REDIRECT_TEMPLATE.format(target=f"/blog/{slug}/")
        (redirect_dir / "index.html").write_text(redirect_html, encoding="utf-8")
        print(f"  Redirect: /{redirect_path}/ -> /blog/{slug}/")

    return post_data


def build_index(posts: list[dict]) -> None:
    """Build the blog index page."""
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)

    def _card_kicker_meta(post: dict) -> str:
        k = post.get("kicker", "")
        if not k:
            return ""
        return f'\n              <div class="post-card-kicker">{escape(k)}</div>'

    cards = "\n".join(
        POST_CARD_TEMPLATE.format(
            slug=p["slug"],
            title=escape(p["title"]),
            description=escape(p["description"]),
            date_iso=p["date_iso"],
            date_display=p["date_display"],
            teaser=p["teaser"],
            teaser_light=p["teaser_light"],
            card_kicker_meta=_card_kicker_meta(p),
        )
        for p in posts_sorted
    )

    html = INDEX_TEMPLATE.format(posts=cards, index_jsonld=_index_jsonld(posts))
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print("  Built: /blog/")


def build_rss(posts: list[dict]) -> None:
    """Build the RSS feed."""
    posts_sorted = sorted(posts, key=lambda p: p["date"], reverse=True)

    def _enclosure(p: dict) -> str:
        teaser = p.get("og_teaser") or ""
        if not teaser:
            return ""
        path = _asset_path(p["slug"], teaser)
        if not path.exists():
            return ""
        ext = "." + teaser.rsplit(".", 1)[-1].lower()
        mime = _IMAGE_MIME.get(ext, "application/octet-stream")
        url = f"{SITE_URL}/blog/{p['slug']}/assets/{teaser}"
        length = path.stat().st_size
        return (
            f'\n      <enclosure url="{url}" length="{length}" type="{mime}"/>'
            f'\n      <media:content url="{url}" medium="image" type="{mime}"/>'
        )

    items = "\n".join(
        RSS_ITEM_TEMPLATE.format(
            slug=p["slug"],
            title=escape(p["title"]),
            description=escape(p["description"]),
            pub_date=p["date"].strftime("%a, %d %b %Y 00:00:00 +0000"),
            enclosure=_enclosure(p),
        )
        for p in posts_sorted
    )

    rss = RSS_TEMPLATE.format(
        build_date=datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        items=items,
    )
    (ROOT / "feed.xml").write_text(rss, encoding="utf-8")
    print("  Built: /blog/feed.xml")


def _asset_hash(path: Path) -> str:
    # md5[:8] to stay consistent with the Makefile's `bump-css` / `bump-js`
    # targets, so either mechanism produces the same cache-busting tag.
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def stamp_assets() -> None:
    """Rewrite /styles.css and /script.js references across all HTML with
    ?v=<content-hash> so a deploy invalidates CDN caches immediately.
    Idempotent: an existing ?v=... suffix is replaced."""
    hashes = {url: _asset_hash(path) for url, path in HASHED_ASSETS.items()}

    def repl(m: re.Match) -> str:
        return f"{m.group(1)}?v={hashes[m.group(1)]}"

    stamped = 0
    for dirpath, dirnames, filenames in os.walk(SITE_ROOT):
        # Prune hidden dirs and vendored deps before descent.
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            html_path = Path(dirpath) / fname
            original = html_path.read_text(encoding="utf-8")
            updated = _ASSET_REF_RE.sub(repl, original)
            if updated != original:
                html_path.write_text(updated, encoding="utf-8")
                stamped += 1
    print(f"  Stamped assets in {stamped} HTML file(s) "
          f"(css={hashes['/styles.css']}, js={hashes['/script.js']})")


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

    stamp_assets()

    print(f"Done. {len(posts)} posts built.")


if __name__ == "__main__":
    main()
