# Design notes: Kashikawa (樫川, "oak river") - scripted hamlet, the top of the band

*One of four demo maps from the scripted-generation experiment (2026-08-11). See
[`../../hamletgen.py`](../../hamletgen.py) for the pipeline and
[`inashiro.notes.md`](inashiro.notes.md) for the head-to-head with the authored Ikegami.*

**Kanji triangle**: 樫 *kashi* "evergreen oak" + 川 *kawa* "river". Kashikawa, "oak river" - named
for the oaks on the high ground the settlement backs onto, which the map draws as its managed
coppice patches and its fengshui belt.

**Subject**: ~20 households - the ceiling of the hamlet band, above which a place needs a headman, a
shrine and tax-free plots and is a village instead - on land falling to the northeast, draining off
the frame.

**What it is here to show**: the size end of the range. As first rolled (2026-08-11) it was also
the one place the pipeline was allowed to miss - 18 farmhouses seated against 20 declared, inside
the gate's 0.85-1.05 band but at the bottom of it - and the notes presented that shortfall as the
honest report it was. The 2026-08-15 re-carve (supply-bank bund hem + the padded well sweep)
re-rolled the whole map and the cluster now seats **all 20**, so the allowed-miss demonstration is
history rather than the map's current state; the reporting machinery is unchanged and a future
re-roll that misses will say so again.

**Known open**: Inashiro's two - the bare comb floor on the fan's shoulders (inherited from
`build_comb`), and a windward quarter derived from the slope. Also: the managed COPPICE patches
the name story leans on land OFF-FRAME on this roll (all three woodland commons sit past the
crop), so the oaks are implied beyond the frame rather than drawn - the fengshui belt is the only
on-sheet woodland. Logged in `future-work.md`.

- 2026-08-15 (supply-bank hem re-roll): bunds hem onto the supply channels' banks
  (`build_comb(supply_banks=True)`, gate `paddy_bunds_clear_the_supply_channels`); the whole map
  re-rolled downstream. `settlement-review` (DELTA) passed the bund/channel read and the three
  re-seated wells, and caught this file's stale shortfall claim plus a gen docstring that was a
  copy of Inashiro's - both fixed the same day.
