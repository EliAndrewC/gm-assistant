# HTTP Routes — L7R Toolkit Phase 1

The L7R Toolkit serves HTML responses (no JSON API in Phase 1). Static assets are served by CherryPy's `tools.staticdir`. The contract is the set of routes, their methods, and what they render.

## New routes (l7r package)

| Method | Path                | Renders                                           | Notes                                                        |
|--------|---------------------|---------------------------------------------------|--------------------------------------------------------------|
| GET    | `/`                 | `landing.html`                                    | Toolkit landing page                                         |
| GET    | `/relics`           | `relics_index.html`                               | All 42 relics grouped by Fortune                             |
| GET    | `/relics/<slug>`    | `relic_detail.html` or 404                        | Detail view; 404 if slug unknown                             |
| GET    | `/names`            | `names_placeholder.html`                          | Coming-soon placeholder for Phase 1.5                        |
| GET    | `/static/css/l7r.css` | CSS file                                        | Design system                                                |
| GET    | `/static/js/l7r.js`   | JS file                                         | Seal-filter behavior                                         |

## Legacy chargen routes (preserved at new prefix)

| Method   | Path                | Description                                      |
|----------|---------------------|--------------------------------------------------|
| GET      | `/chargen`          | Modernized chargen UI (extends `_layout.html`)   |
| GET/POST | `/chargen/generate` | Existing chargen `/generate` (renamed)           |
| POST     | `/chargen/upload`   | Existing chargen `/upload` (renamed)             |
| ...      | `/chargen/...`      | Any other existing chargen endpoint              |

Chargen's frontend JS must be updated to call `/chargen/<endpoint>` paths.

## Error responses

| Status | When                                  | Body                                              |
|--------|---------------------------------------|---------------------------------------------------|
| 404    | Unknown relic slug or unknown path    | `_404.html` rendered inside `_layout.html`        |
| 500    | Unhandled server error                | CherryPy default error page (acceptable Phase 1)  |

## Response headers

- `Content-Type: text/html; charset=utf-8` for HTML routes
- `Content-Type: text/css` for CSS, `application/javascript` for JS (CherryPy auto-sets)
- No cache headers explicitly set in Phase 1 (CherryPy defaults apply)

## CherryPy integration

```python
# l7r/app.py — top-level Root
class Root:
    def __init__(self, relics: list[Relic]) -> None: ...

    @cherrypy.expose
    def index(self) -> bytes: ...           # GET /

    @cherrypy.expose
    def relics(self, slug: str | None = None) -> bytes: ...  # GET /relics, GET /relics/<slug>

    @cherrypy.expose
    def names(self) -> bytes: ...           # GET /names

# Chargen wiring (in entry point):
# cherrypy.tree.mount(L7RRoot(relics=relics), '/')
# cherrypy.tree.mount(ChargenRoot(),          '/chargen')
```

## Contracts summary

The contracts that matter for tests:
1. `GET /` returns 200 with `<title>L7R Toolkit</title>` (or similar) in HTML.
2. `GET /relics` returns 200 with 42 `.card` elements and 7 `.fortune-section` elements.
3. `GET /relics/honest-masu-of-yasuki-bunzo` returns 200 with the relic's kanji rendered.
4. `GET /relics/this-slug-does-not-exist` returns 404 with the shared shell.
5. `GET /names` returns 200 with a placeholder message.
6. `GET /chargen` returns 200 with chargen's existing form fields.
