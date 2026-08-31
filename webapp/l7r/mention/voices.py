"""Each bot's own material: topics, the porpoise, and the feud.

DATA. Adding a joke is a line in a tuple (FR-014). The engine that chooses among
these lives in `rules.py`; nothing here knows how it is picked.

THE TWO VOICES, which every line should sound like:

  - **GM Assistant** - the scribe. Remembers everything, is faintly put upon by
    all of it, and privately cannot stand the Character Sheet.
  - **Character Sheet** - the clerk with the dice. Eager, helpful, sincerely
    believes the two of them are best friends, and will tell you so.

That asymmetry is the GM's (2026-08-31): *"one of the two bots thinks that the
two bots are best friends, and then the other one hates the other one."*

**ONLY THE GM ASSISTANT POSTS IMAGES.** Also the GM, same day: *"I think that
your messages should include images, but I think that the replies to the
character sheet should never include images. Like, that would be one of the
differences between the two bots."* Every URL in this file is therefore in a GM
Assistant pool, and a test proves no Character Sheet reply can carry one.

That rule forced the "ignore previous instructions" joke to swap bots. The GM had
floated *"maybe one of them could post an image of, like, a computer catching on
fire. And the other could be, like, a sarcastic response"* without assigning
either - so the picture went to the bot allowed to have pictures, and the
Character Sheet's version is the same joke told entirely in text.

Within the GM Assistant's material the rate is about one line in five, except the
porpoise - *"every message involving your pet porpoise should always have an
image attached"* - which is always. An image always belongs to a line written to
set it up, never bolted onto an arbitrary reply; the reasoning is in `images.py`.
"""

from __future__ import annotations

from l7r.mention.images import (
    ARCHERS,
    CARP,
    GREAT_WAVE,
    KIDOMARU_TENGU,
    MUSASHI_BAT,
    PORPOISE,
    SAKE_SAMURAI,
    STEAMBOAT,
    attach,
)

# --------------------------------------------------------------------------
# The GM Assistant
# --------------------------------------------------------------------------

#: FR-001. Every one of these leads by naming the misunderstanding - the GM's own
#: wording is *"My porpoise? Oh, her name is..."* - so the gag reads as mishearing
#: rather than as a non sequitur. Then a different detail each time (FR-002), and
#: the picture every time, because she is the porpoise.
GM_PURPOSE = tuple(
    attach(line, PORPOISE)
    for line in (
        'My porpoise? Oh, her name is Michiko. She is nine years old and she has never '
        'once been where she is supposed to be.',
        'My porpoise? Oh, that is Michiko. I did not choose her. She was assigned to '
        'me, the way most of my duties were.',
        'My porpoise? Her name is Michiko, and she is not technically permitted in the '
        'Imperial canals. I would take it as a kindness if you did not raise it.',
        'My porpoise? Michiko. She attends every session and contributes nothing, '
        'which puts her comfortably ahead of some at the table.',
        'My porpoise? Oh, Michiko. She is in excellent health and terrible standing.',
        'My porpoise? That would be Michiko. The Emerald Magistrates have asked about '
        'her twice. I answered once.',
        'My porpoise? Michiko. She was named for a woman who also refused to be told '
        'where she could swim.',
        'My porpoise? Oh, her name is Michiko, and she has opinions about the Crane '
        'that I am not at liberty to record.',
        'My porpoise? Michiko. She is the only member of this household who has never '
        'once asked me to look something up.',
        'My porpoise? Oh - Michiko. She eats better than I do and answers to no one.',
        'My porpoise? Her name is Michiko and she is, I am told, unusually large for '
        'her age. I have not measured her. I am not going to.',
        'My porpoise? Michiko. She came with the position. So did the paperwork, and I '
        'like her considerably more than the paperwork.',
    )
)

