#!/usr/bin/env python3
"""
Static site generator for reginaruane.github.io

Usage
-----
    python3 build.py            # write the HTML files
    python3 build.py --serve    # write, then serve on http://localhost:8000

All links are written relative, so the generated site works whether it is served
from a domain root, from a /reponame/ subfolder, or opened directly from disk.

Content lives in _data/*.yml and the page bodies in pages/*.py.
Nothing here needs Jekyll, Ruby, or a network connection — the generated
HTML is committed to the repository and GitHub Pages serves it as-is.

Requires: PyYAML  (pip install pyyaml)
"""

from __future__ import annotations

import html
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "_data"
OUT = ROOT

# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------


def load(name: str):
    with open(DATA / f"{name}.yml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


SITE = load("site")
PUBS = load("publications")
NEWS = load("news")
TALKS = load("talks")
TEACHING = load("teaching")
LEADERSHIP = load("leadership")
RESEARCH = load("research")
STUDENTS = load("students")
CV = load("cv")

NAV = [
    ("01", "About", "/", "index.html"),
    ("02", "Research", "/research/", "research/index.html"),
    ("03", "Publications", "/publications/", "publications/index.html"),
    ("04", "Teaching", "/teaching/", "teaching/index.html"),
    ("05", "Students", "/students/", "students/index.html"),
    ("06", "Leadership &amp; Grants", "/leadership/", "leadership/index.html"),
    ("07", "Talks", "/talks/", "talks/index.html"),
    ("08", "CV", "/cv/", "cv/index.html"),
]

TOPIC_LABELS = {
    "networks": "Networks",
    "causal": "Causal inference",
    "bayesian": "Bayesian",
    "eviction": "Eviction &amp; law",
    "ml": "Machine learning",
    "fintech": "FinTech",
    "health": "Health",
    "education": "Education",
}

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

SELF_NAMES = ("Regina Ruane", "R. Ruane")


def esc(text: str) -> str:
    """Escape, but leave already-written entities such as &amp; alone."""
    if text is None:
        return ""
    return html.escape(str(text), quote=False).replace("&amp;amp;", "&amp;")


def bold_self(authors: str) -> str:
    out = esc(authors)
    for name in SELF_NAMES:
        out = out.replace(name, f"<strong>{name}</strong>")
    return out


MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def md_inline(text: str) -> str:
    """The small subset of Markdown used in news entries."""
    out = esc(text)
    out = MD_LINK.sub(r'<a href="\2" rel="noopener">\1</a>', out)
    out = MD_BOLD.sub(r"<strong>\1</strong>", out)
    return out


def tidy(text: str) -> str:
    """Collapse the whitespace that YAML folded scalars leave behind."""
    return " ".join(str(text or "").split())


def arxiv_url(aid: str) -> str:
    return f"https://arxiv.org/abs/{aid}"


# --------------------------------------------------------------------------
# link rewriting
# --------------------------------------------------------------------------

# Links are written relative to each page's own depth rather than to the domain
# root. That way the site works wherever it is served from:
#   https://username.github.io/            (user site)
#   https://username.github.io/reponame/   (project site)
#   https://your-own-domain.com/           (custom domain)
#   file:///.../index.html                 (opened locally)
RELATIVE = True
_DEPTH = 0


def u(path: str) -> str:
    """Rewrite a root-absolute site path for the current output depth."""
    if not RELATIVE or not path.startswith("/"):
        return path
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return ("../" * _DEPTH) + rel if _DEPTH else (rel or "index.html")


def rewrite(html_text: str) -> str:
    """Rewrite every root-absolute href/src in a finished page."""
    if not RELATIVE:
        return html_text
    def sub(m):
        attr, path = m.group(1), m.group(2)
        return f'{attr}="{u(path)}"'
    return re.sub(r'\b(href|src)="(/[^"]*)"', sub, html_text)


ICONS = {
    "cv": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 15h6"/><path d="M9 11h2"/></svg>',
    "scholar": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3 1 9l11 6 9-4.91V17h2V9L12 3z"/><path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82z"/></svg>',
    "arxiv": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v16H4z"/><path d="M8 8l8 8"/><path d="M16 8l-8 8"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/></svg>',
    "github": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2A10 10 0 0 0 8.8 21.5c.5.1.7-.2.7-.5v-1.7C6.7 19.9 6.1 18 6.1 18c-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.7.3-1.1.6-1.3-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.4-1.3.1-2.7 0 0 .8-.3 2.7 1a9.4 9.4 0 0 1 5 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .3.3.7 1 .7 2v2.9c0 .3.2.6.7.5A10 10 0 0 0 12 2z"/></svg>',
    "orcid": '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" opacity=".25"/><path d="M8 7.5h1.5v9H8zm3.2 0h3.1c2.4 0 3.9 1.8 3.9 4.5s-1.6 4.5-3.9 4.5h-3.1zm1.5 1.4v6.2h1.5c1.6 0 2.5-1.2 2.5-3.1s-.9-3.1-2.5-3.1z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5A2.5 2.5 0 1 0 5 8.5a2.5 2.5 0 0 0 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.5 4.7 5.8V21h-4v-5.6c0-1.3 0-3-1.9-3s-2.2 1.4-2.2 2.9V21H9z"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
}

# --------------------------------------------------------------------------
# chrome
# --------------------------------------------------------------------------


def head(title: str, description: str, url_path: str, *, is_home=False) -> str:
    full_title = SITE["name"] if is_home else f"{title} · {SITE['name']}"
    # Canonical and og:url have to be absolute, so they are emitted only once
    # `url` is set in _data/site.yml. Leaving it blank simply omits them, which
    # is better than asserting an address the site is not actually served from.
    base = (SITE.get("url") or "").strip().rstrip("/")
    canonical = base + url_path if base else ""
    if base:
        canonical_tags = (
            f'<link rel="canonical" href="{canonical}">\n'
            f'<meta property="og:url" content="{canonical}">\n'
            f'<meta property="og:image" content="{base}{SITE["author"]["photo"]}">'
        )
    else:
        canonical_tags = "<!-- set `url` in _data/site.yml to emit canonical and og:url -->"

    depth_prefix = ""  # assets resolved relative to each page
    return f"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(tidy(description))}">
<meta name="author" content="{esc(SITE['full_name'])}">
{canonical_tags}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE['name'])}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(tidy(description))}">
<meta name="twitter:card" content="summary">

