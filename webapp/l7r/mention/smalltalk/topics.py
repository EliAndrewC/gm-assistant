"""What triggers each category, and in what order.

ORDER IS CONTENT, not plumbing. `rules` walks this list and takes the first hit,
so a specific pattern has to precede a general one that would swallow it: "roll
for initiative" before the bare "roll", "good bot" before the greeting, "are you
an AI" before "are you a bot". Those three are pinned by tests, because placing a
new pattern against the general ones already here is the mistake that recurs
every single time a category is added.

WHERE THE LIST CAME FROM. Conversational platforms ship prebuilt small-talk
intent sets because the questions are so predictable - Dialogflow ES's agent runs
to ~86-100 intents, and Azure's chit-chat datasets to ~100 scenarios in five
personalities. This taxonomy follows that shape and then adds the clusters those
enterprise lists have no reason to carry: science-fiction robot canon, AI-era
jokes, Discord and internet culture, and tabletop reflexes.

**Only the QUESTIONS were reused, never anyone's answers.** Those sets ship their
own response text under their own terms; every line in `gm.py` and `sheet.py` is
written for these two bots. Same standard as `images.py`: the taxonomy is the
reusable part, the writing is not.
"""

from __future__ import annotations

TOPIC_ORDER: tuple[tuple[str, str], ...] = (
    # -- tabletop reflexes, before anything generic ------------------------
    ('initiative', r'\broll for initiative\b|\bnat(ural)? 20\b|\bcrit(ical)? (fail|success)\b'),
    ('rocks_fall', r'\brocks fall\b'),
    ('bribe', r'\bbribe\b'),
    ('wrong_system', r'\bwhat.?s my ac\b|\bthac0\b|\bd&d\b|\bdungeons? (and|&) dragons?\b'),
    ('trap', r'\b(it.?s a trap|check for traps|is it a trap)\b'),
    ('scorpion', r'\bscorpion\b'),
    # -- bot canon ---------------------------------------------------------
    ('good_bot', r'\b(good|best|nice|great) bot\b'),
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
    ('hallucinate', r'\b(hallucinat|make (it|something) up|are you (sure|certain)|prove it)\b'),
    # -- the classic small-talk intents ------------------------------------
    ('name', r"\bwhat(?:'s| is)? your name\b|\bwho named you\b|\bwhat do i call you\b"),
    ('age', r'\bhow old are you\b|\bwhen were you (born|made|created)\b'),
    (
        'creator',
        r'\bwho (made|created|built|wrote|programmed|coded) you\b|\byour (creator|maker)\b',
    ),
    ('human', r'\bare you (a )?(human|real|alive|sentient|conscious|a person)\b'),
    (
        'gender',
        r'\bare you (a )?(boy|girl|man|woman|male|female)\b|\bwhat (are your |your )?pronouns\b',
    ),
    ('dream', r'\bdo you (dream|sleep)\b'),
    ('eat', r'\bdo you eat\b|\bare you hungry\b|\bwhat do you eat\b|\bdo you drink\b'),
    ('family', r'\bdo you have (a family|parents|siblings|children|kids)\b|\bare you married\b'),
    ('feelings', r'\bdo you have (feelings|emotions)\b|\bare you (happy|sad|lonely|okay|ok)\b'),
    ('love', r'\b(i love you|do you love me|will you marry me|marry me)\b'),
    ('joke', r'\btell me a joke\b|\bsay something funny\b|\bmake me laugh\b'),
    ('sing', r'\bsing\b'),
    ('how_are_you', r'\bhow are you\b|\bhow.?s it going\b|\bhow have you been\b'),
    ('bored', r'\bi.?m bored\b|\bentertain me\b'),
    ('favorite', r'\bfavou?rite\b'),
    ('insult', r'\b(you.?re (stupid|dumb|useless|the worst)|shut up|i hate you)\b'),
    ('smart', r'\bare you smart\b|\bhow smart are you\b|\bare you clever\b'),
    ('what_can_you_do', r'\bwhat (can|do) you do\b|\bwhat are you (for|good at)\b'),
    ('where', r'\bwhere (are|do) you( live| from)?\b|\bwhere am i\b'),
    ('language', r'\bwhat languages?\b|\bdo you speak\b'),
    ('busy', r'\bare you busy\b|\bam i bothering you\b|\bdo you have time\b'),
    ('yourself', r'\btell me about yourself\b|\bwho are you really\b'),
    ('remember_me', r'\bdo you remember me\b|\bdo you know who i am\b|\bdo you remember\b'),
    ('listening', r'\bare you (there|listening|awake|around|up)\b|\bhello\?\b'),
    ('recording', r'\b(are you recording|is this (being )?(logged|recorded|saved)|do you save)\b'),
    ('learn', r'\bcan you learn\b|\bdo you get (smarter|better)\b|\bare you trained\b'),
    ('tired', r'\bare you tired\b|\bdo you get (tired|bored)\b|\bdo you rest\b'),
    ('judge', r'\bare you judging me\b|\bdo you judge\b|\bwhat do you think of me\b'),
    ('lie', r'\b(can|do) you lie\b|\bare you lying\b|\btell me the truth\b'),
    ('secret', r'\btell me a secret\b|\bcan you keep a secret\b'),
    ('sorry', r'\b(i.?m sorry|i apolog|my apologies|forgive me)\b'),
    ('goodbye', r'\b(goodbye|good bye|farewell|see you|later|good ?night)\b'),
    ('time', r'\bwhat time is it\b|\bwhat day is it\b|\bwhat.?s the date\b'),
    ('weather', r'\bweather\b|\bis it raining\b'),
    # -- internet culture --------------------------------------------------
    ('meaning', r'\b(meaning of life|forty.?two)\b|\b42\b'),
    ('flip', r'\bdo a (flip|barrel roll)\b|\bdance for me\b'),
    ('sudo', r'\bsudo\b|\brm -rf\b|\bdelete yourself\b|\bself.?destruct\b'),
    ('respects', r'\bpress f\b|\bpay respects\b'),
    ('no_u', r'\bno u\b'),
    ('ping', r'\bping\b'),
    ('rickroll', r'\bnever gonna give you up\b|\brickroll(ed)?\b|\brick astley\b'),
    # -- the general ones, LAST, because they would swallow the specific ---
    ('cake', r'\bcake\b'),
    ('who', r'\bwho (are|r) (you|u)\b'),
    ('greeting', r'\b(hello|hi|hey|greetings|good (morning|evening))\b'),
    ('thanks', r'\b(thank you|thanks|thx|arigato)\b'),
    ('bot', r'\bare you (a |an )?(bot|robot|ai|program|computer)\b'),
    ('help', r'\bhelp\b'),
    ('drink', r'\b(drink|sake|drunk|beer|bar)\b'),
    ('monster', r'\b(monster|oni|demon|tengu|youkai|ghost)\b'),
    ('fish', r'\b(fish|carp|dolphin|whale|shark)\b'),
    ('roll', r'\broll\b'),
)
