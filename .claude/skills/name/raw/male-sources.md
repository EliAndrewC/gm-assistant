# Raw male given-name sources

Collected 2026-08-25 for feature 200 follow-up. This is an uncurated superset:
no dedupe, no similarity rules, no meaning research. Only metadata that came
free with each source. Files:

- `male-attested.jsonl` - one attested name per line (schema in the collection brief).
- `male-nanori-elements.jsonl` - name ELEMENTS (nanori pro-/deuterothemes, Edo merchant first elements), not whole names.

Romaji is capitalized, macron-free (Nobunaga, Goro, Sukezaemon). Where a source
gave only kanji (Kiyose, nihonjin-name, jawiki tsusho), the romaji reading was
supplied by the collector from a kanji-element table and is flagged in `notes`;
treat those readings as plausible, not attested.

| id | URL | what it is | names yielded | caveats |
|---|---|---|---|---|
| `bryant` | https://sengokudaimyo.com/japanese-names | Anthony J. Bryant's SCA Japanese names article: structure, yomyo/zokumyo/nanori/azana, Buddhist names, the "Principal pro- & deuterothemes in common Japanese men's nanori" chart (image + `/s/nanori.pdf`) and the "Common ending elements in older Period men's names" image | 48 example names; 89 nanori elements + 5 old ending elements in the elements file | The nanori chart is an image on the page; transcribed from the PNG and cross-checked against the PDF text. Example names include a few modern/pre-Heian illustrations (Toshiro, Muchimaro, Kamako) kept with a note. Kanji for example names supplied by collector where the article gave romaji only. |
| `sljfaq` | https://www.sljfaq.org/afaq/historical-names.html | sci.lang.japan FAQ "How are historical names formed?" | 35 names; 29 elements (no kanji) | Element list is romaji only. Famous-bearer names given without kanji; kanji supplied by collector for the 12 famous bushi. |
| `kiyose` | https://www.city.kiyose.lg.jp/siseijouhou/kouhou/shishi/1012758.html | Kiyose city history blog: male names from two shumon-ninbetsu-aratamecho registers, Noshio village 1774 (125 readable men, 116 name types) and Kamikiyoto village 1809 (62 men, 59 types) | 175 (116 + 59) | Names are only in two PNG tables (`1774m.png`, `1809m.png`); transcribed visually from the images. Kanji only - romaji supplied by collector; 3 names contain 重 (read ju). Frequencies come from the table headers (2人/3人). |
| `nihonjin-name` | https://nihonjin-name.jimdofree.com/ (series 男性名と「郎」, pages 4, 5, 6) | Ito Nobuhiko's name-research site. Page 5 reproduces the 93 villager names from the 1298 Omi Tsuda/Okutsushima joint oath (Kamakura Ibun no. 19703); page 4 lists the earliest father names in the Kokawa Oji shrine natsukecho (from 1478); page 6 quotes Heike Monogatari zokumyo | 114 | Many 1298 names are in kana or mixed kana/kanji; 8 with an illegible box (□) were dropped. Romaji supplied by collector. Pages 1-3 and 7-9 are statistics (percent of -ro names), not lists. The site also cites five shumon-aratamecho (Kawabe, Isehara, Okazaki) but does not reproduce their names. |
| `issendai-merchants` | https://issendai.com/wp/japanese-names/merchants-names-with-alternate-spellings/ (also `merchants-names-by-pronunciation/`, `first-elements-of-merchants-names/`, `suffixes-used-in-merchants-names/`) | Issendai's Edo-era merchant name tables: pronunciation, kanji spelling, count | 583 (kanji spellings of ~510 pronunciations); 133 first elements in the elements file | Page does not state which merchant directory the counts come from (the `commoner-mens-names-in-edo-era-japan-part-1` essay promises the source but has no list and no part 2). Period recorded as late Edo by assumption. `rank` = position in the count-sorted pronunciation table. Site blocks plain curl (Mod_Security); needs browser headers. |
| `issendai-buddhist` | https://issendai.com/wp/japanese-names/japanese-buddhist-names/ | Issendai's table of attested Buddhist (dharma) names with dates and academic sources | 18 male names dated 794 or later | Pre-794 entries (Nara) and female entries were dropped. Period derived from the date column. |
| `jawiki` | https://ja.wikipedia.org/wiki/<article> (per line) | Japanese Wikipedia category members, given name + reading parsed from each article's lead sentence ("姓 名（せい めい）"). Categories: 戦国大名, 戦国武将, 鎌倉幕府御家人, 平安時代の武士, 鎌倉時代の武士, 室町・安土桃山時代の武士, 南北朝時代の武将, 江戸幕府旗本, 平安時代の貴族, 鎌倉時代の公家, 南北朝時代の公家, 室町・安土桃山時代の公家, and 僧 categories for Heian/Kamakura/Muromachi/Azuchi-Momoyama (kind=buddhist) | 6,584 (incl. ~450 tsusho parsed from "通称は..." with collector-supplied romaji) | Capped at 1,000 members per category. Period comes from the category (hatamoto refined to early/late Edo only when the lead says 前期/後期); reading is the first alternative listed. A handful of women slipped past the female filter if the lead did not say 女性. Article-less redirects and clan articles were skipped. |

Sources that failed or gave nothing:

- `https://www.issendai.com/names/index.html` - Mod_Security 406 for curl; the real index is `https://issendai.com/names/japanese-names/`. There is no Sengoku or Heian men's list on Issendai - only Edo merchants, Buddhist names, Azuchi-Momoyama WOMEN, and Nara (pre-Heian, skipped as out of range).
- Japanese Wikipedia list pages named in the brief (戦国大名一覧, 鎌倉幕府御家人一覧, 守護一覧, 公卿一覧) do not exist under those titles; category members were used instead.
- SCA Sengoku Name List (scribd copy) - not fetched (login-walled); Bryant's own article covers the same material.
- No online 宗門改帳 transcription with a usable name list was found beyond the Kiyose page; nihonjin-name cites printed ones only.
