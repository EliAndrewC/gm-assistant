# Campaign questions and the categories they belong to

Load this file when: a price question comes up at the table, a new kind of thing needs a price, or you are adding rows
or consistency rules.

The GM (2026-10-18): not a list of everything made up front, but each new thing or category researched as it comes up,
and *"these things should make sense relative to each other"*. Each category below has a **recipe** (how to derive a
new item in it) and the **consistency rules** (`webapp/l7r/money/data/rules.jsonl`) that keep it in line with the rest.
Answered prices are a synthesis: source rows may disagree (place, period, debased coin, a different koku) and keep
their reasons, but what the skill answers with satisfies every rule; a note never exempts a row.

Every first answer below is a **guess** derived from named rows, until the research marked "requested" comes back
([diagram#3](https://github.com/EliAndrewC/diagram/issues/3), [diagram#4](https://github.com/EliAndrewC/diagram/issues/4)).
The yardstick throughout is the unskilled laborer's day, ~13 sen.

## Wages

**Recipe.** One wage sets a floor on another (the GM: *"if you can earn more money doing a different thing that is
unskilled labor ... people will tend to move to the more lucrative profession"*). Unskilled ~13 sen a day is the floor;
a skilled craftsman 20-40 sen (1.5-3x); a household servant is paid less in coin because board and lodging come with the
post. A price made by labor is at least the labor-days in it times the wage.
**Rules**: skilled >= unskilled. Every craft good's price >= its labor share.

## Lodging

**Q2. An inn night, room and board, and stabling a horse.**
- Imperial Road inn, supper and breakfast: **8-20 sen** (diagram 0259: a Tokaido *hatago* 120-200 mon, about one
  laborer-day). Cheap lodging, floor space only, bring your own rice and pay for firewood: **2-5 sen** (a *kichin-yado*,
  ~50 mon or less, a fifth of a hatago). Waystations host officials on business, not paying travelers.
- County town: **8-13 sen** (Tsu, 1790: 130 mon). Provincial or capital city: **10-25 sen**, more at a good inn by the
  castle or a temple district (a big-city price is SILENT).
- **Mon in sen**: the research quotes mon; convert through the laborer's day (132-200 mon, Kazusa 1842 and Edo), so
  **1 sen is 10-15 mon**.
- Stabling a horse: **12-20 sen** a night - its hay alone is ~10 sen (20 lb at 1 koku a ton), so a horse costs about as
  much to keep as a laborer earns. That is historically right, and why horses mark wealth.

**Recipe**: rice and food at local prices, plus the innkeeper's labor and rent. **Rules**: an inn >= the rice in its
meals and >= cheap lodging; a city inn >= a road inn; stabling >= the horse's feed.

## Transport

**Q6. Hiring a horse, cart and driver for a few days**: **35-55 sen a day** (driver 13-20, feed 10-15, wear and the
owner's profit), and you pay the driver's days home as well. A three-day trip is about 2-3 bu with the return. A
day hire is SILENT (0260). Post stations charged per stage: a pack horse ~27-30 mon a ri in 1665, ~67 with the 1820s
surcharges (**about 4-7 sen a ri**), a porter ~13 mon (**about 1 sen**); private fares ran about twice the official.
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

**Q4. Apples in season from a cart**: **about 1 sen for two to four** (an Apple Cart Donut costs less than a bowl of
rice). Dearer out of season or in a capital. Japan's native apples were small; persimmons, pears and citrus were the
common fruit (research requested: fruit prices).
**Recipe** (food): staple rice at ~1 sen a meal is the anchor; fresh produce in season is cheap, prepared food adds
labor; anything carried far or out of season costs more.

## Offerings

**Q5. Otsuki's salt bag** (undyed hemp, lined with shrine paper, filled with salt): **3-5 sen** - a cup of salt 1-2
(the Imperial salt monopoly keeps salt above its cost), a small hemp bag 1-2, a sheet of shrine paper about 1, often
given rather than sold. He is out about a third of a laborer's day per bag: nothing to a monk with a temple behind him
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
Adjusted 2026-10-19: city seats priced against the laborer's day, because calibration showed entertainment guesses
running 1.98x high (n=5, typical miss 3.2x; diagram 0266) - the first answers priced the theater as a samurai luxury.
**Rules**: box >= pit >= standing.

## Construction

**Shrines** (the shrine builder, feature 216; Shizu's memorial hermitage for Shoda, 2026-10-18). The builder prices at
1 ryo = 1 koku from Tama-district village ledgers (AIJ paper No. 420), which agrees with this skill's wages: a
craftsman at ~1 koku per 30-40 days is 25-33 sen a day, inside the skilled range, and carpenters at 2.6-4.7x the
unskilled wage (diagram 0250). Its first, hand-set prices (E0035-E0051) were withdrawn - they were not this
model's - and the whole catalog was re-estimated with this recipe on 2026-10-18 (`shrine catalog ...` estimates; the
builder's prices are the midpoints of the ledger's `shrine/...` synthesis rows that began as those estimates, enforced by a test; research moves the rows, never the estimates). Shizu's design: 60 koku before, ~25 after (foot trail), ~30 once diagram 0255 re-priced the sanctuary (2026-10-19).
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
(Fushimi Inari, 0258) is not a monk's dedication.

## Tools

**Q13. A set of chef's knives given to a peasant cook out of respect for the craft** (GM 2026-10-19). An ordinary
kitchen knife: **15-40 sen** (half a day to a day of a country smith with a helper, plus a little iron and steel and the
grinding; below a cheap blade weapon). A fine knife by a noted smith, laminated and polished: **8 zeni-2 bu**. A set of
three fine ones (fish, vegetable, slicing): **2.5-6 bu**, 19-45 laborer-days - months of a cook's wages, so the cook
could never have bought it, and a samurai's gift at the scale of *consideration* (bu). An ordinary set: 0.5-1.2 bu.
Edo Japan's knife towns (Sakai above all) sold kitchen knives by the maker's name (research requested).
**Recipe** (worked metal): smith-days at the skilled rate + iron and steel + grinding and polish; a maker's name adds a
premium. **Rules**: a knife >= half a skilled day; fine >= ordinary and >= two skilled days; a set >= its knives.
