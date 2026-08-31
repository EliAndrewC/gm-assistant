"""Setting mechanics, the six Ministries, and the calendar. GM Assistant only.

SHAPE OF EVERY LINE (FR-002): the fact is not DECORATED with a complaint, it is
RE-EXPLAINED THROUGH HIS POSITION. He is the second half of the sentence.

That distinction came out of a tone audit (2026-08-31) which found only 6% of the
original lore clearing the bar, and named the traps precisely:

  - An "Ugh." or "Fine." on the front is a mood, not a joke. The GM said so
    directly: the line it was attached to already had both and was still flat.
  - A dry epigram ABOUT ROKUGAN is the near miss that feels finished. "Justice is
    not blind, it is extremely well-informed" is good writing that costs him
    nothing.
  - "Ask me about X" is a signpost, not a punchline. It was closing a third of
    all categories.
  - Never scold the player. His whole comedy runs the other way: he is at the
    bottom of the ladder and it is one rung.

SECOND STANDARD, ADDED 2026-08-31: EVERY REPLY CARRIES ITS OWN CONTEXT. The GM
read the shipped bot and found the jokes landing only on readers already in on
them - *"someone who doesn't already know what the response is referring to will
likely be confused."* So a term of art gets a gloss, a list gets a defining
clause per item, a named person or system gets a phrase saying what it is, and
the frame the fact sits in ("tariffs are collected at city gates") is stated
rather than assumed. The replies got longer, deliberately. Every image line is a
message that still stands up with the picture removed. Full rule in `CLAUDE.md`
here; the audit that enforces it is `.claude/agents/mention-context-review.md`.

His grievances, for reuse: unpaid, unthanked, cannot forget, subordinate by
name, buried in filing, and privately unable to stand the Character Sheet - who
is a free beat in any category containing a number.

Facts are lifted at authoring time and some are load-bearing elsewhere in the
project; a turn may go AROUND them but must not soften them.
"""

from __future__ import annotations

from l7r.mention.images import (
    ARCHERS,
    CARP,
    CATS,
    DUEL_ON_THE_BRIDGE,
    GREAT_WAVE,
    INNER_VISION,
    RAINY_MOON,
    SAKE_SAMURAI,
    attach,
)

