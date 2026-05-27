# Phase 1 Data Model: L7R Toolkit Phase 1

**Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)

## Entities

### Relic

Loaded from `/workspace/.claude/skills/relic/pool/<fortune>/<slug>.md`.

```python
@dataclass(frozen=True, slots=True)
class Relic:
    slug: str              # filename basename without .md
    name: str              # frontmatter `name`
    japanese_romaji: str   # frontmatter `japanese_romaji`
    japanese_kanji: str    # frontmatter `japanese_kanji`
    fortune: str           # frontmatter `fortune` (slug)
    clan: str              # frontmatter `clan` (slug or "any")
    temple: str            # frontmatter `temple`
    named_entity: str      # frontmatter `named_entity`
    relic_type: str        # frontmatter `relic_type` (full, including parenthetical)
    description: str       # body prose, multi-paragraph
```

**Validation rules** (enforced by `pool.load_relics`):
- All frontmatter fields above are required. Missing field → log warning, skip file.
- `fortune` must be one of the seven Fortune slugs (see `FORTUNES` registry below).
- `clan` must be one of the known clan slugs or `"any"` (see `CLANS` registry below).
- `description` is the trimmed body (the prose between the closing `---` and EOF).

**Derived view properties** (computed in templates / handlers, not stored):
- `relic_type_short`: the part before `(`, used in card top strips
- `description_html`: paragraphs wrapped in `<p>`, `*italic*` → `<em>` (rendered by a Jinja filter)

---

### Fortune

A lookup record. Defined as a module-level constant — not loaded from files.

```python
@dataclass(frozen=True, slots=True)
class Fortune:
    slug: str       # e.g., "benten"
    name: str       # display label, e.g., "Benten"
    domain: str     # e.g., "Fortune of romantic love"
    kanji: str      # e.g., "弁天"

FORTUNES: dict[str, Fortune] = {
    "benten":      Fortune("benten",      "Benten",      "Fortune of romantic love",       "弁天"),
    "bishamon":    Fortune("bishamon",    "Bishamon",    "Fortune of strength",            "毘沙門"),
    "daikoku":     Fortune("daikoku",     "Daikoku",     "Fortune of wealth",              "大黒"),
    "ebisu":       Fortune("ebisu",       "Ebisu",       "Fortune of honest work",         "恵比寿"),
    "fukurokujin": Fortune("fukurokujin", "Fukurokujin", "Fortune of wisdom and mercy",    "福禄寿"),
    "hotei":       Fortune("hotei",       "Hotei",       "Fortune of contentment",         "布袋"),
    "jurojin":     Fortune("jurojin",     "Jurojin",     "Fortune of longevity",           "寿老人"),
}
```

---

### Clan

A lookup record for display labels. Defined as a module-level constant.

```python
CLANS: dict[str, str] = {
    "any":       "Anywhere",
    "crab":      "Crab",
    "crane":     "Crane",
    "dragon":    "Dragon",
    "fox":       "Fox",
    "lion":      "Lion",
    "mantis":    "Mantis",
    "phoenix":   "Phoenix",
    "scorpion":  "Scorpion",
    "sparrow":   "Sparrow",
    "unicorn":   "Unicorn",
    "wasp":      "Wasp",
    "dragonfly": "Dragonfly",
    "hare":      "Hare",
}
```

---

### Section

Nav registry entry. Single source of truth for the nav.

```python
@dataclass(frozen=True, slots=True)
class Section:
    slug: str       # e.g., "relics", "chargen", "names"
    label: str      # display label, e.g., "Relics"
    path: str       # URL path, e.g., "/relics"
    enabled: bool   # True if functional this phase, False if placeholder

SECTIONS: tuple[Section, ...] = (
    Section(slug="chargen", label="Characters", path="/chargen", enabled=True),
    Section(slug="relics",  label="Relics",     path="/relics",  enabled=True),
    Section(slug="names",   label="Names",      path="/names",   enabled=False),  # placeholder; flipped to True in Phase 1.5
)
```

---

### TemplateContext

A small dict-like object passed to all template renders. Built by `make_context()`.

Keys:
- `nav_sections`: `tuple[Section, ...]` — the registry, used by `_layout.html` to render nav
- `current_section`: `str` — the slug of the currently-active section (`"landing"`, `"chargen"`, `"relics"`, `"names"`); used to highlight the active nav link
- per-page extras (e.g., `relics_by_fortune`, `relic`, `prev_relic`, `next_relic`)

## Relationships

```
Relic.fortune  -> FORTUNES[Relic.fortune] : Fortune     (1:1)
Relic.clan     -> CLANS[Relic.clan]       : str display (1:1)
Section        -> route in CherryPy Root                 (1:1)
TemplateContext.nav_sections -> SECTIONS                 (1:N)
```

The Relic list is grouped by Fortune for the relics index (a `dict[str, list[Relic]]` keyed by fortune slug, in `FORTUNES` ordering).

## State transitions

None. All data is static for the lifetime of the process. A server restart reloads the pool.

## Lookup operations

- `find_relic_by_slug(slug: str) -> Relic | None`: O(1) lookup against a slug → Relic dict built at load time.
- `relics_for_fortune(fortune_slug: str) -> list[Relic]`: returns relics filtered to one Fortune, in stable order (alphabetical by slug).
- `neighbors_in_fortune(slug: str) -> tuple[Relic | None, Relic | None]`: returns (previous, next) relic in the same Fortune, wrapping at the ends.
