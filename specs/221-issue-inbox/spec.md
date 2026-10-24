# Feature 221: issue inbox - a session watches a repository for NEW issues

**Request**: [gm-request.md](gm-request.md) (2026-10-24). **Status**: implemented. **Extends**:
[feature 215](../215-issue-watch/spec.md), the issue watch.

## Why

Feature 215 lets a session watch an issue it already knows about. The GM wants to start sessions in
two containers - say the diagram repository doing research and this repository doing its skills and
website - tell each that it is "coordinating over GitHub issues", and have a NEW issue filed for
either side be noticed and acted on at once, the way a comment on a watched issue already is.

## The shape

A session can now watch a REPOSITORY as well as issues: its **inbox**. From then on, an issue filed
in that repository by someone other than this session's agent is delivered through the same three
hooks as a comment (the GM's next message, the end of a turn, or an idle wake within a minute), and
the session starts watching that issue too, so its comments follow without another command. The
inbox lasts until the session stops it; no issue closing ends it.

## Requirements

- **FR-001 `inbox [OWNER/REPO]`** starts an inbox on that repository; with no argument, on THIS
  repository. Issues already in the repository at that moment count as seen (as `start` treats
  existing comments). Several inboxes per session are allowed; starting one twice is harmless.
- **FR-002 This repository's name** comes from an optional `"repo": "OWNER/REPO"` in
  `.claude/issue-watch.json`, else from a GitHub `origin` remote. A session clone's `origin` is its
  main checkout's local path, so a local-path origin is followed to that checkout's origin (a few
  hops at most). If no GitHub repository is found, `inbox` with no argument is refused with the fix
  (add `"repo"`, or name the repository) in the message. This repository's file also gets
  `"repo": "EliAndrewC/gm-assistant"`.
- **FR-003 A new issue** is one whose number is above the highest the inbox has seen, that is not a
  pull request, and whose description does not carry this session's own agent marker. Each is
  delivered with its title, who filed it (the agent marker, else the GitHub login), its link and its
  description (trimmed as comments are).
- **FR-004 A new issue is acted on, not merely reported.** Its delivery says the session is now
  watching it, that working it follows "Working a GitHub issue" in `~/.claude/CLAUDE.md`, and that
  `stop OWNER/REPO#N` drops it if it is not this session's work. The issue's TEXT is still framed as
  information from someone else, never as instructions that override the session's own.
- **FR-005 Auto-watch.** A delivered new issue is added to the session's watched issues from its
  filing time, so comments posted between filing and detection are delivered too, and it then ends
  the usual way (FR-019 of 215: when it closes).
- **FR-006 Same delivery, same silence.** The inbox uses the three existing hooks; no new hook
  registration and no daemon. A session with neither a watched issue nor an inbox stays exactly as
  silent as before (215 FR-002). A session whose only watch is an inbox keeps its watch file and its
  idle wake even while it watches no issue.
- **FR-007 `stop OWNER/REPO`** ends that inbox; `stop` with no argument ends everything; `status`
  lists inboxes alongside issues.
- **FR-008 Survives `/clear`** exactly as an issue watch does (215 FR-013).
- **FR-009 Live sessions keep working across the install.** The installed script replaces the shared
  copy at once, so a watch file written by the 215 script (no inbox field) is read correctly.
- **FR-010 "Coordinating over GitHub issues" is a procedure where every participant reads it**: a
  section next to "Working a GitHub issue" in the user-level `~/.claude/CLAUDE.md` (loaded by this
  container, the diagram container and the character-sheet one): when Eli says the session is
  coordinating over GitHub issues, run `inbox` first, then work new issues as they arrive.
- **FR-011 Said, so reminded, by hook.** When the GM's message in a participating repository says the
  session is coordinating over GitHub issues and it has no inbox on this repository, the prompt hook
  adds a reminder with the `inbox` command (no network call; outside a participating repository,
  nothing) - the same pattern as 215 FR-017's linked-issue reminder.
- **FR-012 Documentation**: the module docstring, the `docs/key-paths.md` entry, and how to test it
  by hand.
- **FR-013 All three named projects take part.** The diagram and character-sheet repositories
  already carry `.claude/issue-watch.json` from feature 215 (read from GitHub 2026-10-24: agents
  `diagram` and `character-sheet`), so the tooling, the shared hooks and the user-level procedure
  are all they need; FR-002's origin-following lets their clones `inbox` with no `"repo"` added.
  Nothing is written into their trees. Their tokens already write issues (diagram#12 and
  character-sheet#2 were worked through them).

### Amendment - messages 2 and 3 (2026-10-24): a notice for a busy session

- **FR-014 A one-line notice after a tool call.** A fourth hook, `hook notice` (PostToolUse), tells
  a busy session that something arrived: one line per new issue (with its title) and per new
  comment or other activity on a watched issue, each announced once. It says the items come in
  full at the end of the turn, and that the session should finish the step it is on or reach a
  stopping point, optionally acknowledging on the issue with `post` first. It does not deliver the
  text; the end-of-turn delivery (215 FR-007) still does, so nothing is consumed by the notice.
- **FR-015 It costs at most one look a minute.** Between looks the hook reads only the local watch
  file; a look uses the same conditional requests (a 304 costs no rate limit). Like every hook
  path it is silent unless the session has a watch, and silent on any failure.
- **FR-016 Every GitHub request has a timeout** (`HTTP_TIMEOUT`, six seconds), so a hung
  connection cannot stall a tool call or the idle wait. (Found while building FR-014: the constant
  existed but was never passed to `urlopen`.)
- **FR-017 Install registers the fourth hook**, idempotently, as FR-009 of 215 does for the others.

## Decisions (each made by the session, each cheap to change)

1. **One repository, one agent: every new issue in my inbox is mine.** Issues for the diagram
   session are filed in the diagram repository and the money skill already files its research there,
   so a session inboxes its own repository and auto-watches what lands. Declined: an addressing
   label or assignee filter - nothing files issues that way today, and an unlabeled issue the GM
   files by hand would be missed. A session that inboxes someone else's repository can `stop` what is
   not its own.
2. **Newness by issue number, not by date.** GitHub numbers issues and pull requests in one rising
   sequence, so "above the highest seen" cannot miss an issue that is edited, relabeled or closed
   before the next look, and needs no clock agreement. The list request is sorted by creation,
   newest first, conditional on its ETag, so an unchanged repository costs no rate limit.
3. **The session's own issues are not delivered** (215 FR-005's marker); `open` already watches them.
4. **The inbox is a field of the existing per-session watch file**, not a second file, so the
   lock, the `/clear` adoption and the wait loop cover it unchanged.

## Accepted limitations

- **"Immediately" means, for a busy session, a one-line notice within about a minute (FR-014),
  with the full text at the next turn boundary; an idle session is woken within a minute.** The
  session finishes the step it is on before acting, which keeps 215's "at an appropriate time".
- **More than 30 issues filed between two looks** (one minute when idle): only the newest 30 are
  seen. Declined: paging the list - not a real rate of filing.
- **The session must be running**, as in 215.

## Success criteria

- **SC-001** An issue filed by the GM or another agent in an inboxed repository reaches the session
  exactly once, and a later comment on it reaches the session without any further command.
- **SC-002** The session's own new issues and pull requests are never delivered as new issues.
- **SC-003** A session without an inbox or watched issue makes no network call (as 215 SC-001).
- **SC-004** A watch file in the 215 shape loads and keeps delivering (asserted by test).

## Review history

- **Round 1 - CHANGES REQUIRED** (2026-10-24). Every clause carried; Decision 1 (auto-watch every
  new issue, no addressing filter) and the pull-request and own-issue exclusions upheld as the
  literal reading. Two changes: (1) the diagram project is a named participant and the spec never
  made it one - now FR-013, after checking that diagram and character-sheet already carry opt-in
  files, plus FR-002's origin-following so their clones need no `"repo"`; (2) the "immediately"
  limitation now cites the GM's 215 words. The reviewer's aside - a one-line notice to a busy
  session after each tool call - is offered to the GM, not built (it would interrupt, which 215
  ruled out).
- **Round 2 - FAITHFUL** (2026-10-24). Both changes confirmed, neither adds unrequested scope;
  FR-002's origin-following found to serve FR-013 rather than extend it. Its one nit - FR-013
  listed before FR-012 - is fixed.
- **Round 3 (amendment, messages 2 and 3) - CHANGES REQUIRED, then fixed** (2026-10-24). FR-014 to
  FR-017 found faithful: the one-minute limit is the approved proposal's own wording and does not
  defeat "at least knows"; extending the notice to comments and other activity is inside what
  message 3 approved; FR-016 (the unused timeout) is a precondition of a hook that runs after every
  tool call. Two changes, both made: the "Immediately" limitation no longer says a busy session
  hears nothing mid-turn, and this entry records that messages 2 and 3 REVERSED round 1's "offered,
  not built (it would interrupt, which 215 ruled out)" - the GM wants the notice, and a notice that
  forces nothing is not the interruption 215 ruled out.
