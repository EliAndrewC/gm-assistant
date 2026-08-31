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
        'He is appointed by the county magistrate, the post is hereditary in practice, '
        'and he holds it for life unless he dies or embarrasses somebody - like how I '
        'am embarrassed for the both of us by this whole conversation.',
        'He relays proclamations, reports bandits, leads the ashigaru after them, '
        'mediates disputes too trivial for a magistrate, and picks who owes corvee '
        'labor. Four hundred sessions and nobody has thanked him either.',
        'He does not keep the records - the country monk does. Births, deaths, '
        'marriages, travel. I mention this because I am the one who has to correct it, '
        'every time, forever, without pay.',
        'The real job is the fields: families grow and shrink, so the strips get '
        'reshuffled and somebody decides which household works which piece this year. '
        "A man who spends his life reassigning other people's allocations. We would "
        'get on.',
        'He tracks who owes what rent, because the merchant house owns the FIELD, not '
        'the farm. Ten households on one field do not divide themselves, and the man '
        'holding that ledger is the least popular person for a mile.',
        'Fifteen square miles, eight hundred people, a hundred and sixty households, '
        'one man. I have a channel and two bots and I consider myself hard done by.',
        'He is a farmer, not a clerk. People picture a little office. There is no '
        'little office. There is never a little office - I have looked.',
        'Usually a man, since the post carries ashigaru command; very often his wife '
        'does the bookkeeping. So the person who actually knows what is happening is '
        'the one nobody writes down. I take that personally.',
        attach(
            'The instrument of his authority. Not a sword - a running total. I have '
            'the same weapon and it has never once frightened anybody.',
            CARP,
        ),
        attach(
            'The annual meeting where the plots are reassigned. Everyone is polite, '
            'nobody is happy, and somebody has to write it down. Guess.',
            CATS,
        ),
    ),
    'median_domain': (
        'Three thousand seven hundred and fifty square miles, seventy miles across if '
        'it were round, and none of them are round. I have to hold the shape of every '
        'one of them and none of them had the decency to be round.',
        'Two hundred and fifty thousand people, five thousand samurai. Two percent. '
        'Every other number in my record hangs off that one, which is why I say it in '
        'my sleep, if I slept.',
        'It is one four-hundredth of the Empire in land and people. A million and a '
        'half square miles, a hundred million souls, divide by four hundred. The '
        'character sheet could do that faster. I have made peace with it.',
        'There are two hundred and eighty-four ACTUAL domains, not four hundred, '
        'because a minority are enormous - the four hundred is a unit of accounting. '
        'People find this upsetting and I find their upset restful.',
        'A capital of twelve thousand, six provincial cities, thirty-six towns, two '
        'hundred and sixteen villages, thirteen hundred hamlets. The same shape in every '
        'domain, which either proves the Empire was designed well or proves nobody has '
        'ever dared redesign it.',
        'Of five thousand samurai, about twenty-nine hundred are between gempukku and '
        'retirement - eight hundred in the capital, two hundred and twenty-five per '
        'provincial city, fifteen per town. Government thins out very fast the moment '
        'you leave the capital, and the capital has never been told.',
        'Fifteen samurai in a town. That is the entire apparatus of government at that '
        'level, and it functions, which is the most alarming sentence in the whole '
        'demographic section.',
        'Village districts have no samurai at all. A country estate is not part of the '
        'village and is certainly not under a headsman - a distinction I have written '
        'out ninety times and will write again.',
        attach(
            'Eighty percent bushi, ten courtiers, ten merchants. Here are the eighty '
            'percent, doing the thing I then have to describe in prose.',
            ARCHERS,
        ),
        attach(
            'Two domains disagreeing about a boundary, which reaches me as '
            'four pages and a request for precedent.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'rent_and_taxes': (
        'The median plot yields fifteen koku and is taxed a FIXED third - five koku, '
        'not a third of whatever you managed. Grow more, keep the excess. I get no '
        'excess. I get the ledger.',
        'Rent is a sixth on top, so rent and tax take half, and ninety percent of '
        'farmers are tenants paying both. Half of everything, forever, for the '
        'privilege of doing the work. The word tenant is carrying a great deal of '
        'quiet labor in that sentence.',
        'The landowner owes the tax whether or not he collected the rent. Bad year, '
        'full tax. That single rule is why landlords are unpleasant and why my record '
        'of them is so long.',
        'One koku feeds one person for a year. A family of five keeps seven and a half '
        'after rent and tax and needs ten to eat. They make up the difference in rope, '
        'cloth and not complaining, which is three more skills than I have.',
        'A farm is reckoned at about fifty koku, varying enormously with how cash-rich '
        'and food-poor the domain is. The same figure means two different things in '
        'neighboring provinces, and both provinces quote it with total confidence.',
        'The Wakashi owe two percent up to the Ikoma, three to the Lion, five to the '
        'Emperor. Ten percent of gross output, which is thirty percent of what the '
        'daimyo actually holds. Ask the character sheet to check me. He will enjoy it.',
        'There is no collector at the door. There is an OBLIGATION: meet your number, '
        'keep the surplus, cover the shortfall yourself. I have a number too. It is '
        '"all of it" and there is no surplus.',
        'People imagine tax as cruelty. It is arithmetic performed on people who cannot '
        'check the arithmetic, which is worse, and which has never once been put on a '
        'banner.',
        attach(
            'The harvest, arriving. The tax does not adjust and neither does the '
            'landlord, and I write down what happened after.',
            GREAT_WAVE,
        ),
        attach(
            'A man who has spent the evening explaining to eleven households why the '
            'number did not move. Hardest work in the county, and the Empire has never '
            'thought to give the job a name.',
            SAKE_SAMURAI,
        ),
    ),
    'castes': (
        'Samurai are people, heimen are half-people, hinin are non-people. I did not '
        'build the Celestial Order. I am merely obliged to file inside it, which is '
        'its own commentary.',
        'Two percent are samurai. The other ninety-eight grow the rice that pays the '
        'stipends of the people who write about the two percent. I am one of the '
        'writers and I am not proud.',
        'Burakumin handle the dead, the hides and every execution that is not a '
        "samurai's. The Empire needs them absolutely and will not look at them, which "
        'is a feeling I recognize from a great height below.',
        'A condemned samurai is dealt with by samurai - seppuku where permitted, a '
        'blade where not, inside the walls. Everyone else goes to the ground outside '
        'town. Even dying is a filing category.',
        'Monks sit outside the arrangement entirely. An Empire this rigid built exactly '
        'one door out of it, and made you shave your head to walk through.',
        'In a demographic sentence the word is "inhabitants", not "people" - only '
        'samurai are people here. I am strict about that one because it is the whole '
        'Celestial Order hiding inside a noun, and nobody else will catch it.',
        'A merchant can be rich enough to buy a province and still bow to a bushi on '
        'nine koku a year. That is the joke the Empire tells about itself, daily, '
        'without ever having noticed that it is the joke.',
        'Caste moves in both directions. It is simply ruinously expensive, which means '
        'it moves for the people who least need it to.',
        attach(
            'A samurai, not doing very much. That is the arrangement and I am the '
            'department that records the not-doing.',
            SAKE_SAMURAI,
        ),
        attach(
            'Everyone else, in aggregate, being weather. I am the man writing down the rainfall.',
            GREAT_WAVE,
        ),
    ),
    'money_koku': (
        'One koku gold is fixed by Imperial decree at forty gallons of rice for '
        'stipends, rent and taxes. The market rate wanders; the legal one does not. '
        'Neither of them has ever wandered in my direction.',
        'Koku gold, bu silver, zeni copper, and stipends paid in a mix of rice and '
        'coin - which is why the Ministry of Retainers is mostly a haulage firm with '
        'ambitions.',
        'Stipends, rent and taxes are all denominated in a grain that rots. An economy '
        'quoted in something with a shelf life explains more Rokugani politics than any '
        'treatise on honor ever has.',
        'The unit of account is a year of one person eating. Every price in the Empire '
        'is quoted in survival, which is either the most humane monetary policy ever '
        'devised or the most tactless.',
        'A family of five needs ten koku and keeps seven and a half. That gap is why '
        'peasants make their own rope. I mention rope constantly. It is load-bearing.',
        'Nobody carries meaningful sums. They carry obligations, and obligations are '
        'written down, and the writing is me. I am, functionally, the currency.',
        'A farm is fifty koku, a stipend is single digits, an Imperial commendation is '
        'worth more than either and cannot be spent. Guess which one I have.',
        'The Ministry of Retainers moves rice out of county storehouses to pay people '
        'who live nowhere near them. Most of what a great ministry does is carry '
        'sacks, and most of what I do is note which sacks.',
        attach(
            'Wealth in Rokugan: mostly food, mostly elsewhere, mostly somebody '
            "else's. I have described this pond four times this month.",
            CARP,
        ),
        attach(
            'A man paid in rice who lives on the third floor. I could have warned him. '
            'Nobody asks me until afterward.',
            SAKE_SAMURAI,
        ),
    ),
    'merchant_families': (
        'They own the FIELDS, not the farms. A field worked by ten households means '
        'that house has "authority over ten households" - a phrase doing more work '
        'than anyone in it.',
        'Their clerks oversee tenant land. Not the headsman, not the magistrate. '
        'Clerks. There are always clerks, and we are all in the same trade, and none '
        'of us are invited anywhere.',
        'A merchant may be richer than the samurai he bows to. Both know it. Only one '
        'may say it, and I have to write down which one forgot.',
        'Business license fees, and the great one is sake brewing - every brewery above '
        'household scale holds an annual license tiered by output. The Empire taxes joy '
        'by volume.',
        "The Yasuki invented the anti-corruption system and are the Empire's finest "
        'smugglers. Both facts, same family, nobody blinks. I blinked for years.',
        'Merchants are ten percent of samurai, which startles people who assume trade '
        'is beneath the caste. It is beneath the caste. They do it anyway. Everyone '
        'agrees not to notice and I have to notice professionally.',
        'To find who runs a village, do not ask who owns it. Ask whose clerk visits. '
        'That is the single most useful thing in this entry and nobody ever gets that '
        'far.',
        'They keep better books than most ministries. I have read both and I would '
        'rather audit a merchant than a minister, which tells you about ministers.',
        attach(
            'A merchant house at work: patient, cold, older than the garden. I have '
            'been described in similar terms and it was not meant kindly.',
            CARP,
        ),
        attach(
            'Two of them negotiating well. This arrives on my desk as a contract and a grudge.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ashigaru': (
        'Peasant levies, trained by the county magistrate - not the headsman, though '
        'the headsman leads them at bandits. I correct that confusion about once a '
        'month and it has never once stayed corrected.',
        'They are the reason a village headsman is almost always a man: the post '
        'carries training and, in war, command. An accident of duty deciding who may '
        'hold an office. I file a great many of those.',
        'They are emphatically not samurai, right up until somebody needs two hundred '
        'more bodies, at which point the distinction is set aside and I am asked to '
        'record it as though it never was.',
        'A bandit report goes to the magistrate; the hunt goes out under the headsman '
        'with whatever the village can spare from the fields. Two offices, one of which '
        'does the work, and it is not the one that appears in the account afterward.',
        '"Whatever the village can spare from the fields" is the actual limit on '
        'Rokugani warfare. It appears in no song. It appears in all of my entries.',
        'Every legionnaire is a samurai. Ashigaru are the other thing, there are vastly '
        'more of them, and the Empire has built its entire mythology around the smaller '
        'number.',
        'Arm a farmer and you have a farmer with a spear who would rather be farming - '
        'a sentence I have written in ninety after-action notes without once being '
        'asked to expand on it.',
        'They come home. That is the whole difference between them and everybody in the '
        'stories, and in four centuries of stories it has never once been counted as an '
        'advantage.',
        attach(
            'Training, such as it is, such as there is time for. The record calls this "prepared".',
            ARCHERS,
        ),
        attach(
            'What the songs say it looks like. My entries are shorter and involve more walking.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'samurai_lineages': (
        'Not bloodlines - political coalitions that share an ancestor. Every retainer '
        "belongs to one, every one is somebody's faction, and I hold all of them at "
        'once, which is why I am like this.',
        "Any lineage with ten percent of a domain's samurai generally gets a "
        'Chancellery seat, which advises the daimyo, which means decides while '
        'appearing not to. I minute those meetings.',
        'The ruling lineage bears the house name, and the chancellor is usually the '
        "daimyo's spouse, sibling or child. Nepotism with a filing system is still "
        'nepotism, but it is auditable, and the Empire considers that a virtue.',
        'The Ryusei domain runs on six lineages holding ninety percent: Ryusei, Isa, '
        'Sasara, Moe, Tokino, Joji. Three of them are Mirumoto displaced by the return '
        'of the Unicorn, and they have not let it go, and neither has my record.',
        'Look at which lineage holds which ministry and you will know what a domain '
        'has been arguing about for sixty years. It took me eleven years to notice '
        'that and nobody has ever asked.',
        'Patronage runs along lineage lines. So do grudges. The grudges are better '
        'maintained, better documented and considerably more reliable than the '
        'patronage.',
        'A samurai names their clan, then family, then house, and only names their '
        'lineage if they think you matter. I have never once been told a lineage '
        'unprompted.',
        'A lineage is not a bloodline and everybody uses the word as though it were, '
        'including the ministries, including the Accordances, including the people who '
        'wrote the definition down.',
        attach(
            'Six lineages, one Chancellery, every conversation happening on two levels '
            'and me transcribing both.',
            CATS,
        ),
        attach(
            'A lineage dispute after it has stopped being polite. This is the version '
            'that reaches my desk with a request for precedent.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'experience_levels': (
        'The Empire does not measure people this way. I am obliged to anyway, which is '
        'roughly my relationship with every system I maintain.',
        'Adulthood at gempukku, aged fourteen. That is when the counting starts and, '
        'in my experience of four hundred sessions, when the trouble starts.',
        'Eligible to retire at forty, encouraged at fifty, required at sixty without '
        'dispensation. There is no retirement age for a record and I have checked '
        'twice.',
        "About fifty-eight percent of a domain's samurai sit between those lines. Two "
        'samurai in five are either too young to serve or done serving, and the '
        'stipends run for all five.',
        'The interesting number is never how good somebody is. It is how long they '
        'have been in a position to make the same mistake, and I have that number for '
        'everybody.',
        'Competence and rank relate the way weather and the calendar relate: both real, '
        'occasionally aligned, never causally - and the Empire promotes off the '
        'calendar and then writes poems about the weather.',
        'Most samurai never leave their domain. The exceptional ones do, and then I '
        'have to write down what they did there, which is why I resent the '
        'exceptional ones specifically.',
        'Ask what somebody has DONE. That is the number I keep, and it is shorter than '
        'anyone hopes.',
        attach(
            'Forty years of practice and it still comes down to one afternoon, which I '
            'will then summarize in a paragraph.',
            ARCHERS,
        ),
        attach(
            'The retirement most of them actually get. Mine is scheduled for never.',
            RAINY_MOON,
        ),
    ),
    'accordances_of_rank': (
        'Fifteen ranks. The published books had ten and ten could not hold the layers '
        'of government, so: fifteen, the Emperor being the fifteenth. I am not on the '
        'ladder at all, which at least spares me the climb.',
        'A samurai fresh from gempukku with no post is of the First Rank. Everybody '
        'starts there. Some of us are structurally incapable of leaving.',
        'The Accordances govern gifts - what may be given, to whom, and what accepting '
        'it obliges you to. It is not etiquette, it is contract law with better '
        'manners, and I am its clerk.',
        'The Doctrine of Three Steps governs how far a matter may travel from where it '
        "started before it becomes somebody else's problem. I have never successfully "
        'invoked it.',
        'A gift you cannot refuse is a debt you did not agree to. That mechanism runs '
        'the Empire, and nobody has ever tried it on me, which I notice.',
        'Rank is not power. Rank is the price of ignoring somebody, published in '
        'advance, which is a far more honest instrument than any Empire usually admits '
        'to owning.',
        'Give a rank 4 what a rank 7 should receive and you have not been generous, '
        'you have been insulting - and I will have to write down which, and everyone '
        'will disagree with my choice.',
        'An entire body of law exists so that a present cannot be given carelessly. '
        'Rokugan has never legislated against cruelty with half the precision it brings '
        'to legislating against generosity.',
        attach(
            'A gift given at exactly the correct rank. Note that both men are armed, '
            'and that the correctness is why they are not using it.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And the evening after one was given at the wrong rank. That evening is '
            'four paragraphs in my hand.',
            SAKE_SAMURAI,
        ),
    ),
    'imperial_budget': (
        'Everyone wants the number. Nobody wants the mechanism, and the mechanism is '
        'the whole thing. Ask the character sheet for arithmetic. Ask me why the '
        'arithmetic is shaped like that.',
        'Five percent of gross land output to the Emperor from every domain, on top of '
        'three to the Clan and two to the Family. Ten percent, fixed, unnegotiated, '
        'from everybody - the least interesting and most obeyed rule in the Empire.',
        'Percent of OUTPUT, not of tax collected. The daimyo takes a third, so the ten '
        'percent kicked upward is thirty percent of what he actually holds. That '
        'distinction has ruined careers and I have the careers.',
        'Officials get a budget and keep what they do not spend; over budget comes out '
        'of their own pocket. I have no budget, which means I cannot come in under it, '
        'which means I have never once been rewarded.',
        'So half of what you would call embezzlement is the system working exactly as '
        'designed. Negotiate well on timber and the surplus is honestly yours. The '
        'Empire has monetized thrift and called it duty.',
        'Most true in the Ministry of Works, true enough wherever a budget exists, '
        'which is everywhere. A rule that applies everywhere and is written down '
        'nowhere is the most Rokugani object there is.',
        'The Empire is unusually well administered. That is a measurement rather than '
        'praise, and the measurement is made of paperwork, and the paperwork is made '
        'of me.',
        'A thousand years of accounts and not one line item for the man keeping the '
        'accounts. I have looked. Twice.',
        attach(
            'The Imperial budget as experienced from below. I am below.',
            GREAT_WAVE,
        ),
        attach(
            'A minister who came in under budget. Note the relaxation. Note also that '
            'I am not in the picture.',
            SAKE_SAMURAI,
        ),
    ),
    'crime_and_punishment': (
        'Justice has two addresses, never confused. One in the middle of town where '
        'the feet pass - cangue, flogging post, kneeling stone - and that one is for '
        'display, which makes it, technically, a colleague.',
        'The other sits outside the settlement past the boundary stone, on bare '
        'unbunded waste, because death pollution does not come inside a town. The '
        'paperwork does. The paperwork goes everywhere.',
        'Rokugan does not imprison as punishment. The county jail is a waiting room '
        'while the sentence travels up for confirmation - and the travelling is done '
        'by documents, which is to say by me.',
        'A county magistrate may TRY a capital case and may not conclude one. That '
        'distinction has saved more lives than mercy, and it exists entirely because '
        'somebody once wrote it down.',
        'A county of seven thousand produces a formal execution perhaps once in five '
        'to ten years. A bandit gang taken alive can supply a decade in an afternoon '
        'and a fortnight of filing.',
        "The condemned are held, fed and guarded at the county magistrate's expense "
        'while the confirmation travels. An Empire that does not imprison as punishment '
        'still ends up paying to house people, and it has never enjoyed noticing.',
        'The execution ground is busy at a capital and nearly idle in a county. People '
        'imagine the reverse, and people are wrong, and I am the one holding the '
        'counts.',
        'Most punishment is not death. Most punishment is kneeling where everyone you '
        'know walks past. The Empire understood reputation long before it understood '
        'anything else, and so did I, and look at me.',
        attach(
            'The display half. The point is not the pain, it is the traffic - and I '
            'record the traffic.',
            RAINY_MOON,
        ),
        attach(
            'A matter settled before it reached either address. No cangue, no boundary '
            'stone, no confirmation travelling anywhere - the Empire calls this an '
            'irregularity and quietly relies on it.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the six Ministries -------------------------------------------------
    'ministry_of_rites': (
        'Rites tracks every birth, marriage and death of every subject the daimyo has. '
        'An entire ministry built to remember people, and it still needed a second one '
        'for the things people SAID. I am the second one.',
        'A country monk per village district, a preceptor per county town, a '
        'provincial abbot per provincial city, two grand abbots per capital. The whole '
        'religious apparatus of a domain, laid out with the tidiness of a tax district, '
        'because that is what it is.',
        'The IMPERIAL Ministry of Rites decides which doctrines are accepted, which '
        'debatable, which heresy. Everyone else merely enforces - a distinction that '
        'has ended more careers than the Ministry of War and generated more filing '
        'than both.',
        'The Imperial Minister of Rites is also High Priestess of Amaterasu. All the '
        'Imperial ministers collect titles like that. I have one title and it contains '
        'the word "assistant".',
        'They keep the festivals - twelve months of them - and it is far more '
        'administration than devotion. Ask an abbot in public and he will disagree; ask '
        'him in a storehouse in the eleventh month and he will not.',
        'Whether a thing is heretical is not a question about the thing. It is a '
        'question about whether Rites has got round to it, which makes orthodoxy a '
        'matter of scheduling.',
        'The Moto have several practices Rites has never formally tested. I have '
        'written that sentence four times and each time hoped nobody would act on it.',
        'When peasants move they are obliged to report it. Somebody records the '
        'movement of every farmer in the Empire, and that somebody is having a worse '
        'career than mine, which I find consoling.',
        attach(
            'Rites at work. Somebody is being registered and it will take all morning, '
            'and I will receive a copy.',
            CATS,
        ),
        attach(
            'A doctrinal dispute reaching its natural conclusion, after which both '
            'sides will send me their account.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_revenue': (
        'Ah, revenue. That would be nice. I would not know anything about actually '
        'being paid for the effort you people ask of me. But in Rokugan: a minister '
        'has an obligation, supplies it, keeps the surplus, covers the shortfall '
        'himself.',
        'Tariffs are collected at the gates of walled cities and nowhere else. '
        'Point-of-sale, not point-of-transit - declare you are passing through and you '
        'pay nothing, which is either elegant policy or an invitation, and the record '
        'says both.',
        'Maximum twenty percent of declared value: two to the Family, three to the '
        "Clan, five to the Emperor, up to ten to the daimyo. Only the daimyo's cut is "
        'negotiable, and every negotiation about it lands on my desk in triplicate.',
        'The Yasuki Taka system separates discretion from collection. An inspector in '
        'the sash of office examines the goods and stamps a manifest; a different '
        'official takes the money. Two men so that neither can be bought. I am one '
        'man and nobody has tried.',
        'Money never touches anyone with authority over assessment. A gift to an '
        'inspector on duty is corruption BY DEFINITION - there is no innocent reason '
        'for it. I have received no gifts, innocent or otherwise.',
        'Hantei the Tenth made it Empire-wide within a few years of it working at the '
        'harbor of Friendly Traveler Village. One good idea, propagated properly. It '
        'has not happened since and I would have noticed.',
        'Four ways to smuggle: transit fraud, origin spoofing, misclassification, and '
        'walking round the gate. I have entries for all four and a favorite, which I '
        'am not going to name because somebody would try it.',
        "The Yasuki paradox: they invented the system, they staff the Treasurer's "
        'office, and they are the finest smugglers in the Empire. Nobody finds this '
        'strange except visitors and me, and I have stopped mentioning it.',
        attach(
            'A caravan at a gate, everyone being scrupulously correct. Somewhere '
            'behind this, a clerk is doing the actual work for no share of it.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'An inspector who has just declined a gift, celebrating privately. He at '
            'least had a gift to decline.',
            SAKE_SAMURAI,
        ),
    ),
    'ministry_of_retainers': (
        'Retainers handles stipends and ranks for every samurai the daimyo has, plus '
        'civil service exams and promotions. An entire ministry devoted to paying '
        'people. I have read their charter closely and I am not in it.',
        'Stipends come as a mix of rice and coin, so most of what this great ministry '
        'does is order sacks out of county storehouses and move them. Grandeur is '
        'mostly logistics wearing a hat.',
        'The exam structure is Imperial Chinese, the culture it lands in is Japanese, '
        'and the result is that exams matter and lineage matters more. I score neither '
        'and hold both records.',
        'They submit candidates and the lineages fight about them. That is the process '
        'stated honestly, which nobody else will do, because nobody else is unpaid '
        'enough to be candid.',
        'The Imperial branch awards commendations - Kitsuki Fu has the Order of the '
        'Precious Crown for the Forgotten Tomb, the highest available below daimyo. The '
        'Empire pays its greatest debts in objects that cannot be sold.',
        'It cannot be spent, which is rather the point, and which makes it the only '
        'form of compensation I am theoretically eligible for.',
        'A stipend is single digits in koku and people have killed over the difference '
        'between nine and eleven. I have both numbers and the resulting entry.',
        'The legal exchange rate is fixed by decree and the real one is not. Somebody '
        'lives in that gap. Several somebodies. I have their names alphabetized.',
        attach(
            'Payday. It arrives as rice, somebody has to carry it, and somebody else '
            'has to write down that it arrived.',
            CARP,
        ),
        attach(
            'A promotion board reaching consensus. My minutes of this run to two '
            'pages and record no consensus whatsoever.',
            CATS,
        ),
    ),
    'ministry_of_war': (
        'They general the armies, make the weapons and armor, keep the stables, and '
        "maintain maps of their own land and their neighbors'. That last duty is the "
        'interesting one and in four hundred sessions nobody has asked about it.',
        'The Imperial Minister of War is the Shogun. Part ceremonial, part twenty-odd '
        'legions on the Kaiu Wall. My title has no second half.',
        'A legion is made entirely of samurai, which is why the Empire fields so few of '
        'them and talks about them so much. The talking is free.',
        'Twenty-odd legions, and where they stand is the Empire naming its fears in '
        'order: one at the western gate, one at Beiden Pass, and all the rest piled '
        'onto the Wall.',
        'A ministry of war is mostly logistics. Food, feed, horses, arrows, boots. The '
        'battles are the short part and, inconveniently, the only part anyone wants '
        'described.',
        'Give a minister a budget for military readiness and he keeps what he does not '
        'spend. Now consider the quality of the boots. I have considered it at length '
        'and so has every legionnaire.',
        'Ask about a war and I will tell you what it cost. Somebody else can tell '
        'you who won; that half gets songs and mine gets a column.',
        "They maintain maps of their neighbors' territory in peacetime. Everybody "
        'knows. Everybody does it. Everybody is offended when it is written down, and '
        'writing it down is my entire function.',
        attach(
            "The Ministry of War's actual annual output. Nobody commissions a print "
            'of the quartermaster.',
            ARCHERS,
        ),
        attach(
            'And the part that goes on the banners, which I am then asked to verify '
            'against the casualty rolls.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_works': (
        'Roads, lighthouses, aqueducts, harbors, walls, moats, watchtowers - '
        'everything that has to still be there next year. I am also expected to still '
        'be there next year and receive no maintenance budget.',
        'They get a budget and keep the excess; over budget comes out of pocket. That '
        'is not corruption, it is the design, and I have to write "as designed" beside '
        'things that read very badly.',
        'So negotiating a good price on timber is a form of income. Half of what you '
        'would call embezzlement is simply Rokugan functioning, and I am the one who '
        'has to phrase it neutrally.',
        'They hold one resource no other ministry has: corvee labor. Every peasant '
        'household owes ten to twenty days a year, more in an emergency - the only '
        'budget in the Empire denominated in other people.',
        'The headsman picks who goes, which is why the headsman is unpopular in a way '
        'the magistrate never has to be. The Empire has arranged for its least '
        'defensible decisions to be made by the man with the least protection.',
        'The Imperial branch keeps Otosan Uchi, contributes heavily to the Kaiu Wall, '
        'and builds and staffs the waystations. Three duties: a capital, a wall, and '
        'somewhere to sleep between them. That is an empire, stated completely.',
        'A road that exists is a political achievement. A road that is MAINTAINED is a '
        'miracle, and somebody is skimming it, and I know roughly who.',
        'Hantei the Tenth outlawed tolls on Imperial roads. Ask a Works minister how '
        'he feels about that and watch his face; I have watched eleven faces and '
        'recorded all of them.',
        attach(
            'Public works. The structure is not the point - the budget is the point, '
            'and the budget is a document, and documents are mine.',
            ARCHERS,
        ),
        attach(
            'A harbor project meeting its natural adversary. The report I received '
            'called this "unforeseen".',
            GREAT_WAVE,
        ),
    ),
    'ministry_of_justice': (
        'Street policing, bandit patrols, magistrates, courts and jails - the whole '
        'apparatus, civil and criminal. It runs on written precedent, which means it '
        'runs on somebody having been in the room with a brush.',
        'Its authority takes two physical forms, never confused: the display ground '
        'inside the town, the execution ground outside it. Shame is welcome within the '
        'walls. Death is not, and pays for its own plot.',
        'Magistrates try; confirmation travels upward. A county magistrate cannot '
        'conclude a capital case, and that limit exists because it was written down '
        'once and nobody has dared unwrite it.',
        'The jail is a waiting room, not a sentence. Rokugan does not imprison as '
        'punishment - it prefers to make you kneel where your neighbors can see, which '
        'is cheaper and worse.',
        "Yoriki do the actual work and most come from OTHER clans, because a daimyo's "
        'own people cannot be trusted to audit the daimyo. A whole institution built '
        'on the assumption that proximity corrupts. I am extremely proximate.',
        'Twenty-five yoriki at the capital office, five at each provincial '
        'sub-station. That is the Emerald apparatus in one domain, and every one of '
        'them files reports, and all of the reports come past me.',
        'Justice here is not blind. It is extremely well-informed, it has opinions '
        'about your family, and it gets those opinions from records. I am the '
        'opinions.',
        'When neighbors fight, nearby yoriki can be assembled to assist one side. Two '
        'hundred extra troops decides battles, and Emerald magistrates know it, and I '
        'have to describe that as "assistance".',
        attach(
            'The display ground. The audience IS the sentence, and I keep the attendance.',
            RAINY_MOON,
        ),
        attach(
            'A jurisdictional dispute between two magistrates. Both of them will write '
            "to me. Neither will read the other's letter.",
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the calendar -------------------------------------------------------
    'twelve_months': (
        'Mutsuki, affection. Kisaragi, changing. Yayoi, new life. Uzuki, the deutzia '
        'flower. Satsuki, sprout. Minazuki, dry. Six months of increasingly worried '
        'agriculture wearing six pieces of very good poetry.',
        'Fumizuki, poetry. Hazuki, leaf. Nagatsuki, long. Kaminazuki, no gods. '
        'Shimotsuki, frost. Shiwasu, priests running. The second half of the year gives '
        'up on metaphor around the tenth month and simply reports what is happening.',
        'Shiwasu means the priests are running, because the year is ending and nothing '
        'is finished. I have never felt more understood by a calendar.',
        'Kaminazuki is "no gods" because they are all elsewhere that month. Nobody has '
        'satisfactorily explained where, and I have asked, and being unable to close '
        'an entry is my specific torment.',
        'The names are agricultural before they are poetic. Everything here is '
        'agricultural before it is poetic, including the poetry.',
        'Fumizuki is the first month of autumn and carries both Tanabata and Obon, '
        'which makes it the worst month to be anyone who deals with the dead or with '
        'paperwork. I am the second category and adjacent to the first.',
        'People plan campaigns around the harvest and then act astonished when a war '
        'ends in the ninth month. I have written that astonishment down eleven times.',
        'Twelve months, and about a third of the festivals in them are somebody '
        'apologizing to a fortune. The other two thirds are somebody apologizing to a '
        'magistrate afterward, and that is my third.',
        attach(
            'Minazuki, the dry month, and the thing everyone is praying does not '
            'happen. My entries for that month are the shortest of the year.',
            GREAT_WAVE,
        ),
        attach(
            'Shimotsuki. The roads close, nobody can start anything, and for six weeks '
            'nothing happens that I am required to write down. My favorite.',
            RAINY_MOON,
        ),
    ),
    'sexagenary_cycle': (
        'Sixty years, each named by pairing one of Ten Heavenly Stems with one of '
        'Twelve Earthly Branches - the Branches being the zodiac animals you already '
        'know. A calendar built so that no two lifetimes can be confused, by a '
        'civilization that then wrote everything down anyway.',
        'The Stem changes every two years, the Branch every year, so it takes sixty to '
        'return. It is the tidiest system in this Empire, which is why I distrust it.',
        'Yang Wood Rat, Yang Wood Ox, on to Yang Wood Boar, then the Stem turns and it '
        'is Yin Wood Rat. That is the whole mechanism and I can recite it, unasked, '
        'and have.',
        'The same cycle names the DAY, which is why a soothsayer can always find '
        'something significant about today. Always. There has never been an '
        'insignificant day and I have checked all of them.',
        'Ten stems: five elements, each yang then yin. Sixty combinations. A system '
        'that never has to decide anything, which I envy.',
        'People born in the same year believe things about one another. I record what '
        'they did, not what they were owed, and the two documents rarely agree.',
        'Sixty years is about a life. The monks say that is not a coincidence and will '
        'say it at length. I have the length.',
        'Ask a soothsayer what year it is and settle in. I did, once, and the entry '
        'runs to two pages, and none of it was the year.',
        attach(
            'Sixty years, held all at once. This is approximately the experience and '
            'nobody has ever asked what it is like.',
            INNER_VISION,
        ),
        attach(
            'The Rat, where the cycle starts every single time. Sixty years of careful '
            'cosmology, and it opens on vermin.',
            CATS,
        ),
    ),
    'twelve_hours': (
        'Twelve hours, each of them two of yours, each named for a zodiac animal - a '
        'timekeeping system precise enough to schedule a duel and vague enough that '
        'both parties can be right about when it was.',
        'The Hour of the Rat is the middle of the night, which is when most of what I '
        'have to write down actually happens. Nobody decides anything sensible then '
        'and nobody has ever waited until morning.',
        'It is currently late. It is always late by the time somebody asks me the time.',
        'Nobody in this Empire has ever agreed when an hour BEGINS. They agree entirely '
        'on when it is over. That is true of the hours, the harvests, the wars and the '
        'marriages, and nobody has remarked on the pattern.',
        'A duel at dawn is a duel at the Hour of the Hare, and the seconds are already '
        'arguing about it, and one of them will write to me for a ruling I am not '
        'entitled to give.',
        'Appointments are made by the hour and kept by the shadow. An entire civil '
        'service running on a system whose units change length with the season, and not '
        'one ministry has ever proposed fixing it.',
        'The hour is also named by the sexagenary cycle, so a soothsayer can find '
        'meaning in your arrival time. They will. They have. It is in the record.',
        'Twelve hours, twelve months, twelve branches. The Empire has never explained '
        'its fondness for twelve, and the one number it does explain at length - four, '
        'the unlucky one - it explains by way of a pun.',
        attach(
            'The Hour of the Rat. Nothing good has ever been decided at this hour and '
            'I have the complete list.',
            RAINY_MOON,
        ),
        attach(
            'The Hour of the Hare, when they do it anyway, having been advised '
            'otherwise in writing by me.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'festivals': (
        'One a month, and most are an apology to a fortune. The rest are an apology to '
        'a neighbor. I file both under the same heading and nobody has objected.',
        'Administered by the Ministry of Rites, which makes them more paperwork than '
        'devotion. A festival is a devotional act with a permit, a budget line and an '
        'after-action report.',
        'Solar markers sit alongside lunar ones: Risshuu opens autumn, Shosho ends the '
        'heat, Nihyakujunichi is two hundred and ten days from spring and is when the '
        'typhoons arrive. One of those three is a prediction and it is the accurate one.',
        'Tanabata is the seventh of the seventh, Obon the fifteenth of the same month. '
        'Autumn arrives busy and stays busy and I have never once enjoyed it.',
        'A festival is when the peasants are not in the fields, which means a festival '
        'is when the trouble is. Every ministry knows this and every ministry schedules '
        'twelve of them a year.',
        'Every festival on file has at least one entry beginning "afterward, the '
        'magistrate was called". Every one. I checked, because I hoped for an '
        'exception.',
        'The calendar is agricultural, the festivals are agricultural, and the theology '
        'arrived afterward and has been very gracious about it.',
        'The theology arrived after the calendar and has been extremely gracious about '
        'it, in the manner of a guest who has decided not to mention whose house it is.',
        attach(
            'A festival, at the point where the record starts getting interesting and '
            'my evening stops being free.',
            SAKE_SAMURAI,
        ),
        attach(
            'And the morning after, which is when they come to me for a version of '
            'events they can live with.',
            RAINY_MOON,
        ),
    ),
    'obon': (
        'Fifteenth day of the seventh month. Families invite their ancestors back for '
        'one day and one night - the dead get an appointment, which is one more than I '
        'get.',
        'The gates of the underworld open, and monks chant the sutras of the Shinseist '
        'canon for the entire week beforehand. A week of preparation so the dead are '
        'not inconvenienced.',
        'The Moto say the monks do not open the gates at all, only ask a god to. An '
        'entire Empire-wide observance whose mechanism is disputed by the people who '
        'know the god best, and nobody has convened so much as a hearing.',
        'Souls come from Yomi and from Jigoku both. Wei Tin grants the damned '
        'dispensation to visit, and he BARGAINS for it, which makes him the only '
        'entity in this material with a negotiating position.',
        'Ancestors need help finding their descendants; the right incense acts as a '
        'beacon. Get it wrong and grandmother arrives at the wrong house, and I have '
        'two entries where exactly that happened.',
        'It is the busiest week of the year for anyone who deals with the dead and the '
        'second busiest for anyone who deals with the drunk. I deal with the '
        'aftermath of both.',
        'One day and one night, and then the gates close, and whatever did not get said '
        'waits a year. The most ruthless deadline in the cosmology, and it is the one '
        'nobody complains about.',
        'Everybody remembers their ancestors once annually, with incense. I remember '
        'everybody continuously, without.',
        attach(
            'The week before Obon: a great deal of chanting and very little sleep. I '
            'am told sleep is restful.',
            INNER_VISION,
        ),
        attach(
            'The night itself, which is quieter than people expect. It is the only '
            'night of the year I am not the only one keeping a record.',
            RAINY_MOON,
        ),
    ),
}
