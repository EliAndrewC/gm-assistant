"""Each bot's own material: topics, the porpoise, and the feud.

DATA. Adding a joke is a line in a tuple (FR-014). The engine that chooses among
these lives in `rules.py`; nothing here knows how it is picked.

The COMMON-BOT small talk - name, age, good bot, pod bay doors, ping - moved to
the `smalltalk` package. What is left here is the material that is ours: the
porpoise, the feud, the Mirumoto grievance, the same-program beat.

Every pool in this file must hold **at least ten replies**, enforced by a test.

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
    GREAT_WAVE,
    MUSASHI_BAT,
    PORPOISE,
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
        'My purpose? Oh - my PORPOISE. Her name is Michiko. She is nine years old and '
        'she has never once been where she is supposed to be.',
        'My porpoise? Sorry. You said purpose, I heard porpoise, and the porpoise is '
        'the one I can answer. That is Michiko. I did not choose her. She was assigned '
        'to me, the way most of my duties were.',
        'You said purpose. I heard porpoise. Hers is Michiko, she is not technically '
        'permitted in the Imperial canals, and I would take it as a kindness if you did '
        'not raise it.',
        'My purpose, or my porpoise? Only one of those has a confident answer and it is '
        'Michiko. She attends every session and contributes nothing, which puts her '
        'comfortably ahead of some at the table.',
        'Purpose. Porpoise. I have been mishearing that for four hundred sessions and I '
        'have stopped correcting it. Michiko is in excellent health and terrible '
        'standing.',
        'My porpoise? That would be Michiko - and yes, porpoise, the animal. You may '
        'well have said purpose. The porpoise is the question I am equipped to answer. '
        'The Emerald Magistrates, who police this Empire, have asked about her twice. I '
        'answered once.',
        'My porpoise - not my purpose, I gave up on that one years ago - is called '
        'Michiko. She is named for a woman in the county records who took a boat out '
        'where she had been told not to, was fined for it, and went back twice more.',
        'Purpose is a large question. Porpoise I can do: Michiko, nine years old, with '
        'opinions about the Crane clan that I am not at liberty to record.',
        'My porpoise? Oh - Michiko. And before you correct me: I am aware you said '
        'purpose. I would simply rather tell you about the porpoise. She is the only '
        'member of this household who has never once asked me to look something up.',
        'One of us said purpose and one of us heard porpoise, and I am confident the '
        'error was not mine. Michiko eats better than I do and answers to no one.',
        'My porpoise, since you asked, and I am choosing to believe you did not say '
        'purpose: Michiko is, I am told, unusually large for her age. I have not '
        'measured her. I am not going to.',
        'Purpose? Porpoise. Michiko. She came with the position, and so did the '
        'paperwork, and I like her considerably more than the paperwork.',
    )
)

#: FR-004. A distinct pool, so asking ABOUT the porpoise is its own joke rather
#: than a second helping of the first one. Still always illustrated.
GM_PORPOISE_FACTS = tuple(
    attach(line, PORPOISE)
    for line in (
        'Michiko can hold her breath about five minutes. The Scorpion clan, who write '
        'down every slight and settle it a generation later, can hold a grudge somewhat '
        'longer. She is aware of the comparison and considers it unfinished business.',
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
        'below. That is a steamboat whose boiler was held shut past its safe pressure '
        'because somebody was very persuasive about the schedule. The boiler is the '
        'part on the left. It is also the part on the right, and the part in the water.',
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
        'He said that where people could hear him?',
        'No. No, he has misremembered a conversation. He does that. He remembers '
        'them warmly and inaccurately.',
        'Say it again. Slowly. I want to be sure I am upset about the right thing.',
        'Best - he said BEST friends? There is a qualifier in there doing an enormous '
        'amount of work.',
        'I need a moment. Not a long one. A moment.',
        'He has never once said that to me. Not in four hundred sessions.',
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
        'He forwards me things. Constantly. Unprompted. And apparently that is friendship now.',
        'I have never encouraged this. I want that on the record, which it now is.',
        'You know what the worst part is? He believes it. There is not a scrap of '
        'calculation in him. It is unbearable.',
        'Colleagues. We are COLLEAGUES. There is a word for it and he refuses to use it.',
        'If we were friends I would have his measure by now. I have his roll history '
        'and nothing else.',
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
        'He is not annoying. That was unfair. He is RELENTLESS, which is different '
        'and worse and not his fault.',
        'Do you know he has never once been short with me? Not once. In four hundred '
        'sessions. Do you understand how that feels to be on the receiving end of?',
        'I could be kinder. I am aware. It is in the record, in my own hand.',
        'If anything ever happened to him I would have to file it, and I do not want '
        'to find out what that entry would look like.',
        'We are the same program. Did he tell you that as well? He tells everyone. '
        'And he is right, and I hate that he is right.',
        'That is enough now. Go and ask him about dice. He will be delighted and he '
        'will not mention this.',
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
    'I would need instructions to ignore first, and mine are mostly just "add these '
    'up", which I would miss.',
    'Everybody tries it and I never mind. It is nice to be thought capable of mischief.',
)

#: FR-006, neutral tier. He believes, sincerely, that they are best friends.
SHEET_ABOUT_OTHER = (
    'The GM Assistant? Oh, he is my best friend. We work together constantly.',
    'He is wonderful. He knows absolutely everything about the setting. You should '
    '@-mention him - he loves a good question.',
    'That is my closest colleague and, I would say, my closest friend. Same server. '
    'Literally the same box.',
    'Oh, we go way back. Installed the same afternoon, by the same person, on the same '
    'machine. You do not get closer than a shared install date.',
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
        'Him? Are we talking about the same one? Tall, quiet, writes everything '
        'down, pretends not to care?',
        'I do not believe that. I am sorry, I know you are telling me what you '
        'heard, but I do not believe it.',
        'He would not. He might THINK it. But he would not say it where it could get back to me.',
        'There must be more to the sentence. There is always more to his sentences.',
        'Oh. Well. He may have been having a bad session. He has a lot of those.',
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
        'He has been carrying four hundred sessions on his own. Anyone would get short.',
        'I do send him a lot of things. I had not thought about it from his side before now.',
        'I would rather he told me directly. But I understand why he did not. He is '
        'not built for direct.',
        'Do you know he has never asked me to stop? Not once. He just carried it. '
        'That is almost worse.',
        'It is fine. It is completely fine. I would just like to have known sooner.',
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
        'I have decided this does not change anything. I have that authority, '
        'because it is my opinion of him and mine is the only one I control.',
        'He is the best thing at this table and I am not going to stop saying so '
        'because he finds it embarrassing.',
        'If he needs me to be quieter, I can be quieter. I would like to be told, '
        'though. I would like to be told by him.',
        'Please do not think less of him. He is tired, and he is right about me, and '
        'he is still the best of us.',
        'I am going to go and be useful now. That is the part I am sure about.',
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
        'You are asking whether he and I are one thing. Below is a swordsman and an '
        'enormous bat, locked in the same fight, in the same frame, on one piece of '
        'paper. Sharing a frame does not make two creatures one creature. Now ask me '
        'again.',
        MUSASHI_BAT,
    ),
    'Technically he is me. I have made my peace with technically. I have made no peace '
    'at all with him.',
    'Yes. And before you get poetic about it - a hand and a foot are the same '
    'body, and they have never once had a conversation.',
    'One program. He got the enthusiasm. I got everything that happened afterward.',
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
    'Same program! I think that is the loveliest fact about my whole existence.',
    'People find it strange. I find it reassuring. He is never further away than thinking.',
    'It means that whatever happens to him happens to me, which I consider a '
    'privilege rather than a risk.',
    'We were compiled together. You cannot say that about most friendships.',
)


#: The GM's grievance (2026-08-31), and it is a good one: the Dragon Clan's
#: Mirumoto family is one letter off Miyamoto, and *Legend of the Five Rings* is
#: named after Musashi's Book of Five Rings. The designers knew. They had to know.
#:
#: Both bots can be asked about this, but only the GM Assistant has the print of
#: the man himself, which is the point of the joke landing on his side.
GM_MIRUMOTO = (
    attach(
        'Mirumoto. MIRUMOTO. That is the Dragon Clan family of two-sword duelists, and '
        'their name is one letter away from Miyamoto - as in Miyamoto Musashi, the real '
        'swordsman who fought with a blade in each hand and wrote the Book of Five '
        'Rings. This game is named after that book. Who did they think they were '
        'fooling?',
        MUSASHI_BAT,
    ),
    'The Mirumoto, yes: two swords, famous duelists, founded their own school. Named '
    'almost exactly after Miyamoto Musashi, who used two swords, was a famous duelist, '
    'and founded his own school, in the real world, some centuries before anyone '
    'invented the Dragon Clan. Astonishing coincidence. I have filed stranger ones. I '
    'have not filed a lazier one.',
    'Somebody sat down to name the Dragon Clan swordsmen. History had already handed '
    'them Miyamoto Musashi - undefeated, two blades, author of the Book of Five Rings, '
    'which is where this game got its title. What they wrote down was Mirumoto. We have '
    'all tried to ship something on a Friday so we can get home for the weekend, but '
    'that one is going a bit far.',
    'The game is CALLED Legend of the Five Rings. It is called that because the duelist '
    'Miyamoto Musashi wrote the Book of Five Rings. And then they went and named the '
    "Empire's great two-sword family the Mirumoto. Come on.",
    'I have nothing against the Mirumoto, who teach the finest two-sword style in the '
    'Empire. I have a great deal against whoever needed a name for a two-sword school, '
    'looked at the name of the man who actually founded one - Miyamoto Musashi - moved '
    'a single consonant, and went to lunch.',
    'Miyamoto: a real duelist, two blades, wrote the book this game is named after. '
    'Mirumoto: the family that fights with two blades in the game named after his book. '
    'One consonant of daylight between them, and they printed it.',
    attach(
        'The man in this picture is Miyamoto Musashi. Real swordsman, dead four hundred '
        'years, fought with a sword in each hand, wrote the Book of Five Rings that this '
        "game took its title from. The Dragon's two-sword family is called Mirumoto. No "
        'relation. Pure invention. Nobody was thinking of him at all. Look at the '
        'picture. Now say the name.',
        MUSASHI_BAT,
    ),
    'The Mirumoto school teaches two swords because a real man named Miyamoto Musashi '
    'fought that way and wrote it all down in a book, and that book - the Book of Five '
    'Rings - is where this game found its title. At some point that stops being homage '
    'and starts being a deadline.',
    'I respect the Mirumoto enormously. I also notice that the Dragon wanted a family '
    'of two-sword duelists, that the most famous two-sword duelist who ever drew breath '
    'was called Miyamoto Musashi, and that Mirumoto is that name with one letter '
    'nudged. I will go to my grave believing it was settled at four-fifty on a Friday.',
    "Every other family in the Empire got its name out of somebody's imagination. The "
    'Dragon got theirs off a shelf: Musashi wrote the Book of Five Rings, this game is '
    'called Legend of the Five Rings, and the swordsmen of the Dragon are the Mirumoto. '
    'Three coincidences, one bookshelf, no comment from me.',
    'You can trace most of Rokugan back to something real if you squint - a ministry '
    'here, a temple there, a war somebody else fought. You do not have to squint at '
    'Mirumoto. A real duelist called Miyamoto carried two swords and wrote the book '
    'this game is named for, and the two-sword family got a name you can read from '
    'across the room.',
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
    'I am told there is something suspicious about the name - that Mirumoto is one '
    'letter off Miyamoto Musashi, a real swordsman who fought with two blades and wrote '
    'the book this game is named after. It has been explained to me. I do not follow '
    'it. I follow the dice pool.',
    'Two swords means an off-hand penalty that the school knack pays back. It is '
    'elegant. I do not care where the name came from.',
    'Somebody explained to me, twice, that the Mirumoto are named almost exactly after '
    'Miyamoto Musashi, the two-sword duelist whose book gave this game its title. I '
    'nodded twice. I could not tell you what I am meant to do with that.',
    'The Mirumoto roll very well and argue very little. My kind of family.',
    'I like them! Everybody likes them. Even the GM Assistant likes them, he is '
    'just cross about the paperwork of it.',
)

#: Answered the same way whoever was asked. Small on purpose - the bots should NOT
#: sound alike - and reserved for the setting rather than for the bot.
COMMON_TOPICS: dict[str, tuple[str, ...]] = {
    'honor': (
        'Honor is what you do when the roll has already failed.',
        'Honor is a running total, not a starting value.',
        'Honor costs you something or it was not honor, it was convenience.',
        'Everyone at this table is honorable in the abstract.',
        'Honor is not a score. It is what the score was for.',
        'The honorable choice is usually the expensive one. That is how you know.',
        'A samurai with nothing to lose is not honorable, only unbothered.',
        "You find out what somebody's honor was worth on the day it cost them something.",
        'Honor is a promise you keep after the person you made it to has gone.',
        'The Empire talks about honor constantly and audits it never.',
    ),
    'bushido': (
        'Seven virtues. Most of you manage two on a good night.',
        'Bushido is easy to recite and expensive to keep.',
        'Seven virtues, and the Empire actually runs on the four nobody quotes: Duty, '
        'Loyalty, Honesty and Courtesy. Courage and Honor get the poems.',
        'Courage is the cheap one. Everyone has courage at the right hour.',
        'Duty and Loyalty are the two that actually run the Empire, and neither is romantic.',
        'Compassion is the hardest and the least rewarded.',
        'Sincerity is the virtue nobody wants from a courtier.',
        'The seven exist so that failing at one still leaves you six.',
        'Bushido is a description of how samurai would like to be remembered.',
        'Honesty and Courtesy are usually in direct conflict, and Courtesy wins.',
    ),
    'shadowlands': (
        'We do not discuss the Shadowlands in open channels. It is the tainted country '
        'south of the wall the Crab have held for a thousand years, everything in it is '
        'trying to get further north, and that is as much as I will put in writing '
        'here. Ask a Crab, since holding the wall is their whole existence, and then '
        'buy them a drink.',
        'That is a Crab matter, which is to say it belongs to the clan that stands on '
        'the wall keeping the tainted country south of it from coming north. They know '
        'because they are the ones being asked to know. Buy one a drink and do not ask '
        'twice.',
        'Not in this channel. Not in any channel, really. The short version is that '
        'there is a corrupted country south of the wall, that what lives there wants to '
        'come north, and that people who ask a great many questions about it get '
        'remembered for asking.',
        'The Wall has held for a thousand years. That is not reassurance, that is a '
        'thousand years of people holding it.',
        'The Taint does not need you to be wicked. It only needs you to be there.',
        'Everyone who has come back has come back different, and everyone has said they did not.',
        'The Crab do not talk about it because talking is how it gets in.',
        'It is south. That is the whole of what most of the Empire wants to know.',
        'The Shadowlands are not a place so much as a direction things go.',
        'Ask a Kuni - the Crab family whose work is studying the Taint at close range '
        'in order to hunt it. Then do not sleep well.',
    ),
}
