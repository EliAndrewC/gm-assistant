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

## Balancing pass (2026-08-26)

After the old-pool audit the female formats ran 3-10; a re-cull of the raw lists against the freed
stems admitted 22 more attested names, plus 2 court names and 4 invented names on thin initials,
and 38 male names on the thin initials B/D/E/O/R/W/Z (32 attested, 6 built on the attested
prefix-plus-suffix commoner pattern, flagged `invented`). Every addition went to the emptiest
format at the time. Female formats now run 7-10, male 26-27.

## Second collection pass (2026-08-26): temple registers and more shumon-aratame-cho

`female-attested-2.jsonl` (403 lines, 292 distinct; Japanese-language hunt) and
`female-attested-3.jsonl` (455 lines, 303 distinct; English-language hunt), with their source tables
in `female-sources-2.md` / `female-sources-3.md`. New sources that yielded: the 112 Mantokuji
divorce-temple petitioners (Kozuke, late Edo, with counts), an 1837-1865 Umaji (Kameoka) register
top-19, a Kinshoji (Chichibu) women's confraternity plaque, Kishimoto's list of late-Edo commoner
names extinct by Meiji (Baka, Bon, Reo, Wiro, Yan...), and ~1,600 Japanese/English Wikipedia
women-by-era category titles hand-reduced to given names. Dead ends, recorded in the source files:
ADEAC municipal archives (JS-only viewers), scanned-image register PDFs (Kawabe turned out to be the
Tochii 1671 register already used), the Hayami/Cornell/Kurosu demography papers (no individual
names), Throndardottir's SCA book (not online), the Mantokuji article in English (paywalled).
Result: 155 names new to the corpus, but on the rare initials nearly every one is blocked by the
loose similarity rule against a pool or roster name (Rin/Rie, Ruri/Furi, Etsu/Etsuji, Ben/Benka,
Waka/Wakahiko, Ume/Umeko) - 41 promoted, mostly on C/H/K/M/T/Y. No source anywhere yields a
pre-modern female name in Z; D has three (Dai, Dashi, Den), all blocked by male names.

## Third collection pass (2026-08-26): targeted at the eight short female initials

`female-attested-5.jsonl` (35 rows; inscriptions, contracts, the Nishinomiya museum document-reading
blog, an OCR of the Kawabe 1671 register) and `female-attested-4.jsonl` (Meiji registers of Edo-born
women, Kotobank biographical dictionary, further Wikipedia categories), sources in `female-sources-4.md`
/ `-5.md`. Yield against the pool: ONE promotable name (Fuchi). Eighteen attested rare-initial names
were blocked by the loose rule, nearly all by male pool names one edit away (Etsu/Etsuji, Ume/Umehiko,
Bon/Bonshun, Den/Denkichi, Dai/Daigo, Roku/Rokuro-, Waki/Wakizaka, Rei/Reiji, Raku/Kaku); the
rest of the "addable" list were pre-Heian royals, nuns' Buddhist names and a geiko name, which are not
given names for our purposes. The collectors' own list of what is attested-but-blocked is in the
sources files so nobody re-collects it. Conclusion recorded: the record has been mined; the remaining
gap is a similarity-rule decision, not a sources problem.
