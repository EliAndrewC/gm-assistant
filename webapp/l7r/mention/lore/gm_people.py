"""Significant people, relics and geography. GM Assistant only.

Only people the GM kept as individuals live here. Anyone else who is merely
name-shaped gets the dismissal in `sheet.py` - and a HOUSE (`Akodo no Damasu`)
gets the houses handling instead, which is the distinction the GM corrected and
`topics.py` enforces by ordering.
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
        'Kitsu Okura. Prince Daigotsu once observed that Okura is more enigmatic than '
        'the Dragon Clan he derides, and I have never seen it put better.',
        'He derides the Dragon for being enigmatic. He is worse. Everyone notices and '
        'nobody says it to him.',
        'Six doctrines of attunement. I have had all six explained to me twice and I '
        'could not tell you whether they agree with each other.',
        'Agasha Tamori has written on him, which is how you know he matters and how '
        'you know the writing will not help.',
        'The dream-divination material runs through his theology. If you have ever '
        'asked a fortune for guidance in sleep, that is his framework.',
        'Ask him a direct question and receive a better question. It is infuriating '
        'and it is usually correct.',
        'Twenty entries in this record and not one of them is a straight answer.',
        'I like him. I would like him more at a distance.',
        attach(
            'Okura, explaining something. This is minute four.',
            INNER_VISION,
        ),
        attach(
            'And this is the questioner, at minute forty.',
            RAINY_MOON,
        ),
    ),
    'soshi_saibankan': (
        'Soshi Saibankan. A Scorpion, and a ruling of his is in the record, and the '
        'ruling is the reason you have heard the name.',
        'Saibankan means judge. A Scorpion named judge. Sit with that for a moment.',
        'His ruling is cited the way precedent is always cited - by people who have '
        'not read the reasoning.',
        'The reasoning is the good part. The outcome is merely the outcome.',
        'A Scorpion magistrate is not a contradiction. The Empire needs somebody to do '
        'the unpleasant necessary things.',
        'And then it needs somebody to blame for them. Same clan. Very efficient.',
        'When a Scorpion rules against their own interest, look harder.',
        'I have the ruling in full. Ask and be specific.',
        attach(
            'A ruling being delivered. Brief, correct, and about something else.',
            CATS,
        ),
        attach(
            'And this is the appeal.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'grand_abbot_benshi': (
        'Grand Abbot Benshi. The Outrage Over Outrageousness is his, and so is '
        'Promoting the Tao, and the two together tell you everything.',
        'A Grand Abbot sits in a domain capital. Every domain in Lion lands has its '
        'own Order of Bishamon with its own, and they are not subordinate to one '
        'another.',
        'Benshi is very clear about that last point whenever it is raised.',
        'Promoting the Tao sounds devotional. It is mostly administrative and it is '
        'mostly about land.',
        'An abbot who is good at arithmetic is more use to his order than one who is '
        'good at doctrine. Benshi is both, which is why he is difficult.',
        'The Outrage material is where he becomes interesting rather than merely senior.',
        'He endows, he arbitrates, and he remembers. We have that last one in common '
        'and it has not made us friends.',
        'Ask him about the Tao and clear your afternoon.',
        attach(
            'The Grand Abbot at his actual work.',
            INNER_VISION,
        ),
        attach(
            'And this is a dispute between two of them.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'akodo_toturi': (
        'Akodo Toturi. Daimyo of the Lion Clan, which is five hundred thousand samurai '
        'and the largest clan in the Empire.',
        'Every Lion vassal owes him three percent of gross land output. Two goes to '
        'their Family daimyo, five to the Emperor.',
        'That is three percent of everything the Lion grow. Consider the size of that '
        'and then consider that it is the smallest of his problems.',
        'The Matsu alone are two hundred and seventy-five thousand - roughly twice the '
        'next largest family in the Empire. He administers that.',
        'The Lion and the Crane keep fighting, and even the Emperor rarely orders a '
        'clan to stop, lest the clan conclude he has taken a side.',
        'So Toturi is left holding a war the Emperor would prefer did not happen and '
        'cannot say so.',
        'A daimyo of the ruling family of a clan carries two ranks above the listed '
        'rank of his post. He does not need them.',
        'Ask me about the Lion and I will end up talking about him whether or not you wanted that.',
        attach(
            'The Lion, in the aggregate.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is what administering it actually looks like.',
            CATS,
        ),
    ),
    'moto_khuyag': (
        'Moto Khuyag. He builds death detectors, and yes, that is the correct term, '
        'and no, I do not like writing it down either.',
        'Rokugani by birth. Born southeast of Kyuden Otaku, moved there, then to '
        'Kyuden Shinjo. His master is Moto Khunbish, spiritual advisor to Gaheris.',
        'Khunbish was a farrier - had made knives before that - and impressed Gaheris '
        'philosophically while shoeing his horses. His Rokugani name was Seito.',
        'The detection is tied to a geographic location. An accurate map is made, the '
        'blood of horses is spilled at landmarks, and bloodied earth is returned to '
        'Shiro Moto.',
        'Which means a detector works for one region only. He cannot use the Moto one '
        'in Uru lands, where Gaheris is actually fighting.',
        'The intended use is to scatter forces, see where large-scale violent death is '
        'predicted, and concentrate there.',
        'Akodo Natsuki pointed out - convincingly - that this only guarantees death, '
        'and that such deadly ground may produce defeat rather than victory.',
        'Khuyag replied that strategy is not his area. That is the most honest thing '
        'anybody says in this entire section.',
        attach(
            'The instrument. It requires horses and a map and is not subtle.',
            RAINY_MOON,
        ),
        attach(
            'And this is what it predicts.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'kuni_yori': (
        'Kuni Yori. A Kuni, which means a Crab, which means witch-hunting, which means '
        'the conversation is already unpleasant.',
        'The Kuni are fifteen thousand samurai in a single domain. Small, and nobody '
        'treats them as small.',
        'They study what they hunt. That is the whole controversy and it has never been resolved.',
        'A Kuni who knows too much about maho is doing their job. Right up until they are not.',
        'He is in the record twelve times and I would rather he were in it fewer.',
        'Ask a Kuni about the Taint and then do not sleep well.',
        'The Crab do not discuss it in open channels, and neither will I.',
        'Buy him a drink. Do not ask twice.',
        attach(
            "The Kuni's working conditions.",
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what studying it does over time.',
            FOX_WOMAN,
        ),
    ),
    'kuni_isamu': (
        'Kuni Isamu at the Forgotten Tomb. Yes. That entry.',
        'The Forgotten Tomb is the recurring example of a between place - somewhere '
        'coexistent between two realms.',
        'Kitsuki Fu was awarded the Order of the Precious Crown for her service there, '
        'the highest commendation available below daimyo.',
        'Read those two facts together and you will understand that something went '
        'badly and someone behaved extremely well.',
        'You do not find a between place. You are in one, and then you notice. That is '
        'what happened at the Tomb.',
        'A Kuni in a between place is either the best or the worst person to have '
        'brought. Both readings are in the record.',
        'It is called Forgotten. Somebody forgot it deliberately.',
        'Ask me about the commendation. It is the part with a clean answer.',
        attach(
            'The moment of noticing. It is always this quiet.',
            INNER_VISION,
        ),
        attach(
            'And this is what was in there.',
            KIDOMARU_TENGU,
        ),
    ),
    # ---- relics and swords --------------------------------------------------
    'famous_swords': (
        'Famous swords. Fine. There are nine in the record and every one of them has '
        'cost somebody a province, a name, or a life.',
        "Amatsukami no Ken, the Heavenly Sovereign's Sword - ancestral blade of the "
        'Damasu, carried by their daimyo Akodo no Damasu Chiho.',
        'Shitsuten, Lost Heaven. The final sword of Daidoji Masamune, who poured all '
        'his hatred of the Yasuki into it. Cursed, and it works.',
        'Doji Masayo turned up at the Toshi Ranbo tournament with Shitsuten and killed '
        'the man expected to win. Tango province changed hands over it.',
        'Kasai Tsume, Fire Claw - ancestral sword of the Tsume. There are two hundred '
        'and eighty-four domains and most ancestral swords are not worth naming.',
        "Ohari, Big Needle - the Riori lineage's, and the familial sword of the "
        'governor of Owari, who has always been a Riori.',
        'Seishinsho, Spirit Whisper - origin unknown, gifted to Akodo Biko by a hermit '
        'who said it had been blessed. Nobody has verified the hermit.',
        "Kishin no Ketsui, Resolve of the Fierce God, is tied to Lord Akodo's one "
        'stated regret. Akuzuki, Wicked Moon, has a saya so fine a Tsume said the '
        'sword was too good for its wielder.',
        attach(
            'Seiginryu came off Togashi Mountain by the eastern paths. Tamashikari is '
            'only the fifth most famous Scorpion blade. This is what any of them '
            'actually does.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is what a famous sword is for, most of the time. Being owned.',
            INNER_VISION,
        ),
    ),
    'temple_relics': (
        'Temple relics. Half of them are genuine, half are supposedly cursed, and the '
        'distinction is decided by a committee.',
        'A relic is an object with a story attached firmly enough that the story '
        'travels with it. That is the whole definition.',
        'Relic seekers are a real category of person and I have entries on several. '
        'None of the entries end well.',
        'A temple that holds a famous relic holds an income. Pilgrims are an economy.',
        'The Candle of Tears technically refers to the candle-HOLDER. Any candle put '
        'in it dribbles wax in two distinct trails.',
        'Which is either a miracle or a very well-made candle-holder, and the Ministry '
        'of Rites has never been asked to rule.',
        "The Armor of Fool's Regret is supposedly cursed and is currently with Ikoma "
        'Akaho of the 1st Legion, who seems fine.',
        'Ask whether a relic is real and you have asked the wrong question. Ask who '
        'benefits from it being real.',
        attach(
            'A relic doing what relics do. Attracting an audience.',
            CATS,
        ),
        attach(
            'And this is the seeker, on the way back.',
            RAINY_MOON,
        ),
    ),
    'armor_of_fools_regret': (
        "The Armor of Fool's Regret. Supposedly cursed. That word is carrying the entire entry.",
        'It is currently in the possession of Ikoma Akaho, a platoon lieutenant in the '
        '6th battalion of the 1st Imperial Legion.',
        'He is, as far as the record shows, entirely well, which is inconvenient for the story.',
        'A supposedly-cursed item is more useful to a campaign than a cursed one. The '
        'ambiguity does the work.',
        "Somebody named it Fool's Regret. Consider that somebody had to choose that "
        'name and had a reason.',
        'The 1st Legion guards the Gateway. It is a long posting with a lot of time to '
        'think about your armor.',
        'Every piece of famous armor in this Empire is famous because of what happened '
        'to the man inside it.',
        'Ask me whether it is really cursed and I will ask you what would change.',
        attach(
            "The armor's previous owner, allegedly.",
            MUSASHI_BAT,
        ),
        attach(
            'And this is Akaho, being entirely fine.',
            SAKE_SAMURAI,
        ),
    ),
    'candle_of_tears': (
        'The Candle of Tears. And it is not the candle. It is the candle-HOLDER, which '
        'nobody ever gets right.',
        'Any candle placed in it drips wax in two distinct trails, one down each side. '
        'Like tears. Hence the name, which somebody clearly enjoyed choosing.',
        'It does this reliably. That is what makes it a relic rather than an anecdote.',
        'Whether that is divine or merely well-cast has never been formally tested.',
        'The Ministry of Rites decides what is doctrine and what is heresy. Nobody has '
        'asked them about a candle-holder and nobody should.',
        'It is the most modest object in the relic material and the one I find hardest '
        'to explain away.',
        'A thing that weeps on schedule is either a miracle or good metalwork, and the '
        'Empire has never needed to choose.',
        'Put a candle in it and watch. That is the whole ritual.',
        attach(
            'Two trails, every time, for anyone who tries it.',
            RAINY_MOON,
        ),
        attach(
            'And this is the audience it draws.',
            CATS,
        ),
    ),
    'yamaoroshi': (
        'Yamaoroshi. A famous sword with a backstory, and the backstory is the reason '
        'anybody remembers the blade.',
        'The name means the wind that comes down off a mountain. Cold, sudden, and from above.',
        'It is in the touched-by-the-supernatural material, alongside Otaku Mirai and '
        'Doji no Tsume Toyohiro and Kakita Korihime.',
        'Which is company that tells you what kind of sword it is without my having to say so.',
        'Every famous sword in this record is famous for what its owner did, not for '
        'how it was made. Two of the nine are exceptions and this is not one.',
        'A named wind and a named blade. Rokugan does like that construction.',
        'It is not in the list of nine famous swords. It is its own thing and it earned that.',
        'Ask for the backstory. That is genuinely the good part.',
        attach(
            'The wind the sword is named for.',
            GREAT_WAVE,
        ),
        attach(
            'And this is what it was used for.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- geography ----------------------------------------------------------
    'kaiu_wall': (
        'The Kaiu Wall. It has held for a thousand years. That is not reassurance - '
        'that is a thousand years of people holding it.',
        'The 3rd Imperial Legion is there, and most of the remaining twenty-odd '
        'legions are there with it.',
        'Every legionnaire is a samurai. Consider what twenty legions of samurai '
        'standing in one place costs the Empire annually.',
        'The Imperial Ministry of Works contributes significantly to its upkeep, on '
        'top of everything the Crab put in.',
        'The Kaiu are twenty-five thousand samurai in a single domain and the Wall is '
        'their entire reason.',
        'The Crab do not discuss what is on the other side in open channels. Neither do I.',
        'It is the single largest standing commitment in the Empire and most of the '
        'Empire never thinks about it.',
        'Buy a Crab a drink and do not ask twice.',
        attach(
            'What the Wall is for.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what it feels like to be posted there.',
            RAINY_MOON,
        ),
    ),
    'isawa_woodlands': (
        'The Isawa Woodlands. People walk in somewhere else and walk out here, which '
        'is the whole entry.',
        'Someone lost in the Shinomen Forest a hundred miles from the Gateway to the '
        'Burning Sands came out of these woods. That is not a story. It is an entry.',
        'Which makes this a between place, or adjacent to one, and the Empire files it '
        'under forestry.',
        'Phoenix land, which is fitting - a clan whose founder practiced maho having a '
        'wood that does not respect distance.',
        'You do not find a between place. You are in one, and then you notice.',
        'A hundred miles. Write that number down before you decide this is folklore.',
        'The Isawa are ruled by the Council of Elemental Masters rather than a daimyo. '
        'Ask them about the woods and see how the meeting goes.',
        'Go in with a map and a witness. The map will not help.',
        attach(
            'The moment of noticing. It is always this quiet.',
            INNER_VISION,
        ),
        attach(
            'And this is what people report seeing.',
            KIDOMARU_TENGU,
        ),
    ),
    'drowned_merchant_river': (
        'The Drowned Merchant River. Pirates. Yes. On a river. People find that '
        'surprising and rivers are exactly where piracy works.',
        'A river is a road you cannot fence, patrol cheaply, or divert around.',
        'It runs through the Toshi Ranbo material, alongside the irrigation disputes '
        'and the bandit hunting.',
        'The name is doing a lot of work and nobody has ever asked me which merchant.',
        'Tariffs are collected at city gates, not on the water. Consider what that '
        'implies about who uses the river and why.',
        'Point-of-sale, not point-of-transit. A cargo that never enters a walled city never pays.',
        'Which makes the whole river a structural invitation, and the Empire has '
        'noticed and done very little.',
        'River piracy is a Ministry of Justice problem that behaves like a Ministry of '
        'Revenue problem. Nobody wants it.',
        attach(
            'The river, and its principal advantage.',
            GREAT_WAVE,
        ),
        attach(
            'And this is enforcement, such as it is.',
            ARCHERS,
        ),
    ),
}
