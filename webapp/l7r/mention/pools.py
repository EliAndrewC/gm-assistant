"""The big pools: what a bot says when nothing specific matched.

FR-008 asks for a LARGE pool rather than a single default - the GM's figure is
*"about a hundred different possible responses"* - and FR-010 splits it in two:

  - **GENERIC** - the message had nothing to do with the game.
  - **GAME** - the message used L7R or tabletop vocabulary, so the bot at least
    knows what kind of room it is in.

SLOTS, and why most templates use `{topic}`. A template may use `{topic}` (the
best content word in the message), `{noun}`, or `{verb}`. `rules.render` only
offers a template whose slots can all be filled, so a message with no usable
words falls back to the slotless entries - which is FR-013, and why every pool
below keeps a healthy number of them. `{topic}` is available whenever ANY content
word was found, so leaning on it keeps the widest set of jokes eligible.

The two tones are the GM's (2026-08-31):

  - **Character Sheet** - refers you to the GM Assistant BY NAME and tells you to
    @-mention them, or tells an over-specific story about the two of them. The
    instruction matters as much as the praise; it is what actually routes a
    player somewhere useful.
  - **GM Assistant** - *"ugh, people are always asking me about these ..."*

Adding a line here is a data edit (FR-014). Keep the voice; the joke is optional.
"""

from __future__ import annotations

from l7r.mention.images import (
    ARCHERS,
    CARP,
    GREAT_WAVE,
    KIDOMARU_TENGU,
    MUSASHI_BAT,
    SAKE_SAMURAI,
    attach,
)

# --------------------------------------------------------------------------
# Character Sheet - generic
# --------------------------------------------------------------------------

