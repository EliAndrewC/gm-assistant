"""Setting mechanics, the six Ministries, and the calendar. GM Assistant only.

SHAPE OF EVERY LINE (FR-002): annoyance first, then a real fact from `l7r.md`.
A line that is only annoyed fails the requirement; so does one that is only
informative. He is a scribe being made to explain his own filing system.

Facts are lifted at authoring time. The box has no copy of the notes, so a fact
that later changes in `l7r.md` will not change here - accepted by the GM
explicitly, since this material does not move often.
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
        'Ugh. Village headsmen. Fine. He is appointed by the county magistrate, the '
        'post is de facto hereditary, and it is a lifetime appointment unless he dies '
        'or embarrasses somebody.',
        'You want to know what he DOES. He relays proclamations, reports bandits, '
        'leads the ashigaru who go after them, mediates disputes too trivial for a '
        'magistrate, and picks who owes corvee labor this year. Nobody thanks him.',
        'He does not keep the records. That is the country monk - births, deaths, '
        'marriages, travel. Everybody gets this wrong and everybody gets it wrong at '
        'me specifically.',
        'The real job is the fields. Families grow and shrink, so the strips get '
        'reshuffled, and somebody has to decide which household works which piece of '
        'which field this year. That somebody is him.',
        'He tracks who owes what rent, because the merchant house owns the FIELD, not '
        'the farm, and a field worked by ten households does not divide itself.',
        'A village district is about fifteen square miles and eight hundred people in '
        'a hundred and sixty households. One man oversees all of it. Hamlets do not '
        'get their own.',
        'He is still a farmer. Not a clerk. People imagine a little office and there '
        'is no little office - there is a man with a larger family and a stipend that '
        'means he does not have to be in the field every hour.',
        'Usually a man, because the post carries ashigaru training and command. Very '
        'often his wife does the bookkeeping, which is to say very often his wife does '
        'the part that matters.',
        attach(
            'This is the actual instrument of his authority. Not a sword. A running '
            'total of who owes what, which is the same thing more slowly.',
            CARP,
        ),
        attach(
            'And this is the meeting where the plots get reassigned. Everybody is '
            'polite. Nobody is happy. It happens every year.',
            CATS,
        ),
    ),
    'median_domain': (
        'The median domain. Right. Three thousand seven hundred and fifty square '
        'miles, about seventy miles across if it were round, and none of them are '
        'round.',
        'Two hundred and fifty thousand people, five thousand of them samurai, which '
        'is two percent, which is the number everything else is built on.',
        'It is one four-hundredth of the Empire in both land and people. The Empire is '
        'about a million and a half square miles and a hundred million souls. Divide '
        'either by four hundred and there you are.',
        'There are two hundred and eighty-four actual domains, not four hundred, '
        'because a minority of them are enormous. The four hundred is a unit of '
        'accounting. People find this upsetting and I find their upset restful.',
        'A capital of twelve thousand, six provincial cities, thirty-six towns, two '
        'hundred and sixteen villages, thirteen hundred hamlets. That is the shape of '
        'every domain you will ever visit.',
        'Of the five thousand samurai, about twenty-nine hundred are between gempukku '
        'and retirement. Eight hundred in the capital, two hundred and twenty-five in '
        'each provincial city, fifteen in each town.',
        'Fifteen samurai in a town. That is the whole apparatus of government at that '
        'level. Think about that before you tell me the Empire is oppressive.',
        'Village districts have no samurai at all. A country estate is not part of the '
        'village and is most certainly not under a headsman.',
        attach(
            'Eighty percent bushi, ten percent courtiers, ten percent merchants. Here '
            'are the eighty percent, doing what the eighty percent do.',
            ARCHERS,
        ),
        attach(
            'And this is what happens when two domains disagree about where the line '
            'is. It is in the record four hundred times.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'rent_and_taxes': (
        'Taxes. Wonderful. The median family plot yields about fifteen koku a year and '
        'is taxed at a third - a FIXED third, five koku, not a third of whatever you '
        'managed. Grow more and you keep the excess.',
        'Rent is a sixth on top, so rent and tax together take half. About ninety '
        'percent of farmers are tenants, so about ninety percent of farmers pay both.',
        'The landowner owes the tax whether or not he collected the rent. Bad year, '
        'full tax. That is the entire reason landlords are unpleasant.',
        'One koku feeds one person for a year. Forty gallons. A family of five keeps '
        'seven and a half after rent and tax, and needs about ten just to eat, which '
        'is why they also make their own rope.',
        'Yes, the arithmetic is grim. No, it is not a mistake. They make up the '
        'difference in cloth, rope, charcoal and not being ill.',
        'A farm is reckoned at about fifty koku of value, with enormous variation '
        'depending on how cash-rich and food-poor the domain is that year.',
        'The Wakashi of the Ikoma owe two percent up to the Family, three to the Clan, '
        'five to the Emperor. Ten percent of gross output, which is thirty percent of '
        'what the daimyo actually collects.',
        'Everyone imagines tax collectors. What there actually is, is an obligation: '
        'meet your number, keep the surplus, cover the shortfall yourself.',
        attach(
            'A bad harvest arriving. The tax does not care and neither does the landlord.',
            GREAT_WAVE,
        ),
        attach(
            'This is what a man looks like the evening after he has explained to '
            'eleven households why the number did not change.',
            SAKE_SAMURAI,
        ),
    ),
    'castes': (
        'The castes. Samurai are people. Heimin are half-people. Hinin are '
        'non-people. I did not design it and I am obliged to record it accurately.',
        'Two percent samurai. Everyone else is doing the actual work, and the actual work is rice.',
        'Burakumin handle the dead, the hides and the executions. Every execution that '
        "is not a samurai's is theirs. The Empire needs them and will not look at "
        'them.',
        'A condemned samurai is dealt with by samurai - seppuku where it is permitted, '
        'a blade where it is not, inside the walls. Everyone else goes to the ground '
        'outside town.',
        'Monks sit outside the whole arrangement, which is the single most attractive '
        'thing about being a monk.',
        'The word you want in a demographic sentence is "inhabitants", not "people". '
        'The distinction is the entire Celestial Order and it is load-bearing.',
        'A merchant can be rich enough to buy a province and still bow to a bushi with '
        'a stipend of nine koku. Yes. That is the joke the Empire tells.',
        'Caste is not permanent in either direction, whatever anyone tells you. It is '
        'simply very expensive to move.',
        attach(
            'A samurai. Not doing very much. That is rather the arrangement.',
            SAKE_SAMURAI,
        ),
        attach(
            'And this is everyone else, in the aggregate, being weather.',
            GREAT_WAVE,
        ),
    ),
    'money_koku': (
        'Koku. Fine. One koku gold coin is fixed by Imperial decree at forty gallons '
        'of rice for stipends, rent and taxes. The real market rate wanders. The legal '
        'one does not.',
        'Koku gold, bu silver, zeni copper. Stipends are paid in a mix of rice and '
        'coin, which is why the Ministry of Retainers is mostly a haulage operation.',
        'Rokugan is wealth-rich and coin-poor, like most premodern places that are not '
        'poor in both. This surprises people who have read too many merchant '
        'adventures.',
        'One koku feeds one person for a year, which is a much more useful thing to '
        'know than any exchange rate.',
        'A family of five needs about ten koku to eat and keeps seven and a half. Do '
        'the arithmetic and then ask me again why peasants make their own rope.',
        'Nobody carries meaningful sums in coin. They carry obligations, and the '
        'obligations are written down, and I am the writing.',
        'A farm is fifty koku. A stipend is single digits. An Imperial commendation is '
        'worth more than either and cannot be spent.',
        'The Ministry of Retainers orders rice out of county storehouses to pay people '
        'who live nowhere near those storehouses. That is most of what a great '
        'ministry does: move sacks.',
        attach(
            'Wealth in Rokugan, accurately depicted. It is mostly food and mostly somewhere else.',
            CARP,
        ),
        attach(
            'This is a man who has just been paid in rice and lives on the third floor.',
            SAKE_SAMURAI,
        ),
    ),
    'merchant_families': (
        'Merchant families own the FIELDS, not the farms. A field worked by ten '
        'households means that house has "authority over ten households", which is a '
        'phrase doing a great deal of work.',
        'Their clerks oversee tenant land. Not the headsman, not the magistrate. '
        'Clerks. There are always clerks.',
        'A merchant may be wealthier than the samurai he bows to. Both of them know '
        'it. Only one of them may say so.',
        'They pay business license fees, and the great one is sake brewing - every '
        'brewery above household scale holds an annual license, tiered by output.',
        'The Yasuki are the interesting case: they invented the anti-corruption system '
        "and are also the Empire's most accomplished smugglers. Both facts are in the "
        'record.',
        'Merchants are ten percent of samurai, which startles people who assume trade '
        'is beneath the caste. It is beneath the caste and they do it anyway.',
        'When you want to know who really runs a village, do not ask who owns it. Ask '
        'whose clerk visits.',
        'They keep better books than most ministries. I have read both.',
        attach(
            'A merchant house at work. Patient, cold, and considerably older than the garden.',
            CARP,
        ),
        attach(
            'And this is a negotiation between two of them going well.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ashigaru': (
        'Ashigaru. Peasant levies, trained by the county magistrate, not by the '
        'headsman - though the headsman leads them when bandits are reported.',
        'They are the reason a village headsman is almost always a man: the post '
        'carries training and, in war, command.',
        'They are not samurai and everyone is extremely clear about that until the '
        'moment somebody needs two hundred more bodies.',
        'A bandit report goes to the county magistrate. A bandit HUNT goes out under '
        'the headsman with whatever ashigaru the village can spare from the fields.',
        '"Whatever the village can spare from the fields" is the entire limiting '
        'factor on Rokugani warfare and nobody puts it in the songs.',
        'Every legionnaire is a samurai. Ashigaru are the other thing, and there are '
        'vastly more of them.',
        'Arm a farmer, and you have a farmer with a spear who would rather be farming.',
        'They come home. That is the difference between them and everyone in the stories.',
        attach(
            'Training. Such as it is. Such as there is time for.',
            ARCHERS,
        ),
        attach(
            'And this is what the songs say it looks like. It does not look like this.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'samurai_lineages': (
        'Lineages. Not bloodlines - political coalitions that happen to share an '
        'ancestor. Every samurai retainer belongs to one and every one of them is '
        "somebody's faction.",
        "Any lineage holding ten percent of a domain's samurai generally gets a seat "
        'on the house Chancellery, which advises the daimyo, which is to say decides '
        'things while appearing not to.',
        'The ruling lineage bears the house name. The Ryusei house is ruled by a '
        "Ryusei, and the chancellor is usually the daimyo's spouse, sibling or child.",
        'The Ryusei domain runs on six lineages holding almost ninety percent between '
        'them: Ryusei, Isa, Sasara, Moe, Tokino, Joji. Three of them - Isa, Joji, '
        'Meguri - were Mirumoto displaced by the return of the Unicorn.',
        'Look at which lineage holds which ministry and you will know what a domain '
        'has been arguing about for sixty years.',
        'Patronage and mutual aid run along lineage lines. So do grudges. Mostly grudges.',
        'A samurai will tell you their clan, then their family, then their house, and '
        'only tell you their lineage if they think you matter.',
        'The Ministry of Retainers submits candidates and the lineages fight about '
        'them. That is the civil service exam in practice.',
        attach(
            'Six lineages, one Chancellery, and every conversation happening on two '
            'levels at once.',
            CATS,
        ),
        attach(
            'This is what a lineage dispute looks like once it has stopped being polite.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'experience_levels': (
        'Experience levels. Yes. The Empire does not measure people that way and I am '
        'obliged to anyway.',
        'A samurai becomes an adult at gempukku, aged fourteen. That is when the '
        'counting starts and when the trouble starts.',
        'Eligible to retire at forty. Encouraged at fifty. Required at sixty without '
        'special dispensation.',
        "About fifty-eight percent of a domain's samurai are between those two lines. "
        'The rest are children or retired, and the retired ones have opinions.',
        'The interesting thing is not how good somebody is. It is how long they have '
        'been in a position to make the same mistake.',
        'Competence and rank are related the way weather and the calendar are related.',
        'Most samurai never leave their domain. The exceptional ones do, and I have to '
        'write down what they did there.',
        'Ask me what somebody has DONE. That number I keep.',
        attach(
            'Forty years of practice, and it still comes down to the one afternoon.',
            ARCHERS,
        ),
        attach(
            'And this is the retirement most of them actually get.',
            RAINY_MOON,
        ),
    ),
    'accordances_of_rank': (
        'Fifteen ranks. The published books had ten and ten was not enough to hold the '
        'layers of government, so there are fifteen. The Emperor is the fifteenth.',
        'A samurai fresh from gempukku with no post is of the First Rank. Everybody '
        'starts there. Almost everybody stays near there.',
        'The Accordances of Rank govern gifts - what may be given, to whom, and what '
        'accepting it obliges you to. It is not etiquette. It is contract law with '
        'better manners.',
        'The Doctrine of Three Steps is the one people misquote at me. It governs how '
        'far a matter may travel from where it started before it becomes somebody '
        "else's.",
        'A gift you cannot refuse is a debt you did not agree to. That is the whole '
        'mechanism and it runs the Empire.',
        'Rank is not power. Rank is how much trouble it is to ignore you.',
        'The Ministry of Retainers tracks all of it. I record what happened when '
        'somebody got it wrong.',
        'Give a rank 4 what a rank 7 should receive and you have not been generous, '
        'you have been insulting, and I will have to write down which.',
        attach(
            'A gift being given at exactly the correct rank. Note that both men are armed.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the evening after a gift was given at the wrong one.',
            SAKE_SAMURAI,
        ),
    ),
    'imperial_budget': (
        'The Imperial budget. You want the number. Nobody ever wants the mechanism, '
        'and the mechanism is the interesting part.',
        'Five percent of gross land output goes to the Emperor, from every domain, on '
        'top of three to the Clan and two to the Family.',
        'That is percent of OUTPUT, not of tax collected. Since the daimyo takes a '
        'third, the ten percent kicked upward is thirty percent of what he actually '
        'has.',
        'Officials are given a budget and keep what they do not spend. Come in over '
        'and you make up the difference yourself.',
        'Which means half of what a modern person would call embezzlement is simply '
        'Rokugan working as designed. Negotiate well on timber and the surplus is '
        'yours.',
        'This is most true in the Ministry of Works and true enough everywhere else '
        'that a budget exists.',
        'The Empire is unusually well administered. That is not praise, it is a '
        'measurement, and it is why there is so much paperwork.',
        'Ask the character sheet for arithmetic. Ask me why the arithmetic is shaped like that.',
        attach(
            'The Imperial budget, as experienced by anyone below the ministry.',
            GREAT_WAVE,
        ),
        attach(
            'This is a minister who came in under budget. Note the relaxation.',
            SAKE_SAMURAI,
        ),
    ),
    'crime_and_punishment': (
        'Justice has two addresses and they are never confused. One in the middle of '
        'town where the feet pass - cangue frame, flogging post, kneeling stone. That '
        'one is for display.',
        'The other is outside the settlement entirely, past the boundary stone, on '
        'bare unbunded waste. Death pollution does not come inside a town.',
        'Rokugan does not imprison as a punishment. The county jail exists so a '
        'prisoner has somewhere to wait while the sentence travels up for '
        'confirmation.',
        'A county magistrate may TRY a capital case. He may not conclude one. That '
        'distinction has saved more lives than mercy has.',
        'A county of seven thousand produces a formal execution perhaps once in five '
        'to ten years. A bandit gang taken alive can supply a decade in an afternoon.',
        "Burakumin perform every execution that is not a samurai's. A condemned "
        'samurai is dealt with by samurai, inside the walls.',
        'The execution ground is busy at a capital and nearly idle in a county. People '
        'imagine it the other way round.',
        'Most punishment is not death. Most punishment is being made to kneel where '
        'everyone you know walks past.',
        attach(
            'The display half. The point is not the pain, it is the traffic.',
            RAINY_MOON,
        ),
        attach(
            'And this is what happens when a matter is settled before it reaches either address.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the six Ministries -------------------------------------------------
    'ministry_of_rites': (
        'Rites. They track every birth, marriage and death of every subject the daimyo '
        'has, samurai and peasant alike. When a peasant moves they are obliged to '
        'report it.',
        'A country monk in every village district, a preceptor in every county town, a '
        'provincial abbot in every provincial city, and at least two grand abbots in '
        'every capital. That is the whole religious apparatus.',
        'The IMPERIAL Ministry of Rites decides which doctrines are accepted, which '
        'are debatable, and which are heresy. Everyone else merely enforces.',
        'That distinction has ended more careers than the Ministry of War.',
        'The Imperial Minister of Rites is also the High Priestess of Amaterasu. All '
        'the Imperial ministers collect titles like that.',
        'They keep the festivals. Twelve months of them. It is more administration '
        'than devotion and the abbots would agree in private.',
        'If you want to know whether something is heretical, the honest answer is that '
        'it is heretical when Rites says so and not before.',
        'The Moto have several practices Rites has never formally tested. Do not be '
        'the one who asks them to.',
        attach(
            'Rites at work. Somebody is being registered. It will take all morning.',
            CATS,
        ),
        attach(
            'And this is a doctrinal dispute reaching its natural conclusion.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_revenue': (
        'Revenue. Land taxes, business licenses, import tariffs. A minister has an '
        'obligation, supplies it, keeps the surplus, and covers the shortfall himself.',
        'Tariffs are collected at the gates of walled cities and nowhere else. '
        'Point-of-sale, not point-of-transit - declare you are passing through and you '
        'pay nothing.',
        'Maximum legal rate is twenty percent of declared value: two to the Family, '
        'three to the Clan, five to the Emperor, and up to ten to the daimyo. Only the '
        "daimyo's cut is negotiable.",
        'The Yasuki Taka system separates discretion from collection. An inspector '
        'wearing the sash of office examines the goods and stamps a manifest; a '
        'different official takes the money.',
        'Money never touches anyone with authority over assessment. A gift to an '
        'inspector on duty is corruption BY DEFINITION - there is no innocent reason '
        'for it.',
        'Hantei the Tenth made it Empire-wide within a few years, after it worked at '
        'the harbor of Friendly Traveler Village.',
        'Four ways to smuggle: transit fraud, origin spoofing, misclassification, and '
        'simply going round the gate. I have entries for all four.',
        "The Yasuki paradox: they invented the system, they staff the Treasurer's "
        'office, and they are the best smugglers in the Empire. Nobody finds this odd '
        'except visitors.',
        attach(
            'A caravan at a gate. Everyone is being extremely correct.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is an inspector who has just declined a gift, celebrating privately.',
            SAKE_SAMURAI,
        ),
    ),
    'ministry_of_retainers': (
        'Retainers. Stipends and ranks for every samurai the daimyo has, plus civil '
        'service exams and promotion assessments.',
        'Stipends are paid in a mix of rice and coin, which means most of what this '
        'great ministry does is order sacks out of county storehouses and move them.',
        'The exam structure comes from Imperial China. The culture it lands in is '
        'Japanese. The result is that exams matter and lineage matters more.',
        'They submit candidates. The lineages fight about them. That is the process, '
        'stated honestly for once.',
        'The IMPERIAL Ministry of Retainers does the same for Imperial posts, and '
        'awards commendations - Kitsuki Fu has the Order of the Precious Crown for the '
        'Forgotten Tomb.',
        'That is the highest commendation available to anyone below daimyo, and it '
        'cannot be spent, which is rather the point.',
        'A stipend is single digits in koku. People kill over the difference between '
        'nine and eleven.',
        'The legal exchange rate is fixed by decree and the real one is not, and the '
        "gap between them is somebody's entire livelihood.",
        attach(
            'Payday. It arrives as rice and somebody has to carry it.',
            CARP,
        ),
        attach(
            'And this is a promotion board reaching consensus.',
            CATS,
        ),
    ),
    'ministry_of_war': (
        'War. They general the armies, make the weapons and armor, keep the stables, '
        "and maintain maps of their own land and their neighbors'.",
        'That last one is the interesting duty and nobody ever asks about it.',
        'The Imperial Minister of War is the Shogun. Some of the position is '
        'ceremonial. Some of it is twenty-odd legions on the Kaiu Wall.',
        'Every legionnaire is a samurai. That is what makes a legion expensive and '
        'what makes it a legion.',
        'The 1st guards the Gateway to the Burning Sands. The 2nd holds Beiden Pass. '
        "The 3rd is on the Wall, and so is most of the rest of the Empire's standing "
        'strength.',
        'A ministry of war is mostly logistics. Food, feed, horses, arrows, boots. The '
        'battles are the short part.',
        'Give a minister a budget for military readiness and he keeps what he does not '
        'spend. Consider what that does to the quality of boots.',
        'Ask me about a war and I will tell you what it cost. Ask somebody else who won.',
        attach(
            "The Ministry of War's actual output, most years.",
            ARCHERS,
        ),
        attach(
            'And this is the part they put on the banners.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ministry_of_works': (
        'Works. Roads, lighthouses, aqueducts, harbors, walls, moats, watchtowers. '
        'Everything that has to still be there next year.',
        'They are given a budget and keep the excess. Over budget comes out of their '
        'own pocket. That is not corruption, that is the design.',
        'Which means that negotiating a good price on timber is a form of income. Half '
        'of what you would call embezzlement is simply the system working.',
        'They have one resource no other ministry has: corvee labor. Every peasant '
        'household owes ten to twenty days a year, more in an emergency.',
        'The headsman picks who goes. That is why the headsman is unpopular in a way '
        'the magistrate never has to be.',
        'The Imperial Ministry of Works keeps Otosan Uchi, contributes heavily to the '
        'Kaiu Wall, and builds and staffs the waystations.',
        'A road that exists is a political achievement. A road that is maintained is a '
        'miracle and somebody is skimming it.',
        'Hantei the Tenth outlawed tolls on Imperial roads. Ask a Works minister how '
        'he feels about that and watch his face.',
        attach(
            'Public works. Note that the thing being built is not the point; the budget is.',
            ARCHERS,
        ),
        attach(
            'And this is a harbor project meeting its natural adversary.',
            GREAT_WAVE,
        ),
    ),
    'ministry_of_justice': (
        'Justice. Street policing, bandit patrols, magistrates, courts, jails. The '
        'whole apparatus, civil and criminal.',
        'Its authority takes two physical forms and they are never confused: the '
        'display ground inside the town, and the execution ground outside it.',
        'Magistrates try. Confirmation travels upward. A county magistrate cannot '
        'conclude a capital case and that is deliberate.',
        'The jail is a waiting room, not a punishment. Rokugan does not imprison '
        'people as a sentence.',
        'Yoriki do the actual work. Most of them are from other clans, because a '
        "daimyo's own people cannot be trusted to audit the daimyo.",
        "Twenty-five yoriki at the magistrate's office in the capital, five at each "
        'provincial sub-station. That is the Emerald apparatus in one domain.',
        'Justice in Rokugan is not blind. It is extremely well-informed and it has '
        'opinions about your family.',
        'When fighting breaks out between neighbors, nearby yoriki can be assembled to '
        'assist one side. Two hundred extra troops decides battles, and Emerald '
        'magistrates know it.',
        attach(
            'The display ground. The audience is the sentence.',
            RAINY_MOON,
        ),
        attach(
            'And this is a jurisdictional dispute between two magistrates.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- the calendar -------------------------------------------------------
    'twelve_months': (
        'The months. Mutsuki, affection. Kisaragi, changing. Yayoi, new life. Uzuki, '
        'the deutzia flower. Satsuki, sprout. Minazuki, dry.',
        'Then Fumizuki, poetry. Hazuki, leaf. Nagatsuki, long. Kaminazuki, no gods. '
        'Shimotsuki, frost. Shiwasu, priests running.',
        'Shiwasu means the priests are running, because the year is ending and nothing '
        'is finished. I have never felt more understood by a calendar.',
        'Kaminazuki is "no gods" because they are all elsewhere that month. Nobody has '
        'ever explained to my satisfaction where.',
        'The names are agricultural before they are poetic. Everything here is '
        'agricultural before it is poetic.',
        'Fumizuki is the first month of autumn and carries both Tanabata and Obon. It '
        'is the busiest month for anyone who deals with the dead.',
        'People plan campaigns around the harvest and then act surprised when a war '
        'ends in the ninth month.',
        'Twelve months, and about a third of the festivals in them are somebody '
        'apologizing to a fortune.',
        attach(
            'Minazuki. The dry month. This is what everyone is praying does not happen.',
            GREAT_WAVE,
        ),
        attach(
            'And this is Shimotsuki, when the roads close and nobody can start '
            'anything. My favorite.',
            RAINY_MOON,
        ),
    ),
    'sexagenary_cycle': (
        'Sixty years, named by pairing one of the Ten Heavenly Stems with one of the '
        'Twelve Earthly Branches. The Branches are the zodiac animals you already '
        'know.',
        'The Stem changes every two years, the Branch every year, so it takes sixty to '
        'come back round.',
        'Yang Wood Rat, Yang Wood Ox, on to Yang Wood Boar, then the Stem turns and it '
        'is Yin Wood Rat. That is the whole mechanism.',
        'The same cycle names the DAY as well as the year, which is why soothsayers can '
        'always find something significant about today.',
        'Ten stems: five elements, each yang then yin. It is tidier than anything else '
        'in this Empire.',
        'People born in the same year of the cycle believe things about each other. I '
        'record what they did, not what they were owed.',
        'Ask a soothsayer what year it is and settle in.',
        'Sixty years is about a life. That is not a coincidence and the monks will '
        'tell you so at length.',
        attach(
            'Sixty years, and this is roughly what it looks like from the inside.',
            INNER_VISION,
        ),
        attach(
            'The Rat. Where the whole thing starts, every time.',
            CATS,
        ),
    ),
    'twelve_hours': (
        'Twelve hours, each of them two of yours, each named for a zodiac animal.',
        'The Hour of the Rat is the middle of the night, which is when most of what I '
        'have to write down actually happens.',
        'Nobody in this Empire has ever agreed on when an hour begins. They agree on '
        'when it is over.',
        'A duel at dawn is a duel at the Hour of the Hare, and the seconds are already '
        'arguing about it.',
        'Appointments are made by the hour and kept by the shadow. This causes exactly '
        'as much trouble as you would expect.',
        'The hour is also named by the sexagenary cycle, so a soothsayer can find '
        'meaning in your arrival time. They will.',
        'Twelve hours, twelve months, twelve branches. The Empire likes twelve.',
        'It is currently late. It is always late by the time somebody asks me the time.',
        attach(
            'The Hour of the Rat. Nothing good has ever been decided at this hour.',
            RAINY_MOON,
        ),
        attach(
            'And this is the Hour of the Hare, which is when they do it anyway.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'festivals': (
        'Festivals. There is one in every month and most of them are an apology to a fortune.',
        'They are administered by the Ministry of Rites, which means they are more '
        'paperwork than devotion, and the abbots would agree in private.',
        'The solar markers sit alongside the lunar ones - Risshuu opens autumn, Shosho '
        'ends the heat, Nihyakujunichi is two hundred and ten days from spring and is '
        'when the typhoons come.',
        'Tanabata is the seventh of the seventh. Obon is the fifteenth of the same '
        'month. Autumn arrives busy.',
        'A festival is when the peasants are not in the fields, which means it is when '
        'the trouble is.',
        'Every festival I have on file has at least one entry that begins "afterward, '
        'the magistrate was called".',
        'The calendar is agricultural. The festivals are agricultural. The theology '
        'came second and is very good about it.',
        'Ask which festival and I will tell you what usually goes wrong at it.',
        attach(
            'A festival, at the point where the record starts getting interesting.',
            SAKE_SAMURAI,
        ),
        attach(
            'And this is the morning after one.',
            RAINY_MOON,
        ),
    ),
    'obon': (
        'Obon. Fifteenth day of the seventh month. Families invite the spirits of '
        'their ancestors back for one day and one night.',
        'The gates of the underworld open. Monks chant the sutras of the Shinseist '
        'canon for the entire week leading up to it.',
        'The Moto claim the monks are not opening the gates at all - that the sutras '
        'entreat Enma to open them herself. Rites has never tested that assertion.',
        'Do not be the one who asks Rites to test it.',
        'Souls come from Yomi and from Jigoku both. Wei Tin grants the damned '
        'dispensation to visit, and he bargains for it.',
        'Ancestors need help finding their descendants. Burning the correct incense '
        'acts as a beacon. Get the incense wrong and grandmother goes to the wrong '
        'house.',
        'It is the busiest week of the year for anyone who deals with the dead, and '
        'the second busiest for anyone who deals with the drunk.',
        'One day and one night. Then the gates close, and whatever did not get said waits a year.',
        attach(
            'The week before Obon. A great deal of chanting and very little sleep.',
            INNER_VISION,
        ),
        attach(
            'And this is the night itself, which is quieter than people expect.',
            RAINY_MOON,
        ),
    ),
}
