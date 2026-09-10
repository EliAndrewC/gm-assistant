# Data model: Interrogation rolls grouped by line of questioning

Everything is in `webapp/l7r/repl/rolls/models.py` and the pure functions of `rules.py`. No
storage changes: the rolls live on the open `Conversation` and are written as text.

## `Roll` (existing, frozen dataclass) - two new fields

| field | type | default | meaning |
|---|---|---|---|
| `line` | `int \| None` | `None` | The line-of-questioning id this interrogation roll belongs to. `None` for every non-interrogation roll and for an interrogation roll not yet annotated. Ids are small integers unique within one conversation, allocated as `max(existing) + 1` by the menu. |
| `grilling` | `bool` | `False` | Whether the interrogator was grilling on this roll's line. Set on every roll of the line (see "Line of questioning" below); meaningless when `line is None`. |

Existing fields this feature reads: `total` (written exactly), `rank` (written as `@N`; the menu
may set it via `replace()` when the character-sheet app supplied none), `note` (the line's
topic), `character`, `discarded`, `attributed`, `skill`.

Existing fields this feature must IGNORE for interrogation: `opposed_total`, `bonus_self`,
`bonus_opposed` - an interrogation roll never has an opposing side and never applies a bonus
(FR-002, FR-003). A pre-feature roll carrying `opposed_total` is rendered as if it did not
(research R5).

### Validation

- `line is not None` implies the roll is an interrogation roll and `note` is non-empty
  (the menu only allocates a line while taking or inheriting a note). Not enforced by the
  dataclass - `Roll` carries no invariants today and the menu is the only writer.

## Line of questioning (DERIVED - no class)

The set of attributed, non-discarded interrogation rolls of one conversation sharing a `line`
id. Its properties are read from its rolls:

| property | from |
|---|---|
| note | `note` of the first roll in collection order |
| grilling | `grilling` of the first roll in collection order |
| rolls | every roll with that `line`, ordered highest `total` first, ties in collection order (FR-005) |
| position in the record | the collection index of its first roll (FR-010) |

A line with no rolls cannot exist, which is why FR-011's "is not written" needs no code.

`rules.lines_of_questioning(rolls) -> list[list[Roll]]` is the one function that derives them,
so the renderer and the menu agree on what a line is. The menu overlays its staged decisions on
the conversation's rolls before calling it.

## `Decision` (menu staging, `annotate.py`) - three new fields

| field | type | default | meaning |
|---|---|---|---|
| `line` | `int \| None` | `None` | Line id to put the roll on. Non-`None` marks an interrogation decision. |
| `grilling` | `bool` | `False` | The line's grilling flag (inherited when joining). |
| `rank` | `int \| None` | `None` | Rank to record on the roll. Applied only for an interrogation decision; the roll's own recorded rank is copied here when it has one, so `_apply` can set it unconditionally. |

`_apply` for an interrogation decision: `replace(roll, note=..., line=..., grilling=..., rank=...)`
and NOTHING else - no `opposed_total`, no bonuses.

## Rendering (`rules.py`)

```
render_interrogation(rolls_on_one_line) -> str
    'interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts to do'
    'interrogation: 25@2 Jimen - what Fumitake thinks of Tsuruchi'
    'interrogation: 37 Jimen - ...'                # no rank known
    'interrogation: 37@2 Jimen'                     # bare (exit path, FR-012): one roll, no note
```

(As built there is no `bare` flag: the note is written iff the first roll is annotated, which is
already what "bare" meant, so the parameter would have duplicated a fact the roll carries.)

`render_lines` change: in its second pass (annotated rolls in collection order), an interrogation
roll that is the first of its line emits the whole line; later rolls of that line emit nothing.
With `include_unannotated=True`, an interrogation roll with `line is None` emits a bare line of
its own. Everything else in `render_lines` is untouched (FR-013).

`INTERROGATION = 'interrogation'` and `is_interrogation(roll)` live beside
`EXEMPT_FROM_ANNOTATION` and `CONTESTED_PAIRS`, the module's other skill-keyed rules.
