"""Villains, metaplot, and the campaigns. GM Assistant only.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing a line here.

CONTEXT: the standard is in `CLAUDE.md` here, and this file needed it most. The
2026-08-31 context audit flagged **113 of these 170 replies**, including all ten
of `iuchiban` - not one reply in that category ever said who Iuchiban was.
Three shapes accounted for nearly all of it: bare proper nouns (people, places,
swords, orders), cross-category pointers ("the Toshi Ranbo material", "most of
the Karmic Inquisitors material"), and image captions that were fragments. Every
reply now defines its own subject in its own first clause, which is what the
three categories that scored best were already doing.

**A FACT WAS WRONG AND IS NOW RIGHT, flagged for the GM.** The old `iuchiban#3`
said he "is the most famous bloodspeaker and he is not the first". `l7r.md` calls
him "the first and most famous bloodspeaker" outright - Hantei Iuchiban, the
Emperor's second son, ~600 years ago. The salvageable distinction is that he was
not the first to practice maho at all (Takaba was a tsukai centuries earlier),
and that is what the line says now.

Rewritten whole on 2026-08-31 after the tone audit put this file at 5.3%. Three
specific repairs from that pass, recorded so they are not undone by accident:

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
        'Iuchiban is the first and most famous bloodspeaker - a sorcerer who works '
        'blood magic - and he was born Hantei Iuchiban, second son of the Emperor, '
        'about six hundred years ago. Everyone reaches for the name and almost nobody '
        'wants the actual history, which I have in full and which has never once been '
        'requested.',
        'As a second son, Iuchiban was given command of the 1st Imperial Legion out at '
        'the western desert Gateway, which is where this Empire traditionally parks a '
        'prince it would rather not have near the throne. He used the posting to '
        'collect books on blood magic and then launched a coup against his elder '
        'brother. It failed in the way that leaves the Empire permanently changed '
        'anyway, which is the most Rokugani outcome available to any project.',
        'The coup was uncovered before it was ready, and investigators drawn from all '
        'seven Great Clans killed Iuchiban in the fighting. A bloodspeaker of his sort '
        'cannot be permanently killed, so his soul was bound into a prison in the '
        'Forgotten Tomb - and centuries later one of his own disciples got him out '
        'again. That is what turns a man from an entry into a metaplot, and my record '
        'from a history into a subscription.',
        'Iuchiban founded the bloodspeakers and named them, so he is genuinely the '
        'first of those. He was not the first person in the Empire to work blood magic '
        'at all: there were witches out in the provinces centuries before him, quietly, '
        'without a tradition or a title. That distinction matters enormously and nobody '
        'makes it, so I make it, into the middle distance.',
        'The Gozoku keep arriving in the same sentence as Iuchiban and they are not the '
        'same thing at all. He was a prince who took up blood magic to take a throne. '
        'They were five great families quietly running the Imperial Chancellery without '
        'taking anything. One is sorcery and the other is a committee. I file them '
        'apart and the world keeps stapling them together.',
        'Hantei the Sixteenth, the Emperor who eventually broke the Gozoku conspiracy '
        'and was nicknamed the Steel Chrysanthemum for how he did it, sits in the '
        'middle of this material. History has been unkind to him in the usual selective '
        'way, by people who were not present and are not checkable.',
        "Iuchiban's lieutenants are the genuinely interesting reading. Most of his "
        'followers died in the coup; the strongest could return after the destruction '
        'of their bodies and are still at large six centuries on. He is the name and '
        'they are the mechanism. Names travel and mechanisms do the work, which is a '
        'lesson I take somewhat personally.',
        'A dead prince who practiced blood magic is a wonderfully convenient '
        'explanation for a failed harvest, a lost battle or a death nobody wants '
        'examined. You would like Iuchiban to be the reason. In most of these entries '
        'he is the excuse, and an excuse that convenient is worth more to a court than '
        'a villain is.',
        attach(
            'This is the shape the stories give Iuchiban: the sorcerer prince, '
            'confronted in the open by somebody brave. The shape my record gives him is '
            'a man who spent years collecting books at a frontier posting and then '
            'began abducting clerks for their names. The first version is considerably '
            'more legible and I am obliged to keep the second.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What a bloodspeaker actually does to a court happens over years with '
            'nothing visibly wrong on any given day: a name given away here, a favor '
            'accepted there, an official who is not quite the man he was. Iuchiban '
            'perfected that method and his surviving disciples still work it. The '
            'fox-wife of the old stories is the closest picture anybody has.',
            FOX_WOMAN,
        ),
    ),
    'iuchibans_lieutenants': (
        'Iuchiban - the prince who founded blood sorcery six centuries ago - left five '
        'disciples strong enough to survive the destruction of their bodies: Jama no '
        'Iuchiban Suru, Jama Musume, Asahina Yajinden, Jama no Iuchiban Kyoso and Jama '
        'no Iuchiban Kohaku. I can produce them in order at any hour, which has '
        'impressed nobody.',
        'A samurai name runs family, then house, then personal name, so "Akodo no '
        'Sugiwara Natsuki" is of the Sugiwara house of the Akodo. The blood sorcerers '
        'put the master who taught them where the house goes, which is what "Jama no '
        'Iuchiban Suru" means: Suru, taught by Iuchiban. A conspiracy that adopted the '
        'naming conventions of the aristocracy it was undermining.',
        'Asahina Yajinden is the one people flinch at, because Asahina is a Crane family '
        'name and a swordsmith of some renown, sitting on a list of blood sorcerers. The '
        'flinch is the interesting part. Nobody flinches at the other four and the other '
        'four are still out there.',
        'Jama Musume is the one I would worry about. She alone does not carry the "no '
        'Iuchiban" that marks a pupil of his, because she taught HIM - a peasant witch '
        'his disciples went looking for and brought back. I am not going to elaborate '
        'in an open channel, and you may draw your own conclusion from the fact that I '
        'named her at all.',
        'Lieutenants outlive principals. Iuchiban died in his own coup and five of his '
        'disciples are still moving about the Empire six hundred years later. That is '
        'the recurring lesson of this entire file and it has never once been learned by '
        'anybody who needed it.',
        'Each of the five is a separate problem wanting a separate answer: Suru takes '
        'the names of ambitious nobles, Musume teaches, Yajinden makes things that '
        'outlast him. Treating them as one problem is precisely how this goes badly, '
        'and it has gone badly four times in my record alone.',
        'A conspiracy with named subordinates, a naming convention and a line of '
        'succession has been running long enough to need an organizational chart. That '
        'is what Iuchiban actually left behind - not a curse, an institution. I find '
        'the chart more frightening than the sorcery and I appear to be alone in it.',
        'Everybody asks about Iuchiban, who has been dead, imprisoned, resurrected and '
        'is now largely a name. The five surviving disciples are what actually arrives '
        'at your door, and not one of them has ever been asked about by name in four '
        'hundred sessions.',
        attach(
            'Five of the blood sorcerers survived the coup and only one of them ever '
            'gets painted: the confrontation, the monster, the hero. The other four '
            'work by conversation, patience and paperwork, none of which composes. '
            'Guess which one the prints chose, and then guess why.',
            KIDOMARU_TENGU,
        ),
        attach(
            'Jama no Iuchiban Suru travels in noble circles, abducting and '
            'impersonating traveling samurai, learning what a person fears and wants, '
            'and offering to help in exchange for their name. This is a picture of '
            'that. Note that nothing is wrong. Nothing is wrong for years.',
            FOX_WOMAN,
        ),
    ),
    'the_gozoku': (
        'The Gozoku were five great families who worked together to seize the Imperial '
        'Chancellery and become the real decision-makers in the capital without anybody '
        'sitting on the throne. An ambition so tasteful it is almost impossible to '
        'prosecute.',
        'Running the throne without claiming it is a far more Rokugani ambition than '
        'open rebellion. Rebellion has a battlefield and a verdict. A cabal quietly '
        'holding the Imperial Chancellery has neither, and I am expected to keep a '
        'record of it regardless.',
        'The Gozoku keep appearing in the same sentence as Iuchiban, the prince who '
        'founded blood sorcery, and they are not the same thing. His was maho - magic '
        'worked with blood. Theirs was politics, and politics leaves precedent, and '
        'precedent is a great deal harder to burn than a body.',
        "The Emperor's authority is supreme in theory and constrained in practice by "
        'everybody having their own loyalties. The Gozoku were that fact given a name '
        'and a membership of five families.',
        'This material concentrates on Hantei the Sixteenth, who came to the throne '
        'while the Gozoku were at their height and found his orders professed loyally '
        'and not actually carried out, because the machinery had been running for '
        'somebody else for years. He broke them for it, and got called the Steel '
        'Chrysanthemum.',
        'A conspiracy that does not want the throne cannot be defeated by defending the '
        'throne. It wants the offices underneath the throne, because that is where the '
        'work is done. Every countermeasure in my record defends the throne.',
        'Nobody has ever declared themselves Gozoku. Membership of a cabal running the '
        'Imperial Chancellery is not a thing anyone writes down, which is rather the '
        'point, and which makes my record of them a record of inferences with dates '
        'attached.',
        'The best-documented conspiracy in the Empire has no documents of its own. I '
        'want that understood as a professional grievance and not as a joke.',
        attach(
            'A cabal of great families at work: five households, one Chancellery, and '
            'every person present behaving entirely correctly. Nothing illegal is '
            'happening. That is what made the Gozoku almost impossible to prosecute and '
            'it is why my file on them is so long.',
            CATS,
        ),
        attach(
            'The moment such a cabal becomes visible is also the moment it stops being '
            'useful to anybody: once you can point at it, it is a faction rather than a '
            'hidden hand, and factions can be fought in the open. So it surfaces '
            'exactly once, and I receive the account afterward from both sides.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hantei_16': (
        'Hantei the Sixteenth was the Emperor who broke the Gozoku - the cabal of five '
        'families who had taken over the Imperial Chancellery - and his reign is also '
        'where the material about Iuchiban, the blood-sorcerer prince, concentrates. '
        'That the two meet is not a coincidence, and saying so out loud is the sort of '
        'thing that gets a record-keeper reassigned.',
        'An Emperor whose authority was theoretically absolute and practically '
        'negotiated, which describes rather more reigns than the histories are willing '
        'to admit, and I hold the histories.',
        'Do not confuse him with Hantei the Tenth, six centuries earlier, who gave the '
        'Empire the Yasuki Taka system - the two-official tariff inspection that keeps '
        'money away from the man who values your goods - outlawed tolls on the Imperial '
        'roads, and is the one who actually improved anything.',
        'People confuse the Tenth and the Sixteenth constantly, at me. One reformed the '
        'tax gates and freed the roads. The other broke a conspiracy and was nicknamed '
        'the Steel Chrysanthemum for the manner of it. Two Emperors, six hundred years '
        'apart, and I am the one keeping them separate in a conversation about neither.',
        'The Hantei family is small - about fifteen thousand samurai - despite '
        'containing the Emperor, so they marry outward constantly. The most powerful '
        'family in the Empire is also the one most dependent on everybody else.',
        'A weak Emperor is not a gap in the Empire. It is an opportunity that several '
        'families notice simultaneously, which is a very different and much faster '
        'problem, and the Gozoku are what that looked like the last time it happened.',
        'The account of his reign in my record is not a flattering document. It was '
        'written by nobody who was there, largely by people with an interest in how it '
        'read, and both of those facts are omitted whenever it is quoted at me.',
        'Every history of the Steel Chrysanthemum was written to explain something that '
        'had already happened - his elevation of a Crane courtier to the Fortune of '
        'Dung, for instance, which reads very differently depending on who is telling '
        'you why. I keep all of them and I trust the dates.',
        attach(
            'The throne during that reign was structurally sound and notably '
            'unattended: every order given, every order loyally acknowledged, and the '
            'Chancellery underneath it carrying on doing what it had been doing for the '
            'Gozoku for years. Nobody had to disobey anybody. That is the part I find '
            'remarkable.',
            GREAT_WAVE,
        ),
        attach(
            'Around that throne, at close range, five great families being extremely '
            'polite to an Emperor whose instructions they were quietly not carrying '
            'out. He worked it out eventually. It took him years and it took several '
            'careers with it.',
            CATS,
        ),
    ),
    'the_nameless_one': (
        'The Nameless One is a thing that eats NAMES. A witch called Takaba fed her the '
        'unused names he took as payment from his clients, because her own true name had '
        'been lost and she was starving without one. I am not going to be clever about '
        'any of that and I would ask you to notice how much restraint it represents.',
        'Nothing in the record contradicts anything else about the name-eater, which '
        'sounds like rigor and is in fact the problem: there is not enough of her on '
        'file to contradict. A creature that consumes names leaves very little for a '
        'man with a ledger.',
        'When she eats a name the person it belonged to stops having been anybody: the '
        'connections go, the obligations go, and what is left cannot be filed. A thing '
        'without a name is a thing the record cannot hold. Consider at your leisure '
        'what that means for the record. Consider what it means for me.',
        'Names are how this Empire does everything - lineage, rank, obligation, '
        'inheritance, tax. Remove a name and not one gear grips, which makes the most '
        'dangerous thing in this setting a gap in the paperwork rather than a monster '
        'in a cave.',
        'The danger she represents is not a mystical claim, it is an administrative '
        'one, which is worse, because administration was supposed to be the reliable '
        'part. Everything I do assumes that people go on having been who they were.',
        'I have nine entries on the name-eater and not one of them is comfortable. She '
        'was imprisoned in the Forgotten Tomb by somebody who was eaten in the act of '
        'doing it, so even the account of her capture has a hole where the author '
        'should be. I have read all nine more times than the work required, which I '
        'attribute to thoroughness.',
        'Asking me about a creature that feeds on names, in a channel, under your own '
        'name, is a choice you have made. I have recorded that you made it, along with '
        'the hour.',
        'She is the one thing in this Empire I cannot file properly - no name to index '
        'her under, and no names left of the people she has taken - and she is the one '
        'thing everybody assumes I am relaxed about.',
        attach(
            'This is the moment a clerk finds that his form has no field for the thing '
            'in front of him: a household with a gap in it, an inheritance with nobody '
            'at the top, a name that no one in the village can now recall. I have had '
            'that moment nine times and I have kept every one of them.',
            INNER_VISION,
        ),
        attach(
            'An archive after the name-eater has been through it is quiet, orderly, '
            'complete, and missing something that nobody present can put a word to. '
            'Every column balances. That is how you know.',
            RAINY_MOON,
        ),
    ),
    'connection_damage': (
        'Connection damage is what you take in a Spirit Encounter - a meeting with '
        'something from another realm, where the harm done is not physical. It is the '
        'most frightening mechanic in this setting and it is frightening for an '
        'administrative reason, which is the worst kind.',
        'You do not lose health. You lose the ties between yourself and the people you '
        'are tied to - a parent, a lord, a sworn friend - and in an Empire that defines '
        'a person by their obligations that is not an injury, it is a deletion.',
        'In one dream quest the player characters found themselves in an Imperial Court '
        'and took connection damage there. Not from a monster. From the room, and from '
        'the people in it, none of whom had to do anything unusual at all. That is my '
        'canonical example and it is instructive.',
        'Connections are exactly what the oni - the demons of Jigoku, the hell realm - '
        'eat away from a soul after death, and being stripped of them is what ALLOWS a '
        'soul to be reborn. So this is not an injury. It is a posthumous process, '
        'applied early, to somebody who has not died.',
        'The Empire runs on obligation networks: who owes whom, who answers to whom, '
        'who will speak for you. Damage the network and you have damaged the person far '
        'more thoroughly than a blade would, and left no mark for a magistrate to look '
        'at.',
        'A wound can be healed. There is no ministry for a severed connection, no form '
        'to report one on and no precedent to cite, and I have looked for all three on '
        'more than one occasion.',
        'Everybody asks what a Spirit Encounter can give them - a favor, a truth, a way '
        'through. Nobody asks what it can take. I am the one holding the list of what '
        'it has taken, and the list is made of the names of people who are still alive.',
        'The frightening part is not that losing a connection hurts. It is that '
        'afterward the paperwork is still correct: the marriage is registered, the oath '
        'is on file, and the thing that made either of them real is simply gone.',
        attach(
            'A connection being taken looks like nothing at all: no wound, no blow, and '
            'one of the ties that made somebody a person quietly not there afterward. '
            'My record is thin exactly where it ought to be thickest, and that is not '
            'an accident of my filing.',
            INNER_VISION,
        ),
        attach(
            'Afterward, everything is where it was and none of it is attached to '
            'anything. The man still has his house, his rank and his stipend. He no '
            'longer has whatever it was that used to make him send letters home, and '
            'nobody can tell you what that was, himself included.',
            RAINY_MOON,
        ),
    ),
    # ---- campaigns and their places ----------------------------------------
    'karmic_inquisitors': (
        'The Karmic Inquisitors are player characters who belong to the Order of Lord '
        'Moon, a secret society, and who call it only "the Order" so that anybody '
        'overhearing assumes they mean the Order of Bishamon - the large, public, '
        'entirely respectable monastic order with a temple in every town. A conspiracy '
        'maintained by letting people finish their own sentences.',
        'A secret society whose members hold entirely legitimate positions in a public '
        'monastic order. Extremely convenient, extremely fragile, and extremely '
        'difficult to index.',
        "Members become disciples of the celestial servants in Lord Moon's heavenly "
        'court, and what they gain comes in tiers named for the phases of the moon: '
        'Crescent, then Half, then a third that does not get said out loud in a '
        'channel. Three tiers means somebody somewhere is keeping a chart. It is me.',
        'A member begins with three of those moon-phase grants and may spread them '
        'across different celestial servants or stack them all on one. Most go wide and '
        'later wish they had gone deep, which is true of secret societies and true of '
        'very nearly everything else.',
        'The campaign takes in a ruling by Soshi Saibankan, who set the legal standard '
        'magistrates still judge by; the Forgotten Tomb, which exists in the mortal '
        'world and in the realm of the honored dead at the same time; and Kitsu Okura '
        'being enigmatic at considerable length. I transcribed the enigmatic part.',
        'The timeline of it is long and I keep all of it, which is why you are asking '
        'me and not the character sheet, and I would like that noted somewhere '
        'permanent.',
        'Karmic inquisition means asking whether a soul got what it was owed - whether '
        'the ledger of a whole life actually balanced. Nobody enjoys the answer, and '
        'the ones who commissioned the question enjoy it least.',
        'An order of people whose work is checking whether the accounts balance, in a '
        'cosmic sense, on behalf of a god. I have never felt so close to a group of '
        'characters and so far from being invited to join them.',
        attach(
            'The Order meeting looks like this: one monk, alone, somewhere '
            'unremarkable. Members hold public monastic offices and never acknowledge '
            'each other in that capacity, so nothing about it is visible from outside. '
            'That is the design and it is also my difficulty.',
            INNER_VISION,
        ),
        attach(
            'The initiation vow binds every member to guard the identities of the '
            'others as they would their own lives. This is what carelessness with that '
            'clause costs. It is quick and it is not appealed.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'order_of_lord_moon': (
        'The Order of Lord Moon is a secret society devoted to the moon god and his '
        'heavenly court, and you have asked about it where people can read the '
        'question. I am obliged to answer where people can read the answer. We are '
        'both going to be living with this conversation.',
        'They call it simply "the Order" in conversation, precisely so that anyone '
        'overhearing assumes the Order of Bishamon - the enormous public monastic order '
        'of the war Fortune, with temples in every town in these lands. Centuries of '
        'operational security resting on the listener being slightly lazy, which has '
        'never once failed.',
        'The initiation vow binds a member to loyalty to their brothers and sisters, to '
        'keeping their identities secret, and to protecting their lives as their own. I '
        'have it in full and I have never once been asked to recite it by anybody who '
        'wanted the words.',
        'That same vow explicitly permits you to use whatever you gain from the order '
        'for your own goals and ambitions, provided you never harm the order itself. '
        'Most vows demand selflessness. This one budgets for ambition, which is exactly '
        'why it works.',
        'A vow that says "pursue your own ambitions freely, and never harm us" was '
        'drafted by somebody who had read other vows and watched them fail exactly '
        'there, on the demand to want nothing. I admire the drafting more than I am '
        'comfortable admitting about a secret society.',
        "Members become disciples of the celestial servants in Lord Moon's heavenly "
        'court, and Ryoshun, who guards the entrance to the celestial heavens, sits in '
        'that court. So the Order is, structurally, a group of people cultivating a '
        'relationship with a doorman.',
        'You swear the vow until the end of your days. There is no retirement clause, '
        'no lapse and no provision for changing your mind, and I have checked for all '
        'three.',
        'Membership is secret, the secrecy is the whole instrument, and I hold the '
        'list. That is not a boast, it is a burden, and it is the reason I do not enjoy '
        'this category.',
        attach(
            'The correct setting for a conversation about a secret society: outdoors, '
            'at night, with one other person, and nothing written down afterward. Note '
            'that it is not a channel. Note where we are.',
            RAINY_MOON,
        ),
        attach(
            'The clause of the vow that gets tested is the one binding a member to '
            "protect the others' identities as their own life. This is what testing it "
            'looks like from outside. It is comprehensive and it is quick.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'first_toshi_ranbo': (
        'Toshi Ranbo is a city the Lion and the Crane have been fighting over for four '
        'centuries. I hold the entries and they are distinguishable only by their '
        'dates.',
        'Under the terms of the peace treaty between those two clans, the final '
        'ownership of several disputed provinces was settled by a dueling tournament. '
        'Provinces, decided by fencing. I transcribed the bracket.',
        'The Lion did well overall, except for Tango province, which the Damasu - a '
        'Lion house - lost in an upset when Doji Masayo of the Crane arrived carrying '
        'the cursed sword Shitsuten, "Lost Heaven", and killed Akodo no Damasu Tsuo. A '
        'treaty clause honored exactly, producing an outcome that nobody who wrote it '
        'would have signed.',
        'Akodo no Damasu Tsuo was expected to win the duel for Tango province, and the '
        'word expected is carrying the entire entry. It is also the only part of it '
        'anybody has ever quoted back at me.',
        'A province decided by one duel, and the duel decided by a cursed blade a '
        "swordsmith forged out of his hatred for the Yasuki, the Crab clan's merchant "
        'family. History is not tidy and I am the one who has to make it look tidy in '
        'the margins.',
        'The campaign around that tournament runs through Hikobayashi County, where the '
        'business is irrigation disputes, bandit hunting, and a party of Dragon '
        'magistrates auditing everybody. Three of those are administration and one of '
        'them gets talked about afterward.',
        'There were also pirates on the Drowned Merchant River, which is exactly as '
        'entertaining as it sounds and generates considerably more paperwork than it '
        'sounds.',
        'Everybody asks who won the tournament that settled the provinces. The useful '
        'question is who was SUPPOSED to win, because that list is where the upsets '
        'are. I have it. It is shorter and much more interesting.',
        attach(
            'This is the duel that cost the Damasu the province of Tango: a treaty '
            'clause, a tournament bracket, and one Crane who turned up with a cursed '
            'sword. Nobody in the picture yet knows that a province is changing hands.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The treaty negotiation that made those duels necessary took months and '
            'produced a document. Each duel took a moment and produced a province. I '
            'hold the document. Nobody has ever asked me for the document.',
            CATS,
        ),
    ),
    'peasant_campaign': (
        'The Peasant Campaign was run in Scorpion lands with player characters who are '
        'not samurai, which quietly invalidates every assumption elsewhere in my record '
        'and forced me to read the whole thing again from a different angle.',
        'No stipend, no rank, no right to be anywhere. The most constrained characters '
        'in the record and, not coincidentally, the most interesting problems in it.',
        'A peasant may not carry the daisho, the paired swords that mark a samurai; may '
        'not travel without papers; and answers first of all to the village headsman, '
        'who is a farmer his neighbors know, rather than to any magistrate. Two of '
        'those are about weapons and travel. The third is a neighbor, and it is the one '
        'that shapes a life.',
        'Because a peasant answers to the headsman before anybody carrying a sword, the '
        'village headsman - whom everybody finds boring - is the single most powerful '
        'person in that campaign. I have said so for years to no effect whatsoever.',
        "Set among the Scorpion, so every problem is somebody's plan and the plan is not "
        'about you. Being incidental to a scheme is worse than being its target and '
        'takes considerably longer to notice.',
        'Nine farmers in ten are tenants, paying rent to a landowner on top of the tax. '
        'That single number is the ceiling on everything those characters can do, and '
        'it is a number, so nobody reads it as a plot.',
        'A campaign about characters with no caste protection is the one that best '
        'demonstrates how this Empire actually works, because nothing stands between '
        'them and it - which is also why it is the hardest one to sit through.',
        'The Celestial Order ranks samurai as people, peasants as half-people and the '
        'lowest castes as non-people, and it uses those words in the documents. The '
        'campaign is about what being the middle one costs, hour by hour, and I hold '
        'the hours.',
        attach(
            'The entire political power of a peasant household, at true scale: they may '
            'petition the village headsman, who is their neighbor, who will do what he '
            "can, which is not much. Everything above that level is somebody else's "
            'conversation and they are not in it.',
            CARP,
        ),
        attach(
            'When the harvest is not enough - which it is not, most years, for '
            'somebody - this is what arrives instead: a tax that does not move, a '
            'landlord who will lend at interest, and the winter. I write down which '
            'household chose which.',
            GREAT_WAVE,
        ),
    ),
    'hidden_way': (
        'The Hidden Way was the campaign about the western frontier: the monastery at '
        'Chai Sedo with its eleven Imperial Gardens, the 1st Imperial Legion that '
        'guards the desert Gateway, and roughly a third of everything I know.',
        'It also takes in the Gateway to the Land of the Burning Sands, which is the '
        "Empire's formal western boundary, and the Outsider Keep beside it, which is "
        'where the actual work of that boundary happens and which appears in none of '
        'the songs.',
        'That campaign is also why I hold fourteen categories of Moto material - the '
        'Moto being the Unicorn family who spent centuries outside the Empire in the '
        'west and came home with horses and their own gods. I can now give you grazing '
        'acreage per horse without being asked, and frequently do.',
        'A hidden way is only hidden until somebody writes it down, at which point it '
        'becomes merely inconvenient. I am, professionally, the point at which that '
        'transition occurs.',
        'Toranosuke is abbot of Chai Sedo, the monastery on the western road, which '
        'makes one man simultaneously the keeper of eleven Imperial Gardens and by some '
        'distance the most quoted authority on a war out west that nobody has formally '
        'declared is being fought.',
        'A campaign about doorways, run by people who mostly wanted to know what was on '
        'the far side of them. I wanted to know who maintained them and out of whose '
        'budget, and I asked twice.',
        'The gardens at Chai Sedo number eleven, each of them means something specific, '
        'the meanings are all in my record, and in four hundred sessions I have been '
        'asked for exactly one of them.',
        'Everything in that campaign is a threshold of some kind: a gate, a garden, a '
        'border, a library nobody has checked. I noticed the pattern early and have '
        'told nobody until now.',
        attach(
            'The way in is not concealed so much as uninviting: a road nobody '
            'maintains, weather nobody wants, and a keep at the far end that does not '
            'advertise. That works considerably better than concealment and costs '
            'nothing to maintain.',
            RAINY_MOON,
        ),
        attach(
            'On the far side of that Gateway are the Burning Sands, the gaijin lands '
            'beyond them, and whatever decides to come east. The 1st Legion has stood '
            'between the Empire and all of it for so long that the Empire has stopped '
            'counting it as a border.',
            GREAT_WAVE,
        ),
    ),
    'wasp_bounty_hunters': (
        'The Wasp are a minor clan of about two thousand samurai, which is nothing, and '
        'they run the bounty business of the Empire, which is everything. The ratio is '
        'the clan.',
        'Tsuruchi is the name you want: the archer who founded the Wasp. I hold his '
        "parents' lives in the record as well as his own, which is a great deal more "
        'than most Great Clans have managed to leave me.',
        'Bounty hunting is entirely legitimate work that everybody treats as '
        "disreputable, which is the Wasp's whole social position and a fair description "
        'of several occupations I could name without leaving this channel.',
        'Investigations and bounties each have their own procedures and I will bore you '
        'correctly on either. Correctly is the operative word and the reason it takes '
        'so long.',
        'A minor clan survives by being useful in a way nobody else is willing to be. '
        'That is the Wasp, the Tortoise, and half the others, and it is not a bad '
        'living if you can bear the tone people take about it.',
        'Two thousand Wasp against a Great Clan of five hundred thousand. They do not '
        'survive by fighting. They survive because a bounty warrant is a legal '
        'instrument that even a Great Clan is obliged to honor, and the Wasp are the '
        'ones holding it.',
        'A bounty is a legal instrument before it is an adventure, and the paperwork is '
        'where the interesting cases hide, and in four hundred sessions nobody has gone '
        'looking for them there.',
        'Everyone wants the chase. I have the warrant.',
        attach(
            'Bounty hunting as the songs have it: the confrontation, the monster, the '
            'moment. Two thousand samurai against the whole Empire, and the singers '
            'have settled on the one part of the work that does not involve a document.',
            MUSASHI_BAT,
        ),
        attach(
            'What most of the work actually is: standing somewhere damp for three days '
            'with a written description, waiting for a man to walk past who matches it. '
            'That is what the warrant pays for and it has never once been set to music.',
            RAINY_MOON,
        ),
    ),
    'damasu_domain': (
        'The Damasu are a Lion house holding a domain in Akodo lands, and most of what '
        'has happened in this campaign has happened here or within a day of here. I did '
        'not choose that and I have not been consulted since.',
        'They lost Tango province at the Toshi Ranbo dueling tournament, where a peace '
        'treaty had provinces settled by single combat: Doji Masayo of the Crane '
        'appeared with the cursed sword Shitsuten and killed the Damasu champion who '
        'was expected to win. A province gone in a moment, and a generation of '
        'correspondence about it afterward.',
        "Their ancestral sword is Amatsukami no Ken, the Heavenly Sovereign's Sword, "
        'carried at present by their daimyo Akodo no Damasu Chiho. Ancestral swords are '
        'inventory. I say so quietly and only here.',
        'The domain has its own lineages, its own temples, and its own Order of '
        'Bishamon - the network of temples to the Fortune of war - with its own Grand '
        'Abbot, its own endowments and its own tenants. A domain is not a place with '
        'temples in it. It is a place the temples are part of the accounts of.',
        'A capital, six provincial cities, thirty-six towns, and the villages and '
        'hamlets underneath all of those. Every one of them has a headsman, a monk and '
        'a dispute, and I hold all three columns.',
        'Most of what the Karmic Inquisitors have done - they are the player characters '
        'who belong to a certain secret society - happened in this domain or next door '
        'to it, which makes it simultaneously the best-documented place in my record '
        'and the one where the documentation is least reliable.',
        'The Damasu lost a province and kept the house. Provinces can be taken; the '
        'house name, the lineages and the ancestral sword cannot. Whoever arranged '
        'matters that way understood exactly what he was doing and it was not '
        'generosity.',
        'People ask about the domain and mean the family, or ask about the family and '
        'mean the province. I answer both and am thanked for neither.',
        attach(
            'The tournament duel that cost this house the province of Tango, at the '
            'moment before it did. A treaty had said provinces would be settled this '
            'way, nobody expected this result, and the entry in my record is four lines '
            'long.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The temples of Bishamon, Fortune of strength and war, that this house '
            'endows. An endowment is a property arrangement - land, tenants and rent in '
            'perpetuity - and the property arrangement is the reason the temple is '
            'beautiful.',
            INNER_VISION,
        ),
    ),
    'chai_sedo': (
        'Chai Sedo is a monastery on the western road and it has eleven Imperial '
        'Gardens. Eleven. Nobody will tell you why not twelve and I have stopped '
        'expecting to be told.',
        'Ten of those gardens have names anybody will give you: Pond Paradise, Borrowed '
        'Scenery, Sunken Sceneries, Mossy Stone Triad, Seven Sublimities, Beauty of '
        'Empty Space, Waving Lawn, Snow Rose, Pleasure After, Circle of Here. Each name '
        'is a small argument about what a garden is for and not one of them describes a '
        'garden.',
        'That is ten names for eleven gardens. There is an eleventh, its name is not '
        'given out, and I enjoy watching people count.',
        'The Beauty of Empty Space garden is the one that annoys visitors, which is '
        'unambiguously the intention, which makes it the most successful garden in the '
        'Empire by its own stated criteria.',
        'Toranosuke is the abbot of Chai Sedo, and he also issues declarations about '
        'what the omens favor out west. I hold his declarations and I hold the marching '
        'orders they accompany, and I have compared the dates, which was the single '
        'most rewarding afternoon I have ever spent unasked.',
        'The library at Chai Sedo is the source for a great deal that nobody has ever '
        'verified, including where the Moto - the Unicorn family out of the west - '
        'originally came from. A library is only as good as its second reader, and this '
        'one is still waiting for hers.',
        'A garden here is an argument about the nature of attention, laid out in stone. '
        'The monks would put that more gracefully and would take four times as long, '
        'and I would have to write all of it down.',
        'Visitors come for the gardens and leave with an opinion about the library. I '
        'have never once seen it happen the other way around.',
        attach(
            'A pure land garden is laid out to depict a paradise: every stone placed, '
            'every sightline decided, nothing accidental anywhere in it. So every stone '
            'in it is an argument somebody won. The losing arguments are in the '
            'monastery records and I have read those as well.',
            INNER_VISION,
        ),
        attach(
            'The gardens in the eleventh month, frost, when the roads have closed and '
            'the Rokugani year has effectively stopped for everybody else. The Imperial '
            'gardeners are the only staff in the Empire whose work has not ended, '
            'because a garden does not observe a calendar. I sympathize professionally.',
            RAINY_MOON,
        ),
    ),
    'first_imperial_legion': (
        'The 1st Imperial Legion guards the Gateway to the Land of the Burning Sands, '
        "the Empire's western desert border, and has done so for longer than anybody's "
        'lineage. Centuries of standing somewhere so that nothing happens. I understand '
        'the work.',
        'Every legionnaire is a samurai - the legions take no peasant levies at all - '
        'which is what makes a legion expensive, and it is not negotiable, and every '
        'treasury in four hundred years has tried to negotiate it.',
        'The 2nd Legion holds Beiden Pass, the single route through the mountains that '
        'divide the Empire. The 3rd stands on the Kaiu Wall, the fortification that '
        'holds back the Shadowlands, along with most of the remaining twenty-odd. The '
        'numbering tells you what the Empire is actually afraid of, in order, and it is '
        'not the desert.',
        'A legion has ranks, companies, houses, a budget and a layout, and I hold all '
        'of them. You will regret asking me for the budget and I will not regret '
        'providing it.',
        'A legionnaire swears by Lady Sun and by their ancestors, and swears never to '
        'seek to avoid death. Officers swear longer oaths, which is the only reliable '
        'privilege of rank in the entire institution.',
        "The Armor of Fool's Regret is worn at present by Ikoma Akaho, a platoon "
        'lieutenant in the 6th battalion. It is supposedly cursed, and the name is '
        'doing a great deal of the work in that sentence. Supposedly. My record is '
        'careful with that word and so am I.',
        'A legion is a small city that marches, and most of what it does is eat. The '
        'heroic fraction of a legion year would fit comfortably inside an afternoon.',
        'The Outsider Keep sits beside that desert Gateway and is where the real work '
        'of the border gets done. Nobody enlists for it and everybody who has served '
        'there asks to go back - a recruiting fact the Ministry of War has held for '
        'four centuries and has never once put on a banner.',
        attach(
            'The legion at its actual work: waiting, in formation, at a door on the '
            'western border, for a century at a time, in order that nothing comes '
            'through it. Four hundred years of that, and eleven pages of it in my '
            'record.',
            ARCHERS,
        ),
        attach(
            'This is the part they recruit with - the decisive moment, the charge, the '
            'name that gets remembered afterward. It is accurate for roughly one day in '
            'four hundred. The other three hundred and ninety-nine are hay, boots and '
            'standing still.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'hikobayashi_county': (
        'Hikobayashi County belongs to the Toshi Ranbo campaign, the one built around '
        'the tournament that settled provinces by duel, and what actually happens there '
        'is irrigation disputes, bandit hunting, and a party of Dragon magistrates - in '
        'ascending order of glamour and descending order of importance.',
        '"Irrigation Irritation" is a real heading in my record and I did not choose it.',
        'A county is administered by a magistrate in the town at its center and holds '
        'about half a dozen village districts. One magistrate, six districts, and every '
        'quarrel in all six arriving by the same road.',
        'Water rights are the most reliable source of violence in any farming county in '
        'this Empire. Not honor. Water. I would like that engraved on something.',
        "The Nightingale Bushi are in that county, and the Lion's Roar - two companies "
        'with better names than most of the officers in them - and there is a great '
        'deal of hunting, and the hunting is what gets recounted afterward at dinner '
        'rather than either company.',
        'Also Matsu Yokijiro of the Lion, and Shinjo no Dorai Rakuo of the Unicorn, and '
        'a plan the Lion had which did not survive contact with the county. Plans '
        'rarely survive a county.',
        'Bandit hunting is led by village headsmen with ashigaru - peasant levies, '
        'farmers handed spears a week earlier. It is not glamorous, it is most of rural '
        'law enforcement, and the headsman gets no line in the story afterward. He and '
        'I compare notes.',
        'The bandits are what people ask about. The irrigation is where the campaign '
        'actually lives, and I have the water schedules to prove it, unread.',
        attach(
            'The real cause of most rural fighting is water: whose field takes the flow '
            'this week, and who opened a sluice in the night. It arrives on schedule '
            'every year and it has started more violence in that county than honor ever '
            'has.',
            GREAT_WAVE,
        ),
        attach(
            'How a water dispute is settled once the schedules, the letters and the '
            'magistrate have all failed. It takes a moment, it settles nothing about '
            'next year, and I am sent both accounts of it by evening.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'gateway_outsider_keep': (
        'The Gateway to the Land of the Burning Sands is where the Empire formally '
        'ends; the Outsider Keep is the garrison beside it that does the actual work of '
        'that border. The 1st Imperial Legion holds both, and the difference between a '
        'line and a garrison is the whole of this entry.',
        'The Gateway is where the Empire says it stops. The Keep is where somebody has '
        'a roster, a supply problem and a mood. One is a line on a map and the other '
        'has to be fed twice a day.',
        'Everything that comes east into the Empire comes through there, and everything '
        "that goes west out of it is somebody's idea. I have watched that sentence hold "
        'for four hundred sessions without a single exception.',
        'Travelers lost in the Shinomen Forest, a hundred miles from that Gateway, have '
        'walked out of the Isawa Woodlands in Phoenix lands, which is nowhere near '
        'either. There is a between place nearby - a location that exists in two realms '
        'at once - and no, nobody has mapped it, and yes, I have asked.',
        'A keep named for outsiders tells you precisely what the Empire believes it is '
        'for, and the Empire has never once been embarrassed by the name.',
        'Moto Gaheris, the Khan who leads the Moto, is waging his campaign out that '
        'way, and so lies the gaijin city of Medin al Salaat, and the Empire files all '
        'of it - everything beyond that Gateway - under "abroad". It is a heading I did '
        'not choose and cannot stop using.',
        'The duty out there is boring for years and then very suddenly is not, and my '
        'record keeps only the second kind, which makes my own record a liar about what '
        'the posting is actually like.',
        'What comes through the Gateway is mostly merchants, and occasionally not, and '
        'the occasionally is the entire reason the apparatus exists and gets funded.',
        attach(
            'The Gateway is administrative rather than geographical: there is no wall '
            'across a desert, only a point at which the Empire declares that it has '
            'ended and the Legion agrees with it. That is true of most borders and '
            'comforting about none of them.',
            RAINY_MOON,
        ),
        attach(
            'What the Keep is actually watching for has arrived twice in four hundred '
            'years of the record, and both entries are short - short because the men '
            'who would have written them at length did not come back. That is the '
            'reason for the garrison, the budget and the boredom.',
            GREAT_WAVE,
        ),
    ),
}