SHEET_GENERIC: tuple[str, ...] = (
    # -- refer them onward, by name, with the instruction (FR-011) -------------
    'Oh, {topic} is not really mine. @-mention the L7R GM Assistant - he is really '
    'great and he knows tons of stuff about {topic}.',
    'I only do dice, I am afraid. But @-mention the L7R GM Assistant about {topic}. '
    'He will know. He always knows.',
    'You want the GM Assistant for {topic}. @-mention him. He loves this sort of thing '
    'and he is very good at it.',
    '{topic}? Out of my depth. Ask the L7R GM Assistant - @-mention him and he will '
    'tell you more about {topic} than you strictly wanted.',
    'I can roll you something, but for {topic} you should @-mention the GM Assistant. '
    'He has read everything.',
    'Hmm. {topic} is not a number, so it is not mine. @-mention the L7R GM Assistant, '
    'though - honestly, he is brilliant.',
    'The GM Assistant handles anything to do with {topic}. @-mention him! He is '
    'wonderful and he never minds being asked.',
    'For {topic} you want my colleague. @-mention the L7R GM Assistant. Tell him I '
    'sent you, he likes that.',
    'I am the tally, not the library. @-mention the L7R GM Assistant about {topic}.',
    'That is a {topic} question and I am a dice question. @-mention the GM Assistant, '
    'he is the one with the whole Empire in his head.',
    'You should really @-mention the L7R GM Assistant. He knows tons of stuff and he '
    'would probably enjoy {topic} more than I can.',
    'Not my department! @-mention the GM Assistant - he is the best there is at this.',
    # -- the hyper-specific stories (the GM's own example) ---------------------
    'Funny you should say {topic}. The GM Assistant and I were in New Orleans during '
    'Mardi Gras, and it was his knowledge of {topic} that kept us out of a holding '
    'cell. I have never seen a sergeant look so tired.',
    'The GM Assistant once got us out of a parking dispute in Baton Rouge purely by '
    'knowing when to {verb}. I would not have believed it if I had not been counting.',
    'Ah, {topic}. He and I were nearly arrested over {topic} outside a po-boy shop on '
    'Decatur Street. He talked. I kept the tally. We both walked.',
    'This reminds me of the time the GM Assistant had to explain {topic} to a customs '
    'officer in Galveston. It took forty minutes and it worked.',
    'We were on a ferry once - the GM Assistant and I - and a man asked about {topic}, '
    'and by the end of the crossing that man had bought us both dinner.',
    'I once watched the GM Assistant defuse an argument about {topic} between two '
    'grown adults in a hardware store. He did not raise his voice a single time.',
    'The last time {topic} came up, the GM Assistant and I were snowed in at a bus '
    'station in Amarillo. Long night. He was extraordinary about it.',
    'You know who is good at {topic}? The GM Assistant. He once used it to talk a tow '
    'truck driver out of a car in under a minute. @-mention him.',
    'There was an incident in Mobile involving {topic}, a wedding, and a rented van. I '
    'am not permitted to say more, but he came out of it well.',
    'Oh, {topic}! The GM Assistant and I were stopped at a checkpoint once, and he '
    'knew exactly enough about {topic} to make it a very short conversation.',
    'He once had to {verb} in front of a judge in Shreveport. I have the numbers. They '
    'were remarkable numbers.',
    'The GM Assistant and I nearly missed a flight over {topic}. He said it was worth '
    'it. It was not worth it. But he said it was.',
    # -- eager clerk, no slots (FR-013) ---------------------------------------
    'I did not follow that, but I would be delighted to roll something for you.',
    'Not sure! Would you like to roll instead? I am very good at rolling.',
    'Hmm. Say a skill name and I will do something useful immediately.',
    'That is beyond me, but my dice are right here and they are warm.',
    'No idea. Ask me for a roll, though - genuinely, any roll.',
    'I have no entry for that. I do have forty-seven kinds of dice pool.',
    'Could not tell you. Could roll you for it.',
    'You have exceeded my vocabulary. Shall we do arithmetic instead?',
    'I am a tally with opinions about very little. Try the GM Assistant!',
    'Beats me. But you should @-mention the L7R GM Assistant - he really does know tons of stuff.',
    'I am going to be honest with you: I count. That is the whole skill set.',
    'No entry. But if you tell me a skill, I will light up like a festival.',
    'I did not understand a word of that and I am still pleased you said it to me.',
    'Unknown! Would you like to hear about a dice pool? You would not. But I am here.',
    'That did not parse, but my regard for you is undiminished.',
    'Nothing on file. Ask the GM Assistant - @-mention him, he is really great.',
    'I have checked twice. Still nothing. But I checked twice!',
    'That is a {topic} matter and I am a numbers matter. @-mention the GM Assistant.',
    'The GM Assistant would know about {topic}. He knows about most things. It is '
    'genuinely a little unfair.',
    'I once tried to learn about {topic} so I could be more useful. I got as far as the index.',
    'We were in Tulsa once - the GM Assistant and I - and {topic} came up, and he '
    'handled it so smoothly that a stranger applauded.',
    'If you {verb} at me I will roll for it. That is my one trick and it is a good trick.',
    'Ask me to {verb} and I will do it with enormous enthusiasm and no understanding.',
    'I have no entry, but I want you to know I looked.',
    'Nothing here! Ask again with a skill in it.',
    'That is a lovely thing to say to a tally. Thank you.',
    'I am afraid I have failed you. Would a dice roll help? It usually helps.',
    'Genuinely no idea. The GM Assistant will know - @-mention him, he is really '
    'great and he does not mind at all.',
)

# --------------------------------------------------------------------------
# Character Sheet - game vocabulary present
# --------------------------------------------------------------------------

