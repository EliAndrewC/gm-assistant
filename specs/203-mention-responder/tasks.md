# Tasks: Mention Responder

**Feature**: 203-mention-responder | **Plan**: [plan.md](plan.md)

A task is checked only when its artifact exists and was verified. T012, T013 and T016 are the
ones that found real defects; they are written up in full because that is where the value is.

## Phase 1 - What it says, and whether to say it (no network)

- [x] **T001** `rules.py`: `Rule`, the `RULES` table, `DEFAULT_REPLY`, `strip_mentions`,
      `respond_to`. Mentions are stripped before matching, first match wins, and the default catches
      everything else so a page is never met with silence. (FR-002, FR-008)
- [x] **T002** `policy.py`: `is_bot` - the guard, first and unconditional. (FR-004)
- [x] **T003** `policy.py`: `mentioned_bots` - a DIRECT mention only. A role mention or `@everyone`
      that happens to include a bot does not count, so a `@here` does not make both bots answer.
      (FR-006)
- [x] **T004** `policy.py`: `Decider.should_answer` - the bot guard, the seen-message set
      (`SEEN = 500`, so a gateway replay cannot double-answer), and the per-channel rate limit
      (`QUIET_SECONDS = 5.0`). (FR-004, FR-005)
- [x] **T005** Tests for T001-T004. Pure and synchronous, which is the point: every rule that keeps
      this safe is provable without a socket.

## Phase 2 - The network edge

- [x] **T006** `gateway.py`: protocol constants, `INTENTS = (1 << 9) | (1 << 15)` (guild messages +
      message content), `gateway_url`, `identify`, `resume`, `heartbeat_forever`, `backoff`, and
      `Session` (tracks sequence, session id, resume URL). The module docstring summarizes the
      handshake so a reader need not go and look it up.
- [x] **T007** `gateway.send_message`: the REST reply, carrying `allowed_mentions: {parse: []}` so a
      reply can never ping anyone.
- [x] **T008** `bots.py`: `Fleet`, `load_fleet`, `NotConfigured` with messages that say how to fix
      the problem rather than just naming it.
- [x] **T009** `responder.py`: `handle` (one message, synchronous, injectable), `pump` (one
      connection, returns why it ended so the caller can resume or restart), `run_forever`
      (reconnect with backoff; `attempts` bounds the loop under test). (FR-007)
- [x] **T010** `scripts/mention_bot.py` - the entry point. Standalone: no fly.io app, no HTTP
      listener. (FR-009)
- [x] **T011** Tests for Phase 2 with a fake `Socket` yielding scripted payloads. 66 tests total,
      100% coverage, no network.

## Phase 3 - Verification, and the defects it found

- [x] **T012** **Exercise the real handshake.** Tests with a fake socket prove the logic, not that
      Discord accepts what we send - so this was run against live Discord:

      ```
      gateway URL resolved: wss://gateway.discord.gg
      HELLO, heartbeat every 41.25 s
      READY as L7R GM Assistant (1509288141985415300)
        guilds: 2
        session resumable: True
      ```

      It found two defects that 64 passing tests had not:

      - **`gateway_url` was not injectable**, so tests were reaching real Discord and quietly taking
        401s. Fixed by threading a `resolve_url` parameter through `run_forever`.
      - **`SECRETS` pointed at the repo root** (`parents[3]`, copied from `l7r/repl/rolls/`, which
        sits one directory deeper). Every test missed it because every test either injects a path or
        monkeypatches the constant. `test_the_default_paths_point_at_the_real_files` now walks the
        real ones.

- [x] **T013** **The public/secret split, forced by a guard.** The listener's application id was
      first written into `development-secrets.ini`. `tests/test_chargen_security.py` then failed:
      a value from the secrets file was appearing in served HTML.

      The guard was right and the classification was wrong. A Discord application id is public - it
      is in every invite URL and is rendered into this app's own OAuth login link as the OAuth
      `client_id`. **The fix was to move the non-secret out, not to relax the test.** Tokens stay in
      `development-secrets.ini`; the listener id moved to `development-defaults.ini`, which
      `load_fleet` reads with ConfigObj (the defaults file opens with top-level keys before its
      first section, which configparser rejects outright).

      `test_the_listener_id_is_public_and_is_not_kept_as_a_secret` asserts the SHAPE, so putting it
      back fails in `l7r/mention` too and not only in the security suite.

