# Tasks: The Overlap Matrix

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md)

- [x] **T001** `OVERLAP_CLASS` in `check_village.py`: every geometric key -> one class (data-model §1).
- [x] **T002** Drawn-extent extraction (data-model §4): fields via `plots`, groves via `clumps`+`r`, forest via `tree_crowns`, wells via `vr`, markers via `vw`/`vh`, linear features stroked at TRUE half-width.
- [x] **T003** The policy matrix (data-model §2) + parent-scoped exemption (§3), forbidden by default, every permission carrying a reason string.
- [x] **T004** Read-only DRY-RUN over the whole pool. Run ONCE, read once. *Verify*: a report listing every forbidden overlap per map.
- [x] **T005** Classify from the dry run: real defect -> fix the map; legitimate -> a permission with its reason. No pair left implicit (SC-003).
- [x] **T006** Promote to `features_do_not_overlap` + the `every_feature_classified_for_matrix` ratchet. *Verify*: ratchet fails by name on a synthetic unclassified key.
- [x] **T007** Freeze the dry-plot-over-water capture into `pool/regressions/`; unit tests for the matrix, the parent scope, the permissive rows and the envelope-vs-drawn rule.
- [ ] **T008** Fix the dry crop plot over the stream on Ubame (FR-012). NOT DONE - itemized in `_MATRIX_OUTSTANDING` with the other 10 real defects the first run found. See the report.
- [x] **T009** Retire the per-pair checks the matrix subsumes (FR-010). **AUDITED 2026-07-26 - CONCLUSION: retire NONE.** FR-010 says retire what the matrix *subsumes*; the audit found it subsumes none of the nine candidates outright. Every one of them enforces a **clearance margin** on top of the bare no-overlap test - a required gap in feet between two features - and the matrix expresses only "these two drawn extents must not intersect", which is the margin-zero case. Deleting them would have silently loosened nine rules from "stay N feet clear" to "merely do not touch", and no test would have gone red, because a map that satisfies the margin satisfies the matrix by construction.

  The general rule this settles, worth remembering the next time the question comes up: **a per-pair rule is subsumed only if its geometry is margin-zero.** Overlap and clearance are different predicates, and the matrix is deliberately only the first. The nine keep their reason recorded at the point of definition per FR-010's "any kept MUST have a reason".
- [x] **T010** Document the contract in `settlements.md` where authors will read it: "classify the key, get every rule."
- [x] **T011** Cheap linters, whole affected test files, then `make done` ONCE, backgrounded.
- [x] **T012** Confirm no map's DEPICTION changed except the fixed defect (the scoped Principle XII close).
- [x] **T013** Stop-work ritual: commit in the clone, then `sync-with-main.sh done`.