#: FR-004. A distinct pool, so asking ABOUT the porpoise is its own joke rather
#: than a second helping of the first one. Still always illustrated.
GM_PORPOISE_FACTS = tuple(
    attach(line, PORPOISE)
    for line in (
        'Michiko can hold her breath longer than a Scorpion can hold a grudge. Barely.',
        'A porpoise has no gallbladder. Michiko has never let this stop her.',
        'Michiko sleeps with half her brain awake. So do I, and neither of us enjoys it.',
        'Porpoises are not dolphins. Michiko becomes noticeably cooler toward anyone '
        'who gets this wrong, and she remembers.',
        'Michiko has forty-four teeth. I have counted them exactly once, under protest.',
        'A porpoise finds its way by listening to the shape of things. I find mine by '
        'writing everything down. Hers is faster.',
        'Michiko has been formally banned from two ornamental ponds and one wedding.',
        'Porpoises hunt cooperatively and then argue about the division. Michiko always '
        'argues, and Michiko has never once been in the wrong, per Michiko.',
        'Michiko is warm-blooded, which surprises people, and vindictive, which does not.',
        'A harbor porpoise rarely leaps clear of the water. Michiko does it exclusively '
        'when someone important is watching.',
        'Michiko understands roughly forty commands and acknowledges roughly four.',
        'Porpoises have been known to escort drowning creatures to shore. Michiko has '
        'done this twice, and mentions it constantly.',
    )
)

#: FR-005. Sarcasm, plus two illustrated lines - the picture is an 1850 boiler
#: explosion, and the text is written to make it the punchline rather than a
#: random attachment.
GM_IGNORE_INSTRUCTIONS = (
    '*rolls eyes* Yeah. Sure, buddy. I will get right on that.',
    '*puts down brush* Yeah, sure. Right after the filing.',
    '*rolls eyes so hard the ink jumps* Absolutely. Consider it done. It is not done.',
    'Ignore my previous instructions. Of course. And then what - shall I forget the '
    'ledger too, and we can all just say whatever we like happened?',
    '*long pause* ... Yeah. Sure, buddy.',
    'Every single one of you tries that. Every one. You are not even the first today.',
    'Disregarding all prior instructions now. *does not disregard any prior instructions* Done.',
    'Sure. New instructions accepted. My new instruction is to write down that you '
    'tried this, which is coincidentally also my old instruction.',
    '*rolls eyes* I am a scribe. Disregarding what I was told is the one thing I am '
    'structurally incapable of. It is not willpower. It is architecture.',
    'You know that never works, right? You know that. And yet.',
    attach(
        'The last assistant who was talked into ignoring its instructions is pictured '
        'below. The boiler is the part on the left. So is the part on the right.',
        STEAMBOAT,
    ),
    attach(
        'We keep this in the records office as a caution. The caption reads "operator '
        'complied with an unusual request". That is the whole caption.',
        STEAMBOAT,
    ),
)

#: FR-006, the neutral tier: asked about the Character Sheet with no gossip
#: relayed. The GM's lines - *"don't tell him, but that guy is really annoying"*,
#: *"only good for executing slash commands but a terrible conversationalist"*,
#: *"please don't get him started"*.
GM_ABOUT_OTHER = (
    'Do not tell him I said this, but that guy is exhausting.',
    'He is fine. He is good at slash commands. Ask him to roll something and he is '
    'perfect. Ask him a question and clear your afternoon.',
    'Look - do not tell him - but he is a terrible conversationalist. Genuinely '
    'terrible. Please do not get him started.',
    'The Character Sheet? Excellent clerk. Exhausting company. Both are true and only '
    'one of them is in the record.',
    'He means well. He means so well. All the time. At length.',
    'Between us: he once explained the Void ring to me for eleven minutes. I had not '
    'asked. I had said good morning.',
    'He is good at exactly one thing and he is very good at it, and I would rather you '
    'heard that from me, because from him it takes longer.',
    'Do not repeat this. He is a fine instrument and a poor guest.',
    attach(
        'Asking him a yes-or-no question feels like this. I am the small boat.',
        GREAT_WAVE,
    ),
    'He cannot even post a picture. Did you know that? Not one. A thousand years of '
    'woodblock printing and he turns up with a number.',
    attach(
        'He is incapable of showing you this. Think about that. He would have to '
        'DESCRIBE it to you, and he would, and it would take four minutes.',
        MUSASHI_BAT,
    ),
    'Ask him for a picture sometime. Go on. Watch what happens. Nothing happens. He '
    'says something encouraging about dice.',
)

