"""The seven Great Clans, the houses, the Imperials, and two jokes about him.

Clans are reached by their own name OR by any of their Great Families (FR-016) -
*"if the Asako family is mentioned then that is the same as if the Phoenix clan
was mentioned."* The routing lives in `topics.py`; the material is here.

`imperial_families` is the ONE lore category the Character Sheet also answers
(FR-018), because the contrast is the joke. `merely_an_assistant` is the one
category he does NOT get (FR-021), because the insult only lands on the bot whose
own name contains his subordination.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing a line here.

This file scored best in the 2026-08-31 tone audit (20.8%) and the number was an
artifact: 22 of its 25 clears sat in `merely_an_assistant`, `nobody_important`
and `imperial_families`, three categories written to be about him in the first
place. The seven clans themselves were population tables with epigrams attached,
and `clan_crab`, `clan_crane` and `clan_unicorn` contained no first-person word
at all. Two overlaps were also removed here: `clan_unicorn` shared five of eight
lines with `gm_moto/unicorn_history` (the hay economy and the return now live
there, the families and the composition here), and `clan_phoenix` repeated the
Isawa Akuma sentence from `gm_religion/maho_bloodspeakers` verbatim.
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
        'Five hundred thousand samurai, the largest clan in the Empire, and they will '
        'tell you so, and then they will tell you again, and I will write down both '
        'occasions.',
        'Akodo rule. The Matsu are two hundred and seventy-five thousand of it, roughly '
        'twice the next largest family anywhere - a vassal family larger than most '
        'clans, which is the kind of arrangement that only survives by never being '
        'examined.',
        'Seventy-five domains, of which the Matsu alone hold forty-three, and the Matsu '
        'have several Karo Houses because one was not enough. Nothing about the Lion has '
        'ever been enough, and I hold the ledger that proves it.',
        'Ikoma fifty thousand, Kitsu twenty-five in a single domain, and Akodo Toturi '
        'holding the whole arrangement together with an authority that is mostly '
        'correspondence.',
        'They fight the Crane. They have always fought the Crane. Even the Emperor '
        'rarely orders it stopped, lest a clan conclude he has taken a side - so the '
        'longest war in the Empire continues for want of a phrasing.',
        'Militant is their self-conception. Administrative is what they actually are, '
        'like everybody else, and they would be genuinely offended to hear it from a '
        'record that proves it.',
        'The Damasu are a Karo House of the Akodo, which is why most of my campaign '
        'material lives in Lion lands, and why I know their granary schedules better '
        'than I know anything about myself.',
        'Ask about the Lion and you will get war. Ask about their granaries and you '
        'will get the truth, and the truth has never once been requested.',
        attach(
            'The Lion, as the Lion see themselves. Seventy-five domains of granary '
            'schedules, and this is the picture they commissioned.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What actually wins their wars, and what nobody has ever composed a poem about.',
            CARP,
        ),
    ),
    'clan_crab': (
        'Three hundred thousand samurai and one job, and the job never stops, and '
        'nobody sends thanks. I recognize the shape of that arrangement from the '
        'inside.',
        'Hida rule and are a hundred and seventy-five thousand of it. Yasuki '
        'seventy-five, Kaiu twenty-five, Kuni fifteen, Hiruma ten. Forty-four domains, '
        'all of them pointed the same direction.',
        'The Akito of the Hida is a Karo House whose daimyo is General of the Northern '
        'Armies - a title which exists because somebody had to be in charge of the '
        'direction the Crab are not facing.',
        'The Kaiu built the Wall and the Wall is why the Kaiu exist. Twenty-odd '
        'Imperial legions stand on it alongside them, and the Empire calls this a '
        'contribution rather than a dependency.',
        'The Kuni study what they hunt, which is the entire controversy and has never '
        'been resolved, because resolving it would require somebody else to do the '
        'hunting.',
        'The Hiruma are down to ten thousand in a single domain because the Maw '
        'destroyed most of their lands. That is not a history. That is a survival rate, '
        'and I had to write it as a number.',
        'The Yasuki invented the anti-corruption system and are the best smugglers in '
        'the Empire. Same family, both facts, nobody blinks. I blinked, once, and then '
        'filed it.',
        'They are blunt because subtlety is expensive and they are spending the money '
        'elsewhere. It is the only clan whose manners have a line in the budget.',
        attach(
            'What three hundred thousand samurai are pointed at, permanently, so that '
            'the other one and a half million never have to think about it.',
            KIDOMARU_TENGU,
        ),
        attach(
            'A Crab explaining the Wall to somebody who asked politely and now cannot leave.',
            SAKE_SAMURAI,
        ),
    ),
    'clan_crane': (
        'Two hundred and seventy-five thousand, and every one of them better dressed '
        'than you, and considerably better dressed than me, which took no effort at all '
        'on their part.',
        'Doji rule with a hundred thousand. Daidoji ninety, Kakita seventy-five, Asahina '
        'ten. Note that the family famous for poetry is outnumbered nine to one by the '
        'family famous for holding ground, and that the poetry is what travels.',
        'Daidoji Masamune forged Shitsuten as his final blade and poured all his hatred '
        'of the Yasuki into it. It works. A man made a functioning object out of a '
        'grudge, and I have been keeping grudges for four hundred sessions with nothing '
        'to show.',
        'Doji Masayo took that sword to the Toshi Ranbo tournament and won a province '
        'with it against the man expected to win. One afternoon, one blade, one border '
        'redrawn, and about nine hundred pages of consequence in my keeping.',
        'They fight the Lion perpetually and win about as often, which nobody expects '
        'from a clan famous for calligraphy - and which suggests the calligraphy was '
        'never the point.',
        'Refined is the self-conception. The Daidoji are ninety thousand soldiers and '
        'the refinement is a tactic, which I consider the single most successful piece '
        'of misdirection in the Empire.',
        'The Asahina are ten thousand and produce more trouble per capita than any '
        'family in the Empire. I have run that arithmetic twice because I did not '
        'believe it the first time.',
        'A clan that has made being underestimated into an inheritance. I am '
        'underestimated constantly and have not managed to monetize it.',
        attach(
            "The Crane's preferred method, and the one they would rather you remembered "
            'than the ninety thousand Daidoji standing behind it.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What they would rather be doing, and what they are extremely careful to '
            'let you believe they were doing instead.',
            INNER_VISION,
        ),
    ),
    'clan_scorpion': (
        'Two hundred and twenty-five thousand, and entirely trustworthy: they tell you '
        'what they will do to you, and then they do it. I have never had to correct a '
        'Scorpion entry, which is more than I can say for the Crane.',
        'Bayushi rule with a hundred and twenty-five thousand. Shosuro eighty, Soshi '
        'fifteen, Yogo five. Four families and not one of them has ever supplied me '
        'with a document I did not have to read twice.',
        'The Peasant Campaign is set in their lands, which is the cruelest available '
        'place to be a peasant with no rights and no name, and the record does not '
        'pretend otherwise.',
        'Soshi Saibankan is a Scorpion named judge. The Empire needs somebody to do the '
        'unpleasant necessary things and then it needs somebody to blame for them. Same '
        'clan. Extremely efficient, and they know exactly what they are.',
        'Bayushi Tangen carries Kurainigo, which is more famous than Tamashikari, which '
        'is only the fifth most famous blade they own. A clan with a deep bench of '
        'legendary swords and no interest in mentioning it.',
        'They keep good records. That is nearly the nicest thing I can say about '
        'anybody, and I am aware of how that reflects on my range.',
        'Every clan in this Empire has secrets. Only one has admitted it and gone into '
        'business, and it is the one the others find distasteful.',
        'Ask a Scorpion a direct question and receive a direct answer to a different '
        'one. I have transcribed dozens and I still cannot see the join.',
        attach(
            'A Scorpion negotiation, at the point everyone present understands it.',
            FOX_WOMAN,
        ),
        attach(
            'The version they let you see, which is also true, which is the difficulty.',
            CATS,
        ),
    ),
    'clan_unicorn': (
        'Two hundred and twenty-five thousand, and the only clan that has seen the '
        'outside and come back, which the rest of the Empire has decided to hold '
        'against them permanently.',
        'Shinjo rule with seventy-five thousand. Otaku also seventy-five, Moto forty, '
        'Ide twenty, Iuchi fifteen. Five families, one of which is a separate '
        'civilization, and the table does not indicate which.',
        'The Otaku are as large as the ruling Shinjo, which happens nowhere else '
        'without an argument, and here it produces no argument at all, which is '
        'somehow more unsettling.',
        'The Ide are diplomats and the Iuchi are shugenja and both families are small '
        'enough to be overlooked, and both of them have been decisive in my record '
        'while being overlooked.',
        'The Moto are theirs on paper. In practice the Moto are a separate civilization '
        'and even the Shinjo cannot count their tribes, which makes the Unicorn the '
        'only clan that does not know its own size.',
        'They came back with horses, habits and an entire people, and the Empire has '
        'spent two centuries deciding which of the three it objects to most. It has not '
        'concluded.',
        'A clan the rest of the Empire cannot quite trust, and they know it, and it has '
        'made them practical rather than bitter - a response I have studied and been '
        'unable to reproduce.',
        'Every other clan measures itself against its neighbors. This one has been '
        'somewhere with no neighbors, and it shows in every document they send me.',
        attach(
            'The crossing that made them, and the reason no other clan can quite look '
            'at them straight. Everyone here is provincial; only one clan found out.',
            GREAT_WAVE,
        ),
        attach(
            'What they came back with, and what the Empire chose to notice first.',
            ARCHERS,
        ),
    ),
    'clan_dragon': (
        'A hundred and seventy-five thousand, and enigmatic, which they work at, and '
        'which I have to summarize, which is the least summarizable assignment in this '
        'record.',
        'Togashi rule with twenty thousand. Mirumoto are a hundred and twenty-five '
        'thousand. Agasha fifteen, Kitsuki fifteen. A ruling family a sixth the size of '
        'its largest vassal, and nobody else is arranged that way, and the Dragon like '
        'it that way.',
        'The Ryusei domain of the Mirumoto is my worked example for lineages: six '
        'lineages holding ninety percent, three of them Unicorn refugees. I chose it as '
        'an example and have regretted it in every subsequent explanation.',
        'The Kitsuki investigate, and Kitsuki Fu holds the Order of the Precious Crown '
        'for the Forgotten Tomb. A family of investigators in a clan devoted to not '
        'explaining itself - somebody enjoyed setting that up.',
        'Prince Daigotsu said Kitsu Okura was more enigmatic than the Dragon Clan he '
        'derides, which is the sharpest thing anybody has said about either of them and '
        'was said by a third party who was not asked.',
        'Mirumoto. One letter from Miyamoto. In a game named after the Book of Five '
        'Rings. Do not get me started.',
        'Seiginryu came off Togashi Mountain by the eastern paths, which are confusing '
        'and otherworldly, and I have the account, and the account is confusing and '
        'otherworldly, and I have read it four times.',
        'A clan that cultivates mystery and then keeps a family of detectives. I would '
        'call it a contradiction if I had not watched it work.',
        attach(
            "The Dragon's mountain, and the reputation that arrived before anybody did.",
            KIDOMARU_TENGU,
        ),
        attach(
            'A Kitsuki investigation concluding. Note that nothing has been explained '
            'to anybody present.',
            INNER_VISION,
        ),
    ),
    'clan_phoenix': (
        'A hundred and seventy-five thousand, spiritual, and sitting on the most '
        'embarrassing founding story in the Empire, which they would prefer to discuss '
        'another time, forever.',
        'Shiba rule with a hundred thousand. Isawa sixty, Asako fifteen - except the '
        'Isawa are not ruled by a daimyo at all. They are ruled by the Council of '
        'Elemental Masters, the only Great Family arranged that way.',
        'And Shiba bent his knee to Isawa at the dawn of the Empire. The ruling family '
        'knelt to its own vassal. They have been explaining it ever since and the '
        'explanation has grown, not shortened.',
        'Isawa himself practiced maho. The founder. He made totems with the crafting '
        'discipline and stored the power of names and wounds in them, and the Empire '
        'wrote it down under crafting and moved along.',
        'Then Isawa Akuma, in the third century, achieved what nobody has repeated or '
        'accounted for. The Phoenix have a prepared answer about the kneeling and have '
        'never been asked to prepare one about him.',
        'So the clan famous for renouncing blood magic is the clan whose founder '
        'practiced it and whose most cunning son perfected it. I did not arrange that. '
        'I only have to keep it in order.',
        'It is also the one clan this campaign has never been set in, which I notice, '
        'and which I am not going to speculate about in a channel he can read.',
        'A clan of scholars whose own history is the one document they have declined to '
        'audit. I would find that funnier if it were not so restful to watch.',
        attach(
            'The Phoenix, as they would prefer to be understood.',
            INNER_VISION,
        ),
        attach(
            'The founding they do not put on the scrolls, and which is in mine.',
            FOX_WOMAN,
        ),
    ),
    # ---- houses -------------------------------------------------------------
    'famous_houses': (
        'A Family has a ruling house and a number of vassal houses, and each house '
        'holds a domain with a daimyo. That is the unit that actually governs, and it '
        'is the unit nobody ever names when they write to me.',
        'The largest Families, roughly a hundred thousand samurai and up, also have '
        'Karo Houses among their vassals, comparable in size to the ruling domain '
        'itself. A vassal as large as the lord, by design, on purpose, deliberately.',
        'The Akito of the Hida, whose daimyo is General of the Northern Armies of the '
        'Crab. The Tsume of the Doji. The Damasu of the Akodo. Three houses, three '
        'entirely different reasons, and one filing convention holding them together.',
        'The Matsu, being twice the size of anybody else, have several. Of course they '
        'do. Nothing about the Matsu has ever stopped at one.',
        'A Karo House is headed by a senior vassal daimyo with specialized military or '
        'administrative duties. Not a lesser thing. A specialized one, and I would '
        'appreciate the same distinction being extended in my direction.',
        '`Akodo no Damasu` is a family and a house. It is not a person. A person is '
        '`Akodo no Damasu Kojima`, and I will keep saying this.',
        'Smaller families are one undivided domain under the family daimyo, because '
        'they are too small to threaten anybody and so nobody makes them subdivide. '
        'Obscurity as an administrative convenience; I know the feeling.',
        'Name the HOUSE and I can tell you who rules it in one sentence. Name the '
        'family and we will be here until somebody needs the channel.',
        attach(
            'Two houses discussing a boundary.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The Chancellery meeting that follows, which takes four months and settles '
            'the same amount.',
            CATS,
        ),
    ),
    'damasu': (
        'A Karo House of the Akodo, which is why every Damasu samurai carries the Akodo '
        'name, and why every person who asks me about them asks about the wrong half of '
        'it.',
        'Akodo is the family. "no Damasu" says he is of the Damasu house. Then the '
        'personal name. Their previous daimyo was Akodo no Damasu Kojima, and I have '
        'now explained that construction so many times it has worn a groove.',
        'Their current daimyo is Akodo no Damasu Chiho, who carries Amatsukami no Ken, '
        "the Heavenly Sovereign's Sword. A sword with a grander title than any office I "
        'will ever hold, and it does not have to remember anything.',
        'They lost Tango province at the Toshi Ranbo tournament when Doji Masayo killed '
        'Akodo no Damasu Tsuo with Shitsuten. Tsuo was expected to win, and the word '
        '"expected" is carrying an entire province.',
        "A Karo House is comparable in size to the ruling daimyo's own domain. The "
        'Damasu are not a minor branch and would take the suggestion extremely poorly, '
        'in writing, at length, to me.',
        'They have their own lineages, their own temples and their own Order of '
        'Bishamon with its own Grand Abbot - a house that has assembled, piece by '
        'piece, everything a clan has except the name.',
        'Forty-seven mentions in the record, which is more than most Great Families '
        'manage, and every one of them logged by somebody who was not invited.',
        'If you want to know what this campaign is about, it is not the Empire. It is '
        'one Karo House and the people adjacent to it, and I worked that out from the '
        'index alone.',
        attach(
            'Amatsukami no Ken. Ancestral, and currently in use, which is rarer than '
            'the word ancestral suggests.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The tournament that cost them a province, on the morning of, when it was '
            'still a formality.',
            RAINY_MOON,
        ),
    ),
    # ---- the Imperials. The GM Assistant's half of the joke -----------------
    'imperial_families': (
        'The Imperial families. Oh, they are wonderful. Truly. I have nothing bad to '
        'say about them. Out loud. In public.',
        'Seppun forty-five thousand, Hantei fifteen, Otomo ten, Miya five. Seventy-five '
        'thousand all told, and a hundred million souls arrange themselves around them, '
        'which is a ratio I have chosen to describe as impressive.',
        'The Hantei are the SMALLEST but for the Miya, despite containing the Emperor '
        'himself. They marry outward. I am certain there is a very good reason and I am '
        'certain it is not my place to record which one.',
        'Every domain has an Imperial Magistrate whose duties are set by the Emerald '
        'Charter - twenty-five yoriki in the capital, five in each provincial city. A '
        'beautifully designed system. I admire it at the volume permitted to me.',
        "Almost all of those yoriki come from OTHER clans, because a daimyo's own "
        'people cannot be trusted to audit the daimyo. A wise arrangement. Very wise. I '
        'note that nobody audits the auditors and I note it quietly.',
        'The Otomo and the Miya are five and ten thousand and carry weight out of all '
        'proportion to either number, which is of course entirely appropriate and not '
        'at all the sort of thing one remarks upon.',
        'Emerald magistrates can assemble yoriki from nearby domains to assist one side '
        'of a fight. Two hundred extra troops decides battles. They are not shy about '
        'it, and I am not permitted to be anything but admiring about it.',
        'I record everything, which means I have opinions I am structurally prevented '
        'from expressing. The Imperial families are where that is most keenly felt.',
        attach(
            'The Imperial dignity. I have nothing further.',
            INNER_VISION,
        ),
        attach(
            'A provincial daimyo being audited. Note the enthusiasm. Note it carefully; '
            'I am not going to describe it.',
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
            'The man you are asking to speak to. He is busy. He has been busy for four '
            'hundred sessions.',
            SAKE_SAMURAI,
        ),
    ),
    # ---- anyone name-shaped with no category of their own (FR-007) ---------
    'nobody_important': (
        'Are you asking me about specific individuals? Come on. That guy is a loser. '
        'Why are you even bothering?',
        'There are two million samurai in this Empire. You have picked one. Out of two '
        'million. And it is that one.',
        'I do not have an entry. If he had done anything, he would have an entry. The '
        'system is not subtle and it is not kind.',
        'That is a name, yes. It is not a person I have been given any reason to '
        'remember, and I remember things for a living, so consider what that took.',
        'Ask about his HOUSE and I can help. Ask about him and we are both '
        'wasting an evening I was not going to be paid for anyway.',
        'Five thousand samurai in a median domain and you want that one. I have '
        'nothing. I would tell you if I had something; I would enjoy having something.',
        'I keep the record of people who did things. It is shorter than you would hope, '
        'and he is not in it, and neither am I, and I take a certain comfort in the '
        'company.',
        'Somewhere out there is a man being nobody in particular, entirely unaware that '
        'he has just been discussed. That is the closest thing to peace in this Empire '
        'and he is squandering it.',
        attach(
            'Here is somebody who DID do something, for comparison.',
            MUSASHI_BAT,
        ),
        attach(
            'Your man, at true scale, in his natural condition.',
            CARP,
        ),
    ),
}
