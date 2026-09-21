# GM request - feature 212

Received 2026-09-21, in the gm-assistant session "Discord repl". Reproduced verbatim, voice-dictation
artifacts included ("roles" is "rolls" and "school map" is "school knack" - see the project's
mistranscription table). This is the text the `spec-fidelity` review grades [spec.md](spec.md)
against.

---

## Message 1

The character sheet app and its Discord integration have already implemented most of our types of roles. However, we never got to implement discern honor as a school map. Now, it would be nice if the discern honor skill when rolled during a conversation automatically gave back not only a result but also telling whoever rolled it what their current take on a character's honor is. However, in order to do that, it would need to be able to read from Obsidian Portal, which I believe is something that the GM Assistant bot currently does, but that the character sheet bot does not. Does that sound right? What would be involved in making this actually work? Additionally, we would need to keep track of what their past results have been. In past conversations. We would also need to make sure that if somebody slips up and accidentally runs discern honor twice in the same conversation, then it will return the same result rather than incrementing them closer to what the actual number is, if you know what I mean. I hope I'm making myself clear on what I want the semantics to be, but I can clarify if I'm not. What would be involved in this and how much of what is happening would happen in the GM assistant bot and how much would happen in the character sheet bot? What do you think the best integration would be?

## The session's answer to message 1 (summarized - this is what message 2 says yes to)

The session reported that the knack already exists as the REPL's `discern_honor()` with its history
kept on Obsidian Portal, that Obsidian Portal access lives in gm-assistant's REPL (not in either
Discord bot), and proposed this shape:

1. On `begin_conversation("Otsuki")`, gm-assistant works out what each PC who has the knack would be
   told in this conversation.
2. It pushes only `{conversation_id, pc -> told value}` to the sheet app. The true Honor never leaves
   gm-assistant or Obsidian Portal.
3. `/discern-honor` in the sheet bot replies to the player with their told value and marks it used.
4. Because the command is a lookup, asking twice returns the same number.
5. The REPL's existing watcher already polls the sheet API. When it sees a "used" mark, it commits
   that PC's new record to Obsidian Portal. The record line gains a conversation id or date, so a
   crash and reopen cannot double-count.
6. Values nobody asked for are discarded, and no player ever saw them.

Split of work as proposed: gm-assistant holds a conversation id and idempotency in `honor.py`, the
precompute and push in `begin_conversation`, commit on use and discard on `abandon_conversation()`,
and the same idempotency for the manual REPL `discern_honor()` call. character-sheet gets one
authenticated write endpoint (the GM API is read-only today), a small table, the `/discern-honor`
command (checks the PC has the knack; replies with the told value visible only to that player; says
"no conversation is open - ask the GM" when none is), and expiry for stale conversations (e.g. 12
hours). That side goes to the character-sheet session as a requirements document, as with 211.

Two things were put to the GM: whether reopening a conversation with the same NPC the same evening
counts as a new conversation (the session's default: yes), and that `rules/05-school_knacks.md`
still reads `(1k1 - 0.5)` where the advantages text and the code use `- 5`.

The session closed with: "If this shape works for you, I'll write it up as feature 212: the spec
here, plus the handoff document for the character-sheet repository."

## Message 2

Yes, please do that, thanks, and please also include the rules text fix.

## Message 3

(In reply to the session noting that the code rolls a flat d10 with no reroll on 10, while the rules
text's "1k1" would normally explode.)

Oh yes it should be "no rerolls" so please fix that, thanks.
