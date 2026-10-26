# Tasks 229

- [x] T001 Fox secret libraries into l7r.md (done before the spec)
- [x] T002 Docs: FR-009..FR-020, generation-rules "memory" line, script comments
- [x] T003 house-style: local paths in content (+ cases)
- [x] T004 clone-sync: seed secrets (+ test)
- [x] T005 clone-sync: stop mode + settings.json Stop hook (+ test)
- [x] T006 op.OPNotConfigured (+ test)
- [x] T007 setup-dev-env: flyctl
- [x] T008 art.py steering + headshot pad (+ tests)
- [x] T009 frontend-review rule
- [x] T010 Shoda price test
- [x] T011 guards.md, CLAUDE.md, autoMemoryEnabled false
- [x] T012 make done; push; delete memory files

## Implementation notes
- Fox libraries: the vetted OP page (public body and GM-only notes) converted from Textile and inserted under The Fox
  Clan as "The Secret Libraries of the Fox" and "The Truth Behind the Secret Libraries", before "The Three Man
  Alliance". No TOC entry: the GM's curated TOC lists none of The Fox Clan's subsections.
- House-style path rule: for a Bash heredoc only a redirect target counts as the destination, because a python
  heredoc that edits l7r.md names that file in its code (found while writing the rule; a quiet case pins it).
- Headshot padding lives in `crop_headshot` (y <= 0 gains a white band of 12% of the crop height, split evenly to the
  sides), not in `get_headshot_crop`, whose coordinates drive the webapp's crop box and must stay inside the image.
- Footwear is caste-aware: peasants get straw sandals, everyone else white tabi and straw zori.
- `OPNotConfigured` subclasses `ValueError`, so any caller that already caught the old `ValueError` still does; the
  six fail-soft reads re-raise it and stay fail-soft for network errors.
- Secrets are refreshed whenever main's copy differs, not only when missing: `deploy-secrets-hooks.sh` already refuses
  a differing clone copy at deploy, so a clone-only edit to the secrets file was never a supported state.
- frontend-review TDD: the rule was run (via general-purpose adopting the edited definition, the same-session
  gotcha) on a reconstructed card reading "Browse 200 place names" beside a live "12 of 200 match": it flagged the
  first as issue 1 and called the second fine. No live page has the defect today.
