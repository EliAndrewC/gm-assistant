# Feature 230 tasks

- [x] T1 models: `Member`, `Event`; `Conversation.members` / `events`; primary-delegating properties; `GmRoll.npc`; `Roll.against`, `Roll.npc`.
- [x] T2 conversation: argument classification; members at open (numbers per member, link entries); handles + `use_namespace`; `add_to_conversation` / `remove_from_conversation`; segmented `written_lines` with markers; per-member notes in `_tick`; close/abandon remove handles.
- [x] T3 npcskills: member-aware `SkillTag` (bound tags via `MemberHandle`), `_pending` + `settle_pending`, `PrimaryLeft` / `MemberLeft`, every effect against the settled member.
- [x] T4 oppose: target per oppose roll (primary default), per-member penalties, `move_oppose`.
- [x] T5 hidden / voidspent: entries per member.
- [x] T6 annotate: contested line names the paired member; typed total / appearance rule.
- [x] T7 shell: displayhook + prompt hooks; one-shot path; `use_namespace(ns)`.
- [x] T8 discern: the multi-NPC shape (plan / payloads / poll / commit / roll_back per member); `honor.discern_honor` per member.
- [x] T9 docs: `rolls/CLAUDE.md` section, `COMMANDS` rows, module docstrings.
- [x] T10 gate green; push; tell character-sheet#6 the REPL switched. (No `MULTI_NPC` flag: the sheet shipped the shape before this side was written.)