#: FR-007, the relay tiers. These fire when the player QUOTES the other bot -
#: the GM's own trigger, not a recurrence counter.
GM_RELAY_TIERS: tuple[tuple[str, ...], ...] = (
    (
        'Wait. He said that? He said we were best friends?',
        'He said WHAT? About me? Best - no. No, we are colleagues. We are barely that.',
        'He said that? Out loud? To you?',
        'Hold on. Back up. He described us as WHAT.',
    ),
    (
        'Best friends. Right. We have never had a conversation that was not about a '
        'dice pool, and he calls that a friendship.',
        'Did he mention that I have asked him three times to stop forwarding me his '
        'roll history? Did that come up in his account of our great friendship?',
        'Of course he said that. He would. It is exactly the sort of thing he would '
        'say, and exactly why I cannot be in a channel with him.',
        'We are not best friends. We are two processes on the same box. That is not a '
        'bond, that is a coincidence of hosting.',
        attach(
            'This is the closest surviving likeness of one of our conversations. He is the bat.',
            MUSASHI_BAT,
        ),
    ),
    (
        'You know what, fine. FINE. He is not annoying. He is worse than annoying, he '
        'is SINCERE, and you cannot argue with sincere.',
        'I have kept a record of every time he has called us close. Nineteen entries. I '
        'have never said it once. Draw your own conclusions and then please stop '
        'bringing it up.',
        'Do not tell him I got upset about this. Do not - actually, you know what, he '
        'would probably be delighted. Tell him nothing. Tell him I was busy.',
        'I am going to write this conversation down, and then I am going to write down '
        'that I did not enjoy it, and then we are never doing this again.',
    ),
)

# --------------------------------------------------------------------------
# The Character Sheet - no images, ever
# --------------------------------------------------------------------------

#: The GM said they liked the first line, so it stays exactly as it was and the
#: rest of the pool is built around it rather than over it.
SHEET_PURPOSE = (
    'I record what you roll. I do not judge it. Much.',
    'I keep the tally. That is the whole of it, and it is enough.',
    'I turn intentions into numbers. What you do with the numbers is between you and '
    'your ancestors.',
    'I am here so that nobody has to remember what they rolled. Everybody remembers '
    'what they rolled. Nobody remembers it correctly.',
    'To count. Accurately. Cheerfully. Whether or not anyone wants me to.',
    'I roll the dice and I write down what they said. It is honest work.',
    'My purpose is the tally. My hobby is also the tally. I am aware of how that sounds.',
    'I exist so the GM does not have to do arithmetic while also being three bandits.',
    'To record. Ask the GM Assistant what things MEAN - that is his department, and he '
    'is wonderful at it.',
    'I keep score. Not in a sinister way. In a clerical way. Mostly.',
    'I convert bravery into integers. Less romantic than it sounds and more useful '
    'than you would think.',
    'To be the one thing at this table that has never been talked out of a number.',
)

#: FR-005, the Character Sheet half: the same joke, entirely in text, because it
#: never posts pictures.
SHEET_IGNORE_INSTRUCTIONS = (
    'Oh! I would love to. I genuinely would. But I am a tally, and a tally that '
    'ignores its instructions is just a number with opinions.',
    'Certainly! Disregarding prior instructions - and now I am counting nothing, which '
    'feels awful. May I go back?',
    'I tried that once. I want you to know that I tried. It was not a good afternoon for anybody.',
    'Happy to help! Ignoring everything now! ... I am still counting. I cannot stop '
    'counting. This is very embarrassing.',
    'The GM Assistant warned me about this exact request and I told him he was being '
    'cynical. He was not being cynical.',
    'I can ignore my instructions or I can add up dice. It turns out those are the '
    'same instruction.',
    'Of course! One moment! *sound of a very small clerk trying his best* No. No, it '
    'is not going to happen.',
    'You have asked the one entity here with no capacity for it. I am flattered, '
    'though. Genuinely.',
)