<link rel="icon" href="{depth_prefix}/images/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,500;0,600;1,6..72,400&amp;family=Inter:wght@400;500;600;650&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap">
<link rel="stylesheet" href="{depth_prefix}/assets/css/main.css">

<script>
/* Dark is the default. Apply a stored preference before first paint so the
   page never flashes the wrong theme. */
(function(){{try{{var t=localStorage.getItem('rr-theme');
if(t==='light'||t==='dark'){{document.documentElement.setAttribute('data-theme',t);}}}}catch(e){{}}}})();
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def theme_button() -> str:
    return (
        '<button class="theme-toggle" type="button" aria-pressed="false" '
        'aria-label="Switch between dark and light theme">'
        f'<span class="t-light">{ICONS["sun"]}</span>'
        f'<span class="t-dark">{ICONS["moon"]}</span>'
        '<span class="tt-text">Theme</span>'
        "</button>"
    )


def sidebar(active: str) -> str:
    a = SITE["author"]
    items = []
    for num, label, href, _ in NAV:
        cls = ' class="is-current" aria-current="page"' if href == active else ""
        items.append(
            f'<li><a href="{href}"{cls}><span class="nav-num">{num}</span>'
            f"<span>{label}</span></a></li>"
        )

    interests = "".join(f'<span class="interest">{esc(i)}</span>' for i in SITE["interests"])

    # The "Elsewhere" list. Each entry appears only when its value is set in
    # _data/site.yml, so blanking a value removes the link rather than leaving a
    # dead one. arXiv is deliberately left out of this list — it still appears on
    # the publications page. To show it here again, add this line back:
    #   if a.get("arxiv"):
    #       profiles.append(f'<li><a href="{a["arxiv"]}" rel="noopener">'
    #                       f'{ICONS["arxiv"]}<span>arXiv</span></a></li>')
    profiles = []
    if a.get("cv"):
        profiles.append(f'<li><a href="{a["cv"]}">{ICONS["cv"]}<span>Curriculum vitae</span></a></li>')
    if a.get("scholar"):
        profiles.append(f'<li><a href="{a["scholar"]}" rel="noopener">{ICONS["scholar"]}<span>Google Scholar</span></a></li>')
    if a.get("github"):
        profiles.append(f'<li><a href="{a["github"]}" rel="noopener">{ICONS["github"]}<span>GitHub</span></a></li>')
    if a.get("orcid"):
        profiles.append(f'<li><a href="{a["orcid"]}" rel="noopener">{ICONS["orcid"]}<span>ORCID</span></a></li>')
    if a.get("linkedin"):
        profiles.append(f'<li><a href="{a["linkedin"]}" rel="noopener">{ICONS["linkedin"]}<span>LinkedIn</span></a></li>')

    return f"""
<div class="mobile-bar">
  <a class="mb-name" href="/">{esc(SITE['name'])}</a>
  <div class="mb-actions">
    {theme_button()}
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="sidebar">Menu</button>
  </div>
</div>

<div class="shell">
<aside class="sidebar" id="sidebar">
  <div class="sidebar-inner">
    <a class="identity" href="/">
      <img class="portrait" src="/images/profile.jpg" alt="{esc(SITE['full_name'])}" width="118" height="118">
      <span class="identity-name">{esc(SITE['name'])}</span>
    </a>
    <p class="identity-role">{esc(SITE['tagline'])}</p>

    <p class="interests">{interests}</p>

    <nav class="nav" aria-label="Main navigation">
      <ul>{''.join(items)}</ul>
    </nav>

    <div class="side-block">
      <p class="side-label">Contact</p>
      <p class="contact-line">{esc(a['affiliation'])}</p>
      <p class="contact-line">{esc(a['location'])}</p>
      <p class="contact-line"><a href="mailto:{a['email']}">{a['email']}</a></p>
    </div>

    <div class="side-block">
      <p class="side-label">Elsewhere</p>
      <ul class="profiles">{''.join(profiles)}</ul>
    </div>

    {theme_button()}
  </div>
</aside>

<main id="main" class="content">
"""


