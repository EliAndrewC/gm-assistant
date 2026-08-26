# raw/ - attested pre-modern Japanese given names (collected 2026-08-25)

Load this directory when expanding the `/name` pool. These files are the SUPERSET of real names
the pool is grown from under the SKILL.md "Period Sensibility" rule (majority attested, at most
20% invented, invented budget spent only on thin initials). They are deliberately uncurated: not
deduplicated across sources, not checked against the pool or the similarity rules, and carrying no
research beyond what the source gave for free. A name gets researched (meaning, kanji triangle,
explanation format) only when it is promoted into `pool-*.jsonl`.

| file | what | size |
|---|---|---|
| `female-attested.jsonl` | one line per source occurrence; 2,380 lines, 1,149 distinct, 614 distinct once the `issendai-geisha-*` sources are dropped | `name, kana_or_kanji, source, url, rank, frequency, period, notes` |
| `female-sources.md` | the 23 sources, yields, caveats, failures | |
| `male-attested.jsonl` | 7,557 lines, 3,568 distinct; `kind` = nanori / tsusho / yomyo / buddhist / commoner | `name, kanji, kind, source, url, rank, frequency, period, notes` |
| `male-nanori-elements.jsonl` | 255 nanori building blocks with kanji, position, meaning - the combinatorial system that makes the male stock effectively unbounded | `element, kanji, position, meaning, source, url, notes` |
| `male-sources.md` | the sources, yields, caveats, failures | |

Culling notes the collectors left (details in the two sources files):

- Female: the 609 `issendai-geisha-*` lines are professional names from the 1730s to the 2010s with
  no per-name period - drop them wholesale or cull hard. Village-register names were transcribed from
  table images by eye; historical kana spellings are preserved literally (Shiyau, ゑ -> e). Prefixes
  (o-, 小) and suffixes (-no, -he) were stripped to the base with the affix in `notes`.
- Male: jawiki lines were parsed from article leads across 12 category sweeps (capped at 1,000 per
  category); romaji for kanji-only sources (Kiyose, nihonjin-name, jawiki tsusho) was supplied by the
  collector and is flagged in `notes`. Issendai's merchant table is labeled late Edo by assumption.
- Both: distinct-name counts per first letter are the input to the invented-name budget. Female
  non-geisha: K 109, S 88, T 76, M 48, H 45, I 39, N 35, Y 29, A 28, C 24, F 20, R 19, O 15, E 9,
  G 9, U 8, B 4, J 3, W 3, D 2, Z 1. Male: T 570, S 507, K 493, M 479, N 281, Y 253, H 241, I 90,
  A 88, J 82, G 80, C 78, U 69, F 64, R 50, Z 36, D 32, B 28, O 18, W 2.

## Culled lists (2026-08-25)

`female-culled.jsonl` (191) and `male-culled.jsonl` (2,005) are the attested names that survive:
geisha sources dropped; malformed or historical-kana spellings dropped; names within edit distance 1
of, or a prefix/extension of, any pool name or campaign-roster name removed (`is_too_similar`, the
pool-wide rule); then a greedy pass keeping a mutually distinct set under the same rule, ordered so
names attested by more sources win ties. The prefix clause is the expensive one for women (Kiyo
blocks Kiyoko, Kiku blocks Kikuno): 398 candidates -> 191 strict, 218 with edit distance alone.
Each line: `name, sources, attestations, periods, kanji, kinds`. These are still unresearched.

## Promotion pass (2026-08-25)

401 male and 89 female entries were promoted into `pool-*.jsonl` from the culled lists (plus 17
`O-` forms of attested Edo bases, 2 court names, and 14 invented names on thin female initials).
Every promoted entry's `notes` states its attestation (source type, period, kind) or says it is
constructed in the pre-modern idiom, plus the kanji triangle; `invented: true` marks the
constructed ones. The female target of 200 was NOT reached: after hand-removing transcription
artifacts (Maa, Nme, Ayaya...) and on-yomi court readings from the 191 "mutually distinct"
survivors, only ~66 clean attested names remained, and the pool-wide prefix clause blocks the
`-ko` / `O-` / `-no` extensions of every base already present. Reaching 200 would have needed
~100 invented names, past the 20% budget, so the pool grew to what the rules allow. A further cost surfaced at merge time: the validator applies the prefix rule ACROSS genders, so the two-mora women Tsune and San alone knocked out 18 male nanori (Tsuneharu, Sanemoto...); the male side was topped back up from the culled list, the female side was not (no stock to draw on).

The 18 `TOO SIMILAR TO CAMPAIGN` lines `validate_pool.py` prints are all PRE-EXISTING old entries that collide with names already on the campaign roster (Isao, Noboru, Reiko, Ayame...). They are harmless in use - `pick_name.py` filters against the roster at pick time - and `fix_pool.py` would delete them; the GM asked that the old pool be left alone (2026-08-25), so they stay until the GM says otherwise.
