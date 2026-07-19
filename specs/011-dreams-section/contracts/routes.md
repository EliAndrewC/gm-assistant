# Phase 1 Contract: Dreams Routes

Server-rendered pages on the L7R `Root`, mirroring `/relics`. Public access (root tree defaults to `min_role: anonymous`; no auth config change).

## GET /dreams

- **Purpose**: Landing page - the player-facing rules & framework, then the examples gallery.
- **Input**: none.
- **Renders**: `dreams_index.html` with:
  - `current_section='dreams'`
  - `framework_html` - `content/dreams_framework.md` rendered to HTML.
  - `scenes` - the loaded `list[DreamScene]`, sorted by title (each shown as a card: title, sender, summary, link to `/dreams/<slug>`).
- **Response**: 200, HTML.
- **Empty pool**: renders the framework and a graceful "no examples yet" state (never errors).

## GET /dreams/<slug>

- **Purpose**: Detail page - one full rendered scene.
- **Input**: `slug` (path segment).
- **Behavior**:
  - Look up the scene by slug. If not found → `_render_404()` (friendly 404), FR-009.
  - Otherwise render `dream_detail.html` with `current_section='dreams'` and `scene=<DreamScene>` (its `body_html`, `title`, `sender`).
- **Response**: 200 HTML on hit; 404 HTML on miss.

## Invariants (tested)

- **INV-1 (FR-007, load-bearing)**: No slug that exists only in `pool-local/` is ever resolvable. Given a public pool dir with a sibling `pool-local/` containing a decoy scene, `GET /dreams/<decoy-slug>` returns 404 and the decoy never appears in `scenes`. Enforced structurally (loader reads only the configured dir) and frozen by test.
- **INV-2 (FR-008)**: A malformed scene file in the public dir is absent from `scenes` (skipped with a logged warning), and the gallery still renders.
- **INV-3**: Adding a valid scene file to the public dir and reloading makes it appear in `scenes` and resolvable at its slug, with no code change (FR-006 / SC-003).
- **INV-4 (Principle I)**: Both pages pass `dom_audit.py` (zero issues) at GM-100 / GM-200 / tablet / mobile.

## Navigation contract

- `sections.py` gains `Section(slug='dreams', label='Dreams', path='/dreams', enabled=True)`, placed after `places` (order: Characters, Relics, Names, Places, Dreams). The shared `_layout.html` nav renders it automatically. SC-002: from the nav, a full scene is reachable in ≤ 2 clicks (nav → /dreams → scene).
