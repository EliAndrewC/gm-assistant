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
- [ ] **T009** Retire the per-pair checks the matrix subsumes (FR-010). NOT DONE - deliberately deferred: the matrix is additive first, and retiring proven checks while 11 real defects are still outstanding would remove the precise geometry that currently governs them.
- [x] **T010** Document the contract in `settlements.md` where authors will read it: "classify the key, get every rule."
- [x] **T011** Cheap linters, whole affected test files, then `make done` ONCE, backgrounded.
- [x] **T012** Confirm no map's DEPICTION changed except the fixed defect (the scoped Principle XII close).
- [x] **T013** Stop-work ritual: commit in the clone, then `sync-with-main.sh done`.