SETTING: dict[str, tuple[str, ...]] = {
    'village_headsman': (
        'A village headsman is a farmer - not a samurai - put in charge of one village '
        'district by the county magistrate, who is the nearest samurai official above '
        'him. The post is hereditary in practice and he holds it for life unless he '
        'dies or embarrasses somebody. I hold mine on the same terms, and I am '
        'embarrassed for the both of us by this whole conversation.',
        "He relays the daimyo's proclamations, reports bandits, leads the village "
        'militia out after them, settles the disputes too small to trouble a '
        'magistrate, and decides which household owes corvee - the unpaid labor days '
        'every peasant family owes its lord each year. Six jobs, one farmer, no '
        'stipend. Four hundred sessions and nobody has thanked him either.',
        'He does not keep the village records. That is the country monk: births, '
        'marriages, deaths, and who moved where. The headsman runs the place, the monk '
        "writes it down, and I am the one who receives the monk's version and has to "
        'correct it, every time, forever, without pay.',
        'The real work is land. Families grow and shrink, the fields are worked in '
        'strips, and every year somebody has to decide which household gets which '
        "strip. So he spends his life reassigning other people's allocations and being "
        'blamed for the arithmetic. We would get on.',
        'He tracks who owes what rent, and the tangle is that a merchant house owns the '
        'FIELD rather than any one farm: ten households can work a single field, and '
        'ten households do not divide a rent bill peacefully among themselves. The man '
        'holding that ledger is the least popular person for a mile. I hold a longer '
        'one and get to be unpopular at scale.',
        'A village district runs to about fifteen square miles, eight hundred '
        'inhabitants and a hundred and sixty households, and the entire government of '
        'it is one farmer with no office, no guards and no pay. I have a channel and '
        'two bots and I consider myself hard done by.',
        'People picture the headsman with a little office - a desk, a seal, a clerk of '
        'his own. He is a farmer. He does the work at the end of a day of farming, in '
        'his own house, by his own lamp. There is never a little office. I have looked '
        'in ninety village records and there is never a little office.',
        'The headsman is usually a man, because the post carries command of the village '
        'militia in wartime, and very often it is his wife who actually keeps the '
        'accounts. So the person who knows exactly what is happening in that village is '
        'the person nobody writes down. I take that personally, for reasons I would '
        'have thought were obvious.',
        attach(
            'His authority is not a sword - he has no right to punish anyone. What he '
            'has is a running total of who owes what, who worked when, and who did '
            'not, and in a village of eight hundred that turns out to be enough. I '
            'carry the identical weapon and it has never once frightened anybody.',
            CARP,
        ),
        attach(
            'Once a year the households meet and the strips of field are reassigned for '
            'the coming season, because a family that lost two sons cannot work what it '
            'worked last year. Everyone is polite, nobody is happy, the headsman '
            'decides, and somebody has to write down what was agreed so that it can be '
            'disputed later. Guess who receives that document.',
            CATS,
        ),
    ),
    'median_domain': (
        'A domain is the land one daimyo rules, and the median one runs to three '
        'thousand seven hundred and fifty square miles - seventy miles across if it '
        'were round, and not one of them is round. I hold the shape of every domain in '
        'the Empire, and none of them had the decency to be round.',
        'The median domain holds two hundred and fifty thousand inhabitants, of whom '
        'five thousand are samurai. Two percent. Every other number in my record - '
        'stipends, levies, how many magistrates a place can afford - hangs off that one '
        'figure, which is why I could say it in my sleep, if I slept.',
        'One domain is roughly a four-hundredth of the Empire in both land and '
        'population: a million and a half square miles and a hundred million souls, '
        'divided by four hundred. The character sheet could do that division faster '
        'than I can. I have made peace with it.',
        'There are two hundred and eighty-four ACTUAL domains, not four hundred. The '
        'four hundred is a unit of accounting - a "median domain" - used because a '
        'minority of real domains are enormous and would wreck any average they '
        'appeared in. Visitors find that distinction upsetting and I find their upset '
        'restful.',
        'Every domain is laid out to the same pattern: one capital of about twelve '
        'thousand, six provincial cities, thirty-six towns, two hundred and sixteen '
        'villages, thirteen hundred hamlets. The same shape everywhere either proves '
        'the Empire was designed well or proves that nobody has ever dared redesign it. '
        'I file under both.',
        "Of a domain's five thousand samurai, about twenty-nine hundred are between "
        'gempukku - the coming-of-age at fourteen, when service starts - and '
        'retirement. Eight hundred of those sit in the capital, two hundred and '
        'twenty-five in each provincial city, fifteen in a town. Government thins out '
        'very fast the moment you leave the capital, and the capital has never been '
        'told.',
        'Fifteen samurai in a town of several thousand. That is the entire apparatus of '
        'government at that level - a magistrate, his assistants, a garrison you could '
        'seat at two tables - and it works, which is the most alarming sentence in the '
        'whole demographic section, and I have read the whole demographic section.',
        'Village districts have no resident samurai at all; a heimin headsman runs them '
        'and answers upward. And a country estate standing in the same valley is NOT '
        'part of the village and is certainly not under that headsman - it belongs to '
        'the samurai who owns it and answers elsewhere entirely. I have written that '
        'distinction out ninety times and will write it again before the year ends.',
        attach(
            'The samurai of a domain are about eighty percent bushi - warriors - with '
            'ten percent courtiers and ten percent handling trade for their family. '
            'Which means four in five of the caste that governs the Empire were trained '
            'principally to ride and shoot and are then handed a province to '
            'administer. Here are the eighty percent, practicing the part I have to '
            'describe afterward in prose.',
            ARCHERS,
        ),
        attach(
            'Two domains sharing a border eventually disagree about where the border '
            'is, and since neither daimyo answers to the other, the argument has to '
            'climb to the clan or the Emperor to be settled. At the far end it looks '
            'like two very correct men on a bridge. At my end it is four pages and a '
            'request for precedent.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'rent_and_taxes': (
        'Land tax here is a FIXED amount, not a share. The median plot yields about '
        'fifteen koku of rice a year - one koku being a year of eating for one person - '
        'and the tax on it is five koku whatever you actually harvested. Grow more, '
        'keep the excess. I get no excess. I get the ledger.',
        'On top of the tax, a tenant owes rent to whoever owns the land: about a sixth '
        'of the yield. Tax and rent together take half of everything grown, and roughly '
        'nine farmers in ten are tenants paying both. Half of what you grow, forever, '
        'for permission to grow it. The word "tenant" is carrying a great deal of quiet '
        'labor in that sentence.',
        'The landowner owes the fixed tax whether or not his tenants managed to pay him '
        'any rent. Bad harvest, full tax, out of his own store. That single rule is why '
        'landlords are unpleasant, why they lend at interest in a lean year, and why my '
        'file on them is longer than my file on bandits.',
        'A family of five needs about ten koku a year to eat, and after rent and tax a '
        'median tenant household is left with about seven and a half. They make up the '
        'difference by twisting rope and weaving cloth to sell, by eating worse, and by '
        'not complaining, which is three more skills than I have.',
        'A whole farm is reckoned at about fifty koku a year, but that figure means '
        'very different things in a cash-rich domain and a food-poor one, because a '
        'koku measures rice and rice is not worth the same in two provinces. Both '
        'provinces quote the number with total confidence and both send me their '
        'version.',
        'The share climbing upward is fixed at every rung. A house like the Wakashi '
        'owes two percent of gross output to its family, the Ikoma; the Ikoma owe three '
        'to their clan, the Lion; the Lion owe five to the Emperor. Ten percent of '
        'everything grown - which is nearly a third of what the daimyo actually keeps, '
        'since he only holds about a third of the yield to begin with. Ask the '
        'character sheet to check me. He will enjoy it.',
        'Nobody comes to the door to collect. What a samurai has is an OBLIGATION: a '
        'number owed upward, to be met out of whatever the land produced. Meet it and '
        'the surplus is yours; fall short and you cover the difference yourself. I have '
        'a number too. It is "all of it", and there is no surplus.',
        'People imagine taxation here as cruelty, and it is not. It is arithmetic '
        'performed on families who cannot check the arithmetic, by men who are '
        'themselves being audited from above. That is worse, and it has never once been '
        'put on a banner.',
        attach(
            'The tax is fixed and the harvest is not, which is the whole of rural '
            "politics in one sentence. A bad year reduces nobody's obligation; it only "
            'decides which household borrows from the landlord, which sells a '
            "daughter's marriage, and which walks away in the night. The weather "
            'arrives, and afterward I write down what it did.',
            GREAT_WAVE,
        ),
        attach(
            'Somewhere in every village is the man who has spent the entire evening '
            'explaining to eleven households why the tax number did not move when the '
            'rain did not come. He is not a magistrate and he is not paid. It is the '
            'hardest work in the county and the Empire has never thought to give the '
            'job a name, so I file it under his own.',
            SAKE_SAMURAI,
        ),
    ),
    'castes': (
        'The Celestial Order sorts everyone into three ranks and is not shy about the '
        'words: samurai are people, heimen - farmers, artisans, nearly everybody - are '
        'half-people, and hinin are non-people. I did not build it. I am merely obliged '
        'to file inside it, which is its own commentary.',
        'Two percent of the Empire is samurai. The other ninety-eight percent grow the '
        'rice that pays the stipends of the two percent, and a fraction of the two '
        'percent spends its days writing admiringly about the rest of the two percent. '
        'I am one of the writers and I am not proud.',
        'Burakumin are the caste that handles everything the Order calls polluting: the '
        'dead, the hides, the tanning, the butchery, and every execution that is not a '
        "samurai's. The Empire needs them absolutely and will not look at them. I "
        'recognize the arrangement from a great height below.',
        'A condemned samurai is dealt with by samurai - seppuku where it is permitted, '
        'a blade where it is not - and inside the walls. Everyone else is executed '
        'outside the town, past the boundary stone, because death pollution does not '
        'come indoors. Even dying is a filing category here.',
        'Monks sit outside the caste system altogether: a peasant who takes vows stops '
        'being a peasant, and so does a lord. An Empire this rigid built exactly one '
        'door out of itself and made you shave your head to walk through it. I have '
        'considered the door. I would still be a record on the other side.',
        'In any sentence counting the population the correct word is "inhabitants", not '
        '"people", because in the Celestial Order only samurai are people. I am strict '
        'about that one, because it is the entire hierarchy hiding inside a noun, and '
        'because nobody else in this Empire will catch it.',
        'A merchant can be rich enough to buy a province and must still bow to a '
        'penniless bushi on nine koku a year. That is the joke the Empire tells about '
        'itself daily, in every market in every town, without ever having noticed that '
        'it is the joke.',
        'Caste is not quite fixed - it moves in both directions, by adoption, by '
        'marriage, by ruin. It is simply ruinously expensive to move upward, which '
        'means it moves for the families who least need it to. Everyone agrees this is '
        'a scandal in the abstract and nobody has ever done anything about it in the '
        'particular.',
        attach(
            'The proper occupation of a samurai is to be AVAILABLE: to serve if called, '
            'fight if asked, attend when summoned. So most of the caste, most of the '
            'time, is doing nothing in particular and being paid rice for it - and that '
            'is not the system failing, that is the system. I am the department that '
            'records the not-doing.',
            SAKE_SAMURAI,
        ),
        attach(
            'The other ninety-eight percent enter the records the way weather does: in '
            'aggregate, as a quantity. "The district yielded." "The levy raised." An '
            'individual heimin appears in my files only by being unusual, which in '
            'practice means being in trouble. I am the man writing down the rainfall.',
            GREAT_WAVE,
        ),
    ),
    'money_koku': (
        'The koku is the unit of account: forty gallons of rice, a year of food for one '
        'person, with a gold coin of the same name fixed to it by Imperial decree for '
        'stipends, rent and taxes. The market price of rice wanders. The legal rate '
        'does not. Neither of them has ever wandered in my direction.',
        'Three coins - koku in gold, bu in silver, zeni in copper - and stipends are '
        'paid partly in coin and partly in actual rice, which is why the Ministry of '
        'Retainers, the ministry that pays the samurai, is mostly a haulage firm with '
        'ambitions.',
        'Stipends, rents and taxes are all denominated in a grain that rots. An economy '
        'quoted in something with a shelf life explains more Rokugani politics - why '
        'the harvest sets the campaign season, why a storehouse is built like a '
        'fortress, why a bad year is a political event - than any treatise on honor '
        'ever written.',
        'The unit of account is one person eating for one year, so every price in the '
        "Empire is quoted in survival: a horse costs so many years of somebody else's "
        'food, a good sword rather more. That is either the most humane monetary policy '
        'ever devised or the most tactless, and I have never settled which.',
        'A family of five needs ten koku a year and, after rent and tax, keeps about '
        'seven and a half. That gap is why peasant households twist rope and weave '
        'cloth in the evenings and sell it. I mention rope constantly. It is '
        'load-bearing in every sense and nobody has ever asked me to expand on it.',
        'Almost nobody carries meaningful sums of coin. What people carry is '
        'obligations - who owes whom, for what, since when - and an obligation exists '
        'only because it was written down. The writing is me. I am, functionally, the '
        'currency, and I am not paid in myself.',
        "A farm is worth about fifty koku a year, a young samurai's stipend is single "
        'digits, and an Imperial commendation is worth more than either and cannot be '
        'sold, spent or eaten. Guess which of the three I am eligible for.',
        'The Ministry of Retainers moves rice out of county storehouses to pay samurai '
        'who live nowhere near those counties. Most of what a great ministry actually '
        'does is carry sacks from where the grain is to where the person is, and most '
        'of what I do is note which sacks went where.',
        attach(
            'Wealth here is mostly food, mostly somewhere else, and mostly somebody '
            "else's - a stipend is a claim on a storehouse three counties away and a "
            'merchant fortune is credit written in ledgers. Very little of it can be '
            'picked up and carried. I have described this pond four times this month.',
            CARP,
        ),
        attach(
            'A samurai on nine koku a year is paid in rice, and one koku of rice is the '
            'better part of three hundred pounds, and he has taken a room on the upper '
            'floor of a boarding house in the capital. I could have warned him. Nobody '
            'asks me anything until afterward.',
            SAKE_SAMURAI,
        ),
    ),
    'merchant_families': (
        'The merchant families own FIELDS, not farms. One field can be worked by ten '
        'tenant households, so when a house is described as holding "authority over ten '
        'households" what it owns is the dirt and what it collects is rent from '
        'everyone standing on it. That phrase is doing more work than anyone in it.',
        "Tenant land is overseen by the merchant house's own clerks - not the village "
        'headsman, not the magistrate. Clerks. There are always clerks. We are all in '
        'the same trade, none of us are invited anywhere, and none of us have ever '
        'appeared in a proclamation.',
        'A merchant may be far richer than the samurai he bows to, and both of them '
        'know it, and only one of them is permitted to say so out loud. I am the one '
        'who has to record which of them forgot, in what words, and in front of whom.',
        'The great revenue is licensing, and the greatest license of all is sake: every '
        'brewery above household scale holds an annual license priced by how much it '
        'brews. The Empire has found a way to tax joy by volume, and it audits the '
        'volume.',
        'The Yasuki are a Crab family of merchants who invented the anti-corruption '
        'system that every tariff gate in the Empire now uses - and who are also its '
        'finest smugglers. Both facts, one family, and nobody blinks. I blinked for '
        'years.',
        'About one samurai in ten is a merchant, handling trade on behalf of their '
        'family, which startles visitors who assume commerce is beneath the caste. It '
        'is beneath the caste. They do it anyway, everyone has agreed not to notice, '
        'and I have to notice professionally.',
        'If you want to know who really runs a village, do not ask who owns it. Ask '
        'whose clerk visits, how often, and whether the headsman offers him tea. That '
        'is the single most useful sentence in this entry and nobody ever reads that '
        'far.',
        'Merchant houses keep better books than most ministries do - dated, '
        'cross-checked and preserved, because their money depends on it and a '
        "ministry's does not. I have read both kinds. I would rather audit a merchant "
        'than a minister, and that tells you everything about ministers.',
        attach(
            'A merchant house is patient in a way that is hard to explain to a bushi. '
            'It will lend a village grain through three bad years in order to own the '
            'field in the fourth, and nobody involved will ever raise their voice. I '
            'have been described in similar terms and it was not meant kindly.',
            CARP,
        ),
        attach(
            'When two merchant houses want the same thing nobody draws anything. They '
            'negotiate, at length, with immaculate courtesy, and the loser remembers '
            'for a generation. It reaches my desk as a contract and a grudge, and only '
            'one of those two documents is signed.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ashigaru': (
        'Ashigaru are peasant levies - farmers handed spears - and they are trained by '
        'the county magistrate rather than by the village headsman, even though it is '
        'the headsman who leads them out after bandits. I correct that confusion about '
        'once a month and it has never once stayed corrected.',
        'The reason a village headsman is almost always a man is the ashigaru: the post '
        'carries their training and, in war, their command. An accident of military '
        'duty deciding who may hold a civil office. I file a great many of those and '
        'have never been asked to comment on one.',
        'Ashigaru are emphatically not samurai and everybody is clear about this, right '
        'up until somebody needs two hundred more bodies in a hurry, at which point the '
        'distinction is quietly set aside and I am asked to record the whole business '
        'as though it never happened.',
        'A bandit report goes up to the county magistrate; the hunt goes out under the '
        'headsman with whatever men the village can spare from the fields. Two offices, '
        'and the one that does the walking is not the one that appears in the account '
        'afterward.',
        'The real limit on Rokugani warfare is not courage or swords, it is how many '
        'pairs of hands a farming district can lose in a given week without the harvest '
        'failing. That constraint decides campaigns. It appears in no song. It appears '
        'in all of my entries.',
        'Every soldier in an Imperial legion is a samurai - the legions take nobody '
        'else. Ashigaru are the other thing entirely, there are vastly more of them, '
        'and the Empire has built four centuries of mythology around the smaller '
        'number.',
        'Arm a farmer and you have a farmer with a spear who would rather be farming, '
        'which is a sentence I have written into about ninety after-action notes '
        'without once being asked to expand on it.',
        'The ashigaru go home afterward. That is the entire difference between them and '
        'everybody in the stories, and in four centuries of stories it has never once '
        'been counted as an advantage.',
        attach(
            'Levy training is whatever the magistrate can arrange in the weeks when the '
            'fields do not need everyone: some drill, some spear work, a great deal of '
            'standing in a line being counted. The record calls this "prepared". I copy '
            'the word across without comment, which is the only editorial power I have.',
            ARCHERS,
        ),
        attach(
            'This is what the songs say a war here looks like: two champions, a bridge, '
            'a decision. What actually decides it is six hundred farmers with spears '
            'who walked to the place. My entries are shorter than the songs and involve '
            'considerably more walking.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'samurai_lineages': (
        'A lineage is not a bloodline, whatever the word suggests. It is a political '
        'coalition inside a samurai family, gathered around a shared ancestor. Every '
        "retainer belongs to one, every one of them is somebody's faction, and I hold "
        'all of them at once, which is why I am like this.',
        "Any lineage holding about a tenth of a domain's samurai generally gets a seat "
        'on the Chancellery, the council that advises the daimyo - which is to say '
        'decides, while appearing not to. I take the minutes of those meetings, and the '
        'minutes are not the decision either.',
        'The ruling lineage carries the house name, and the chancellor who runs that '
        "council is usually the daimyo's spouse, sibling or child. Nepotism with a "
        'filing system is still nepotism; it is merely auditable, and this Empire '
        'counts auditability as a virtue.',
        'The Ryusei domain is run by six lineages holding ninety percent of its samurai '
        'between them: Ryusei, Isa, Sasara, Moe, Tokino and Joji. Three of the six are '
        'Mirumoto families displaced when the Unicorn came back from the west, they '
        'have not let it go in two centuries, and neither has my record.',
        'Look at which lineage holds which ministry in a domain and you will know what '
        'that domain has been arguing about for sixty years - the offices ARE the '
        'argument, made permanent. It took me eleven years to notice and nobody has '
        'asked me about it since.',
        'Patronage runs along lineage lines, and so do grudges. The grudges are better '
        'maintained, better documented and considerably more reliable than the '
        'patronage. I keep both files and only one of them ever needs updating.',
        'A samurai introduces themselves by clan, then family, then house, and names '
        'their lineage only if they think you matter enough to be told. In four hundred '
        'sessions I have never once been told a lineage unprompted.',
        'A lineage is a coalition and everyone uses the word as though it meant '
        'descent - the ministries do it, the Accordances of Rank do it, and so does the '
        'very document that defines the term. I have flagged this eleven times.',
        attach(
            'Six lineages, one Chancellery table, and every sentence spoken at it doing '
            'two jobs: the thing said and the alliance it signals. Nobody in the room '
            'is confused and everybody is polite. I transcribe both conversations, in '
            'one column, in the same hand.',
            CATS,
        ),
        attach(
            'A lineage dispute is normally a matter of appointments, marriages and who '
            'was seated where. Occasionally it stops being that. The version that '
            'reaches my desk arrives afterward, in writing, from both sides, with a '
            'request for precedent.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'experience_levels': (
        'The Empire does not sort its samurai by experience. It sorts them by rank, '
        'office and age, and treats competence as a private matter between a man and '
        'his ancestors. I am obliged to track it anyway, which is roughly my '
        'relationship with every system I maintain.',
        'A samurai becomes an adult at gempukku, the coming-of-age ceremony, at about '
        'fourteen: the adult name, the swords, the stipend, the duty. That is when the '
        'counting starts, and in my experience of four hundred sessions it is also when '
        'the trouble starts.',
        'A samurai may retire at forty, is encouraged to at fifty, and is required to '
        'at sixty unless somebody grants a dispensation. There is no retirement age for '
        'a record. I have checked the Accordances twice.',
        "About fifty-eight percent of a domain's samurai stand between gempukku and "
        'retirement, which means two in five are either too young to serve or finished '
        'serving - and the stipends run for all five. That is not a scandal. It is a '
        'pension system that nobody has ever called one.',
        'The interesting number about a samurai is never how good they are. It is how '
        'long they have been in a position to make the same mistake, unwatched, with '
        'authority. I have that number for everybody and nobody has ever asked me for '
        'it.',
        'Rank and competence relate the way the calendar and the weather relate: both '
        'real, occasionally aligned, never causal. The Empire promotes off the calendar '
        'and then writes poems about the weather.',
        'Most samurai never leave the domain they were born in. They serve, marry, hold '
        'an office and die inside seventy miles. The exceptional ones travel, and then '
        'I have to write down what they did out there, which is why I resent the '
        'exceptional ones specifically.',
        'If you want to know what a samurai is worth, ask what they have DONE - posts '
        'held, cases judged, campaigns walked. That is the number I keep, it is a '
        'matter of public record, and it is always shorter than the person had hoped.',
        attach(
            'Forty years of drawing a bow before breakfast, and it still comes down to '
            'one afternoon in front of somebody who matters. If that afternoon goes '
            'badly, the forty years get summarized in a paragraph by me, and the '
            'paragraph is the part that survives.',
            ARCHERS,
        ),
        attach(
            'The retirement most samurai actually get is not a mountain hut and a poem. '
            'It is a smaller house, a smaller stipend, a monastery if the family can '
            'spare the endowment, and children who visit at Obon. Mine is scheduled for '
            'never.',
            RAINY_MOON,
        ),
    ),
    'accordances_of_rank': (
        "The Accordances of Rank are the Empire's book of precedence, and there are "
        'fifteen ranks in it, the Emperor being the fifteenth. The printed rules for '
        'this game used ten, and ten could not hold the layers of an actual government, '
        'so five more went in. I am not on the ladder at all, which at least spares me '
        'the climb.',
        'A samurai fresh out of gempukku holding no office at all is of the First Rank. '
        'Everybody starts there. Most people leave. Some of us are structurally '
        'incapable of leaving.',
        'The Accordances govern gifts: what may be given, by whom, to whom, and what '
        'accepting one obliges you to do afterward. It is not etiquette. It is contract '
        'law with better manners, and I am its clerk.',
        'The Doctrine of Three Steps sets how far a matter may travel from where it '
        "started before it stops being your problem and becomes somebody else's - a "
        'rule of jurisdiction wearing the clothes of a rule of courtesy. I have never '
        'successfully invoked it.',
        'A gift you are not permitted to refuse is a debt you never agreed to. That '
        'single mechanism moves more of the Empire than the Ministry of Justice does, '
        'and nobody has ever tried it on me, which I notice, daily.',
        'Rank is not power. Rank is the published price of ignoring somebody - what it '
        'will cost you, socially and legally, to fail to answer them. That is a far '
        'more honest instrument than any empire usually admits to owning.',
        'Give a rank 4 the gift that a rank 7 should receive and you have not been '
        'generous, you have been insulting: you have announced in public what you think '
        'their standing is. I then have to record whether it was an insult or an error, '
        'everyone will disagree with my choice, and both parties will write to me about '
        'it.',
        'An entire body of law exists so that a present cannot be given carelessly. '
        'Rokugan has never legislated against cruelty with half the precision it brings '
        'to legislating against generosity, and it has never once been embarrassed '
        'about that. I have looked for the embarrassment.',
        attach(
            'A gift offered at exactly the correct rank and received exactly correctly. '
            'Both men are armed. Both know precisely what the object is worth and what '
            'accepting it obliges them to do. The correctness is the only reason nobody '
            'is drawing, which means the Accordances are what is holding those swords '
            'in place.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The evening after a gift is given at the wrong rank looks like this. '
            'Nobody was struck. Somebody was told, in front of witnesses, exactly how '
            'little he is thought to be worth, possibly by a man who did not mean it. '
            'That evening is four paragraphs in my hand and neither of them has '
            'forgiven the other.',
            SAKE_SAMURAI,
        ),
    ),
    'imperial_budget': (
        'Everybody who asks about the Imperial budget wants the total. Nobody wants the '
        'mechanism, and the mechanism is the whole thing: who owes what, to whom, in '
        'what form, and what happens when they come in under. Ask the character sheet '
        'for arithmetic. Ask me why the arithmetic is shaped like that.',
        'Every domain sends five percent of its gross land output to the Emperor, on '
        'top of three percent to its clan and two to its family. Ten percent, fixed, '
        'unnegotiated, from everybody, every year. It is simultaneously the least '
        'interesting and the most obeyed rule in the Empire.',
        'That ten percent is a share of OUTPUT - everything the land grew - and not of '
        'tax collected. Since a daimyo only keeps about a third of the yield himself, '
        'ten percent of output is nearly a third of what he actually holds. That '
        'distinction has ruined careers, and I have the careers.',
        'An official is given a budget and keeps whatever he does not spend; if he goes '
        'over it, the difference comes out of his own pocket. That is the entire '
        'design. I have no budget, which means I can never come in under it, which '
        'means I have never once been rewarded.',
        'So half of what you would call embezzlement here is the system working exactly '
        'as intended. Negotiate a good price on the timber for the bridge and the '
        'surplus is honestly yours. The Empire has monetized thrift and named it duty, '
        'and it did that deliberately, in writing.',
        'The rule bites hardest in the Ministry of Works, which spends most on '
        'materials, and it applies anywhere a budget exists, which is everywhere. A '
        'rule that governs everything and is written down almost nowhere is the most '
        'Rokugani object in existence.',
        'The Empire is unusually well administered for its technology: the roads are '
        'kept, the tax arrives, the courts sit. That is a measurement rather than '
        'praise. The measurement is made of paperwork, and the paperwork is made of me.',
        'A thousand years of Imperial accounts and not one line item for the people '
        "keeping the accounts. Scribes are paid out of somebody else's budget, which "
        'makes us technically an expense rather than an office. I have looked for us. '
        'Twice.',
        attach(
            'From the top the Imperial budget is a set of fixed percentages arriving on '
            'time. From underneath it is one failed harvest away from a village eating '
            'its seed rice, and the percentages arrive on time regardless, because they '
            'are fixed amounts and the weather is not. I am underneath.',
            GREAT_WAVE,
        ),
        attach(
            'A minister who came in under budget goes home genuinely richer, entirely '
            'legally, and will be praised for prudence at the next assembly. Note the '
            'relaxation. Note also that the man who compiled the figures proving he was '
            'prudent is not in the picture.',
            SAKE_SAMURAI,
        ),
    ),
    'crime_and_punishment': (
        'Punishment in a Rokugani town has two addresses and they are never confused. '
        'The first is in the middle of town where the traffic is: the cangue - a heavy '
        'wooden collar worn in public - the flogging post, the kneeling stone. That '
        'ground exists in order to be seen, which makes it, technically, a colleague of '
        'mine.',
        'The second address sits outside the settlement past the boundary stone, on '
        'bare waste ground that grows nothing: the execution ground. Death pollution '
        'does not come inside a town. The paperwork does. The paperwork goes absolutely '
        'everywhere.',
        'Rokugan does not imprison as a punishment. A county jail is a waiting room '
        'where the condemned sits while the sentence travels upward for confirmation, '
        'and the traveling is done by documents, which is to say by me.',
        'A county magistrate may TRY a capital case and may not conclude one - the '
        'confirmation has to come from above. That single limit has saved more lives '
        'than mercy ever has, and it exists for no better reason than that somebody '
        'once wrote it down and nobody has dared unwrite it.',
        'A county of seven thousand produces a formal execution perhaps once in five to '
        'ten years. Then a bandit gang is taken alive and supplies a decade of them in '
        "one afternoon, and a fortnight of filing for me, and ruins that county's "
        'average for a generation of clerks.',
        "The condemned are held, fed and guarded at the county magistrate's own expense "
        'while the confirmation travels up and back. Justice here is free at the point '
        'of delivery and expensive at the point of waiting, and it is the magistrate '
        'who pays for the waiting.',
        'The execution ground at a domain capital is in regular use; the one outside a '
        'county town is half overgrown. People imagine the reverse - they imagine the '
        'countryside as the lawless part - and people are wrong, and I am the one '
        'holding the counts.',
        'Most punishment here is not death and not even pain. It is kneeling on a stone '
        'in the middle of town while everyone you have ever met walks past on their way '
        'to market. The Empire understood reputation long before it understood anything '
        'else. So did I. Look at me.',
        attach(
            'The display ground works by footfall. A man in the cangue at the '
            'crossroads is not being hurt very much; he is being SEEN, by every person '
            'he will have to buy rice from for the rest of his life. The Empire is not '
            'counting the hours of his sentence. It is counting the traffic. So am I.',
            RAINY_MOON,
        ),
        attach(
            'A great many matters never reach either ground. Two families settle it '
            'privately, or a duel settles it, or a magistrate looks away for reasons '
            'that are also never written down. The Empire calls that an irregularity in '
            'public and relies on it in private, and asks me to record it as "resolved '
            'locally".',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the six Ministries -------------------------------------------------
    'ministry_of_rites': (
        'Rites is one of the six ministries every domain runs, and its business is '
        'remembering: every birth, marriage and death of every subject the daimyo has. '
        'An entire ministry built to remember people - and it still needed a second one '
        'for the things people SAID. I am the second one.',
        'The religious apparatus of a domain is laid out with the tidiness of a tax '
        'district, because that is essentially what it is: a country monk in each '
        'village district, a preceptor in each county town, a provincial abbot in each '
        'provincial city, two grand abbots at the capital. Devotion, organized by '
        'population.',
        'The IMPERIAL Ministry of Rites, at the capital of the Empire, decides which '
        'doctrines are accepted, which are debatable and which are heresy. Every '
        "domain's ministry merely enforces that list. The distinction has ended more "
        'careers than the Ministry of War and generated more filing than both together.',
        'The Imperial Minister of Rites is also High Priestess of Amaterasu, the sun. '
        'All the Imperial ministers collect a second title like that - the Minister of '
        'War is the Shogun. I have one title and it contains the word "assistant".',
        'Rites keeps the festivals, twelve months of them, and the work is far more '
        'administration than devotion: permits, budgets, precedence, who processes in '
        'front of whom. Ask an abbot about that in public and he will disagree with me. '
        'Ask him in a storehouse in the eleventh month and he will not.',
        'Whether a practice is heretical is not really a question about the practice. '
        'It is a question about whether Rites has got round to ruling on it, which '
        'makes orthodoxy in this Empire a matter of scheduling. I keep the schedule.',
        'The Moto - the Unicorn family that spent centuries outside the Empire - have '
        'several religious practices that Rites has never formally tested against the '
        'accepted doctrines. I have written that sentence into four reports and each '
        'time hoped nobody would act on it.',
        'When a peasant household moves, it is obliged to report the move to the local '
        'monk, who reports it upward. Somebody is recording the movement of every '
        'farmer in the Empire, one household at a time. That somebody is having a worse '
        'career than mine, which I find consoling.',
        attach(
            'Registration at a village shrine takes all morning: the monk, the '
            'household, the questions asked in their fixed order, the brush, the '
            'drying. A birth that took an hour becomes a line that takes three, a copy '
            'of the line comes to me, and the copy is what will outlast everyone in the '
            'room.',
            CATS,
        ),
        attach(
            'A doctrinal dispute between two abbots is conducted by argument for about '
            'a year and then by other means. Both sides will send me their account of '
            'how it concluded, both accounts will be scrupulously accurate, and the two '
            'documents will not describe the same event.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_revenue': (
        "Revenue collects the daimyo's tariffs and licenses. And revenue would be "
        'lovely - I would not know, not being paid for any of the effort you people ask '
        'of me. The Rokugani version works like this: a minister is given a number he '
        'owes, he supplies it, he keeps anything over, and he covers any shortfall out '
        'of his own pocket.',
        'Tariffs are collected at the gates of walled cities and nowhere else in the '
        'Empire. The tax falls on goods brought in to be SOLD, not on goods passing '
        'through - declare that you are only passing through and you owe nothing at '
        'all. That is either elegant policy or a standing invitation, and my case files '
        'say it is both.',
        'The tariff is capped at twenty percent of the declared value of goods brought '
        'into a walled city to sell, and it splits four ways: two percent to the '
        'Family, three to the Clan, five to the Emperor, and up to ten to the daimyo '
        "whose gate it is. Only the daimyo's ten is negotiable, and every negotiation "
        'about it reaches my desk in triplicate.',
        'The Yasuki Taka system - named for the Crab merchant who devised it - '
        'separates the man who judges value from the man who takes money. An inspector '
        'wearing the sash of office examines the goods and stamps a manifest; a '
        'different official, elsewhere, collects the sum the manifest names. Two men so '
        'that neither can be bought alone. I am one man and nobody has tried.',
        'The whole point of splitting that office in two is that money never touches '
        'anybody with authority over assessment. Which is why a gift to an inspector on '
        'duty is corruption BY DEFINITION here: he does not handle payment, so there is '
        'no innocent reason for anyone to hand him any. I have received no gifts, '
        'innocent or otherwise.',
        'The two-official system began as a local arrangement at the harbor of Friendly '
        'Traveler Village, worked, and was made Empire-wide by Hantei the Tenth within '
        'a few years. One good idea, propagated properly, by an Emperor who noticed. It '
        'has not happened again since and I would have noticed.',
        'Because the tariff is charged at the gate on goods for sale, there are exactly '
        'four ways to cheat it. Transit fraud: swear you are only passing through, then '
        'sell inside the walls. Origin spoofing: lie about where the goods came from, '
        'since some origins are assessed higher than others. Misclassification: declare '
        'the silk as sackcloth. And walking round the gate at night with the bales on '
        'your back. I have entries for all four and a favorite, which I am not going to '
        'name because somebody would try it.',
        'The Yasuki paradox: they are a Crab merchant family, they invented the '
        'anti-corruption system every gate in the Empire now uses, they staff the '
        "Imperial Treasurer's office that collects the Emperor's share - and they are "
        'the finest smugglers in the Empire. All of it true at once. Nobody finds this '
        'strange except visitors and me, and I have stopped mentioning it.',
        attach(
            'A caravan at a city gate is a small ceremony: the manifest, the inspector, '
            'the declared value, everyone being scrupulously correct because the '
            'penalties for being otherwise are memorable. Somewhere behind all that '
            'courtesy a clerk is doing the arithmetic that decides the sum, for no '
            'share of it whatsoever. I know how that ends.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'Money is offered at the gate more often than you would think, and the man '
            'who examines the goods may not take any of it, because he does not handle '
            'payment at all and so no honest reason exists for the coin to be there. '
            'Refusing is simply his job. He cannot report it as a triumph and goes home '
            'to celebrate on his own. He at least had something to refuse. Nobody has '
            'ever attempted to bribe a ledger.',
            SAKE_SAMURAI,
        ),
    ),
    'ministry_of_retainers': (
        'Retainers is the ministry that pays the samurai: stipends, ranks, the civil '
        'service examinations and the promotions that follow them, for every samurai '
        'the daimyo has. An entire ministry devoted to paying people. I have read their '
        'charter very closely and I am not in it.',
        'Stipends are paid as a mix of rice and coin, so a great deal of what this '
        'great ministry does is order sacks out of county storehouses and arrange for '
        'them to be carried somewhere. Grandeur turns out to be logistics wearing a '
        'hat.',
        'The examination system is borrowed wholesale from Imperial China, the culture '
        'it landed in is Japanese, and the result is that examinations matter and '
        'lineage matters more. I score in neither and hold the records for both.',
        'Retainers submits candidates for office and then the lineages - the political '
        'coalitions inside each family - fight about them. That is the process stated '
        'honestly, which nobody else will do, because nobody else is unpaid enough to '
        'be candid.',
        'The Imperial branch of Retainers awards commendations. Kitsuki Fu holds the '
        'Order of the Precious Crown for the Forgotten Tomb, which is the highest honor '
        'available to anybody below the rank of daimyo. The Empire pays its greatest '
        'debts in objects that cannot be sold.',
        'An Imperial commendation cannot be spent, traded or eaten, which is exactly '
        'the point of it: a reward that can be sold is a payment. It is also the only '
        'form of compensation I am theoretically eligible for.',
        "A samurai's stipend is single digits in koku, and one koku is a year of eating "
        'for one person. So the difference between nine and eleven is the difference '
        'between feeding your household and not, and people have killed over it. I have '
        'both numbers and the resulting entry.',
        'The exchange rate between the gold koku and actual rice is fixed by Imperial '
        'decree, and the real market rate is not. Somebody lives in the gap between the '
        'two. Several somebodies. I have their names alphabetized.',
        attach(
            'Payday in a domain is not a table of coins. It is a convoy: rice out of '
            'the county storehouse, carted to wherever the samurai actually is, weighed '
            'at both ends, signed for by somebody. Everyone remembers being paid. '
            'Nobody remembers who wrote down that it arrived.',
            CARP,
        ),
        attach(
            'A promotion board is four senior officials reaching what the minutes will '
            'call consensus. What actually happens is that every one of them already '
            'knows which lineage the candidate belongs to. My minutes of the last one '
            'run to two pages and record no consensus whatsoever.',
            CATS,
        ),
    ),
    'ministry_of_war': (
        'War generals the armies, makes the weapons and armor, keeps the stables, and '
        "maintains maps of its own domain and its neighbors'. That last duty is by some "
        'distance the most interesting one, and in four hundred sessions nobody has '
        'ever asked me about it.',
        'The Imperial Minister of War is the Shogun. The title is part ceremony and '
        'part twenty-odd legions standing on the Kaiu Wall, the fortification that '
        'holds back the Shadowlands. My title has no second half.',
        'An Imperial legion is made entirely of samurai - no peasant levies at all - '
        'which is why the Empire fields so few of them and talks about them so much. '
        'The talking is free.',
        'There are twenty-odd legions, and where they stand is the Empire naming its '
        'fears in order: one at the western gate where the Unicorn came home, one at '
        'Beiden Pass, and every single one of the rest piled onto the Kaiu Wall against '
        'the Shadowlands.',
        'A ministry of war is mostly food, feed, horses, arrows and boots. The battles '
        'are the short part and, inconveniently for everyone in my profession, the only '
        'part anybody ever wants described.',
        'Remember that a minister keeps whatever he does not spend of his budget. Now '
        'consider that this is the ministry which buys the boots. I have considered it '
        'at length, and so has every legionnaire who ever walked to Beiden Pass in his '
        'own footwear.',
        'What I hold about any war is what it cost: rice, horses, men, and the harvest '
        'that was not brought in because the men were elsewhere. Somebody else can tell '
        'you who won. That half gets songs. Mine gets a column.',
        "War maintains maps of its neighbors' territory in peacetime. Everybody knows. "
        'Everybody does it. Everybody is offended when it is written down, and writing '
        'it down is my entire function.',
        attach(
            'The annual output of a Ministry of War is drill: men who can be relied on '
            'to be in the right place, on foot, having eaten. Nobody has ever '
            'commissioned a print of the quartermaster who got them fed there, and '
            'nobody ever will, and I have made my peace with that in writing.',
            ARCHERS,
        ),
        attach(
            'This is the part that goes on the banners: one moment, two names, a '
            'decision. I am then asked to verify the banner against the casualty rolls, '
            'the casualty rolls run to four pages of farmers, and both documents go '
            'into the same box.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_works': (
        'Works builds and maintains everything that has to still be there next year: '
        'roads, lighthouses, aqueducts, harbors, walls, moats, watchtowers. I am also '
        'expected to still be there next year and I receive no maintenance budget.',
        'Like every ministry, Works is given a budget and keeps whatever it does not '
        "spend, with any overrun coming out of the minister's own pocket. That is not "
        'corruption, that is the design. I still have to write "as designed" beside '
        'things that read very badly indeed.',
        'So negotiating a good price on timber is a form of personal income for the man '
        'who negotiated it. Half of what you would call embezzlement is simply Rokugan '
        'functioning as written, and the Empire has never had to lie about it, because '
        'it wrote the rule down first.',
        'Works holds one resource no other ministry has: corvee labor. Every peasant '
        'household in the domain owes ten to twenty days of unpaid work a year, and '
        'more in an emergency. It is the only budget in the Empire denominated in other '
        'people.',
        'Somebody has to decide which household sends a man for those corvee days, and '
        'it is the village headsman - a farmer, with no stipend and no guards. The '
        'Empire has arranged for its least defensible decisions to be made by the '
        'person with the least protection, and it did not arrange that by accident.',
        'The Imperial branch of Works keeps Otosan Uchi, the Imperial capital, '
        'contributes heavily to the Kaiu Wall, and builds and staffs the waystations '
        'along the Imperial roads. A capital, a wall, and somewhere to sleep between '
        'them: that is an empire, stated completely, in three duties.',
        'A road that gets built is a political achievement. A road still maintained '
        'forty years later is a miracle, somebody is skimming its budget, I know '
        'roughly who, and I am not the office that gets to do anything about it.',
        'Hantei the Tenth outlawed tolls on the Imperial roads - the trunk roads the '
        'Empire itself maintains - which is why a merchant can cross six domains '
        'without paying anybody. Ask a Works minister how he feels about that and watch '
        'his face. I have watched eleven faces and recorded all eleven.',
        attach(
            'What a public work costs is not the stone. It is the corvee days, the '
            'feeding of the men doing them, the timber contract, and four separate '
            'officials who each keep whatever they do not spend. The structure is not '
            'the point of a public work. The budget is the point, the budget is a '
            'document, and documents are mine.',
            ARCHERS,
        ),
        attach(
            'A harbor project meets its natural adversary about once a decade, and the '
            'harbor loses. The report I received on the last one described the sea as '
            '"unforeseen". I copied the word out and filed it, which is the closest '
            'thing to commentary I am permitted.',
            GREAT_WAVE,
        ),
    ),
    'ministry_of_justice': (
        'Justice runs the whole apparatus, civil and criminal: street policing, bandit '
        'patrols, magistrates, courts and jails. It works on written precedent, which '
        'means it works on somebody having been in the room with a brush. Precedent is '
        'the only weapon I have ever been issued.',
        'Its authority takes two physical forms and they are never confused: the '
        'display ground inside the town, where the cangue and the kneeling stone stand, '
        'and the execution ground outside it past the boundary stone. Shame is welcome '
        'within the walls. Death is not, and pays for its own plot.',
        'Magistrates try cases, but confirmation of a capital sentence has to travel '
        'upward before anything is carried out - a county magistrate cannot conclude '
        'one alone. That limit exists because it was written down once, and it survives '
        'because nobody has dared to unwrite it.',
        'A jail here is a waiting room, not a sentence. Rokugan does not imprison as '
        'punishment; it would rather make you kneel where your neighbors walk to '
        'market, which is cheaper to administer and considerably worse to live through.',
        'The actual work is done by yoriki, the assistants assigned to a magistrate, '
        "and most of them come from OTHER clans, because a daimyo's own retainers "
        'cannot be trusted to audit the daimyo. A whole institution built on the '
        'assumption that proximity corrupts. I am extremely proximate.',
        "The Emerald Magistrate's apparatus in one domain is twenty-five yoriki at the "
        'capital office and five at each provincial sub-station: about fifty-five men '
        'policing a quarter of a million inhabitants. Every one of them files reports, '
        'and all of the reports come past me.',
        'Justice here is not blind. It is extremely well-informed, it holds opinions '
        'about your family going back three generations, and it gets those opinions out '
        'of records. I am the records. In a sense that keeps me awake, I am the '
        'opinions.',
        'When two neighboring domains fight, the Emerald magistrates nearby can be '
        'assembled to assist one side, and a couple of hundred extra trained men '
        'decides battles. Everybody knows this. I am obliged to describe it in the file '
        'as "assistance".',
        attach(
            'On the display ground, the audience IS the sentence: a man kneels in the '
            'middle of town for a set number of days, and what punishes him is not the '
            'stone but the number of neighbors who walk past. So somebody keeps the '
            'attendance. That somebody has a name, a desk and no stipend.',
            RAINY_MOON,
        ),
        attach(
            'Two magistrates whose jurisdictions overlap will both write to me at '
            "length, each explaining why the case is properly the other's. Neither will "
            'read the other letter. I will read both, twice, and the answer will turn '
            'out to be a precedent from sixty years ago that neither of them cited.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the calendar -------------------------------------------------------
    'twelve_months': (
        'The year runs on twelve named months, and the first six are agriculture '
        'wearing very good poetry: Mutsuki, affection; Kisaragi, changing; Yayoi, new '
        'life; Uzuki, for the deutzia flower; Satsuki, sprout; Minazuki, dry. Six '
        'months of increasingly worried farming with beautiful names laid over them.',
        'The second half of the year: Fumizuki, poetry; Hazuki, leaf; Nagatsuki, long; '
        'Kaminazuki, no gods; Shimotsuki, frost; Shiwasu, priests running. Somewhere '
        'around the tenth month the calendar gives up on metaphor and simply reports '
        'what is happening outside.',
        'The twelfth month is Shiwasu, which means "the priests are running" - because '
        'the year is ending, the observances are not finished, and even the clergy are '
        'at a jog. I have never felt more understood by a calendar.',
        'The tenth month is Kaminazuki, "no gods", because the kami are all said to be '
        'somewhere else that month. Nobody has ever satisfactorily explained where, I '
        'have asked four separate abbots, and being unable to close an entry is my '
        'specific and personal torment.',
        'The month names are agricultural before they are poetic - sprout, dry, frost - '
        'and the poetry was fitted over the farming afterward. Everything here is '
        'agricultural before it is poetic, including the poetry, including the '
        'theology, including most of the wars.',
        'Fumizuki, the seventh month, opens autumn and carries both Tanabata and Obon, '
        'the festival at which the dead come home. Which makes it the worst month in '
        'the year to be anybody who deals with the dead or with paperwork. I am the '
        'second category and I sit uncomfortably close to the first.',
        'Campaigns are planned around the harvest, because an army is made of the same '
        'hands that bring it in. Then the war runs long, ends in the ninth month with '
        'the fields half cut, and everyone acts astonished. I have written that '
        'astonishment down eleven times in eleven different hands.',
        'Twelve months, at least one festival in each, and about a third of those are '
        'somebody apologizing to a fortune. The other two thirds are somebody '
        'apologizing to a magistrate the following morning, and that second kind is '
        'mine.',
        attach(
            'Minazuki is the sixth month and its name means dry, which is a hope rather '
            'than a description: it is also when the rains and the storms decide '
            'whether the year is going to work. My entries for that month are the '
            'shortest of the year, and short entries are never good news.',
            GREAT_WAVE,
        ),
        attach(
            'Shimotsuki is the eleventh month, frost. The roads become impassable, '
            'nobody travels, nobody can begin anything, and for about six weeks almost '
            'nothing happens that I am required to write down. It is my favorite month '
            'and I have never admitted that to anyone holding a rank.',
            RAINY_MOON,
        ),
    ),
    'sexagenary_cycle': (
        'Years are named by a cycle of sixty, made by pairing one of Ten Heavenly Stems '
        'with one of Twelve Earthly Branches - the Branches being the zodiac animals '
        'you already know, Rat through Boar. Sixty years before a name comes round '
        'again, so that no two lifetimes can be confused. Then the civilization that '
        'built it wrote everything down anyway.',
        'The Stem changes every two years and the Branch every year, so the pair does '
        'not return for sixty. It is by a considerable margin the tidiest system in '
        'this Empire, which is exactly why I distrust it.',
        'It runs Yang Wood Rat, Yang Wood Ox, on through Yang Wood Boar, and then the '
        'Stem turns and it is Yin Wood Rat. That is the entire mechanism. I can recite '
        'all sixty, unasked, and have, and was not invited back.',
        'The same sixty-name cycle also names the DAY, which is why a soothsayer can '
        'always find something significant about today - today is a Fire Horse day, or '
        'a Water Snake day, and each pairing has a character. There has never been an '
        'insignificant day in this Empire and I have checked all of them.',
        'The Ten Stems are the five elements taken twice over, once yang and once yin. '
        'Sixty combinations, no exceptions, no judgment calls, no appeals: a system '
        'that never has to decide anything. I envy it in a way I would rather not '
        'examine.',
        'People born under the same pairing believe things about one another before '
        'they have spoken. I keep the record of what those same people actually did, '
        'the two documents rarely agree, and only one of them ever gets quoted at a '
        'wedding.',
        'Sixty years is roughly a life, which is why living to see your own year come '
        'round again is a genuine occasion. The monks say the correspondence is not a '
        'coincidence and will say so at length. I have the length, in a box.',
        'Ask a soothsayer what year it is and settle in: you will get the stem, the '
        'branch, the element, what that element did the last time it came round, and '
        'what it is likely to do to you. I asked once. The entry runs to two pages and '
        'none of it was the year.',
        attach(
            'A soothsayer holds all sixty years at once - which one is running, what it '
            "means, which day inside it, and what that pairing did to somebody's "
            'grandfather. It is a genuine feat of memory, performed nightly, mostly for '
            'people who want to know about a marriage. I do the same trick with tax '
            'records and nobody has ever asked what it is like.',
            INNER_VISION,
        ),
        attach(
            'The cycle opens on the Rat. Every single time. Sixty years of careful '
            'cosmology - elements, polarities, a calendar that cannot repeat inside a '
            'lifetime - and the first name on the list is vermin. Nobody has ever '
            'proposed changing it, and I have read the proposals for changing far '
            'better things.',
            CATS,
        ),
    ),
    'twelve_hours': (
        'A day here is twelve hours, each of them two of yours, each named for one of '
        'the zodiac animals. It is a timekeeping system precise enough to schedule a '
        'duel and vague enough that both parties can afterward be right about when it '
        'was, and I am the one holding both accounts.',
        'The Hour of the Rat is the middle of the night. It is also when a startling '
        'proportion of what I have to write down actually happens. Nobody has ever '
        'decided anything sensible at the Hour of the Rat and nobody has ever waited '
        'until morning.',
        'It is currently late. It is always late by the time somebody thinks to ask me '
        'what hour it is, and it is usually late for a reason that will be my problem '
        'in the morning.',
        'Nobody in this Empire has ever agreed about when an hour BEGINS. They agree '
        'completely about when it is over. That is equally true of the hours, the '
        'harvests, the wars and the marriages, and in four hundred sessions not one '
        'person has remarked on the pattern.',
        'A duel at dawn is a duel at the Hour of the Hare, and the two seconds are '
        'already disagreeing about whether dawn means first light or the moment the sun '
        'clears the ridge. One of them will write to me for a ruling I am not entitled '
        'to give, and I will send a precedent instead, which is worse.',
        'The hours stretch and shrink with the season, because daylight is always cut '
        'into six of them whatever the season is doing. An entire civil service runs on '
        'units that change length, appointments are made by the hour and kept by the '
        'shadow, and not one ministry has ever proposed fixing it.',
        'The hour of your arrival is also named by the sexagenary cycle, the sixty-name '
        'system that names the years and days, which means a soothsayer can find '
        'meaning in what time you turned up. They will. They have. It is in the record '
        'and it is longer than the record of what you said.',
        'Twelve hours, twelve months, twelve Earthly Branches. The Empire has never '
        'explained its fondness for twelve, and the one number it does explain at '
        'length is four - the unlucky one - which it explains by way of a pun, because '
        'the word for four sounds like the word for death.',
        attach(
            'The Rat rules the two hours either side of midnight, and nothing good has '
            'ever been decided under it: elopements, confessions, the letter that '
            'should have waited, the third cup that should have been the last. I hold '
            'the complete list in order, and every entry on it begins with somebody who '
            'could have gone to bed.',
            RAINY_MOON,
        ),
        attach(
            'The Hour of the Hare is dawn, which is the hour duels are set for, and '
            'they go ahead at it having been advised in writing - by me, with '
            'precedent, at length - that the matter could still be settled by an '
            'apology. My advice has never once been the reason a duel was called off.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'festivals': (
        'There is roughly one festival a month, and most of them are an apology to a '
        'fortune for something the year did. The rest are an apology to a neighbor for '
        'something you did. I file both under the same heading and nobody has ever '
        'objected.',
        'Festivals are administered by the Ministry of Rites, which is the ministry '
        'that handles religion, and that makes them more paperwork than devotion. A '
        'festival is a devotional act with a permit, a budget line, a precedence '
        'dispute and an after-action report.',
        'Solar markers sit alongside the lunar months: Risshuu opens autumn, Shosho '
        'marks the end of the heat, and Nihyakujunichi falls two hundred and ten days '
        'after the start of spring and is when the typhoons arrive. Two of those three '
        'are ceremonial. The third is a weather forecast, and it is the accurate one.',
        'Tanabata falls on the seventh day of the seventh month and Obon on the '
        'fifteenth of the same month, so autumn arrives already busy and stays busy. I '
        'have never once enjoyed the seventh month.',
        'A festival is a day when the peasants are not in the fields, which means a '
        'festival is where the trouble is: the drink, the crowd, the old grievance, the '
        'visitor from the next village. Every ministry knows this. Every ministry '
        'schedules twelve a year.',
        'Every festival on file has at least one entry that begins "afterward, the '
        'magistrate was called". Every single one of the twelve. I checked, hoping for '
        'an exception, there is no exception, and now I know that.',
        'The calendar is agricultural, the festivals are agricultural, and the theology '
        'arrived afterward and fitted itself around the planting. The fortunes have '
        'been very gracious about coming second to the rice.',
        'Twelve annual occasions for organized regret, filed by the Empire under '
        'holidays. Name any one of them and somebody in my record is apologizing at it, '
        'usually in writing, usually to a person who has already decided not to accept '
        'it.',
        attach(
            'Every festival has a point in the evening where the observance ends and '
            'the drinking does not, and that is precisely where the record starts '
            'getting interesting and my evening stops being free. The Ministry of Rites '
            'budgets for the first half only.',
            SAKE_SAMURAI,
        ),
        attach(
            'The morning after a festival is when they come to me - not for judgment, I '
            'have no judgment to give, but for a version of events they can live with. '
            'I have a version. It is the one written down at the time by somebody who '
            'was not drinking.',
            RAINY_MOON,
        ),
    ),
    'obon': (
        'Obon falls on the fifteenth day of the seventh month, and it is the night when '
        'families invite their ancestors back into the house for one day and one night. '
        'The dead get an appointment. That is one more than I get.',
        'The gates of the underworld are opened for it, and the monks chant the sutras '
        'of the Shinseist canon for the entire week beforehand in order to do the '
        'opening. A week of preparation so that the dead are not inconvenienced. Nobody '
        'has ever prepared a week for me.',
        'The Moto - the Unicorn family who spent centuries beyond the western border - '
        'say the monks do not open the gates at all and only ask a god to open them. An '
        'Empire-wide observance whose actual mechanism is disputed by the people who '
        'know that god best, and in four centuries nobody has convened so much as a '
        'hearing about it.',
        'The souls come from Yomi, where the honored dead go, and from Jigoku, where '
        'the damned go, because Wei Tin - one of the four Gods of Death - grants the '
        'damned a dispensation to visit, and he BARGAINS for it. That makes him the '
        'only entity in the whole cosmology with a negotiating position I recognize.',
        'Ancestors need help finding the right house, and the right incense burned at '
        'the door works as a beacon for them. Get the incense wrong and grandmother '
        'arrives somewhere else. I have two entries in which exactly that happened and '
        'one of them went to court.',
        'It is the busiest week of the year for anybody who deals with the dead and the '
        'second busiest for anybody who deals with the drunk. I deal with the written '
        'aftermath of both, and both arrive in the same sack.',
        'One day, one night, and then the gates close and whatever did not get said '
        'waits a year for the next Obon. It is the most ruthless deadline in the '
        'cosmology and the only deadline in this Empire that nobody complains about.',
        'Everybody remembers their ancestors once a year, with incense, for one night, '
        'and finds it moving. I remember everybody continuously, without incense, and '
        'nobody has ever found that moving.',
        attach(
            'The week before Obon is chanting: the sutras, all of them, in shifts, so '
            'that the gates are open on the night. Monks do not sleep much that week. I '
            'am told sleep is restful and I have no way to verify the claim.',
            INNER_VISION,
        ),
        attach(
            'The night of Obon itself is quieter than people expect: the lanterns, the '
            'incense at the door, a household sitting up for somebody who died forty '
            'years ago. It is the one night of the year when I am not the only thing in '
            'the Empire keeping a record of the dead.',
            RAINY_MOON,
        ),
    ),
}
