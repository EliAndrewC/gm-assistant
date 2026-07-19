# Phase 1 Data Model: Dreams Section

## Entity: DreamScene

One worked, spoiler-safe example of dream divination, loaded from a public pool markdown file. Frozen dataclass in `l7r/dreams.py`, mirroring `l7r/pool.py::Relic`.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `slug` | `str` | filename stem | URL id, e.g. `daikoku-masamune-sword-akishi`. Stable, human-readable. |
| `name` | `str` | frontmatter `name` | Internal id (matches slug in practice). Required. |
| `title` | `str` | frontmatter `title` | Display title for card + detail header. Required. |
| `sender` | `str` | frontmatter `sender` | The god/spirit consulted, e.g. "Daikoku, the Fortune of Wealth and Bounty". Required. |
| `sender_type` | `str` | frontmatter `sender_type` | e.g. `fortune`. Optional; defaults to `fortune`. |
| `summary` | `str` | frontmatter `setting` or derived | Short descriptor for the gallery card. Falls back to the first sentence of the body's intro if absent. |
| `body_html` | `str` | rendered markdown body | The full scene rendered to sanitized HTML via `markdown-it-py` (CommonMark + tables, raw-HTML disabled). |

**Frontmatter fields read but not surfaced as columns** (kept for card/metadata / future use): `split_mentality`, `split_factor`, `attunement`, `bands`, `roll`, `partition`, `setting`. The loader may retain a raw `meta: dict` for flexibility, but MUST NOT require optional keys.

### Required vs optional

- **Required** (a file missing any of these is skipped with a logged warning - FR-008): `name`, `title`, `sender`, and a non-empty body.
- **Optional**: everything else, with sensible defaults.

### Validation / loading rules

1. Only files directly under the single configured public pool dir are read. The loader never traverses to a sibling `pool-local/` (FR-007). No `tier:`/`spoiler:` frontmatter value can cause a `pool-local/` file to be read, because that directory is never scanned.
2. Frontmatter is split with the same `^---\n(.*?)\n---\n(.*)$` approach as `pool.py`; a file without valid frontmatter is skipped with a warning.
3. Scenes are returned sorted by `title` (deterministic order for the gallery).
4. `slug` uniqueness: if two files produce the same stem, later-sorted wins with a logged warning (defensive; not expected).

### Derived / rendering

- `body_html` is produced once at load time (startup), not per request, matching how relics are parsed once. The markdown renderer instance is module-level and reused.
- The body is trusted GM/dev-authored content, but the renderer runs with raw-HTML **disabled** as defense-in-depth; only markdown constructs (headings, lists, blockquotes, emphasis, tables) become HTML.

## Not modeled

- No per-scene GM-only vs public sub-sections: public examples render in full (design notes included). Spoiler protection is the tier boundary, not intra-scene hiding (spec Assumptions).
- No user state, no persistence, no write path.