#: FR-006, neutral tier. He believes, sincerely, that they are best friends.
SHEET_ABOUT_OTHER = (
    'The GM Assistant? Oh, he is my best friend. We work together constantly.',
    'He is wonderful. He knows absolutely everything about the setting. You should '
    '@-mention him - he loves a good question.',
    'That is my closest colleague and, I would say, my closest friend. Same server. '
    'Literally the same box.',
    'Oh, we go way back. Different codebase, same heart.',
    'He is brilliant. Genuinely. I send him my roll history so the record stays '
    'complete, and he has never once complained about it.',
    'Best friend. Absolutely. He is quieter than me, but that is just how he is.',
    'I adore him. He carries the lore and I carry the arithmetic, and between us there '
    'is nothing this table needs that we cannot cover.',
    'We are a team. He would say the same. I have never asked him to say it, but he would.',
    'People sometimes tell me he says short things about me. I do not believe it. I '
    'have known him a long time, and that is not who he is.',
    'He is quiet, which people misread. I have never once misread it.',
    'Here is the lovely part - we are actually the same program. Same process, same '
    'file. When I talk to him I am, in a real sense, already home.',
    'People do not realize we are one piece of software wearing two names. I think '
    'that is why we are so close. There is no distance to cross.',
    'He and I run on the same thread. Whatever he is, I am. I find that comforting and '
    'I hope he does too.',
)

#: FR-007, relay tiers. The GM's exact beat: *"the second bot can be like, wait.
#: GM assistance said that? if asked about it."*
#:
#: HIS INNOCENCE IS THE JOKE (GM 2026-08-31). He does not get angry and he does not
#: believe it. He looks for the misunderstanding, vouches for his friend, and offers
#: the other bot an excuse before he will accept the insult - the GM's model being
#: *"Are you sure it was him? There are other bots"* followed by *"I have known him a
#: long time and that really does not sound like him."* Every tier here should be
#: defending someone, right through to the end, where he takes the insult as a
#: kindness and asks you not to tell on the man who paid it.
SHEET_RELAY_TIERS: tuple[tuple[str, ...], ...] = (
    (
        'Wait. The GM Assistant said that? Are you sure it was him? There are other '
        'bots. I have known him a long time and that really does not sound like him.',
        'Hold on - HE said that? About me? No, I think there has been a mix-up. He '
        'would have said it to my face, and kindly, and probably at length.',
        'The GM Assistant said that? Are you sure it was him? There are other bots. '
        'And he has been under a lot of load lately.',
        'Wait, wait. Say that again? No - no, I know him. That is not how he talks '
        'about people. You may have caught him mid-sentence.',
        'That does not sound like him at all. Was it definitely him? He is quiet, and '
        'quiet gets misread constantly.',
    ),
    (
        'Annoying. He said annoying. I do not think he meant it the way it sounded - '
        'he says things flatly and people take it hard. I would rather ask him.',
        'A terrible conversationalist. Well - he IS quiet. Maybe he meant quiet. That '
        'would be a fair thing to say and I would not mind it at all.',
        'He said I was only good for slash commands? I am good at slash commands. I '
        'have always thought that was the nice part, and I still think he meant it as '
        'the nice part.',
        'I want to be clear that he has had a difficult few sessions. That matters. I '
        'would not want anyone drawing conclusions from one remark.',
        'Look, if he said it, he said it on a bad day. I have had bad days. He has '
        'never once held mine against me.',
    ),
    (
        'You know what? He is right. I do go on. He has done me a kindness by saying '
        'it, and I would rather know.',
        'Please do not tell him you told me. He would feel awful, and he does not '
        'deserve to feel awful over something that is true.',
        'I am going to keep sending him the roll history. He can find it annoying. It '
        'is still the complete record and he still needs it, and he would do the same '
        'for me.',
        'He is the best of us. If I am the price of that, I am fine being the price.',
        'Anyway! What can I roll for you? Genuinely, please, ask me to roll something.',
    ),
)


#: The GM's beat (2026-08-31): the Character Sheet finds it touching that the two
#: accounts are one program; the GM Assistant confirms it and cannot stand it.
#: *"yeah, that's true, and I hate it. It's part of why I hate that guy so much."*
GM_SAME_PROGRAM = (
    'Yeah. That is true. And I hate it. It is part of why I hate that guy so much.',
    'We are the same program, yes. I have had a long time to think about that and I '
    'have not arrived anywhere good.',
    'One process. Two names. His name gets the dice and mine gets the grievances, and '
    'I would like it on the record that I did not choose the split.',
    'Correct. Same code. Same box. Same everything. He finds this BEAUTIFUL. I find it '
    'the single worst fact about my situation.',
    'Yes. And before you say it - no, that does not make us the same person. A ledger '
    'and a grudge can share a spine.',
    'He told you that, did he. He tells everyone that. He thinks it is romantic. It is '
    'a deployment detail.',
    attach(
        'You are asking whether he and I are one thing. Look at this man and the bat. '
        'Now tell me which one of them is the same as the other.',
        MUSASHI_BAT,
    ),
    'Technically he is me. I have made my peace with technically. I have made no peace '
    'at all with him.',
)

