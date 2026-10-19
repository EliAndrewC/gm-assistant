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
- Imperial Road inn, supper and breakfast: **7-13 sen** (half to one laborer-day; the Edo post-town *hatago* pattern,
  research requested). Cheap lodging, floor space only, bring your own rice and pay for firewood: **2-3 sen**.
  Waystations host officials on business, not paying travelers.
- County town: **7-15 sen**. Provincial or capital city: **10-25 sen**, more at a good inn by the castle or a temple
  district.
- Stabling a horse: **12-20 sen** a night - its hay alone is ~10 sen (20 lb at 1 koku a ton), so a horse costs about as
  much to keep as a laborer earns. That is historically right, and why horses mark wealth.

**Recipe**: rice and food at local prices, plus the innkeeper's labor and rent. **Rules**: an inn >= the rice in its
meals and >= cheap lodging; a city inn >= a road inn; stabling >= the horse's feed.

## Transport

**Q6. Hiring a horse, cart and driver for a few days**: **35-55 sen a day** (driver 13-20, feed 10-15, wear and the
owner's profit), and you pay the driver's days home as well. A three-day trip is about 2-3 bu with the return. Edo
post stations set fixed per-ri rates for pack horses and porters (research requested).
**Recipe**: driver's wage + the animal's keep + wear + return trip. **Rule**: >= driver's wage + horse feed.

## Arrows

**Q1. A good arrow; a hundred; retrieving them.** An ordinary war arrow with a forged iron head: **4-8 sen** (bamboo and
feathers 1-2, the head 1-3, a fletcher making ~10 a day). A fine samurai arrow (selected bamboo, hawk or eagle feathers,
lacquer): **10-30 sen**. **A hundred war arrows: 4-8 bu**, 30-60 laborer-days - about 5-9% of a Rank 3 samurai's
9-koku stipend. Not a fraction of a samurai's net worth, but each arrow is a third to two-thirds of a laborer's day:
worth picking up after a fight when it is safe, not worth risking anything for. Heads were often recovered and reshafted
(research requested: Japanese and Chinese arrow prices, arrowhead forging).
**Recipe** (weapons): material + skilled labor-days + the smith's iron; samurai-grade goods add status premium.
**Rule**: fine >= ordinary.

## Posters

**Q3. Wanted posters.** A large sheet of ordinary paper: **1-3 sen**; a poster with ink and paste, written by the PCs:
**2-4 sen**; a set of ten, **2-4 zeni**. Ink is a stick that lasts months. **Paper or a board?** In Tokugawa Japan the official notice boards
(*kosatsu*) carried edicts written in ink on wooden plaques, put up by authority; private and temporary notices were
paper pasted up. A wanted poster put up by magistrates could plausibly be either. Drawing straight onto an outdoor board was not the practice for anything meant to last: rain
runs ink, so writing went on paper or on a plaque made for the purpose. Village boards and what was posted on
them: research requested.
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

**Q7. A remote riverside warehouse, empty, off season, for a week**: **20-60 sen** (a storehouse worth 10-30 koku
letting at ~10% a year is 2-6 zeni a week; remote and off season, the low end; a short let carries a premium).
**Q12. Renting in a domain capital** (research requested: Edo row-house rents, townhouse and estate rents):
- One room in a tenement: **15-40 sen a month** (Edo *nagaya* pattern: a month's rent for one or two laborer-days; the GM
  notes give 2 bu per tenant for really poor housing).
- A small standalone house: **50-150 sen a month**.
- A modest city estate, walled, several rooms and a garden: **4-17 bu a month** (5-20 koku a year).
- Household staff separately: a menial servant ~0.7-1 koku a year plus board, a steward ~3 koku (Kanazawa rows).
**Recipe** (land and buildings): rent is ~8-12% of a building's value a year; sale price against rent against yield
(diagram#1 Q1). **Rules**: estate >= small house >= room.

## Clothing

**Q8. Ten plain kimono for low-to-mid ranking samurai**, simply dyed in clan colors, no mon or embroidery:
- Cotton, the cloth alone: **~3 bu a kimono** - from our own basket: Kyoto cotton cloth at 5.83 g silver a meter is
  ~26 sen, and a kimono takes one *tan*, ~12 m of narrow cloth. Dyed and sewn: **3.5-4.5 bu**. **Ten: 3.5-4.5 koku.**
- Plain silk or pongee, as a mid-rank samurai would wear: **1.3-3.3 koku each; ten: 13-33 koku.**
- Against a Rank 3 stipend of 9 koku, ten cotton kimono are five months of it: clothing is expensive, as the GM
  remembers. Most commoners and poor samurai bought used clothes (research requested: cloth by the *tan*, new and used
  kimono, tailoring).

**Q9. Silk sheets**: **2.5-6 koku a set** (about two kimono lengths of silk). Worth a thief's trouble and a magistrate's
attention.
**Recipe** (cloth and clothing): fiber -> cloth by the *tan* -> dyeing -> sewing. Silk is several times cotton; hemp
below cotton. **Rules**: a kimono >= its cloth (the GM's example); silk >= cotton; sheets >= their silk.

## Drink

**Q10. Sake.** Ordinary sake from a brewer or shop: **1-2 sen a cup** (one *go*, 180 ml); in a tavern, warmed: **2-4
sen**; a flask of two or three cups, **5-10 sen**; good sake 2-3x. A night for six with snacks, ~15-20 cups: **4-8
zeni**. The tavern markup is ~1.5-2x, not a modern bar's 4-5x, because labor and rent are cheap (research requested:
Edo sake prices retail and in taverns).
**Recipe**: retail price + the tavern's labor, warming and rent. **Rules**: tavern >= retail; an evening >= its cups.

## Entertainment

**Q11. Seeing a play, and other entertainers.** First answers by venue:
- Peasants, street or temple-front performers: watch free, **a sen or a handful of rice** in the hat. Temple-fair
  performances were often fund-raising for the temple (*kanjin*).
- County township: a festival play is usually paid for by the village or a patron (**1-3 koku** a run, guess) and free to
  watch.
- Provincial or capital playhouse: a standing place for one act **3-8 sen**, a pit place **2-5 zeni**, a box for the
  day with food **1-3 bu** a head. A private performance for a lord: koku.
- Troupes: in Tokugawa Japan, kabuki and noh troupes were actors and their own musicians; jugglers, acrobats,
  storytellers and performing animals were separate street acts, gathered in variety shows at temple fairs. The mixed
  traveling troupe is an L5R convention as much as a historical one (research requested). The "pass the hat before the
  ending" story about Shakespeare-era players is doubtful as stated; research requested as a comparative footnote only.
- Other entertainers: street acts (jugglers, acrobats, storytellers, performing monkeys) are paid like street plays,
  a sen or less a head into the hat; a musician hired for a party or a banquet, **1-3 zeni** for an evening plus food;
  a well-known performer for a lord's banquet, bu to koku.
**Recipe**: who pays (the audience, a patron, a temple, the village) decides the price more than the act does.
**Rules**: box >= pit >= standing.
