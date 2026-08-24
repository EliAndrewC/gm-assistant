# `future-work/` - deferred engineering, split by what kind of map it is about

**Load ONE file: the one for the map type you are working on.** That is the whole point of the
split. This directory replaced a single 3,453-line `future-work.md` on 2026-08-24 at the GM's
direction, because a session planning hamlet work was loading the capital-era backlog to find it,
and a human auditing the list had to sift a changelog to see what was actually outstanding.

| file | load it when | size |
|---|---|---|
| [`farming-communities.md`](farming-communities.md) | working on hamlets or villages - paddy fabric, lanes, homesteads, wells, woodland, the notice board, cohort seeds | large; this is where the live work is |
| [`cities.md`](cities.md) | working on towns, provincial cities or capitals - walls, gates, wards, streets, the castle | small |
| [`compounds.md`](compounds.md) | working on a Mode A compound plan - magistracies, and the estate/mansion types still to be built | EMPTY, deliberately - read why |
| [`cross-cutting.md`](cross-cutting.md) | the thing you are fixing would change more than one kind of map, or no map at all (the gate, the caches, module structure) | small |
| [`closed.md`](closed.md) | you want to know whether something was SETTLED or merely forgotten | a one-line ledger |

## Why these groupings and not others

**Hamlets and villages share a file** (GM 2026-08-24). A village is a hamlet with a headman, a shrine
and tax-free plots - not a different kind of place - and its defects are the same defects.

**Provincial cities and capitals share a file** for the same reason: they are largely scaled versions
of one another.

**Towns are filed with cities**, and that is the one judgment call here. The GM's split named farming
communities and cities; towns sit between. Their open defects are urban in kind - storefronts,
streets, inns, kiln glyphs - even though a town's population is still mostly farmers. Move them if
that reads wrong.

**Compounds are Mode A** - a walled compound drawn as an interior plan rather than a settlement in
its fields. Only magistracies exist today; samurai city estates, governor's mansions, samurai country
estates and keeps are coming.

## The rules that keep this from rotting back into what it was

1. **An entry is OPEN WORK.** Not history, not a lesson, not a decision record. Closed items go to
   `closed.md`; method lessons - dead ends, wrong claims, the shapes failures take - go to
   [`../dev/lessons.md`](../dev/lessons.md).
2. **Close it in the same commit that closes the work.** The audit found two settled questions still
   reading as OPEN, one for five days and one for seven, both about to be put to the GM a second
   time. That is the specific failure this rule prevents, and it costs the GM a decision they had
   already made.
3. **Each entry names the pain, the evidence, and a sketch of the fix.** An entry without a
   measurement is a feeling, and this project's own history says a feeling is usually wrong about
   which fix will work.
4. **Check the era before you act on an old entry.** Much of the city material predates scripted
   generation and assumes a next hand-authored map. There will not be one: the 19 hand-authored maps
   are FROZEN and conversion is the answer for every tier above hamlet
   ([`../migration-plan.md`](../migration-plan.md)). Those entries are annotated - the task is dead,
   the insight is an input to that tier's conversion.
