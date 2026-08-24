"""Generate ``pool/index.html`` - a browsable index of every map in the diagram pool.

WHY (GM 2026-08-15): the scripted-generation experiment folder is gone and the pool is foldered by
TIER, not by method - the four hamletgen demo maps live in ``pool/hamlets/`` beside the
hand-authored hamlets, with ``meta.generated_by`` in the manifest as the only marker of HOW a map
was made. The GM asked for one page over the whole pool: every map's tier, its subtype (field
archetype, walled or open, dispersed or nucleated), the tunable knobs its manifest records, the
method that drew it, and a thumbnail of the render.

Columns are DERIVED, not curated: a dedicated column consumes the handful of meta keys it names,
and every other key the manifest records lands verbatim in the Knobs column - so a new knob added
to any generator shows up in the index with no change here. A pool folder not in the known tier
list still gets a section (appended after the known ones), so a new tier can never be silently
missing. A column that is empty for a whole section is dropped from that section's table (the Mode
A rows have no manifest knobs; five rows of empty cells earn nothing).

Mode A compound plans are classified POSITIVELY, by their folder (``MODE_A_DIRS``) - never by the
absence of a JSON manifest. The first draft classified by absence and the frontend-review pass
caught the failure that invites: an index built while a regen was mid-flight showed a hamlet as a
"Mode A compound" at the wrong scale with all its knobs hidden - confidently wrong, not missing. A
settlement-tier map without a manifest now says "manifest missing" in red instead of guessing.

The page is derived and gitignored, exactly like the renders it embeds: render-sync
(``render_cache.main``) rewrites it in main after every push (after the regen completes, so the
manifests it reads are final), and it stays current in the one tree that holds every render.
Thumbnails are relative ``<img>`` links to the pool pngs, so the page works from a plain
``file://`` open of main's tree; a map whose render is not present says so instead of showing a
broken image.

Standalone run (from the skill dir): ``python3 -m l7r.diagram.pipeline.pool_index [--pool <dir>]``.
"""

from __future__ import annotations

import argparse
import html
import json
import os

SKILL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)  # the skill root; this module lives in l7r/diagram/pipeline/ - FOUR levels up since feature 119, not two

# Known tiers, in the order the GM reads the pool (smallest settlement first, Mode A last). A
# folder not listed here still gets a section, appended alphabetically after these.
TIER_SECTIONS: tuple[tuple[str, str], ...] = (
    ("hamlets", "Hamlets"),
    ("villages", "Villages"),
    ("towns", "Towns"),
    ("provincial-cities", "Provincial cities"),
    ("capitals", "Capital cities"),
    ("magistracies", "Magistracies (Mode A compound plans)"),
)

# Folders holding Mode A compound plans: tracked svg source, no JSON manifest, 3 px = 1 ft.
MODE_A_DIRS = frozenset({"magistracies"})

# Not maps: negative fixtures and interpreter droppings.
SKIP_DIRS = frozenset({"regressions", "__pycache__"})

COLUMNS: tuple[str, ...] = ("Map", "Name", "Method", "Subtype", "Scale", "Size", "Knobs", "Notes")

# Columns kept even when empty for a whole section - dropping the identity columns would make
# sections' tables start at different places, which reads as a layout bug rather than pruning.
ALWAYS_KEPT = frozenset({"Map", "Name", "Method"})

# Meta keys consumed by a dedicated column (or pure canvas framing: W/H/view/toscale). Everything
# else is a tunable knob and is shown verbatim in the Knobs column.
_CONSUMED = frozenset(
    {
        "W",
        "H",
        "view",
        "toscale",
        "name",
        "scale",
        "ftpx",
        "generated_by",
        "field_archetype",
        "land_use_overlay",
        "walled",
        "nucleated",
        "settlement_form",
        "households",
        "population",
    }
)

