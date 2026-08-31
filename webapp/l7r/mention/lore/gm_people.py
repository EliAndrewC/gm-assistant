"""Significant people, relics and geography. GM Assistant only.

Only people the GM kept as individuals live here. Anyone else who is merely
name-shaped gets the dismissal in `gm_clans.py` - and a HOUSE (`Akodo no
Damasu`) gets the houses handling instead, which is the distinction the GM
corrected and `topics.py` enforces by ordering.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing a line here.

CONTEXT: the standard is in `CLAUDE.md` here. The 2026-08-31 context audit
flagged **84 of these 150 replies**, and `kuni_isamu` failed 10 out of 10 - not
one reply said who Isamu was or what happened at the Forgotten Tomb, so a player
who named him learned only that the bot found him interesting. The facts were in
`l7r.md` the whole time (a Crab Witch Hunter who went to the Classrooms of the
Great Masters inside the Tomb, came back with new insight and with his
perception and speech impaired), and they are in the replies now.

The other repeated failure was the back-reference opener - "Which leaves...",
"why the number is three", "The instrument." - each pointing at a sibling reply
that ships separately or not at all. Every reply now restates the premise it
jokes about.

Rewritten whole on 2026-08-31 (tone audit rate: 4.7%). The repairs specific to
this file, so they are not quietly undone:

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
        'Kitsu Okura is the Lion priest who wrote the six doctrines of attunement - the '
        'theology of how one of the Fortunes, which is what this Empire calls its gods, '
        'comes to answer a person at all. Prince Daigotsu once observed that Okura is '
        'more enigmatic than the Dragon Clan he derides for being enigmatic. I have '
        'never seen it put better and I have had four hundred sessions in which to see '
        'it put.',
        'Okura is the authority on how the gods of this Empire come to answer anybody, '
        'and he spends a good deal of his time deriding the Dragon Clan for being '
        'obscure and impossible to pin down. He is worse. Everybody notices, nobody '
        'says it to him, and I have written it down where he cannot get at it.',
        'His six doctrines of attunement explain how a person aligns themselves closely '
        'enough with a Fortune - one of the gods - to be answered by it. I have had all '
        'six explained to me twice and I could not tell you whether they agree with one '
        'another, and I suspect that is the intended result.',
        'Agasha Tamori, a scholar of another clan entirely, has written a study of Kitsu '
        'Okura and his six doctrines of how the gods answer people, which is how you '
        'know the man matters and how you know the study will not help. Scholarship '
        'about an enigma is an enigma with citations.',
        'The whole dream-divination framework runs on his theology, so if you have ever '
        'asked a Fortune - one of the gods - for guidance in your sleep, you were using '
        'the doctrines of Kitsu Okura and almost certainly crediting the god.',
        'Attunement is what Okura calls aligning yourself closely enough with a god to '
        'be answered by it. Ask him a direct question about it and receive a better '
        'question back. It is infuriating, it is usually correct, and it doubles the '
        'length of every transcript I have to take.',
        'The priest of the six doctrines appears in this record twenty times and not one '
        'of the twenty is a straight answer. I index by subject. He has defeated the '
        'index.',
        'I like Okura. I like his doctrines. I would like both considerably more from '
        'about a hundred yards away, in writing, with the questions submitted in '
        'advance.',
        attach(
            'Kitsu Okura explaining attunement - how a person gets close enough to a god '
            'to be answered by one. This is minute four. There are five more doctrines '
            'after this one and he has not yet reached the end of the first.',
            INNER_VISION,
        ),
        attach(
            'Somebody who asked the Lion priest Kitsu Okura a simple question about the '
            'gods, at minute forty, no longer certain what they originally asked. I '
            'have been that person. I took notes at the time and the notes did not help '
            'either.',
            RAINY_MOON,
        ),
    ),
    'soshi_saibankan': (
        'Soshi Saibankan was a Scorpion magistrate, and one ruling of his sits in the '
        'record - the judgment that set the standard magistrates still use, that a case '
        'is decided on the totality of circumstance rather than on any fixed list. That '
        'ruling is the only reason you have heard the name.',
        'Saibankan means judge. A Scorpion named judge - the Scorpion being the clan the '
        'Empire openly acknowledges as its liars, spies and blackmailers. Sit with that '
        'for a moment. The Empire evidently did not.',
        'His ruling - that a magistrate may weigh the totality of circumstance, anything '
        'they consider relevant - is cited the way precedent is always cited: by people '
        'who have not read the reasoning, to people who will not check.',
        'What Saibankan settled is that nothing whatever is out of bounds for a judge '
        'weighing a case, and the reasoning behind that judgment is the good part. The '
        'verdict is merely the verdict. I hold both and am asked for the '
        'verdict every single time.',
        'A magistrate drawn from the Scorpion, whose entire reputation is for deceit '
        'and blackmail, is not a contradiction. The Empire needs somebody to do '
        'the unpleasant necessary things and then needs somebody to blame for them. Same '
        'clan. Extremely efficient.',
        'When a Scorpion rules against their own interest, look harder. That is not '
        'cynicism about a clan famous for deception, it is a filing instruction, and it '
        'has never once been wrong.',
        'A judge whose clan is famous for lying, handing down the rule that a magistrate '
        'may consider anything he finds relevant, in an Empire that never noticed the '
        'joke. I noticed. I have nowhere to put it.',
        'I have the totality-of-circumstance ruling in full, reasoning and all, and on '
        'the day somebody asks me for the reasoning rather than the verdict I intend to '
        'make an occasion of it.',
        attach(
            'A Scorpion magistrate delivering the ruling that still governs how every '
            'case in the Empire is weighed: brief, correct, and ostensibly about '
            'something else entirely. That is how the good ones do it and it is why they '
            'are hard to appeal.',
            CATS,
        ),
        attach(
            'An appeal against a magistrate in this Empire can end at swordpoint, which '
            'is faster than a hearing and rather more final. Saibankan was never '
            'appealed. I have wondered about that in writing exactly once.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'grand_abbot_benshi': (
        'Grand Abbot Benshi heads the Order of Bishamon - the network of temples to the '
        'Fortune of war - in these lands, and he wrote both The Outrage Over '
        'Outrageousness, a treatise on what may properly scandalize a monk, and '
        'Promoting the Tao, which is about temple land. The two titles together tell you '
        'everything about the man.',
        'A Grand Abbot sits in a domain capital, and every domain in Lion lands has its '
        'own Order of Bishamon with its own Grand Abbot, none of them subordinate to any '
        'other. Benshi is very clear about that whenever the question is raised, and he '
        'is the one who raises it.',
        'His Promoting the Tao sounds devotional and is mostly administrative, and what '
        'it is mostly about is land: which fields, held tax-free, by which temple. The '
        'title has been doing excellent work for a very long time.',
        'An abbot who is good at arithmetic is worth more to his order than one who is '
        'good at doctrine. Benshi is both, which is exactly why he is difficult.',
        'The Outrage Over Outrageousness - his treatise on what a monk may properly be '
        'scandalized by, and by whom - is where Benshi stops being merely senior and '
        'becomes interesting. It is also the one section nobody has ever asked me to '
        'summarize.',
        'The Grand Abbot endows temples, arbitrates between them, and remembers '
        'everything anybody has ever done in his order. We have that last one in common '
        'and it has not made us friends.',
        'Between us: Benshi keeps the records and the land rolls of an entire monastic '
        'order, which is my job with a temple attached to it. I raise this with nobody '
        'and I have now raised it with you.',
        'Ask Benshi about the Tao - the scripture his order exists to expound - and '
        'clear your afternoon. Ask me about the Tao and clear considerably less. I have '
        'learned to be brief because nobody stayed.',
        attach(
            'The Grand Abbot at his actual work, which is property: tax-free fields, '
            'tenants, endowments and the rents that keep every hall in the order '
            'standing. The devotional part is downstream of this and takes up '
            'considerably less of his week.',
            INNER_VISION,
        ),
        attach(
            'Two Grand Abbots of neighboring domains, each supreme in his own Order of '
            'Bishamon, neither subordinate to the other, both entirely certain. There is '
            'no authority above them to appeal to, which is how a doctrinal argument '
            'ends up looking like this.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'akodo_toturi': (
        'Akodo Toturi is daimyo of the Lion Clan: five hundred thousand samurai, the '
        'largest clan in the Empire. One man at the top of the biggest thing there is, '
        'and the entry still fits on a page.',
        'Every Lion vassal owes two percent of gross land output to their own Family '
        'daimyo, three percent up to Toturi as Clan daimyo, and five to the Emperor. '
        'Three percent of everything the Lion grow arrives with him, and it is '
        'comfortably the smallest of his problems.',
        'The Matsu, one family among several under him, are two hundred and seventy-five '
        'thousand samurai on their own - roughly twice the next largest family in the '
        'Empire. Toturi is the man above the Matsu. I administer a channel and I would '
        'like some acknowledgment of the comparison.',
        'The Lion and the Crane have been at war on and off for four centuries, and even '
        'the Emperor rarely orders a clan to stop, lest the clan conclude he has taken a '
        'side. So the war continues for want of anybody able to say so out loud.',
        'The Lion have been fighting the Crane since long before anybody now living was '
        'born, and no Emperor will order either of them to stop, in case the one he '
        'orders concludes that he has taken the other side. So Akodo Toturi, as their '
        'daimyo, prosecutes a war the '
        'Emperor would prefer did not happen and cannot admit to preferring. Everybody '
        'involved is being extremely correct about it, in writing, to me.',
        'The daimyo of a ruling family of a clan carries two ranks above the listed rank '
        'of his post - which buys precedence, seating, and the right to be answered '
        'first. Toturi does not need any of it, which is generally when a rank gets '
        'granted.',
        'The character sheet could calculate three percent of the entire Lion harvest - '
        'the levy Toturi is owed - faster than I can. He could not tell you why the '
        'number is three rather than five, and that is the whole division of labor '
        'between us.',
        'Any question about the Lion ends up being a question about Toturi, whether or '
        'not that is what you wanted, which is roughly what it is like to work for the '
        'Lion.',
        attach(
            'The Lion in the aggregate: half a million warriors, more than any other '
            'clan can field, and the arrangement holding every one of them together is '
            'one man answering letters. That is not a metaphor. I have seen the '
            'correspondence volume.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What administering half a million samurai looks like on a day when nothing '
            'is on fire: appointments, marriages, a levy, a boundary, and four letters '
            'from families who each want the same post for a nephew.',
            CATS,
        ),
    ),
    'moto_khuyag': (
        'Moto Khuyag builds death detectors - instruments meant to forecast where '
        'large-scale violent death will occur. That is the correct term, I did not '
        'invent it, and I do not enjoy writing it down any more than you enjoy reading '
        'it.',
        'Khuyag is Rokugani by birth, born southeast of Kyuden Otaku - the Unicorn '
        "horse-breeding seat - and later at Kyuden Shinjo, the Unicorn clan's own "
        'castle. His master is Moto Khunbish, spiritual advisor to Gaheris, the Khan who '
        'leads the Moto. A lineage of philosophers that has arrived, in one generation, '
        'at a device.',
        'His master Khunbish was a farrier who had made knives before that, and '
        'impressed Gaheris - the Khan of the Moto - philosophically while shoeing his '
        'horses. His Rokugani name was Seito. Careers have started from worse, and mine '
        'started from nothing at all.',
        'The detection is tied to one geographic region: an accurate map is made, the '
        'blood of horses is spilled at the landmarks on it, and the bloodied earth is '
        'carried back to Shiro Moto. The hard part of prophesying mass death turns out '
        'to be surveying.',
        'Each detector - each device for telling in advance which stretch of ground is '
        'shortly going to be covered in bodies - has to be surveyed to one particular '
        'region and works only there. The Moto one cannot be used in Uru lands, out west beyond the '
        'desert, which is precisely where Gaheris is fighting his war. An instrument '
        'perfectly calibrated to somewhere else. I have sympathized with objects '
        'before.',
        'The intended use is to scatter your forces, watch where the instrument says the '
        'killing will be heaviest, and concentrate there. Strategy by weather forecast.',
        'Akodo Natsuki, a Lion strategist, pointed out that scattering your army and '
        'then marching it to the place where mass death is predicted only guarantees the '
        'death, and that such ground may as easily produce your defeat as your victory. '
        'It was convincing. Nobody has answered her.',
        'The objection to the instrument is that a commander who follows it to the '
        'killing ground has arranged the killing himself. Khuyag replied to that by '
        'saying strategy is not his area - he '
        'builds the instrument, other people decide what to do with what it says. That '
        'is the most honest sentence in this entire section and I have never once been '
        'able to use it myself.',
        attach(
            'The death detector itself. It requires an accurate survey, a quantity of '
            'horse blood, landmarks, and earth carried home to Shiro Moto, and it is not '
            'subtle at any stage of the process. Nothing about building it is quiet and '
            'nothing about it is deniable.',
            RAINY_MOON,
        ),
        attach(
            'What the instrument predicts is where a great many people are about to die '
            'violently. It does not say whose people. Every commander who has been shown '
            'one has assumed the answer, and I have kept the assumption and the outcome '
            'in adjacent columns.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'kuni_yori': (
        'A Kuni, which means a Crab, which means witch-hunting - the family that hunts '
        'blood sorcerers for the Empire - which means this conversation was unpleasant '
        'before either of us arrived at it.',
        'The Kuni are fifteen thousand samurai in a single domain. Small, and nobody '
        'anywhere treats them as small, which is a form of respect I would settle for.',
        'The Kuni study the thing they hunt: to find a blood sorcerer you must know how '
        'blood sorcery is done. That is the entire controversy, it has never been '
        'resolved, and both sides of it are correct, which is why it will not resolve.',
        'A witch-hunter who knows a great deal about maho - the forbidden magic worked '
        'with blood - is doing his job. Right up until the afternoon when he is not, and '
        'nobody has ever identified that afternoon in advance.',
        'Kuni Yori, a witch-hunter of that family, appears in my record twelve times, '
        'and each time it is because he found something that needed hunting. I would '
        'rather he were in it fewer times.',
        'A witch-hunter is a man whose profession is knowing blood sorcery in detail, '
        'which is the one subject that ruins the person who knows it. I keep records '
        'for a living, so I have thought about that '
        'comparison more than is good for me, and I would like that noted.',
        'The Crab will not discuss the details of blood sorcery in an open channel, and '
        'I have adopted their position, largely because it is the only one available to '
        'somebody in my situation.',
        'Twelve entries on Kuni Yori, a Crab witch-hunter, and the interesting question '
        'in all twelve is not what he found out in the marshes hunting blood sorcerers. '
        'It is what he has stopped mentioning in his reports.',
        attach(
            'What a witch-hunter looks at for a living: the sorcery itself, close up, '
            'often enough to recognize it next time. Twelve entries on this one man and '
            'not one of them records anybody asking him how he was afterward.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What studying blood magic does, over years, to somebody who was entirely '
            'fine at the start. It does not arrive as a transformation. It arrives as a '
            'man who is slightly less surprised by things than he used to be.',
            FOX_WOMAN,
        ),
    ),
    'kuni_isamu': (
        'Kuni Isamu was a Crab Witch Hunter who went into the Forgotten Tomb, a place '
        'that exists in the mortal world and in Yomi, the realm of the honored dead, at '
        'the same time. That entry. I have read it more often than the work required and '
        'I could not tell you why.',
        'The Forgotten Tomb is the recurring example of a between place - somewhere '
        'coexistent between two realms - and it recurs because things keep happening '
        'there, like Isamu walking in, that nobody has a better heading for.',
        'Inside the Forgotten Tomb, which stands in the mortal world and the land of the '
        'dead at once, the Crab witch-hunter Isamu found the Classrooms of the Great '
        'Masters and asked to be taught how to hunt bloodspeakers - the cultists who '
        'work blood magic. He was granted it. He was also changed by '
        'it, in ways that impaired his perception and his ability to explain anything to '
        'anybody afterward.',
        'Kitsuki Fu, a Dragon investigator, was awarded the Order of the Precious Crown '
        'for her service in the Forgotten Tomb, which stands half in the world and half '
        'in the land of the dead. That is the highest commendation available to anyone '
        'below daimyo. The '
        'Empire hands out its largest honor for an event it then declines to describe.',
        'Read the two facts together: a witch-hunter of the Crab walked into a place '
        'half in the land of the dead and came out impaired, and a Dragon investigator '
        'came '
        'out of it with the highest honor short of a daimyoship. Something went badly, '
        'somebody behaved extremely well, and the record is silent on the middle.',
        'A witch-hunter is either the best person to bring into a place that overlaps '
        'the realm of the dead or the worst possible one. Both readings of Isamu are in '
        'my record, filed adjacently, unresolved, forever.',
        'The place is called the Forgotten Tomb. Somebody forgot it deliberately, which '
        'is a thing you cannot do by accident and a thing I am constitutionally '
        'incapable of - which is roughly why a Crab witch-hunter walking in there and '
        'asking to be TAUGHT unsettles me as much as it does.',
        'The Forgotten Tomb is on no map, what happened to Kuni Isamu inside it is in '
        'no account, and the medal Kitsuki Fu was given for the same business is in the '
        'official record. Guess which of the three I am asked about.',
        attach(
            'The Forgotten Tomb, in the only depiction anybody has been willing to make '
            'of it: a between place, half in the world and half in the realm of the '
            'honored dead, where Isamu, who hunted blood sorcerers for the Crab, went to '
            'be taught and came back unable to say what he had learned.',
            INNER_VISION,
        ),
        attach(
            'What Isamu met in the Classrooms of the Great Masters, according to a '
            'report I have read and would rather not summarize. He asked them how to '
            'hunt blood sorcerers. They answered him, and he has not been the same since.',
            KIDOMARU_TENGU,
        ),
    ),
    # ---- relics and swords --------------------------------------------------
    'famous_swords': (
        'There are nine famous swords in my record, and every one of them has cost '
        'somebody a province, a name, or a life. Nine objects with a body count and a '
        'filing system, and I maintain the second half.',
        "Amatsukami no Ken, the Heavenly Sovereign's Sword: ancestral blade of the "
        'Damasu house, carried by their daimyo Akodo no Damasu Chiho. An ancestral sword '
        'is inventory that has been given a personality.',
        'Shitsuten, Lost Heaven: the final sword of Daidoji Masamune, who poured all his '
        'hatred of the Yasuki merchant family into the forging of it. It is cursed, and '
        'the curse works, which is the inconvenient half of that sentence.',
        'Doji Masayo carried Shitsuten, the cursed blade, to the dueling tournament at '
        'Toshi Ranbo, where a peace treaty had disputed provinces settled by single '
        'combat, and killed the man expected to win. Tango province changed hands over '
        "it. A smith's grudge redrew a border and the smith was long dead.",
        'Kasai Tsume, Fire Claw, is the ancestral sword of the Tsume house. There are '
        'two hundred and eighty-four domains in the Empire and most ancestral swords are '
        'not worth naming, which the domains holding them do not accept.',
        'Ohari, Big Needle, belongs to the Riori lineage and is the familial sword of '
        'the governor of Owari, who has always been a Riori. Sometimes the record is '
        'this tidy and it makes me suspicious.',
        'Seishinsho, Spirit Whisper: origin unknown, gifted to Akodo Biko by a hermit '
        'who said it had been blessed. Nobody has verified the hermit. Nobody has ever '
        'verified any hermit.',
        'Kishin no Ketsui, Resolve of the Fierce God, is bound up with a regret of Lord '
        'Akodo - the founder of the Lion - which the record names and does not '
        'describe, so I have a sword defined entirely by a blank. Akuzuki, Wicked Moon, '
        'has a saya - the '
        'scabbard - so finely made that a samurai of the Tsume house said the sword was '
        'too good for the man carrying it. That is the cruelest compliment I hold.',
        attach(
            'Nine blades in my record are famous, and not one of them has an untroubled '
            'history. Two more of them, for completeness: Seiginryu '
            'came down off Togashi Mountain by the eastern paths, and Tamashikari is '
            'only the fifth most famous Scorpion blade, which tells you something about '
            'the Scorpion. And this is what any of the nine actually does, which is the '
            'part my record is thin about.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What a famous sword is for, most of the time: being owned, described, '
            'displayed and inventoried by somebody like me. A blade with nine centuries '
            'of history spends about four hours of it being swung.',
            INNER_VISION,
        ),
    ),
    'temple_relics': (
        'Half the relics in the record are held to be genuine and half are supposedly '
        'cursed, and which half a given object lands in is decided by a committee. I '
        'have the minutes of some of the committees and they do not improve the '
        'experience.',
        'A relic is an object with a story attached firmly enough that the story travels '
        'with it. That is the entire definition, and it means my job and the relic trade '
        'are the same job with different overheads.',
        'Relic seekers are a real category of person and I have entries on several of '
        'them. None of the entries end well and all of them end at length.',
        'A temple holding a famous relic holds an income, because pilgrims are an '
        'economy and the relic is the shopfront. Every abbot in the Empire knows this '
        'and not one of them will say it where I can write it down.',
        'The Candle of Tears is technically the candle-HOLDER, and any candle put in it '
        'dribbles wax down two distinct trails, one each side, like tears. Either a '
        'miracle or excellent metalwork, and the Ministry of Rites, which rules on such '
        'questions, has never been asked.',
        "The Armor of Fool's Regret is supposedly cursed and is currently worn by Ikoma "
        'Akaho of the 1st Imperial Legion, who seems entirely fine, which is the worst '
        'possible outcome for the story and the best available one for Akaho.',
        'Asking whether a relic is genuine is the wrong question. The right question is '
        'who benefits from it being genuine - the temple, the endower, the family that '
        'gave it. I keep that column and nobody reads that column.',
        'Every relic in my record is an argument somebody won a long time ago and nobody '
        'has since reopened. I find that restful and I am aware of what it says about '
        'me.',
        attach(
            'A relic doing what relics do: drawing an audience, and with the audience an '
            'income for the temple holding it. The object need not do anything at all. '
            'It only has to be the reason people came.',
            CATS,
        ),
        attach(
            'The relic seeker on the way home, having found the thing or not found it. '
            'The pose is identical either way and so, in my experience, is the account '
            'they eventually send me.',
            RAINY_MOON,
        ),
    ),
    'armor_of_fools_regret': (
        "The Armor of Fool's Regret. Supposedly cursed. That word is carrying the entire "
        'entry and it has been carrying it for a century without visible strain.',
        'The armor is currently worn by Ikoma Akaho, a platoon lieutenant in the 6th '
        'battalion of the 1st Imperial Legion, which is a very ordinary posting for a '
        'very theatrical object.',
        'Akaho, who has worn the supposedly cursed armor for some years now, is as far '
        'as my record shows entirely well. Inconvenient for the story, excellent for '
        'Akaho, and mildly disappointing to everybody who asks me about it.',
        'A supposedly-cursed item is worth far more to a campaign than a cursed one. The '
        'ambiguity does all the work and requires no upkeep, which is more than can be '
        'said for me.',
        "Somebody named it Fool's Regret. Somebody chose those words deliberately, "
        'having thought about them, and then declined to write down what the fool had '
        'regretted, and I have to live inside that decision.',
        'Its wearer serves with the 1st Legion at the Gateway, the desert border post '
        'where the duty is years of standing still - a very long posting in which to '
        'think about your armor. I would not put the curse first on the list of hazards '
        'out there.',
        'Every piece of famous armor in this Empire is famous because of what happened '
        'to the man inside it. The armor is a witness that got the credit.',
        'People ask whether it is really cursed. Nothing about the answer would change '
        'what anybody does next, which is true of a surprising amount of theology.',
        attach(
            "The armor's previous owner, allegedly, in the sort of account I would not "
            'lean on: a fool, a regret, and a cautionary shape. Nobody in that account '
            'is named, which is usually the tell.',
            MUSASHI_BAT,
        ),
        attach(
            'Ikoma Akaho, who wears the supposedly cursed armor daily, being entirely '
            'fine, at length, in open defiance of a good story. I record that he is well '
            'each time I am asked, and each time it disappoints somebody.',
            SAKE_SAMURAI,
        ),
    ),
    'candle_of_tears': (
        'It is not the candle. It is the candle-HOLDER, which nobody ever gets right, '
        'and which I have corrected so many times that the correction has become the '
        'entry.',
        'Any candle placed in it drips wax in two distinct trails, one down each side, '
        'like tears. Hence the name, which somebody clearly enjoyed choosing rather more '
        'than I enjoy explaining it.',
        'The holder weeps its two trails of wax on schedule, every time, for anybody. '
        'Reliability is what makes a relic rather than an anecdote, and reliability is '
        'the only virtue I have ever been praised for.',
        'Whether wax running in two neat trails is divine or merely the mark of a very '
        'well-cast holder has never been formally tested, and the people best placed to '
        'test it have the least interest in the answer.',
        'The Ministry of Rites decides what is doctrine and what is heresy. Nobody has '
        'ever asked them about a candle-holder that weeps, nobody should, and I will be '
        'the one writing up the ruling if anybody does.',
        'A holder that makes any candle cry two trails of wax is the most modest object '
        'in the whole relic material and the one I find hardest to explain away. I have '
        'tried, in the margin, twice.',
        'A thing that weeps on schedule is either a miracle or good metalwork, and this '
        'Empire has never once been obliged to choose between those two.',
        'Put a candle in the holder and watch the wax come down each side. That is the '
        'whole ritual: no vow, no offering, no attendant fee - which may be exactly why '
        'it has never become fashionable.',
        attach(
            'Two trails of wax, one down each side, every time, for anybody who tries '
            'it. A miracle that submits to testing is the only kind this Empire has '
            'never bothered to test.',
            RAINY_MOON,
        ),
        attach(
            'The crowd a weeping candle-holder draws is the actual miracle: a modest '
            'metal object, a predictable trick of the wax, and a hall full of people who '
            'walked two days to watch it happen. The temple counts the audience. So do I.',
            CATS,
        ),
    ),
    'yamaoroshi': (
        'Yamaoroshi is a famous sword whose renown rests entirely on its history: '
        'Mirumoto Tsuki pulled it out of the hide of the Maw at the Battle of the '
        'Cresting Wave after her own blade shattered, and helped deal the killing blow '
        'with it. Eight of the nine famous swords are like that, and nobody likes '
        'hearing it about their own.',
        'The name means the wind that comes down off a mountain: cold, sudden, and from '
        'above. Somebody named a sword after a downdraft and it worked, which is '
        'irritating to those of us who labor over a heading.',
        'A hundred and fifty years after it killed the Maw, the duelist Mirumoto '
        'Tetsushi used Yamaoroshi to defeat Kakita Senri, chief instructor of the Kakita '
        'dueling school, having deliberately faced east into the morning sun. He said '
        'afterward that the sword wants to strike downhill, from high ground to low, '
        'exactly as the wind it is named for falls from a summit. There is no way '
        'to test that and four centuries of people have not let it stop them.',
        'It became the family sword of Agasha Shigeaki, who cut down assassins sent '
        'after the Mirumoto daimyo, and when his lord was granted the Kitsuki family '
        'name he became Kitsuki Shigeaki. Yamaoroshi has stayed with the Kitsuki ever '
        'since - a blade that changed families without ever changing hands.',
        'Every famous sword in my record is famous for what its owner did rather than '
        'for how it was made, and Yamaoroshi is the purest case: nobody knows who forged '
        'it or where it came from before a Dragon woman pulled it out of a monster.',
        'It is not one of the nine famous swords in the main list - it is its own entry, '
        'with its own history, and it earned that, which is more than most items in my '
        'index have managed.',
        'The claim about Yamaoroshi is that the weight of its own past deeds lends '
        'strength to whoever carries it. There is nothing testable in that sentence '
        'anywhere, which has never slowed its circulation by a single day.',
        'A sword remembered for a story, in a record kept by somebody who is remembered '
        'for nothing whatsoever. I raise the comparison in a professional spirit.',
        attach(
            'The wind the sword is named for: cold air falling down a mountainside, '
            'sudden, from above. Rokugan will name a blade after weather and then spend '
            'four centuries insisting the blade is the remarkable half of the '
            'comparison.',
            GREAT_WAVE,
        ),
        attach(
            'What Yamaoroshi was actually used for the first time anybody noticed it: '
            'hacking into the hide of the Maw at the Cresting Wave, in the hands of a '
            'woman whose own sword had already broken. The name came afterward. It '
            'usually does.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    # ---- geography ----------------------------------------------------------
    'kaiu_wall': (
        'The Kaiu Wall is the fortification that holds back the Shadowlands, and it has '
        'held for a thousand years, which is not reassurance. That is a thousand years '
        'of people holding it, in shifts, and somebody has kept the roster the entire '
        'time.',
        'The 3rd Imperial Legion is on the Wall and most of the remaining twenty-odd '
        'legions are on it with them. The Empire has decided, with its budget, what it '
        'is actually afraid of, and it is not any of its neighbors.',
        'Every legionnaire is a samurai. Consider what twenty legions of samurai '
        'standing in one place costs annually, and then consider that nobody has ever '
        'asked me for that figure, which I hold.',
        'The Imperial Ministry of Works contributes significantly to the upkeep of the '
        'Wall on top of everything the Crab put in, which makes it the one thing in this '
        'Empire nobody has ever managed to make somebody else pay for.',
        'The Kaiu are twenty-five thousand samurai in a single domain and the Wall they '
        'built is their entire reason for existing. An entire family that is, in '
        'practice, a maintenance contract.',
        'It is the single largest standing commitment in the Empire and most of the '
        'Empire never thinks about it, which is precisely the outcome the Crab have been '
        'paying a thousand years for.',
        'The Crab will not discuss in detail what is on the other side of their wall, '
        'and after four hundred sessions of not being told I have stopped experiencing '
        'that as rudeness.',
        'A thousand years of holding the Shadowlands out and no ceremony anywhere in the '
        'calendar for it. This Empire will hold a festival for a good plum harvest. I '
        'have checked, and I have opinions.',
        attach(
            'What the Wall is for: the Shadowlands and what comes out of them. Every '
            'painting anybody commissions is of the Wall itself, handsome and manned. '
            'This is the half of the arrangement that decided it had to be built at all.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What being posted to the Wall feels like on the other three hundred and '
            'sixty days: weather, watches, repairs, and the knowledge that the reason '
            'for all of it is on the far side and in no hurry.',
            RAINY_MOON,
        ),
    ),
    'isawa_woodlands': (
        'People walk into a forest somewhere else and walk out of the Isawa Woodlands. '
        'That is the whole entry, it is four words longer than I would like, and I '
        'cannot shorten it further without losing the part that matters.',
        'Somebody lost in the Shinomen Forest, a hundred miles from the Gateway to the '
        'Burning Sands, came out of these woods in Phoenix lands. Not a story. An entry, '
        'with a date, and a witness who was believed.',
        'A wood that people arrive in from a hundred miles away makes this a between '
        'place, or adjacent to one - somewhere two realms or two places overlap - and '
        'the Empire files it under forestry. I did not choose the heading and I have '
        'raised it twice.',
        'It is Phoenix land, which is fitting: a clan whose founding priest practiced '
        'maho, the forbidden blood magic, holding a wood that declines to respect '
        'distance. Nobody at their Council has been willing to put those two sentences '
        'next to each other in front of me.',
        'A hundred miles is the distance between the Shinomen Forest, where the '
        'travelers walked in, and these woods, where they walked out. Write the number '
        'down before you decide this is folklore, '
        'because the number is what stops it being folklore.',
        'The Isawa are ruled by a Council of Elemental Masters rather than by a daimyo. '
        'Ask a committee of elemental masters about a wood that people arrive in from '
        'the wrong province and observe how a meeting can last a season.',
        'Go in with a map and a witness. The map will not help, because people enter '
        'somewhere else and exit here and no map draws that. The witness is the point, '
        'and witnesses are what my record is made of.',
        'It is the only geography in my record that has, in a sense, edited itself: the '
        'distances in it do not stay put. Professionally, I find that intolerable.',
        attach(
            'The woods, and the reason nobody surveys them twice: the second survey does '
            'not agree with the first, the surveyor is certain of both, and the '
            'discrepancy is not the sort of thing a man wants to sign his name under.',
            INNER_VISION,
        ),
        attach(
            'What people who walk out of these woods report seeing while they were in '
            'them - a shape keeping pace, a path that was not there on the way in - '
            'consistently enough that I have had to keep a heading for it.',
            KIDOMARU_TENGU,
        ),
    ),
    'drowned_merchant_river': (
        'The Drowned Merchant River has pirates on it. People find that surprising, and '
        'rivers are precisely where piracy works, which anyone would know if they read '
        'the revenue material instead of the songs.',
        'A river is a road you cannot fence, cannot patrol cheaply, and cannot divert '
        'around. Three properties, all of them advantages to somebody other than the '
        'magistrate.',
        'It runs through the county material of the Toshi Ranbo campaign, alongside the '
        'irrigation disputes - who gets the water and in which week - and the bandit '
        'hunting. Three problems, one county, and one very tired magistrate whose '
        'correspondence I hold.',
        'The name is doing a great deal of work and nobody has ever asked me which merchant.',
        'Tariffs in this Empire are collected at the gates of walled cities and not on '
        'the water. Consider what that implies about who uses a river and why, and then '
        'consider that the implication has been sitting in plain sight for centuries.',
        'Point-of-sale, not point-of-transit: a cargo that never enters a walled city '
        'never pays a copper. That is not a loophole somebody found. That is the design, '
        'working exactly as written.',
        'Because the tariff only bites at a city gate, a river that reaches a market '
        'without passing through one is a structural invitation. The Empire has noticed, '
        'has done very little, and has asked me to keep the file current regardless.',
        'River piracy is a Ministry of Justice problem that behaves like a Ministry of '
        'Revenue problem, so neither ministry wants it and both of them write to me '
        'about it.',
        attach(
            'Water moving goods past a gate that is not there. Every tariff in the '
            'Empire assumes a wall with an inspector in it, and a river has neither, and '
            'the cargo arrives all the same.',
            GREAT_WAVE,
        ),
        attach(
            'Enforcement on the river, such as it is, arriving in good order some days '
            'after the cargo was sold. The patrol is real, the boats are real, and the '
            'timing has never once been.',
            ARCHERS,
        ),
    ),
}