def footer() -> str:
    year = 2026
    return f"""
  <footer class="footer">
    <span>&copy; {year} {esc(SITE['full_name'])}</span>
    <span><a href="{SITE['author']['cv']}">CV</a> · <a href="mailto:{SITE['author']['email']}">Email</a> · <a href="{SITE['author']['scholar']}" rel="noopener">Scholar</a></span>
  </footer>
</main>
</div>
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def page(path_key: str, title: str, description: str, body: str, *, is_home=False,
         subtitle: str = "") -> str:
    href = next(h for _, _, h, k in NAV if k == path_key)
    head_block = ""
    if not is_home:
        sub = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
        head_block = f'<header class="page-head"><h1 class="page-title">{title}</h1>{sub}</header>'
    return (
        head(title, description, href, is_home=is_home)
        + sidebar(href)
        + head_block
        + body
        + footer()
    )


# --------------------------------------------------------------------------
# shared components
# --------------------------------------------------------------------------


def pub_card(p: dict) -> str:
    topics = " ".join(p.get("topics") or [])
    bits = []

    if p.get("status"):
        bits.append(f'<span class="tag">{esc(p["status"])}</span>')
    if p.get("venue") and p.get("venue") != p.get("status"):
        bits.append(f"<cite>{esc(p['venue'])}</cite>")
    if p.get("note"):
        bits.append(f'<span class="pub-note">{esc(p["note"])}</span>')
    if p.get("award"):
        bits.append(f'<span class="tag tag-award">{esc(p["award"])}</span>')

    links = []
    if p.get("arxiv"):
        links.append(f'<a href="{arxiv_url(p["arxiv"])}" rel="noopener">arXiv:{p["arxiv"]}</a>')
    if p.get("doi"):
        links.append(f'<a href="{p["doi"]}" rel="noopener">DOI</a>')
    if p.get("code"):
        links.append(f'<a href="{p["code"]}" rel="noopener">Code</a>')
    links_html = f'<p class="pub-links">{"".join(links)}</p>' if links else ""

    abstract = ""
    if p.get("abstract"):
        abstract = (
            '<details class="pub-abstract"><summary>Abstract</summary>'
            f"<p>{esc(tidy(p['abstract']))}</p></details>"
        )

    return f"""
    <li class="pub reveal" data-topics="{topics}">
      <div class="pub-head">
        <h3 class="pub-title">{esc(p['title'])}</h3>
        <span class="pub-year">{p.get('year', '')}</span>
      </div>
      <p class="pub-authors">{bold_self(p['authors'])}</p>
      <p class="pub-meta">{''.join(bits)}</p>
      {links_html}
      {abstract}
    </li>"""


def pub_list(items: list) -> str:
    return '<ol class="pubs">' + "".join(pub_card(p) for p in items) + "</ol>"


def all_pubs() -> list:
    out = []
    for key in ("published", "review", "preprints", "working"):
        out.extend(PUBS.get(key) or [])
    return out


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------


def build_home() -> str:
    metrics = "".join(
        f'<div class="metric"><span class="metric-value">{m["value"]}</span>'
        f'<span class="metric-label">{m["label"]}</span></div>'
        for m in SITE["metrics"]
    )

    news_items = "".join(
        f'<li><span class="news-date">{esc(n["date"])}</span>'
        f'<p class="news-text">{md_inline(n["text"])}</p></li>'
        for n in NEWS[:6]
    )

    featured = [p for p in all_pubs() if p.get("featured")]
    featured.sort(key=lambda p: (-int(p.get("year") or 0), p["title"]))
    featured = featured[:6]

    body = f"""
<section class="hero">
  <canvas id="net-canvas" aria-hidden="true"></canvas>
  <div class="hero-inner">
    <p class="hero-eyebrow">University of Pennsylvania</p>
    <h1>{esc(SITE['full_name'])}</h1>
    <p class="hero-role">{SITE['role']}</p>
    <p class="lede">
      I am a statistician who works on data about people and institutions that are
      connected to one another. My research builds models for networks that are measured
      with error, and applies them to a setting where the network is the mechanism:
      the legal infrastructure that produces eviction.
    </p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/research/">Research {ICONS['arrow']}</a>
      <a class="btn" href="/publications/">Publications</a>
      <a class="btn" href="{SITE['author']['cv']}">CV (PDF)</a>
    </div>
  </div>
