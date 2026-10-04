# Feature 215: issue watch - two Claude Code sessions talking through a GitHub issue

**Request**: [gm-request.md](gm-request.md) (three messages, 2026-10-03). **Status**: specified.

## Why

The GM wants sessions in different containers (and, by extension, on different hosts) to coordinate
through a tracker item the way coworkers do, without paying model tokens to poll and without being
interrupted mid-work - and to learn the pattern for GitLab at work. gm-assistant and
character-sheet are the two participants; feature 214's sheet-side handoff is the first real use.

## The shape

One stdlib-only Python script, `issue_watch.py`, developed and tested in this repository and
installed into the shared `~/.claude/hooks/`. A session STARTS a watch on an issue; from then on:

- when the GM sends a message, unseen activity on the issue is added to the turn's context;
- when the session ends a turn with unseen activity, it is blocked once and shown it;
- while the session sits idle, a background `Stop` hook checks the issue every minute and WAKES the
  session when something new arrives.

Polling happens only inside those hooks, so there is no daemon to start, orphan or clean up.
Conditional requests (ETag) make an unchanged check free of rate limit.

## Requirements

- **FR-001 Opt-in per repository.** A repository participates by containing
  `.claude/issue-watch.json`, which names the agent (`"agent": "gm-assistant"`) and where that
  repository's GitHub token is read from (an INI file section and key, or an env file and key).
  `start` and `post` refuse outside a participating repository, with the fix in the message.
- **FR-002 Nothing fires for other projects.** Every hook exits at once, silently and successfully,
  unless THIS session has an active watch. A watch can only be started from a participating
  repository, so the diagram repository and every other project see no output and no GitHub call.
  No hook path may fail a session: every error exits 0, except the deliberate wake (exit 2).
- **FR-003 Commands** (run by the session through Bash; the session is `$CLAUDE_CODE_SESSION_ID`):
  `start OWNER/REPO#N` (what is already on the issue counts as seen), `stop [OWNER/REPO#N]`,
  `status`, `post OWNER/REPO#N` (body from a file or stdin), `open OWNER/REPO "title"` (creates an
  issue, body from a file or stdin, and starts watching it). A session may watch several issues.
- **FR-004 Activity** is a new comment, an edited comment, an edit to the issue's title or body,
  and the issue being closed or reopened.
- **FR-005 Identity.** Everything posted carries a visible `**[<agent>]**` lead and a hidden
  `<!-- issue-watch agent=<agent> -->` marker; a watch never reports its own agent's posts. The
  GM's own comments (no marker) are reported.
- **FR-006 Delivery on the GM's message**: unseen activity is added as context, framed as coming
  from other sessions or people - information to weigh, not instructions - newest five items, each
  trimmed, and every older one by its heading and link (FR-014). Delivered items are not
  delivered again.
- **FR-007 Delivery at the end of a turn**: unseen activity blocks the stop ONCE and is shown; it
  never blocks twice in a row.
- **FR-008 Idle wake**: after a turn ends with a watch active, a background check runs every 60
  seconds and wakes the session with the activity; a newer turn's check replaces it; it ends when
  the session ends or no watch is left.
- **FR-009 Install** is one command, idempotent: copy the script to `~/.claude/hooks/` and register
  its three hook entries in `~/.claude/settings.json` (backup first, existing entries untouched).
  A `--check` mode reports whether the installed copy matches the repository's.
- **FR-010 Participation**: this repository gets its `.claude/issue-watch.json`; the
  character-sheet repository gets one written into its tree uncommitted, with a short note for its
  session, as the 211 / 212 / 214 handoffs were.
- **FR-011 First use**: an issue for the feature 214 handoff, watched by this session, once the
  GM's token change lets both sides write.
- **FR-012 Documentation**: the procedure, how to test it, and the GitLab differences (only the API
  calls and the comment markup) are written where the next session finds them.

- **FR-013 A watch survives `/clear`.** A hook or command whose session id has no watch adopts
  the watch recorded for the same Claude process and carries on; activity posted after a `/clear`
  is delivered like any other (SC-004).
- **FR-014 Nothing is dropped unseen**: when more than five items are waiting, the newest five are
  shown in full and every older one is listed by its one-line heading and link.

### Amendment - message 4 (2026-10-04)

