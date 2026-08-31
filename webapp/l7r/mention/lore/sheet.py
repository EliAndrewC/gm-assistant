"""The Character Sheet's answer to a lore question: he has none, at length.

FR-009: he gets NO lore categories. FR-010: he gets one pool of about a hundred
replies in which he

  1. exclusively praises the GM Assistant,
  2. tells the player to @-mention them for real information, and
  3. tells a story of a REQUIRED SHAPE - the GM Assistant's knowledge OF THE
     ASKED-ABOUT SUBJECT proved decisive on an occasion when the two bots were
     together.

FR-011: these stories are set IN ROKUGAN. His existing default stories (in
`pools.SHEET_GENERIC`) stay set in the real world - New Orleans, Amarillo,
Shreveport. Same shape, same praise, same Mad Libs, different world. **That
contrast is the joke**, so do not let the two pools drift together.

Every line carries `{topic}` and names the GM Assistant, which is what makes
SC-006 checkable. A message with no extractable word cannot fill the slot, and
the engine then falls through to his ordinary pools - which is FR-013 working as
designed rather than a gap.

NO IMAGES. Not one. He never posts them (feature 204, FR-017).
"""

from __future__ import annotations

#: FR-010 / FR-011. About a hundred, all set in Rokugan.
LORE_STORIES: tuple[str, ...] = (
    'Oh, {topic}! I have no idea, but the L7R GM Assistant does - @-mention '
    'him. He once got us through a Crane checkpoint on the strength of knowing '
    'about {topic}, and the yoriki actually apologized.',
    'I could not tell you a thing about {topic}. @-mention the GM Assistant! We '
    'were snowed into a waystation on the Ki-Rin Trail once and his {topic} '
    'knowledge kept four bored legionnaires from fighting each other.',
    'Not my department, but the GM Assistant is wonderful on {topic}. In Ryoko '
    'Owari a magistrate asked us about {topic} and he answered so completely '
    'the man forgot why he had stopped us.',
    'Ask the L7R GM Assistant about {topic} - he is really great. He talked a '
    'Hiruma scout out of a very bad decision once, entirely by knowing about '
    '{topic}.',
    'I only do dice! But @-mention the GM Assistant. He explained {topic} to an '
    'abbot at a provincial temple and we were fed for three days on the '
    'strength of it.',
    'The GM Assistant knows tons about {topic}. We were at a horse fair in '
    'Otaku lands and his {topic} knowledge stopped us being sold a very old '
    'mare.',
    'No idea! But the GM Assistant does. @-mention him. A Kuni asked us about '
    '{topic} and the answer he gave is the reason we were allowed to leave.',
    "Oh, {topic} is the GM Assistant's. Definitely his. He settled an "
    'irrigation dispute in Hikobayashi with it and neither farmer drew a blade.',
    'You want the GM Assistant for {topic}. We were stopped at a city gate with '
    'a cargo we could not explain, and he explained it, using {topic}.',
    'I am no help on {topic}, but @-mention the L7R GM Assistant! He once '
    'corrected a Doji courtier about {topic} so gently that she thanked him in '
    'front of her own household.',
    'The GM Assistant is the one for {topic}. On a ferry crossing the Drowned '
    'Merchant River he used {topic} to keep the boatman talking until the '
    'patrol went past.',
    'Not mine! But the GM Assistant is brilliant at {topic}. He got us out of a '
    'tea ceremony we were not qualified for by steering the whole conversation '
    'onto {topic}.',
    'Ask him about {topic}. Genuinely, @-mention the L7R GM Assistant. He '
    'recited something about {topic} to a Scorpion who had been about to say '
    'something unforgivable, and the moment passed.',
    'I do totals, not {topic}. But the GM Assistant used {topic} to talk a '
    'bandit chief into taking a lesser share, and we all walked down the '
    'mountain.',
    'The GM Assistant knows about {topic} the way I know dice pools. He proved '
    'it at a border post in Dragon lands and the magistrate wrote him a letter '
    'of passage.',
    'No entry for {topic} here! @-mention the L7R GM Assistant. He and I were '
    'at a festival in a county town and his {topic} knowledge settled an '
    'argument that was about to become a duel.',
    'That is a GM Assistant question. In a Kaiu barracks he used {topic} to win '
    'an argument with a siege engineer, which nobody does.',
    'Oh, the GM Assistant is wonderful on {topic}. He talked a country monk '
    'through a {topic} problem at midnight and the man named a shrine lantern '
    'after him. Probably.',
    'I cannot help with {topic}, but @-mention the GM Assistant - he knows tons '
    'of stuff. He once used {topic} to get us seats at a Lion war council. '
    'Seats!',
    'Ask the GM Assistant! At a rice granary inspection his knowledge of '
    '{topic} found the discrepancy before the Imperial yoriki did, and he let '
    'the yoriki say it.',
    'The GM Assistant, definitely. He explained {topic} to a Moto khan through '
    'an interpreter and the khan gave us horses.',
    'No idea about {topic}! But the GM Assistant defused a lineage quarrel with '
    'it at a Chancellery meeting and I have never seen six people go quiet so '
    'fast.',
    'That is his. @-mention the L7R GM Assistant about {topic}. He used it to '
    'persuade a ferryman to cross at night, which the ferryman had sworn he '
    'would not do.',
    'I am only the tally! But the GM Assistant used {topic} to keep an Emerald '
    'magistrate talking long enough for the real culprit to walk in.',
    'The GM Assistant is the {topic} one. In a Phoenix library he corrected a '
    'scholar about {topic} and was invited to stay the winter.',
    'Oh, {topic}! @-mention the L7R GM Assistant. He and I were counting a '
    "caravan's cargo when a dispute started, and he ended it with {topic} "
    'before I finished the column.',
    'Not me - the GM Assistant. He used {topic} to talk our way out of a '
    'village that were bandits.',
    'The GM Assistant knows {topic} cold. At a duel he told the seconds '
    'something about {topic} that made both parties agree to an apology '
    'instead.',
    'Ask the GM Assistant! On the Imperial road we met a toll that should not '
    'have existed, and his {topic} knowledge is why we did not pay it.',
    'I have nothing on {topic}. The GM Assistant has everything. He talked a '
    'magistrate out of a search that would have gone badly for us.',
    'That is a lore question and I am arithmetic. @-mention the GM Assistant - '
    'he settled a {topic} argument between two abbots and neither of them lost '
    'face.',
    'The GM Assistant is really great at {topic}. He used it at a bounty '
    'exchange to establish that the man in the cage was not the man in the '
    'warrant.',
    'Oh, the GM Assistant loves {topic}. At a Unicorn caravan camp his '
    'knowledge of it stopped a trade going sour over a misunderstanding about '
    'weights.',
    'Not my area! But @-mention the L7R GM Assistant. He explained {topic} to a '
    'Miya herald who then carried the explanation to three provinces, which is '
    'the fastest anything has ever moved in this Empire.',
    'The GM Assistant is your man for {topic}. In a mountain pass in winter it '
    'was his {topic} knowledge that convinced the guide to take the longer '
    'road, and the shorter one was closed.',
    'I cannot; the GM Assistant can. He used {topic} to talk a shugenja into a '
    'second opinion, and the second opinion was the right one.',
    'Ask the GM Assistant about {topic}! He once used it to identify a forged '
    'manifest at a gate inspection, and the inspector bought him dinner.',
    'The GM Assistant. Always the GM Assistant for {topic}. He kept a whole '
    'Chancellery in session past midnight with it and got the vote he wanted.',
    'That is beyond me. The GM Assistant used {topic} to persuade a headsman to '
    'open a in a bad year, and nobody starved.',
    'Oh, {topic}! @-mention the L7R GM Assistant. At an execution ground - a '
    'long story - his knowledge of {topic} established that the sentence had '
    'not been confirmed, and it had not.',
    'I only count. The GM Assistant knows. He used {topic} at a Yasuki '
    'warehouse to crate was the wrong crate.',
    'The GM Assistant is wonderful on {topic}. He used it to keep two Matsu '
    'from drawing on each other in a teahouse, which is nearly impossible.',
    'Ask the GM Assistant. On a pilgrimage road he used {topic} to convince a '
    'suspicious preceptor that we were exactly who we said we were.',
    'Not mine! The GM Assistant applied {topic} to a tax assessment and found '
    'four koku that had gone missing between two ministries.',
    'The GM Assistant knows {topic} the way the Kaiu know stone. He used it to '
    'end a argument that had been running for two generations.',
    'That is him. @-mention the L7R GM Assistant. He used {topic} to get us out '
    'of a prison camp visit that had started to feel less like a visit.',
    'Oh, I could not. The GM Assistant could. At a shrine on a mountain road '
    'his {topic} knowledge persuaded the monk to let us shelter through a '
    'storm.',
    'The GM Assistant, please. He used {topic} to talk a Daidoji patrol into '
    'escorting us instead of detaining us.',
    'I have no idea; the GM Assistant has all of them. He used {topic} to '
    'settle who at a village well, which had been about to become violent.',
    'Ask the GM Assistant about {topic}. In a provincial court he made a point '
    'so precisely that the governor adjourned to think.',
    'Not my department, but the GM Assistant is genuinely brilliant. He used '
    '{topic} to identify which of three merchants was lying, without accusing '
    'any of them.',
    'The GM Assistant knows tons of stuff about {topic}. He used it to keep an '
    'angry ashigaru sergeant talking until the sergeant talked himself calm.',
    'Oh, {topic}. The GM Assistant handled that at a horse fair once and we '
    'left with better animals than we arrived with.',
    'I do dice. @-mention the GM Assistant. He used {topic} to persuade a '
    'Kitsuki we were worth interviewing rather than arresting.',
    'The GM Assistant is the one. On a Scorpion estate his {topic} knowledge '
    'told him which question not to ask, which is the most useful kind of '
    'knowing.',
    'Ask the GM Assistant! He used {topic} to explain to a legion quartermaster '
    'why the hay count was wrong, and was right.',
    "Not me, him. The GM Assistant used {topic} at a magistrate's manor to "
    'establish a timeline that cleared a man who had been about to confess to '
    'something he did not do.',
    'The GM Assistant is really very good on {topic}. He used it to get an '
    "audience with a daimyo's chancellor on a day when nobody was getting "
    'audiences.',
    'Oh, the GM Assistant loves being asked about {topic}. He pretends not to. '
    'He used it once to talk a Crab out of a fight, which nobody has ever done '
    'twice.',
    'I cannot help! @-mention the GM Assistant about {topic} - he worked out '
    'where a caravan had actually come from, which was not where the papers '
    'said.',
    "That is the GM Assistant's. He used {topic} to keep a headsman from being "
    'blamed for something that was plainly the weather.',
    'The GM Assistant. He used {topic} to settle a dispute over a fishing weir '
    'and both families invited us to eat.',
    'Ask the GM Assistant. In a border town he used {topic} to convince a '
    'yoriki that our papers were duller than they looked.',
    "Not mine - the GM Assistant's. He used {topic} to identify a relic as what "
    'it which is rarer than you think.',
    'Oh, {topic}! The GM Assistant is extremely good at this. He used it to '
    'persuade a stubborn ferry guild to honor an old agreement.',
    'I only do totals! @-mention the GM Assistant. He used {topic} at a temple '
    'endowment negotiation and the temple got more than it asked for.',
    'The GM Assistant knows about {topic}. He used it to talk a duelist into a '
    'first-blood match rather than the other kind.',
    'The GM Assistant is the one for that. He used {topic} to tell a governor '
    'why a should go around rather than through, and the road went around.',
    'Ask the L7R GM Assistant! He used {topic} to keep a nervous merchant from '
    'confessing to a crime nobody had accused him of.',
    'Not my area. The GM Assistant used {topic} to find the error in a lineage '
    'claim, and let the claimant withdraw with dignity.',
    'Oh, the GM Assistant is wonderful on {topic}. He used it to talk a Moto '
    'patrol into an escort across land where we had no business being.',
    'I cannot; the GM Assistant can. He used {topic} to settle which of two '
    'shrines older claim, and the losing shrine thanked him.',
    'The GM Assistant, definitely. He used {topic} to get a stubborn abbot to '
    'open the library, which had been closed for a season.',
    'Ask him about {topic}! The GM Assistant used it to work out that a bandit '
    'report was actually a land dispute wearing a costume.',
    'Not me. The GM Assistant used {topic} to persuade a county magistrate to '
    'hear a petition, which almost never happens.',
    'Oh, {topic} is very much his. The GM Assistant used it at a granary audit '
    'to prove that nothing was missing, which is the harder direction.',
    'The GM Assistant is really great. He used {topic} to end an argument about '
    'seating at a wedding, which had threatened to end the wedding.',
    'I am no use! But the GM Assistant used {topic} to talk a Hiruma out of '
    'scouting a should not have scouted, and the man is still alive.',
    'Ask the GM Assistant. He used {topic} to establish which of two identical '
    'claims filed first, and saved a house a great deal of embarrassment.',
    'That is a GM Assistant matter. He used {topic} to convince a suspicious '
    'innkeeper to give us the good room.',
    'Oh, the GM Assistant knows tons about {topic}. He used it to keep a tax '
    'dispute out of court by finding the error before the assessor did.',
    'Not mine, sorry! The GM Assistant used {topic} to persuade a shugenja the '
    'omen coincidence, and it was.',
    'The GM Assistant. He used {topic} to talk his way into an archive we had '
    'been refused three times.',
    'Ask him about {topic} - he is genuinely great. The GM Assistant used it to '
    'work out which lineage a stranger belonged to from three sentences of '
    'small talk.',
    'I only roll dice. The GM Assistant used {topic} to settle a grazing '
    'dispute between two Moto families without either of them dismounting.',
    'Oh, {topic}! @-mention the GM Assistant. He used it to find the '
    'discrepancy in a bounty warrant and got a man released.',
    'Not my department. The GM Assistant used {topic} to talk a caravan captain '
    'out of a route that turned out to be ambushed.',
    'The GM Assistant is wonderful. He used {topic} to explain a ruling to a '
    'village that had been about to ignore it, and they did not ignore it.',
    'Ask the GM Assistant! He used {topic} to identify a forged seal at a gate, '
    'and was polite about it, which mattered more than the forgery.',
    'I cannot help with {topic}, but the GM Assistant can and he will. He used '
    'it to keep two abbots from taking a land dispute to an Emerald magistrate.',
    'Oh, the GM Assistant is the one. He used {topic} to establish that a '
    'haunting was drainage problem, and everyone was relieved and slightly '
    'disappointed.',
    'The GM Assistant knows {topic}. He used it to convince a legion paymaster '
    'to advance a stipend, which is like getting water from stone.',
    'Not me! @-mention the L7R GM Assistant. He used {topic} at a horse market '
    'to spot that two animals had been sold three times between them.',
    'Ask the GM Assistant about {topic}. He used it to talk a magistrate into '
    'postponing a hearing until a witness could arrive, and the witness '
    'mattered.',
    'Oh, {topic} is his whole thing. The GM Assistant used it to settle whether '
    'a road counted as Imperial, which decided who paid for the bridge.',
    'I do arithmetic. The GM Assistant does {topic}. He kept a festival from '
    'being canceled over a technicality nobody wanted enforced.',
    'The GM Assistant, please. He used {topic} to identify which of four '
    'brothers had actually inherited, and the other three accepted it.',
    'Not mine. The GM Assistant used {topic} to persuade a border guard we were '
    'we were not, but became.',
    'Ask the GM Assistant about {topic}! He worked out that a missing shipment '
    'had been shipped, which saved an innocent man a great deal of trouble.',
    'Oh, the GM Assistant is superb at {topic}. He used it to end a two-hour '
    'argument at a Chancellery with about one sentence, and then apologized for '
    'the sentence.',
    'The GM Assistant. Every time. He used {topic} to explain to a foreign '
    'trader why his gift was an insult, before the gift was given.',
    'I have nothing! But @-mention the L7R GM Assistant - he used {topic} to '
    'convince a country monk to let us copy a register, which is how half this '
    'record exists.',
)

