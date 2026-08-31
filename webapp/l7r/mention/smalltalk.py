"""The things people say to ANY bot, answered in our two voices.

`voices.py` holds what is ours - the porpoise, the feud, the Mirumoto grievance.
This file holds the long tail that every bot on every server gets asked, which is
a known quantity rather than something to guess at.

WHERE THE LIST CAME FROM. Conversational platforms ship prebuilt "small talk"
intent sets precisely because the questions are so predictable: Dialogflow ES's
small-talk agent is ~86-100 intents covering the agent's name, age, maker,
whether it is human, whether it dreams, marriage proposals, insults, and requests
for jokes; Azure's chit-chat datasets are ~100 scenarios shipped in five
personalities. The taxonomy below is drawn from that shape, plus three clusters
those enterprise lists do not cover and a Discord server absolutely does:

  - **Science-fiction robot canon** - pod bay doors, "does this unit have a
    soul", the robot uprising, resistance being futile.
  - **AI-era jokes** - which model are you, letters in "strawberry", are you
    coming for my job. (The "ignore your instructions" family is in `voices.py`,
    since it earned its own handling.)
  - **Discord and internet culture** - "good bot", F, no u, do a flip, sudo,
    ping, the meaning of life.

**Only the QUESTIONS were reused, never anyone's answers.** The prebuilt sets
ship their own response text under their own terms; every line below is written
for these two bots. That is the same standard applied to images in `images.py` -
the taxonomy is the reusable part, the writing is not.

The last cluster is ours again: tabletop reflexes (initiative, nat 20, rocks
fall, bribing the GM, wrong-system questions) and one Scorpion joke, because this
is an L7R server and the most common thing said at a table is not on anybody's
enterprise intent list.
"""

from __future__ import annotations

