# Feature 230 plan: conversations with several NPCs

Spec: [spec.md](spec.md). Everything lives in `webapp/l7r/repl/rolls/` plus `shell.py` and
`__init__.py`.

## Decision 1 - a `Member` per NPC; the conversation keeps the shared state

`models.Member` holds what is about ONE NPC: the record, handle, `present`, numbers, schools,
what was last written to its notes (`numbers_written`, `hidden_written`, `void_written`),
Discern Honor (`discern`, `honor`), and whether its link entry is written. `Conversation` keeps
what the scene shares: rolls, lines of questioning, channels, title, boosts, cursors, the bio
lines last written, `sincerity_rolls` and `void_spends` (each entry now knows its member through
its `GmRoll.npc`), and a list of membership `Event`s (who joined or left, when).

`Conversation.npc` stays a real field (the primary's record) so the 19 test constructions and the
37 `npc_name` / `npc_id` sites keep meaning "the primary". `numbers`, `schools`, `discern`,
`honor` and the `*_written` fields become properties delegating to the primary member, with
setters - every existing one-NPC caller is unchanged (FR-012). Code that must be per-member is
changed to say which member: npcskills, oppose, hidden, voidspent, discern, the notes write and
the annotate menu.

Declined: threading a `member` argument through every function (touches every test for a
one-member conversation that has only one member to name), and a per-member `Conversation` view
object (two objects that each look like the conversation is the bug factory).

## Decision 2 - a GM roll carries its NPC (`GmRoll.npc`, the member's Obsidian Portal id)

`''` means not settled. `gmrolls.py` still imports nothing from its own package; the id is a
string.

- One-member conversation (never had a second member): a tag settles on the primary at once,
  exactly as today.
- Otherwise `- tact` with no NPC marks the roll and puts it on `npcskills._pending`.
- `souma.tag_roll(total)` (the `- souma` form) sets `npc`; if the roll is already tagged and
  pending, it runs the tag's effects for Souma right then. A roll whose `npc` is set runs its
  effects at once when tagged (`- souma - tact`). Both roads call the SAME `_settle(entry,
  member)`, which is how FR-005's equivalence holds by construction; a test asserts it anyway.
- `npcskills.settle_pending()` settles every pending roll on the primary, or raises
  `PrimaryLeft` (the roll stays tagged with no NPC). Called from:
  - `sys.displayhook` (wrapped; chains to the original so `_` still updates) - before the echo,
    and the echoed value is rebuilt from the entry so it shows the taxed total;
  - the prompt (`sys.ps1` becomes an object whose `__str__` settles first - assignment statements
    never reach the displayhook); an error there is printed, since the prompt cannot raise;
  - the entry points the GM calls next: every called tag, `annotate`, `new_line_of_questioning`,
    `add_` / `remove_from_conversation`, `end_conversation`, the exit path.
  - Never from the watcher thread: settling can prompt.
- `shell.install_prompt_hooks()` installs both hooks for the interactive prompt and the one-shot
  snippet path (`run_snippet` compiles a lone expression in `'single'` mode, so its echo goes
  through the displayhook too).

## Decision 3 - handles

`npcskills.MemberHandle(member)`: `tag_roll` (the `- souma` form), `__getattr__` returning a
bound tag for any skill name in `build_tags()` (`souma.tact`, `souma.tact()`, `xky - souma.tact`),
and a one-line repr. A bound tag is a `SkillTag` with `member` set; every SkillTag code path takes
the member from there, else the primary. The REPL namespace is registered with
`rolls.conversation.use_namespace(ns)` by `shell.main`; begin/add put handles in it and
end/abandon take them out. `conversation.handle(name)` (internal, not at the prompt - review
round 1 struck a public `npc()`) resolves a member by whole name tokens, for tests and scripts.
A departed member's handle raises `MemberLeft` for every roll except marking a roll whose
`GmRoll.at` is before the member's last `left` event.

## Decision 4 - membership and the bio

`add_to_conversation(*names)` resolves every name first (all-or-nothing), then for each: a new
`Member` (numbers loaded, Discern Honor planned when the sheet's multi-NPC shape is on), an
`Event('joined', at)`, a handle, and the link entry written at once to its bio (`bio.insert`
under the portrait). Re-adding a departed member flips `present` and records an event.
`remove_from_conversation(*names)` flips `present` and records `Event('left', at)`.

`written_lines` splits the rolls into SEGMENTS at membership events by message time (`Roll.at`),
renders each segment with `rules.render_lines`, and puts the marker line between segments, so
every grouped line (Etiquette, a line of questioning) is split at a marker (review round 1).
`add_to_conversation` on an UNTITLED conversation is an error until the GM answers the spec's
open question (review round 2). Join and leave are measured against `datetime.now(UTC)` (the
injected clock), the same clock `Roll.at` comes from (Discord message time).

## Decision 5 - per-member effects

- `npcnumbers`: `_check` / `resolve` / `_rank` / `_roll` read and write `member.numbers`;
  the disagreement prompt names the member.
- `oppose`: `Roll.against` (member id) on an oppose roll, set when collected: the primary if
  present, else `''` (no target; the watcher says so). `for_skill(conv, skill, when, npc)` counts
  only oppose rolls against that member; `for_line` uses the line's Sincerity owner.
  `move_oppose(handle, pc=None, knack=None)` re-targets (never guessing, `cancel_oppose`'s rule)
  and re-settles every tagged roll of the old and the new target.
- `hidden.entries(conv, member)` / `voidspent.entries(conv, member)` filter by `GmRoll.npc`; a
  line's entry follows its Sincerity roll's owner; a bare-number Sincerity (no roll) belongs to
  the primary.
- `_tick` writes each member's notes when that member's numbers / hidden / void lines changed.
- `annotate`: a contested line names the paired roll's member (`Roll.npc`, the member's name,
  rendered in place of the conversation's NPC when set); a typed total and an intimidation
  appearance go to the primary while it is present and ALWAYS ask which present member once it
  has left (review round 1).

## Decision 6 - Discern Honor (character-sheet#6)

The sheet shipped the multi-NPC shape (with the old one alongside) before this side's code was
written, so there is no switch: the new code sends and reads only `npcs`. `plan` runs per member
(each with its own `Honor:`), `payloads` builds `npcs: [...]` in membership order with `present`,
`poll` reads `asked_at` per (NPC, character), `commit` / `roll_back` work per member, `add` /
`leave` re-PUT when membership changes, and `discern_honor(npc, pc)` returns the planned value for
whichever member it names. Two present members whose personal names collide are sent by full name
(the sheet refuses case-insensitive duplicates).

## Verification

- Every existing rolls test passes unmodified (FR-012).
- New `tests/test_rolls_members.py`: argument classification; handles; each form of Story 3's
  table, including the `- tact - souma` / `- souma - tact` equivalence over the conversation's
  rendered notes, prompts asked and echoed total; join/leave markers in the bio order; primary
  left raises; per-member notes; oppose default and `move_oppose`; the link entry.
- `tests/test_repl_shell.py`: the displayhook and prompt hooks settle, and `_` is still set.
- `tests/test_rolls_discern.py`: the multi-NPC payload and per-member commit, flag on.
- Gate: `make done`.
