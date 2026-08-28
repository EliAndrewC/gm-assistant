# Contract: the REPL surface

What the GM types. Follows `l7r/repl` conventions - printing is the interface, and every function
still RETURNS a real value so it composes in a snippet.

```python
begin_conversation(npc, channel=None)   -> Conversation
```
Opens a conversation. `npc` resolves through `chargen.opsynth.match_character`, exactly as
`discern_honor` does: whole name tokens only, and an ambiguous match raises listing the candidates
(FR-001). `channel` defaults to the channel of the group whose campaign the NPC belongs to; the GM
names it when that cannot be determined. Prints what it opened. Starts the poller.

```python
end_conversation()                      -> str
```
Closes, formats, and WRITES - immediately, with no confirmation step (FR-019). Prints and returns
the line it wrote. Reports anything unresolved. With zero rolls collected it writes nothing and says
so.

```python
abandon_conversation()                  -> None
```
Closes without writing. For the "opened against the wrong NPC" case only. Nothing blocks on it.
**Recorded in the spec's Assumptions as an addition beyond the GM's request**, to raise with the GM
once the implementation works.

```python
conversation_status()                   -> Conversation | None
```
What is open and what has been collected so far. Prints a preview of the line as it currently
stands. This is a read, NOT a gate: `end_conversation()` never waits on it.

## The written line

Open rolls (FR-021), the GM's own example:

```
Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15
```

Contested (FR-012). Both totals unrounded, the margin rounded down to 5:

```
Jimen vs Otsuki sincerity: 41 vs 28, Jimen by 10
```

The contested wording is the spec's choice, not the GM's - flagged in Assumptions as trivially
adjustable.
