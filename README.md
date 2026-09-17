# reginaruane.github.io

Academic website for Regina (Jeanne) Ruane, Ph.D. — statistician, University of
Pennsylvania.

Plain static HTML. No Jekyll, no Ruby, no build step on GitHub's side, so nothing
can fail at deploy time. Content lives in `_data/*.yml`; a small Python script
regenerates the HTML from it.

Every link in the site is relative, so it works wherever it is served from — a
user site at the domain root, a project site in a `/reponame/` subfolder, a
custom domain, or just opened from your own hard drive. Nothing has to match a
particular repository or account name.

---

## Putting it online

1. Upload everything in this folder to the **root** of the repository — so that
   `index.html` is visible on the repo's Code tab, not inside another folder.
   Drag the files into GitHub's web uploader, or:

   ```bash
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/<username>/<reponame>.git
   git push -u origin main
   ```

2. In the repository, go to **Settings → Pages**. Under *Source*, choose
   **Deploy from a branch** — not "GitHub Actions", which waits for a workflow
   file that this site does not use and never deploys without one. Set the
   branch to `main` and the folder to `/ (root)`, then Save.

3. Wait one to three minutes and reload that settings page. A green banner
   appears with the live address.

**Which address you get.** GitHub serves a repository named exactly
`<username>.github.io` at `https://<username>.github.io`. Any other repository
name is served at `https://<username>.github.io/<reponame>/` instead. Both work
with these files. To get the short address, the repository name and the account
name have to match — note that the *username* is changed under
**Settings → Account**, which is a different field from the display name under
Settings → Public profile.

Once the address is settled, set `url:` in `_data/site.yml` and re-run
`build.py` so the canonical and social-preview tags point at the right place.
Leaving it blank just omits those tags; nothing breaks.

---

## Changing the content

Everything editable is in `_data/`:

| File | What's in it |
| --- | --- |
| `site.yml` | Name, title, email, links, the four numbers on the home page |
| `publications.yml` | Every paper, grouped by status |
| `news.yml` | The "Recent" list on the home page and the talks page |
| `research.yml` | The four research strands and the collaborator grid |
| `teaching.yml` | Courses taught, and courses to build |
| `students.yml` | Mentees, project ideas, mentoring principles |
| `leadership.yml` | Roles, grants, consulting, service |
| `talks.yml` | Conference presentations |
| `cv.yml` | Education, appointments, expertise, awards, references |

After editing, regenerate the HTML:

```bash
pip install pyyaml        # first time only
python3 build.py
```

Then commit and push. To preview locally before pushing:

```bash
python3 build.py --serve  # then open http://localhost:8000
```

You can also just double-click `index.html` to open the site from disk — the
relative links mean it works without a server at all.

### Adding a paper

Open `_data/publications.yml`, copy an existing entry, and edit it. The four
groups are `published`, `review`, `preprints`, and `working`; move an entry
between them as its status changes. Set `featured: true` to put it in "Selected
work" on the home page (the six most recent featured papers are shown). Add
`topics:` so the topic filters pick it up.

You can also edit the generated `.html` files directly if you prefer — the build
script will overwrite them next time it runs, so make the change in the YAML if
you want it to stick.

---

## Replacing the PDFs

`files/` holds the CV, research statement, and teaching statement. Replace them
with new PDFs under the same filenames and the links keep working:

- `files/Ruane_CV.pdf`
- `files/Ruane_Research_Statement.pdf`
- `files/Ruane_Teaching_Statement.pdf`

These were converted from the Word originals; if the formatting matters, export
fresh PDFs from Word and drop them in.

---

## How it's put together

```
_data/            content (YAML)
assets/css/       one stylesheet — design tokens at the top
assets/js/        theme toggle, nav, publication filters, the hero network
images/           portrait and favicon
files/            CV and statements
build.py          generates the HTML
index.html …      generated — don't edit by hand if you use build.py
```

**Theme.** Dark by default, with a light mode on the toggle in the sidebar. The
choice is remembered per browser. To make light the default instead, swap the
two blocks at the top of `assets/css/main.css` — or just change
`data-theme="dark"` in `build.py`'s `head()` function to `"light"`.

**Colours.** All of them are CSS custom properties in `:root` (dark) and
`html[data-theme="light"]` at the top of `assets/css/main.css`. Change the
`--accent` values to reskin the whole site. The current pair clears WCAG AA for
normal text against every background it's used on.

**The hero animation** is a small latent-space graph: nodes drift, and edges
appear between nodes closer than a fixed radius, so the graph rewires as it
moves. It pauses when scrolled out of view or when the tab is hidden, and renders
a single static frame for visitors who ask for reduced motion.

**The "Elsewhere" list** in the sidebar is built in `build.py`'s `sidebar()`
function. Each entry appears only when its value is filled in under `author:` in
`_data/site.yml`, so blanking a value removes the link instead of leaving a dead
one. arXiv is deliberately not in that list — it still appears at the foot of the
Publications page. The commented-out lines just above `profiles = []` show how to
put it back.

**Fonts** come from Google Fonts (Newsreader, Inter, IBM Plex Mono). If you'd
rather not depend on Google, download the files into `assets/fonts/`, add
`@font-face` rules, and delete the three `fonts.` lines in `build.py`'s `head()`.
The fallback stack is decent, so nothing breaks if the CDN is blocked.

---

## Checked

Built and verified before hand-off: every internal link resolves from its own
page's directory, no failed requests, no JavaScript errors, one `<h1>` per page,
no horizontal overflow at 390 / 1024 / 1440 px, topic filters and the theme
toggle round-trip correctly, and text/background contrast meets WCAG AA in both
themes. Confirmed rendering in all three serving contexts: domain root,
`/reponame/` subfolder, and opened directly from disk.
