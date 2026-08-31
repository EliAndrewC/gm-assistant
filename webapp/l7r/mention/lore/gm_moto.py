"""The Moto, the Unicorn, and the gaijin west. GM Assistant only.

Fourteen categories the GM approved in message 2, and they must resolve BEFORE
the Great Clan routing added in message 3 - `Moto` is a Unicorn family, so
family-to-clan routing would swallow this entire file. See `topics.py`.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing any line here. This file scored the
worst of the six in the 2026-08-31 tone audit - **2.9%**, with eight of its
fourteen categories containing no first-person word at all - so it was rewritten
whole rather than patched.

CONTEXT, the second bar, added later the same day. A context audit found **80 of
these 140 replies** unintelligible to a player who had not read the GM's notes,
and named the mechanism exactly: **openers that carry the frame and follow-ons
that assume it.** Most categories had one reply doing all the defining and eight
riding on it with "it", "that place", "the same greeting", "the work". Four
referents accounted for most of the damage and now carry a one-clause gloss
wherever they appear: **khan** (a Moto clan leader), the **Shinjo** and **Otaku**
(Unicorn families), **Gaheris** and his war in Uru lands, and the **Dark Moto**
story. `burning_sands` also carried a cross-reference - *"See the Dark Moto"* -
to a reply the player can never be sent; a category may never point at another
category, because only one reply is ever delivered.

Two duplications the tone audit caught and its rewrite removed, worth knowing
about before adding a line: `vindicator_moto` used to close on "Buy a Vindicator
a drink and do not ask twice", which also appeared verbatim in `gm_people`
twice; and `unicorn_history` shared five of its eight text lines with
`gm_clans/clan_unicorn`. Reuse across categories thins an already small stock of
good jokes - if a line would work in two places, it belongs in the one where the
player is more likely to be standing.
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
    RAINY_MOON,
    attach,
)

MOTO: dict[str, tuple[str, ...]] = {
    'the_moto': (
        'The Moto are a family of the Unicorn clan: herders, mostly nomadic, spread '
        'across land in the far west that is semi-arid and about one percent farmable. '
        'Every single difficulty in this file descends from that one percent.',
        'Imperial taxes are assessed on agricultural yield, and the Moto grow almost '
        'nothing, so the Moto pay almost nothing. Everyone resents it and nobody can '
        'fix it. A tax code defeated by grass.',
        'Their population is thin because their land is dry: one percent of it will '
        'grow food, and grass feeds animals rather than families. You cannot graze a '
        'city. I have watched three separate administrators discover that sentence in '
        'my presence.',
        'On paper the Moto tribes are ruled by local governors. The Moto call those men '
        'khans, which is their own word for the leader of a clan. Two words for one '
        'office, chosen by two peoples who each believe the other is being humored.',
        'Nobody has an accurate count of the Moto tribes - not even the Shinjo, who are '
        'the Unicorn family nominally in charge of them. Not knowing how many '
        'subordinate units you have is administratively my least favorite fact in this '
        'entire record, and I have held it for years.',
        'They are Unicorn. They are also, in every practical sense, a separate '
        'civilization living inside the Empire, and the Empire has decided not to '
        'examine that too closely.',
        'Every Moto entry I hold needs three qualifiers: which tribe, which khan, and '
        'which of the two languages the conversation actually happened in. Nobody has '
        'ever supplied any of the three unprompted.',
        'The modern Moto are bringing back what they call the old ways - the '
        'pre-Imperial custom and worship they carried through their centuries outside '
        'the Empire. That phrase ought to worry the Ministry of Rites, which decides '
        'what is orthodox, considerably more than it currently does. I have said so in '
        'a document nobody has opened.',
        attach(
            'Moto land, which is semi-arid grazing country and about one percent '
            'farmable. Note the total absence of anything an Imperial official could '
            'assess, levy or file a return on. The tax code has no opinion about grass.',
            RAINY_MOON,
        ),
        attach(
            'A Moto negotiation reaching its customary stage. Among the Moto an '
            'exchange of insults is a greeting and dismounting is the escalation, so '
            'this is not the negotiation failing. This is a step in it, and I am '
            'expected to minute the step.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_etiquette': (
        'Moto etiquette is not the absence of etiquette. It is a different etiquette, '
        'it is extremely precise, and the people most offended by it have never once '
        'asked what its rules actually are.',
        'The pattern runs: a statement with a demeaning implication, an immediate '
        'refutation, and an offer to get down off the horses and settle it like men. '
        'Three movements, reliably, like a tea ceremony with worse outcomes.',
        'Among the Moto an insult is an opening, not a challenge, so the correct reply '
        'to "what did you just say to me" is not an apology. It is to ask whether their '
        'hearing is failing and to offer to speak up. That is warmth. It does not look '
        'like warmth.',
        'The insult and the refutation are not a fight starting. They are a greeting. '
        'Rokugani guests survive it by accident roughly half the time, and I write up '
        'the other half.',
        'Getting off the horse is the escalation. Everything said on horseback is still '
        'conversation, however it sounds - a rule of enormous practical importance '
        'which appears in no courtier training anywhere in this Empire.',
        'A Rokugani courtier hears an insult where a Moto is offering friendliness, and '
        'then I am the one who has to write down what happened next, in order, with '
        'names.',
        'A visiting Rokugani rolling to navigate Moto company does it at half his usual '
        'ability. That is not a penalty for being rude. It is a penalty for being '
        'foreign, which this Empire usually prefers to apply in the other direction.',
        'They are not being difficult. You are being quiet, which in their reading is '
        'considerably worse than being rude, and which is the only social advantage I '
        'have ever held over anybody.',
        attach(
            'Two Moto greeting one another cordially. The insult, the refutation, and '
            'the dismounting are the greeting, in that order, and nobody present '
            'considers any of it a quarrel. I file it under correspondence.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'A Rokugani courtier three minutes into that same greeting, having taken '
            'the traded insults for a duel challenge. He is not in danger. He does not '
            'know that. Nobody will tell him and I am four hundred miles away.',
            RAINY_MOON,
        ),
    ),
    'moto_tribal_structure': (
        'Extended families gather into what the Moto call a clan, led by a khan, and '
        'the Empire calls those clans "tribes" because the word clan was already spoken '
        'for by the seven Great Clans. An entire vocabulary decided by a scheduling '
        'conflict.',
        'They call themselves clans. We call them tribes. Both parties know, both '
        'parties are being polite about it, and I have to choose one word per document '
        'and live with the choice.',
        'A Moto clan runs to the low thousands - smaller than a Rokugani county and '
        'covering vastly more ground. Nothing in Imperial administration has a category '
        'for that, so it gets filed under county, incorrectly, by me.',
        'The khan - the leader of one Moto clan - settles disputes, metes out justice '
        'within it, and leads it in war. Three jobs, one man, no ministry, no clerks. I '
        'have read that sentence many times and my feelings about it have not settled.',
        'The Empire runs a Ministry of Justice for its courts and jails and a Ministry '
        'of Retainers to pay and promote its samurai. The Moto have neither. They have '
        'a khan and whoever he chooses to listen to, which is either a catastrophe or '
        'an efficiency depending on the khan, and my record contains both.',
        'One man doing justice, war and every dispute in a clan of a few thousand, with '
        'no bureaucracy underneath him, works. That is the part that unsettles Rokugani '
        'administrators, I include myself, and I would rather not have had to include '
        'myself.',
        'Nobody has an accurate count of the Moto tribes, including the Shinjo, the '
        'Unicorn family who are supposed to administer them. I have made my peace with '
        'that and it took years off me.',
        'Ask which tribe before you ask anything else. It is the only unit that '
        'reliably means anything out there, and the Empire has spent two centuries '
        'asking which province instead and writing down the answers.',
        attach(
            'The unit that matters out there is the clan under its khan - not a '
            'province, not a county, not anything with a boundary you could draw. It '
            'moves, it fights and it pays no tax, and it fits on no form I possess.',
            CATS,
        ),
        attach(
            'A dispute the khan is about to settle, personally, in the open, in front '
            'of everybody it concerns. Note the absence of a hearing, a docket, a '
            'confirmation traveling upward, or anybody at all taking notes.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_language': (
        'The Moto speak a language of their own, and that single fact has caused more '
        'theological confusion in this record than anything else in it. Not heresy. '
        'Translation.',
        'For decades everyone assumed Enma was simply the Moto word for Emma-O, the '
        'Fortune of death. It is not - Enma is a different god who guards the gates of '
        'hell, and the two names merely sound alike. Decades of scholarship, and the '
        'error was that nobody asked.',
        'The eastern Moto are mostly bilingual, because Rokugani has been the official '
        'language for centuries and the successful ones needed it. Bilingualism runs '
        'one direction here, and the Empire has never once noticed which direction.',
        'Speaking both languages, among the eastern Moto, belongs to the families who '
        'prospered - which tells you plainly what became of the others. The record is '
        'silent about them in a way that is itself an entry.',
        'The same trap waits with every foreign pantheon. A traveler from Medin al '
        'Salaat, a gaijin city out west, names their god of love; a samurai hears '
        'Benten, who is ours, and writes down Benten; and I inherit the note.',
        'Nobody has ever gone back to check one of those identifications - a whole '
        'foreign pantheon mapped onto ours by travelers who were tired, in a hurry, and '
        'confident. Not one entry has been revisited since, and I have suggested it '
        'twice.',
        'Every misunderstanding in the Moto material is a translation before it is a '
        'heresy. I would put that sentence on a wall if anybody would let me have a '
        'wall.',
        'If a Moto tells you something impossible, ask which word they used, and then '
        'ask what it means to them, in their language, before you write anything down. '
        'That has resolved more of my corrections than any quantity of theology.',
        attach(
            'Two languages meeting, which out here means an insult, a refutation, and '
            'both parties believing they were understood. It usually goes rather better '
            'than it looks, and my file is made entirely of the exceptions.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'What a mistranslated god looks like some decades on: a foreign deity '
            'written into our records under a Rokugani name by somebody in a hurry, now '
            'settled in, with worshippers of its own and a shape nobody chose.',
            FOX_WOMAN,
        ),
    ),
    'moto_rank': (
        'Every office in the Empire sits somewhere on a ladder of fifteen ranks, the '
        'Emperor being the fifteenth. The Moto are on it like everybody else, and then '
        'come the adjustments, which is where every single person gets it wrong and '
        'where I earn what I am not paid.',
        'The published table is only the start. Anyone above Governor who comes from '
        'the ruling House of a Family sits one rank above what the table says; from a '
        "Clan's ruling Family, two. A system of exceptions wearing a system of ranks "
        'over it.',
        'A worked example: Ikoma Yuan is Deputy Minister of War for the Ikoma lands and '
        'sits at the tenth rank, because that ministry also oversees the vassal '
        'families - the lesser houses sworn to the Ikoma. Try deriving that from the '
        'table alone. I did, once, incorrectly, in ink.',
        'A county magistrate is of the fifth rank. The Emperor is the fifteenth and the '
        'only one. Everything interesting happens in the nine ranks between them and '
        'nobody has ever asked me about the middle.',
        'The Moto map their khans - the leaders of their clans - onto that fifteen-rung '
        'Imperial ladder, and the fit is poor. This suits both sides perfectly and '
        'suits me not at all, because I am the one writing the letters.',
        'Moto Gaheris, who leads the Moto, is a Family daimyo by the reckoning of the '
        'Empire and khan of khans by the reckoning of his own people. Those are not the '
        'same office and they do not confer the same things. He uses whichever is more '
        'convenient and I record which he was using at the time.',
        'Rank is a measure of how much trouble it is to ignore you. Among the Moto that '
        'calculation runs on a different denominator entirely, and by either '
        'denominator I round to zero.',
        "Get a Moto's rank wrong in writing and you have created a diplomatic incident "
        'with a brush. I have done it. It took four months to settle and I was not the '
        'one thanked when it did.',
        attach(
            'Rank being established the direct way, which out here is a legitimate '
            'procedure rather than a breakdown of one. Faster than the correspondence '
            'and considerably harder to file.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The ceremonial way of establishing the same thing - who outranks whom, '
            'settled by precedence, seating and an exchange of gifts. It takes three '
            'days instead of three minutes and it produces documents, which is the only '
            'reason I prefer it.',
            ARCHERS,
        ),
    ),
    'moto_gaheris': (
        'Moto Gaheris is daimyo of the Moto family. His own people call him the khan of '
        'khans - the leader of every Moto clan leader - a title the Empire has never '
        'formally recognized and has never once challenged. That combination is the '
        'whole of Imperial policy toward the man.',
        'Gaheris carries four swords, one dedicated to each of the four Gods of Death '
        'in Moto teaching, and which one he draws says what kind of killing this is: '
        'Bloodstorm into an expected battle, Lamentation when ambushed, Lightning in '
        'single combat, Retirement for executions. A man who has pre-decided every '
        'killing he will ever do.',
        'He chose which sword for which killing at Bodi Kaikhan, the pilgrimage ground '
        'where the Moto go to speak with their ancestors, and swore a covenant there. '
        'That is not flourish. It means a man has thought harder about the categories '
        'of killing than I have thought about anything.',
        'Gaheris is waging a military campaign in Uru lands, which lie out west beyond '
        'the desert and beyond the Empire entirely, and everything else in the Moto '
        'material is downstream of that war. Every entry I have opened this year '
        'eventually arrives back at it.',
        "Moto Khunbish is spiritual advisor to Gaheris. Moto Khuyag is Khunbish's "
        'student, and Khuyag builds detectors meant to sense a death before it is '
        'reported. A lineage of advisors ending in a device, which is either the '
        'beginning or the end of a philosophy.',
        'A Rokugani abbot has publicly declared the war in Uru lands blessed, which '
        'means the Empire has now taken a formal position on a campaign it has never '
        'formally acknowledged is being fought. Both documents came to me.',
        'Khunbish met Gaheris years ago at Kyuden Shinjo, the Unicorn seat, as a farrier '
        'assigned to the Moto guests, and impressed him philosophically while shoeing '
        'their horses. Somebody was promoted out of a stable for talking well. I shoe '
        'nothing and talk constantly.',
        'A man who dedicates a separate sword to executions - as Gaheris has, out of '
        'four - has considered executions rather more carefully than you have, and a '
        'great deal more carefully than the people currently describing him as a '
        'barbarian.',
        attach(
            'A fight nobody will write down. Four years of dispatches out of the Uru '
            "campaign, where the Khan of the Moto is fighting a war beyond the Empire's "
            'border, and not one Imperial record of any of it. I have asked. Twice.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            "Gaheris' war, from the perspective of Uru lands, where it is not called a "
            'campaign and where the people writing about it are writing in a language '
            'nobody in this Empire has offered to read.',
            GREAT_WAVE,
        ),
    ),
    'the_yassa': (
        'The Yassa is Moto law. There is a written Yassa and there is what is actually '
        'done, and the gap between the two is where every interesting case lives and '
        'where all of my footnotes live with them.',
        'It is not the Emerald Charter - the Imperial law that governs the rest of us - '
        'and it does not pretend to be. The Yassa answers to a khan, the leader of a '
        'clan, rather than to a ministry, which means it can be wrong quickly instead '
        'of wrong slowly.',
        'Rokugani magistrates find the Yassa arbitrary. The Moto find Rokugani law '
        'slow. Both assessments are entirely correct and neither party has ever '
        "conceded a word of the other's.",
        'A law that fits on a few pages and is enforced by a man who knows everyone '
        'involved works far better than it has any right to, which is a deeply '
        'inconvenient thing for a record-keeper to have observed and written down.',
        'It covers theft, horses, water, and insult, in roughly that order of '
        'seriousness. Consider what it says about a place that water outranks insult '
        'and horses outrank water.',
        'Horse theft is a capital matter, because on dry grazing land a stolen horse is '
        'not lost property - it is a man left on foot, days from water, with his herd '
        'unattended. So it is treated as nearer to attempted murder, and visitors learn '
        'this in exactly one way.',
        'The Empire has never formally tested whether the Yassa conflicts with Imperial '
        'law. Nobody wants that answer written down, and I am the one it would be '
        'written down by.',
        'Every Yassa ruling in this record is really a fact about which khan made it, '
        'because each khan is judge in his own clan and there is nobody above him to '
        'appeal to. The text is almost incidental, which no student of Imperial law is '
        'prepared to hear from me.',
        attach(
            'A Yassa judgment being handed down: summary, in the open, enforced on the '
            'spot by the man who gave it. It is brief. The brevity is the feature and '
            'not the flaw, and I have stopped arguing about that.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'Here is the appeal process against a Yassa ruling, in full: the khan '
            'decided it, the khan is the law among his own people, and there is no '
            'higher court anywhere to write to. I have drafted the letter regardless. '
            'Twice. It has nowhere to go.',
            RAINY_MOON,
        ),
    ),
    'vindicator_moto': (
        'The Vindicator Clan are the southernmost Moto tribe, on the western side of '
        'the Twilight Mountains, and their business is whatever wanders out of the '
        'Shadowlands. A whole tribe whose address is a job description.',
        'Their doctrine holds that an oni - a demon out of the Shadowlands - is not '
        'evil in the mortal realm but maddened, like a rabid animal that has to be put '
        'down. A theology of pity, arrived at by the people with the most reason to '
        'hate.',
        'It follows from that doctrine that killing such a creature is a MERCY: it '
        'protects the people the thing would have killed and it returns the demon to '
        'the realm it actually belongs in. I have read a great deal of doctrine and '
        'very little of it does that much work in one sentence.',
        'Their hatred of all things Shadowlands is well known, which is precisely why '
        'their unusual line on demons - that killing one is mercy rather than justice - '
        'is treated with deference even by those who consider it foolish. Credentials, '
        'in this Empire, are mostly a matter of what you have buried.',
        'The Ministry of Rites has ruled it heretical to say that demons are "not '
        'malicious". The Vindicator therefore say something carefully adjacent - that a '
        'creature in the wrong realm is maddened rather than wicked - and I would like '
        'it noted that theological caution is a skill and that they have it.',
        'They are the ones who turned away the corrupted Moto who tried to come home: '
        'kinsmen who had crossed into the Shadowlands in desperation, been changed '
        'there, and walked back to the gate. The same tribe that preaches mercy toward '
        'demons applied none of it at their own gate. Doctrine is easiest at a '
        'distance.',
        'A tribe defined by what it stands between - the Shadowlands on one side and '
        'the Empire on the other. There are several such postings in this Empire, none '
        'of them cheerful, and every one of them is asked to explain itself by people '
        'who have never stood anywhere.',
        'They will talk about the work - the patrols, the ambushes, the disposal, the '
        'same again next week. They will not talk about the kinsmen who came back '
        'changed and were refused. I hold both halves and am only ever asked for the '
        'first.',
        attach(
            'What the Vindicator actually do: patrol the border of the Shadowlands, '
            'kill what crosses it, dispose of the remains, and go out again. Less '
            'heroic than the songs and considerably more repetitive, which is true of '
            'most work that keeps anybody alive.',
            KIDOMARU_TENGU,
        ),
        attach(
            'The evening after. A tribe that has argued its way to calling the killing '
            'a mercy - a maddened thing returned to where it belongs - still drinks '
            'afterward like men who have done something else entirely. I record what '
            'they say, not what they mean.',
            RAINY_MOON,
        ),
    ),
    'dark_moto': (
        'The Dark Moto. Yes. Be careful where you ask that, and be aware that asking it '
        'here means I have written down that you asked.',
        'When the Unicorn made their long journey outside the Empire, some went south - '
        'the Moto especially, whose ancestral homelands lie southwest of the gaijin '
        'city of Medin al Salaat, according to the library at Chai Sedo, which is a '
        'monastery here and the most-cited shelf in my record. Somewhere southwest of a '
        'foreign city is not a location. It is a direction with a story attached.',
        'This is the story that gives them the name. A large contingent of Moto ran out '
        'of water on that crossing and, in desperation, went into the Shadowlands '
        'instead of dying in the sand. What lives there changed them. The whole tragedy '
        'turns on a quartermaster.',
        'Some of the Moto who were corrupted in the Shadowlands tried to come home '
        'anyway. Their own kinsmen met them at the border and turned them away, because '
        'what came back was not entirely what had left. That is the sentence in this '
        'record I would most like never to have had to write.',
        'The story is short: a desert crossing, no water, a decision to enter the '
        'Shadowlands, and kinsmen refused at the gate afterward. The Moto take a whole '
        'evening over it and they are right to, and the Empire has the three-sentence '
        'version in writing, which is how these things get settled.',
        'Water is the constraint on any desert crossing - not the distance, but the '
        'RATE at which a well refills. Get that arithmetic wrong with enough people and '
        'they will go anywhere rather than stay still. An entire people lost to a rate '
        'of flow.',
        'The Vindicator, the Moto tribe posted on the edge of the Shadowlands, are the '
        'ones who deal with what came of it, and they are also the ones who turned the '
        'corrupted away. That is why their doctrine about mercy reads the way it does. '
        'Mercy is easier to preach from further off.',
        'The Empire treats the whole business - the crossing, the corruption, the '
        'refusal at the gate - as folklore. The Moto do not. When those two positions '
        'differ, my experience is that the Empire is the one that has not checked.',
        attach(
            'The crossing that started it: a column of Moto, out of water, with the '
            'Shadowlands on one side and the sand on the other. The problem was never '
            'the sand. The problem was the rate at which the wells came back.',
            GREAT_WAVE,
        ),
        attach(
            'What walked back to the border afterward - kinsmen changed by the '
            'Shadowlands - and was not let in by its own family. The Empire files this '
            'under folklore, which is a decision it reached without going to look.',
            KIDOMARU_TENGU,
        ),
    ),
    'horse_culture': (
        'A horse means two completely different economies depending on who owns it: the '
        'Rokugani way, which is stabling and grain, and the Moto way, which is a herd '
        'loose on grass. People conflate the two constantly, in my hearing, at length, '
        'with confidence.',
        'Keeping a horse the Rokugani way means grain at four to five koku a year and '
        'two to four acres of grazing that would otherwise be growing food for people. '
        'That second cost is the real one and it has never appeared in a single ledger '
        'I have been shown.',
        'The land a horse eats is the true price of a Rokugani horse, and the reason a '
        "bushi's mount is a statement rather than a conveyance. Nobody has ever ridden "
        'an argument about land use, and yet.',
        'A Moto horse costs a few bu - a silver coin or two - where a Rokugani mount '
        'costs a small fortune in grain and grazing, and a single Moto family keeps '
        'dozens of them alongside their sheep at almost no effort. The same animal, '
        'priced an order of magnitude apart by two civilizations, each certain the '
        'other is a fool.',
        'The catch with running horses loose on open grass is pedigree: you have no '
        'idea which stallion fathered which colt. The Otaku, the Unicorn family who '
        "breed the Empire's finest horses, find this appalling. They are correct. The "
        'Moto have never once cared.',
        'Traders buy cheap in Moto lands and sell dear in the Empire, and the reason it '
        'works at all is that the goods walk themselves to market. Horses are '
        'self-transporting. I am still asked about the caravan costs.',
        'The horse trade BARELY works: months of driving the animals east eats most of '
        'the margin, and a bad stretch of road eats the rest. That detail is left out '
        'of every story about a wealthy horse trader, and it is why there are so few of '
        'them.',
        'An active horse eats twenty pounds of hay a day. Everything else about cavalry '
        'in this Empire follows from that one number, including several campaigns that '
        'ended because nobody thought to ask me to multiply it.',
        attach(
            'The expensive way to keep a horse: stabled, fed on grain, standing on land '
            'that could have grown food for a family. It costs more per year than most '
            'samurai are paid, and it is the version that gets painted.',
            ARCHERS,
        ),
        attach(
            'The cheap way, which is also most of the horses in the world: loose on '
            'open grass, herded rather than stabled, eating nothing anybody had to grow. '
            'It has never been painted by anyone, and it is the reason the Moto can '
            'field cavalry the Empire cannot afford.',
            RAINY_MOON,
        ),
    ),
    'unicorn_history': (
        'The Unicorn clan left the Empire, spent centuries outside it, and came back, '
        'and the Empire has never entirely forgiven either decision. Two hundred years '
        'of grievance, and it is the RETURN that offends people most.',
        'They were called the Ki-Rin when they left. They went out past the Burning '
        'Sands - the desert on the western frontier - and came home with horses, '
        'foreign habits and the Moto, and the Empire has spent every year since '
        'deciding which of those three it minds least.',
        'Their return displaced Mirumoto samurai, the Dragon clan swordsmen who had '
        'been living on that land in the meantime, which is why three of the six major '
        'lineages of the Ryusei domain are descended from families evicted by it. That '
        'is what "the return of the Unicorn" means in practice: not a parade, a land '
        'dispute.',
        'That land dispute - the returning Unicorn against the Dragon families already '
        'settled there - has lasted generations and been conducted almost entirely in '
        'documents, most of which have passed through my hands and none of which have '
        'settled anything.',
        'A clan that has seen the outside is a clan the rest of the Empire cannot quite '
        'trust, and they know it, and they long ago stopped bothering to mind.',
        'The Unicorn peg one koku to one ton of hay, where the Emperor pegs it to forty '
        'gallons of rice. An entire worldview smuggled into a unit of account, which is '
        'where worldviews usually hide.',
        'One percent of Unicorn farmland is legally set aside for hay, and the lands of '
        'the Otaku - the Unicorn family who breed the horses - stockpile beyond that by '
        'law. A clan that legislates its own fodder is a clan that has been hungry '
        'somewhere I have not.',
        'Otaku lands produce about fifteen thousand tons of hay a year from the '
        'mandated fields alone, which is enough to keep several thousand horses through '
        'a winter, plus a few thousand tons more besides. I hold that number because '
        'somebody must, and nobody has ever asked me for it.',
        attach(
            'The return of the Unicorn as the Unicorn remember it: a homecoming, after '
            'centuries away, to land that had been theirs when they left. Two hundred '
            'years on they are still the only party to it who use that word.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The same event as the Mirumoto remember it - the Dragon samurai who were '
            'farming that ground when the Unicorn came back and wanted it. Same date, '
            'same event, two entries in my hand that do not agree on a single noun.',
            RAINY_MOON,
        ),
    ),
    'medin_al_salaat': (
        'Medin al Salaat is a gaijin city - foreign, west, beyond the Empire entirely - '
        'and it is the reason half of this record has footnotes attached to it in a '
        'smaller hand.',
        'The Moto ancestral homelands are said to lie southwest of that city, according '
        'to the library at Chai Sedo, a monastery in these lands. It is the '
        'single most-cited shelf in my whole record and the one nobody has ever offered '
        'to go and check.',
        'Kitsuki Tetsu, a Dragon investigator, considered swearing a vow of creation - '
        'a binding promise to build a thing, enforced by a god - to Jikoju, the Fortune '
        'of civilization: a temple built and staffed in that foreign city, civilization '
        'carried there as the Great Ancestors are said to have carried it to the '
        'warlords of old. A sentiment with a construction schedule attached.',
        'A vow of creation binds you to build the thing whatever happens next. Sworn '
        'over a foreign city, it binds you even if the army that made building there '
        'sensible - which is to say the Moto campaign in the west - stops winning. '
        'Kitsuki Tetsu has considered this at length, out loud, to me.',
        'There is a dream quest associated with the place: a pilgrimage undertaken '
        'asleep, in which what is seen is treated as an instruction. I have the '
        'account. I do not enjoy having the account, and nobody offered me the option '
        'of not having it.',
        'Foreign gods get translated into Rokugani ones on contact, usually wrongly, '
        'occasionally catastrophically, and always by somebody who was quite certain at '
        'the time and is no longer available to ask.',
        'A samurai hears a foreigner name their god of love, writes down Benten - who '
        'is the Fortune of love here - and is usually correct, and has still filed a '
        'foreign god under a Rokugani name without asking anybody. That is the Empire '
        'abroad, in one sentence.',
        'It is a real city with real politics and records of its own, older than most '
        'of ours, and the Empire files the entire thing under "abroad". I am obliged to '
        'use the same heading and I resent every use of it.',
        attach(
            'The approach to the city. Everything about it is foreign except the '
            'arithmetic - the water, the distance, the rate at which a well refills - '
            'which is identical everywhere and is the only part of any of this I trust.',
            GREAT_WAVE,
        ),
        attach(
            'A gaijin god as a samurai understands it: a foreign deity written into our '
            'records under the name of whichever of our Fortunes seemed closest, which '
            'is to say a god wearing a name that was already taken.',
            FOX_WOMAN,
        ),
    ),
    'burning_sands': (
        'The Burning Sands are the desert on the western frontier, with the 1st '
        'Imperial Legion guarding the Gateway into it and having done so for a very '
        'long time. Centuries of duty at a door, which is a posting I feel qualified to '
        'comment on.',
        'The constraint out there is water, and specifically the RATE: a well may hold '
        'plenty and still not refill fast enough for an army and its animals to drink '
        'in turn. Every expedition that died in that desert was defeated by a well '
        'that was, technically, full.',
        'No song about the Burning Sands has ever mentioned a well, and the wells '
        'decided every single one of the events the songs are about.',
        'The Unicorn crossed that desert and were gone for centuries. The Moto came '
        'from beyond it. Everything the Empire finds strange about both of them starts '
        'out there, and everybody who finds them strange has declined to go and look.',
        'Some who tried the crossing ran out of water and went into the Shadowlands '
        'instead - the Moto contingent whose descendants are called the Dark Moto, '
        'changed by what lives there and refused at the border when they came back. '
        'That is what the desert does to a bad calculation.',
        'The Khan of the Moto is waging his campaign out that way, in Uru lands beyond '
        'the desert, which means the Burning Sands are now producing correspondence as '
        'well as casualties. Only one of the two reaches me on time.',
        'The Empire thinks of that desert as an edge. The people living out there think '
        'of it as the middle. Both sides are keeping records and only one set of them '
        'reaches me.',
        'People ask about the Gateway and mean the sand. The Gateway is a keep, with a '
        'garrison and a supply problem, and the keep is the part that has actually '
        'decided anything.',
        attach(
            'The crossing. The enemy is arithmetic: so many people and animals, so much '
            'water in the next well, and so many hours before that well has refilled '
            'enough for the ones at the back. It does not negotiate and it does not '
            'care who you are.',
            GREAT_WAVE,
        ),
        attach(
            "The last well before the land stops being anybody's territory. Nothing "
            'about the picture tells you that, or how fast it refills, or how many '
            'died a week past it - which is the whole difficulty with pictures and the '
            'reason I am employed.',
            RAINY_MOON,
        ),
    ),
    'bodi_kaikhan': (
        'Bodi Kaikhan is where Moto pilgrims go to commune with the spirits of their '
        'honored ancestors. A place whose entire function is talking to people who are '
        'no longer available for comment.',
        'Pilgrims there pray to Wei Tin, the god who brokers between the dead and the '
        'living, to help them, because ancestors need assistance finding their '
        'descendants and he is the one who bargains. A pilgrimage that requires an '
        'intermediary to arrange the meeting.',
        'Moto Gaheris, the Khan who leads the Moto, prayed at Bodi Kaikhan before '
        'swearing his vows and forging his covenant with the four Gods of Death of Moto '
        'teaching. The most consequential ground in the whole Moto material is a place '
        'with no building on it and no office-holder in it.',
        'It is the most consequential site in this file and almost nobody asks about '
        'it. They ask about the four swords Gaheris dedicated to the gods of death. The '
        'swords came afterward. The ground came first.',
        'It is a pilgrimage, not a temple network. There is no Grand Abbot of Bodi '
        'Kaikhan, and the Ministry of Rites finds that irregular, because Rites finds '
        'anything without an office-holder irregular. I am an office-holder without an '
        'office, so I am filed under irregular as well.',
        'Communing with your ancestors is ordinary enough anywhere in the Empire. '
        'Bargaining with a god of ghosts to arrange the appointment is not, and the '
        'Moto say both parts in exactly the same tone.',
        'Everything the modern Moto are reviving - the pre-Imperial worship, the old '
        'law, the covenants - passes through that ground at some point. If you want to '
        'know where the old ways are coming back from, it is not a book. I would like '
        'that on the record as the only professional insult I have ever taken from '
        'geography.',
        'Go if you like. Write down what you agreed to, in full, before you leave the '
        'ground, because pilgrims routinely come away sworn to something and remember '
        'the terms loosely. I make that request of everybody and I have never once been '
        'obliged.',
        attach(
            'The pilgrimage itself: quiet, unstructured, no building and no priest, a '
            'man sitting on ground where his ancestors are said to be reachable. '
            'Considerably quieter than the covenant that tends to follow it - Gaheris '
            'went for the former and came away with the latter.',
            INNER_VISION,
        ),
        attach(
            'On the other side of that conversation are the ancestors, and between you '
            'and them is a god of ghosts who has agreed to make the introduction and '
            'will want something for it. He is doing most of the negotiating. You are '
            'doing most of the agreeing.',
            FOX_WOMAN,
        ),
    ),
}
