# Research: the historical basis behind the /diagram rules

*Every rule in the [`../settlements/`](../settlements/) and [`../buildings.md`](../buildings.md) docs that came out of historical research has its finding recorded here - what the research found, the decision it drove, and any deliberate departure from literal reality. The rule files stay operational; this tree is where the reasoning lives, and where citations and deeper historical context get added as they accumulate.*

**Load a research file when you are CHANGING a rule, questioning one, or adding to the record** - never merely to draw a map. Rules link in by stable `#anchor`.

| Research file | Grounds the rules in |
|---|---|
| [`archetypes.md`](archetypes.md) | [`../settlements/archetypes.md`](../settlements/archetypes.md) |
| [`buildings.md`](buildings.md) | [`../buildings.md`](../buildings.md) |
| [`cities/capitals.md`](cities/capitals.md) | [`../settlements/capitals.md`](../settlements/capitals.md) |
| [`cities/defenses.md`](cities/defenses.md) | [`../settlements/cities/defenses.md`](../settlements/cities/defenses.md) |
| [`cities/fabric.md`](cities/fabric.md) | [`../settlements/cities/fabric.md`](../settlements/cities/fabric.md) |
| [`cities/government.md`](cities/government.md) | [`../settlements/cities/government.md`](../settlements/cities/government.md) |
| [`cities/hinterland.md`](cities/hinterland.md) | [`../settlements/cities/hinterland.md`](../settlements/cities/hinterland.md) |
| [`cities/river-cities.md`](cities/river-cities.md) | [`../settlements/cities/river-cities.md`](../settlements/cities/river-cities.md) |
| [`fields.md`](fields.md) | [`../settlements/fields.md`](../settlements/fields.md) |
| [`homesteads.md`](homesteads.md) | [`../settlements/homesteads.md`](../settlements/homesteads.md) |
| [`religion-and-death.md`](religion-and-death.md) | [`../settlements/religion-and-death.md`](../settlements/religion-and-death.md) |
| [`towns.md`](towns.md) | [`../settlements/towns.md`](../settlements/towns.md) |
| [`urban-features.md`](urban-features.md) | [`../settlements/urban-features.md`](../settlements/urban-features.md) |
| [`vegetation.md`](vegetation.md) | [`../settlements/vegetation.md`](../settlements/vegetation.md) |
| [`water.md`](water.md) | [`../settlements/water.md`](../settlements/water.md) |

## Entry format

Every entry carries the same four fields, in this order:

```
## <stable anchor title>

**Grounds:** the checks, generator methods or constants this finding justifies

**Evidence:** <one or more classes, see below>

**Sources:** `key`, `key` - or an explicit "not recorded"

<the finding: what the research found, the decision it drove, and any disclosed departure>
```

`**Grounds:**` is what makes a stale finding visible - if nothing in the codebase matches it any more, the entry is describing a rule that no longer exists.

## Evidence classes

The vocabulary is fixed, and an entry may carry several (they compose - a finding can be `attested` in one tradition, `corroborated` by the other, and still applied as a `liberty`):

| Class | Means |
|---|---|
| `attested` | A specific historical instance, figure or statute is named. The strongest class. |
| `corroborated` | Both reference traditions agree (China-first with Japan agreeing, or the reverse). |
| `analog` | The figure is borrowed from an adjacent domain and flagged as such - e.g. the Willow Palisade spacing standing in for a polder dike, where no polder-specific statute was found. Treat as weaker than `attested`. |
| `interpolated` | Reasoned from a related or aggregate figure rather than a direct one - e.g. a national average narrowed to one village type. |
| `reconstruction` | Reasoned from norms with no direct source. Honest inference, not evidence. |
| `setting-canon` | Rests on `l7r.md` / `budgets.md` rather than on history. Not weaker - just a different authority, and it outranks history where the two disagree. |
| `liberty` | A deliberate, disclosed departure from the historical answer, taken for legibility or game reasons. Always paired with whatever the history actually said. |
| `researched` | Research was done in-session but its class was never recorded. A backlog marker: sharpen it when the entry is next revisited. |

The classes were seeded from each entry's own language and hand-set for the entries reviewed closely; **correct one when you revisit its entry** rather than trusting it blindly.

## Citing

Sources live in [`SOURCES.md`](SOURCES.md) with stable keys; an entry cites by key. **Never add a citation that has not actually been consulted** - if a finding's source was not written down at the time, its `**Sources:**` line says `not recorded` and that is the correct, honest state. 72 of the 83 entries currently say exactly that: the research was done, the citation was not captured. Filling those in is ordinary future work, done by re-consulting, never by attributing a plausible-looking source after the fact.

Named real-world measurements (Suzugamori, Pingyao, Himeji, Fushimi...) are *anchors* rather than works - they are listed in a separate table in `SOURCES.md` and cited inline by name.

## Adding to the record

Keep the four fields. Anchors are stable - rules link to `#slug`, so rename a heading only if you also fix its inbound links. Citations belong here rather than in the rule file: per project policy the *why* is mandatory and explicit sources are optional, so a bare finding is fine and a cited one is better.