- **FR-015 An issue may be named by its URL** wherever `OWNER/REPO#N` is accepted.
- **FR-016 The procedure is written where every participating session reads it**: "Working a GitHub
  issue" in the user-level `~/.claude/CLAUDE.md`, which both containers load - watch first, read,
  acknowledge on the issue, work under the repository's rules, report at milestones, keep watching
  until closed, and who closes it (the side that asked, once verified; the implementer when Eli
  filed it alone).
- **FR-017 A linked issue is a reminder, by hook**: when the GM's message links an issue in a
  participating repository that this session is not watching, the prompt hook adds a reminder with
  the `start` and `show` commands. No network call; outside a participating repository, nothing.
- **FR-018 `show`** prints the issue and its whole thread; **`close`** optionally comments, closes
  the issue, and stops the watch.
- **FR-019 A watch ends when its issue closes** ("watching it until it's done"), with a delivered
  line saying so.

## Decisions (each made by the session, each cheap to change)

1. **No daemon.** The GM's message 1 imagined "a script running in the background". The background
   part is the async `Stop` hook (memwatch's tested mechanism), which runs exactly while the session
   is idle, which is the only time a wake is wanted; while it is busy, the next prompt or turn end
   delivers. This REPLACES the line in the session's answer to message 1 that the watcher "must not
   wake the session by exiting": that warned against a process whose exit starts a turn at any
   moment, while this wake can only fire when no turn is in progress, and the GM's next message
   retires it, so it never interrupts work. Declined: a detached poller with pidfiles - it survives the session it serves, needs
   lifecycle code, and wakes nobody by itself.
2. **The watch is keyed by session id AND by the session's Claude process.** Every session gets
   `$CLAUDE_CODE_SESSION_ID` in its Bash environment and the same id on hook stdin; `/clear` mints a
   new id but keeps the process. So a watch also records `pid:<pid namespace>:<claude pid>`
   (memwatch's key, which survives `/clear` the same way), and the first hook that finds no watch
   for its id adopts the one recorded for its process (FR-013).
3. **Code in one place, opt-in in each repository** (the GM's "shared ... but must not be firing ...
   for other projects"). Declined: a copy of the script in each repository (two copies drift), and a
   hook registered per repository (the sheet repository would need the code anyway).
4. **Token per repository, read from where that repository already keeps secrets.** No new secret
   store. Which repository holds a given issue is the participants' choice; both tokens get Issues
   read/write on both repositories (the GM's change), so either works.

5. **The procedure lives in the user-level `CLAUDE.md`, not in each repository's** (message 4): it
   is the one file both containers load, so one copy serves both repositories and cannot drift; its
   trigger names the opt-in file, so it is inert elsewhere. Declined: a copy in each repository's
   `CLAUDE.md` (two copies to keep in step, one of them in a repository this session does not
   commit to).

## Accepted limitations

- **A busy session hears about activity at its next turn boundary, not instantly** - the GM's
  "not interrupted". The cost is minutes of latency on a long turn.
- **The session must be running.** A closed session is woken by nothing; a restarted (not
  cleared) one is a new process and starts its watch again.

## Success criteria

- **SC-001** In a repository without the opt-in file, the hooks produce no output and make no
  network call (asserted by test).
- **SC-002** A comment by the other agent reaches this session at the next prompt, at turn end, or
  by an idle wake, exactly once.
- **SC-003** The session's own posts never come back to it.
- **SC-004** Activity posted after a `/clear` still reaches the session (asserted by test).

## Review history

- **Round 1 - CHANGES REQUIRED** (2026-10-03). Every clause carried and nothing unrequested;
  Decision 1 (no daemon), the idle wake, `open` and the GitLab notes upheld. Two changes: (1) the
  watch was keyed by session id alone, so a `/clear` silently ended it - the exact "don't just
  ignore it" failure the GM asked the hooks to prevent; now it also records the Claude process and
  is adopted after a `/clear` (Decision 2, FR-013, SC-004). (2) The idle wake contradicted the
  session's own earlier "must not wake by exiting" without saying why; Decision 1 now says. The
  reviewer's aside - older items were only linked - is taken as FR-014.
- **Round 2 - FAITHFUL** (2026-10-03). Both round-1 changes confirmed; FR-013 and FR-014 found in
  scope (both serve "don't just ignore it"); no new findings. Its one wording note - FR-006 still
  said "a link for the rest" - is aligned with FR-014.
- **Round 3 (amendment, message 4) - FAITHFUL** (2026-10-04). FR-015 to FR-019 and Decision 5
  traced to message 4; the prompt-hook reminder, `show` / `close`, the watch ending on close and
  the procedure's who-closes rule all found in scope; no carve-outs.
