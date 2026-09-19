# Research and decisions: feature 207

Each entry: what was found or decided, why, and what was declined. Dated 2026-09-19 unless noted.

## R1 - Baseline

`make done` on unmodified HEAD (`0e6d1c3e` plus the spec commits) in the clone: **green, 1508
passed, 100% coverage**. Every failure after this point is this feature's.

## R2 - Pontificate and athletics were never captured

Measured before any change: `25 etiquette` parsed; `31 pontificate`, `25 athletics` and the sheet
bot's `**Roll Tester**: **23** Pontificate@2` all parsed to nothing. The parser's rule is "a number
is a roll only beside a vocabulary word", and the vocabulary was read from `02-skills.md` alone -
both are school knacks (`05-school_knacks.md`).

**Decision**: the vocabulary gains the knacks whose rules entry declares a ring other than `N/A`
(a derivable reading of "rollable") and whose name is ONE word (the parser cannot read two).
That is athletics, commune, counterattack, feint, iaijutsu, lunge, pontificate, presence,
spellcasting.

**Corpus check** (`EXPECTED_ROLLS` is a regression fixture): swept all 615 messages with and
without the knacks. Exactly two parses changed - `43 athletics` and `38 Athletics`, both real rolls
that had been silently dropped. No new problem lines, no new ambiguity. 123 -> 125.

**Declined**: listing pontificate and athletics by hand (a list that must be remembered is the
thing `skills.py` exists to avoid); admitting multi-word knacks by matching their last word
(`double attack 31` would be filed under `attack`).

## R3 - The keystroke is reachable; the first answer about it was wrong

The session first told the GM a double backspace was not practical because Python's readline
binding cannot call back into Python on a key. True, and beside the point: the key can be read
BEFORE readline is given the line. `keys.ask_with_undo` prints the prompt, reads one key in cbreak
mode, and either undoes the selection or hands the key to readline through a startup hook that
inserts it - so the note keeps line editing and `ask_quietly` still keeps it out of the history.

- **Accepted limit**: recognized only while the line is empty - the GM's own condition (*"while
  there is no text on the current line"*). Priced and declined: prompt_toolkit for these prompts.
- **Two presses**, the GM's word in messages 1 and 5. The draft had one.
- **`TCSANOW`, not `tty.setcbreak`'s default `TCSAFLUSH`**: the flush discards type-ahead.
- **A FAILED approach, recorded so it is not retried**: the first pty test queued `\x7f\x7f` on the
  master and then entered cbreak. It hung the suite. In canonical mode the line discipline consumes
  a queued Backspace as an ERASE, so nothing is ever readable; measured directly with
  `select` before and after the mode switch (empty both times), against a pty already in cbreak
  (readable at once). The test terminal is therefore put in cbreak before the bytes are written.
  Not a product defect - a GM presses the key after the prompt is up - but it means type-ahead of
  the undo itself cannot work, which is inherent to the terminal, not to this code.
- `os.read(fd, 1)`, never `sys.stdin.read(1)`: the text layer reads ahead, and a pasted note's
  remainder would sit in Python's buffer where readline never sees it.

## R4 - Lines of questioning: declared, and still derived

Feature 206 derived a line purely from the rolls sharing an id so that staging and Ctrl-C needed
one code path (its R2). That still holds for RENDERING. A small `Conversation.lines` list was added
beside it because a declared line may have no rolls yet and owns the hidden Sincerity roll, which
no `Roll` may carry. `grilling()` therefore rewrites the flag on every roll of the line.

**Attach by MESSAGE time** (`conversation.attach`), not poll time: the watcher polls every 20 s,
so a roll posted just before a declaration is normally collected just after it.
`new_line_of_questioning` collects once, synchronously, before asking - which put two threads in
`collect` for the first time, hence `_collect_lock`.

**The narrowing of "each previous interrogation roll"** to (a) rolls on no line and (b) a PC's
repeat roll on the line being left was put to the fidelity reviewer by name and judged
LEGITIMATE: the GM's two answers (join, discard) are both wrong for a PC's first roll on a line
the GM declared.

## R5 - What the fidelity review struck

Round 1 required one change: a draft edge case recorded and checked rolls tagged with NO
conversation open once the next conversation began. The GM scoped the check to *"if we are in a
conversation with an NPC"*, and the deferred write could put one NPC's numbers on another's
permanent record. A tag outside a conversation now only marks the roll. Round 2: FAITHFUL.

The seam round 2 noted: such a roll has no recorded rank, so when it is pre-paired its rank is
read off its dice (`annotate._their_rank`) exactly as an untagged roll's is.

## R6 - Rules facts used, and where they were read

| fact | source | how it is held |
|---|---|---|
| a skill's ring; which skills are advanced | `02-skills.md`, each `### Skill` entry | parsed (`skills.skill_rings`, `advanced_skills`) |
| schools with an extra die, and on what | `04-schools.md`, `11-non_pc_schools.md`, "Roll one extra die on ..." | parsed (`npcnumbers.school_extra_dice`); Merchant and Shosuro Actor are the two for sincerity, as the GM said |
| rank 0: no rerolled tens; advanced at 0 takes -10 | `02-skills.md:73` | applied by the called form only |
| void point: one rolled AND one kept die | `01-character_creation.md`, Void Points | `vp` |
| casual conversation: 2 free raises to the NPC | `02-skills.md`, Interrogation | `hidden.CASUAL_RAISES`, applied by the grilling flag alone |
| acting -> sincerity, intimidation; history -> culture, law, strategy | `02-skills.md`, Acting and History | a written table (`npcnumbers.AUTOMATIC_RAISES`), because WHICH are automatic is the GM's ruling |

The GM first called history's raise on culture conditional; the rules say heraldry is the
conditional one. Asked, and the GM corrected it (message 7).

## R7 - School detection is whole-tag or whole-line

*"we should be able to look for those strings mechanically."* A school name matches a whole OP tag
or a whole line of the description or GM-only notes, case-insensitively, with or without a trailing
"school". Substring matching was declined: "he was once a merchant" is backstory, not a school.
When a school die changes an inference the tool names the school, so a false match is visible.
Checked against two live records (read-only): the school is not on every NPC, and an NPC without
one simply gets no adjustment.

## R8 - Persistence

Both GM-only blocks ride `_tick`: same debounce, first write immediate. The bio is written first
and the notes on a separate call inside a `try`, so a failed GM-only write never costs the public
record (Story 10.3). `wrote_before` now also looks at `written_at`, because a conversation can
write notes before it has any bio line, and without that every tagged roll would write at once.

## R9 - Found by running a whole session, not by a unit test

A scripted end-to-end session (every new function, through the real namespace, against a fake
Obsidian Portal) exposed a defect no unit test had: the GM's tagged investigation roll PRE-PAIRED a
sneaking roll, and the `n` typed to say "nobody opposed it" was taken as the roll's NOTE - writing
a contest that never happened. Pre-pairing had moved the question the letter belonged to out from
under it. Fix: the picker's own letters (`n`, `f`, `t`) are honored at a pre-paired prompt, each
only where the picker would offer it, and pinned by
`TestThePickersLettersWorkAtAPairedPrompt`. A tagged investigation roll is inherently ambiguous
between a sneaking and an acting roll (both are opposed by investigation); nearest-in-time pairs
it, and the undo or a letter reaches everything else.

The same run confirmed the two halves of the record: the bio carried no sincerity or investigation
number, and the GM-only notes carried both blocks. It is reproduced in quickstart.md's hand-check.