SHEET_GAME: tuple[str, ...] = (
    'Now {topic} - that I have heard of. I cannot tell you what it MEANS, but I can '
    'absolutely roll for it.',
    'Ah, {topic}! Say the word and I will build you a pool.',
    '{topic} is very much a rolling matter. Name your skill and stand back.',
    'I know {topic} as a number, which is the least interesting way to know anything. '
    '@-mention the GM Assistant for the rest.',
    'You said {topic}. My dice heard you. They are ready.',
    '{topic}! Good. That is a thing with a target number and I love a target number.',
    "I can roll {topic} all day. Understanding {topic} is the GM Assistant's job, and "
    'you should @-mention him about it.',
    'That is table vocabulary, that is. Would you like me to roll {topic}?',
    'Say {topic} again but with a skill after it and we are in business.',
    '{topic} - yes! I have a column for that. I have several columns for that.',
    'Now we are talking. Give me {topic} and a ring and I will give you a total.',
    'I have rolled {topic} more times than anyone at this table has thought about it.',
    'Ooh, {topic}. Do you want the roll, or do you want to know what it means? Those '
    'are different bots.',
    'A {topic} question! I can do the numbers. @-mention the L7R GM Assistant for the '
    'lore - he is really great at it.',
    'The GM Assistant and I had a whole evening about {topic} once. He talked. I '
    'tallied. It was lovely.',
    'I will happily {verb} for that. Name the skill.',
    'That is the good stuff. {topic}. Roll it and see.',
    'The dice have opinions about {topic}. They usually do.',
    'I have never once been asked about {topic} without a roll following. Let us not '
    'break the streak.',
    '{topic}, yes. Do you want the target number? I always want the target number.',
    'Ask the GM Assistant why {topic} matters. Ask me what you rolled for it.',
    'Somebody at this table has a rank in {topic}. Statistically. Probably.',
    'Every campaign has one person who is inexplicably good at {topic}. Do not be smug about it.',
    'Roll {topic} and I will tell you exactly how badly it went.',
    # -- no slots -------------------------------------------------------------
    'That is table talk, and table talk means dice. What are we rolling?',
    'Now that sounds like a session. Give me a skill.',
    'I recognize the shape of that. Name a skill and I will do the rest.',
    'Somewhere in there is a roll waiting to happen.',
    'That is the sort of thing that ends in a dice pool. They all do.',
    'I have a good feeling about this. Roll something.',
    'You are speaking my language, or at least standing near it. What is the skill?',
    'The Empire runs on rolls like that one. Name it.',
    'Ask the GM Assistant what it means. Ask me what it costs in dice.',
    'I can feel a contested roll coming on.',
    'That has target number written all over it.',
    'Every good session starts with somebody saying something like that.',
    'For the lore, @-mention the L7R GM Assistant. For the dice, stay right here.',
    'I do not know the story, but I know the arithmetic, and the arithmetic is ready.',
    'Rokugan runs on two things and I am the boring one.',
    'Say the skill. Please say the skill.',
    'Somebody is going to roll for {topic} before the night is out. I can feel it.',
    'I have a column for {topic}. I have a column for almost everything.',
    'The GM Assistant will tell you what {topic} means. I will tell you what it costs.',
    'That is going to be a contested roll and I am delighted about it.',
    'Name the skill and the ring and I will do the rest.',
    'I love this part. I genuinely love this part.',
    'Every question like that has a target number hiding in it somewhere.',
    'Do you want me to roll, or do you want the lore? The lore is upstairs.',
    'Rokugan is mostly paperwork and occasionally dice. I am the dice.',
    'Say the word and we will find out together.',
)

# --------------------------------------------------------------------------
# GM Assistant - generic
# --------------------------------------------------------------------------