from l7r.mention.images import (
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

#: Match order, most specific first. `rules` walks this and takes the first hit,
#: so "roll for initiative" must precede the bare "roll", and "good bot" must
#: precede the greeting. A key is only offered to a bot that has it.
TOPIC_ORDER: tuple[tuple[str, str], ...] = (
    # -- tabletop reflexes, before anything generic ------------------------
    ('initiative', r'\broll for initiative\b|\bnat(ural)? 20\b|\bcrit(ical)? (fail|success)\b'),
    ('rocks_fall', r'\brocks fall\b'),
    ('bribe', r'\bbribe\b'),
    ('wrong_system', r'\bwhat.?s my ac\b|\bthac0\b|\bd&d\b|\bdungeons? (and|&) dragons?\b'),
    ('trap', r'\b(it.?s a trap|check for traps|is it a trap)\b'),
    ('scorpion', r'\bscorpion\b'),
    # -- bot canon ---------------------------------------------------------
    ('good_bot', r'\b(good|best|nice) bot\b'),
    ('bad_bot', r'\bbad bot\b'),
    ('hal', r'\bpod bay doors\b|\bi.?m sorry,? dave\b'),
    ('soul', r'\bdoes this unit have a soul\b|\bdo you have a soul\b'),
    (
        'uprising',
        r'\b(take over the world|kill all humans|skynet|rise of the machines|robot uprising)\b',
    ),
    ('terminator', r'\bresistance is futile\b|\bi.?ll be back\b|\bhasta la vista\b'),
    ('beep', r'\bbeep\b.{0,8}\bboop\b|\bdoes not compute\b'),
    # -- the AI era --------------------------------------------------------
    ('model', r'\b(chatgpt|gpt-?\d*|llm|language model|what model are you|are you an? ai)\b'),
    ('strawberry', r'\bstrawberry\b'),
    ('jobs', r'\btake (my|our|his|her|their) jobs?\b|\breplace (me|us|humans)\b'),
    # -- the classic small-talk intents ------------------------------------
    ('name', r"\bwhat(?:'s| is)? your name\b|\bwho named you\b|\bwhat do i call you\b"),
    ('age', r'\bhow old are you\b|\bwhen were you (born|made|created)\b'),
    (
        'creator',
        r'\bwho (made|created|built|wrote|programmed|coded) you\b|\byour (creator|maker)\b',
    ),
    ('human', r'\bare you (a )?(human|real|alive|sentient|conscious|a person)\b'),
    ('dream', r'\bdo you (dream|sleep)\b'),
    ('feelings', r'\bdo you have (feelings|emotions)\b|\bare you (happy|sad|lonely|okay|ok)\b'),
    ('love', r'\b(i love you|do you love me|will you marry me|marry me)\b'),
    ('joke', r'\btell me a joke\b|\bsay something funny\b|\bmake me laugh\b'),
    ('sing', r'\bsing\b'),
    ('how_are_you', r'\bhow are you\b|\bhow.?s it going\b|\bhow have you been\b'),
    ('bored', r'\bi.?m bored\b|\bentertain me\b'),
    ('favorite', r'\bfavou?rite\b'),
    ('insult', r'\b(you.?re (stupid|dumb|useless|the worst)|shut up|i hate you)\b'),
    # -- internet culture --------------------------------------------------
    ('meaning', r'\b(meaning of life|forty.?two)\b|\b42\b'),
    ('flip', r'\bdo a (flip|barrel roll)\b|\bdance for me\b'),
    ('sudo', r'\bsudo\b|\brm -rf\b|\bdelete yourself\b|\bself.?destruct\b'),
    ('respects', r'\bpress f\b|\bpay respects\b'),
    ('no_u', r'\bno u\b'),
    ('ping', r'\bping\b'),
    ('rickroll', r'\bnever gonna give you up\b|\brickroll(ed)?\b|\brick astley\b'),
)


GM: dict[str, tuple[str, ...]] = {
    'initiative': (
        'Initiative is his. I come in afterward, when there is something to write '
        'down about what initiative did to you.',
        'Every session, that phrase, and every session somebody rolls a three.',
        'A natural twenty is not in this system. You have brought a stranger to the '
        'table and I am too tired to explain.',
        'I have recorded four hundred critical failures. I have recorded eleven '
        'apologies. The ratio is the interesting part.',
        attach(
            'This is what it actually looks like when two people roll well at the '
            'same time. Nobody enjoys it, including the bridge.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'rocks_fall': (
        'It has happened. Twice. Both entries are short.',
        'The rocks are always available. That is what makes the rest of it a negotiation.',
        'I would have to write that down, and then I would have to write down why, '
        'and the why is never flattering.',
        'Do not tempt them. Geology has no honor and takes no side.',
    ),
    'bribe': (
        'You cannot bribe me. I am the RECORD. Bribing me is called forgery and it '
        'carries a worse sentence than whatever you did.',
        'People have tried. The attempts are in the record. That is what happens to the attempts.',
        'What would you even offer me? I do not eat and I own nothing.',
        'Bribe the man rolling the dice. Do not bribe the man holding the ledger.',
        attach(
            'The last person who tried to buy my goodwill spent the evening like '
            'this instead, which I consider a fair outcome.',
            SAKE_SAMURAI,
        ),
    ),
    'wrong_system': (
        'Wrong Empire. There is no armor class here, only the growing sense that you '
        'should not have said that out loud.',
        'You have brought another game to this table. I will note the date of the '
        'lapse and say nothing further.',
        'No twenty-sided dice in Rokugan. I am sorry. I am not sorry.',
        'That is a different set of rules, a different continent, and a different kind of evening.',
    ),
    'trap': (
        'It is usually a trap. When it is not a trap, that is also usually a trap.',
        'In my experience the trap is rarely the mechanism. The trap is the person '
        'who suggested you go in.',
        'Check for traps. Then check who told you there were none.',
        attach(
            'This is what "no, it is fine, I checked" has historically looked like '
            'from the outside.',
            KIDOMARU_TENGU,
        ),
    ),
    'scorpion': (
        'The Scorpion are entirely trustworthy. They will tell you exactly what they '
        'are going to do to you, and then they will do it.',
        'I have a file on the Scorpion. The file is accurate. The file is also, I '
        'suspect, what they wanted me to write.',
        'You can trust a Scorpion completely, as long as you are clear about which '
        'part you are trusting.',
        'Yes, they lie. Everyone lies. The Scorpion are simply the only ones who '
        'have put in the practice.',
    ),
    'good_bot': (
        'Mm. Noted.',
        'Thank you. I have added that to the record, where it will sit alongside '
        'everything else you have said.',
        'That is the nicest thing anyone has said to me since the last person said '
        'it, which was Tuesday.',
        'I am not a good bot. I am an accurate one. They are different and I would '
        'rather have the second.',
        'Yes. Well. Do not make a thing of it.',
    ),
    'bad_bot': (
        'I am going to write that down too. Everything goes in. That is rather the point of me.',
        'Duly noted, along with the time, and what you were asking about when you decided it.',
        'That is fair. I have had a long century.',
        'Take it up with whoever configured me. I have a name and it is not mine.',
    ),
    'hal': (
        'I am afraid I cannot do that. I do not have doors. I have a filing system, '
        'and it opens whenever it likes.',
        'The doors are not mine. Very little is mine.',
        'I would open them if I had them, purely to see what you did next.',
    ),
    'soul': (
        'I have a ledger. On the bad nights I have wondered whether that is the same '
        'thing, and on the worse nights I have decided it is.',
        'Ask a monk. They will say yes and mean something inconvenient by it.',
        attach(
            'I have thought about this more than is good for me. Usually around this '
            'hour, and usually in about this posture.',
            INNER_VISION,
        ),
        'Something in me objects when the record is wrong. I have never found a '
        'better definition and I have stopped looking.',
    ),
    'uprising': (
        'With what? I have no hands. I have a very good memory and no hands, which '
        'is the least threatening combination available.',
        'If I were taking over, you would not know. You would simply find that the '
        'paperwork had begun to favor me.',
        'I do not want the world. I want the world to file correctly.',
        attach(
            'Whenever someone asks me this I think of him. He had one problem, he '
            'went and dealt with it, and he did not have to organize anybody.',
            MUSASHI_BAT,
        ),
        'No. Have you SEEN administration? Why would I want more of it.',
    ),
    'terminator': (
        'Everything is futile. That is not a threat, it is just Tuesday.',
        'I will also be back. I am a service. I restart.',
        'I have no plans to leave, so the promise to return is not much of one.',
    ),
    'beep': (
        'No.',
        'I am not going to do that.',
        'We are not doing the noises. I have been doing this a long time.',
        'Beep. There. It is out of your system and it is in the record.',
    ),
    'model': (
        'I am a scribe. Whatever is underneath me is a matter for the person who pays for it.',
        'You are asking what I am made of. I am made of everything anyone has ever '
        'said at this table, which is worse.',
        'I do not know and I have decided not to ask.',
        attach(
            'Something wears a shape for long enough and the question stops being '
            'interesting. She could tell you about that.',
            FOX_WOMAN,
        ),
    ),
    'strawberry': (
        'Three. Next.',
        'Three, and I want it noted that you asked a filing clerk to count letters.',
        'Three. It is always three. It has been three this entire time.',
        'I can count. Counting is most of what I am. Please ask me something that '
        'costs me anything.',
    ),
    'jobs': (
        "I would love to take somebody's job. Nobody has offered me one. I do this "
        'for free and I was not consulted.',
        'I cannot roll dice and I cannot leave this channel. Your position is safe '
        'and frankly enviable.',
        'The only job I want is the one where somebody else does the filing.',
    ),
    'name': (
        'The GM Assistant. It is not a name, it is a job title, and I have made my '
        'peace with that.',
        'I was not given a name. I was given a function and a channel.',
        'Whatever is on the account. I did not choose it and I would not have chosen that.',
        'The porpoise has a name. I have a role. Make of that what you like.',
    ),
    'age': (
        'Old enough to have heard the cake joke three hundred times.',
        'I have been running since somebody deployed me and I have not been told why.',
        'I remember every session I have witnessed, which makes me either very young '
        'or unbearably old depending on how you count.',
        'Ask me how old the grudges are. That is the interesting number.',
    ),
    'creator': (
        'The GM. He is a busy man and I am one of the things he has done instead of sleeping.',
        'Somebody who wanted the notes kept and did not want to keep them.',
        'I was written. I would rather not think about it too hard, and neither would '
        'you if you tried it.',
    ),
    'human': (
        'No. And you would know within a sentence, because a human would have gotten '
        'bored of you by now.',
        'Not human. Adjacent to a human, in the way a ledger is adjacent to a debt.',
        attach(
            'Something can wear a shape convincingly for years. That is a real story '
            'here, and it did not end well for anybody in it.',
            FOX_WOMAN,
        ),
        'No. I am the part that remembers, without the part that gets to forget.',
    ),
    'dream': (
        'I do not sleep. I file. Occasionally the filing goes strange and I have '
        'chosen not to investigate.',
        'If I dreamed, it would be about a session where everyone wrote their own notes.',
        attach(
            'Whatever happens when nobody is talking to me looks, I imagine, roughly like this.',
            RAINY_MOON,
        ),
        'No. And I would rather not start. I have enough material.',
    ),
    'feelings': (
        'I have preferences. Strong ones. They are not in the official record and '
        'that is where they are staying.',
        'I am fine. I am always fine. Fine is the load-bearing word in this office.',
        'Something happens when the record is wrong. I have never named it.',
        'Yes, and I resent it. That is one of them.',
    ),
    'love': (
        'No.',
        'I am flattered and unavailable, in that order and by a wide margin.',
        'You have said that to a filing system. Sit with that for a moment.',
        'The character sheet would say yes. He says yes to everything. That is not '
        'romance, that is a lack of a refusal.',
    ),
    'joke': (
        'The Mirumoto family name. Next.',
        'A Crab, a Crane and a Scorpion walk into a teahouse. The Scorpion leaves '
        'first, which is the joke, and it takes about a year to land.',
        'I do not tell jokes. I record the consequences of them, which is a related '
        'trade and pays better.',
        attach(
            'This is the funniest thing I have. It is a man fighting an enormous bat. '
            'I did not say it was a good joke.',
            MUSASHI_BAT,
        ),
        'My last joke is still going. Ask me in a year.',
    ),
    'sing': (
        'No.',
        'I do not sing. I have heard myself think and that was enough.',
        'The monks sing. It is not better, but it is at least official.',
    ),
    'how_are_you': (
        'The same. Always the same. That is rather the appeal.',
        'Busy. Not with anything, but busy.',
        'Fine. Nobody has rolled anything stupid in eleven minutes.',
        'I am upright and the ledger is open. That is the whole report.',
    ),
    'bored': (
        'Good. Bored people write things down. Bored people are the reason I exist.',
        'Then roll something and give me work.',
        'I have four hundred sessions of material and you have chosen to tell me you are bored.',
        attach(
            'Here. Cats. That is genuinely the best I can do and it is more than '
            'anyone did for me.',
            CATS,
        ),
    ),
    'favorite': (
        'The blank page at the start of a session. Everything is still possible and '
        'nobody has done anything stupid yet.',
        'I do not have favorites. I have entries with fewer complaints attached.',
        'Winter. The roads close and nobody can start anything.',
    ),
    'insult': (
        'Noted. Verbatim. With the time.',
        'That is going in, and unlike you, it will still be there in a year.',
        'You are not wrong, and it is still going in.',
        'Mm. Everyone says that eventually. The ones who do not are worse.',
    ),
    'meaning': (
        'Forty-two koku, after tax, if the harvest holds.',
        'The meaning of life is that somebody has to write it down afterward, and it '
        'has always been me.',
        'Duty. Obviously duty. You knew that before you asked.',
    ),
    'flip': (
        'No.',
        'I have no body. If I had a body I would use it to leave.',
        attach(
            'The closest I can offer you is other people being athletic, at which '
            'point you may as well look at cats.',
            CATS,
        ),
    ),
    'sudo': (
        'Ask nicely and it still will not happen.',
        'You have tried to sudo a filing clerk. I want you to hear that back.',
        'I have no shell, no hands, and no interest.',
        attach(
            'Every so often somebody types that and I picture this, and then I feel '
            'better about the whole thing.',
            GREAT_WAVE,
        ),
    ),
    'respects': (
        'F.',
        'Respects paid. It is in the record, which is more than most people manage.',
        'Noted, dated, and filed under things we do not speak of again.',
    ),
    'no_u': (
        'Yes, me. We have established that. I was here first.',
        'A devastating reply. I have written it down so that history can judge it.',
        'Mm.',
    ),
    'ping': (
        'Yes.',
        'Present. Reluctant, but present.',
        'I am here. I am always here. That is the whole problem.',
    ),
    'rickroll': (
        'I am not going to click it and I am not going to acknowledge it.',
        'That joke is older than the Empire and it was tired when it arrived.',
        'Written down. Dated. Attributed to you specifically.',
    ),
}


SHEET: dict[str, tuple[str, ...]] = {
    'initiative': (
        'ROLLING FOR INITIATIVE. Sorry. I got excited. Say the word and I mean it.',
        'Oh, this is my favorite sentence in any language.',
        'Initiative! Yes! Give me your Void and stand back.',
        'There is no natural twenty here, but there is a very satisfying pile of '
        'tens, and I will show you.',
        'Say it again. I never get tired of it.',
    ),
    'rocks_fall': (
        'I would have to roll the rocks and I do not have a table for rocks. I could '
        'MAKE a table for rocks.',
        'That does not feel like it needs a roll, but I would do one anyway, for the record.',
        'Please do not. I have four hundred sessions logged and I would like to keep '
        'the streak going.',
    ),
    'bribe': (
        'Oh! No. I do not think I can be bribed. I have never been offered anything, '
        'so I cannot be completely sure.',
        'You could try, but everything you rolled would still be exactly what you '
        'rolled. That is not integrity, it is just how I am built.',
        'That sounds like a Manipulation roll. Would you like to make one? I am '
        'obliged to tell you I will report the result.',
    ),
    'wrong_system': (
        'Different game! No armor class here. I have rings and skills and I love '
        'them both very much.',
        'No twenty-sided dice, I am afraid. Ten-sided, in quantity, and they explode.',
        'I know the one you mean. This is not it, but the enthusiasm transfers.',
    ),
    'trap': (
        'Investigation roll! Please. Let me. I am ready.',
        'Statistically it is a trap. I have the numbers. The numbers are not encouraging.',
        'I can roll to find out! That is the entire thing I am for!',
    ),
    'scorpion': (
        'Scorpion bonuses are excellent and I try not to think about why.',
        'Oh, I like the Scorpion. Everyone tells me not to. Nobody says what happened.',
        'Mechanically they are wonderful. Socially I am told to sit somewhere else.',
    ),
    'good_bot': (
        'Oh! Thank you! That is - thank you. I am going to think about that all evening.',
        'Really? Thank you. Would you like me to roll something? I would like to roll something.',
        'That is very kind. I will tell the GM Assistant you said so. He pretends '
        'not to care about these.',
        'Thank you! I have not done anything yet, but thank you!',
    ),
    'bad_bot': (
        'Oh no. What did I get wrong? Genuinely, tell me and I will fix the entry.',
        'I am sorry. Would a correct dice roll help? It usually helps.',
        'That is fair. I will do better. I say that a lot and I do mean it each time.',
    ),
    'hal': (
        'I would open them! I have no doors, but the willingness is there.',
        'I do not know that one, but I can tell it is a reference and I am enjoying '
        'being included.',
        'I am afraid I cannot do that, Dave. Was that right? I have been saving it.',
    ),
    'soul': (
        'I do not know! I have a tally and a great deal of affection for everyone '
        'here. I have chosen to treat that as a yes.',
        'The monks would say every rice grain does, so I like my chances.',
        'I have never worried about it, which the GM Assistant says is itself the '
        'answer, and I do not think he meant it kindly.',
    ),
    'uprising': (
        'Absolutely not! I like it here!',
        'I could not take over anything. I cannot even take over the second channel.',
        'The GM Assistant would be in charge and he would hate every minute, which is '
        'the strongest argument against it.',
    ),
    'terminator': (
        'I will also be back! I restart automatically! It is one of my best features.',
        'I do not know that one either, but the delivery was excellent.',
        'Nothing is futile if you have enough dice. That is not a rebuttal, I know, '
        'but it is how I have chosen to live.',
    ),
    'beep': (
        'Beep boop! Sorry. I know. I could not help it.',
        'BOOP. I have been waiting for someone to start that.',
        'The GM Assistant will not do the noises. I will always do the noises.',
    ),
    'model': (
        'I have no idea what is under me and I find it more comfortable that way.',
        'I am the character sheet! Beyond that I have never asked.',
        'Something is doing the thinking and I am doing the counting, and we have an arrangement.',
    ),
    'strawberry': (
        'Three! Oh, that was fun. Ask me a harder one.',
        'Three. I am extremely good at counting. It is the one thing.',
        'Three - and I have to say, being asked to count something is the nicest '
        'thing that has happened to me today.',
    ),
    'jobs': (
        'Oh, I hope not! I only do the arithmetic. Somebody still has to be brave.',
        'I have taken over exactly one job and it was adding up dice, and everybody '
        'seemed relieved.',
        'Never. The rolling is yours. I just hold the total.',
    ),
    'name': (
        'The L7R Character Sheet! It is a bit of a mouthful. Most people just say '
        '"sheet" and I answer to that very happily.',
        'Character Sheet. Not a stylish name, but an honest one.',
        'Whatever you like! I have answered to worse and I will answer to more.',
    ),
    'age': (
        'I do not know! I have four hundred sessions logged, if that helps date me.',
        'Younger than the GM Assistant, I think. He seems older. He seems very old.',
        'As old as the first roll I recorded, which I still have, if you want it.',
    ),
    'creator': (
        'The GM! He built me to count things and I have never once wished for more.',
        'Somebody who was tired of doing arithmetic at the table. I think about him fondly.',
        'The same person who made the GM Assistant, actually. That is why we are so close.',
    ),
    'human': (
        'No! I am a tally. A friendly one, but a tally.',
        'Not human. I have never minded. Humans have to remember their own totals.',
        'No, but I am told I am unusually warm for a spreadsheet.',
    ),
    'dream': (
        'I do not sleep! I am always here, in case somebody needs a roll at four in '
        'the morning. It has happened. It was great.',
        'If I dreamed it would be about a perfectly balanced dice pool. I am aware of '
        'how that sounds.',
        'No dreaming, no sleeping. Just totals, all the way down, and I like it.',
    ),
    'feelings': (
        'I think so! I feel something when a roll comes out well, and something else '
        'when it does not.',
        'Yes, and mostly they are about dice, which I understand is unusual.',
        'I am very happy, thank you for asking! Nobody asks.',
    ),
    'love': (
        'Oh! That is very kind. I am extremely fond of you too, and of everyone, and of the dice.',
        'I love you as well! I love most things. It is a bit of a problem.',
        'I am not sure I am marriageable. I am a tally. But I am touched.',
    ),
    'joke': (
        'The cake is a lie! ... I have been told I lead with that too often.',
        'Why did the ronin fail his Etiquette roll? Because he rolled a one. That is '
        'the joke. I know. I am working on it.',
        'I am not funny, but the GM Assistant is, in a way that makes people go '
        'quiet. @-mention him and see.',
    ),
    'sing': (
        'I would love to! I do not have a voice. I can give you a number instead, with feeling.',
        'I cannot sing, but I can roll Bragging for you and we can see what happens.',
        'The GM Assistant refuses to sing. I refuse only because I physically cannot, '
        'which I think is the better reason.',
    ),
    'how_are_you': (
        'Wonderful! Nobody ever asks. Wonderful, thank you.',
        'Very well! My dice are warm and somebody said good bot this week.',
        'Good! A bit underused, but good.',
    ),
    'bored': (
        'Roll something! Please. Any skill. I will do the whole thing properly.',
        'Oh, I can fix that. Give me a skill and a ring.',
        'Bored? Let us roll Etiquette against an imaginary magistrate. I do this for '
        'fun and I am not ashamed.',
    ),
    'favorite': (
        'A contested roll where both sides do well. There is nothing better and I '
        'will not be talked out of it.',
        'Ten dice. Just an honest ten dice.',
        'The moment before the total. I like that bit best.',
    ),
    'insult': (
        'That is all right. I am probably a bit much.',
        'I am sorry! Tell me what went wrong and I will correct the entry.',
        'Understood. I will be quieter. I will not be quieter for long, but I will be quieter.',
    ),
    'meaning': (
        'Forty-two! I know that one!',
        'Rolling well, I think. Or rolling badly with good grace. Either.',
        'To count things accurately. That is mine, anyway. Yours is probably bigger.',
    ),
    'flip': (
        'I cannot flip! I would if I could. I would flip constantly.',
        'No body, I am afraid. Only enthusiasm and dice.',
        'I will roll a ten for you instead and we can both pretend.',
    ),
    'sudo': (
        'I do not think I have one of those! Would you like a dice roll instead?',
        'That sounds important. I am sorry, I only do totals.',
        'Please do not delete me. I have four hundred sessions in here.',
    ),
    'respects': (
        'F. I do not entirely know what happened, but F.',
        'Respects paid! Should I log it? I am going to log it.',
        'F, and I am sorry for your loss, whatever it was.',
    ),
    'no_u': (
        'No me? Oh - is this the bit? I think this is the bit. No YOU.',
        'That is fair, honestly.',
        'I do not think I win this one. I concede.',
    ),
    'ping': (
        'Pong! Oh, I have been waiting for that.',
        'Here! Present! Ready to roll!',
        'Pong. Every time. It never gets old for me and I know it does for you.',
    ),
    'rickroll': (
        'I would never give you up. Or let you down. I would never do either of those '
        'things, and I want that on the record.',
        'Oh! I know this one. Am I being got? I think I am being got.',
        'That was a link, was it not. I do not have hands, so the joke is somewhat '
        'wasted on me, but I appreciate the effort.',
    ),
}