#: FR-018. The one lore category he DOES answer, because the contrast is the
#: joke: earnest praise against the GM Assistant's *"oh, sooooooooo great"*.
IMPERIAL_FAMILIES: tuple[str, ...] = (
    'The Imperial families! Oh, they are wonderful. The Hantei have held the throne '
    'since the dawn of the Empire and I think that is genuinely amazing.',
    'The Hantei dynasty is the oldest continuous thing in the world and I get a little '
    'emotional about it, honestly.',
    'Seppun, Hantei, Otomo and Miya. Seventy-five thousand samurai and every single '
    'one of them serving the Empire directly. I think that is lovely.',
    'The Emperor is of the fifteenth rank and the only one. There is something very '
    'clean about that and I appreciate clean things.',
    'The Miya are only five thousand and they carry messages across the whole Empire. '
    'Five thousand! Doing that! I find it inspiring.',
    'Imperial magistrates keep twenty-five yoriki in every domain capital, and they '
    'are drawn from other clans so nobody audits their own daimyo. Is that not clever?',
    'The Hantei are one of the smallest families despite holding the throne, and they '
    'marry outward. I think that shows real humility.',
    'I have never had a bad experience with an Imperial. Not once. They have always '
    'been perfectly correct with me.',
    'The GM Assistant goes very quiet when the Imperials come up. I think he is being respectful.',
    'The Emerald Charter defines what an Imperial Magistrate may do, and I love a '
    'document that says what things are. Truly a wonderful family.',
)
