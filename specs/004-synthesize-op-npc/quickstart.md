# Quickstart: /synthesize

## Use

In a Claude Code session for this project:

```
/synthesize Daidoji Jitsuyo
```

The skill resolves the name to the OP character (here
"Daidoji no Etsuko Jitsuyo"), reads their data including the one-line summary
("drinking companion of Kyoma"), generates a backstory grounded in the same
setting corpus and campaign cast the web generator uses, and shows it to you with
two options plus a free-text box:

1. **Upload as-is to Obsidian Portal** - saves the backstory into the character's
   GM-only notes under a `--- Synthesized Backstory (auto) ---` section, leaving
   your other notes untouched.
2. **Generate another synthesis** - re-rolls from the same context and re-asks.
3. **Type your changes** in the free-text box - whatever you type is applied to
   the backstory, then it is saved (this is the "upload with changes" path).

Re-running later replaces only the synthesized section, never your other notes.

## Prerequisites

- OP credentials (`[obsidian_portal]` in `development-secrets.ini`) and the
  Gemini key configured, plus the setting corpus available (dev mount or bundle) -
  the same prerequisites as the note-intake workflow and the web generator.

## Verify (developer)

From `/gm-assistant/webapp`:

```
make done            # ruff + format + mypy --strict + pytest + 100% coverage
```

`opsynth.py` is pure logic at 100% coverage; `op.py`'s new page-fetch boundary is
covered by the saved `fixtures/op_character_page.html`. A manual read-only
end-to-end check (resolve + tagline + synthesize, no save) confirms parity with
the webapp before any real upload.