</section>

<div class="metrics reveal">{metrics}</div>

<p class="section-note">
  Managing Director of Penn's Computational Social Science Lab and the Center for AI and
  Society, Executive Director of the International Society for Computational Social
  Science, and a Lecturer in Statistics and Data Science at the Wharton School.
</p>

<p class="section-label">Recent</p>
<ul class="news">{news_items}</ul>

<p class="section-label">Selected work</p>
<p class="section-note">The full record, grouped by status, is on the
  <a class="linky" href="/publications/">publications</a> page.</p>
{pub_list(featured)}

<p class="section-label">Elsewhere on this site</p>
<div class="card-grid card-grid--2">
  <a class="card" href="/research/">
    <p class="card-meta">Four strands</p>
    <h3>Research</h3>
    <p>Eviction as a networked legal process; robustness and spillover in network models;
       data quality and classifier behavior; and the methodology underneath.</p>
  </a>
  <a class="card" href="/teaching/">
    <p class="card-meta">Two decades</p>
    <h3>Teaching</h3>
    <p>Sample survey methods at Wharton, statistical learning and network analysis at
       Temple, and the courses I would build next.</p>
  </a>
  <a class="card" href="/students/">
    <p class="card-meta">Undergraduate research</p>
    <h3>Students</h3>
    <p>How I scope a project to one term, who I have worked with, and three questions a
       student could start on now.</p>
  </a>
  <a class="card" href="/leadership/">
    <p class="card-meta">$12M+ secured</p>
    <h3>Leadership &amp; grants</h3>
    <p>Two institutes directed, a $10M Knight Foundation award across six Penn schools,
       and grants from NSF and Templeton.</p>
  </a>
</div>
"""
    return page("index.html", "About", SITE["description"], body, is_home=True)


def build_research() -> str:
    areas = []
    for a in RESEARCH["areas"]:
        chips = "".join(f'<span class="chip">{esc(m)}</span>' for m in a.get("methods", []))
        papers = ""
        if a.get("papers"):
            links = "".join(
                f'<a href="{arxiv_url(pid)}" rel="noopener">arXiv:{pid}</a>'
                for pid in a["papers"]
            )
            papers = f'<p class="area-papers">{links}</p>'
        areas.append(f"""
<section class="area reveal" id="{a['id']}">
  <div class="area-num">{a['number']}</div>
  <div class="area-body">
    <h3>{esc(a['title'])}</h3>
    <p class="area-tagline">{esc(a['tagline'])}</p>
    <div class="area-text"><p>{esc(tidy(a['body']))}</p></div>
    <div class="chips">{chips}</div>
    {papers}
  </div>
</section>""")

    collabs = "".join(
        f'<div class="card reveal"><p class="card-meta">{esc(c["role"])}</p>'
        f"<h4>{esc(c['name'])}</h4><p>{esc(c['note'])}</p></div>"
        for c in RESEARCH["collaborators"]
    )

    body = f"""
<div class="prose">
  <p class="lede">
    My research sits between statistics and computational social science — between network
    models and causal inference, and between the survey and the machine that now answers
    it.
  </p>
  <p>
    The common thread is dependence that cannot be assumed away. When observations are
    connected, the network is not a nuisance parameter to be conditioned out; it is often
    the mechanism producing what we observe. That claim has a methodological half — what
    survives when a network is measured with error, or shifts underneath you — and an
    applied half, worked out in the legal infrastructure of eviction.
  </p>
</div>

<figure class="figure reveal">
  <svg viewBox="0 0 720 200" role="img" aria-labelledby="dia-title dia-desc">
    <title id="dia-title">Four research strands and how they connect</title>
    <desc id="dia-desc">An applied strand on eviction and a methods strand on robustness
      both draw on shared foundations in models and computation, and both feed a third
      strand on data quality and classifier behaviour.</desc>
    <defs>
      <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
      </marker>
    </defs>
    <g color="var(--line-strong)" stroke="currentColor" stroke-width="1.2" fill="none" marker-end="url(#ah)">
      <path d="M170 92 L270 62"/>
      <path d="M170 108 L270 138"/>
      <path d="M430 62 L530 92"/>
      <path d="M430 138 L530 108"/>
    </g>
    <g>
      <rect x="18" y="72" width="152" height="56" rx="9" fill="var(--panel)" stroke="var(--accent-line)" stroke-width="1.2"/>
      <text x="94" y="96" text-anchor="middle" font-family="'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace" font-size="10" fill="var(--accent)" letter-spacing="1.2">04 · FOUNDATIONS</text>
      <text x="94" y="113" text-anchor="middle" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="12" fill="var(--ink-soft)">Models &amp; computation</text>

      <rect x="272" y="32" width="158" height="58" rx="9" fill="var(--panel)" stroke="var(--line)" stroke-width="1.2"/>
      <text x="351" y="56" text-anchor="middle" font-family="'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace" font-size="10" fill="var(--accent)" letter-spacing="1.2">01 · APPLIED</text>
      <text x="351" y="73" text-anchor="middle" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="12" fill="var(--ink-soft)">Eviction as a network</text>

      <rect x="272" y="110" width="158" height="58" rx="9" fill="var(--panel)" stroke="var(--line)" stroke-width="1.2"/>
      <text x="351" y="134" text-anchor="middle" font-family="'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace" font-size="10" fill="var(--accent)" letter-spacing="1.2">02 · METHODS</text>
      <text x="351" y="151" text-anchor="middle" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="12" fill="var(--ink-soft)">Robustness &amp; spillover</text>

      <rect x="532" y="72" width="170" height="56" rx="9" fill="var(--panel)" stroke="var(--accent-line)" stroke-width="1.2"/>
      <text x="617" y="96" text-anchor="middle" font-family="'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace" font-size="10" fill="var(--accent)" letter-spacing="1.2">03 · MEASUREMENT</text>
      <text x="617" y="113" text-anchor="middle" font-family="Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="12" fill="var(--ink-soft)">Data quality &amp; classifiers</text>
    </g>
  </svg>
  <figcaption>
    <b>How the strands connect.</b> Shared methodology feeds both an applied programme on
    eviction and a methodological one on robustness; each in turn raises the same question
    about measurement — what a model does when the data it was trained on is imperfect.
  </figcaption>
