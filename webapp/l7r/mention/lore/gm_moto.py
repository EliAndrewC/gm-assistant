"""The Moto, the Unicorn, and the gaijin west. GM Assistant only.

Fourteen categories the GM approved in message 2, and they must resolve BEFORE
the Great Clan routing added in message 3 - `Moto` is a Unicorn family, so
family-to-clan routing would swallow this entire file. See `topics.py`.
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
        'The Moto. Pastoralists, mostly nomadic, spread over land that is semi-arid '
        'and about one percent farmable.',
        'Which matters, because Imperial taxes are assessed on agricultural yield. The '
        'Moto pay almost nothing and everyone resents it and nobody can fix it.',
        'Their population is sparse for the same reason. You cannot graze a city.',
        'On paper their tribes are ruled by local governors. The Moto call those '
        'governors khans, and even the Shinjo usually do not know how many tribes '
        'there are.',
        'Not knowing how many subordinate units you have is, administratively, my '
        'least favorite fact in this entire record.',
        'They are Unicorn. They are also, in every practical sense, a separate '
        'civilization inside the Empire.',
        'Ask me about a Moto and you will get the tribe, the khan, and a note about '
        'which language the conversation happened in.',
        'The modern Moto are bringing back the old ways. That phrase should worry the '
        'Ministry of Rites more than it currently does.',
        attach(
            'Moto lands. Note the total absence of anything you could tax.',
            RAINY_MOON,
        ),
        attach(
            'And this is a Moto negotiation reaching its customary stage.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_etiquette': (
        'Moto etiquette. It is not the absence of etiquette. It is a different '
        'etiquette and it is extremely precise.',
        'The pattern runs: a statement with a demeaning implication, an immediate '
        'refutation, and an offer to get off the horses and settle it like men.',
        'The correct reply to "what did you just say to me" is not an apology. It is '
        'to ask whether their hearing is failing and offer to speak up.',
        'That exchange is not a fight starting. That exchange is a greeting. Rokugani '
        'guests survive it by accident about half the time.',
        'Getting off the horse is the escalation. Everything said on horseback is '
        'still conversation.',
        'A Rokugani courtier reads insult where a Moto reads warmth, and I have to '
        'write down what happened next.',
        'Etiquette rolls in Moto company take fifty percent off the top. That is not a '
        'penalty for rudeness; it is a penalty for being foreign.',
        'They are not being difficult. You are being quiet, which is worse.',
        attach(
            'Two Moto greeting one another cordially.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is a Rokugani courtier three minutes into the same greeting.',
            RAINY_MOON,
        ),
    ),
    'moto_tribal_structure': (
        'Extended family groups gather into what they call a clan, led by a khan. The '
        'Empire calls those clans "tribes" because "clan" was taken.',
        'They call themselves clans. We call them tribes. Both parties know and both '
        'parties are being polite about it.',
        'A clan runs to the low thousands. That is smaller than a Rokugani county and '
        'covers vastly more ground.',
        'The khan settles disputes, metes out justice within the clan, and leads it in '
        'war. Three jobs, one man, no ministry.',
        'No Ministry of Justice. No Ministry of Retainers. A khan and whoever he listens to.',
        'It works. That is the part that unsettles Rokugani administrators, and I include myself.',
        'Nobody, including the Shinjo, has an accurate count of the tribes. I have '
        'made my peace with that and it took years.',
        'Ask which tribe before you ask anything else. It is the only unit that '
        'reliably means something.',
        attach(
            'A tribe, in the only arrangement that matters to them.',
            CATS,
        ),
        attach(
            'And this is a dispute the khan is about to settle.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_language': (
        'They speak a different language. That single fact causes more theological '
        'confusion than anything else in this record.',
        'Enma was assumed for decades to be the Moto word for Emma-O. It is not. '
        'Different god entirely. Everyone was simply translating.',
        'Eastern Moto are mostly bilingual, because Rokugani has been the official '
        'language for centuries and the successful ones needed it.',
        'The successful ones. Which tells you what happened to the others.',
        'The same trap waits with every gaijin pantheon. A traveler from Medin al '
        'Salaat names their God of Love and a samurai hears Benten.',
        'They will probably be right - Benten is part of the fabric of reality and '
        'therefore omnipresent. Probably is doing the work.',
        'Every misunderstanding in the Moto material is a translation before it is a heresy.',
        'If a Moto tells you something impossible, ask which word they used. Twice.',
        attach(
            'Two languages meeting. This usually goes better than it looks.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is what a mistranslated god looks like once it has settled in.',
            FOX_WOMAN,
        ),
    ),
    'moto_rank': (
        'Moto rank. Fifteen ranks like everyone else, and then the adjustments, which '
        'is where people get it wrong.',
        'Anyone above Governor from the ruling House of a Family gets one rank higher '
        'than listed. From the ruling Family of a Clan, two.',
        'So Ikoma Yuan is Deputy Minister of War for Ikoma lands and sits at the tenth '
        'rank, because that ministry oversees the vassal families too.',
        'A county magistrate is of the fifth rank. The Emperor is the fifteenth and the only one.',
        'The Moto map their khans onto this and the fit is poor, which suits both sides.',
        "Gaheris is a Family daimyo by the Empire's reckoning and khan of khans by "
        'theirs. Those are not the same office and he uses both.',
        'Rank is how much trouble it is to ignore you. Among the Moto that calculation '
        'has a different denominator.',
        "Get a Moto's rank wrong in writing and you have created a diplomatic "
        'incident with a brush.',
        attach(
            'Rank being established the direct way.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the ceremonial version, which takes longer.',
            ARCHERS,
        ),
    ),
    'moto_gaheris': (
        'Moto Gaheris. Daimyo of the Moto Family. The Moto call him the khan of khans, '
        'which is a title the Empire has never formally recognized and never '
        'challenged.',
        'He carries four swords, one for each God of Death. Bloodstorm into battle, '
        'Lamentation when ambushed, Lightning in single combat, Retirement for '
        'executions.',
        'He chose which sword for which killing. That is not flourish, that is a '
        'covenant, and he swore his vows at Bodi Kaikhan.',
        'He is waging a military campaign in Uru lands, and everything else in the '
        'Moto material is downstream of that campaign.',
        "Moto Khunbish is his spiritual advisor. Khuyag is Khunbish's student, and "
        'Khuyag builds death detectors.',
        'Toranosuke of Chai Sedo declared that gaijin soulmate sketches portend success '
        'for his campaign. Abbots say that sort of thing once armies are moving.',
        'Khunbish met him years ago at Kyuden Shinjo as a farrier assigned to the Moto '
        'guests, and impressed him philosophically while shoeing horses.',
        'A man who dedicates a separate sword to executions has thought about '
        'executions more than you have.',
        attach(
            'Four swords. One decision per killing.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the campaign, from the perspective of Uru lands.',
            GREAT_WAVE,
        ),
    ),
    'the_yassa': (
        'The Yassa. Moto law. There is a written Yassa and there is what is actually '
        'done, and the gap is where every interesting case lives.',
        'It is not the Emerald Charter and it does not pretend to be. It answers to a '
        'khan, not a ministry.',
        'Rokugani magistrates find it arbitrary. Moto find Rokugani law slow. Both '
        'assessments are correct.',
        'A law that fits on a few pages and is enforced by a man who knows everyone '
        'involved works better than it has any right to.',
        'It covers theft, horses, water, and insult, in roughly that order of seriousness.',
        'Horse theft is not property crime among pastoralists. It is closer to '
        'attempted murder and is treated accordingly.',
        'The Empire has never formally tested whether the Yassa conflicts with '
        'Imperial law. Nobody wants that answer written down.',
        'Ask me about a Yassa ruling and I will tell you which khan made it, because '
        'that is the operative fact.',
        attach(
            'A Yassa ruling being handed down. It is brief.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the appeal process.',
            RAINY_MOON,
        ),
    ),
    'vindicator_moto': (
        'The Vindicator Clan. Southernmost Moto tribe, on the western side of the '
        'Twilight Mountains, dealing with whatever wanders out of the Shadowlands.',
        'Their doctrine: oni in the mortal realm are not evil. They are like rabid '
        'animals that need putting down.',
        'So killing one is a MERCY - it protects its victims and returns the oni to '
        'where the Tao prospers for it. That is a genuinely unusual theological '
        'position.',
        'Their hatred of all things Shadowlands is well known, which is why the '
        'position is treated with deference even by those who think it foolish.',
        'It is heretical to say oni are "not malicious". The Vindicator have found a '
        'formulation that is not quite that. Deliberately.',
        'They are the ones who turned away the corrupted Moto who tried to come home. '
        'That is in the record and it is not a comfortable entry.',
        'A tribe defined by what it stands between. There are several of those in this '
        'Empire and none of them are cheerful.',
        'Buy a Vindicator a drink and do not ask twice.',
        attach(
            "The Vindicator's actual work. Less heroic, more repetitive.",
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what they think about it afterward.',
            RAINY_MOON,
        ),
    ),
    'dark_moto': (
        'The Dark Moto. Yes. Careful where you ask that.',
        'When the Unicorn journeyed, some went south - the Moto especially, whose '
        'ancestral homelands are southwest of Medin al Salaat according to the Chai '
        'Sedo library.',
        'A large contingent ran out of water and, in desperation, entered the '
        'Shadowlands. They were corrupted there.',
        'Some tried to come back anyway. Their own kinsmen turned them away.',
        'That is the whole tragedy in three sentences and the Moto do not tell it in '
        'three sentences.',
        'Water is the constraint on every desert crossing. Not distance - the rate at '
        'which wells refill.',
        'The Vindicator are the ones who deal with what came of it, which is why their '
        'doctrine reads the way it does.',
        'The Empire treats this as folklore. The Moto do not.',
        attach(
            'The crossing that started it. The problem was never the sand.',
            GREAT_WAVE,
        ),
        attach(
            'And this is what came back to the gate.',
            KIDOMARU_TENGU,
        ),
    ),
    'horse_culture': (
        'Horses. Two entirely different economies and people conflate them constantly.',
        'Stabled: grain for one horse costs four to five koku a year. Grazing needs '
        'two to four acres per horse, and that land would otherwise grow food.',
        'That opportunity cost is the real price of a Rokugani horse, and it is why a '
        "bushi's mount is a statement.",
        'Moto horses cost a few bu. A single family keeps dozens alongside their '
        'sheep, at almost no effort.',
        'The catch is pedigree - run horses that way and you have no idea which '
        'stallion fathered which colt. The Otaku find this appalling.',
        'Traders buy cheap in Moto lands and sell dear in the Empire. Horses are '
        'self-transporting, which is the only reason the trade works.',
        'Only reason it BARELY works. Months of driving them east eats most of the margin.',
        'An active horse eats twenty pounds of hay a day. Everything else about '
        'cavalry follows from that number.',
        attach(
            'The expensive way to keep a horse.',
            ARCHERS,
        ),
        attach(
            'And this is the cheap way, which is also most of them.',
            RAINY_MOON,
        ),
    ),
    'unicorn_history': (
        'The Unicorn. They left, they came back, and the Empire has never entirely '
        'forgiven either decision.',
        'They were the Ki-Rin. They went out past the Burning Sands and returned with '
        'horses, gaijin habits, and the Moto.',
        'Their return displaced Mirumoto samurai, which is why three of the six major '
        'lineages in the Ryusei domain are refugees from it.',
        'That is what "the return of the Unicorn" means in practice. Not a parade. A '
        'land dispute lasting generations.',
        'A clan that has seen the outside is a clan the rest of the Empire cannot '
        'quite trust, and they know it.',
        'They peg one koku to one ton of hay the way the Emperor pegs it to forty '
        'gallons of rice. That is a whole worldview in a unit of account.',
        'One percent of Unicorn farmland is legally set aside for hay. Otaku lands '
        'stockpile beyond that by law.',
        'Otaku lands produce about fifteen thousand tons of hay a year from mandated '
        'land alone, and a few thousand more besides.',
        attach(
            'The return, as remembered by the Unicorn.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And as remembered by the people who were living there.',
            RAINY_MOON,
        ),
    ),
    'medin_al_salaat': (
        'Medin al Salaat. A gaijin city, west, and the reason half this record has footnotes.',
        'The Moto ancestral homelands are southwest of it, according to the Chai Sedo '
        'library. That library is the source for a great deal that nobody has '
        'verified.',
        'Kitsuki Tetsu considered a vow of creation to Jikoju to build and staff a '
        'temple there - civilization brought to the city, as the Great Ancestors '
        'brought it to the warlords.',
        'The danger being that if the campaign fails he is still bound to build it or die trying.',
        'There is a dream quest associated with the place. I have the account and I do '
        'not enjoy it.',
        'Gaijin gods get translated into Rokugani ones on contact, usually wrongly, '
        'occasionally catastrophically.',
        'A samurai hears their God of Love and thinks Benten. They are probably right. Probably.',
        'It is a real city with real politics and the Empire files it under "abroad".',
        attach(
            'The approach. Everything about it is foreign except the arithmetic.',
            GREAT_WAVE,
        ),
        attach(
            'And this is a gaijin god as a samurai understands it.',
            FOX_WOMAN,
        ),
    ),
    'burning_sands': (
        'The Burning Sands. Desert. West. The 1st Imperial Legion guards the Gateway '
        'to it and has for a very long time.',
        'The constraint is water, and specifically the RATE - a well may hold enough '
        'and still not refill fast enough for an army and its animals.',
        'That single fact has killed more expeditions than any enemy.',
        'The Unicorn crossed it. The Moto came from beyond it. Everything strange '
        'about both clans starts there.',
        'Some who tried ran out of water and went into the Shadowlands instead. See '
        'the Dark Moto, and then wish you had not asked.',
        'Gaheris is waging his campaign out that way, in Uru lands.',
        'The Empire thinks of it as an edge. The people out there think of it as the middle.',
        'Ask me about the Gateway and I will tell you about the keep, which is the '
        'part that actually matters.',
        attach(
            'The crossing. The enemy is arithmetic.',
            GREAT_WAVE,
        ),
        attach(
            "And this is the last well before it stops being anybody's territory.",
            RAINY_MOON,
        ),
    ),
    'bodi_kaikhan': (
        'Bodi Kaikhan. Pilgrims go there to commune with the spirits of their honored ancestors.',
        'They pray to Wei Tin to assist them, because ancestors need help finding their '
        'descendants and he is the one who bargains.',
        'Gaheris certainly prayed there before swearing his vows and forging his '
        'covenant with the four Gods of Death.',
        'Which makes it the single most consequential site in the Moto material and '
        'almost nobody asks about it.',
        'It is a pilgrimage, not a temple network. There is no Grand Abbot of Bodi '
        'Kaikhan and the Ministry of Rites finds that irregular.',
        'Communing with ancestors is ordinary. Bargaining with a god of ghosts to '
        'arrange it is not.',
        'Everything the modern Moto are reviving passes through that place at some point.',
        'Go if you like. Write down what you agreed to.',
        attach(
            'The pilgrimage. Quieter than the covenant that follows it.',
            INNER_VISION,
        ),
        attach(
            'And this is what is on the other side of the conversation.',
            FOX_WOMAN,
        ),
    ),
}