_CSS = """
body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 90rem; padding: 0 1rem;
       background: #faf8f4; color: #2a2620; }
h1 { margin-bottom: 0.2rem; }
p.lede { color: #6b6355; margin-top: 0; }
nav { margin: 0.6rem 0 0; color: #6b6355; }
nav a { margin-right: 0.9rem; }
h2 { border-bottom: 2px solid #d8cfc0; padding-bottom: 0.2rem; margin-top: 2.2rem; }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #d8cfc0; padding: 0.45rem 0.6rem; text-align: left;
         vertical-align: top; }
th { background: #efe9de; }
tr:nth-child(even) td { background: #f4f0e8; }
td.thumb { width: 170px; text-align: center; }
td.thumb img { max-width: 160px; max-height: 120px; border: 1px solid #c9bfae; background: #fff; }
td.thumb span { color: #99917f; font-size: 0.85rem; }
td.knobs { font-size: 0.85rem; color: #4a443a; }
td.method { white-space: nowrap; }
.none { color: #b3ab99; }
.warn { color: #a03123; font-weight: 600; }
"""


def _fmt_val(v: object) -> str:
    """One knob value, compactly: a waivers dict shows its check names (the reasons live in the
    manifest), a list joins its items, everything else prints as-is."""
    if isinstance(v, dict):
        return ", ".join(sorted(str(k) for k in v))
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v)


def _load_meta(dirpath: str, stem: str) -> dict[str, object]:
    """A map's manifest meta, or {} when the JSON is absent (see _row for how that is reported)."""
    path = os.path.join(dirpath, stem + ".json")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        meta = json.load(fh).get("meta", {})
    return dict(meta)


def _mode_a_program(dirpath: str, stem: str) -> str:
    """The '**Program type**: ...' line from a Mode A map's notes, or '' if the notes lack one."""
    path = os.path.join(dirpath, stem + ".notes.md")
    if not os.path.exists(path):
        return ""
    with open(path) as fh:
        for line in fh:
            if line.startswith("**Program type**:"):
                return line.split(":", 1)[1].split(" - ")[0].strip()
    return ""


def _subtype(meta: dict[str, object]) -> str:
    """The map's subtype, composed from the meta keys that name a KIND of map rather than a
    quantity: field archetype, land-use overlay, walled/unwalled, dispersed/nucleated."""
    parts: list[str] = []
    if meta.get("field_archetype"):
        parts.append(str(meta["field_archetype"]))
    if meta.get("land_use_overlay"):
        parts.append(f"overlay: {meta['land_use_overlay']}")
    if "walled" in meta:
        parts.append("walled" if meta["walled"] else "unwalled")
    if meta.get("settlement_form") == "dispersed" or meta.get("nucleated") is False:
        parts.append("dispersed")
    return ", ".join(parts)


def _knobs(meta: dict[str, object]) -> str:
    knobs = {k: v for k, v in meta.items() if k not in _CONSUMED}
    # hamletgen records water_source_position beside an identical water_source; one is enough here.
    if knobs.get("water_source_position") == knobs.get("water_source"):
        knobs.pop("water_source_position", None)
    return "; ".join(f"{k}={_fmt_val(v)}" for k, v in sorted(knobs.items()))


def _row(dirname: str, dirpath: str, stem: str) -> dict[str, str]:
    """One map's cells, keyed by column name; '' marks an empty cell (rendered as a dash, and a
    column empty across a whole section is dropped). Values are final HTML."""
    meta = _load_meta(dirpath, stem)
    name = str(meta.get("name") or stem.replace("-", " ").title())
    if dirname in MODE_A_DIRS:
        method = "Mode A compound"
        subtype = html.escape(_mode_a_program(dirpath, stem))
        scale = html.escape("1/3 ft/px (3 px = 1 ft)")
        size = knobs = ""
    elif not meta:
        # A settlement-tier map ALWAYS has a manifest; say the index is wrong rather than guess.
        method = '<span class="warn">manifest missing - regenerate the map, then this index</span>'
        subtype = scale = size = knobs = ""
    else:
        method = html.escape(f"scripted ({meta['generated_by']})" if meta.get("generated_by") else "hand-authored")
        subtype = html.escape(_subtype(meta))
        ftpx = meta.get("ftpx", "?")
        if isinstance(ftpx, float) and ftpx.is_integer():
            ftpx = int(ftpx)  # 1.0 and 1 are the same scale; the index should not imply otherwise
        scale = html.escape(f"{meta.get('scale', '?')} ({ftpx} ft/px)")
        size = ""
        if meta.get("households"):
            size = html.escape(f"{meta['households']} households")
        elif meta.get("population"):
            size = html.escape(f"pop {meta['population']}")
        knobs = html.escape(_knobs(meta))
    png = f"{dirname}/{stem}.png"
    if os.path.exists(os.path.join(dirpath, stem + ".png")):
        thumb = f'<a href="{html.escape(png)}" target="_blank" rel="noopener"><img src="{html.escape(png)}" alt="{html.escape(name)}" loading="lazy"></a>'
    else:
        thumb = "<span>render not synced</span>"
    notes = f"{dirname}/{stem}.notes.md"
    notes_cell = f'<a href="{html.escape(notes)}">notes</a>' if os.path.exists(os.path.join(dirpath, stem + ".notes.md")) else ""
    return {
        "Map": thumb,
        "Name": html.escape(name),
        "Method": method,
        "Subtype": subtype,
        "Scale": scale,
        "Size": size,
        "Knobs": knobs,
        "Notes": notes_cell,
    }


