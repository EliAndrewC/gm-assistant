# GM request - feature 213

The GM's requirement for this feature was written in the character-sheet repository, not in a
gm-assistant session: `combat-design/design.md` in <https://github.com/EliAndrewC/character-sheet>,
the GM-approved design for the combat tracker (NPC generation, encounters, rounds). The decisions
below were the GM's answers to that document's question rounds; section 4.6 is the design they
approved for names. They are reproduced VERBATIM from that file as of 2026-09-28 (character-sheet
at `17555dc`). This is the text the `spec-fidelity` review grades [spec.md](spec.md) against.

The character-sheet session ("Combat") delegated the gm-assistant half to this session, and its
client for the endpoint is already written (`app/services/npc_names.py` there, uncommitted when
this feature began). That session's work order is summarized at the end; it is NOT the GM's
words and carries no authority the decisions below do not.

---

## Decisions (`combat-design/design.md`, section 2)

Round 1:

| # | decision |
|---|---|
| D10 | **Names are suggested the way gm-assistant does it:** its pool, excluding names already used in the campaign and names too similar to them. |

Round 2:

| # | decision |
|---|---|
| D16 | **NPC names are always male.** |

Round 3:

| # | decision |
|---|---|
| D26 | **Names:** Wave Men always from the **peasant** pool. Samurai-school NPCs get a **samurai-eligible personal name only**; the GM types a full name if one is ever needed. |

## Section 4.6 of the approved design, verbatim

### 4.6 Names (D10, D16)

- **The used-name data is only reachable from gm-assistant**, so picking stays there. It gets a token-authed `GET /api/names?count=&peasant=`, male pool only. `peasant=true` for Wave Men; `peasant=false` (samurai-eligible) for school NPCs, given name only (D26). The endpoint refreshes the used-name cache when stale and applies both the used-name and within-batch rules.
- **In this app:** the builder pre-fills names, and the GM can edit one or ask for another. If gm-assistant is asleep or down, names fall back to "Wave Man 1..N".
- **NPC names reach gm-assistant's used-name set through `/api/characters`**, flagged `is_npc`. The public-index scrape cannot see them.

---

## The delegating session's work order (summary, not the GM's words)

Build the endpoint in the CherryPy app like `l7r/repl/names.py` builds a batch (repeated
`namepool.pick_name('m', pool, used, [*avoid, *picks], peasant=peasant)` with
`used = opcache.used_given_names()`, returning fewer on `NamePoolExhausted`); `count` clamped to
1..30, `peasant` defaulting false, an `avoid` comma list; bearer-token auth against a new
`[character_sheet] names_token`, compared in constant time, 503 when unset, 401 on a wrong or
missing bearer, header only; JSON errors. Decide and record how fresh the used-name cache is, given
that the sheet calls with a ~12 second timeout and falls back to "Wave Man 1..N" on any failure.
Do not deploy and do not add a real secret; the GM sets it.