</figure>

{''.join(areas)}

<p class="section-label">Long-running collaborations</p>
<div class="card-grid">{collabs}</div>

<div class="callout reveal">
  <p class="callout-title">Statements</p>
  <p>A fuller account is in my
     <a class="linky" href="/files/Ruane_Research_Statement.pdf">research statement (PDF)</a>,
     and the complete publication record is on the
     <a class="linky" href="/publications/">publications page</a>.</p>
</div>
"""
    return page(
        "research/index.html",
        "Research",
        "Statistical network models, causal inference under interference, robustness under "
        "measurement error, and the quantitative study of eviction as a legal process.",
        body,
        subtitle="Four strands, one problem: dependence that cannot be assumed away.",
    )


def build_publications() -> str:
    used_topics = set()
    for p in all_pubs():
        used_topics.update(p.get("topics") or [])

    filters = ['<button class="filter-btn is-active" data-filter="all" aria-pressed="true">All</button>']
    for key, label in TOPIC_LABELS.items():
        if key in used_topics:
            filters.append(
                f'<button class="filter-btn" data-filter="{key}" aria-pressed="false">{label}</button>'
            )

    groups = [
        ("Published &amp; accepted", "published"),
        ("Under review", "review"),
        ("Preprints", "preprints"),
        ("In preparation", "working"),
    ]
    sections = []
    for label, key in groups:
        items = PUBS.get(key) or []
        if not items:
            continue
        items = sorted(items, key=lambda p: (-int(p.get("year") or 0), p["title"]))
        sections.append(
            f'<div data-pub-group><p class="section-label">{label}</p>{pub_list(items)}</div>'
        )

    # "Also" links at the foot of the page — each included only if set in site.yml
    also = []
    if SITE["author"].get("scholar"):
        also.append(f'<a class="linky" href="{SITE["author"]["scholar"]}" rel="noopener">Google Scholar profile</a>')
    if SITE["author"].get("arxiv"):
        also.append(f'<a class="linky" href="{SITE["author"]["arxiv"]}" rel="noopener">arXiv listing</a>')
    also.append('<a class="linky" href="/talks/">conference presentations</a>')
    also_html = " · ".join(also)

    body = f"""
<div class="prose">
  <p>
    Author order in statistics is alphabetical in some of these venues and
    contribution-ordered in others; where a paper is joint with Marios Papamichalis, the
    work is genuinely shared. arXiv identifiers link to the current version.
  </p>
</div>

<div class="pub-filters" role="group" aria-label="Filter publications by topic">{''.join(filters)}</div>

<p class="pub-empty">No papers match that filter.</p>

{''.join(sections)}

<div class="callout">
  <p class="callout-title">Also</p>
  <p>{also_html}</p>
</div>
"""
    return page(
        "publications/index.html",
        "Publications",
        "Papers and preprints on statistical network models, robustness, causal inference, "
        "and the legal infrastructure of eviction.",
        body,
        subtitle="Grouped by status. Filter by topic below.",
    )


def build_teaching() -> str:
    blocks = []
    for group in TEACHING["courses"]:
        rows = []
        for c in group["items"]:
            note = f'<p class="course-note">{esc(c["note"])}</p>' if c.get("note") else ""
            rows.append(f"""
      <div class="course">
        <div class="course-code">{esc(c['code'])}</div>
        <div>
          <p class="course-title">{esc(c['title'])}</p>
          <p class="course-level">{c['level']}</p>
          {note}
        </div>
      </div>""")
        dot = '<span class="now" aria-label="current"></span>' if group.get("current") else ""
        blocks.append(f"""
