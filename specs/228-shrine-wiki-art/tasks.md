# Tasks 228

- [x] T1 spec, spec-fidelity (FAITHFUL round 2), claim
- [x] T2 catalog: Other prefixes, looks.yaml merge, legacy.yaml table + validation
- [x] T3 design: Other, instead semantics, upgrade_params, share_query
- [x] T4 pricing: Other work contract, gm_other_, unpriced
- [x] T5 art.py, describe.py, wiki.py
- [x] T6 routes + guard
- [x] T7 template, JS, CSS
- [x] T8 tests (frozen links, Other, pricing, secrecy, prompt, describe, wiki, routes with fakes)
- [x] T9 docs: l7r/shrines/CLAUDE.md (standing old-links rule, new files), gate
- [x] T10 live check (describe, draw, OP wiki for Shizu's shrine), frontend-review, shrine-text-review of new text
- [x] T11 deploy, verify

Deployed 2026-10-26; verified on l7r-gm-assistant.fly.dev: Shizu's link opens, /shrines/wiki answers, describe
refuses signed-out callers (401) and writes a description for a signed-in GM. frontend-review passed on round 3;
dom_audit: no layout issues.
