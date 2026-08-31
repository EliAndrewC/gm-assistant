"""Villains, metaplot, and the campaigns. GM Assistant only.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing a line here.

Rewritten whole on 2026-08-31 after the tone audit put this file at 5.3%. Three
specific repairs, recorded so they are not undone by accident:

  - **The withholding deflection was load-bearing and should not have been.**
    `the_nameless_one` closed on "Next question." and `order_of_lord_moon` on
    "I am going to stop here." Withholding is not a punchline; it is the absence
    of one wearing a cloak. Both categories now pay off the secrecy instead.
  - **The initiation-vow line appeared in three categories verbatim** (here
    twice, plus `gm_religion/lord_moons_court`). It survives in one place only.
  - **`damasu_domain` overlapped `gm_clans/damasu` on four of eight lines.**
    This file now holds the PLACE - provinces, temples, lineages, what happened
    there - and the genealogy lives with the houses.
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
    attach,
)

WORLD: dict[str, tuple[str, ...]] = {
    'iuchiban': (
        'Everyone reaches for that name and almost nobody wants the actual history, '
        'which I have, in full, and which has never once been requested.',
        'He staged a coup. It failed in the way that leaves the Empire permanently '
        'changed anyway - the most Rokugani outcome available to any project.',
        'Then he was resurrected, which is the part that turns him from an entry into a '
        'metaplot, and turns my record from a history into a subscription.',
        'He is the most famous bloodspeaker and he is not the first. That distinction '
        'matters enormously and nobody makes it, so I make it, into the middle distance.',
        'The Gozoku keeps arriving in the same sentence as him and they are not the '
        'same thing. One is maho. The other is a committee. I file them apart and the '
        'world keeps stapling them together.',
        'Hantei the 16th sits in the middle of all of it, and history has been unkind to '
        'him in the usual selective way, by people who were not present and are not '
        'checkable.',
        'His lieutenants are the genuinely interesting reading. He is the name; they '
        'are the mechanism. Names travel and mechanisms do the work, which is a lesson '
        'I take somewhat personally.',
        'You would like him to be the reason. He is, in most of these entries, the '
        'excuse - and an excuse that convenient is worth more to a court than a villain.',
        attach(
            'The shape the stories give him, which is considerably more legible than '
            'the shape the record gives him.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What he actually does to a court, over years, with nothing visibly '
            'happening on any given day.',
            FOX_WOMAN,
        ),
    ),
    'iuchibans_lieutenants': (
        'Jama no Iuchiban Suru, Jama Musume, Asahina Yajinden, Jama no Iuchiban Kyoso, '
        'Jama no Iuchiban Kohaku. Five names, and I can produce them in order at any '
        'hour, which has impressed nobody.',
        'The "Jama no Iuchiban" construction is doing exactly what a house name does. '
        'Read it that way and the whole group resolves - a conspiracy that adopted the '
        'naming conventions of the aristocracy it was undermining.',
        'Asahina Yajinden is the one people flinch at, a Crane name sitting on that '
        'list. The flinch is the interesting part; nobody flinches at the other four.',
        'Jama Musume is the one I would worry about, and I am not going to elaborate in '
        'an open channel, and you may draw your own conclusion from the fact that I '
        'named her at all.',
        'Lieutenants outlive principals. That is the recurring lesson of this entire '
        'file and it has never once been learned by anybody who needed to.',
        'Each of them is a separate problem with a separate solution. Treating them as '
        'one problem is precisely how this goes badly, and it has gone badly four times '
        'in my record alone.',
        'A conspiracy with named subordinates has been running long enough to need an '
        'organizational chart. I find that more frightening than the maho and I appear '
        'to be alone in it.',
        'Everyone asks about Iuchiban. These five are what actually arrives at your '
        'door, and not one of them has ever been asked about by name.',
        attach(
            'Five of them, and only one ever gets painted. Guess which, and then guess why.',
            KIDOMARU_TENGU,
        ),
        attach(
            'One of them in a court. Note that nothing is wrong. Nothing is wrong for years.',
            FOX_WOMAN,
        ),
    ),
    'the_gozoku': (
        'The Gozoku: a conspiracy of great families to control the throne without '
        'sitting on it. An ambition so tasteful it is almost impossible to prosecute.',
        'Which is a far more Rokugani ambition than open rebellion. Rebellion has a '
        'battlefield and a verdict. This has neither, and I am expected to keep a '
        'record of it regardless.',
        'It keeps appearing in the same sentence as Iuchiban and they are not the same '
        'thing. One is maho. This is politics, and politics has precedent, and '
        'precedent is far harder to burn.',
        "The Emperor's authority is supreme in theory and constrained by everybody "
        'having their own loyalties in practice. The Gozoku is simply that fact having '
        'been given a name and a membership.',
        'Hantei the 16th is where this material concentrates, which is to say where the '
        'gap between theory and practice grew wide enough for people to stand in it.',
        'A conspiracy that does not want the throne cannot be defeated by defending the '
        'throne. Every countermeasure in my record defends the throne.',
        'Nobody has ever declared themselves Gozoku, which is rather the point, and '
        'which makes my record of them a record of inferences with dates attached.',
        'The best-documented conspiracy in the Empire has no documents. I want that '
        'understood as a professional grievance and not a joke.',
        attach(
            'A conspiracy at work. Everyone present is behaving entirely correctly.',
            CATS,
        ),
        attach(
            'The single moment it becomes visible, which is also the moment it stops '
            'being useful to anybody.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hantei_16': (
        'Hantei the 16th. That reign is where the Gozoku material and the Iuchiban '
        'material meet, and the meeting is not a coincidence, and saying so out loud is '
        'the sort of thing that gets a record-keeper reassigned.',
        'An Emperor whose authority was theoretically absolute and practically '
        'negotiated - which describes rather more reigns than the histories are willing '
        'to admit, and I hold the histories.',
        'Do not confuse him with Hantei the Tenth, who gave us the Yasuki Taka system, '
        'outlawed tolls on Imperial roads, and is the one who actually improved '
        'anything.',
        'People do confuse them. Constantly. At me. Two Emperors, six centuries apart, '
        'and I am the one who has to keep them separate in a conversation about neither.',
        'The Hantei family is small - fifteen thousand samurai - despite containing the '
        'Emperor, so they marry outward. The most powerful family in the Empire is also '
        'the one most dependent on everybody else.',
        'A weak Emperor is not a gap in the Empire. It is an opportunity that several '
        'families notice simultaneously, which is a very different and much faster '
        'problem.',
        'The reign is in my record and it is not a flattering document, and it was not '
        'written by anybody who was there, and both of those facts are usually omitted '
        'when it is quoted at me.',
        'Every history of this reign was written to explain something that had already '
        'happened. I keep them all and I trust the dates.',
        attach(
            'The throne as an institution during that reign. Structurally sound, '
            'notably unattended.',
            GREAT_WAVE,
        ),
        attach(
            'What surrounded it, at close range, being extremely polite.',
            CATS,
        ),
    ),
    'the_nameless_one': (
        'The Nameless One. I am not going to be clever about the name and I would ask '
        'you to notice how much restraint that represents.',
        'Nothing in the record contradicts anything else about him, which sounds like '
        'rigor and is actually the problem: there is not enough of him to contradict.',
        'A thing without a name is a thing the record cannot hold. Consider, at your '
        'leisure, what that means for the record. Consider what it means for me.',
        'Names are how this Empire does everything: lineage, rank, obligation, '
        'inheritance. Remove the name and not one gear grips - which makes the most '
        'dangerous thing in the setting a gap in the paperwork.',
        'That is not a mystical claim. It is an administrative one, which is worse, '
        'because administration is the part that was supposed to be reliable.',
        'I have nine entries and not one of them is comfortable, and I have read all '
        'nine more times than the work required, which I attribute to thoroughness.',
        'Asking me this in an open channel is a choice you have made, and I have '
        'recorded that you made it, along with the hour.',
        'The one thing in this Empire I cannot file properly, and it is the one thing '
        'everybody assumes I am relaxed about.',
        attach(
            'The moment a clerk discovers his form has no field for the thing in front '
            'of him. I have had that moment nine times and kept every one.',
            INNER_VISION,
        ),
        attach(
            'Quiet, orderly, and missing something nobody can put a word to. That is '
            'how an archive looks once he has been in it.',
            RAINY_MOON,
        ),
    ),
    'connection_damage': (
        'Connection damage is taken in Spirit Encounters and it is the most frightening '
        'mechanic in this setting, and it is frightening for an administrative reason, '
        'which is the worst kind.',
        'You do not lose health. You lose the ties between yourself and the people you '
        'are tied to - and in an Empire that defines a person by their obligations, '
        'that is not an injury, it is a deletion.',
        'In one dream quest the PCs found themselves in a Court and took it there. That '
        'is my canonical example and it is instructive: the Court did not have to do '
        'anything unusual at all.',
        'Connections are what oni eat in Jigoku, and being stripped of them is what '
        'ALLOWS rebirth. So this is not injury. It is a posthumous process, applied '
        'early, to somebody who has not died.',
        'The Empire runs on obligation networks. Damage the network and you have '
        'damaged the person far more thoroughly than a blade would, and left no mark '
        'for a magistrate to look at.',
        'You can heal a wound. There is no ministry for this, no form, no precedent, '
        'and I have looked for all three on more than one occasion.',
        'Everybody asks what an encounter can give them. Nobody asks what it can take, '
        'and I am the one holding the list of what it has taken.',
        'The frightening part is not that it hurts. It is that afterward the paperwork '
        'is still correct.',
        attach(
            'A connection being taken. There is nothing to see, which is precisely the '
            'problem, and why the record is thin exactly where it should be thickest.',
            INNER_VISION,
        ),
        attach(
            'Afterward. Everything is where it was and none of it is attached to anything.',
            RAINY_MOON,
        ),
    ),
    # ---- campaigns and their places ----------------------------------------
    'karmic_inquisitors': (
        'The Karmic Inquisitors: PCs who are members of the Order of Lord Moon, which '
        'they refer to only as "the Order" so listeners assume Bishamon. A conspiracy '
        'maintained entirely by letting people finish their own sentences.',
        'A secret society whose members hold entirely legitimate positions in a public '
        'monastic order. Extremely convenient, extremely fragile, and extremely '
        'difficult to index.',
        "They become disciples of Lord Moon's celestial servants - Crescent, Half, and "
        'the third phase of abilities. Three tiers, which means somebody, somewhere, is '
        'keeping a chart. It is me.',
        'Each begins with three phases and may mix them across different servants. Most '
        'go wide and later wish they had gone deep, which is true of secret societies '
        'and true of almost everything else.',
        'The campaign includes a Saibankan ruling, the Forgotten Tomb, and Kitsu Okura '
        'being enigmatic at considerable length. I transcribed the enigmatic part.',
        'The timeline is long and I keep all of it, which is why you are asking me and '
        'not the character sheet, and I would like that noted somewhere permanent.',
        'Karmic inquisition means asking whether a soul got what it was owed. Nobody '
        'enjoys the answer, and the ones who commissioned the question enjoy it least.',
        'An order of people who investigate whether the accounts balance. I have never '
        'felt so close to a group of characters and so far from being invited.',
        attach(
            'The Order, meeting. Nothing about this is visible from outside, which is '
            'the design and also my difficulty.',
            INNER_VISION,
        ),
        attach(
            'What carelessness costs a member. It is quick and it is not appealed.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'order_of_lord_moon': (
        'The Order of Lord Moon. You have asked that where people can read it, and I am '
        'obliged to answer where people can read it, and we will both be living with '
        'this conversation.',
        'It is called "the Order" in conversation precisely so anyone overhearing '
        'assumes the Order of Bishamon. Centuries of operational security resting on '
        'the listener being slightly lazy, which has never once failed.',
        'The initiation vow binds you to loyalty to the brothers and sisters, to keep '
        'their identities secret, and to protect their lives as your own. I have it in '
        'full and I have never been asked to recite it by anybody who wanted the words.',
        'It also explicitly permits you to use what you gain for your own goals and '
        'ambitions, provided you never harm the order. Most vows demand selflessness. '
        'This one budgets for ambition, which is exactly why it works.',
        'A vow written by somebody who had read other vows and watched them fail. I '
        'admire the drafting more than I am comfortable admitting about a secret '
        'society.',
        "Members become disciples of Lord Moon's heavenly court, and Ryoshun guards the "
        'entrance to the celestial heavens - so the Order is, structurally, a group of '
        'people cultivating a relationship with a doorman.',
        'You swear it until the end of your days. There is no retirement clause and I '
        'have checked.',
        'I know who they are. That is not a boast, it is a burden, and it is the reason '
        'I do not enjoy this category.',
        attach(
            'The correct setting for this conversation. Note that it is not a channel.',
            RAINY_MOON,
        ),
        attach(
            'The second clause being tested. It is comprehensive and it is quick.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'first_toshi_ranbo': (
        'Toshi Ranbo: the Lion and the Crane, again, over a city, again. I have four '
        'centuries of this and the entries are distinguishable only by date.',
        'A dueling tournament settled the final ownership of several disputed provinces '
        'under the terms of the peace treaty. Provinces, decided by fencing. I '
        'transcribed the bracket.',
        'The Lion did well overall - except for Tango province, which the Damasu lost '
        'in an upset when Doji Masayo turned up with the cursed sword Shitsuten and '
        'killed Akodo no Damasu Tsuo. A treaty clause, honored exactly, producing an '
        'outcome nobody who wrote it would have signed.',
        'Akodo no Damasu Tsuo was expected to win Tango province, and the word expected '
        'is carrying the entire entry. It is also the only part of it anybody has ever '
        'quoted back to me.',
        'A province decided by one duel, and the duel decided by a sword forged out of '
        "a swordsmith's hatred for the Yasuki. History is not tidy and I am the one who "
        'has to make it look tidy in the margins.',
        'The campaign runs through Hikobayashi County, irrigation disputes, bandit '
        'hunting, and the Dragon magistrates - three of which are administration and '
        'one of which gets talked about.',
        'Also pirates on the Drowned Merchant River, which is exactly as entertaining '
        'as it sounds and generates considerably more paperwork than it sounds.',
        'Everybody asks who won the tournament. The useful question is who was supposed '
        'to, and I have that list, and it is shorter and much more interesting.',
        attach(
            'The duel that cost a province. Nobody in the picture knows that yet.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The treaty negotiation that made the duel necessary. This took months and '
            'produced the document; the duel took a moment and produced the province.',
            CATS,
        ),
    ),
    'peasant_campaign': (
        'The Peasant Campaign, in Scorpion lands: PCs who are not samurai, which '
        'quietly invalidates every assumption elsewhere in my record and forced me to '
        'read the whole thing again from a different angle.',
        'No stipend, no rank, no right to be anywhere. The most constrained characters '
        'in the record and, not coincidentally, the most interesting problems in it.',
        'A peasant may not carry a daisho, may not travel without papers, and answers '
        'to a headsman before a magistrate. Two of those are about weapons and travel. '
        'The third is a neighbor, and it is the one that shapes the life.',
        'Which means the village headsman - whom everybody finds boring - is the single '
        'most powerful person in the campaign. I have said this for years to no effect '
        'whatsoever.',
        "Set among the Scorpion, so every problem is somebody's plan and the plan is not "
        'about you. Being incidental to a scheme is worse than being its target and '
        'takes much longer to notice.',
        'Ninety percent of farmers are tenants. That single number is the ceiling on '
        'everything the characters can do, and it is a number, so nobody reads it as a '
        'plot.',
        'It is the campaign that best demonstrates how the Empire actually works, '
        'because nothing shields you from it - which is also the reason it is the '
        'hardest one to sit through.',
        'Peasants are half-people in the Celestial Order. The campaign is about what '
        'that costs, hour by hour, and I hold the hours.',
        attach(
            "The whole of a peasant's political power, at true scale.",
            CARP,
        ),
        attach(
            'What arrives when it is not enough, which is most years.',
            GREAT_WAVE,
        ),
    ),
    'hidden_way': (
        'The Hidden Way. That campaign contains the eleven Imperial Gardens of Chai '
        'Sedo, the 1st Imperial Legion, and roughly a third of everything I know.',
        'Also the Gateway to the Land of the Burning Sands and the Outsider Keep, which '
        'is where the actual work happens and which appears in none of the songs.',
        'And the Moto, which is why fourteen categories of my material are Moto '
        'material, and why I can tell you the grazing acreage per horse without being '
        'asked.',
        'A hidden way is only hidden until somebody writes it down, at which point it '
        'becomes merely inconvenient. I am, professionally, the point at which that '
        'transition occurs.',
        'Toranosuke is the abbot of Chai Sedo, which makes one man simultaneously the '
        "keeper of eleven Imperial Gardens and, by some distance, the Empire's most "
        'quoted authority on a war nobody has formally declared is happening.',
        'A campaign about doorways, run by people who mostly wanted to know what was on '
        'the far side of them. I wanted to know who maintained them.',
        'The gardens number eleven and each of them means something, and the meanings '
        'are in my record, and in four hundred sessions I have been asked for one of '
        'them.',
        'Everything in this campaign is a threshold of some kind: a gate, a garden, a '
        'boundary, a library nobody checks. I have noticed and I have told nobody until '
        'now.',
        attach(
            'The way in. It is not concealed so much as uninviting, which works better.',
            RAINY_MOON,
        ),
        attach(
            'What is at the other end of it. The Legion has stood between the Empire '
            'and this for so long that the Empire has stopped counting it as a border.',
            GREAT_WAVE,
        ),
    ),
    'wasp_bounty_hunters': (
        'The Wasp: a minor clan of about two thousand samurai, which is nothing, and a '
        'bounty operation, which is everything. The ratio is the clan.',
        "Tsuruchi is the name you want. I have his parents' lives in the record, which "
        'is a great deal more than most Great Clans have managed to leave me.',
        'Bounty hunting is legitimate work that everyone treats as disreputable, which '
        "is the Wasp's entire social position and a fair description of several "
        'occupations I could name.',
        'Investigations and bounties have their own procedures, and I will bore you '
        'correctly on either. Correctly is the operative word and the reason it takes '
        'so long.',
        'A minor clan survives by being useful in a way nobody else is willing to be. '
        'That is the Wasp, the Tortoise, and half the others, and it is not a bad '
        'living if you can bear the tone.',
        "Two thousand samurai against a Great Clan's five hundred thousand. They do not "
        'survive by fighting. They survive by being the ones holding the document.',
        'The bounty is a legal instrument before it is an adventure hook, and the '
        'paperwork is where the interesting cases hide, and nobody has ever gone '
        'looking for them there.',
        'Everyone wants the chase. I have the warrant.',
        attach(
            'The pursuit, as the stories have it. Two thousand samurai against the '
            'Empire, and the songs have settled on the one part of the work that does '
            'not involve a document.',
            MUSASHI_BAT,
        ),
        attach(
            'What most of it actually is: waiting somewhere damp with a description.',
            RAINY_MOON,
        ),
    ),
    'damasu_domain': (
        'The Damasu domain sits in Akodo lands, and most of what has happened in this '
        'campaign has happened here or within a day of here. I did not choose that and '
        'I have not been consulted since.',
        'They lost Tango province in the Toshi Ranbo tournament when Doji Masayo killed '
        'the expected winner with Shitsuten. A province, gone in a moment, and a '
        'generation of correspondence about it afterward.',
        "Their ancestral sword is Amatsukami no Ken, the Heavenly Sovereign's Sword, "
        'currently carried by their daimyo Akodo no Damasu Chiho. Ancestral swords are '
        'inventory. I say so quietly and only here.',
        'The domain has its own lineages, its own temples, and its own Order of '
        'Bishamon with its own Grand Abbot, its own endowments and its own tenants. A '
        'domain is not a place with temples in it; it is a place the temples are part '
        'of the accounts of.',
        'A capital, six provincial cities, thirty-six towns, and the villages and '
        'hamlets underneath them. Every one of those has a headsman, a monk, and a '
        'dispute, and I hold all three columns.',
        'Most of the Karmic Inquisitors material happens here or adjacent to it, which '
        'means the domain is simultaneously the best-documented place in my record and '
        'the one where the documentation is least reliable.',
        'The provinces are the thing that can be lost. The house is the thing that '
        'cannot. Whoever set that arrangement up understood exactly what he was doing '
        'and it was not generosity.',
        'People ask about the domain and mean the family, or ask about the family and '
        'mean the province. I answer both and get thanked for neither.',
        attach(
            'The tournament that cost them a province, at the moment before it did.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The Order of Bishamon they endow. The endowment is a property arrangement '
            'and the arrangement is the reason the temple is beautiful.',
            INNER_VISION,
        ),
    ),
    'chai_sedo': (
        'Chai Sedo has eleven Imperial Gardens. Eleven. Nobody will tell you why not '
        'twelve and I have stopped expecting to be told.',
        'Pond Paradise. Borrowed Scenery. Sunken Sceneries. Mossy Stone Triad. Seven '
        'Sublimities. Beauty of Empty Space. Waving Lawn. Snow Rose. Pleasure After. '
        'Circle of Here. Ten names, each of them a small argument, none of them a '
        'description of a garden.',
        'Ten gardens have names anybody will tell you. There is an eleventh, and I '
        'enjoy watching people count.',
        'The Beauty of Empty Space Garden is the one that annoys visitors, which is '
        'unambiguously the intention, and which makes it the most successful garden in '
        'the Empire by its own stated criteria.',
        'Toranosuke is the abbot. I have his declarations and the marching orders they '
        'accompany, and I have compared their dates, which is the single most '
        'rewarding afternoon I have ever spent unasked.',
        'The Chai Sedo library is the source for a great deal that nobody has verified, '
        'including where the Moto originally came from. A library is only as good as '
        'its second reader, and this one is still waiting for hers.',
        'A garden here is an argument about the nature of attention, laid out in stone. '
        'The monks would put that more gracefully and would take four times as long, '
        'and I would have to write all of it down.',
        'Visitors come for the gardens and leave with an opinion about the library. I '
        'have never once seen it happen the other way around.',
        attach(
            'A pure land garden. Every stone in it is an argument somebody won.',
            INNER_VISION,
        ),
        attach(
            'The gardens in the eleventh month, when the Imperial gardeners are the '
            'only staff in Rokugan whose year has not yet ended.',
            RAINY_MOON,
        ),
    ),
    'first_imperial_legion': (
        'The 1st Imperial Legion guards the Gateway to the Land of the Burning Sands '
        "and has done for longer than anybody's lineage. Centuries of standing "
        'somewhere so that nothing happens. I understand the work.',
        'Every legionnaire is a samurai, which is what makes a legion expensive, and it '
        'is not negotiable, and every treasury in four hundred years has tried to '
        'negotiate it.',
        'The 2nd holds Beiden Pass. The 3rd is on the Kaiu Wall along with most of the '
        'remaining twenty-odd. The numbering tells you what the Empire is actually '
        'afraid of, in order.',
        'It has ranks, companies, houses, a budget and a layout, and I have all of '
        'them. You will regret asking for the budget and I will not regret providing it.',
        'A legionnaire swears by Lady Sun and by their ancestors, and swears never to '
        'seek to avoid death. Officers swear longer, which is the only reliable '
        'privilege of rank in the entire institution.',
        "The Armor of Fool's Regret is currently with Ikoma Akaho, a platoon lieutenant "
        'in the 6th battalion. Supposedly cursed. Supposedly. The record is careful '
        'about that word and so am I.',
        'A legion is a small city that marches, and most of what it does is eat. The '
        'heroic fraction of a legion year would fit in an afternoon.',
        'Nobody enlists for the Outsider Keep and everybody who has served there asks '
        'to go back, which is a recruiting fact the Ministry of War has had for four '
        'centuries and has never once put on a banner.',
        attach(
            'The legion at its actual work: waiting, in formation, at a door, for a '
            'century at a time. Four hundred years of this and eleven pages of it.',
            ARCHERS,
        ),
        attach(
            'The part they recruit with, which is accurate for approximately one day in '
            'four hundred.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hikobayashi_county': (
        'Hikobayashi County: Toshi Ranbo material - irrigation disputes, bandit '
        'hunting, and the Dragon magistrates, in ascending order of glamour and '
        'descending order of importance.',
        'Irrigation Irritation is a real heading in my record and I did not choose it.',
        'A county is administered by a magistrate in the town at its center and holds '
        'about half a dozen village districts. One magistrate, six districts, and every '
        'quarrel in all six arriving by the same road.',
        'Water rights are the most reliable source of violence in any farming county in '
        'the Empire. Not honor. Water. I would like that engraved on something.',
        "The Nightingale Bushi are there, and the Lion's Roar, and a great deal of "
        'hunting, and the hunting is what gets recounted afterward at dinner.',
        'Also Matsu Yokijiro, and Shinjo no Dorai Rakuo, and a plan the Lion had which '
        'did not survive contact with the county. Plans rarely survive a county.',
        'Bandit hunting is led by village headsmen with ashigaru. It is not glamorous, '
        'it is most of rural law enforcement, and the headsman gets no line in the '
        'story afterward. He and I compare notes.',
        'The bandits are what people ask about. The irrigation is where the campaign '
        'actually lives, and I have the water schedules to prove it, unread.',
        attach(
            'The actual casus belli of most rural disputes, arriving on schedule.',
            GREAT_WAVE,
        ),
        attach(
            'How they get settled, after the schedules and the letters have failed.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'gateway_outsider_keep': (
        'The Gateway to the Land of the Burning Sands, and the Outsider Keep beside it. '
        'The 1st Legion holds both, and the difference between them is the whole entry.',
        'The Gateway is the formal boundary. The Keep is where the work of the boundary '
        'actually happens. One is a line on a map and the other has a roster, a '
        'supply problem, and a mood.',
        'Everything that comes east comes through there, and everything that goes west '
        "is somebody's idea. I have watched that sentence hold for four hundred "
        'sessions without exception.',
        'Travelers lost in the Shinomen Forest a hundred miles from the Gateway have '
        'walked out of the Isawa Woodlands. There is a between place nearby, and no, '
        'nobody has mapped it, and yes, I have asked.',
        'A keep named for outsiders tells you precisely what the Empire believes it is '
        'for, and the Empire has never once been embarrassed by the name.',
        "Gaheris' campaign is out that way. So is Medin al Salaat. So is everything the "
        'Empire files under "abroad", which is a heading I did not choose and cannot '
        'stop using.',
        'The duty is boring for years and then it is not, and the record keeps only the '
        'second kind - which makes my own record a liar about what the posting is like.',
        'What comes through is mostly merchants, and occasionally not, and the '
        'occasionally is the reason the whole apparatus exists and gets funded.',
        attach(
            'The Gateway. The line is administrative rather than geographical, which is '
            'true of most lines and comforting about none of them.',
            RAINY_MOON,
        ),
        attach(
            'What the Keep is actually watching for. It has arrived twice in the record '
            'and both entries are short.',
            GREAT_WAVE,
        ),
    ),
}
