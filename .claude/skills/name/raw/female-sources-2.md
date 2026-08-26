# Female attested names - collection pass 2 (2026-08-26)

Companion to `female-attested-2.jsonl`. Pass 1 sources (issendai, daijirou, Kiyose shishi, nihonjin-name pages, jawiki consort/empress lists, sengokudaimyo) were NOT re-collected. Schema is identical to pass 1. Romaji is Hepburn without macrons; the honorific `o-`/`於` prefix and the archaic `-me` (売/女) suffix are stripped and noted per row.

## Sources used

| id | URL | what it is | yield (rows / distinct) | caveats |
|---|---|---|---|---|
| `kishimoto-mantokuji` | https://www.kishimotoyoshinobu.com/l/江戸～明治時代の女性名について/ | Kishimoto Yoshinobu (genealogist) reproducing the list of 112 women who took refuge at Mantokuji, the Kozuke divorce temple, with counts, quoted from Ueno Kazuo et al., *Namae to shakai* (Waseda UP 2006) | 81 / 81 | exact years not given (temple records run Edo-wide, mostly 18th-19th c.); commoner women of the Kanto; counts recorded in `frequency` as n/112 |
| `kishimoto-rare-edo` | https://www.kishimotoyoshinobu.com/l/いゑのよを型の女性名前/ | same author; 21 Edo commoner names that had died out by Meiji, plus the 6 "overwhelmingly common" types | 27 / 27 | register not named; treat the 21 rare ones (Baka, Bon, Mesu, Yan, Reo, Iro ...) as attested-but-odd, weight low |
| `komonjyo-kinshoji` | https://komonjyo.net/goeika01.html | Komonjyo.net decipherment of a votive plaque at Kinshoji, Chichibu: a women's confraternity roster in kana | 15 / 15 | undated but Edo (page says late Edo style); one name (しゆん = Shun) is a 3-kana reading |
| `uehiro-shimonome` | https://uehiro-tohoku.net/works/2022/4651.html | Tohoku Univ. Uehiro column on the Chiba family takaninzu-aratamecho (Shimonome village, Mutsu, 1829-1837) | 3 / 3 | column, not a full transcription; documents the renaming of a bride on marriage |
| `ndl-crd-horie` | https://crd.ndl.go.jp/reference/entry/index.php?id=1000281025&page=ref_view | NDL reference-cooperative answer citing the Horie family documents (1708) | 4 / 4 | secondary; only the four example names |
| `yoro-shishi` | https://tagizou.com/main/elibrary/pdf/26yoro_history_shiryo2_1.pdf | Yoro town history, shiryo-hen (Mino), text-layer PDF; 1818-1836 deeds and affidavits | 3 / 3 | full register not included; names found by grepping 女房 in 14,898 lines |
| `togetter-owaki` | https://togetter.com/li/2436430 | Togetter thread on Owaki Hidekazu, *Onna no shimei tanjo* (Chikuma 2024): late-Edo names that read as modern (Rin, Ren, Miku, Risa ...) | 15 / 15 | secondhand quotes of a book; useful for R-initials; verify against the book before weighting |
| `jawiki-women-by-era` | https://ja.wikipedia.org/wiki/Category:江戸時代の女性 (+ 安土桃山, 戦国 (日本), 室町, 鎌倉, 平安, 奈良, 飛鳥) | 743 article titles pulled through the MediaWiki API with intro readings; given names extracted by hand. Kept: -hime, o-/於 forms, "no kata"/gozen forms that carry a real given name, surname + given name titles. Dropped: 院号, 尼 names, court titles (局/内侍/式部), pen names (号), place-derived 殿 names, Christian names | 255 / ~200 | mostly samurai and court class, not commoners; Asuka/Nara rows carry `period: unknown` with the era in notes since they predate the schema's bands; a few names are unusual (Uji, Kuso, Jako, Himeyasa) and flagged in notes |

Total: 403 lines, 292 distinct names, 123 names not present in `female-attested.jsonl`.

Rare-initial names (W Z B E G J R U D): 42 distinct, 24 of them new to the corpus - W: Waka, Wakasa, Warabi; Z: none; B: Baka, Ben, Bon; E: Ei, Eiko, En, Etsu; G: Gin, Ginchiyo, Gio, Go; J: Jako, Jo; R: Rei, Ren, Reo, Rie, Rika, Rin, Rina, Rino, Rio, Risa, Riso, Risu, Riyo, Roku, Rui, Rume, Ruri, Ryu; U: Uji, Umashi, Ume, Uta, Utako; D: Dai, Dashi, Den.

## Tried and rejected / failed

- **ADEAC digital archives** (Nagara town 宗門人別改帳 and 五人組帳, Nakatsugawa 宗門改帳, Adachi 宗門人別改帳, Shinshu regional 翻刻, Koshigaya 五人組帳): every page is a JS viewer; the HTML (411 KB) carries no transcription text and there is no public JSON endpoint. Would need a browser session.
- **Kawabe town history, shiryo-hen, 宗門人別改帳 PDF** (kawabe-gifu.jp): 98-page image scan, no text layer. Sampled OCR (tesseract jpn_vert) shows it is the Tochii village 1671 register - the same register nihonjin-name's "Tochii 1671" page tabulates - so it was dropped as already used.
- **Fussa city history, "宗門人別帳からみた村" PDF** (lib.fussa.tokyo.jp): 74-page image scan, OCR'd in full; it is narrative analysis, not a transcription, and OCR surfaced only 3-4 legible names (かや, たけ, きの?). Not included.
- **Niigata archives 古文書講座 第05回, Fukui archives 615718.pdf, Kyoto Kyoiku Univ. museum PDF**: sample register images without transcription text.
- **Saitama archives "戦国時代の仮名文書を読む" PDF**: kana letters to women; no female given names in the text.
- **Fukui prefectural history 中世の女たち page, Yahoo Chiebukuro threads, sengoku-his.com, sheemandzu blog**: names already covered by the Wikipedia pass or were 院号/title forms.
- **oterac.com/jin/swoman**: 22 well-known names, all already in the Wikipedia pass.
- **blog.goo.ne.jp, metal-museum.net, edojidai.info, corontomomousagi.com**: DNS/cert failures or 404.
- **J-STAGE / CiNii / repositories**: searches for 女性名 frequency tables in 宗門改帳 studies returned demographic papers (Nakajima, Hamano) without name tables; the genderhistory paper PDF had no extractable text.
- **Owaki Hidekazu, *Onna no shimei tanjo* (Chikuma 2024)** and **Ueno et al., *Namae to shakai* (2006)**: the two books behind the best secondary quotes here; not online.

## Searches that found nothing usable

"宗門改帳 翻刻 女 名前 一覧 村", "人別帳 女性 名前 一覧 江戸時代 村 翻刻", "過去帳 俗名 女 一覧 江戸時代 翻刻", "五人組帳 翻刻 女房 娘 名前 村", "檀家 女 名 江戸", "子安講 石塔 女性 名前 刻まれ", "女人講 石塔 銘文 女性 名前 翻刻", "奉公人 請状 女 名前 一覧 翻刻 下女", "位牌 戒名 俗名 女性 江戸時代 一覧", "東慶寺 駆込 女性 名前 一覧", "奥女中 一覧 名前 大奥 分限帳", "遊女 名前 一覧 吉原細見 翻刻" (deprioritized: professional names), "中世 女性名 一覧 鎌倉 室町 譲状", "戦国 女性 書状 差出 名前 かな 一覧", "人別帳 データベース 女性 名前 CSV 歴史人口学".
