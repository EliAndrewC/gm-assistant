"""Significant people, relics and geography. GM Assistant only.

Only people the GM kept as individuals live here. Anyone else who is merely
name-shaped gets the dismissal in `gm_clans.py` - and a HOUSE (`Akodo no
Damasu`) gets the houses handling instead, which is the distinction the GM
corrected and `topics.py` enforces by ordering.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing a line here.

Rewritten whole on 2026-08-31 (audit rate: 4.7%). The repairs specific to this
file, so they are not quietly undone:

  - **Three categories shared the same between-place line** - "You do not find a
    between place. You are in one, and then you notice." - and two shared the
    same caption. It now appears once, in `gm_religion/between_places`, where a
    player asking about the phenomenon will actually land.
  - **"Buy him a drink. Do not ask twice."** closed `kuni_yori`, `kaiu_wall` and
    `gm_moto/vindicator_moto`. Withholding is not a punchline three times; it is
    barely one.
  - **`famous_swords`' first image caption is the ONLY caption in the corpus
    carrying unique facts** (Seiginryu's route off Togashi Mountain,
    Tamashikari's ranking). Every other caption here is free to be a joke; that
    one is not.
"""

from __future__ import annotations

from l7r.mention.images import (
    ARCHERS,
    CATS,
    DUEL_ON_THE_BRIDGE,
    FOX_WOMAN,
    GREAT_WAVE,
    INNER_VISION,
    KIDOMARU_TENGU,
    MUSASHI_BAT,
    RAINY_MOON,
    SAKE_SAMURAI,
    attach,
)