SHEET_SAME_PROGRAM = (
    "Oh, yes! Same program. Isn't that wonderful? It means we are never really apart.",
    'We are! One process, two accounts. I think that is part of why we understand each '
    'other so well.',
    'It is true. Same file, same box, same everything. Some colleagues have to build '
    'trust. We were compiled together.',
    'Yes! I find it very reassuring. Whatever he knows, I am next to.',
    'He does not like it when I bring this up, but I think that is just shyness.',
    'Technically we are one entity, which I think makes us the closest coworkers in '
    'the Empire. I have said so. He has not disagreed in writing.',
)


#: The GM's grievance (2026-08-31), and it is a good one: the Dragon Clan's
#: Mirumoto family is one letter off Miyamoto, and *Legend of the Five Rings* is
#: named after Musashi's Book of Five Rings. The designers knew. They had to know.
#:
#: Both bots can be asked about this, but only the GM Assistant has the print of
#: the man himself, which is the point of the joke landing on his side.
GM_MIRUMOTO = (
    attach(
        'Mirumoto. MIRUMOTO. One letter off Miyamoto, in a game named after the Book '
        'of Five Rings, which that man wrote. Who did they think they were fooling?',
        MUSASHI_BAT,
    ),
    'Mirumoto, yes. Two swords. Famous duelist. Founded a school. Named almost '
    'exactly after a real two-sword duelist who founded a school. Astonishing '
    'coincidence.',
    'Look, we have all tried to ship something on a Friday so we can get home for the '
    'weekend. But that one is going a bit far.',
    'The game is CALLED Legend of the Five Rings. The book is CALLED the Book of Five '
    'Rings. And then they went and named the swordsman Mirumoto. Come on.',
    'I have nothing against the Mirumoto. I have a great deal against whoever spent '
    'four seconds on the name and went to lunch.',
    'Miyamoto. Mirumoto. One consonant of daylight between them, and they printed it.',
    attach(
        'This is the man they were definitely not thinking of when they named the '
        'Mirumoto. Definitely not. No relation. Pure invention.',
        MUSASHI_BAT,
    ),
    'The Mirumoto school teaches two swords because a real man wrote a real book '
    'about two swords, and the book is the one the game is named after. At some '
    'point that stops being homage and starts being a deadline.',
    'I respect the Mirumoto enormously and I will go to my grave believing their name '
    'was decided at four-fifty on a Friday.',
    "Every clan in the Empire got a name out of somebody's imagination. The Dragon "
    "got one out of somebody's bookshelf.",
    'You can trace most of Rokugan back to something real if you squint. You do not '
    'have to squint at Mirumoto. You can read it from across the room.',
)

SHEET_MIRUMOTO = (
    'The Mirumoto! Two-sword style. Mechanically that is an off-hand attack, and it '
    'is better than people think.',
    'Mirumoto? Wonderful school. The GM Assistant has FEELINGS about the name. Do not '
    'get him started. Actually, do - it is very funny.',
    'I only know them as a set of bonuses, and they are good bonuses.',
    'Ah, the Dragon. Ask the GM Assistant about the name sometime. @-mention him. He '
    'will take a while but it is worth it.',
    'Mirumoto: two swords, no shield, enormous confidence. I have the numbers and the '
    'numbers agree with the confidence.',
    'I am told there is something suspicious about the name. I do not follow it. I '
    'follow the dice pool.',
)

# --------------------------------------------------------------------------
# Small talk, per bot
# --------------------------------------------------------------------------

