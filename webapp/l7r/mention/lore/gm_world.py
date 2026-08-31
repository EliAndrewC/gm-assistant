"""Villains, metaplot, and the campaigns. GM Assistant only."""

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
    attach,
)

WORLD: dict[str, tuple[str, ...]] = {
    'iuchiban': (
        'Iuchiban. Everyone reaches for that name and almost nobody wants the actual history.',
        'He staged a coup. It failed in the way that leaves the Empire changed anyway.',
        'And then he was resurrected, which is the part that makes him a metaplot '
        'rather than an entry.',
        'He is the most famous bloodspeaker and he is not the first. That distinction '
        'matters and nobody makes it.',
        'The Gozoku is a separate problem that keeps arriving in the same sentence as '
        'him. They are not the same thing.',
        'Hantei the 16th sits in the middle of all of it and history has been unkind '
        'in the usual selective way.',
        'His lieutenants are the interesting reading. He is the name; they are the mechanism.',
        'You want him to be the reason. He is usually the excuse.',
        attach(
            'The shape the stories give him.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what he actually does to a court, over years.',
            FOX_WOMAN,
        ),
    ),
    'iuchibans_lieutenants': (
        'The lieutenants. Jama no Iuchiban Suru, Jama Musume, Asahina Yajinden, Jama '
        'no Iuchiban Kyoso, Jama no Iuchiban Kohaku.',
        'The "Jama no Iuchiban" construction is doing what a house name does. Read it '
        'that way and the whole group makes more sense.',
        'Asahina Yajinden is the one people flinch at, being a Crane name attached to that list.',
        'Jama Musume is the one I would worry about, and I am not going to elaborate '
        'in an open channel.',
        'Lieutenants outlive principals. That is the recurring lesson and nobody learns it.',
        'Each of them is a separate problem with a separate solution. Treating them as '
        'one problem is how this goes badly.',
        'A conspiracy with named subordinates is a conspiracy that has been running '
        'long enough to need an organizational chart.',
        'Ask me about one of them specifically and I will tell you what they are for.',
        attach(
            'Five of them, and only one gets painted.',
            KIDOMARU_TENGU,
        ),
        attach(
            'This is how one of them looks in a court. Note that nothing is wrong.',
            FOX_WOMAN,
        ),
    ),
    'the_gozoku': (
        'The Gozoku. A conspiracy of great families to control the throne without sitting on it.',
        'Which is a far more Rokugani ambition than open rebellion, and far harder to prosecute.',
        'It keeps appearing in the same sentence as Iuchiban and they are not the same '
        'thing. One is maho. This is politics.',
        'Politics is worse. Politics has precedent.',
        "The Emperor's authority is supreme in theory and constrained by everyone "
        'having their own loyalties in practice. The Gozoku is that fact wearing a '
        'name.',
        'Hantei the 16th is where this material concentrates.',
        'A conspiracy that does not want the throne cannot be defeated by defending the throne.',
        'Nobody has ever declared themselves Gozoku. That is rather the point.',
        attach(
            'A conspiracy at work. Everyone present is behaving correctly.',
            CATS,
        ),
        attach(
            'And this is the one moment it becomes visible.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hantei_16': (
        'Hantei the 16th. Yes. That reign is where the Gozoku material and the '
        'Iuchiban material meet, and it is not a coincidence.',
        'An Emperor whose authority was theoretically absolute and practically '
        'negotiated. Which describes more reigns than the histories admit.',
        'Do not confuse him with Hantei the Tenth, who gave us the Yasuki Taka system '
        'and outlawed road tolls and is the one who actually improved anything.',
        'People do confuse them. Constantly. At me.',
        'The Hantei family is small - fifteen thousand samurai - despite containing '
        'the Emperor. They marry outward.',
        'A weak Emperor is not a gap in the Empire. It is an opportunity that several '
        'families notice simultaneously.',
        'I have the reign in the record. It is not a flattering document and it was '
        'not written by anyone who was there.',
        'Ask me about the Tenth instead. Better reign, better paperwork.',
        attach(
            'The throne, as an institution, during that reign.',
            GREAT_WAVE,
        ),
        attach(
            'And this is what surrounded it.',
            CATS,
        ),
    ),
    'the_nameless_one': (
        'The Nameless One. And no, I am not going to be clever about the name.',
        'The worldbuilding here is deliberately consistent - a new concept is not '
        'allowed to contradict an existing principle. That constraint is what makes '
        'this one land.',
        'A thing without a name is a thing the record cannot hold. Consider what that '
        'means for a scribe.',
        'Names are how this Empire does everything. Lineage, rank, obligation, '
        'inheritance. Remove the name and none of the machinery grips.',
        'That is not a mystical claim. It is an administrative one, which is worse.',
        'I have nine entries and none of them are comfortable.',
        'Asking me this in an open channel is a choice you have made.',
        'Next question.',
        attach(
            'What the record can hold.',
            INNER_VISION,
        ),
        attach(
            'And what it cannot.',
            RAINY_MOON,
        ),
    ),
    'connection_damage': (
        'Connection damage. It is taken in Spirit Encounters and it is the most '
        'frightening mechanic in this setting.',
        'You do not lose health. You lose the ties between yourself and the people you '
        'are tied to.',
        'In one dream quest the PCs found themselves in a Court and took it there. '
        'That is the canonical example and it is instructive.',
        'Connections are what oni eat in Jigoku, and being stripped of them is what '
        'ALLOWS rebirth. So this is not merely injury.',
        'It is the same process, applied early, to somebody who is not dead.',
        'The Empire runs on obligation networks. Damage the network and you have '
        'damaged the person more thoroughly than a blade would.',
        'You can heal a wound. There is no ministry for this.',
        'Ask what it costs before you agree to the encounter. Everyone forgets.',
        attach(
            'A connection being taken. There is nothing to see, which is the problem.',
            INNER_VISION,
        ),
        attach(
            'And this is afterward.',
            RAINY_MOON,
        ),
    ),
    # ---- campaigns and their places ----------------------------------------
    'karmic_inquisitors': (
        'The Karmic Inquisitors. PCs who are members of the Order of Lord Moon, which '
        'they refer to only as "the Order" so listeners assume Bishamon.',
        'A secret society whose members hold entirely legitimate positions in a public '
        'monastic order. Extremely convenient and extremely fragile.',
        "They become disciples of Lord Moon's celestial servants - Crescent, Half, and "
        'the third phase of abilities.',
        'Each begins with three phases and may mix them across different servants. '
        'Most go wide and later wish they had gone deep.',
        'The campaign includes a Saibankan ruling, the Forgotten Tomb, and Kitsu Okura '
        'being enigmatic at length.',
        'The timeline is long and I keep all of it, which is why you are asking me and not him.',
        'Karmic inquisition means asking whether a soul got what it was owed. Nobody '
        'enjoys the answer.',
        'I have the initiation vow written out. I am not reciting it here.',
        attach(
            'The Order, meeting. Nothing about this is visible from outside.',
            INNER_VISION,
        ),
        attach(
            'And this is what happens when a member is careless.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'order_of_lord_moon': (
        'The Order of Lord Moon. Careful - you have asked that where people can read it.',
        'It is called "the Order" in conversation precisely so anyone overhearing '
        'assumes you mean the Order of Bishamon.',
        'The initiation vow binds you to loyalty to the brothers and sisters, to keep '
        'their identities secret, and to protect their lives as your own.',
        'It also explicitly permits you to use what you gain for your own goals and '
        'ambitions - provided you never harm the order.',
        'That clause is unusual. Most vows demand selflessness. This one budgets for '
        'ambition, which is why it works.',
        "Members become disciples of Lord Moon's heavenly court. Ryoshun guards the "
        'entrance to the celestial heavens.',
        'You swear it until the end of your days. There is no retirement clause and I '
        'have checked.',
        'I am going to stop here.',
        attach(
            'The correct setting for this conversation. Not this channel.',
            RAINY_MOON,
        ),
        attach(
            'And this is the second clause being tested.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'first_toshi_ranbo': (
        'Toshi Ranbo. The Lion and the Crane, again, over a city, again.',
        'A dueling tournament settled the final ownership of several disputed '
        'provinces under the terms of the peace treaty. The Lion did well overall.',
        'Except for Tango province, which the Damasu lost in an upset when Doji Masayo '
        'turned up with the cursed sword Shitsuten and killed Akodo no Damasu Tsuo.',
        'The man was expected to win. That is the entire weight of the entry.',
        'A province decided by one duel, and the duel decided by a sword forged out of '
        "a swordsmith's hatred for the Yasuki. History is not tidy.",
        'The campaign runs through Hikobayashi County, irrigation disputes, bandit '
        'hunting, and the Dragon magistrates.',
        'Also pirates on the Drowned Merchant River, which is exactly as much fun as '
        'it sounds and considerably more paperwork.',
        'Ask me about the tournament and I will tell you who was supposed to win.',
        attach(
            'The duel that cost a province.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the treaty negotiation that made it necessary.',
            CATS,
        ),
    ),
    'peasant_campaign': (
        'The Peasant Campaign. Scorpion lands. PCs who are not samurai, which changes '
        'every single assumption in this record.',
        'No stipend. No rank. No right to be anywhere. The most constrained set of '
        'characters and the most interesting problems.',
        'A peasant may not carry a daisho, may not travel without papers, and answers '
        'to a headsman before a magistrate.',
        'Which means the village headsman - who everyone finds boring - is the single '
        'most powerful person in that campaign.',
        "Set among the Scorpion, which means every problem is somebody's plan and the "
        'plan is not about you.',
        'Ninety percent of farmers are tenants. That is the ceiling on everything the '
        'characters can do.',
        'It is the campaign that best demonstrates how the Empire actually works, '
        'because nothing shields you from it.',
        'Peasants are half-people in the Celestial Order. The campaign is about what '
        'that costs, hour by hour.',
        attach(
            "The whole of a peasant's political power.",
            CARP,
        ),
        attach(
            'And this is what arrives when it is not enough.',
            GREAT_WAVE,
        ),
    ),
    'hidden_way': (
        'The Hidden Way. Yes. That campaign.',
        'The eleven Imperial Gardens of Chai Sedo sit inside it, and so does the 1st '
        'Imperial Legion.',
        'Also the Gateway to the Land of the Burning Sands and the Outsider Keep, '
        'which is where the actual work happens.',
        'And the Moto, which is why fourteen categories of my material are Moto material.',
        'A hidden way is only hidden until somebody writes it down, and then it is '
        'merely inconvenient.',
        'Toranosuke is the abbot of Chai Sedo and declares things portend success at '
        'convenient moments.',
        'The Chai Sedo library is the source for a great deal that nobody has '
        'independently verified. Including where the Moto came from.',
        'Ask me about the gardens. There are eleven and they each mean something.',
        attach(
            'The way in.',
            RAINY_MOON,
        ),
        attach(
            'And this is what is at the other end of it.',
            GREAT_WAVE,
        ),
    ),
    'wasp_bounty_hunters': (
        'The Wasp. A minor clan with about two thousand samurai, which is nothing, and '
        'a bounty operation, which is everything.',
        "Tsuruchi is the name you want. I have his parents' lives in the record, which "
        'is more than most clans get.',
        'Bounty hunting is legitimate work that everyone treats as disreputable, which '
        "is the Wasp's entire social position.",
        'Investigations and bounties have their own procedures. Ask and I will bore you correctly.',
        'A minor clan survives by being useful in a way nobody else wants to be. That '
        'is the Wasp, the Tortoise, and half the others.',
        "Two thousand samurai against a Great Clan's five hundred thousand. They do "
        'not survive by fighting.',
        'The bounty is a legal instrument before it is an adventure hook, and the '
        'paperwork is where the interesting cases hide.',
        'Everyone wants the chase. I have the warrant.',
        attach(
            'The pursuit, as the stories have it.',
            MUSASHI_BAT,
        ),
        attach(
            'And this is what most of it actually is.',
            RAINY_MOON,
        ),
    ),
    'damasu_domain': (
        'The Damasu domain. Akodo lands - the Damasu are a Karo House of the Akodo, '
        'which is why their samurai carry the Akodo name.',
        'Their previous daimyo was Akodo no Damasu Kojima. Akodo is the family, "no '
        'Damasu" the house, Kojima the man.',
        'They lost Tango province in the Toshi Ranbo tournament when Doji Masayo '
        'killed the expected winner with Shitsuten.',
        "Their ancestral sword is Amatsukami no Ken, the Heavenly Sovereign's Sword, "
        'currently carried by their daimyo Akodo no Damasu Chiho.',
        'The domain has its own lineages, its own temples, and its own Order of '
        'Bishamon with its own Grand Abbot.',
        "A Karo House is comparable in size to the ruling daimyo's own domain and "
        'headed by a senior vassal with specialized duties. Not a lesser thing.',
        'Most of the Karmic Inquisitors material happens here or adjacent to it.',
        'Ask about the HOUSE and I will tell you about the family. Ask about the '
        'DOMAIN and I will tell you about the provinces.',
        attach(
            'The tournament that cost them a province.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the Order of Bishamon they endow.',
            INNER_VISION,
        ),
    ),
    'chai_sedo': (
        'Chai Sedo. Eleven Imperial Gardens, and yes, eleven, and no, nobody will tell '
        'you why not twelve.',
        'Pond Paradise. Borrowed Scenery. Sunken Sceneries. Mossy Stone Triad. Seven '
        'Sublimities. Beauty of Empty Space. Waving Lawn. Snow Rose. Pleasure After. '
        'Circle of Here.',
        'That is ten. There is an eleventh and I enjoy watching people count.',
        'The Beauty of Empty Space Garden is the one that annoys visitors, which is the intention.',
        'Toranosuke is the abbot. He declares things portend success, generally when '
        'an army is already moving.',
        'The Chai Sedo library is the source for a great deal nobody has verified - '
        'including where the Moto originally came from.',
        'A garden here is an argument about the nature of attention, laid out in '
        'stone. The monks would put it more gracefully and take longer.',
        'People visit for the gardens and leave with an opinion about the library.',
        attach(
            'A pure land garden. Every stone is an argument.',
            INNER_VISION,
        ),
        attach(
            'And this is the Beauty of Empty Space, which visitors find infuriating.',
            RAINY_MOON,
        ),
    ),
    'first_imperial_legion': (
        'The 1st Imperial Legion. It guards the Gateway to the Land of the Burning '
        "Sands, and has for longer than anyone's lineage.",
        'Every legionnaire is a samurai. That is what makes a legion expensive and it '
        'is not negotiable.',
        'The 2nd holds Beiden Pass. The 3rd is on the Kaiu Wall, along with most of '
        'the remaining twenty-odd.',
        'It has ranks, companies, houses, a budget and a layout, and I have all of '
        'them, and you will regret asking for the budget.',
        'A legionnaire swears by Lady Sun and by their ancestors, and swears never to '
        'seek to avoid death. Officers swear longer.',
        "The Armor of Fool's Regret is currently with Ikoma Akaho, a platoon "
        'lieutenant in the 6th battalion. Supposedly cursed. Supposedly.',
        'A legion is a small city that marches. Most of what it does is eat.',
        'Ask me about the Outsider Keep. That is where the interesting duty is.',
        attach(
            'The legion at its actual work.',
            ARCHERS,
        ),
        attach(
            'And this is the part they recruit with.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hikobayashi_county': (
        'Hikobayashi County. Toshi Ranbo material - irrigation disputes, bandit '
        'hunting, and the Dragon magistrates.',
        'Irrigation Irritation is a real heading in my record and I did not choose it.',
        'A county is administered by a magistrate in the town at its center, and holds '
        'about half a dozen village districts.',
        'Water rights are the most reliable source of violence in any farming county '
        'in the Empire. Not honor. Water.',
        "The Nightingale Bushi are there, and the Lion's Roar, and a great deal of hunting.",
        'Also Matsu Yokijiro, and Shinjo no Dorai Rakuo, and a plan the Lion had that '
        'did not survive contact.',
        'Bandit hunting is led by village headsmen with ashigaru. It is not glamorous '
        'and it is most of rural law enforcement.',
        'Ask about the irrigation. Everyone asks about the bandits and the irrigation '
        'is where the campaign actually lives.',
        attach(
            'The actual casus belli of most rural disputes.',
            GREAT_WAVE,
        ),
        attach(
            'And this is how they get settled.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'gateway_outsider_keep': (
        'The Gateway to the Land of the Burning Sands, and the Outsider Keep beside '
        'it. The 1st Legion holds both.',
        'The Gateway is the formal boundary. The Keep is where the actual work of the '
        'boundary happens.',
        'Everything that comes east comes through there, and everything that goes west '
        "is somebody's idea.",
        'People have been lost in the Shinomen Forest a hundred miles from the Gateway '
        'and walked out of the Isawa Woodlands. That is a between place and it is '
        'nearby.',
        'A keep named for outsiders tells you exactly what the Empire thinks it is for.',
        "Gaheris' campaign is out that way. So is Medin al Salaat. So is everything "
        'the Empire files under "abroad".',
        'The duty is boring for years and then it is not, and the record only keeps '
        'the second kind.',
        'Ask me what comes through. The answer is mostly merchants and occasionally not.',
        attach(
            'The Gateway. The line is administrative, not geographical.',
            RAINY_MOON,
        ),
        attach(
            'And this is what the Keep is actually watching for.',
            GREAT_WAVE,
        ),
    ),
}
