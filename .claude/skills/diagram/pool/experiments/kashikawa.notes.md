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

**What it is here to show**: the size end of the range, and the one place the scripted pipeline is
allowed to miss. It seats 18 farmhouses against 20 declared households, inside the gate's 0.85-1.05
band but at the bottom of it: at the top of the tier the field is large enough that its margins run
out of frontage before the count is met. The generator widens the cluster band and draws more
candidates rather than re-rolling the map, and reports what actually landed, so the shortfall is
visible instead of silent.

**Known open**: the household shortfall above; plus Inashiro's two - the bare comb floor on the
fan's shoulders (inherited from `build_comb`), and a windward quarter derived from the slope.
