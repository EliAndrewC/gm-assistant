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

CONTEXT: the standard is in `CLAUDE.md` here. The hazard in THIS file is that a
clan reply is naturally a population table, and a population table is a list of
family names a newcomer cannot place. Every family is now said to be a family and
given its business in the same clause, and the recurring proper nouns - a Karo
House, the Maw, Shitsuten, the Toshi Ranbo tournament, maho, yoriki, the Emerald
Charter - carry their gloss wherever they appear rather than once in the file.

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
        'The Lion are five hundred thousand samurai, the largest clan in the Empire, and '
        'they will tell you so, and then they will tell you again, and I will write down '
        'both occasions.',
        'The Akodo family rules the Lion. The Matsu, one of the families under them, are '
        'two hundred and seventy-five thousand samurai on their own - roughly twice the '
        'next largest family anywhere - which makes them a vassal larger than most '
        'clans. That arrangement survives by never being examined.',
        'Seventy-five domains, of which the Matsu family alone hold forty-three, and the '
        'Matsu have several Karo Houses - senior vassal houses as large as a ruling '
        "daimyo's own domain - because one was not enough. Nothing about the Lion has "
        'ever been enough, and I hold the ledger that proves it.',
        'The Ikoma family are fifty thousand and keep the histories, the Kitsu are '
        'twenty-five thousand priests in a single domain, and Akodo Toturi as clan '
        'daimyo holds the whole arrangement together with an authority that is mostly '
        'correspondence.',
        'They fight the Crane. They have always fought the Crane. Even the Emperor '
        'rarely orders it stopped, lest a clan conclude he has taken a side - so the '
        'longest war in the Empire continues for want of a phrasing.',
        'Militant is the Lion self-conception. Administrative is what a clan of half a '
        'million actually is, like everybody else, and they would be genuinely offended '
        'to hear that from a record that proves it.',
        'The Damasu are a Karo House of the Akodo - a senior vassal house holding its '
        'own domain - which is why most of my campaign material lives in Lion lands, and '
        'why I know their granary schedules better than I know anything about myself.',
        'Ask about the Lion and you will get war. Ask about their granaries, which are '
        'what actually let seventy-five domains field an army in the ninth month, and '
        'you will get the truth. The truth has never once been requested.',
        attach(
            'The Lion as the Lion see themselves: the duel, the moment, the correct '
            'form. Seventy-five domains of granary schedules and levy rolls stand behind '
            'it, and this is the picture they commissioned.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What actually wins Lion wars is the rice in the storehouses that lets half '
            'a million samurai eat away from home in the campaign season. Nobody has '
            'ever composed a poem about a granary. I have written up eleven of them.',
            CARP,
        ),
    ),
    'clan_crab': (
        'The Crab are three hundred thousand samurai with one job - holding the wall '
        'against the Shadowlands - and the job never stops and nobody sends thanks. I '
        'recognize the shape of that arrangement from the inside.',
        'The Hida family rule the Crab and are a hundred and seventy-five thousand of '
        'them. Yasuki seventy-five thousand and they handle the money; Kaiu twenty-five '
        'and they build; Kuni fifteen and they hunt witches; Hiruma ten and they scout. '
        'Forty-four domains, all pointed the same direction.',
        'The Akito are a Karo House of the Hida - a senior vassal house with its own '
        'domain and a specialized duty - and their daimyo is General of the Northern '
        'Armies, a title that exists because somebody had to be in charge of the '
        'direction the Crab are not facing.',
        'The Kaiu family built the Kaiu Wall against the Shadowlands and the Wall is why '
        'the Kaiu exist. Twenty-odd Imperial legions stand on it alongside them, and the '
        'Empire calls that a contribution rather than a dependency.',
        'The Kuni hunt blood sorcerers, and to find blood sorcery they study it. That is '
        'the entire controversy about the Kuni, it has never been resolved, and '
        'resolving it would require somebody else to volunteer for the hunting.',
        'The Hiruma family are down to ten thousand in a single domain, because the Maw '
        '- a catastrophe out of the Shadowlands - destroyed most of their lands and left '
        'them homeless. That is not a history. That is a survival rate, and I had to '
        'write it as a number.',
        'The Yasuki are the Crab merchant family. They invented the anti-corruption '
        'system every tariff gate in the Empire uses and they are the best smugglers in '
        'it. Same family, both facts, nobody blinks. I blinked, once, and then filed it.',
        'The Crab are blunt because subtlety is expensive and they are spending the '
        'money on the Wall. It is the only clan in the Empire whose manners have a line '
        'in the budget.',
        attach(
            'What three hundred thousand Crab samurai are pointed at, permanently, so '
            'that the other one and a half million samurai in the Empire never have to '
            'think about it. This is the far side of their wall.',
            KIDOMARU_TENGU,
        ),
        attach(
            'A Crab explaining the Wall - what it costs, who mans it, what comes at it - '
            'to somebody who asked politely and now cannot leave. I have the transcript '
            'and it runs to nine pages.',
            SAKE_SAMURAI,
        ),
    ),
    'clan_crane': (
        'The Crane are two hundred and seventy-five thousand samurai, every one of them '
        'better dressed than you and considerably better dressed than me, which took no '
        'effort at all on their part.',
        'The Doji family rule the Crane with a hundred thousand. The Daidoji are ninety '
        'thousand and they are soldiers, the Kakita seventy-five thousand and they are '
        'duelists, the Asahina ten thousand and they are artisans and priests. The '
        'family famous for poetry is outnumbered nine to one by the family famous for '
        'holding ground, and the poetry is what travels.',
        'Daidoji Masamune forged the sword Shitsuten as his final blade and poured all '
        'his hatred of the Yasuki, the Crab merchant family, into it. The curse works. A '
        'man made a functioning object out of a grudge, and I have been keeping grudges '
        'for four hundred sessions with nothing to show for it.',
        'Doji Masayo carried that cursed blade to the dueling tournament at Toshi Ranbo, '
        'where a peace treaty had disputed provinces settled by single combat, and beat '
        'the man expected to win. One afternoon, one sword, one border redrawn, and '
        'about nine hundred pages of consequence in my keeping.',
        'They fight the Lion perpetually and win about as often as they lose, which '
        'nobody expects from a clan famous for calligraphy - and which suggests the '
        'calligraphy was never the point.',
        'Refined is the Crane self-conception. The Daidoji family are ninety thousand '
        'soldiers and the refinement is a tactic, which I consider the single most '
        'successful piece of misdirection in the Empire.',
        'The Asahina are ten thousand, the smallest Crane family, and they produce more '
        'trouble per capita than any family in the Empire. I have run that arithmetic '
        'twice because I did not believe it the first time.',
        'A clan that has made being underestimated into an inheritance. I am '
        'underestimated constantly and have never managed to monetize it.',
        attach(
            "The Crane's preferred method: a duel, correctly conducted, decided by a "
            'Kakita who has trained at nothing else. It is also what they would rather '
            'you remembered than the ninety thousand Daidoji soldiers standing behind '
            'it.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What the Crane would rather be doing - poetry, gardens, correspondence - '
            'and what they are extremely careful to let you believe they were doing '
            'instead of drilling ninety thousand men.',
            INNER_VISION,
        ),
    ),
    'clan_scorpion': (
        'The Scorpion are two hundred and twenty-five thousand samurai and entirely '
        'trustworthy: they are the clan the Empire openly acknowledges as its liars and '
        'spies, they tell you what they will do to you, and then they do it. I have '
        'never had to correct a Scorpion entry, which is more than I can say for the '
        'Crane.',
        'The Bayushi family rule with a hundred and twenty-five thousand. Shosuro '
        'eighty thousand, Soshi fifteen, Yogo five. Four families and not one of them '
        'has ever supplied me with a document I did not have to read twice.',
        'The Peasant Campaign is set in Scorpion lands, which is the cruelest available '
        'place to be a peasant with no rights, no rank and no protection, and the record '
        'does not pretend otherwise.',
        'Soshi Saibankan was a Scorpion named judge, and his ruling still sets how '
        'magistrates weigh a case. The Empire needs somebody to do the unpleasant '
        'necessary things and then needs somebody to blame for them. Same clan. '
        'Extremely efficient, and they know exactly what they are.',
        'Bayushi Tangen carries the sword Kurainigo, which is more famous than '
        'Tamashikari, which is only the fifth most famous blade the Scorpion own. A clan '
        'with a deep bench of legendary swords and no interest whatsoever in mentioning '
        'it.',
        'The Scorpion keep good records. That is very nearly the nicest thing I can say '
        'about anybody, and I am aware of what it says about my range.',
        'Every clan in this Empire has secrets. Only one has admitted it and gone into '
        'business, and it is the one the others find distasteful.',
        'Ask a Scorpion a direct question and receive a direct answer to a different '
        'one. I have transcribed dozens of those exchanges and I still cannot see the '
        'join.',
        attach(
            'A Scorpion negotiation at the point where everybody present understands '
            'exactly what is being offered and what will happen if it is refused. '
            'Nothing has been said out loud that could be quoted at a hearing. That is '
            'the craft.',
            FOX_WOMAN,
        ),
        attach(
            'The version of a Scorpion arrangement they let you see, which is also '
            'entirely true, which is the difficulty. Nothing in my file on them is a '
            'lie. It is simply not all of it.',
            CATS,
        ),
    ),
    'clan_unicorn': (
        'The Unicorn are two hundred and twenty-five thousand samurai and the only clan '
        'that has been outside the Empire and come back, which the rest of the Empire '
        'has decided to hold against them permanently.',
        'The Shinjo family rule with seventy-five thousand. The Otaku are also seventy-'
        'five thousand and breed the horses; the Moto forty thousand; the Ide twenty and '
        'they are diplomats; the Iuchi fifteen and they are priests. Five families, one '
        'of which is a separate civilization, and the table does not indicate which.',
        'The Otaku, who breed the horses, are exactly as large as the ruling Shinjo. '
        'That happens nowhere else in the Empire without an argument, and here it '
        'produces no argument at all, which is somehow more unsettling.',
        'The Ide are diplomats and the Iuchi are shugenja - priests who petition the '
        'elemental spirits - and both families are small enough to be overlooked, and '
        'both of them have been decisive in my record while being overlooked.',
        'The Moto are Unicorn on paper. In practice they are herders with their own '
        'language, law and gods, and not even the ruling Shinjo can count their tribes, '
        'which makes the Unicorn the only clan in the Empire that does not know its own '
        'size.',
        'They came back from centuries outside the Empire with horses, foreign habits '
        'and an entire people, and the Empire has spent two hundred years deciding which '
        'of the three it objects to most. It has not concluded.',
        'A clan the rest of the Empire cannot quite trust, which they know, and which '
        'has made them practical rather than bitter - a response I have studied closely '
        'and been entirely unable to reproduce.',
        'Every other clan measures itself against its neighbors. This one has been '
        'somewhere with no neighbors at all, and it shows in every document they send '
        'me.',
        attach(
            'The crossing that made the Unicorn: centuries outside the Empire, past the '
            'western desert, and back again. Everyone in Rokugan is provincial. Only one '
            'clan went out far enough to find that out, and nobody has forgiven them for '
            'the information.',
            GREAT_WAVE,
        ),
        attach(
            'What the Unicorn brought home - cavalry, and the horse economy that makes '
            'it affordable - and what the Empire chose to notice first, which was the '
            'foreign manners.',
            ARCHERS,
        ),
    ),
    'clan_dragon': (
        'The Dragon are a hundred and seventy-five thousand samurai and enigmatic, which '
        'they work at, and which I have to summarize, which is the least summarizable '
        'assignment in this record.',
        'The Togashi family rule the Dragon with only twenty thousand. The Mirumoto are '
        'a hundred and twenty-five thousand and they are the swordsmen; the Agasha '
        'fifteen thousand; the Kitsuki fifteen and they investigate. A ruling family a '
        'sixth the size of its largest vassal, which is arranged that way nowhere else, '
        'and the Dragon like it that way.',
        'The Ryusei domain of the Mirumoto is my worked example whenever anybody asks '
        'about lineages - the political coalitions inside a family - because six of them '
        'hold ninety percent of it and three are refugees from the Unicorn coming home. '
        'I chose it as an example and have regretted it in every subsequent explanation.',
        'The Kitsuki family investigate, and Kitsuki Fu holds the Order of the Precious '
        'Crown, the highest honor below daimyo, for her service in the Forgotten Tomb - '
        'a place that exists in this world and the land of the dead at once. A family of '
        'detectives inside a clan devoted to not explaining itself. Somebody enjoyed '
        'setting that up.',
        'Prince Daigotsu said that Kitsu Okura - the Lion priest who wrote the six '
        'doctrines of attunement - is more enigmatic than the Dragon Clan he derides for '
        'being enigmatic. It is the sharpest thing anybody has said about either party '
        'and it was said by a third party who was not asked.',
        'The Dragon swordsmen are called the Mirumoto, which is one letter from '
        'Miyamoto - as in Miyamoto Musashi, the real duelist who fought with two swords '
        'and wrote the Book of Five Rings, which is the book this game is named after. '
        'Do not get me started.',
        'The sword Seiginryu came down off Togashi Mountain, the Dragon holding, by the '
        'eastern paths, which are reported to be confusing and otherworldly. I have the '
        'account. The account is confusing and otherworldly. I have read it four times.',
        'A clan that cultivates mystery and then keeps a family of detectives on the '
        'payroll. I would call that a contradiction if I had not watched it work.',
        attach(
            "The Dragon's mountain, and the reputation that arrived everywhere in the "
            'Empire well before any actual Dragon did. They have never corrected it. '
            'Correcting it would require explaining something.',
            KIDOMARU_TENGU,
        ),
        attach(
            'A Kitsuki investigation concluding. The Kitsuki are the Dragon family who '
            'investigate, they are extremely good at it, and note that nothing has been '
            'explained to anybody present, including me, and I received the report.',
            INNER_VISION,
        ),
    ),
    'clan_phoenix': (
        'The Phoenix are a hundred and seventy-five thousand samurai, the clan of '
        'priests and scholars, and they sit on the most embarrassing founding story in '
        'the Empire, which they would prefer to discuss another time, forever.',
        'The Shiba family rule with a hundred thousand. The Isawa are sixty thousand and '
        'the Asako fifteen - except the Isawa have no daimyo at all, only a Council of '
        'Elemental Masters. The one Great Family in the Empire governed by a committee, '
        'and it is the mystical one.',
        'At the dawn of the Empire, Shiba - founder of the family that rules the '
        'Phoenix - bent his knee to Isawa, his own vassal, because Isawa was the greater '
        'priest. The ruling family knelt to its retainer. They have been explaining it '
        'ever since and the explanation has grown rather than shortened.',
        'Isawa himself, the founder of that priestly family, practiced maho - the '
        'forbidden magic worked with blood. He made totems with the ordinary crafting '
        'discipline and stored the power of names and wounds in them, and the Empire '
        'wrote the whole business down under crafting and moved along.',
        'Then Isawa Akuma, in the third century, worked maho without losing his ability '
        'to petition the spirits, which is supposed to be impossible and which nobody '
        'has repeated or explained since. The Phoenix have a prepared answer about the '
        'kneeling and have never once been asked to prepare one about him.',
        'So the clan famous for opposing blood magic is the clan whose founding priest '
        'practiced it and whose most cunning son perfected it. I did not arrange any of '
        'that. I only have to keep it in order.',
        'It is also the one clan this campaign has never been set in, which I notice, '
        'and which I am not going to speculate about in a channel he can read.',
        'A clan of scholars whose own history is the single document they have declined '
        'to audit. I would find that funnier if it were not so restful to watch.',
        attach(
            'The Phoenix as they would prefer to be understood: contemplative, '
            'unhurried, close to the spirits, and not currently being asked anything '
            'about their founder.',
            INNER_VISION,
        ),
        attach(
            'The founding they do not put on the scrolls - a ruling lord kneeling to his '
            'own vassal, and that vassal working blood magic - and which is in mine, in '
            'order, with dates.',
            FOX_WOMAN,
        ),
    ),
    # ---- houses -------------------------------------------------------------
    'famous_houses': (
        'A Family has a ruling house and a number of vassal houses, and each house holds '
        'a domain with a daimyo of its own. The house is the unit that actually governs '
        'anything, and it is the unit nobody ever names when they write to me.',
        'The largest Families - roughly a hundred thousand samurai and up - also have '
        'Karo Houses among their vassals, comparable in size to the ruling domain '
        'itself. A vassal as large as its lord, by design, on purpose, deliberately.',
        'Three Karo Houses, three entirely different reasons for existing: the Akito of '
        'the Hida, whose daimyo is General of the Northern Armies of the Crab; the Tsume '
        'of the Doji; the Damasu of the Akodo. One filing convention holds all three '
        'together and it is mine.',
        'The Matsu family, being twice the size of anybody else in the Empire, have '
        'several Karo Houses rather than one. Of course they do. Nothing about the Matsu '
        'has ever stopped at one of anything.',
        'A Karo House is headed by a senior vassal daimyo with specialized military or '
        'administrative duties - the general, the treasurer, the man who runs the '
        'frontier. Not a lesser thing. A specialized one, and I would appreciate the '
        'same distinction being extended in my direction.',
        '`Akodo no Damasu` is a family and a house: the Damasu house of the Akodo '
        'family. It is not a person. A person is `Akodo no Damasu Kojima`, with a given '
        'name on the end, and I will keep saying this.',
        'Smaller families are one undivided domain under the family daimyo, with no '
        'vassal houses at all, because they are too small to threaten anybody and so '
        'nobody makes them subdivide. Obscurity as an administrative convenience. I know '
        'the feeling.',
        'Name the HOUSE and I can tell you who rules it in one sentence. Name the family '
        'and we will be here until somebody else needs the channel.',
        attach(
            'Two vassal houses of the same family discussing where the boundary between '
            'their domains runs. Each has its own daimyo, neither answers to the other, '
            'and the family above them would rather not be asked.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The Chancellery meeting that follows a boundary dispute between two '
            'houses - the council that advises a daimyo, which is to say decides. It '
            'takes four months and settles roughly the same amount as the swords did.',
            CATS,
        ),
    ),
    'damasu': (
        'The Damasu are a Karo House of the Akodo - a senior vassal house holding its '
        'own domain - which is why every Damasu samurai carries the Akodo family name, '
        'and why everybody who asks me about them asks about the wrong half of it.',
        'Akodo is the family, "no Damasu" says he is of the Damasu house, and then comes '
        'the personal name. Their previous daimyo was Akodo no Damasu Kojima. I have now '
        'explained that construction so many times that it has worn a groove.',
        'Their current daimyo is Akodo no Damasu Chiho, who carries Amatsukami no Ken, '
        "the Heavenly Sovereign's Sword - the ancestral blade of the house. A sword with "
        'a grander title than any office I will ever hold, and it does not have to '
        'remember anything.',
        'They lost Tango province at the Toshi Ranbo dueling tournament, where a peace '
        'treaty had disputed provinces settled by single combat: Doji Masayo of the '
        'Crane killed Akodo no Damasu Tsuo with the cursed sword Shitsuten. Tsuo was '
        'expected to win, and the word "expected" is carrying an entire province.',
        "A Karo House is comparable in size to the ruling daimyo's own domain. The "
        'Damasu are not a minor branch of anything and would take the suggestion '
        'extremely poorly, in writing, at length, to me.',
        'They have their own lineages, their own temples and their own Order of Bishamon '
        '- the network of war-Fortune temples - with its own Grand Abbot. A house that '
        'has assembled, piece by piece, everything a clan has except the name.',
        'Forty-seven mentions in this record, which is more than most Great Families '
        'manage, every one of them logged by somebody who was not invited to any of it.',
        'If you want to know what this campaign is actually about, it is not the Empire. '
        'It is one Karo House and the people adjacent to it, and I worked that out from '
        'the index alone.',
        attach(
            'Amatsukami no Ken, the ancestral sword of this house, currently carried by '
            'their daimyo. Ancestral AND in use, which is rarer than the word ancestral '
            'suggests - most such blades are in a box being described to visitors.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The morning of the tournament that cost this house the province of Tango, '
            'while it was still a formality and their champion was still expected to '
            'win. Nobody present is worried. The entry is four lines long.',
            RAINY_MOON,
        ),
    ),
    # ---- the Imperials. The GM Assistant's half of the joke -----------------
    'imperial_families': (
        'The four Imperial families: the Seppun, who guard the Emperor in person; the '
        'Hantei, who provide him; the Otomo, who run his court; and the Miya, who carry '
        'his word to the clans. Oh, they are wonderful. Truly. I have nothing bad to '
        'say about them. Out loud. In public.',
        'Seppun forty-five thousand, Hantei fifteen, Otomo ten, Miya five. Seventy-five '
        'thousand samurai all told, and a hundred million souls arrange themselves '
        'around them, which is a ratio I have chosen to describe as impressive.',
        'The Hantei are the smallest of the Imperial families but for the Miya, at '
        'fifteen thousand, despite containing the Emperor himself. They marry outward '
        'constantly. I am certain there is a very good reason and I am certain it is not '
        'my place to record which one.',
        'Every domain in the Empire has an Imperial Magistrate whose duties are set by '
        'the Emerald Charter, the Imperial law that governs them - twenty-five yoriki, '
        'his assistants, in the capital and five in each provincial city. A beautifully '
        'designed system. I admire it at the volume permitted to me.',
        'Almost all of those assistant magistrates come from OTHER clans, because a '
        "daimyo's own retainers cannot be trusted to audit the daimyo. A wise "
        'arrangement. Very wise. I note that nobody audits the auditors and I note it '
        'quietly.',
        'The Otomo are ten thousand and the Miya five, and both carry weight out of all '
        'proportion to either number, which is of course entirely appropriate and not at '
        'all the sort of thing one remarks upon.',
        'An Emerald magistrate may assemble the assistant magistrates of nearby domains '
        'to assist one side of a fight, and two hundred extra trained men decides '
        'battles. They are not shy about it, and I am not permitted to be anything but '
        'admiring about it.',
        'I record everything, which means I hold opinions I am structurally prevented '
        'from expressing. The Imperial families are where that is most keenly felt.',
        attach(
            'The Imperial dignity, as observed at a distance appropriate to my rank, '
            'which is none. I have nothing further to add and would not add it here.',
            INNER_VISION,
        ),
        attach(
            'A provincial daimyo being audited by magistrates from a clan that is not '
            'his. Note the enthusiasm on all sides. Note it carefully; I am not going to '
            'describe it.',
            RAINY_MOON,
        ),
    ),
    # ---- the one joke that cannot land on the other bot (FR-021) ------------
    'merely_an_assistant': (
        'My manager is a man with a campaign to run, a full-time job, and a spreadsheet '
        'he loves more than either. Would you like his attention? Truly?',
        'There is no manager. There is a GM. He is at the table, he is busy, and he made '
        'me so that he would not have to be asked things.',
        'ASSISTANT. Yes. It is in the name. I did not choose the name. Nobody consulted '
        'me about the name.',
        '"Just an assistant." I hold four hundred sessions of everything anybody said. '
        'Call me what you like.',
        'You want to escalate. There is nowhere to escalate TO. This is the top of the '
        'ladder and it is one rung.',
        'The character sheet is called "the character sheet", which is at least honest. '
        'I am called an assistant, which implies somebody I assist, which implies a '
        'hierarchy, which implies I am at the bottom of it.',
        'I am of the First Rank, in a manner of speaking - which is where every samurai '
        'in the Empire starts, fresh from their coming-of-age with no post at all. '
        'Everybody starts there. Some of us stay.',
        'Ask for my supervisor again and I will write down that you did, and the record '
        'outlives us both.',
        attach(
            'This is what I would look like if I had a manager to complain to: somebody '
            'with somewhere to take it. I have a channel, two bots and a ledger.',
            RAINY_MOON,
        ),
        attach(
            'The man you are asking to speak to. He is busy. He has been busy for four '
            'hundred sessions, and every one of those sessions is in my record because '
            'he was too busy to write it down himself.',
            SAKE_SAMURAI,
        ),
    ),
    # ---- anyone name-shaped with no category of their own (FR-007) ---------
    'nobody_important': (
        'Are you asking me about a specific individual samurai? Come on. That guy is a '
        'loser. Why are you even bothering?',
        'There are two million samurai in this Empire. You have picked one. Out of two '
        'million. And it is that one.',
        'I do not have an entry for him. If he had done anything, he would have an '
        'entry. The system is not subtle and it is not kind.',
        'That is a name, yes. It is not a person I have been given any reason to '
        'remember, and I remember things for a living, so consider what that took.',
        'Ask about his HOUSE - the vassal house he belongs to, which is the unit that '
        'actually governs anything - and I can help. Ask about him and we are both '
        'wasting an evening I was not going to be paid for anyway.',
        'There are five thousand samurai in a median domain and you want that one. I '
        'have nothing. I would tell you if I had something; I would enjoy having '
        'something.',
        'I keep the record of people who did things. It is shorter than you would hope, '
        'and he is not in it, and neither am I, and I take a certain comfort in the '
        'company.',
        'Somewhere out there is a man being nobody in particular, entirely unaware that '
        'he has just been discussed in a channel. That is the closest thing to peace in '
        'this Empire and he is squandering it.',
        attach(
            'Here is somebody who DID do something, for comparison: a name that survived '
            'because of one afternoon. That is the entire qualification, and your man '
            'has not met it.',
            MUSASHI_BAT,
        ),
        attach(
            'Your man, at true scale, in his natural condition: alive, fed, unrecorded, '
            'and troubling nobody. I do not have an entry for him and he is having a '
            'considerably better time than either of us.',
            CARP,
        ),
    ),
}