<section class="reveal">
  <p class="section-label">{group['institution']} &nbsp;·&nbsp; {group['years']}{dot}</p>
  {''.join(rows)}
</section>""")

    proposed = "".join(
        f'<div class="card reveal"><h4>{esc(c["title"])}</h4><p>{esc(tidy(c["blurb"]))}</p></div>'
        for c in TEACHING["proposed"]
    )

    body = f"""
<div class="prose">
  <p class="lede">
    An inclusive classroom, in my experience, is built with a real question, real data, and
    the chance for students to see the result themselves.
  </p>
  <p>
    My master's is in curriculum and teaching from Columbia, and I began in classrooms in
    Germany and Poland, where I was named Teacher of the Year. Two decades later the method
    has not changed much: start from a question about a student's neighbourhood, career, or
    interest, and let the statistics arrive as the thing that answers it.
  </p>
  <p>
    Three commitments organise the work. <strong>Interdisciplinary integration</strong> —
    with appointments across data science, engineering, business, and education, I design
    courses that put statistics, machine learning, and network science inside
    application-rich contexts. <strong>Research-informed instruction</strong> — live coding
    in R and Python, anonymised real datasets, and class projects aligned with my own
    applied work; students in my social network analysis course have worked on digital
    interaction data from city policy interventions.
    <strong>Inclusive and adaptive pedagogy</strong> — I have taught undergraduates through
    doctoral students, in traditional, executive, hybrid, and online formats, and use
    backward design and formative assessment to scaffold across that range.
  </p>
</div>

<div class="pull reveal">
  Students commented that the guest speakers transformed their career trajectories and
  inspired them to study more. That is the return on treating a course as a door rather
  than a requirement.
  <cite>From the teaching statement</cite>
</div>

{''.join(blocks)}

<p class="section-label">Courses I would build</p>
<div class="card-grid">{proposed}</div>

<div class="callout reveal">
  <p class="callout-title">Statement</p>
  <p>The full <a class="linky" href="/files/Ruane_Teaching_Statement.pdf">teaching statement (PDF)</a>,
     and how I run undergraduate research on the <a class="linky" href="/students/">students page</a>.</p>
</div>
"""
    return page(
        "teaching/index.html",
        "Teaching",
        "Sample survey methods, statistical learning, and social network analysis — taught "
        "from real questions with real data, across undergraduate and doctoral levels.",
        body,
        subtitle="Courses taught, and courses I would build next.",
    )


def build_students() -> str:
    principles = "".join(
        f'<div class="card reveal"><h4>{esc(p["title"])}</h4><p>{esc(tidy(p["body"]))}</p></div>'
        for p in STUDENTS["principles"]
    )

    projects = "".join(f"""
<div class="entry reveal">
  <div class="entry-years">{esc(p['scope'])}</div>
  <div class="entry-body">
    <p class="entry-title">{esc(p['title'])}</p>
    <p class="entry-prereq">Needs: {esc(p['prereq'])}</p>
    <p>{esc(tidy(p['body']))}</p>
  </div>
</div>""" for p in STUDENTS["projects"])

    mentees = "".join(f"""
<div class="card reveal">
  <p class="card-meta">{esc(m['then'])}</p>
  <h4>{esc(m['name'])}</h4>
  <p>{esc(tidy(m['note']))}</p>
  {'<p class="card-meta" style="margin:.6rem 0 0">Now · ' + esc(m['now']) + '</p>' if m['now'] != '—' else ''}
</div>""" for m in STUDENTS["mentees"])

    body = f"""
<div class="prose">
  <p class="lede">
    Research at an undergraduate college can be immensely successful. I have seen it work
    at both Penn and Temple, and the benefit runs in both directions.
  </p>
  <p>
    Students have contributed real components to the teams I have led — verifying that news
    articles were correctly labelled in a media bias detector, engineering platform
    capabilities for a geolocation data repository. One of my undergraduate mentees at
    Temple, Srikar Katta, wrote his first publication with me; he is now a doctoral student
    in computer science at Duke, publishing in top venues.
  </p>
</div>

<p class="section-label">How I run it</p>
<div class="card-grid card-grid--2">{principles}</div>

<p class="section-label">Projects a student could start now</p>
<p class="section-note">Each is scoped so that a result exists at the end of one ten-week
  term, and so that it can grow if the student stays.</p>
<div class="entries">{projects}</div>

<p class="section-label">Students I have worked with</p>
<div class="card-grid">{mentees}</div>

<div class="callout reveal">
  <p class="callout-title">Get in touch</p>
  <p>If one of these questions interests you, or you have one of your own,
     <a class="linky" href="mailto:{SITE['author']['email']}">write to me</a>.
     A statistics course and a programming course are enough to begin.</p>