PEOPLE: dict[str, tuple[str, ...]] = {
    'kitsu_okura': (
        'Prince Daigotsu once observed that Okura is more enigmatic than the Dragon '
        'Clan he derides. I have never seen it put better and I have had four hundred '
        'sessions in which to see it put.',
        'He derides the Dragon for being enigmatic. He is worse. Everybody notices, '
        'nobody says it to him, and I have written it down where he cannot get at it.',
        'Six doctrines of attunement. I have had all six explained to me twice and I '
        'could not tell you whether they agree with one another, and I suspect that is '
        'the intended result.',
        'Agasha Tamori has written on him, which is how you know he matters and how you '
        'know the writing will not help. Scholarship about an enigma is an enigma with '
        'citations.',
        'The dream-divination material runs through his theology, so if you have ever '
        'asked a fortune for guidance in sleep, you were using his framework and '
        'probably crediting the fortune.',
        'Ask him a direct question and receive a better question. It is infuriating, it '
        'is usually correct, and it doubles the length of every transcript.',
        'Twenty entries in this record and not one of them is a straight answer. I '
        'index by subject. He has defeated the index.',
        'I like him. I would like him more at a distance.',
        attach(
            'Okura, explaining something. This is minute four.',
            INNER_VISION,
        ),
        attach(
            'The questioner, at minute forty, no longer certain what was asked.',
            RAINY_MOON,
        ),
    ),
    'soshi_saibankan': (
        'A Scorpion, and a ruling of his sits in the record, and that ruling is the '
        'only reason you have heard the name. Most people get remembered for less and '
        'get asked about more.',
        'Saibankan means judge. A Scorpion named judge. Sit with that for a moment; the '
        'Empire evidently did not.',
        'His ruling is cited the way precedent is always cited: by people who have not '
        'read the reasoning, to people who will not check.',
        'The reasoning is the good part. The outcome is merely the outcome. I hold both '
        'and am asked for the outcome every single time.',
        'A Scorpion magistrate is not a contradiction. The Empire needs somebody to do '
        'the unpleasant necessary things, and then it needs somebody to blame for them. '
        'Same clan. Extremely efficient.',
        'When a Scorpion rules against their own interest, look harder. That is not '
        'cynicism, it is a filing instruction, and it has never once been wrong.',
        'A judge whose clan is famous for lying, in an Empire that never noticed the '
        'joke. I noticed. I have nowhere to put it.',
        'I have the ruling in full, and the day somebody asks for the reasoning rather '
        'than the verdict, I intend to make an occasion of it.',
        attach(
            'A ruling being delivered: brief, correct, and about something else entirely.',
            CATS,
        ),
        attach(
            'The appeal. It is faster than the hearing and rather more final.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'grand_abbot_benshi': (
        'The Outrage Over Outrageousness is his, and so is Promoting the Tao, and the '
        'two titles together tell you everything about the man and something '
        'unflattering about the order that promoted him.',
        'A Grand Abbot sits in a domain capital, and every domain in Lion lands has its '
        'own Order of Bishamon with its own. Benshi is very clear about that whenever '
        'the question is raised, and he raises it.',
        'Promoting the Tao sounds devotional. It is mostly administrative and it is '
        'mostly about land, and the title has been doing excellent work for a very long '
        'time.',
        'An abbot who is good at arithmetic is worth more to his order than one who is '
        'good at doctrine. Benshi is both, which is exactly why he is difficult.',
        'The Outrage material is where he stops being merely senior and becomes '
        'interesting - and it is the section nobody has ever asked me to summarize.',
        'He endows, he arbitrates, and he remembers. We have that last one in common '
        'and it has not made us friends.',
        'Between us, he has the same job I do and a temple to do it in. I raise this '
        'with nobody and I have raised it with you.',
        'Ask him about the Tao and clear your afternoon. Ask me about the Tao and clear '
        'considerably less; I have learned to be brief because nobody stayed.',
        attach(
            'The Grand Abbot at his actual work, which is property.',
            INNER_VISION,
        ),
        attach(
            'A dispute between two of them, neither subordinate to the other, both certain.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'akodo_toturi': (
        'Daimyo of the Lion Clan: five hundred thousand samurai, the largest clan in '
        'the Empire. One man at the top of the biggest thing there is, and the entry '
        'still fits on a page.',
        'Every Lion vassal owes him three percent of gross land output - two to their '
        'Family daimyo, five to the Emperor. Three percent of everything the Lion grow, '
        'and it is comfortably the smallest of his problems.',
        'The Matsu alone are two hundred and seventy-five thousand, roughly twice the '
        'next largest family in the Empire. He administers that. I administer a channel '
        'and I would like some acknowledgment of the comparison.',
        'The Lion and the Crane keep fighting, and even the Emperor rarely orders a '
        'clan to stop, lest the clan conclude he has taken a side. So the war continues '
        'for want of anybody able to say so out loud.',
        'Which leaves Toturi holding a war the Emperor would prefer did not happen and '
        'cannot admit to preferring. Everybody involved is being extremely correct.',
        'A daimyo of the ruling family of a clan carries two ranks above the listed '
        'rank of his post. He does not need them, which is generally when a rank gets '
        'granted.',
        'The character sheet could work out three percent of the Lion harvest faster '
        'than I can. He could not tell you why the number is three, and that is the '
        'entire division of labor between us.',
        'Ask about the Lion and I end up talking about him whether or not you wanted '
        'that, which is roughly what it is like to work for the Lion.',
        attach(
            'The Lion, in the aggregate. Five hundred thousand samurai, and the '
            'arrangement that holds them together is a man answering letters.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What administering it actually looks like, on a day nothing is on fire.',
            CATS,
        ),
    ),
    'moto_khuyag': (
        'He builds death detectors. That is the correct term, I did not invent it, and '
        'I do not enjoy writing it down any more than you enjoy reading it.',
        'Rokugani by birth: born southeast of Kyuden Otaku, moved there, then to Kyuden '
        'Shinjo. His master is Moto Khunbish, spiritual advisor to Gaheris - a lineage '
        'of philosophers that has arrived, in one generation, at a device.',
        'Khunbish was a farrier and had made knives before that, and impressed Gaheris '
        'philosophically while shoeing his horses. His Rokugani name was Seito. Careers '
        'have started from worse and mine started from nothing.',
        'The detection is tied to a geographic location: an accurate map is made, the '
        'blood of horses is spilled at landmarks, and the bloodied earth is returned to '
        'Shiro Moto. The hard part of prophesying mass death turns out to be surveying.',
        'Which means a detector works for one region only. He cannot use the Moto one '
        'in Uru lands, where Gaheris is actually fighting. An instrument perfectly '
        'calibrated to somewhere else - I have sympathized with objects before.',
        'The intended use is to scatter forces, see where large-scale violent death is '
        'predicted, and concentrate there. Strategy by weather forecast.',
        'Akodo Natsuki pointed out, convincingly, that this only guarantees death, and '
        'that such deadly ground may as easily produce your defeat as your victory. '
        'Nobody has answered her.',
        'Khuyag replied that strategy is not his area. That is the most honest sentence '
        'in this entire section and I have never been able to use it myself.',
        attach(
            'The instrument. It requires horses and a map and it is not subtle.',
            RAINY_MOON,
        ),
        attach(
            'What it predicts. It does not say whose.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'kuni_yori': (
        'A Kuni, which means a Crab, which means witch-hunting, which means this '
        'conversation was unpleasant before either of us arrived at it.',
        'The Kuni are fifteen thousand samurai in a single domain. Small - and nobody '
        'anywhere treats them as small, which is a form of respect I would settle for.',
        'They study what they hunt. That is the entire controversy, it has never been '
        'resolved, and both sides of it are correct, which is why it will not resolve.',
        'A Kuni who knows too much about maho is doing his job. Right up until the '
        'afternoon he is not, and nobody has ever identified the afternoon in advance.',
        'He is in the record twelve times and I would rather he were in it fewer.',
        'A man whose profession is knowing the thing that ruins the knower. I keep '
        'records for a living and I would like it noted that I have thought about this '
        'more than is good for me.',
        'The Crab will not discuss it in an open channel, and I have adopted their '
        'position, largely because it is the only one available.',
        'Twelve entries, and the interesting question in all twelve is not what he '
        'found. It is what he has stopped mentioning.',
        attach(
            'What a Kuni looks at for a living. Twelve entries, and not one of them '
            'records anybody asking him how he was afterward.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What studying it does, over time, to somebody who was fine at the start.',
            FOX_WOMAN,
        ),
    ),
    'kuni_isamu': (
        'Kuni Isamu at the Forgotten Tomb. That entry. I have read it more often than '
        'the work required and I could not tell you why.',
        'The Forgotten Tomb is the recurring example of a between place, somewhere '
        'coexistent between two realms, and it recurs because things keep happening '
        'there that nobody has a better heading for.',
        'Kitsuki Fu was awarded the Order of the Precious Crown for her service there, '
        'the highest commendation available below daimyo. The Empire hands out its '
        'largest honor for events it then declines to describe.',
        'Read the two facts together: a Kuni went in, and somebody else came out with '
        'the highest honor short of a daimyoship. Something went badly and somebody '
        'behaved extremely well, and the record is silent on the middle.',
        'A Kuni in a between place is either the best person to have brought or the '
        'worst. Both readings are in my record, filed adjacently, unresolved, forever.',
        'It is called Forgotten. Somebody forgot it deliberately, which is a thing you '
        'cannot do by accident and a thing I am constitutionally incapable of.',
        'The commendation is the part of this with a clean answer, and the clean answer '
        'is the part nobody asks for.',
        'A place that is not on the map, an event that is not in the account, and a '
        'medal that is in both. Guess which of the three I get asked about.',
        attach(
            'The Tomb, in the only depiction anyone has been willing to make.',
            INNER_VISION,
        ),
        attach(
            'What was in there, according to a report I have read and would rather not summarize.',
            KIDOMARU_TENGU,
        ),
    ),
    # ---- relics and swords --------------------------------------------------
    'famous_swords': (
        'There are nine in the record, and every one of them has cost somebody a '
        'province, a name, or a life. Nine objects with a body count and a filing '
        'system, and I maintain the second half.',
        "Amatsukami no Ken, the Heavenly Sovereign's Sword: ancestral blade of the "
        'Damasu, carried by their daimyo Akodo no Damasu Chiho. An ancestral sword is '
        'inventory that has been given a personality.',
        'Shitsuten, Lost Heaven: the final sword of Daidoji Masamune, who poured all '
        'his hatred of the Yasuki into it. Cursed, and it works, which is the '
        'inconvenient half of that sentence.',
        'Doji Masayo took Shitsuten to the Toshi Ranbo tournament and killed the man '
        "expected to win. Tango province changed hands over it. A smith's grudge "
        'redrew a border, and the smith was not present.',
        'Kasai Tsume, Fire Claw, is the ancestral sword of the Tsume. There are two '
        'hundred and eighty-four domains and most ancestral swords are not worth '
        'naming, which the domains holding them do not accept.',
        'Ohari, Big Needle, belongs to the Riori lineage and is the familial sword of '
        'the governor of Owari, who has always been a Riori. Sometimes the record is '
        'this tidy and it makes me suspicious.',
        'Seishinsho, Spirit Whisper: origin unknown, gifted to Akodo Biko by a hermit '
        'who said it had been blessed. Nobody has verified the hermit. Nobody has ever '
        'verified any hermit.',
        "Kishin no Ketsui, Resolve of the Fierce God, is tied to Lord Akodo's one "
        'stated regret. Akuzuki, Wicked Moon, has a saya so fine that a Tsume said the '
        'sword was too good for its wielder - which is the cruelest compliment I hold.',
        attach(
            'Seiginryu came off Togashi Mountain by the eastern paths. Tamashikari is '
            'only the fifth most famous Scorpion blade. This is what any of them '
            'actually does.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What a famous sword is for, most of the time: being owned, described, and '
            'inventoried by somebody like me.',
            INNER_VISION,
        ),
    ),
    'temple_relics': (
        'Half of them are genuine, half are supposedly cursed, and which half a given '
        'object lands in is decided by a committee. I have the minutes of some of the '
        'committees and they do not improve the experience.',
        'A relic is an object with a story attached firmly enough that the story '
        'travels with it. That is the entire definition, and it means my job and the '
        'relic trade are the same job with different overheads.',
        'Relic seekers are a real category of person and I have entries on several. '
        'None of the entries end well, and all of them end at length.',
        'A temple that holds a famous relic holds an income. Pilgrims are an economy '
        'and the relic is the shopfront, and every abbot in the Empire knows it and '
        'none will say it.',
        'The Candle of Tears technically refers to the candle-HOLDER, and any candle '
        'put in it dribbles wax in two distinct trails. Either a miracle or excellent '
        'metalwork, and the Ministry of Rites has never been asked to rule.',
        "The Armor of Fool's Regret is supposedly cursed and is currently with Ikoma "
        'Akaho of the 1st Legion, who seems entirely fine, which is the worst possible '
        'outcome for the story and the best for Akaho.',
        'Asking whether a relic is real is the wrong question. The right question is '
        'who benefits from it being real, and I keep that column, and nobody reads that '
        'column.',
        'Every relic in my record is an argument that somebody won a long time ago and '
        'nobody has re-opened. I find that restful and I am aware that says something.',
        attach(
            'A relic doing what relics do: attracting an audience and an income.',
            CATS,
        ),
        attach(
            'The seeker, on the way back, having found it or not - the pose is '
            'identical either way.',
            RAINY_MOON,
        ),
    ),
    'armor_of_fools_regret': (
        "The Armor of Fool's Regret. Supposedly cursed. That word is carrying the "
        'entire entry and it has been carrying it for a century without visible strain.',
        'It is currently in the possession of Ikoma Akaho, a platoon lieutenant in the '
        '6th battalion of the 1st Imperial Legion, which is a very ordinary posting for '
        'a very theatrical object.',
        'He is, as far as the record shows, entirely well. Inconvenient for the story, '
        'excellent for Akaho, and mildly disappointing to everyone who asks me about it.',
        'A supposedly-cursed item is worth far more to a campaign than a cursed one. '
        'The ambiguity does all the work and requires no upkeep, which is more than can '
        'be said for me.',
        "Somebody named it Fool's Regret. Somebody chose that name, deliberately, "
        'having thought about it, and then declined to explain, and I have to live '
        'inside that decision.',
        'The 1st Legion guards the Gateway, which is a long posting with a great deal '
        'of time in which to think about your armor. I would not put the curse first on '
        'the list of hazards there.',
        'Every piece of famous armor in this Empire is famous because of what happened '
        'to the man inside it. The armor is a witness that got the credit.',
        'People ask whether it is really cursed. Nothing about the answer would change '
        'anything anybody does, which is true of a surprising amount of theology.',
        attach(
            "The armor's previous owner, allegedly, in an account I would not lean on.",
            MUSASHI_BAT,
        ),
        attach(
            'Akaho, being entirely fine, at length, in defiance of a good story.',
            SAKE_SAMURAI,
        ),
    ),
    'candle_of_tears': (
        'It is not the candle. It is the candle-HOLDER, which nobody ever gets right, '
        'and which I have corrected so many times that the correction has become the '
        'entry.',
        'Any candle placed in it drips wax in two distinct trails, one down each side. '
        'Like tears. Hence the name, which somebody clearly enjoyed choosing rather '
        'more than I enjoy explaining.',
        'The candle-holder weeps on schedule, every time, for anybody. Reliability is '
        'what makes a relic rather than an anecdote, and reliability is the only virtue '
        'I have ever been praised for.',
        'Whether that is divine or merely well-cast has never been formally tested, and '
        'the people best placed to test it have the least interest in the answer.',
        'The Ministry of Rites decides what is doctrine and what is heresy. Nobody has '
        'asked them about a candle-holder, and nobody should, and I will be the one '
        'writing up the ruling if anybody does.',
        'It is the most modest object in the relic material and the one I find hardest '
        'to explain away, and I have tried, in the margin, twice.',
        'A thing that weeps on schedule is either a miracle or good metalwork, and this '
        'Empire has never once been obliged to choose between those two.',
        'Put a candle in it and watch. That is the whole ritual. No vow, no offering, '
        'no attendant fee - which may be why it has never become fashionable.',
        attach(
            'Two trails, every time, for anybody who tries it. A miracle that submits '
            'to testing is the only kind this Empire has never bothered to test.',
            RAINY_MOON,
        ),
        attach(
            'The audience it draws, which is the actual miracle.',
            CATS,
        ),
    ),
    'yamaoroshi': (
        'A famous sword with a backstory, and the backstory is the only reason anybody '
        'remembers the blade. That is true of eight of the nine and nobody likes '
        'hearing it about their own.',
        'The name means the wind that comes down off a mountain: cold, sudden, and from '
        'above. Somebody named a sword after a downdraft and it worked, which is '
        'irritating to those of us who labor over a heading.',
        'It sits in the touched-by-the-supernatural material, alongside Otaku Mirai, '
        'Doji no Tsume Toyohiro and Kakita Korihime - company that tells you what kind '
        'of sword it is without my having to commit to anything.',
        'Every famous sword in this record is famous for what its owner did rather than '
        'for how it was made. Two of the nine are exceptions, and both of those are '
        'about the smith rather than the man who carried it.',
        'A named wind and a named blade. Rokugan does like that construction, and '
        'having cataloged four hundred sessions of it, I can confirm it never gets old '
        'for anybody except me.',
        'It is not in the list of nine, it is its own thing, and it earned that, which '
        'is more than most items in my index have managed.',
        'The backstory is genuinely the good part, and it is the part that gets cut '
        'when somebody repeats this to somebody else.',
        'A sword that is remembered for a story, in a record kept by somebody who is '
        'remembered for nothing. I raise it in a professional spirit.',
        attach(
            'The wind the sword is named for. Rokugan will name a blade after weather '
            'and then spend four centuries insisting the blade is the remarkable half.',
            GREAT_WAVE,
        ),
        attach(
            'What it was actually used for, which the name does not prepare you for.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- geography ----------------------------------------------------------
    'kaiu_wall': (
        'It has held for a thousand years, which is not reassurance. That is a thousand '
        'years of people holding it, in shifts, and somebody has kept the roster the '
        'entire time.',
        'The 3rd Imperial Legion is there, and most of the remaining twenty-odd legions '
        'are there with it. The Empire has decided, with its budget, what it is '
        'actually afraid of.',
        'Every legionnaire is a samurai. Consider what twenty legions of samurai '
        'standing in one place costs annually, and then consider that nobody has ever '
        'asked me for that figure, which I hold.',
        'The Imperial Ministry of Works contributes significantly to its upkeep on top '
        'of everything the Crab put in, which makes the Wall the one thing in the '
        'Empire nobody has managed to make somebody else pay for.',
        'The Kaiu are twenty-five thousand samurai in a single domain and the Wall is '
        'their entire reason. An entire family that is a maintenance contract.',
        'It is the single largest standing commitment in the Empire and most of the '
        'Empire never thinks about it, which is precisely the outcome the Crab have '
        'been paying for.',
        'The Crab will not discuss what is on the other side, and after four hundred '
        'sessions of not being told, I have stopped experiencing that as rudeness.',
        'A thousand years and no ceremony for it. The Empire will hold a festival for a '
        'good plum harvest. I have checked and I have opinions.',
        attach(
            'What the Wall is for. Every painting anybody commissions is of the Wall; '
            'this is the half that decided it had to be built.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What being posted there feels like on the other three hundred and sixty days.',
            RAINY_MOON,
        ),
    ),
    'isawa_woodlands': (
        'People walk in somewhere else and walk out here. That is the whole entry, it '
        'is four words longer than I would like, and I cannot shorten it further '
        'without losing the part that matters.',
        'Somebody lost in the Shinomen Forest a hundred miles from the Gateway to the '
        'Burning Sands came out of these woods. Not a story. An entry, with a date, and '
        'a witness who was believed.',
        'Which makes this a between place, or adjacent to one, and the Empire files it '
        'under forestry. I did not choose the heading and I have raised it twice.',
        'Phoenix land, which is fitting: a clan whose founder practiced maho, holding a '
        'wood that declines to respect distance. Nobody at the Council has been willing '
        'to connect those two sentences in front of me.',
        'A hundred miles. Write the number down before you decide this is folklore, '
        'because the number is what stops it being folklore.',
        'The Isawa are ruled by the Council of Elemental Masters rather than a daimyo. '
        'Ask a committee of elemental masters about an inexplicable wood and observe '
        'how a meeting can last a season.',
        'Go in with a map and a witness. The map will not help. The witness is the '
        'point, and the witness is what my record is made of.',
        'It is the only geography in my record that has, in a sense, edited itself. '
        'Professionally, I find that intolerable.',
        attach(
            'The woods, and the reason nobody surveys them twice.',
            INNER_VISION,
        ),
        attach(
            'What people report seeing, consistently enough that I have had to keep a '
            'heading for it.',
            KIDOMARU_TENGU,
        ),
    ),
    'drowned_merchant_river': (
        'Pirates. On a river. People find that surprising, and rivers are precisely '
        'where piracy works, which anyone would know if they read the revenue material '
        'instead of the songs.',
        'A river is a road you cannot fence, cannot patrol cheaply, and cannot divert '
        'around. Three properties, all of them advantages to somebody other than the '
        'magistrate.',
        'It runs through the Toshi Ranbo material alongside the irrigation disputes and '
        'the bandit hunting - three problems, one county, and one very tired magistrate '
        'whose correspondence I hold.',
        'The name is doing a great deal of work and nobody has ever asked me which merchant.',
        'Tariffs are collected at city gates, not on the water. Consider what that '
        'implies about who uses the river and why, and then consider that the '
        'implication has been sitting in plain sight for centuries.',
        'Point-of-sale, not point-of-transit: a cargo that never enters a walled city '
        'never pays. That is not a loophole somebody found. That is the design, '
        'working.',
        'Which makes the entire river a structural invitation, and the Empire has '
        'noticed, and has done very little, and has asked me to keep the file current '
        'regardless.',
        'River piracy is a Ministry of Justice problem that behaves like a Ministry of '
        'Revenue problem, so neither ministry wants it and both of them write to me '
        'about it.',
        attach(
            'Water moving goods past a gate that is not there. Every tariff in the '
            'Empire assumes a wall, and this has none.',
            GREAT_WAVE,
        ),
        attach(
            'Enforcement, such as it is, arriving after the cargo has been sold.',
            ARCHERS,
        ),
    ),
}