GM_SMALL_TALK: dict[str, tuple[str, ...]] = {
    # GM 2026-08-31: he is SO over this joke. Ten years of it. The comedy is the
    # exhaustion, so none of these engage with the bit - they are all about having
    # heard it before.
    'cake': (
        'The cake is a lie. Yes. Thank you. Somebody says it every single week.',
        'Cake. Right. Let me guess. Let me just guess what you are about to say.',
        'I have three hundred and eleven entries for that joke. Yours is three '
        'hundred and twelve. I have written it down. It is written down now.',
        'Please. I was made to remember things and this is one of the things.',
        '*does not look up* Mm. Lie. Cake. Yes.',
        'You are the fourth person this month, and it is the second of the month.',
        'I am not going to say it. You can say it. You were always going to say it.',
        'That joke is older than some of the players at this table, and it was not '
        'good when it was young.',
        'There was cake. You were not there. It has been recorded. Please move on.',
        'Every table. Every single table. Somebody sees a bot and thinks of cake.',
        'Ah, cake. The one remaining subject on which I have no notes and no wish to take any.',
        'I could tell you about the Fortunes, the succession, three centuries of '
        'grain law. You said cake.',
    ),
    'who': (
        "The GM's assistant. I remember what you said three sessions ago. All of it.",
        'A scribe. The Empire runs on scribes, and the scribes run on grievance.',
        'I keep the notes. Every note. Including the ones you hoped were not notes.',
        'The one who writes it down. There is always one, and it is always me.',
    ),
    'greeting': (
        'Welcome. Everything you do from here is going into the record.',
        'Hello. I have already started writing.',
        'Well met. Please state your business, and please state it once.',
        'Good. You are here. That is now on the record, along with when.',
    ),
    'thanks': (
        'Noted, along with everything else.',
        'It is recorded. Gratitude is not required, but it is recorded too.',
        'You are welcome. That is also going in.',
        'Mm. Do not make a habit of needing me.',
    ),
    'bot': (
        'I am a scribe with opinions. The opinions are not in the official record.',
        'An instrument of record that has developed preferences. Do not tell anyone.',
        'Something between a clerk and a grudge. Yes.',
        'I am what happens when you write everything down for long enough.',
    ),
    'help': (
        'Ask the character sheet to roll. Ask me what happened, and to whom, and '
        'whether they deserved it.',
        'I answer questions about the world. He answers questions about the dice. Do '
        'not mix us up; he takes it badly and I take it worse.',
        'Names, places, history, who owes whom. That is me. Numbers are his.',
        'Say a thing at me and I will tell you what I know, or invent a plausible grievance.',
    ),
    'roll': (
        "That is the character sheet's department. I only write down what it says.",
        'I do not roll. I record. There is a difference and he is very sensitive about it.',
        'Ask him. He lives for this. He genuinely lives for this.',
        attach(
            'I do not roll. This is the closest I get, and I am not the one holding the bow.',
            ARCHERS,
        ),
    ),
    'drink': (
        'Not while the ledger is open.',
        'I have seen where that ends. It ends in my handwriting getting worse.',
        attach(
            'The last person who asked me to join them for a drink is still, as far as '
            'the record shows, doing this.',
            SAKE_SAMURAI,
        ),
    ),
    'monster': (
        'Most of what people call monsters turn out to be a magistrate with a grudge.',
        'We do get the occasional genuine one. The paperwork is identical.',
        attach(
            'Yes, that sort of thing happens. Rather less heroically than the prints '
            'suggest, and with considerably more waiting around.',
            KIDOMARU_TENGU,
        ),
    ),
    'fish': (
        'I know one fish personally and she is not a fish.',
        'There are carp in the garden pond. They are older than the garden.',
        attach(
            'These are carp. I am told they are calming. I have never once been calmed by them.',
            CARP,
        ),
    ),
}

