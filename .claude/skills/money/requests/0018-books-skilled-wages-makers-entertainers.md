**Money research: books, skilled wages, a smith's income, and entertainers' incomes and gear**

Questions from the gm-assistant money skill, asked by the GM (2026-10-25), verbatim:

> Do we know what books cost? To buy? To transcribe?
>
> We have some sense of the cost of unskilled labor, but what about different kinds of skilled labor? Like a clerk who
> was literate? What about a caravan guard who carried a weapon? A skilled servant such as a chef or a ladies maid?
>
> We've come up with the sales prices of various finished goods, but do we have a sense of how much income their
> creators made in a year? I'm guessing we have a price list demonstrating the prices of various items like various
> metalworked goods - but do we know the smith's costs of inputs and thus their profit from each sale? Or how many such
> sales he made in a year and thus his gross revenue?
>
> How much money might an entertainer make? An entire acting troupe? How large would such a troupe be? How expensive
> would their supplies be, like their costumes or their musical instruments?

The skill's guesses are logged as estimates E0169-E0193 (`webapp/l7r/money/data/estimates.jsonl` in gm-assistant), made
before this research so they can be graded against it. Anchors: the Kyoto unskilled day 13 sen (0250; a koku = 1,000
sen), a skilled day 17-34 sen (0275), the kitchen knife (0276), plays (0266).

### 1. Books: buying one, borrowing one, having one copied
- **Question**: in Tokugawa Japan (and Ming/Qing China beside it), what did a printed book cost: a cheap popular booklet,
  and one bound volume of an ordinary classic, primer or reference work? What did a lending library charge a loan? What
  did a copyist charge to copy a book by hand (per leaf, per volume, or a day's pay), and how many leaves a day did one
  write?
- **Figure needed**: silver or copper per booklet, per volume (with its leaf count), per loan, per copied leaf; a
  copyist's leaves a day and day's pay.
- **Canon beside it**: `l7r.md` lists scribes among the heimen professions; no price.
- **Region order**: Japan first, China beside it.

### 2. Skilled and trusted labor
- **Question**: what were the wages of (a) a literate clerk: a merchant house's live-in clerk (tedai, banto) by
  seniority, and a scribe hired by the day; (b) an armed guard for goods on the road: Japanese escorts of goods or cash,
  or China's escort agencies (biaoju), per day or per trip; (c) skilled servants: a household cook, a lord's noted cook,
  a lady's personal maid (a samurai house's jochu or koshimoto), each with what came in kind (board, clothing)?
- **Figure needed**: per year (servants, live-in clerks) or per day/trip (hired scribes, guards), in silver or copper,
  with the in-kind part named.
- **Canon beside it**: stipend = rank squared for samurai clerks (`l7r.md`); servants and cooks are hinin laborers.
  The ledger's servant and steward figures are an unverified Kanazawa lead (0.7-1 koku a year; a young steward 3).
- **Region order**: Japan first, China beside it.

### 3. What a maker earned: a blacksmith's inputs, sales and income
- **Question**: for a Tokugawa (or Qing) blacksmith, ideally a village or town smith making and mending farm tools:
  the price of a common tool (a sickle, a hoe) against the iron and charcoal in it; how many tools or repairs a smith
  turned out in a year; his gross takings and his net income, and how many apprentices or journeymen worked with him.
  Any other craft's yearly accounts (a carpenter-master, a cooper, a tailor) would serve as a second case.
- **Figure needed**: per tool, price and input cost; per year, items made, gross takings and net income.
- **Canon beside it**: smiths are heimen craftsmen (`l7r.md`).
- **Region order**: Japan first, China beside it.

### 4. Entertainers: incomes, troupe size, costumes and instruments
- **Question**: what did entertainers earn: a traveling country troupe's takings per performance and per year and how
  it was shared; a street performer's daily take; a city star actor's yearly pay? How large was a traveling or rural
  troupe (as against the city kabuki and puppet companies of ~43 and ~26 in 0266)? What did a stage costume cost
  (ordinary and fine), and a shamisen, a bamboo flute and a hand drum (tsuzumi)?
- **Figure needed**: incomes per performance, day and year; troupe size; prices per costume and per instrument.
- **Canon beside it**: `l7r.md` "Entertainers": *"Each county generally has an acting troupe, which usually consists of
  around 5-10 entertainers ... Acting troupes usually make most of their money on market day"*, a weekly market in the
  county town, with special performances at the magistrate's manor. Entertainers are hinin.
- **Region order**: Japan first (kabuki, rural troupes, Morisada), China beside it.
