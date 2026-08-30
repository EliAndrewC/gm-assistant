# Implementation Plan: Mention Responder

**Feature**: 203-mention-responder | **Spec**: [spec.md](spec.md) | **Status**: implemented

## Summary

One long-lived process holds a single Discord gateway connection, watches for messages that mention
a bot it has a token for, and replies **as that bot**. It runs on the GM's always-on AWS Lightsail
box rather than fly.io, because a fly.io machine that never scales to zero costs real money every
month for what the GM calls "basically a joke".

## Technical Context

- **Language**: Python 3.14 (the same interpreter the rest of this repo uses)
- **Dependency added**: `websockets` (asyncio client). Measured resident footprint of the whole
  process: **21 MB**. That number settled the "should this be Rust?" question the GM raised - the
  saving over Python was not worth a second toolchain on the Lightsail box, and the GM agreed.
- **No new service**: no HTTP listener, no fly.io app, no interactions endpoint.
- **Testing**: `webapp/tests/test_mention.py`, no socket and no network.

## Constitution Check

| Principle | How this satisfies it |
|---|---|
| I (independent review) | `spec-fidelity` reviewed the spec against the GM's verbatim request before implementation; the review history is at the bottom of `spec.md`. |
| III (pool/data convention) | What the bot SAYS is a data table (`rules.RULES`), not code. Adding a joke is a row. |
| VI (verification) | The live gateway handshake was exercised end to end against real Discord before the feature was called done - see Task 12. |
| X (quality gate) | `make done`: ruff, ruff format, mypy --strict, pytest, 100% coverage. Every module is under 200 lines. |
| XIII (no known regressions) | Baseline taken in a detached worktree; the only failure the gate found was one this feature introduced, and it was fixed rather than waived (see Task 13). |

## Key Design Decisions

### One connection, many tokens

Posting a message is a plain REST call authorized by a bot token. It needs no gateway of its own.
So one bot holds the socket and hears everything it can see, and whichever bot was addressed is the
one that replies. This is what makes FR-003 cheap, and FR-003 is the GM's own requirement:

> it is a feature of good user interface design that a computer program works the way that its users
> will intuitively expect it to work.

**Consequence to know about**: the listener should be the bot with the WIDEST channel access, since
a message in a channel it cannot see is a message this process never hears. That is a permissions
question at invite time, not a code question.

### The bot guard is structural, not a heuristic

`policy.is_bot` refuses any message whose author is a bot, before anything else runs. The GM has
watched this exact failure take a server down:

> the bot was carelessly programmed, so it just kept responding to itself in an infinite loop that
> was really bad for the server and made it unusable.

A reply therefore cannot re-enter the trigger path whatever it says, and with two of our bots in
one server neither can set off the other. Replies also carry `allowed_mentions: {parse: []}`, so a
reply can never ping anyone even if a joke contains an `@`.

### Replies are scripted, not generated

**This was an implementer's decision taken where the GM's request was silent**, and it is recorded
because it costs something real: a question nobody anticipated gets `DEFAULT_REPLY` rather than an
answer. The alternative - calling a model per mention - buys better answers for a per-message cost
and a latency the 3-second ack window does not forgive, on a feature the GM described as a joke. The
GM can overrule this, and doing so touches only `rules.py`.

### Config is split by sensitivity

Bot tokens are credentials and live in the gitignored `development-secrets.ini`. Which bot listens
is a **public** Discord application id - it appears in every invite URL and is rendered into this
app's own OAuth login link - and lives in the checked-in `development-defaults.ini`.

This split was not planned; it was forced by a test, and the test was right. See Task 13.

## Project Structure

```
webapp/l7r/mention/
  rules.py       what to say. DATA.
  policy.py      whether to answer at all. Pure and synchronous.
  bots.py        which application ids we can speak as, and which one listens.
  gateway.py     the only module that touches the network.
  responder.py   the loop: handle one message, pump one connection, run forever.
  CLAUDE.md      the index.
scripts/mention_bot.py   the entry point.
webapp/tests/test_mention.py
```

Every boundary - connecting, resolving the gateway URL, sending, sleeping, the clock - is an
injectable parameter, which is why the whole feature is testable without a socket.