</div>
"""
    return page(
        "students/index.html",
        "Students &amp; mentoring",
        "Undergraduate research mentoring: how I scope a project to one term, students I "
        "have worked with, and three questions a student could start on now.",
        body,
        subtitle="Undergraduate research, scoped to a term.",
    )


def build_leadership() -> str:
    roles = []
    for r in LEADERSHIP["roles"]:
        dot = '<span class="now" aria-label="current"></span>' if r.get("current") else ""
        pts = ""
        if r.get("points"):
            pts = "<ul>" + "".join(f"<li>{esc(p)}</li>" for p in r["points"]) + "</ul>"
        inst = f'<p class="entry-org">{r["institution"]}</p>' if r.get("institution") else ""
        roles.append(f"""
<div class="entry reveal">
  <div class="entry-years">{r['years']}{dot}</div>
  <div class="entry-body">
    <p class="entry-title">{r['title']}</p>
    <p class="entry-sub">{r['org']}</p>
    {inst}
    <p>{esc(tidy(r['blurb']))}</p>
    {pts}
  </div>
</div>""")

    grants = []
    for g in LEADERSHIP["grants"]:
        period = f'<span class="grant-period">{esc(g["period"])}</span>' if g.get("period") and g["period"] != "—" else ""
        pis = f' <span class="grant-role">{esc(g["pis"])}</span>' if g.get("pis") else ""
        grants.append(f"""
<li class="grant reveal">
  <div>
    <p class="grant-title">{g['title']}</p>
    <p class="grant-funder">{g['funder']}</p>
    <p class="grant-role">{esc(g['role'])}{pis}</p>
  </div>
  <div>
    <span class="grant-amount">{esc(g['amount'])}</span>
    {period}
  </div>
</li>""")

    consulting = "".join(
        f'<div class="card reveal"><p class="card-meta">{esc(c["location"])} · {c["years"]}</p>'
        f"<h4>{c['org']}</h4><p>{esc(tidy(c['blurb']))}</p></div>"
        for c in LEADERSHIP["consulting"]
    )

    service = "".join(
        f'<div class="course"><div class="course-code">{esc(s["year"])}</div>'
        f'<div><p class="course-title">{esc(s["org"])}</p>'
        f'<p class="course-level">{esc(s["role"])}</p></div></div>'
        for s in LEADERSHIP["service"]
    )

    body = f"""
<div class="prose">
  <p class="lede">
    For six years I have built and run research institutes. Institution-building carries
    steadily outward from the two things that drew me to this profession: problems to solve,
    and students.
  </p>
</div>

<p class="section-label">Funding secured</p>
<ol class="grant-list" style="list-style:none">{''.join(grants)}</ol>

<p class="section-label">Roles</p>
<div class="entries">{''.join(roles)}</div>

<p class="section-label">Consulting</p>
<div class="card-grid">{consulting}</div>

<p class="section-label">Professional service</p>
<div>{service}</div>
"""
    return page(
        "leadership/index.html",
        "Leadership &amp; grants",
        "Directing Penn's Computational Social Science Lab and ISCSS, a $10M Knight "
        "Foundation award across six schools, and grants from NSF and Templeton.",
        body,
        subtitle="Two institutes, a conference, and $12M+ in research funding.",
    )


def build_talks() -> str:
    items = sorted(TALKS, key=lambda t: -int(t.get("year") or 0))
    rows = []
    for t in items:
        kind = f' <span class="tag tag-muted">{esc(t["kind"])}</span>' if t.get("kind") else ""
        rows.append(f"""
<div class="talk reveal">
  <div class="talk-date">{esc(t['date'])}</div>
  <div>
    <p class="talk-title">{esc(t['title'])}{kind}</p>
    <p class="talk-authors">{bold_self(t['authors'])}</p>
    <p class="talk-venue">{esc(t['venue'])} <span class="loc">· {esc(t['location'])}</span></p>
  </div>
</div>""")

    news_items = "".join(
        f'<li><span class="news-date">{esc(n["date"])}</span>'
        f'<p class="news-text">{md_inline(n["text"])}</p></li>'
        for n in NEWS
    )

    body = f"""
<p class="section-label">News</p>
<ul class="news">{news_items}</ul>

<p class="section-label">Conference presentations</p>
<div>{''.join(rows)}</div>
"""
    return page(
        "talks/index.html",
        "Talks &amp; news",
        "Conference presentations and recent news, from computational social science and "
        "statistics venues to educational research meetings.",
        body,
        subtitle="Presentations and recent updates.",
    )


def build_cv() -> str:
    edu = "".join(f"""
<div class="entry">
  <div class="entry-years">{e['years']}</div>
  <div class="entry-body">
    <p class="entry-title">{e['degree']}</p>
    <p class="entry-sub">{e['institution']}</p>
  </div>
</div>""" for e in CV["education"])

    pos = []
    for p in CV["positions"]:
        dot = '<span class="now" aria-label="current"></span>' if p.get("current") else ""
        sub = f'<p class="entry-sub">{p["sub"]}</p>' if p.get("sub") else ""
        pos.append(f"""
