# Female attested-name sources, pass 4 (2026-08-26)

Companion to `female-attested-4.jsonl`. Target: women born before 1868 whose given name begins with A, B, D, E, F, G, I, J, R, U, W or Z, at least two letters away from the pool names already held. Everything below is new relative to passes 1-3. The pass was run mostly as scripted crawls (Wikidata SPARQL, the ja.wikipedia API, the kotobank keyword index) because free-text web search had stopped turning up new register transcriptions.

## Sources used

| id | URL / method | what it is | yield (lines) | caveats |
|---|---|---|---|---|
| wikidata-jawiki-pre1868 | SPARQL on query.wikidata.org: female humans with a ja.wikipedia article and P569 before 1868-01-01 (3,098 rows, 1,075 with Japanese-script labels); readings from P1814 or parsed from the article's first parenthesis via the MediaWiki `extracts` API | Elite women with birth dates; the only systematic way found to get a BIRTH YEAR next to every name | 7 (Atsuko, Ioko, Iwashiro, Ikuko, Ryoko, Reiko, Aguri) | Court and daimyo-house women dominate; -ko names are on-yomi in some articles (eiko/eishi) and the article's kana was preferred over P1814 where they differed |
| jawiki-cat-crawl | MediaWiki `categorymembers` over 34 seed categories (幕末の女性, 明治時代の女性, 19世紀日本の女性 and subcats, 大奥関連人物, 将軍側室/正室, 江戸時代の俳人/歌人, 女性画家, 大名の正室/側室 by domain, 尼僧 ...) to depth 2 = 3,763 titles, minus those already covered; intros fetched and parsed for the title reading plus 名は / 実名 / 幼名 / 俗名 / 別名 patterns with furigana; birth year taken from the first western year in the intro | Women whose ARTICLE gives a personal name different from the title (院号 / 局名 pages) | 5 (Ate, Itsuki, Inui, Izumi, Aku) | The parse only sees the intro paragraph; a 名は buried lower in the article is missed |
| kotobank-nihonjinmei | All 1,080 pages of the 日本人名大辞典+Plus keyword index (74,396 headwords) crawled; 1,401 headwords selected (pure hiragana, kanji surname + hiragana given name, or ending 女/尼/局/院/姫/の方/御前/夫人/后/妃) and each entry fetched; kept if the entry says 女性/妻/娘/側室/尼 etc. and the birth year or period label is pre-1868 | The requested kotobank pass, done as a full index sweep rather than by guessing search strings | 3 (An, Riku, Etsu) | Hiragana-titled headwords are overwhelmingly Meiji-born (school founders, midwives, weavers); the pre-1868 residue is small and mostly already held (Ume, Ine, Iso, Ichi, Raku, Den, Ren). Court women appear under 院号 with the given name inside the entry |
| jawiki-ooku-pages | 徳川家定付き大奥女中, 和宮付き大奥女中, 天璋院付き大奥女中, 徳川家茂付き大奥女中, 本寿院付き大奥女中, 絵島, 幾島 | Named Ooku attendants | 4 (Ejima, Ikushima, Utahashi, Iwao) | These are SERVICE NAMES (女中名), flagged as such in `notes`; the brief's pen-name rule was applied loosely here because the brief explicitly asked for 大奥女中 and the personal names of these women are not recorded anywhere |
| jissen-kosetsu-2021 | Jissen Women's University Kosetsu Museum leaflet, 江戸時代後期の女性画家たち (PDF, text extracted with pdftotext) | Late-Edo women painters with their 名 | 1 (Rai, reading inferred) | Also gives Gyokuran 名は町 (Machi), Hayashi Haiho 名は蝶 (Cho), Ema Saiko 名を多保 (Taho), Kagawa Hyosen 名を苑葵 (reading not given) - none in the target initials or reading not recoverable |

## Rare-initial tally (distinct new names, at least two letters from every pool name)

A 4 (An, Ate, Atsuko; Aguri and Aku are attestation upgrades for forms already in raw) - E 2 (Ejima service name, Etsu upgrade) - I 8 (Itsuki, Inui, Ioko, Iwashiro, Ikuko, Izumi, Ikushima, Iwao; the last two are service names) - R 4 (Riku, Ryoko, Reiko, Rai) - U 1 (Utahashi, service name) - B 0 - D 0 - F 0 - G 0 - J 0 - W 0 - Z 0.

Found but WITHIN one letter of a pool name, so not written to the jsonl (recorded so the search is not redone): Isako (中山績子 1795, vs Iyako), Utano (長谷川歌野 1832, vs Utako), Riya (尼崎りや 1677, ashigaru's daughter, vs Riyo). Riya is the one genuinely commoner, register-grade form in that group.

Found but already in raw (not re-collected): Ayaya (尾崎局 実名あやゝ), Ako (雲照院), Akane (南の局), Ei (葛飾応為 名は栄; 妙向尼 名は営; 瑛想院 名は永), En (野中婉 1661), Rui (佐々木累), Ruri (大石るり 1699, 湯浅瑠璃 1670), Rin, Ryu, Ryo, Riu, Rei (青松院 実名れゐ), Ren (平井連山), Ran (高場乱 幼名), Riki, Dashi, Den, Jako (沼田麝香), Ginchiyo, Uji, Ima, Ine, Iso, Ichi, Ume, Raku.

## Rejected or empty

- kishimotoyoshinobu.com "明治時代初期の女性名" - fetched; it is Tsunoda Bunei's list drawn from pre-war girls'-school alumnae directories, so the bearers were born in the 1870s-90s. Not used. The brief's "1871 register page" on that site could not be located: site search, Google and the site's own Q&A index turned up only the 壬申戸籍と身分法 essay (no names) and the two pages already used in pass 3.
- kuzan.hatenadiary.jp "メモ・明治の女性名" - a 1941 alumnae roster of a normal-school elementary; graduation years Meiji 26+, so born after 1880. Not used.
- 壬申戸籍 / 明治初期 人別 transcriptions - searched in Japanese six ways; the 1872 register is sealed (閲覧禁止 since 1968) and nothing transcribed with women's names is online. Genealogy blogs on 明治19年式戸籍 discuss method, never print names.
- ADEAC (adeac.jp) 宗門人別改帳 pages for Nagara, Nakatsugawa, Tsurugashima, Miyako and the Shinshu archive - the transcription text is loaded by a JS viewer; curl and WebFetch both get only navigation. Not extractable without a browser session.
- J-STAGE / CiNii - CiNii OpenSearch returned nothing for 宗門改帳 女性名, 人別帳 女性 名前, 近世 女子名; J-STAGE hits (Sekine and Shibuya on gravestones, the Kaga-han journal) print no name tables. The Mori 2024 paper used in pass 3 remains the only table found.
- Wikidata query for women with a death date but no birth date timed out three times (502 / upstream timeout) even restricted to 1500-1900; the category crawl covers the same population.
- ja.wikipedia Category:大奥女中 and Category:江戸幕府大奥の人物 - 404; the live categories are 大奥 and 大奥関連人物, both crawled.
- oterac.com "戦国・江戸の女性" - 22 names, all already held.
- corontomomousagi.com girl-name page - 404 (second URL tried).
- 大阪府立図書館 江戸時代～女子の本懐 - WebFetch returned hallucinated content; discarded.
- WebSearch for specific hiragana forms (ゑん, ゑい, うら, いさ, わき, えつ, ぎん, わか, うた ...) with 人別帳 / 宗門改帳 - only the pass-1-3 pages came back.