_CELL_CLASS = {"Map": "thumb", "Method": "method", "Knobs": "knobs"}


def _table(rows: list[dict[str, str]]) -> str:
    cols = [c for c in COLUMNS if c in ALWAYS_KEPT or any(r[c] for r in rows)]
    out = ["<tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"]
    for r in rows:
        cells = []
        for c in cols:
            cls = f' class="{_CELL_CLASS[c]}"' if c in _CELL_CLASS else ""
            cells.append(f"<td{cls}>{r[c] or '<span class=none>-</span>'}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="tablewrap"><table>' + "".join(out) + "</table></div>"


def _sections(pool_dir: str) -> list[tuple[str, str]]:
    """(folder, heading) pairs: the known tiers in reading order, then any unknown map folder
    appended alphabetically so a new tier is never silently missing from the index."""
    known = [d for d, _ in TIER_SECTIONS]
    present = sorted(d for d in os.listdir(pool_dir) if os.path.isdir(os.path.join(pool_dir, d)) and d not in SKIP_DIRS)
    sections = [(d, title) for d, title in TIER_SECTIONS if d in present]
    sections += [(d, d.replace("-", " ").title()) for d in present if d not in known]
    return sections


def build_index(pool_dir: str) -> str:
    """The whole page, deterministically from the pool's files (so a rebuild with no pool change
    is byte-identical - no timestamps)."""
    body: list[str] = []
    nav: list[str] = []
    for dirname, heading in _sections(pool_dir):
        dirpath = os.path.join(pool_dir, dirname)
        stems = sorted(f[: -len(".gen.py")] for f in os.listdir(dirpath) if f.endswith(".gen.py"))
        if not stems:
            continue
        nav.append(f'<a href="#{html.escape(dirname)}">{html.escape(heading)}</a>')
        body.append(f'<h2 id="{html.escape(dirname)}">{html.escape(heading)}</h2>')
        body.append(_table([_row(dirname, dirpath, s) for s in stems]))
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>L7R Diagram Pool</title>",
        f"<style>{_CSS}</style>",
        "</head><body>",
        "<h1>L7R Diagram Pool</h1>",
        '<p class="lede">Every map in the pool, by tier. Scripted maps carry <code>meta.generated_by</code>; everything else is hand-authored. Click a thumbnail for the full render.</p>',
        "<nav>" + "".join(nav) + "</nav>",
        *body,
        "</body></html>",
    ]
    return "\n".join(out) + "\n"


def write_index(pool_dir: str) -> str:
    path = os.path.join(pool_dir, "index.html")
    with open(path, "w") as fh:
        fh.write(build_index(pool_dir))
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rebuild the pool's index.html.")
    ap.add_argument("--pool", default=os.path.join(SKILL_DIR, "pool"), help="pool directory to index")
    args = ap.parse_args(argv)
    print(f"pool-index: wrote {write_index(args.pool)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    from l7r.diagram._invocation import guard

    # REFUSE unless invoked through this project's make (feature 127). At the TOP of the
    # entry point, never in a loop - the determination reads /proc and is cached per process.
    guard("l7r.diagram.pipeline.pool_index")
    raise SystemExit(main())
