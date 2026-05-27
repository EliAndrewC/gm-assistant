# Phase 0 Research: L7R Toolkit Phase 1

**Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md)

## Open questions resolved

### 1. YAML frontmatter parsing

**Decision**: Use `pyyaml` to parse frontmatter, regex to split frontmatter from body.

**Rationale**: The pool files all use a simple frontmatter block (`---\nkey: value\n---\nbody`). Full markdown parsing isn't needed — body content is rendered as paragraphs with `*italic*` runs. `pyyaml.safe_load()` handles the frontmatter cleanly with proper type-aware parsing (strings, lists if we add them later). Lighter than `python-frontmatter` and we already have it.

**Alternatives considered**:
- *Hand-rolled parser per line*: works but doesn't handle quoted values, lists, multi-line strings well. Rejected.
- *python-frontmatter package*: adds a dep for a thin wrapper around pyyaml. Rejected — we control the format and pyyaml is plenty.
- *Full markdown parser (`markdown-it-py` or `mistune`)*: overkill for the body content, which is paragraph + `*em*`. Rejected.

### 2. CherryPy routing strategy

**Decision**: Single top-level `Root` class in `l7r.app`. Sub-mount the legacy chargen `Root` instance at `/chargen` via `cherrypy.tree.mount` or as a sub-controller attribute.

**Rationale**: This separates routing concerns cleanly. The new `l7r.app:Root` owns `/`, `/relics*`, `/names`. Chargen's `Root` owns `/chargen*`. The two are constructed independently and either can be tested independently. The cost is updating chargen's frontend AJAX URLs from `/generate` to `/chargen/generate` — but this is mechanical and small.

**Alternatives considered**:
- *Keep chargen routes at root*: Convenient for chargen but creates a confused single Root class that's "L7R" but contains chargen-specific endpoints. Rejected.
- *Use cherrypy.dispatch.MethodDispatcher*: requires more refactoring of chargen routes; rejected for Phase 1.

### 3. Shared Jinja2 environment across packages

**Decision**: One Jinja2 `Environment` constructed in `l7r.jinja_env`, with a `ChoiceLoader` that looks in `l7r/templates/` first, then `chargen/templates/`. Both packages render through the same env.

**Rationale**: Allows chargen's `index.html` to `{% extends "_layout.html" %}` where `_layout.html` is in `l7r/templates/`. Also makes filter / global additions live in one place.

**Alternatives considered**:
- *Two separate Jinja environments*: chargen's existing env stays; l7r gets its own. But then chargen's template can't extend the shared layout without duplicating the layout file. Rejected.

### 4. Pool data: load at startup vs. per request

**Decision**: Load all 42 relics once at process startup, cache in memory as a `list[Relic]`. Restart-to-refresh.

**Rationale**: Pool is small (~250 KB total), parsing is fast (~ms), and the data doesn't change while the server is running on localhost. Caching avoids re-parsing on every request and simplifies request handlers. Hot reloading is out of scope for Phase 1.

**Alternatives considered**:
- *Per-request load*: simpler code path, slower per request. Acceptable for 42 files but not the right pattern.
- *Watch-based reload*: requires inotify/watchdog; overkill.

### 5. Slug derivation for `/relics/<slug>`

**Decision**: Slug = the markdown filename's basename without `.md` extension (e.g., `honest-masu-of-yasuki-bunzo.md` → `honest-masu-of-yasuki-bunzo`). Stored as `Relic.slug`.

**Rationale**: The pool filenames are already kebab-case. Reusing them as URL slugs avoids ambiguity and keeps the mapping bidirectional and obvious.

**Alternatives considered**:
- *Slugify from name field*: introduces slug drift if the name changes; rejected.

### 6. 404 handling inside the shell

**Decision**: Register a CherryPy `request.error_response` handler that renders `_404.html` extending `_layout.html`.

**Rationale**: A 404 from a bad relic slug should look like the rest of the toolkit, not a CherryPy default error page. Plays nicely with the shared shell.

### 7. Static asset serving

**Decision**: CherryPy `tools.staticdir` mounted at `/static` pointing at `l7r/static/`.

**Rationale**: Standard CherryPy pattern. Chargen already uses similar patterns. CSS and JS are served directly without templating.

### 8. The Google Fonts dependency

**Decision**: Continue loading Fraunces / EB Garamond / Shippori Mincho from `fonts.googleapis.com` via `<link>` in `_layout.html`.

**Rationale**: The prototype already uses this. Self-hosting fonts is a Phase 2/3 concern (when we're on Fly.io with offline-capable behavior in mind).

**Alternatives considered**:
- *Self-host fonts*: better for offline / privacy, but adds 5-10 MB of font files. Defer.

### 9. Coverage measurement for `l7r/`

**Decision**: `pytest --cov=l7r --cov-fail-under=100` on the `l7r/` package only. Chargen excluded (already in pyproject.toml).

**Rationale**: Principle X says pure-logic packages get 100% coverage. CherryPy controllers in `l7r.app` are integration tested with `cherrypy.test.helper.CPWebCase` style or by calling handler methods directly with mock requests; route registration is tested via integration. The dataclasses and loaders in `pool.py` and `slugs.py` and `sections.py` are pure logic.

### 10. The chargen template's "config in HTML" issue

**Decision**: Acknowledge and defer. Chargen continues to serialize its config (including secrets) into its HTML page. This is acceptable for localhost-only Phase 1. Phase 2 will refactor chargen to not serialize secrets, in conjunction with adding auth for Fly.io deployment.

**Rationale**: Fixing this requires changes to chargen's frontend JS which is in scope for Phase 2 (Claude API integration is when we revisit chargen's data plumbing).

## Decisions summary

| # | Topic                          | Decision                                                          |
|---|--------------------------------|-------------------------------------------------------------------|
| 1 | Frontmatter parsing            | pyyaml + regex split                                              |
| 2 | Routing                        | Single l7r Root; sub-mount chargen at /chargen                    |
| 3 | Jinja environment              | Shared env via ChoiceLoader (l7r first, chargen second)           |
| 4 | Pool loading                   | Once at startup, cached in memory                                 |
| 5 | Slug derivation                | Markdown filename basename                                        |
| 6 | 404 handling                   | Custom error page using shared layout                             |
| 7 | Static assets                  | CherryPy tools.staticdir at /static                               |
| 8 | Google Fonts                   | CDN load from fonts.googleapis.com (defer self-hosting to Phase 2)|
| 9 | Coverage scope                 | l7r/ only at 100%; chargen on grace period                        |
| 10| Chargen config-in-HTML        | Defer to Phase 2 with auth work                                   |

All NEEDS CLARIFICATION resolved. Ready for Phase 1 design.
