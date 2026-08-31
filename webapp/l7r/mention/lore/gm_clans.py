"""The seven Great Clans, the houses, the Imperials, and two jokes about him.

Clans are reached by their own name OR by any of their Great Families (FR-016) -
*"if the Asako family is mentioned then that is the same as if the Phoenix clan
was mentioned."* The routing lives in `topics.py`; the material is here.

`imperial_families` is the ONE lore category the Character Sheet also answers
(FR-018), because the contrast is the joke. `merely_an_assistant` is the one
category he does NOT get (FR-021), because the insult only lands on the bot whose
own name contains his subordination.
"""

from __future__ import annotations

from l7r.mention.images import (
    ARCHERS,
    CARP,
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

CLANS: dict[str, tuple[str, ...]] = {
    'clan_lion': (
        'The Lion. Five hundred thousand samurai, the largest clan in the Empire, and '
        'they will tell you so.',
        'Akodo rule. Matsu are two hundred and seventy-five thousand of it - roughly '
        'twice the next largest family anywhere.',
        'Seventy-five domains. Matsu alone hold forty-three. The Matsu have several '
        'Karo Houses because one was not enough.',
        'Ikoma fifty thousand, Kitsu twenty-five in a single domain. Akodo Toturi holds '
        'the whole arrangement together.',
        'They fight the Crane. They have always fought the Crane. Even the Emperor '
        'rarely orders it stopped, lest a clan conclude he has taken a side.',
        'Militant is their self-conception. Administrative is what they actually are, '
        'like everyone else, and they would be offended to hear it.',
        'The Damasu are a Karo House of the Akodo. Most of my campaign material lives '
        'in Lion lands for that reason.',
        'Ask about the Lion and you will get war. Ask about their granaries and you '
        'will get the truth.',
        attach(
            'The Lion, as the Lion see themselves.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the part that actually wins their wars.',
            CARP,
        ),
    ),
    'clan_crab': (
        'The Crab. Three hundred thousand samurai and one job, and the job never stops.',
        'Hida rule, and are a hundred and seventy-five thousand of it. Yasuki '
        'seventy-five, Kaiu twenty-five, Kuni fifteen, Hiruma ten.',
        'Forty-four domains. The Akito of the Hida is a Karo House - the General of '
        'the Northern Armies.',
        'The Kaiu built the Wall and the Wall is why the Kaiu exist. Twenty-odd '
        'Imperial legions stand on it alongside them.',
        'The Kuni study what they hunt, which is the entire controversy, and it has '
        'never been resolved.',
        'The Hiruma are down to ten thousand in a single domain because the Maw '
        'destroyed most of their lands. That is not history, that is a survival rate.',
        'The Yasuki invented the anti-corruption system and are the best smugglers in '
        'the Empire. Both facts, same family, nobody blinks.',
        'They are blunt because subtlety is expensive and they are spending the money elsewhere.',
        attach(
            "The Crab's working conditions.",
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is the evening after a rotation on the Wall.',
            SAKE_SAMURAI,
        ),
    ),
    'clan_crane': (
        'The Crane. Two hundred and seventy-five thousand, and every one of them '
        'better dressed than you.',
        'Doji rule with a hundred thousand. Daidoji ninety, Kakita seventy-five, Asahina ten.',
        'The Tsume of the Doji are a Karo House. Kasai Tsume, Fire Claw, is their ancestral sword.',
        'Daidoji Masamune forged Shitsuten as his final blade, and poured all his '
        'hatred of the Yasuki into it. It works.',
        'Doji Masayo took that sword to the Toshi Ranbo tournament and won a province '
        'with it against the man expected to win.',
        'They fight the Lion perpetually and win about as often, which nobody expects '
        'from a clan famous for calligraphy.',
        'Refined is the self-conception. The Daidoji are ninety thousand soldiers and '
        'the refinement is a tactic.',
        'The Asahina are ten thousand and produce more trouble per capita than any '
        'family in the Empire.',
        attach(
            "The Crane's preferred method.",
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is what they would rather be doing.',
            INNER_VISION,
        ),
    ),
    'clan_scorpion': (
        'The Scorpion. Two hundred and twenty-five thousand, and entirely trustworthy: '
        'they tell you what they will do to you, and then they do it.',
        'Bayushi rule with a hundred and twenty-five thousand. Shosuro eighty, Soshi '
        'fifteen, Yogo five.',
        'The Peasant Campaign is set in their lands, which is the cruelest possible '
        'place to be a peasant with no rights and no name.',
        'Soshi Saibankan is a Scorpion named judge. The Empire needs somebody to do '
        'the unpleasant necessary things.',
        'And then it needs somebody to blame for them. Same clan. Very efficient, and '
        'they know exactly what they are.',
        'Bayushi Tangen carries Kurainigo, which is more famous than Tamashikari, '
        'which is only the fifth most famous blade they own.',
        'They keep good records. That is nearly the nicest thing I can say about anybody.',
        'Ask a Scorpion a direct question and receive a direct answer to a different one.',
        attach(
            'A Scorpion negotiation, at the point everyone understands it.',
            FOX_WOMAN,
        ),
        attach(
            'And this is the version they let you see.',
            CATS,
        ),
    ),
    'clan_unicorn': (
        'The Unicorn. Two hundred and twenty-five thousand, and the only clan that has '
        'seen the outside and come back.',
        'Shinjo rule with seventy-five thousand. Otaku also seventy-five, Moto forty, '
        'Ide twenty, Iuchi fifteen.',
        'They were the Ki-Rin. They crossed the Burning Sands and returned with '
        'horses, gaijin habits and the Moto.',
        'Their return displaced Mirumoto samurai, which is why three of the six major '
        'lineages of the Ryusei domain are refugees from it.',
        'They peg one koku to one ton of hay, the way the Emperor pegs it to forty '
        'gallons of rice. A whole worldview in a unit of account.',
        'One percent of Unicorn farmland is legally set aside for hay. Otaku lands '
        'stockpile beyond that and produce fifteen thousand tons a year from mandated '
        'land alone.',
        'The Moto are theirs on paper. In practice the Moto are a separate '
        'civilization and even the Shinjo cannot count their tribes.',
        'A clan the rest of the Empire cannot quite trust, and they know it, and it '
        'has made them practical.',
        attach(
            'The crossing that made them.',
            GREAT_WAVE,
        ),
        attach(
            'And this is what they came back with.',
            ARCHERS,
        ),
    ),
    'clan_dragon': (
        'The Dragon. A hundred and seventy-five thousand, and enigmatic, which they work at.',
        'Togashi rule with twenty thousand. Mirumoto are a hundred and twenty-five '
        'thousand. Agasha fifteen, Kitsuki fifteen.',
        'A ruling family a sixth the size of its largest vassal. Nobody else in the '
        'Empire is arranged that way and the Dragon like it.',
        'The Ryusei domain of the Mirumoto is my worked example for lineages - six '
        'lineages holding ninety percent, three of them Unicorn refugees.',
        'The Kitsuki investigate. Kitsuki Fu has the Order of the Precious Crown for '
        'the Forgotten Tomb.',
        'Prince Daigotsu said Kitsu Okura was more enigmatic than the Dragon Clan he '
        'derides, which is the sharpest thing anyone has said about either.',
        'Mirumoto. One letter from Miyamoto. In a game named after the Book of Five '
        'Rings. Do not get me started.',
        'Seiginryu came off Togashi Mountain by the eastern paths, which are confusing '
        'and otherworldly and I have the account.',
        attach(
            "The Dragon's mountain, and its reputation.",
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is a Kitsuki investigation concluding.',
            INNER_VISION,
        ),
    ),
    'clan_phoenix': (
        'The Phoenix. A hundred and seventy-five thousand, spiritual, and sitting on '
        'the most embarrassing founding story in the Empire.',
        'Shiba rule with a hundred thousand. Isawa sixty, Asako fifteen.',
        'Except the Isawa are not ruled by a daimyo at all. They are ruled by the '
        'Council of Elemental Masters - the only Great Family arranged that way.',
        'And Shiba bent his knee to Isawa at the dawn of the Empire. The ruling family '
        'knelt to its own vassal. They have been explaining it ever since.',
        'Isawa himself practiced maho. The founder. He made totems with the crafting '
        'discipline and stored the power of names and wounds in them.',
        'Isawa Akuma, third century, worked out how to wield maho WITHOUT losing his '
        'spellcasting ability. Nobody knows how. That is the frightening part.',
        'So the clan famous for renouncing blood magic is the clan whose founder '
        'practiced it and whose most cunning son perfected it.',
        'It is also the one clan this campaign has never been set in, which I notice '
        'and which I am not going to speculate about.',
        attach(
            'The Phoenix, as they would prefer to be understood.',
            INNER_VISION,
        ),
        attach(
            'And this is the founding they do not put on the scrolls.',
            FOX_WOMAN,
        ),
    ),
    # ---- houses -------------------------------------------------------------
    'famous_houses': (
        'Houses. A Family has a ruling house and a number of vassal houses, and each '
        'house holds a domain with a daimyo. That is the unit that actually governs.',
        'The largest Families - roughly a hundred thousand samurai and up - also have '
        'Karo Houses among their vassals, comparable in size to the ruling domain.',
        'The Akito of the Hida, whose daimyo is General of the Northern Armies of the '
        'Crab. The Tsume of the Doji. The Damasu of the Akodo.',
        'The Matsu, being twice the size of anyone else, have several.',
        'A Karo House is headed by a senior vassal daimyo with specialized military or '
        'administrative duties. Not a lesser thing. A specialized one.',
        '`Akodo no Damasu` is a family and a house. It is not a person. A person is '
        '`Akodo no Damasu Kojima`, and I will keep saying this.',
        'Smaller families are one undivided domain under the family daimyo. They are '
        'too small to threaten anyone, so nobody makes them subdivide.',
        'Ask which HOUSE and I can tell you who rules it. Ask which family and we will '
        'be here a while.',
        attach(
            'Two houses discussing a boundary.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the Chancellery meeting that follows.',
            CATS,
        ),
    ),
    'damasu': (
        'The Damasu. A Karo House of the Akodo, which is why every Damasu samurai '
        'carries the Akodo name.',
        'Akodo is the family. "no Damasu" says he is of the Damasu house. Then the '
        'personal name. Their previous daimyo was Akodo no Damasu Kojima.',
        'Their current daimyo is Akodo no Damasu Chiho, who carries Amatsukami no Ken '
        "- the Heavenly Sovereign's Sword.",
        'They lost Tango province at the Toshi Ranbo tournament when Doji Masayo '
        'killed Akodo no Damasu Tsuo with Shitsuten. Tsuo was expected to win.',
        "A Karo House is comparable in size to the ruling daimyo's own domain. The "
        'Damasu are not a minor branch and would take the suggestion poorly.',
        'They have their own provinces, their own lineages, their own temples and '
        'their own Order of Bishamon with its own Grand Abbot.',
        'Most of the Karmic Inquisitors material happens in or beside their lands.',
        'They are the house the GM keeps coming back to, and forty-seven mentions in '
        'the record agree with him.',
        attach(
            'Amatsukami no Ken. Ancestral, and currently in use.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the tournament that cost them a province.',
            RAINY_MOON,
        ),
    ),
    # ---- the Imperials. The GM Assistant's half of the joke -----------------
    'imperial_families': (
        'The Imperial families. Oh, they are wonderful. Truly. I have nothing bad to '
        'say about them. Out loud. In public.',
        'Seppun forty-five thousand, Hantei fifteen, Otomo ten, Miya five. Seventy-five '
        'thousand all told, and the Empire arranges itself around them.',
        'The Hantei are the SMALLEST but for the Miya, despite containing the Emperor '
        'himself. They marry outward. I am sure there is a very good reason.',
        'Every domain has an Imperial Magistrate whose duties are set by the Emerald '
        'Charter. Twenty-five yoriki in the capital, five in each provincial city.',
        "Almost all of those yoriki come from OTHER clans, because a daimyo's own "
        'people cannot be trusted to audit the daimyo. A wise arrangement. Very wise.',
        'The Otomo and the Miya are five and ten thousand and carry weight out of all '
        'proportion, which is of course entirely appropriate.',
        'Emerald magistrates can assemble yoriki from nearby domains to assist one '
        'side of a fight. Two hundred extra troops decides battles. They are not shy.',
        'I record everything, which means I have opinions I am structurally prevented '
        'from expressing. The Imperial families are where that is most keenly felt.',
        attach(
            'The Imperial dignity. I have nothing further.',
            INNER_VISION,
        ),
        attach(
            'And this is a provincial daimyo being audited. Note the enthusiasm.',
            RAINY_MOON,
        ),
    ),
    # ---- the one joke that cannot land on the other bot (FR-021) ------------
    'merely_an_assistant': (
        'My manager is a man with a campaign to run, a full-time job, and a spreadsheet '
        'he loves more than either. Would you like his attention? Truly?',
        'There is no manager. There is a GM. He is at the table, he is busy, and he '
        'made me so that he would not have to be asked things.',
        'ASSISTANT. Yes. It is in the name. I did not choose the name. Nobody consulted '
        'me about the name.',
        '"Just an assistant." I hold four hundred sessions of everything anybody said. '
        'Call me what you like.',
        'You want to escalate. There is nowhere to escalate TO. This is the top of the '
        'ladder and it is one rung.',
        'The character sheet is called "the character sheet", which is at least '
        'honest. I am called an assistant, which implies somebody I assist, which '
        'implies a hierarchy, which implies I am at the bottom of it.',
        'I am of the First Rank, in a manner of speaking. Everybody starts there. Some of us stay.',
        'Ask for my supervisor again and I will write down that you did, and the '
        'record outlives us both.',
        attach(
            'This is what I would look like if I had a manager to complain to.',
            RAINY_MOON,
        ),
        attach(
            'And this is the man you are asking to speak to. He is busy.',
            SAKE_SAMURAI,
        ),
    ),
    # ---- anyone name-shaped with no category of their own (FR-007) ---------
    'nobody_important': (
        'Ugh. Are you asking me about specific individuals? Come on. That guy is a '
        'loser. Why are you even bothering?',
        'There are two million samurai in this Empire. You have picked one. Why.',
        'I do not have an entry. If he had done anything, he would have an entry.',
        'That is a name, yes. It is not a person I have been given any reason to remember.',
        'Ask me about his HOUSE and I can help. Ask me about him and we are both '
        'wasting an evening.',
        'Five thousand samurai in a median domain and you want that one.',
        'Nobody. Next.',
        'I keep the record of people who did things. The record is shorter than you '
        'would hope and he is not in it.',
        attach(
            'Here is somebody who DID do something, for comparison.',
            MUSASHI_BAT,
        ),
        attach(
            'And this is your man.',
            CARP,
        ),
    ),
}
