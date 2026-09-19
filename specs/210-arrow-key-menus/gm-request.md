# The GM's request, verbatim (2026-09-19)

Voice-dictated. Two messages, with the session's answer between them, because the second message
approves a plan and the plan is therefore part of what was asked for.

## Message 1

> Good stuff. Thanks. Now I was thinking it's so much nicer to be able to use the arrow keys to
> select between menu options than to have to type in a number. So how hard would it be for us to
> make it so that all of the times that when we are annotating something in the middle of a
> annotate() session then whenever I am choosing between multiple options then instead of having to
> type `o` or `c` or `ob` etc then I could just have something selected and then move my arrow keys
> up and down and then hit enter. Like how hard would that be?

## The session's answer (what the GM then approved), condensed

- Cheap: `keys.py` already reads raw keys and whole arrow sequences. No new dependency; a menu
  library would replace readline, which was priced and declined for the two-press undo.
- COVERS every prompt that is a choice from a fixed list: open / contested / discard / open with a
  bonus; "Which roll?"; "Which of yours?" (the opposing roll); "Which line?"; how the NPC appeared;
  the join-or-discard question when declaring a line; the mistake / record-was-wrong prompt.
- DOES NOT COVER free text (what the roll was for, a bonus, a typed total), and leaves the MIXED
  prompt alone: "What was it for?" takes a note but also accepts `c`, `ob`, `d` - those stay typed
  lines, so nothing typed today stops working.
- The letters keep working inside a menu (`o`, `c`, `d`, a number).
- The background watcher prints above the prompt and assumes a one-line prompt; a multi-line menu
  must be redrawn after a roll announcement.
- With no terminal (a pipe, the tests) the menus fall back to today's typed answers.
- Ctrl-C keeps meaning "abandon everything staged"; "Which roll?" needs an explicit finish row in
  place of the blank Enter.
- One reusable menu helper that every choice prompt calls.

## Message 2

> Yes, that sounds great. Please build that. Thanks.
