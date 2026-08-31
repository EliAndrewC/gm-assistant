# `l7r.mention` - answering when a bot is mentioned

A standalone process for an always-on box. A player writes `@L7R GM Assistant what is your
purpose?` and the bot answers, in seconds, under its own name.

```
./scripts/mention_bot.py
```

**One gateway connection, any number of tokens.** Posting a message is a plain REST call authorized
by a bot token and needs no gateway of its own, so the listener hears everything it can see and
WHICHEVER BOT WAS ADDRESSED is the one that replies. That is the GM's requirement and their reason
for it: *"it is a feature of good user interface design that a computer program works the way that
its users will intuitively expect it to work."* Answering under the wrong name breaks exactly that.

| file | holds |
|---|---|
| `rules.py` | The reply table. DATA - adding a joke is an entry, not a code change. Mentions are stripped before matching, first match wins, and `DEFAULT_REPLY` catches everything else so a page is never met with silence. |
| `policy.py` | Whether to answer at all: the bot guard, who was addressed, the per-channel rate limit, and the seen-message set. Pure and synchronous, so every rule that keeps this safe is testable without a socket. |
| `bots.py` | The fleet - which application ids this process can speak as, and which one holds the socket. Split by sensitivity: tokens from the gitignored secrets, the listener's public application id from the checked-in defaults. |
| `gateway.py` | The only module that touches the network: the websocket protocol constants, `IDENTIFY`/`RESUME`, the heartbeat, and the REST call that posts a reply. Its docstring summarizes the protocol so a reader need not go and look it up. |
| `responder.py` | The loop. `handle` answers one message (synchronous, injectable); `pump` runs one connection; `run_forever` reconnects with backoff. |

## The guard that matters

**A message whose author is a bot is never answered.** The GM has watched this exact failure take a
server down (2026-08-28): *"the bot was carelessly programmed, so it just kept responding to itself
in an infinite loop that was really bad for the server and made it unusable."*

`policy.is_bot` makes the loop IMPOSSIBLE rather than unlikely - a reply cannot re-enter the trigger
path whatever it says - and with two bots in the fleet it also stops one of ours setting off the
other. Replies also carry `allowed_mentions: {parse: []}`, so a reply can never ping anyone even if
a joke contains an `@`.

## Two design notes worth keeping

**The listener should be the bot with the WIDEST channel access.** A message in a channel it cannot
see is a message this process never hears - the one place the "works how users expect" rationale can
break, and it is a permissions question at invite time rather than a code question.

**Replies are scripted rather than generated, and that was an implementer's decision taken where the
GM's request was silent** - recorded in `specs/203-mention-responder/spec.md`. It costs something
real: a question nobody anticipated gets `DEFAULT_REPLY` rather than an answer. The GM can overrule
it, and doing so touches only `rules.py`.

## Configuration

Split across two files by SENSITIVITY. Tokens are credentials, in the gitignored
`development-secrets.ini`:

```ini
[mention_bots]
1509288141985415300 = <the GM Assistant's bot token>
1490400739934212116 = <the Character Sheet's bot token>
```

Which one listens is a **public** Discord application id - it is in every invite URL and is
rendered into this app's own OAuth login link - so it goes in the checked-in
`development-defaults.ini`:

```ini
[mention_bots]
listener = 1509288141985415300
```

It started out in the secrets file, and `tests/test_chargen_security.py` caught it: a value from
the secrets file was appearing in served HTML. The guard was right and the classification was
wrong. If that test fires again, move the non-secret out - do not relax the test.

Each speaking bot needs **Send Messages** in the guild; the listener needs the **Message Content**
privileged intent. Both are Discord configuration, not code - and a bot's permissions widen IN PLACE
on its managed role, with no kick and no re-invite.

## Deployment

It runs on the GM's always-on AWS Lightsail box, NOT on fly.io - a machine that never scales to
zero costs a few dollars a month, and the GM's ruling on that was that this is *"basically a joke"*
and not worth it.

```
eval "$(./scripts/lightsail_access.py --export)"
./scripts/deploy_mention_bot.sh "$LIGHTSAIL_TARGET"
```

Live since 2026-08-31 on the Lightsail instance `courtwright.org` (Ubuntu, `nano_3_0`, us-east-1)
as the systemd user service `l7r-mention`, resident at ~18 MB of the box's 512 MB.

Idempotent: re-run it after any change. It syncs, rebuilds the venv if needed, and restarts the
systemd user service, so there is no separate update path to get wrong.

**The box gets the two bot tokens and nothing else.** The deploy script writes a minimal
`development-secrets.ini` containing only `[mention_bots]`; it does not copy the real one, which
also holds AWS keys, a GitHub PAT, the Gemini key and the Obsidian Portal credentials. A joke bot on
an internet-facing box has no business holding any of those.

Three third-party pieces total: `websockets` and `configobj` on the box, and systemd to keep it up.
Everything else the responder uses is stdlib - which is why the answer to *"should this be Rust to
be lightweight?"* was no. Measured resident footprint of the whole Python process: **21 MB**.

**No durable SSH key exists for this, deliberately.** `scripts/lightsail_access.py` mints
credentials that expire in minutes, so there is no key to store, leak or remember to rotate. The
IAM policy `gm-assistant-lightsail-deploy` is attached to `gm-assistant-ci` and grants exactly
three read-ish actions - `GetInstances`, `GetInstance`, `GetInstanceAccessDetails` - and no
lifecycle actions at all, so these credentials cannot create, delete, reboot or snapshot anything.

**The gotcha, because it costs a confusing half hour otherwise:** Lightsail's temporary access is
CERTIFICATE-based. The private key alone gets `Permission denied (publickey)`, because the box
trusts the Lightsail CA and not that key. The `certKey` from the same response must be written
beside the key as exactly `<identity>-cert.pub` for OpenSSH to present it.

Host keys come back from that same call and are written to a `known_hosts` file, so the deploy
verifies the host instead of reaching for `StrictHostKeyChecking=no`.

## Testing

```
( cd webapp && pytest -n auto tests/test_mention.py )
```

Everything is tested without a socket or a network call: `Socket` in the test file is a fake that
yields scripted gateway payloads, and every boundary - connecting, resolving the gateway URL,
sending - is an injectable parameter. `run_forever` takes `attempts` so the forever loop terminates
under test.
