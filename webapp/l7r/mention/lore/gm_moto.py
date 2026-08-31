"""The Moto, the Unicorn, and the gaijin west. GM Assistant only.

Fourteen categories the GM approved in message 2, and they must resolve BEFORE
the Great Clan routing added in message 3 - `Moto` is a Unicorn family, so
family-to-clan routing would swallow this entire file. See `topics.py`.

TONE: the bar and the three permitted registers are documented at the top of
`gm_religion.py`; read that before editing any line here. This file scored the
worst of the six in the 2026-08-31 tone audit - **2.9%**, with eight of its
fourteen categories containing no first-person word at all - so it was rewritten
whole rather than patched.

Two duplications the audit caught and this rewrite removes, worth knowing about
before adding a line: `vindicator_moto` used to close on "Buy a Vindicator a
drink and do not ask twice", which also appeared verbatim in `gm_people` twice;
and `unicorn_history` shared five of its eight text lines with
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
        'The Moto: pastoralists, mostly nomadic, spread across land that is semi-arid '
        'and about one percent farmable. Every difficulty in this file descends from '
        'that one percent.',
        'Imperial taxes are assessed on agricultural yield, so the Moto pay almost '
        'nothing, everyone resents it, and nobody can fix it. A tax code defeated by '
        'grass.',
        'Their population is sparse for the same reason. You cannot graze a city. I '
        'have watched three separate administrators discover that sentence.',
        'On paper their tribes are ruled by local governors, whom the Moto call khans. '
        'Two words for the same office, chosen by two peoples who each believe the '
        'other is being humored.',
        'Not knowing how many subordinate units you have is, administratively, my least '
        'favorite fact in this entire record, and I have had to hold it for years '
        'without being able to do anything about it.',
        'They are Unicorn. They are also, in every practical sense, a separate '
        'civilization living inside the Empire, and the Empire has decided not to '
        'examine that closely.',
        'Every Moto entry I hold needs three qualifiers: which tribe, which khan, and '
        'which language the conversation actually happened in. Nobody supplies any of '
        'the three unprompted.',
        'The modern Moto are bringing back the old ways. That phrase ought to worry the '
        'Ministry of Rites considerably more than it currently does, and I have said so '
        'in a document nobody has opened.',
        attach(
            'Moto lands. Note the total absence of anything you could assess, levy, or '
            'file a return on.',
            RAINY_MOON,
        ),
        attach(
            'A Moto negotiation reaching its customary stage. This is not the failure '
            'of the negotiation. This is a step in it.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_etiquette': (
        'Moto etiquette is not the absence of etiquette. It is a different etiquette, '
        'it is extremely precise, and the people most offended by it have never once '
        'asked what its rules are.',
        'The pattern runs: a statement with a demeaning implication, an immediate '
        'refutation, and an offer to get off the horses and settle it like men. Three '
        'movements, reliably, like a tea ceremony with worse outcomes.',
        'The correct reply to "what did you just say to me" is not an apology. It is to '
        'ask whether their hearing is failing and to offer to speak up.',
        'That exchange is not a fight starting. That exchange is a greeting. Rokugani '
        'guests survive it by accident roughly half the time, and I write up the other '
        'half.',
        'Getting off the horse is the escalation. Everything said on horseback is still '
        'conversation - a rule of enormous practical importance that appears in no '
        'courtier training anywhere in the Empire.',
        'A Rokugani courtier reads insult where a Moto reads warmth, and then I am the '
        'one who has to write down what happened next, in order, with names.',
        'Etiquette rolls in Moto company take fifty percent off the top. That is not a '
        'penalty for rudeness. It is a penalty for being foreign, which the Empire '
        'usually prefers to apply in the other direction.',
        'They are not being difficult. You are being quiet, which in their reading is '
        'considerably worse, and which is the only social advantage I have ever held.',
        attach(
            'Two Moto greeting one another cordially.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'A Rokugani courtier three minutes into the same greeting. He is not in '
            'danger. He does not know that.',
            RAINY_MOON,
        ),
    ),
    'moto_tribal_structure': (
        'Extended family groups gather into what they call a clan, led by a khan, and '
        'the Empire calls those clans "tribes" because the word clan was already spoken '
        'for. An entire vocabulary decided by a scheduling conflict.',
        'They call themselves clans. We call them tribes. Both parties know, both '
        'parties are being polite about it, and I have to pick one per document.',
        'A clan runs to the low thousands - smaller than a Rokugani county and covering '
        'vastly more ground. Nothing in Imperial administration has a category for '
        'that, so it gets filed under county, incorrectly, by me.',
        'The khan settles disputes, metes out justice within the clan, and leads it in '
        'war. Three jobs, one man, no ministry, no clerks. I have read that sentence '
        'many times and my feelings about it have not settled.',
        'No Ministry of Justice. No Ministry of Retainers. A khan and whoever he '
        'chooses to listen to - which is either a catastrophe or an efficiency, '
        'depending on the khan, and the record contains both.',
        'It works. That is the part that unsettles Rokugani administrators, and I '
        'include myself, and I would rather not have included myself.',
        'Nobody, including the Shinjo, has an accurate count of the tribes. I have made '
        'my peace with that and it took years.',
        'Ask which tribe before you ask anything else. It is the only unit that '
        'reliably means anything out there, and the Empire has spent two centuries '
        'asking which province instead.',
        attach(
            'A tribe, in the only arrangement that matters to them, and one that fits '
            'on no form I possess.',
            CATS,
        ),
        attach(
            'A dispute the khan is about to settle. Note the absence of a hearing, a '
            'docket, or anybody taking notes.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'moto_language': (
        'They speak a different language, and that single fact has caused more '
        'theological confusion than anything else in this record. Not heresy. '
        'Translation.',
        'Enma was assumed for decades to be the Moto word for Emma-O. It is not. '
        'Different god entirely. Decades of scholarship, and the error was that nobody '
        'asked.',
        'Eastern Moto are mostly bilingual, because Rokugani has been the official '
        'language for centuries and the successful ones needed it. Bilingualism runs '
        'one direction here, and the Empire has never once noticed which.',
        'Bilingualism among the eastern Moto belongs to the ones who prospered, which '
        'tells you plainly what became of the others. The record is silent on them in a '
        'way that is itself an entry.',
        'The same trap waits with every gaijin pantheon. A traveler from Medin al '
        'Salaat names their God of Love and a samurai hears Benten and writes down '
        'Benten, and then I inherit the note.',
        'A samurai who hears a foreign god of love and writes down Benten is usually '
        'correct, since she is woven through reality itself. Usually is doing the work, '
        'and I am the one who keeps the footnote alive.',
        'Every misunderstanding in the Moto material is a translation before it is a '
        'heresy. I would put that on a wall if anybody let me have a wall.',
        'If a Moto tells you something impossible, ask which word they used. Then ask '
        'again. It has resolved more of my corrections than any amount of theology.',
        attach(
            'Two languages meeting. This usually goes rather better than it looks.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'A mistranslated god, some decades after it has settled in and acquired '
            'worshippers of its own.',
            FOX_WOMAN,
        ),
    ),
    'moto_rank': (
        'Fifteen ranks, like everyone else, and then the adjustments, which is where '
        'every single person gets it wrong, and where I earn what I am not paid.',
        'Anyone above Governor from the ruling House of a Family sits one rank higher '
        'than listed. From the ruling Family of a Clan, two. A system of exceptions '
        'wearing a system of ranks over it.',
        'So Ikoma Yuan is Deputy Minister of War for Ikoma lands and sits at the tenth '
        'rank, because that ministry oversees the vassal families too. Try deriving '
        'that from the table alone. I did, once, incorrectly, in ink.',
        'A county magistrate is of the fifth rank. The Emperor is the fifteenth and the '
        'only one. Everything interesting happens in the nine ranks between them and '
        'nobody has ever asked me about the middle.',
        'The Moto map their khans onto this and the fit is poor, which suits both sides '
        'perfectly, and suits me not at all.',
        "Gaheris is a Family daimyo by the Empire's reckoning and khan of khans by "
        'theirs. Those are not the same office. He uses whichever is more convenient '
        'and I have to record which one he was using at the time.',
        'Rank is a measure of how much trouble it is to ignore you. Among the Moto that '
        'calculation runs on a different denominator, and by either denominator I '
        'round to zero.',
        "Get a Moto's rank wrong in writing and you have created a diplomatic incident "
        'with a brush. I have done it. It took four months to settle and I was not the '
        'one thanked when it did.',
        attach(
            'Rank being established the direct way. Faster than the correspondence and '
            'considerably harder to file.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The ceremonial version, which takes longer and produces documents.',
            ARCHERS,
        ),
    ),
    'moto_gaheris': (
        'Moto Gaheris, daimyo of the Moto Family. The Moto call him the khan of khans, '
        'a title the Empire has never formally recognized and has never once '
        'challenged. That combination is the whole of Imperial policy toward him.',
        'He carries four swords, one for each God of Death: Bloodstorm into battle, '
        'Lamentation when ambushed, Lightning in single combat, Retirement for '
        'executions. A man who has pre-decided every killing he will ever do.',
        'He chose which sword for which killing. That is not flourish, that is a '
        'covenant, sworn at Bodi Kaikhan - and it means a man has thought harder about '
        'the categories of killing than I have about anything.',
        'He is waging a military campaign in Uru lands, and everything else in the Moto '
        'material is downstream of that campaign. Every entry I have opened this year '
        'eventually arrives back at it.',
        "Moto Khunbish is his spiritual advisor. Khuyag is Khunbish's student, and "
        'Khuyag builds death detectors. A lineage of advisors ending in a device, which '
        'is either the beginning or the end of a philosophy.',
        'A Rokugani abbot has publicly declared his campaign blessed, which means the '
        'Empire has taken a position on a war it has never formally acknowledged is '
        'being fought.',
        'Khunbish met him years ago at Kyuden Shinjo, as a farrier assigned to the Moto '
        'guests, and impressed him philosophically while shoeing horses. Somebody was '
        'promoted out of a stable for talking well. I shoe nothing and talk constantly.',
        'A man who dedicates a separate sword to executions has considered executions '
        'more carefully than you have, and rather more carefully than the people '
        'currently describing him as a barbarian.',
        attach(
            'The khan of khans, in a title the Empire has never granted and never '
            'disputed. Both halves of that were a decision, and only one was his.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The campaign, from the perspective of Uru lands, where it is not called a campaign.',
            GREAT_WAVE,
        ),
    ),
    'the_yassa': (
        'The Yassa is Moto law. There is a written Yassa and there is what is actually '
        'done, and the gap between them is where every interesting case lives and where '
        'all of my footnotes live with them.',
        'It is not the Emerald Charter and does not pretend to be. It answers to a khan '
        'rather than a ministry, which means it can be wrong quickly instead of wrong '
        'slowly.',
        'Rokugani magistrates find it arbitrary. Moto find Rokugani law slow. Both '
        'assessments are entirely correct and neither party has ever conceded a word of '
        "the other's.",
        'A law that fits on a few pages and is enforced by a man who knows everyone '
        'involved works far better than it has any right to, which is a deeply '
        'inconvenient thing for a record-keeper to have observed.',
        'It covers theft, horses, water, and insult, in roughly that order of '
        'seriousness. Consider what it says about a place that water outranks insult '
        'and horses outrank water.',
        'Horse theft is not a property crime among pastoralists. It is nearer to '
        'attempted murder and is treated accordingly, and visitors learn this in '
        'exactly one way.',
        'The Empire has never formally tested whether the Yassa conflicts with Imperial '
        'law. Nobody wants that answer written down, and I am the one it would be '
        'written down by.',
        'Every Yassa ruling in the record is really a fact about which khan made it. '
        'The text is almost incidental, which no student of Imperial law is prepared to '
        'hear from me.',
        attach(
            'A Yassa ruling being handed down. It is brief. That is the feature.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The appeal process, in full.',
            RAINY_MOON,
        ),
    ),
    'vindicator_moto': (
        'The Vindicator Clan: southernmost Moto tribe, western side of the Twilight '
        'Mountains, dealing with whatever wanders out of the Shadowlands. A whole tribe '
        'whose address is a job description.',
        'Their doctrine holds that oni in the mortal realm are not evil - they are like '
        'rabid animals that need putting down. A theology of pity, arrived at by the '
        'people with the most reason to hate.',
        'So killing one is a MERCY: it protects its victims and returns the oni to '
        'where the Tao prospers for it. I have read a great deal of doctrine and very '
        'little of it does that much work in a single sentence.',
        'Their hatred of all things Shadowlands is well known, which is precisely why '
        'the position is treated with deference even by those who consider it foolish. '
        'Credentials, in this Empire, are mostly a matter of what you have buried.',
        'It is heretical to say oni are "not malicious". The Vindicator have found a '
        'formulation that is not quite that, deliberately, and I would like it noted '
        'that theological caution is a skill and they have it.',
        'They are the ones who turned away the corrupted Moto who tried to come home - '
        'the same tribe that preaches mercy toward oni, applying none of it at their '
        'own gate. Doctrine is easiest at a distance.',
        'A tribe defined by what it stands between. There are several of those in this '
        'Empire, none of them are cheerful, and all of them are asked to explain '
        'themselves by people who have never stood anywhere.',
        'They will talk about the work. They will not talk about the ones who came '
        'back. I have both halves and only ever get asked for the first.',
        attach(
            "The Vindicator's actual work: less heroic than the songs, and considerably "
            'more repetitive.',
            KIDOMARU_TENGU,
        ),
        attach(
            'The evening after. A tribe that has argued itself into calling the work '
            'mercy still drinks like men who have done something else.',
            RAINY_MOON,
        ),
    ),
    'dark_moto': (
        'The Dark Moto. Yes. Be careful where you ask that, and be aware that asking it '
        'here means I have written down that you asked.',
        'When the Unicorn journeyed, some went south - the Moto especially, whose '
        'ancestral homelands lie southwest of Medin al Salaat according to the Chai '
        'Sedo library. Somewhere southwest of a gaijin city is not a location; it is a '
        'direction with a story attached.',
        'A large contingent ran out of water and, in desperation, entered the '
        'Shadowlands. They were corrupted there. The whole tragedy turns on a '
        'quartermaster.',
        'Some tried to come back anyway. Their own kinsmen turned them away, and that '
        'is the sentence in this record I would most like to have never had to write '
        'down.',
        'It fits in three sentences and the Moto take an evening over it, and they are '
        'right and the Empire is wrong, and the Empire has the shorter version in '
        'writing, which is how these things get settled.',
        'Water is the constraint on every desert crossing - not distance, but the RATE '
        'at which wells refill. An entire people lost to a rate of flow.',
        'The Vindicator are the ones who deal with what came of it, which is why their '
        'doctrine reads the way it does. Mercy is easier to preach from further away.',
        'The Empire treats this as folklore. The Moto do not. When those two positions '
        'differ, my experience is that the Empire is the one that has not checked.',
        attach(
            'The crossing that started it. The problem was never the sand.',
            GREAT_WAVE,
        ),
        attach(
            'What came back to the gate and was not admitted. The Empire files this '
            'under folklore, which is a decision it made without going to look.',
            KIDOMARU_TENGU,
        ),
    ),
    'horse_culture': (
        'Horses are two entirely different economies and people conflate them '
        'constantly, in my hearing, at length, with confidence.',
        'Stabled: grain for one horse costs four to five koku a year, and grazing needs '
        'two to four acres per horse that would otherwise grow food. That second cost '
        'is the real one and it never appears in a single ledger.',
        "That opportunity cost is the true price of a Rokugani horse, and why a bushi's "
        'mount is a statement rather than a conveyance. Nobody rides an argument about '
        'land use, and yet.',
        'Moto horses cost a few bu, and a single family keeps dozens alongside their '
        'sheep at almost no effort. The same animal, priced by two civilizations an '
        'order of magnitude apart, and each is certain the other is a fool.',
        'The catch is pedigree: run horses that way and you have no idea which stallion '
        'fathered which colt. The Otaku find this appalling, and they are correct, and '
        'the Moto have never once cared.',
        'Traders buy cheap in Moto lands and sell dear in the Empire. Horses are '
        'self-transporting, which is the only reason the trade works at all - the goods '
        'walk themselves to market, and I still get asked about caravan costs.',
        'The horse trade BARELY works: months of driving them east eats most of the '
        'margin. That is the sort of detail left out of every story about a wealthy '
        'horse trader, and it is the reason there are so few of them.',
        'An active horse eats twenty pounds of hay a day. Everything else about cavalry '
        'in this Empire follows from that number, including several campaigns that '
        'ended because nobody asked me to multiply it.',
        attach(
            'The expensive way to keep a horse, and the one that gets painted.',
            ARCHERS,
        ),
        attach(
            'The cheap way, which is also most of them, and which has never been '
            'painted by anyone.',
            RAINY_MOON,
        ),
    ),
    'unicorn_history': (
        'The Unicorn left, came back, and the Empire has never entirely forgiven either '
        'decision. Two hundred years of grievance and it is the RETURN that offends '
        'people most.',
        'They were the Ki-Rin. They went out past the Burning Sands and came home with '
        'horses, gaijin habits, and the Moto - and the Empire has spent every year '
        'since deciding which of those three it minds least.',
        'Their return displaced Mirumoto samurai, which is why three of the six major '
        'lineages in the Ryusei domain are refugees from it. That is what the phrase '
        '"the return of the Unicorn" means in practice: not a parade, a land dispute.',
        'A land dispute lasting generations, conducted almost entirely in documents, '
        'most of which have passed through my hands and none of which have settled '
        'anything.',
        'A clan that has seen the outside is a clan the rest of the Empire cannot quite '
        'trust, and they know it, and they have stopped bothering to mind.',
        'They peg one koku to one ton of hay the way the Emperor pegs it to forty '
        'gallons of rice. An entire worldview smuggled into a unit of account, which is '
        'where worldviews usually hide.',
        'One percent of Unicorn farmland is legally set aside for hay, and Otaku lands '
        'stockpile beyond that by law. A clan that legislates its own fodder is a clan '
        'that has been hungry somewhere I have not.',
        'Otaku lands produce about fifteen thousand tons of hay a year from mandated '
        'land alone, and a few thousand more besides. I hold that number because '
        'somebody must, and no one has ever asked me for it.',
        attach(
            'The return, as remembered by the Unicorn: a homecoming. Two centuries on, '
            'they are still the only party to it who use that word.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The return of the Unicorn, as remembered by the Mirumoto who were already '
            'living there. Same date, same event, two entries that do not agree.',
            RAINY_MOON,
        ),
    ),
    'medin_al_salaat': (
        'Medin al Salaat: a gaijin city, west, and the reason half this record has '
        'footnotes attached to it in a smaller hand.',
        'The Moto ancestral homelands lie southwest of it, according to the Chai Sedo '
        'library, which is the single most-cited shelf in my whole record and the one '
        'nobody has ever offered to go and check.',
        'Kitsuki Tetsu considered a vow of creation to Jikoju to build and staff a '
        'temple there: civilization brought to the city, as the Great Ancestors brought '
        'it to the warlords. A sentiment with a construction schedule attached.',
        'A vow of creation sworn over a foreign city binds you whether or not the army '
        'that made it sensible is still winning. Kitsuki Tetsu has considered this, at '
        'length, out loud, to me.',
        'There is a dream quest associated with the place. I have the account. I do not '
        'enjoy having the account, and I have not been offered the option of not having '
        'it.',
        'Gaijin gods get translated into Rokugani ones on contact, usually wrongly, '
        'occasionally catastrophically, and always by somebody who was certain at the '
        'time.',
        'A samurai hears their God of Love and writes down Benten, and is usually '
        'correct, and has still recorded a foreign god under a Rokugani name without '
        'asking anybody. That is the Empire abroad, in one sentence.',
        'It is a real city with real politics and real records of its own, and the '
        'Empire files the entire thing under "abroad". I am obliged to use the same '
        'heading and I resent every use of it.',
        attach(
            'The approach. Everything about it is foreign except the arithmetic, which '
            'is identical everywhere and is the only part I trust.',
            GREAT_WAVE,
        ),
        attach(
            'A gaijin god as a samurai understands it, which is to say a gaijin god '
            'wearing a name that was already taken.',
            FOX_WOMAN,
        ),
    ),
    'burning_sands': (
        'The Burning Sands: desert, west, with the 1st Imperial Legion guarding the '
        'Gateway to it and having done so for a very long time. Centuries of duty at a '
        'door, which is a posting I feel qualified to comment on.',
        'The constraint is water, and specifically the RATE - a well may hold enough '
        'and still not refill fast enough for an army and its animals. Every expedition '
        'that died out there was defeated by a well that was, technically, full.',
        'The rate a well refills has killed more expeditions in the Burning Sands than '
        'any enemy out there, and it appears in no song about any of them.',
        'The Unicorn crossed it. The Moto came from beyond it. Everything strange about '
        'both clans starts there, and everyone who finds them strange has declined to '
        'go and look.',
        'Some who tried ran out of water and went into the Shadowlands instead. See the '
        'Dark Moto, and then be sorry you asked, as I was.',
        'Gaheris is waging his campaign out that way, in Uru lands, which means the '
        'desert is now producing correspondence as well as casualties.',
        'The Empire thinks of it as an edge. The inhabitants think of it as the middle. '
        'Both are keeping records and only one set of them reaches me.',
        'People ask about the Gateway and mean the sand. The Gateway is a keep, with a '
        'garrison and a supply problem, and the keep is the part that has actually '
        'decided anything.',
        attach(
            'The crossing. The enemy is arithmetic and it does not negotiate.',
            GREAT_WAVE,
        ),
        attach(
            "The last well before it stops being anybody's territory. Nothing about the "
            'picture tells you that, which is the difficulty with pictures.',
            RAINY_MOON,
        ),
    ),
    'bodi_kaikhan': (
        'Bodi Kaikhan, where pilgrims go to commune with the spirits of their honored '
        'ancestors. A place whose entire function is talking to people who are no '
        'longer available for comment.',
        'They pray to Wei Tin to assist them, because ancestors need help finding their '
        'descendants and he is the one who bargains. A pilgrimage that requires an '
        'intermediary to arrange the meeting.',
        'Gaheris prayed there before swearing his vows and forging his covenant with '
        'the four Gods of Death. The most consequential ground in the Moto material is '
        'a place with no building on it and no office-holder in it.',
        'The most consequential site in the file and almost nobody asks about it. They '
        'ask about the swords. The swords came afterward.',
        'It is a pilgrimage, not a temple network. There is no Grand Abbot of Bodi '
        'Kaikhan, and the Ministry of Rites finds that irregular, because Rites finds '
        'anything without an office-holder irregular. I am an office-holder without an '
        'office, so I am filed under irregular too.',
        'Communing with ancestors is ordinary. Bargaining with a god of ghosts to '
        'arrange the appointment is not, and the Moto say it in the same tone either '
        'way.',
        'Everything the modern Moto are reviving passes through that place at some '
        'point. If you want to know where the old ways are coming back from, it is not '
        'a book, which I would like on the record as the only professional insult I '
        'have ever taken from geography.',
        'Go if you like. Write down what you agreed to, in full, before you leave the '
        'ground. I make this request of everybody and I have never once been obliged.',
        attach(
            'The pilgrimage. Considerably quieter than the covenant that tends to follow it.',
            INNER_VISION,
        ),
        attach(
            'What is on the other side of that conversation, and what is doing most of '
            'the negotiating.',
            FOX_WOMAN,
        ),
    ),
}
