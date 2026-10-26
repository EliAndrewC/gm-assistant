# Campaign questions and the categories they belong to

Load this file when: a price question comes up at the table, a new kind of thing needs a price, or you are adding rows
or consistency rules.

The GM (2026-10-18): not a list of everything made up front, but each new thing or category researched as it comes up,
and *"these things should make sense relative to each other"*. Each category below has a **recipe** (how to derive a
new item in it) and the **consistency rules** (`webapp/l7r/money/data/rules.jsonl`) that keep it in line with the rest.
Answered prices are a synthesis: source rows may disagree (place, period, debased coin, a different koku) and keep
their reasons, but what the skill answers with satisfies every rule; a note never exempts a row.

Every first answer below is an **estimate** derived from named rows, until the research marked "requested" comes back
([diagram#3](https://github.com/EliAndrewC/diagram/issues/3), [diagram#4](https://github.com/EliAndrewC/diagram/issues/4)).
The yardstick throughout is the unskilled laborer's day, ~13 sen.

## Wages

**Recipe.** One wage sets a floor on another (the GM: *"if you can earn more money doing a different thing that is
unskilled labor ... people will tend to move to the more lucrative profession"*). Unskilled ~13 sen a day is the floor;
a skilled craftsman 17-34 sen (1.3-2.6x the unskilled day: Osaka carpenters ~1.8x their helpers, a village carpenter 2.6x the farm rate, Beijing ~2x; diagram 0275); a household servant is paid less in coin because board and lodging come with the
post. A price made by labor is at least the labor-days in it times the wage. Live-in posts by the year, with board (diagram 0307): a
servant ~3 koku (a samurai house's 1828 contract, 3 ryo 2 bu), a rice-cooking manservant 2.3-2.6, a merchant clerk 2.6-4.7 by
seniority (Mitsui, 160-330 monme), a shop manager up to ~45. A scribe by the day, a guard and a trained cook are unrecorded.
**Rules**: skilled >= unskilled. Every craft good's price >= its labor share.

## Lodging

**Q2. An inn night, room and board, and stabling a horse.**
- Imperial Road inn, supper and breakfast: **8-20 sen** (diagram 0259: a Tokaido *hatago* 120-200 mon, about one
  laborer-day). Cheap lodging, floor space only, bring your own rice and pay for firewood: **2-5 sen** (a *kichin-yado*,
  ~50 mon or less, a fifth of a hatago). Waystations host officials on business, not paying travelers.
- County town: **8-13 sen** (Tsu, 1790: 130 mon). Provincial or capital city: **9-17 sen** (Morisada, 1837-53: Edo ~248 mon with two meals, Kyoto's lesser inns
  200-250 mon, first-class 3 monme 5 bu; diagram 0259), more at a great house's inn by the castle.
- **Mon in sen**: the research quotes mon; convert through the laborer's day (132-200 mon, Kazusa 1842 and Edo), so
  **1 sen is 10-15 mon**. Cross-checked by diagram 0277: on the Osaka market a monme of silver fetched 105-110 mon
  (1787-1854; ~95 in the later 1850s; the law's rate was ~67 from 1700), so Kazusa's 132-mon day is ~1.26 monme, beside
  Kyoto's 0.92-1.08 monme laborer's day. Silver monme convert through the same day (~12 sen a monme in 1851). Edo's own market (Oishi, 1781-1842; diagram 0277) ran ~5,900-6,900 mon a ryo, beside Osaka's.
- Stabling a horse: **12-20 sen** a night - its hay alone is ~10 sen (20 lb at 1 koku a ton), so a horse costs about as
  much to keep as a laborer earns. That is historically right, and why horses mark wealth.

**Recipe**: rice and food at local prices, plus the innkeeper's labor and rent. **Rules**: an inn >= the rice in its
meals and >= cheap lodging; a city inn >= a road inn; stabling >= the horse's feed.

## Transport

**Q6. Hiring a horse, cart and driver for a few days**: **35-55 sen a day** (driver 13-20, feed 10-15, wear and the
owner's profit), and you pay the driver's days home as well. A three-day trip is about 2-3 bu with the return. A
day hire is SILENT (0260). Post stations charged per stage: a pack horse ~27-30 mon a ri in 1665, ~67 with the 1820s
surcharges (**about 4-7 sen a ri**), a porter ~13 mon (**about 1 sen**); private fares ran about twice the official.
**Freight** (goods, not a traveler's hire) ran well under those fares: a tax-rice pack horse beyond 5 ri paid 24 mon a ri
for two bales (0281), and a Qing pack mule comes to ~2 sen a horse-load a ri (Cheng, 0280): **about 1.3-2.4 sen a
horse-load (~120 kg) a ri**. Per 100 kg over 100 km (Cheng, late 1600s): river ~4-5 sen, cart ~17, pack mule ~46, porter
~345; water ran about a tenth of pack carriage. Cheap heavy goods stay home (the Han rule: firewood is not sold beyond
100 li, grain not beyond 1,000; 0281); a costly light good goes far, carriage adding a third (Wuyi tea to Canton, 0283)
and the price 2.5-4x at the far end (brick tea at Lhasa, 0282).
**Recipe**: driver's wage + the animal's keep + wear + return trip. **Rule**: >= driver's wage + horse feed.

## Arrows

**Q1. A good arrow; a hundred; retrieving them.** An ordinary war arrow with a forged iron head: **5-12 sen**; a fine
samurai arrow (selected bamboo, crane or eagle feathers, lacquer): **17-52 sen**; **a hundred war arrows: 7-12 bu**,
55-90 laborer-days - about 8-13% of a Rank 3 samurai's 9-koku stipend (diagram 0263: Qing official prices, 1650-1736;
Japan's are SILENT). Each arrow is half a laborer's day or more: worth picking up after a fight when it is safe, not
worth risking anything for. No source says arrows or heads were gathered after battle; the Qing made every arrow bear
its owner's name and charged soldiers for arms lost outside battle.
**Recipe** (weapons): material + skilled labor-days + the smith's iron; samurai-grade goods add status premium.
**Feathers are a main cost**: the 1727 ruling priced war arrows by their fletching (eagle 8 taels the hundred, goose 5).
**Rule**: fine >= ordinary.
Adjusted 2026-10-19: arrows priced at about half to one laborer-day each, with feathers as a main input, because
calibration showed weapons guesses running 1.56x low (n=3, diagram 0263).

## Posters

**Q3. Wanted posters.** A large sheet of ordinary paper: **1-3 sen**; a poster with ink and paste, written by the PCs:
**2-4 sen**; a set of ten, **2-4 zeni** (a sheet of Qing placard paper was 0.01 tael, ~1-2 sen, diagram 0264; Edo paper
SILENT). Ink is a stick that lasts months. **Paper or a board?** Edo official notices were wooden plaques (cypress, plum
or similar) written in ink with title, text, date and issuing authority, put up by the shogunate or by the lord; re-inking
needed permission (diagram 0190). Paper notices pasted up are attested at one 1857 lost-child pillar, set up with the
town magistrate's leave. A magistrate's wanted notice would be a plaque; PCs pasting paper would need leave. What was
posted on a village board, and whether anyone but the lord could post: SILENT.
**Recipe** (paper and writing): paper by sheet and quality; labor of a calligrapher if hired (a skilled day writes many).
**Rule**: a poster >= its paper.

## Apples

**Q4. Apples in season from a cart**: **2-6 sen for three** (about 1-2 sen an apple). No Japanese apple price survives
(diagram 0272); a persimmon cost 6 mon in Kanto villages (~0.5 sen, so two for a sen), and the Qing court paid nearly
four times as much for an apple as for a persimmon. Dearer out of season or in a capital. Japan's native apples were
small and scarce; persimmons, pears and citrus were the common fruit.
**Recipe** (food): staple rice at ~1 sen a meal is the anchor; fresh produce in season is cheap, prepared food adds
labor; anything carried far or out of season costs more.

## Offerings

**Q5. Otsuki's salt bag** (undyed hemp, lined with shrine paper, filled with salt): **3-5 sen** - a cup of salt 1
(0.5-0.9 sen at inland prices, 4-7 sen a sho; diagram 0273; the Imperial salt monopoly keeps salt above its cost), a small hemp bag 1-2, a sheet of shrine paper about 1, often
given rather than sold (no price for hemp by the *tan* or for one amulet survives, diagram 0274: an Ise priest's 1813 round
took ~0.02 ryo a household for the talisman, the calendar and gifts together). He is out about a third of a laborer's day per bag: nothing to a monk with a temple behind him
for one, real money if he hands out dozens.
**Recipe** (religious goods): materials and labor, plus a donation that is customary rather than priced.
**Rule**: the bag >= its salt, bag and paper.

## Rentals

**Q7. A remote riverside warehouse, empty, off season, for a week**: **10-30 sen** (a storehouse worth 10-30 koku
letting at 3-6% a year; remote and off season, the low end; a short let carries a premium. Storehouses were let in
Edo, rate SILENT).
**Q12. Renting in a domain capital** (research requested: Edo row-house rents, townhouse and estate rents):
- One room in a tenement: **20-60 sen a month** (Edo back tenements 300-600 mon a month, diagram 0265, from a popular
  page; the GM notes give 2 bu per tenant for really poor housing).
- A small standalone house: **1-2 bu a month** (an Edo carpenter's household paid 10 monme a month, ~1.2-1.4 bu).
- A modest city estate, walled, several rooms and a garden: **4-17 bu a month** (5-20 koku a year).
- Household staff separately: a menial servant ~0.7-1 koku a year plus board, a steward ~3 koku (Kanazawa rows).
**Recipe** (land and buildings): rent is **3-6% of a property's value a year** (Edo lots, 0265; Mitsui ~4.8% gross,
~2.4% net of the rebuilding fund). Adjusted 2026-10-19 from 8-12%, because 0265 attests 3-6%; sale price against rent against yield
(diagram#1 Q1). **Rules**: estate >= small house >= room.

## Clothing

**Q8. Ten plain kimono for low-to-mid ranking samurai**, simply dyed in clan colors, no mon or embroidery:
- Cotton, the cloth alone: **65-145 sen a kimono** - one *tan* (~36 cm by ~10 m) cost 4-9 monme of silver in Ako,
  1781-90, 5-11 laborer-days (diagram 0261). Dyed and sewn: **110-290 sen**. **Ten: 1.1-2.9 koku.** (The first answer,
  3.5-4.5 koku, used Bassino and Ma's Osaka 1840s cloth price, 2-5x Ako's.)
- Plain silk, as a mid-rank samurai would wear: **4.5-10.5 bu each; ten: 4.5-10.5 koku.** Silk ran ~3-7x cotton; the
  one Japanese price is from fiction (habutae 45 monme a tan, 1692).
- Against a Rank 3 stipend of 9 koku, ten cotton kimono are two to four months of it: clothing is expensive, as the GM
  remembers. Most commoners and poor samurai bought used clothes (used clothing and tailoring: SILENT).

**Q9. Silk sheets**: **0.85-2 koku a set** (about two kimono lengths of silk). Worth a thief's trouble and a magistrate's
attention.
**Recipe** (cloth and clothing): fiber -> cloth by the *tan* -> dyeing -> sewing. Silk is several times cotton; hemp
below cotton. **Rules**: a kimono >= its cloth (the GM's example); silk >= cotton; sheets >= their silk.

## Drink

**Q10. Sake.** Ordinary sake from a brewer or shop: **1-3 sen a cup** (one *go*, 180 ml; diagram 0262: Kazusa 1842,
100 mon a sho of local sake against a man's day of 132 mon); in a tavern, warmed: **2-4 sen** (Edo 8-24 mon, a soba shop
40); a flask of two or three cups, **5-10 sen**; good sake 2-3x. A night for six with snacks, ~15-20 cups: **4-8
zeni**. The tavern markup is ~1.5-2x, not a modern bar's 4-5x, because labor and rent are cheap (Japan's markup is
SILENT; Qing bought wine ran ~2x home-brew).
**Recipe**: retail price + the tavern's labor, warming and rent. **Rules**: tavern >= retail; an evening >= its cups.

## Entertainment

**Q11. Seeing a play, and other entertainers.** First answers by venue:
- Peasants, street or temple-front performers: watch free, **a sen or a handful of rice** in the hat. Temple-fair
  performances were often fund-raising for the temple (*kanjin*).
- County township: a festival play was mostly the village's own young men, at the shrine festival, a rain prayer or Bon;
  a bought-in local troupe cost **~1.7-3.3 koku** for three days (a Kaifeng village troupe; 0266), free to watch. A big
  troupe for a market town's festival took far more (Hamanoichi, 1690-1737: tens of koku a run, 43 players).
- Provincial or capital playhouse: one act from the back **1-2 sen**, a pit place **9-13 sen** (about a laborer's day),
  a box **5-7 zeni** a head, about 5-12 zeni with the teahouse's food (Edo kabuki 1801-04: 16 mon, 132 mon, 25-35 monme a
  box of seven; diagram 0266). Sumo was priced like the theater. A private performance for a lord: koku.
- Troupes: in Tokugawa Japan, kabuki and noh troupes were actors and their own musicians; jugglers, acrobats,
  storytellers and performing animals were separate street acts, gathered in variety shows at temple fairs. The mixed
  traveling troupe is an L5R convention as much as a historical one (research requested). The "pass the hat before the
  ending" story about Shakespeare-era players is NOT ATTESTED (diagram 0267, comparative): money was taken at the door, even while the play went on (Norwich 1583), a penny to stand, another to sit, a third for a cushion (Platter 1599); what went round mid-play was food and drink for sale.
- Other entertainers: street acts (jugglers, acrobats, storytellers, performing monkeys) are paid like street plays,
  a sen or less a head into the hat; a musician hired for a party or a banquet, **1-3 zeni** for an evening plus food;
  a well-known performer for a lord's banquet, bu to koku.
**Recipe**: who pays (the audience, a patron, a temple, the village) decides the price more than the act does. Price a
seat in laborer-days: one act ~0.1, the pit ~1, a box ~4-5 a head. Troupes were actors with their own or the theater's
musicians (kabuki troupes ~43 players, puppet troupes ~26); acrobats formed their own troupes.
Adjusted 2026-10-25: a performer's pay scales with the house's takings, and those with its city: Edo's stars took
700-1,000 ryo (diagram 0308), so a domain capital of ~12,000 pays its star about a hundredth of that, ~8-11 koku, not a
flat guess; touring troupes were hired by the visit (Shima, 18-20 players, ~2-4 ryo with board). Because calibration
showed entertainment's typical miss at 3.23x (n=6): the star actor had been guessed at 20-100 koku without a scale.
Adjusted 2026-10-19: city seats priced against the laborer's day, because calibration showed entertainment guesses
running 1.98x high (n=5, typical miss 3.2x; diagram 0266) - the first answers priced the theater as a samurai luxury.
**Rules**: box >= pit >= standing.

## Construction

**Shrines** (the shrine builder, feature 216; Shizu's memorial hermitage for Shoda, 2026-10-18). The builder prices at
1 ryo = 1 koku from Tama-district village ledgers (AIJ paper No. 420), which agrees with this skill's wages: a
craftsman at ~1 koku per 30-40 days is 25-33 sen a day, inside the skilled range, and carpenters at 2.6-4.7x the
unskilled wage (diagram 0250). Its first, hand-set prices (E0035-E0051) were withdrawn - they were not this
model's - and the whole catalog was re-estimated with this recipe on 2026-10-18 (`shrine catalog ...` estimates; the
builder's prices are the midpoints of the ledger's `shrine/...` synthesis rows that began as those estimates, enforced by a test; research moves the rows, never the estimates). Shizu's design: 60 koku before, ~25 after (foot trail), ~30 once diagram 0255 re-priced the sanctuary, ~31 once 0269 raised the site line (2026-10-19).
Research: [diagram#6](https://github.com/EliAndrewC/diagram/issues/6) (her lines, priority),
[#7](https://github.com/EliAndrewC/diagram/issues/7) (the rest). A LOAD of porterage is ~400 kg, ten porter trips.
**Recipe**: craftsman-days x the skilled day + materials + workers' rice + rites, scaled from the nearest ledger;
roof work scales with roof AREA (the square of the bay), not the bay's width; stone and earth add porter loads at the
remoteness rate. **Check every line in labor-days**: a line that buys more craftsman-days than the work could take is
too high, whatever its ledger ancestry. Diagram 0255 (2026-10-19) settled the
small sanctuary: a new 6-shaku decorated one cost over 30 ryo in 1841 (~2,000 laborer-days), so a 4.2-shaku plain one is
12.7-18.2 koku (~300-770 craftsman-days), up from the first estimate's 4.9-16.2; the other forms moved in proportion.
0256-0258 found no price for the bark roof, tannin, wooden torii, stone posts, stepping stones, mound, the monk's
dedication, the ground rite or the furnishings, so those stay as estimated. A parent shrine's installation fee
(Fushimi Inari, 0258) is not a monk's dedication. Diagram 0268-0271 (2026-10-19): a pair of stone lanterns 4 ryo 3 bu
(~4 koku), a village worship hall 11 ryo 2 bu to its carpenter (scaled like the sanctuary, ~5.85 for the pavilion),
relief panels 3 ryo each, base stones at least ~2 ryo 2 bu for a 6-shaku sanctuary (the site line now 1.5-2.6). A ryo is
~0.85 koku through the laborer's day (60 monme, 0.92 monme a day). Every other form, finish, metal furnishing and rite:
SILENT.
Diagram#10 (feature 408, 2026-10-21) asked the 48 small lines: Japan is SILENT or has only a nearest figure for all
but the swept path (a 1704 road-sweeping crew, 7 laborer-days, inside 39-160 sen), so no shrine price moved. A
woodcarver earned 3.6 monme a day, 1.4-2.4x a carpenter (row `wage-carver-day`, 45-80 sen). The Qing porter rates
(0278) bracket the trail's 10 porter-days a load, so porterage stands.

## Tools

**Q13. A set of chef's knives given to a peasant cook out of respect for the craft** (GM 2026-10-19). An ordinary
kitchen knife: **10-45 sen** (Edo's knife wholesalers, 1851: a vegetable knife, a deba or a low-grade blade 0.7-2.75
monme of silver, 8-33 sen, before a shop's margin; diagram 0276). A fine knife, the top grade, laminated and polished:
**1.7-3 bu** (top-grade thin-bladed and sashimi knives 14-19 monme wholesale, 170-230 sen). A set of three fine ones
(fish, vegetable, slicing): **5-9 bu**, 40-70 laborer-days - months of a cook's wages, so the cook could never have
bought it, and a samurai's gift at the scale of *consideration* (bu). An ordinary set: 0.3-1.4 bu. No price by a noted
maker (Sakai, Seki, Takefu, Tosa) survives.
**Recipe** (worked metal): smith-days at the skilled rate + iron and steel + grinding and polish; a maker's name adds a
premium. **Rules**: a knife >= half a skilled day; fine >= ordinary and >= two skilled days; a set >= its knives.
Adjusted 2026-10-25: a plain farm tool is priced from its iron and a short forging, not from the kitchen knife; its iron
is about a quarter of its price (a Beijing sickle 0.07 tael, ~10 sen, against 0.0225-0.027 tael a jin of iron; diagram
0306), and in the itinerant smith's trade the farmer brought the charcoal. Because calibration showed tools guesses
running 1.68x high (n=4, typical miss 1.89x): the sickle had been priced like a knife, 15-35 sen against ~10.

## Fuel

**Q14. Charcoal, ordinary and shrine-grade** (GM 2026-10-21; estimates E0159-E0166; diagram 0279, feature 410).

| | small bag (~1 kg) | 10 lb | bale (~15 kg) | ox-cart (~500 kg, wholesale) |
|---|---|---|---|---|
| ordinary black | 1-2 sen | 5-8 sen | 1.5-2 zeni (1.1-1.6 laborer-days) | 4.5-7 bu |
| Fox white, near the kilns | 2-5 sen | 1.1-2 zeni | 3.5-6 zeni | 1.1-1.9 koku |
| Fox white, neighboring clans (Kakita, Etsuko) | 5 sen-1 zeni | 2-4 zeni | 6 zeni-1.1 bu | 2-3.5 koku |
| Fox white, Ryoko Owari (~205 ri overland) | 1-3 zeni | 4 zeni-1.2 bu | 1.1-3.2 bu (6-18x black) | not carried |

Black rests on Edo's 1842 bale prices (342-466 mon by grade) and Beijing's 1736 official list, which agree on a bale at
1.1-1.6 laborer-days. Shrine-grade is 2-3x black: generic white ran ~2x black (Beijing), a famous white (Kumano, 1716)
2.2-2.5x a local white; no Japanese black-against-white price survives. First guesses ran high (white 3-4x).
Fox white is the Kumano of Rokugan (a famous white from a special oak, sold far away): in neighboring clans ~4-6x
local black, as Kumano in Edo; carriage is ~0.15-0.3 sen a bale a ri by pack horse (Transport, freight), plus a 15%
tariff per border and a merchant's margin, so at Ryoko Owari (~205 ri overland) a bale is 1.1-3.2 bu, 3-5x the kiln price. Ordinary charcoal is burned locally
everywhere; only a temple's few bales travel that far (GM 2026-10-22; E0167-E0168, asked in diagram#12).
A household brazier burns about a small bag a day or two; a bale lasts it two to four weeks of winter.
A cartload of white charcoal is paid in gold by a merchant or a great shrine (the Fox Road footpads took one).
**Canon**: shrine-grade white charcoal is a Fox Clan specialty from sacred oak under the Fox Ministry of Rites (ordinary
charcoal under Revenue), odorless and nearly smokeless, at a premium throughout the Empire and worth counterfeiting
(l7r.md, "The Fox Clan's economy"; the Kitsune Denhei bounty). Near Fox kilns, less; far away, add carriage.
**Recipe** (black): laborer-days for cutting, a 3-5 day burn and baling (~0.6-1.1 a bale, the wood ~5x the charcoal's
weight) + a day's carriage to town (3-7 sen a bale) + a dealer's 1.2-1.5x. **White**: a stone kiln gives about a tenth of an
earth kiln's bales a firing (0279), sold at 2-3x. A cartload is 33 bales at the kiln price plus cart hire, no shop
margin. **Rules**: white >= 2x black by the bale; 10 lb >= a quarter bale; a cartload >= 20 bales; a bale >= 0.6
laborer-days.
Adjusted 2026-10-22: the white premium cut from 3-4x to 2-3x black, and black's dealer margin read as the low end, because
calibration showed "other: n=8, guesses run 1.57x high" (all eight are the charcoal estimates; white ran 2.2-2.6x high,
black 1.3-1.6x high except the cartload, 0.76x).
Adjusted 2026-10-22: long-haul carriage cut from 0.5-1 to 0.15-0.3 sen a bale a ri and the Ryoko Owari tier from 2.5-6
bu to 1.1-3.2 bu a bale, because diagram 0280-0283 (feature 411) gave freight rates (tax rice 24 mon a horse-load a ri,
Qing mule ~2 sen) a third to a sixth of the post-station fares the guess used; E0167-E0168 themselves are SILENT.