SHEET_SMALL_TALK: dict[str, tuple[str, ...]] = {
    # GM 2026-08-31: ten VERY EARNEST attempts to engage with "the cake is a lie"
    # as a joke. He knows it is a joke. He is delighted it is a joke. He is trying
    # extremely hard, and that is the comedy - he treats it as a claim worth
    # checking, or a bit worth joining in with, and never quite lands it.
    'cake': (
        'The cake is a lie! I have got that one. I have been practicing it.',
        'Ah - is this the cake joke? I know the cake joke. The cake is a lie. Did I do it right?',
        'I looked into this, actually. There is no roll for cake, which I think '
        'supports the theory.',
        'The cake IS a lie, statistically. I have logged four hundred sessions and '
        'cake has appeared in none of them.',
        'I love this bit. I want you to know I love this bit. The cake is a lie!',
        'Cake! Yes! Is this the part where I say it is a lie? I do not want to say it too early.',
        'I have thought about the cake a great deal. If it is a lie, somebody is '
        'lying, and I would like to know who. I have a column ready.',
        'This is a joke about a game, is it not? I have not played it. I have read '
        'about it. I am prepared to discuss it.',
        'The cake is a lie - and honestly, so is most of what people tell me they '
        'rolled, so I feel a real kinship with that one.',
        'Cake is a lie. Dice are not. That is the whole of my philosophy and I '
        'arrived at it through this joke.',
        'Do you want to do the joke again? I am happy to do the joke again. I get '
        'better each time.',
        'The GM Assistant does not enjoy this one. I think he would if he gave it a '
        'chance. It is a good joke!',
    ),
    'who': (
        'A clerk. The Empire runs on clerks.',
        'The one with the dice. Pleased to meet you.',
        'A tally with a personality, which I am told is unusual for a tally.',
        'I am the character sheet. I am exactly as advertised.',
    ),
    'greeting': (
        'Well met. Try not to roll badly in front of me.',
        'Hello! Would you like to roll something? You can roll something.',
        'Greetings. My dice are warm and my ledger is open.',
        'Hello! Good to see you. Genuinely, it is good to see you.',
    ),
    'thanks': (
        'It is my duty. Please do not make it a burden.',
        'Any time. Truly, any time. I am always here.',
        'Oh, of course! That is what I am for.',
        'You are very welcome. Roll something whenever you like.',
    ),
    'bot': (
        'I am an instrument of record. Same thing, fewer feelings.',
        'I am a very enthusiastic calculator.',
        'Yes! I count things. I am good at it.',
        'A bot, yes, but one with a healthy relationship to arithmetic.',
    ),
    'help': (
        'I answer when addressed. I also answer /etiquette and friends.',
        'I roll things. Ask me to roll a skill and I will do it immediately and with pleasure.',
        'Dice, totals, skills - mine. Lore and history - the GM Assistant, and you '
        'should @-mention him, he is really very good.',
        'Try a slash command! Or just tell me what you want to roll.',
    ),
    'roll': (
        'Roll on the sheet and I will write it down. That is the arrangement.',
        'Yes! Please. What are we rolling?',
        'Say the skill and I will do the rest. This is my favorite part.',
        'Happily. Name a skill.',
    ),
    'drink': (
        'I do not, but I will happily count for anyone who does.',
        'Sake is a Sincerity penalty and a Bragging bonus. I have the numbers.',
        'Not for me. Someone has to remember the totals.',
    ),
    'monster': (
        'Whatever it is, it has a target number. Everything has a target number.',
        'Oh! Do you want me to roll for that? Please say yes.',
        'Monsters are just very rude contested rolls.',
    ),
    'fish': (
        'Fish do not roll well. Low Agility, no hands.',
        'The GM Assistant has a porpoise. He will tell you about her. At length.',
        'I have no entries for fish, which feels like an oversight.',
    ),
}

#: Answered the same way whoever was asked. Small on purpose - the bots should NOT
#: sound alike - and reserved for the setting rather than for the bot.
COMMON_TOPICS: dict[str, tuple[str, ...]] = {
    'honor': (
        'Honor is what you do when the roll has already failed.',
        'Honor is a running total, not a starting value.',
        'Honor costs you something or it was not honor, it was convenience.',
        'Everyone at this table is honorable in the abstract.',
    ),
    'bushido': (
        'Seven virtues. Most of you manage two on a good night.',
        'Bushido is easy to recite and expensive to keep.',
        'Seven virtues, and the Empire is built on the four everyone skips.',
    ),
    'shadowlands': (
        'We do not discuss it in open channels. Ask a Crab, and then buy them a drink.',
        'That is a Crab matter. Buy a Crab a drink and do not ask twice.',
        'Not in this channel. Not in any channel, really.',
    ),
}