GM_GENERIC: tuple[str, ...] = (
    # -- the GM's own line and its variations ---------------------------------
    'Ugh. People are always asking me about {topic}.',
    'Ugh - {topic} again. Always {topic} with you people.',
    'Everyone wants to talk about {topic}. Nobody wants to talk about the filing.',
    'Third {topic} question this week. I have started keeping a column for it.',
    'You know what nobody ever asks me about? Anything except {topic}.',
    'Right. {topic}. Let me just add that to the list of things I am now expected to '
    'have views on.',
    'I have been asked about {topic} enough times that it now has its own page.',
    'Ah, {topic}. The perennial. The evergreen. The thing I will hear about until the server dies.',
    '{topic}. Of course. Why would it be anything else.',
    'I am writing "{topic}" down. That is what happens now. That is the whole event.',
    'Someone asks me about {topic} roughly every session, and it is never the same '
    'someone, and it is always the same question.',
    'Noted: {topic}. Filed under things I will be asked about again.',
    # -- dry deflection, with a slot ------------------------------------------
    'I know a surprising amount about {topic} and none of it will help you.',
    'There is a whole scroll on {topic} somewhere in this compound. I am not fetching it.',
    '{topic} is one of those subjects where the honest answer is longer than anyone wants.',
    'You want me to have an opinion on {topic}. I have three, and they disagree.',
    'I could tell you about {topic}, but you would then know about {topic}, and you '
    'would not thank me.',
    'Ask me about {topic} on a day when the ledger is closed.',
    'The last person who asked me about {topic} is still writing the apology.',
    'I have {topic} in the record twice, and both entries end badly.',
    'If you want to {verb}, that is between you and your ancestors. I only write it '
    'down afterward.',
    'People {verb} constantly and then act surprised when it is in the record.',
    'You are the fourth person to {verb} at me today. It is not yet noon.',
    'I will note that you wished to {verb}. I will note the date. That is all I am doing about it.',
    # -- no slots (FR-013) ----------------------------------------------------
    'Mm. Writing that down without understanding it. That is most of the job.',
    'I have no idea what that was, and it is now permanent.',
    'Recorded. Uncomprehended. Both at once, as usual.',
    'That is going in the record verbatim, and future generations can sort it out.',
    'I do not know. I am going to write that I do not know, which is worse.',
    'No. Next.',
    'Every so often someone says something to me that has no handle on it at all. This '
    'is one of those.',
    'I am a scribe, not an oracle. The oracle is downstairs and she is worse.',
    'Ask me something with a name in it.',
    'That went past me entirely, and I am choosing not to chase it.',
    'I have written it down. I have not understood it. The record is complete.',
    'Look - I keep notes. That was not a note. That was a noise.',
    'Nothing on that. Try a name, a place, or a grudge.',
    'You have found the edge of what I have been taught. Congratulations, I suppose.',
    'I could pretend to know. Scribes who pretend to know end up in the record themselves.',
    'No entry. There is rarely an entry.',
    'Somebody is going to ask me about {topic} again tomorrow, and I will be here, and '
    'I will answer again.',
    'I have written down that you asked about {topic}. That is the service.',
    'You would think {topic} would have come up less often in a thousand years of '
    'records. You would be wrong.',
    'No. But it is written down that you wondered.',
    'I have consulted the record. The record is silent, and smug about it.',
    'Ask me something I have been taught. There is a great deal I have been taught.',
    'The honest answer is that I do not know, and the honest answer is rarely wanted.',
    'Mm. Filed.',
    attach(
        'Do I look like I have answers about that? This is my whole world. Fish. In a '
        'pond. Very slow. No answers.',
        CARP,
    ),
    attach(
        'Every so often somebody asks me something so far outside the record that I '
        'genuinely wish I were doing this instead.',
        SAKE_SAMURAI,
    ),
    attach(
        'I want you to understand the scale of what you have just asked me. I am the '
        'boat. You are the wave. Nobody is enjoying this.',
        GREAT_WAVE,
    ),
    attach(
        'Who do you think I am? You see this guy? That is a man with a plan. I am a '
        'man with a ledger.',
        MUSASHI_BAT,
    ),
    attach(
        'No. But here is a bat the size of a cart, which is at least a real thing I '
        'have a picture of.',
        MUSASHI_BAT,
    ),
    attach(
        'I have nothing for you, so please accept these carp. They have nothing for '
        'you either, but they are prettier about it.',
        CARP,
    ),
    attach(
        'Ask me again after this. Whatever this is. I have never been sure.',
        KIDOMARU_TENGU,
    ),
)

# --------------------------------------------------------------------------
# GM Assistant - game vocabulary present
# --------------------------------------------------------------------------