- [x] **T014** `l7r/mention/CLAUDE.md` - the package index, including the two design notes worth
      keeping (the listener wants the widest channel access; replies are scripted and that was an
      implementer's call).
- [x] **T015** `make done` green: ruff, ruff format, mypy --strict, hook guards, pytest, 100%
      coverage.

- [x] **T016** **A live credential leak, found by T013 and fixed under this feature**
      (constitution XIV - a defect you find while doing something else is fixed IN that work).

      Adding `[mention_bots]` to the secrets file made `test_chargen_security` fail, which raised
      the question of why a NEW section leaked at all. `chargen/templates/index.html` inlines the
      whole config dict via `{{ config|tojson }}`, and `chargen/website.py` stripped the secret
      sections using a hand-maintained frozenset of six names carrying the comment *"Add new secret
      sections here whenever development-secrets.ini grows."* The test kept its own copy of the same
      six. So the guard and the thing it guarded agreed with each other, and both had drifted from
      the file.

      **Measured, against the unfixed filter** - three sections beyond the new one were being served
      in the page:

      | section | what was in the page |
      |---|---|
      | `aws` | `access_key_id` and `secret_access_key` |
      | `character_sheet` | `roll_query_token` (the bearer token for the roll API) |
      | `github` | `push_pat` (the fine-grained PAT `sync-with-main.sh` pushes with) |
      | `mention_bots` | both Discord bot tokens (the failure that started this) |

      Both sides are now DERIVED from `development-secrets.ini` itself - the filter in
      `chargen/website.py` and the harvest list in `tests/test_chargen_security.py` - by independent
      code paths, so a new secret section is excluded the moment it exists and the guard cannot
      drift again. A static floor remains as belt-and-suspenders for an environment where the file
      is absent. **A list that must be updated from memory is not a security boundary.**

      **GM ACTION - rotate.** The fix stops future serving; it cannot un-serve what was already
      served. Anyone who loaded the chargen index while this was live could read all four from
      view-source. Rotate the AWS access key, the character-sheet roll query token, the GitHub PAT,
      and both Discord bot tokens.

## Outstanding - the GM's, not the implementation's

These are FR-011: what the GM has to do to exercise it. None of them is code.

- [ ] Invite the **Character Sheet** bot to the live L7R server (it is in Robot Role Call only).
      Until then it can be mentioned in the test server but not the real one.
- [x] **T017** `scripts/deploy_mention_bot.sh` - deployment, written after the GM asked why it had
      not happened. The original answer conflated two things: refusing to use the private key they
      pasted (correct - it is in a transcript and is burned) was treated as a reason not to deploy
      at all (wrong). The box gets a MINIMAL secrets file holding the two bot tokens and nothing
      else, runs under a systemd user service with lingering enabled, and the script is idempotent
      so a redeploy is the same command.

- [x] **T018** **Deployed.** The GM supplied a temporary admin key; it was used for exactly one
      thing - creating `gm-assistant-lightsail-deploy` and attaching it to `gm-assistant-ci` - and
      the rest of the work ran as the CI user. Live on `courtwright.org` as the systemd user service
      `l7r-mention`, ~18 MB resident. No durable SSH key was created: `scripts/lightsail_access.py`
      mints credentials that expire in minutes. Lightsail's access turned out to be
      CERTIFICATE-based, which is documented at the point of use because the private key alone fails
      with a misleading `Permission denied (publickey)`.

- [ ] ~~Grant Lightsail permissions, or run the deploy script yourself.~~ Done - but **the temporary admin access key the GM pasted
      (`AKIAR4SG6VVWRTCYQYV5`) should now be deleted** - it is in a transcript, it is no longer
      needed, and it was full IAM admin.
