# Tasks: feature 224

- [x] T1 goods.json: miso, soy-sauce; Soybeans reworded
- [x] T2 eras.py: Mitsui miso and soy sauce in seven eras; declined cells noted; regenerate
- [x] T3 baskets: standard and standard-no-housing split (soy sauce after the GM's yield ruling)
- [x] T4 basket.py: snapshots sorted by date; reprice help
- [x] T5 snapshot 2026-10-25
- [ ] T6 export; tests updated and added; gate
- [ ] T7 docs and memory; screenshots and frontend check of the new goods; deploy; diagram#18

## Where it stopped (2026-10-25, weekly soft cap)

Committed in the clone, NOT pushed: 14 money tests fail because they pin the old basket, the old snapshot list or
the old headline. Next:
1. Update those tests (`make test`-style run of tests/test_money*.py lists them: test_cli_convert, the 2017 sheet's
   standard-basket left_out tuple (now also Miso, Soy sauce), test_cli_dated_inputs, test_a_partly_priced_era_says_so,
   test_housing_is_the_largest_lever, test_reading_takes_substitutes_and_quantities, test_cli_history_and_check,
   test_standard_basket_is_the_default_and_carries_the_needs, test_committed_table_is_current (re-run export),
   test_cli_baskets_era_and_export, test_cli_mean_and_weights, test_reprice_adds_a_good_the_newest_snapshot_lacks,
   test_goods_the_old_snapshot_cannot_price_are_named, test_the_page_names_every_goods_figure (14 goods now)).
   Check each failure is the expected new value, not a bug, before re-pinning.
2. spec-fidelity round 2 on the amended spec (soy sauce ruled: 3.0 L a kg), record the verdict.
3. Docs: money SKILL.md range ($453 to $995), l7r/money/CLAUDE.md, memory; gate; screenshots of Miso and Soy sauce
   expanded; deploy; post the new conversions.json on diagram#18 (diagram refreshes its copy).