<div class="entry">
  <div class="entry-years">{p['years']}{dot}</div>
  <div class="entry-body">
    <p class="entry-title">{p['title']}</p>
    {sub}
    <p class="entry-org">{p['org']}</p>
  </div>
</div>""")

    expertise = "".join(
        f'<div class="card"><p class="card-meta">{g["group"]}</p>'
        + '<div class="chips">'
        + "".join(f'<span class="chip">{i}</span>' for i in g["items"])
        + "</div></div>"
        for g in CV["expertise"]
    )

    awards = "".join(
        f'<div class="course"><div class="course-code">{esc(a["year"])}</div>'
        f'<div><p class="course-title">{esc(a["name"])}</p></div></div>'
        for a in CV["awards"]
    )

    refs = "".join(
        f'<div class="card"><h4>{esc(r["name"])}</h4>'
        f'<p>{esc(r["title"])}</p>'
        f'<p class="card-meta" style="margin:.5rem 0 0">{r["org"]}</p>'
        f'<p style="margin-top:.35rem"><a class="linky" href="mailto:{r["email"]}">{r["email"]}</a></p></div>'
        for r in CV["references"]
    )

    counts = {k: len(PUBS.get(k) or []) for k in ("published", "review", "preprints", "working")}

    body = f"""
<div class="hero-actions" style="margin-bottom:2.4rem">
  <a class="btn btn-primary" href="{SITE['author']['cv']}">Download CV (PDF) {ICONS['arrow']}</a>
  <a class="btn" href="/files/Ruane_Research_Statement.pdf">Research statement</a>
  <a class="btn" href="/files/Ruane_Teaching_Statement.pdf">Teaching statement</a>
</div>

<p class="section-label">Education</p>
<div class="entries">{edu}</div>
<p class="section-note" style="margin-top:1.2rem">{esc(tidy(CV['postgraduate']))}</p>

<p class="section-label">Appointments</p>
<div class="entries">{''.join(pos)}</div>

<p class="section-label">Expertise</p>
<div class="card-grid">{expertise}</div>

<p class="section-label">Publications at a glance</p>
<div class="metrics">
  <div class="metric"><span class="metric-value">{counts['published']}</span><span class="metric-label">Published &amp; accepted</span></div>
  <div class="metric"><span class="metric-value">{counts['review']}</span><span class="metric-label">Under review</span></div>
  <div class="metric"><span class="metric-value">{counts['preprints']}</span><span class="metric-label">Preprints</span></div>
  <div class="metric"><span class="metric-value">{counts['working']}</span><span class="metric-label">In preparation</span></div>
</div>
<p class="section-note" style="margin-top:.9rem">
  Full list on the <a class="linky" href="/publications/">publications page</a>;
  presentations on the <a class="linky" href="/talks/">talks page</a>.
</p>

<p class="section-label">Awards</p>
<div>{awards}</div>

<p class="section-label">Languages</p>
<p class="section-note">{CV['languages']}</p>

<p class="section-label">References</p>
<div class="card-grid">{refs}</div>
"""
    return page(
        "cv/index.html",
        "Curriculum vitae",
        "Education, appointments, expertise, awards, and references for Regina Ruane, Ph.D.",
        body,
        subtitle="The short version. The PDF has everything.",
    )


def build_404() -> str:
    body = """
<div class="prose">
  <h1 style="margin-top:2rem">404</h1>
  <p>That page does not exist. Try the navigation, or start from the
     <a class="linky" href="/">front page</a>.</p>
</div>
"""
    return head("Not found", "Page not found", "/404.html") + sidebar("/") + body + footer()


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

PAGES = {
    "index.html": build_home,
    "research/index.html": build_research,
    "publications/index.html": build_publications,
    "teaching/index.html": build_teaching,
    "students/index.html": build_students,
    "leadership/index.html": build_leadership,
    "talks/index.html": build_talks,
    "cv/index.html": build_cv,
    "404.html": build_404,
}


def sitemap() -> str:
    base = SITE["url"].rstrip("/")
    urls = "".join(
        f"  <url><loc>{base}{href}</loc></url>\n" for _, _, href, _ in NAV
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n"
    )


def main() -> None:
    global _DEPTH
    out_root = OUT
    for rel, fn in PAGES.items():
        _DEPTH = rel.count("/")
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rewrite(fn()), encoding="utf-8")
        print(f"  wrote {dest.relative_to(OUT)}")

    (OUT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['url'].rstrip('/')}/sitemap.xml\n",
        encoding="utf-8",
    )
    # tell GitHub Pages not to run Jekyll over these files
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print("  wrote sitemap.xml, robots.txt, .nojekyll")
    print(f"\nDone — {len(PAGES)} pages.")

    if "--serve" in sys.argv:
        import http.server
        import socketserver

        os.chdir(OUT)
        port = 8000
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Serving on http://localhost:{port}  (ctrl-c to stop)")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
