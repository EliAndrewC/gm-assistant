# Female attested names, pass 5 - sources, yields, dead ends

Target initials: A B D E F G I J R U W Z. Names within one edit of any held name were dropped
at build time (Levenshtein <= 1 against the whole held list, not just the same initial), which is
why common finds such as Ei (Ebi), Iku (Ikue), Fusa (Zusa), Fuyu (Fuku), Uno (Ino), Iyo (Riyo),
Inoko (Itoko), Ichi (Ishi) do not appear in the JSONL even though they were attested.

## Sources that worked

| id | what it is | yield (after the distance filter) |
|---|---|---|
| Nishinomiya-kobunsho-han 2014 | Nishinomiya City Local History Museum document-reading team blog, one post per kana row (`?p=1123` a, `1193` ka, `1194` sa, `1275` ta, `1276` na, `1277` ha, `1308` ma, `1309` ya, `1310` ra, `1311` wa). Names picked "at random" from Edo documents they read in 2014; no per-name year. Found by probing post ids 1194-1308 | En, Fuchi, Iwa, Raku, Riku, Rei, Waki (+ Ei, Fusa, Fuyu, Iku, Isa, Itsu, Iyo, Uno filtered) |
| Kawabe-cho-shi shiryo-hen vol.1 ch.8 | 98-page scanned PDF of the printed transcription of the 1671 shumon aratamecho of Tochii and neighbouring villages, Kamo district, Mino. pdftotext gives nothing; OCR with tesseract `jpn_vert --psm 5` at 200 dpi (about 8 min for the file) is good enough to read `<kana> 年 <age>` runs | Iya (+ Fuu, Ichi, Inoko filtered). Non-target names visible: kuni, tori, take, sute, kochiyo, muyau, tatsu, tsuki, kame, san, tsuru, mume |
| Nakatsugawa-shi-shi (ADEAC) | city-history chapter on the Kyoho 2 (1717) shumon-cho of Yufunezawa village, with the full female name table and counts | Iyo, Fuu (both filtered); non-target: ama, kame x8; oto, kuni, haru, hana x4 etc. |
| Kishimoto Yoshinobu, Edo-Meiji josei-mei | 112 women's names from Tokuman-ji temple records, Ota, Kozuke | Ise (+ Ei, Fusa, Iku, Ichi, Riso, Ume filtered/kept) |
| Kishimoto Yoshinobu, ie-no-yo-wo-gata | author's list of late-Edo names that "appeared and vanished" - no document cited, weakest attestation here | Bon, Rewo (+ Risu, Baka filtered) |
| komonjyo.net Kinsho-ji hengaku | women's ko donor plaque, Chichibu | Roku (+ Iro filtered) |
| NDL reference DB 1000281025 | librarian answer quoting 1708 Horie documents and an 1837-1865 ninbetsucho survey | Etsu (+ Fuyo filtered) |
| nihonjin-name jimdo | 1564 Sugaura shussen nikki women (nare, chiyachi, tsuru, inoko, kuri, tonari, shiyute, nana, nara, saru, tsuitachi, yome) and 1671 Tochii ko-prefixed names | Inoko (filtered) |
| ja.wikipedia | named historical women, used only where the given name itself is attested (not a court title) | Ahe, Abe, Asahara, Anahobe, Abutsu, Ashobu, Dai, Den, Eshin, Go (x2), Ginchiyo, Iitoyo, Iga, Ikumatsu, Jukei, Reijo, Rengetsu, Ryoko, Ume, Utako (filtered) |

## Sources that failed or were dead

- Akiruno-shi "kyodo no komonjo" PDFs 12/13 (hokonin ukejo, ribetsujo): real transcriptions but the women are Tome and Nami - not target initials.
- Niigata prefectural library online komonjo lecture 09 (rienjo): one woman, Okin.
- Nerima-ku-shi koshinto section: five women on a 1674 tower (o-Tan, o-Tatsu, o-Tane, o-Susu, o-Masa) and three on a 1667 one (o-Tami, o-Hino, o-Sen). Real koshinto female names, none in target initials.
- Kiyose-shi "Edo jidai no onamae" blog: the 76+53-name lists are images; only the top-frequency names are in text (matsu, san, tsuru, tan, ine, kin, sayo, kane, kaya, kiyo, aki, iku, miyo, kichi, sute, ume, saki). Aki and Iku filtered.
- Uehiro-Tohoku column on the Chiba family takaninzu-cho: Sato, Shimo, Rin only.
- Fussa city history vol.7 ch.1 (shumon ninbetsucho): 18 MB scanned PDF, no text layer; not OCR'd (would need the same tesseract pass as Kawabe - worth doing on a later pass, the chapter analyses female names).
- Keio kobunsho-shitsu 2013 exhibition (Hoshido village 1792 ninbetsucho) and Nagara-town / Joso-city ADEAC shumon-cho pages: viewer-only, no text reachable.
- Fukui archives shumon-cho PDF: one girl, Mina.
- Gender-history journal paper on oohime/otohime (J-STAGE): medieval naming analysis; only Ako-me and Oto-me as name forms.
- Searches that returned nothing usable: 鐘銘 女 寄進 翻刻; 庚申塔 銘文 女 名 施主 (municipal koshinto pages list male names only); 念仏講 女 名簿 翻刻; 供養塔 施主 女 翻刻; 絵馬 奉納 女 名前 翻刻; 過去帳 翻刻 俗名 女; 墓石 俗名 女 刻銘 調査; 吉原細見 遊女名 (only stage-name lineages such as Usugumo/Agemaki, not taken); 飯盛女 名前 翻刻; every per-name probe for ぎく/ごん/げん/じゅん/ぜん/ぼん/だい/でん/うら/うし (the search engine returns generic pages for two-kana names).
- Z: nothing attested found beyond the held set. The Kishimoto and Nishinomiya lists have no za-row names at all; Z-initial female names appear to be genuinely rare before 1868.
- J: only Jukei (nun name). No commoner じ/じゅ names surfaced in any register read.