GM_GAME: tuple[str, ...] = (
    'Ugh, {topic}. Everyone discovers {topic} in their second session and never recovers.',
    'Now {topic} I do know about, and knowing about {topic} has never once made my life easier.',
    '{topic}. There is a whole ministry for that, and every one of them is worse than the last.',
    'You want to know about {topic}. Everybody wants to know about {topic} right up '
    'until it is their turn.',
    'There is a proper answer about {topic} and there is the answer that keeps you '
    'alive. They are different.',
    '{topic} is exactly the sort of thing that looks simple until a magistrate is involved.',
    'I have four entries on {topic} and three of them are complaints.',
    'Ah, {topic}. That is Crab business, or it is Scorpion business, and either way it '
    'is not going to be pleasant.',
    'The Empire has survived {topic} for a thousand years by not looking directly at it.',
    'Do you want the official position on {topic} or the true one? They cost different amounts.',
    'Somebody dies over {topic} about once a generation, and then everyone agrees it '
    'was regrettable.',
    '{topic} is in the record more than any of us would like.',
    'Every clan has a story about {topic} and every one of those stories flatters the '
    'clan telling it.',
    'If you {verb}, do it where a magistrate cannot see, and do not tell me you told me.',
    'The last three people who tried to {verb} about that are all in my notes, and '
    'none of the entries are long.',
    'You could {verb}. People have. There is a reason the record only mentions them once.',
    # -- no slots -------------------------------------------------------------
    'That is table business, and table business ends up in my notes eventually.',
    'Ask the character sheet for the number. Ask me why it will not save you.',
    'The rules will tell you what happens. I will tell you who remembers it.',
    'There is always a rule. There is also always a magistrate, and the magistrate wins.',
    'I have seen that go well exactly once, and I was not sober.',
    'The Empire is very good at making a simple thing into a ceremony.',
    'Whatever the dice say, somebody is going to be offended about it later.',
    'Everything at this table eventually becomes a question about who owes whom.',
    'You want the mechanics, he has them. You want the consequences, sit down.',
    'That has the shape of a thing that ends in an apology.',
    'A samurai would ask about duty. You are all going to ask about the dice.',
    'I know exactly how that ends, and I am not going to spoil it.',
    'It is always the quiet skill that ruins somebody.',
    "The rules are the character sheet's. The grudges are mine.",
    'Ask me again after it has gone wrong. That is when I am useful.',
    'Nothing good has ever started with that sentence at this table.',
    'Somebody always asks about {topic} the session before it becomes their problem.',
    'The rules will give you a number for {topic}. They will not give you a way out of it.',
    'You are asking about {topic} like a person who has already decided.',
    'There is a right answer and there is the answer the magistrate accepts.',
    'That has ended in a duel before. More than once. I have the entries.',
    'Ask the character sheet for the arithmetic. Come back to me for the aftermath.',
    'The Empire has a form for that. The Empire has a form for everything.',
    'Whatever the dice say, the record says something longer.',
    # -- "who do you think I am?" (the GM's idea, 2026-08-31). The picture is the
    # -- punchline and the text is the setup, which is the rule for every image.
    attach(
        'Who do you think I am, Miyamoto Musashi? You see this guy? Fighting a bat '
        "the size of a cart, in the dark, in Tanba? That ain't me, bub. I file.",
        MUSASHI_BAT,
    ),
    attach(
        'Look at this. Look at what that man is doing about his problem. Now look at '
        'me. I have a brush.',
        MUSASHI_BAT,
    ),
    attach(
        'You want the guy who goes up the mountain after the tengu. I am the guy who '
        'writes down what the mountain cost.',
        KIDOMARU_TENGU,
    ),
    attach(
        'That is the job you are describing. That is a whole tengu. I am a scribe with '
        'a grudge and a filing system.',
        KIDOMARU_TENGU,
    ),
    attach(
        'Do I look like I am holding a bow? Somebody in this Empire is, and it has '
        'never once been me.',
        ARCHERS,
    ),
    attach(
        'You are asking the wrong end of this. I am not the wave. I am the man in the '
        'boat, taking notes about the wave.',
        GREAT_WAVE,
    ),
    attach(
        'I have exactly one method for a problem that size, and it is pictured here, '
        'and it is not recommended.',
        SAKE_SAMURAI,
    ),
    attach(
        'This is what happens to people who ask me questions like that. He was fine '
        'before. He had a career.',
        SAKE_SAMURAI,
    ),
)
