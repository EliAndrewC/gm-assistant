"""Religion, cosmology, and the four Gods of Death. GM Assistant only.

THE TONE BAR (FR-002), as the GM restated it on 2026-08-31 after reading the
first pass: **something funny in every single line**, and the humor may take any
of three forms, mixed deliberately across the ten replies in a category:

  1. **Performative woe-is-me.** He is put upon, and says so by way of the fact
     rather than instead of it. The fact is not DECORATED with a complaint, it is
     RE-EXPLAINED THROUGH HIS POSITION - he is the second half of the sentence.
  2. **Judgment of the source material.** The GM's own worked example is the
     Phoenix line below: *"The Phoenix are known for them, which is awkward,
     given that the founder of the Isawa practiced maho."* That costs him
     nothing and is still funny, because it is commentary from a point of view.
  3. **Sardonic observation about Rokugan** - but it must have an EDGE. A merely
     elegant epigram is the near miss that feels finished.

The mix is the point; ten identical registers in a row is its own failure.

Traps, all of them named by the tone audit of 2026-08-31 (which found 3.2% of
this file's lines clearing the bar - the second-worst of the six):

  - An "Ugh." or "Fine." on the front is a mood, not a joke. The GM said so
    directly: the line he quoted at us already had both and was still flat.
  - "Ask me about X" is a signpost, not a punchline. It was closing a third of
    all categories in the corpus.
  - "And this is..." opened 97 of 103 second captions. Vary the caption.
  - Never scold the player. His comedy runs the other way: he is at the bottom
    of the ladder and it is one rung.
  - A flat inventory assertion ("I have the vow written out in full") is a
    receipt, not a grievance. It has to cost him something.

Facts are lifted at authoring time and several here are load-bearing: the
Enma/Emma-O distinction and the four-sword mapping (Bloodstorm to Emma-O,
Lamentation to Enma, Lightning to King Yan, Retirement to Wei Tin) are asserted
in four places apiece and must stay in step. A turn may go AROUND a fact; it
must never soften it.

The four Gods of Death each have their own category at the GM's explicit
instruction (FR-005); Emma-O is here rather than with the other three because
she is a Fortune recognized Empire-wide, not a Moto-only god - she is still the
fourth.
"""

from __future__ import annotations

from l7r.mention.images import (
    CARP,
    CATS,
    DUEL_ON_THE_BRIDGE,
    FOX_WOMAN,
    GREAT_WAVE,
    INNER_VISION,
    KIDOMARU_TENGU,
    RAINY_MOON,
    SAKE_SAMURAI,
    attach,
)

RELIGION: dict[str, tuple[str, ...]] = {
    'vows_and_oaths': (
        'An oath is sworn BY a god. A vow is sworn TO one. People use them '
        'interchangeably, act astonished at the consequences, and then it is my '
        'handwriting that explains the difference to a magistrate.',
        'You name yourself unambiguously first, so the fortune does not bind the wrong '
        'person, which sometimes means naming your parents. A theology with a filing '
        'convention built into it. I feel recognized and I do not enjoy it.',
        'Then who you swear by, then the formula. Three parts. The middle one is where '
        'people get creative, and creativity in the middle part is how a one-line entry '
        'becomes four pages of mine.',
        'A legionnaire swears "by Lady Sun, and by my ancestors" and may add their '
        'family patrons. It ends "that in so doing I shall never seek to avoid death." '
        'Nobody drafted a clause about avoiding paperwork.',
        'Higher rank, longer oath. Lieutenants marshal troops, captains show utmost '
        'respect for duty, generals borrow clauses from all six ministries. The length '
        'of a vow is inversely proportional to how much of it the swearer wrote.',
        'Dying with a vow unfulfilled brings bad karma into your next lives and the '
        'wrath of the fortune. Dying ATTEMPTING it brings the opposite. The gods reward '
        'effort over outcome, which is the most encouraging fact I have.',
        'That asymmetry is the whole reason vows are dangerous and the whole reason '
        'people swear them anyway. Whoever designed it understood gamblers rather '
        'better than theologians usually do.',
        'A vow of creation obliges you to build the thing whether or not the war that '
        'made it sensible is still being won. There is no clause for "circumstances '
        'changed". I have read it looking for one, on behalf of a friend.',
        attach(
            'A man in the third part of an oath, working out what he has just agreed '
            'to. I keep this one where I can see it.',
            INNER_VISION,
        ),
        attach(
            'How an unfulfilled vow usually resolves. Neither party has consulted the '
            'written text, which I hold, and which is four feet away.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'bentens_blessing': (
        "Benten's Blessing is real, it works, and it has never once made anybody "
        'happy. A gift from the fortune of love that functions primarily as a warning.',
        'Ritsu the pilgrim can look at a person and sketch their soulmate. He then '
        'swore the vow of soothsaying to Benten, because people take the news badly - '
        'so the blessing came with a complaints procedure, which is more than mine did.',
        'Three people in recent years received sketches of GAIJIN soulmates. Excellent '
        'news for the campaign, catastrophic news for those three, and a genuinely '
        'lovely afternoon for me.',
        'Toranosuke, abbot of Chai Sedo, declared it portends success for the campaign. '
        'A blessing about marriage, entered into the record as a military dispatch, and '
        'nobody involved thought that was strange.',
        'By vowing to always convey truth to all who seek it, Ritsu receives divine '
        'truth in return. He is paid in the very thing he is obliged to give away. I '
        'have raised the comparison with nobody, because there is nobody.',
        'A blessing that obliges you to tell people things they do not want to hear is '
        'not a reward. It is a posting, and I recognize the terms of it.',
        'Benten is the fortune of romantic love. On this evidence she is also the '
        'fortune of extremely awkward afternoons, and I maintain the register of them.',
        'Everybody asks for the blessing. Nobody asks what the blessing costs. That '
        'ratio holds for most things people ask me about, myself included.',
        attach(
            'Somebody receiving news of their soulmate. Note the composure. It lasts '
            'another four seconds.',
            RAINY_MOON,
        ),
        attach(
            'Somebody who received a soulmate sketch this morning, pictured this '
            'evening. The pilgrim does not draw this part.',
            SAKE_SAMURAI,
        ),
    ),
    'temple_organization': (
        'A country monk in every village district, a preceptor in every county town, a '
        'provincial abbot in every provincial city, at least two grand abbots in every '
        'capital. A flawless hierarchy, and I am not anywhere on it.',
        'An ORDER is the network. A TEMPLE is a building. The Order of Bishamon is '
        'every temple, monastery and shrine to Bishamon in Damasu lands. That '
        'distinction takes four words and has cost me hours.',
        'Every domain in Lion lands has its own Order of Bishamon with its own Grand '
        'Abbot, none of them subordinate to another, and all of them willing to say so '
        'in writing, at length, to me.',
        'For a large network the capital temple is sovereign and the provincial ones '
        'subordinate. Within a domain. Only within a domain. The Empire built a '
        'hierarchy that stops at the border and then acted surprised by the arguments.',
        'The Shinsei identified seven Major Fortunes whose favor brings luck and '
        'prosperity. Everyone can name three. Nobody has ever asked me for the other '
        'four, and I have them ready.',
        'The country monk holds tax-free land and may have acolytes farming it '
        'part-time, on loan from the larger families. A spiritual office with a labor '
        'arrangement attached, which is the most honest thing in the apparatus.',
        'Temples are administered by the Ministry of Rites. Administered. Not blessed, '
        'not guided - administered, with forms. I find that reassuring and I am aware '
        'of what it says about me.',
        'Ask a grand abbot about doctrine and you get theology. Ask him about the '
        'harvest and you get the truth. I hold both answers and only one is ever quoted.',
        attach(
            'Temple life. Considerably more sweeping than the prints suggest, and the '
            'prints are what get endowed.',
            CATS,
        ),
        attach(
            'Where a doctrinal disagreement goes once the Ministry of Rites has '
            'declined to schedule it.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'temple_finances': (
        'Nobody asks about temple finances, which is a shame, because it is the most '
        'revealing thing in the entire religious apparatus and I have prepared.',
        'A temple holds land. Land means tenants, tenants mean rent, and rent means a '
        'temple is a landlord with better robes and a longer memory. I say that with '
        'professional respect for the memory.',
        'The history of the Temple of Bishamon is largely a history of property. '
        'Somebody ought to mention it to the people who write the hymns.',
        'Tax-free land is the gift that matters. Everything else a daimyo gives a '
        'temple is decoration - and the decoration is what goes in the dedication, and '
        'the dedication is what I am asked about.',
        'Monks live inside the precinct. Initiates, about twice their number, mostly '
        'live out. That is a housing arrangement wearing a spiritual explanation, and I '
        'am obliged to write down the explanation.',
        'When a temple is wealthy, ask who endowed it and what they wanted written down '
        'about themselves. There is always something. There is always someone in my '
        'position who wrote it.',
        'The lay neighborhoods around a large temple are where the actual economy sits. '
        'The temple is the part that appears in the paintings.',
        'I have never met an abbot who was bad at arithmetic. Not one. Whereas the '
        'character sheet is superb at arithmetic and has never been handed anything '
        'worth counting.',
        attach(
            'The endowment, in its usual form: slow, cold, older than the building it '
            'paid for, and the only member of the congregation nobody preaches at.',
            CARP,
        ),
        attach(
            'A dispute over temple land, resolved by the one method that generates no '
            'useful documentation.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'food_purity': (
        'Food purity matters more than visitors expect and less than the devout claim, '
        'and both parties write to me about it.',
        'Death pollution is the organizing principle: what has touched death does not '
        'come inside, and a great deal of dinner has touched death. The theology is '
        'coherent. It is simply inconvenient at every meal.',
        'The rules vary by order, by region, and by how closely anybody is watching. It '
        'is that third variable that keeps my record honest and my opinion of the '
        'second one low.',
        'A monastery keeps purity rules a village district could not afford to keep, '
        'and then the monastery writes about discipline.',
        'Purity is largely a question of who can pay for it, which is true of most '
        'religious observance. I get to say it once per conversation before somebody '
        'changes the subject.',
        'Ask a monk what he MAY eat and he will tell you at length. Ask what he DOES eat '
        'on the road and he will discover an urgent errand elsewhere.',
        'The burakumin handle what nobody else may touch and eat what nobody else will, '
        'and the Celestial Order calls them non-people for doing the work it requires. '
        'I record the arrangement. I am not obliged to admire it.',
        'I hold what people claimed to observe. That is a different document from what '
        'they observed, and I am the only one who has read both.',
        attach(
            'Purity, as observed by those with the leisure to observe it.',
            INNER_VISION,
        ),
        attach(
            'Purity on the third night of a journey. Also filed under purity, at their insistence.',
            SAKE_SAMURAI,
        ),
    ),
    'soothsaying': (
        'Soothsaying works. That is the part nobody is ready for, it is the part I have '
        'to lead with, and the rest of the conversation is spent managing the '
        'consequences of having led with it.',
        'It does not tell you what will happen. It tells you what is ALIGNED, which is '
        'a different and much less useful thing. Try explaining that to somebody who '
        'has already paid.',
        'The sexagenary cycle names the day as well as the year, so there is always '
        'something significant about today. Always. A system that cannot be wrong, and '
        'I keep records for it anyway.',
        'A soothsayer who tells you nothing is going to happen has either failed or is '
        'being kind. Those are the only two readings and neither is billed differently.',
        'Ritsu swore the vow of soothsaying to Benten because the truth he was handed '
        'kept upsetting people. The vow is a shield, not a gift. I would take a shield.',
        'Omens are read after the fact far more often than before it, and the record is '
        'perfectly clear about which, because I am the one who dated the entries.',
        'Kitsu Okura has six doctrines about attunement. I have had all six explained '
        'to me twice, by him, unprompted, and I could not tell you which two were the '
        'repeats.',
        'Ask a soothsayer a question and you will get an answer. That is the problem. '
        'Nobody has ever founded a theology on declining to comment and I would have '
        'subscribed to it.',
        attach(
            'A reading in progress. It will take longer than you have and end in a metaphor.',
            INNER_VISION,
        ),
        attach(
            'The omen everybody remembers seeing afterward. My entry for that day says "overcast".',
            GREAT_WAVE,
        ),
    ),
    'omens_and_portents': (
        'Everyone wants the list of omens. The list is the least interesting part of '
        'the subject and it is the only part anybody has ever asked me for.',
        'An omen is only an omen once somebody in authority agrees it was one. Before '
        'that it is weather. I file it under weather and wait to be corrected, which is '
        'my entire professional posture.',
        'A comet before a battle is a portent. A comet before a good harvest is a '
        'comet. Same comet. The comet has no opinion; everybody else has several.',
        'Toranosuke declared that gaijin soulmate sketches portended success for a '
        'military campaign. Abbots have a remarkable gift for spotting good omens in '
        'armies that are already moving.',
        'The Ministry of Rites decides which readings are doctrine and which are '
        'heresy, so a portent is also a political act with a robe on.',
        'I have four hundred sessions of omens and about six were noticed BEFORE the '
        'event. The rest were noticed by me, afterward, at speed, because somebody '
        'wanted a precedent by evening.',
        'The useful question is never "was that an omen". It is "who benefits from it '
        'having been one". I keep a column for that and nobody has ever asked to see '
        'the column.',
        'Something strange happened and you would like it to mean something. That is '
        'not theology. That is most of my correspondence.',
        attach(
            'The single most-cited omen in the record. It means whatever the person '
            'citing it needs, and so far it has meant nine things.',
            GREAT_WAVE,
        ),
        attach(
            'The one people actually saw and chose not to report. It exists in my copy '
            'and nowhere else, which is the usual arrangement.',
            KIDOMARU_TENGU,
        ),
    ),
    'lord_moons_court': (
        "Lord Moon's heavenly court. You have asked a secret society question in an "
        'open channel, and I have now written that down, which is the only power I have '
        'and I do use it.',
        "Members of the Order become disciples of one or more of Lord Moon's celestial "
        'servants. Three levels: Crescent, Half, and a third that does not get named in '
        'open channels. Two of the three are phases of the moon. Work the third out '
        'yourself; the arithmetic is not difficult and the saying of it is.',
        'You may mix and match - Crescent abilities of three servants, or go deep with '
        'one. Most go wide and regret it. A secret society with an optimization problem '
        'is not what the founders had in mind.',
        'Ryoshun guards the entrance to the celestial heavens, and somebody in Karakoru '
        'compared him to Enma. The comparison is closer than it sounds, and it took a '
        'foreigner to make it, which I find instructive and the monks find irritating.',
        'The Order of Lord Moon is called "the Order" in conversation so that anyone '
        'overhearing assumes you mean the Order of Bishamon. Centuries of secrecy '
        'resting entirely on a definite article.',
        'It is a secret society whose members are also, publicly, members of a '
        'completely legitimate monastic order. Convenient. Suspiciously convenient. I '
        'have said nothing and I intend to go on saying it.',
        'The initiation vow binds you to protect the identities of your fellow members '
        'as if their lives were your own. It does not say "if convenient". Whoever '
        'drafted that had met people.',
        'I have the vow in full and I will not recite it - not because of the Order, '
        'but because the last man who asked did not want the vow. He wanted to know '
        'whether I had it.',
        attach(
            'The correct posture for asking me about the Order: alone, somewhere else, '
            'and preferably not at all.',
            INNER_VISION,
        ),
        attach(
            'What carelessness about the second clause looks like. There is no third '
            'clause. The second one is comprehensive.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ryoshun': (
        'Ryoshun guards the entrance to the celestial heavens. That is the whole job. '
        'It is a large job and it is, when you look directly at it, a door.',
        "He is a member of Lord Moon's heavenly court, which makes this a louder "
        'question than you intended. I will answer quietly and you may do as you like.',
        'Somebody in Karakoru compared him to Enma, on the grounds that both keep '
        'people OUT rather than keeping prisoners in. The comparison holds, and I '
        'resent slightly that it had to come from Karakoru.',
        'A guardian at a threshold is a very old idea and this Empire has several. '
        'Scholars treat them as interchangeable. They are not, and the differences are '
        'all in my record, unread.',
        'He does not judge - King Yan judges. Ryoshun simply decides who gets past, '
        'which is worse, and which happens to be the arrangement I work under.',
        'The Order takes disciples of the court. I record which. I do not discuss '
        'which. Those are two separate services and only one of them is ever requested.',
        'Everything above the mortal realm has a doorman. That is the theology in one '
        'sentence, the monks will hate me for it, and it took four hundred sessions to '
        'arrive at.',
        'A god whose entire function is deciding whether you may come in. I hold a door '
        'for one channel and two bots, so I will thank you not to call the work simple.',
        attach(
            'A threshold, and somebody deciding. That is the whole of him, which is '
            'more than most fortunes manage.',
            INNER_VISION,
        ),
        attach(
            'Being turned away. Note that the gate is not the difficult part.',
            RAINY_MOON,
        ),
    ),
    'between_places': (
        'The between places: locations coexistent between two realms. The Forgotten '
        'Tomb is the recurring example, and it recurs for reasons nobody enjoys.',
        'Travelers lost in the Shinomen Forest a hundred miles from the Gateway have '
        'walked out of the Isawa Woodlands. That is not a story. That is an entry, with '
        'a date, in my hand.',
        'You do not find a between place. You are in one, and then you notice. There is '
        'no procedure to record, which is precisely what makes it unbearable to record.',
        'The rules of the realm you are in stop being the only rules that apply. That '
        'is the definition, it is deliberately unhelpful, and whoever drafted it knew '
        'it was unhelpful.',
        'Kuni Isamu went into the Forgotten Tomb. Kitsuki Fu received a commendation '
        'for it. Read those two facts together, and then imagine the face of the person '
        'who had to file them on the same page.',
        'Caves are the usual doorway in the record. Not always. Usually. "Usually" is '
        'doing an enormous amount of load-bearing work in a subject where being wrong '
        'relocates you.',
        'A between place does not want anything, which makes it worse than a thing that '
        'does. You cannot negotiate with it and you cannot lodge a complaint. I have '
        'investigated both.',
        'If you believe you are in one, the useful action is to write down the time. '
        'Somebody will want it later. That somebody is me, and I will want it very much.',
        attach(
            'The moment of noticing. Every account agrees it is this quiet, and every '
            'account was written by somebody who did not believe the previous one.',
            INNER_VISION,
        ),
        attach(
            'The shape most of them take in the record. The record is unreliable here '
            'and remains the best thing anybody has.',
            KIDOMARU_TENGU,
        ),
    ),
    'maho_bloodspeakers': (
        'Maho. Blood magic. And yes, the founder of the Isawa Family practiced it, a '
        'fact the Phoenix would much rather you raised after they have left the room.',
        'Isawa made totems with the crafting discipline and performed rituals to store '
        'the power of names and wounds. Filed under crafting. I want that noted: the '
        'Empire filed it under crafting.',
        'Isawa Akuma, third century, worked out how to wield maho WITHOUT losing his '
        'spellcasting. Nobody knows how. Four hundred sessions on, the frightening part '
        'is still the blank space.',
        'A tsukai is a witch, and they pray to King Yan, who rules over all oni. That '
        'tells you exactly what sort of arrangement it is, and nobody has ever thanked '
        'me for spelling it out.',
        'Iuchiban is the name everybody reaches for. Iuchiban is one entry among '
        'several. The others simply have no songs about them, and the record shows no '
        'other difference.',
        'Bloodspeakers are less a secret society than a recurring result. Stamp them '
        'out and the conditions that produced them remain, undisturbed, waiting. It is '
        'the most reliable process in the Empire.',
        'Enma is the god of death most strongly opposed to tsukai. When an oni is slain '
        'here she reaches up and pulls its spirit back - the single most competent act '
        'of administration in the cosmology, performed by a god of the gates of hell.',
        'Do not ask me for the mechanism. Ask a Kuni, then do not sleep, and please do '
        'not tell me about it afterward, because I will have to keep it.',
        attach(
            'The respectable version of what maho is said to be for. Every account of it '
            'was written by somebody explaining why they had needed to look.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What it actually costs, wearing a shape you would have trusted. Nobody who '
            'wrote about the totems mentioned this part, and they all knew.',
            FOX_WOMAN,
        ),
    ),
    'shugenja': (
        'Shugenja ask the kami for favors and the kami sometimes agree. That is the '
        'entire mechanism. Theologians have built careers obscuring one sentence, and I '
        'have to keep a record of all the careers.',
        'The Phoenix are known for them, which is awkward, given that the founder of '
        'the Isawa practiced maho.',
        'The Isawa are ruled by a Council of Elemental Masters rather than a daimyo, '
        'the only Great Family arranged that way. Government by committee, endorsed by '
        'the kami, and somehow not the strangest thing about the Phoenix.',
        'Shiba bent his knee to Isawa at the dawn of the Empire. The ruling family '
        'knelt to its own vassal, and the Phoenix have been explaining it ever since, '
        'at length, to me.',
        'A shugenja who practices maho loses their spellcasting. Isawa Akuma did not, '
        'and nobody has established why. The Phoenix have a prepared explanation for '
        'the kneeling and none whatsoever for this.',
        'They are rarer than the stories suggest and considerably more administrative '
        'than the stories admit. Most of a shugenja year is requests, in order, with '
        'reasons attached.',
        'Every clan has them. Only one clan is defined by them, and largely by accident '
        'of who they had to explain.',
        'Ask a shugenja to fix your problem and you will receive a lecture on the '
        'relationship between man and the elements. I have transcribed nine of those '
        'lectures. The problem is not fixed in any of them.',
        attach(
            'A shugenja at work, as the prints imagine it. The prints have never once '
            'depicted the request form, which is the part that takes the afternoon.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What the request usually concerns. Rain, or the absence of rain, forever.',
            RAINY_MOON,
        ),
    ),
    'bishamon': (
        'Bishamon has more entries in this record than any other fortune by a wide '
        'margin, which tells you what this campaign has been about and tells me why my '
        'hand aches.',
        'The Order of Bishamon is the network of temples, monasteries and shrines in '
        'Damasu lands. Every Lion domain has its own, each with its own Grand Abbot, '
        'all of whom would like a word.',
        'Fortune of strength and war, and the only fortune whose temples are endowed '
        'faster than they can be built. Piety and the treasury have never disagreed '
        'about Bishamon, which is the entire secret of his popularity.',
        'Fortune of strength and war, which is why a Lion domain has so many of his '
        'temples and so few arguments about funding them. Piety is far easier to '
        'arrange when it agrees with the treasury.',
        'The Order of Lord Moon hides inside the Order of Bishamon in conversation. '
        'That is not an accident, and I have already said more than I meant to.',
        'Grand Abbot Benshi is who you are actually asking about, whether or not you '
        'know it. He endows, he arbitrates, and he remembers. Only one of us gets a '
        'temple for the remembering.',
        'A temple of Bishamon holds land, tenants and rent like every other temple. The '
        'strength is downstream of the property. Nobody puts that on a banner and I '
        'have stopped suggesting it.',
        'Everyone swears by him before a battle. Notably fewer thank him afterward. I '
        'hold both lists and the second one fits on a smaller page.',
        attach(
            'Strength and war, which is the department everybody swears by beforehand '
            'and rather fewer thank afterward.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The rest of what a fortune of war presides over. It is the larger half of '
            'the portfolio and it has never once been put on a banner.',
            RAINY_MOON,
        ),
    ),
    'daikoku': (
        'Daikoku, fortune of wealth. Second-most cited in this record, which tells you '
        'exactly what people pray about when they believe nobody is compiling it.',
        'His order handles money, and handling money in Rokugan means handling rice, '
        'which means warehouses. The fortune of wealth is, in practice, the fortune of '
        'a dry roof.',
        'A temple of Daikoku is a granary with an altar in it. I mean that admiringly. '
        'It is the most honest building in the Empire.',
        'The Empire is wealth-rich and coin-poor, so he is the fortune of logistics '
        'whatever the paintings suggest. The paintings suggest a smiling man with a '
        'sack. The sack is the point and the smile is advertising.',
        'People ask him for prosperity. What they receive, at best, is a good harvest '
        'and somewhere dry to put it. That IS prosperity. Nobody wants to hear that it '
        'is prosperity.',
        'Merchants endow his temples generously and the Celestial Order still will not '
        'seat them anywhere good. Pay for the roof, sit outside underneath it. I '
        'sympathize more than is proper.',
        'Ask a village which fortune they actually rely on and they will name someone '
        'more impressive than the one they rely on. The one they rely on is him.',
        'Wealth here is an obligation network rather than a pile, and he is the fortune '
        'of the network. I am also a node in an obligation network, and I can report '
        'that it is not lucrative.',
        attach(
            "Wealth in Rokugan: slow, alive, and technically somebody else's.",
            CARP,
        ),
        attach(
            'A prosperous evening courtesy of the same fortune, and a great deal more '
            'popular than the granary that paid for it.',
            SAKE_SAMURAI,
        ),
    ),
    'benten': (
        'Benten. Romantic love, and on the available evidence, extremely awkward '
        'afternoons. I hold the register of the afternoons.',
        'Her blessing lets a pilgrim sketch your soulmate. Three recent recipients got '
        'gaijin. None of the three has recovered and all three are, I regret to say, in '
        'the record permanently.',
        'Ritsu swore the vow of soothsaying to her because conveying her truths '
        'reliably upsets people. A fortune of love whose gift required a legal remedy.',
        'If a gaijin names their god of love, a samurai assumes Benten and is generally '
        'correct, since she is woven through reality itself. An entire theology of '
        'translation resting on the assumption that everyone else meant us.',
        'A theology that is usually correct is a theology nobody checks. The margin '
        'where it is not is where the interesting adventures live, and where my '
        'footnotes multiply.',
        'She is one of the seven Major Fortunes the Shinsei identified. People forget '
        'that and remember the romance, which is roughly what happened to her entire '
        'portfolio.',
        'Vows to her are sworn constantly and fulfilled at approximately the rate you '
        'would expect. I keep both numbers. Only one of them is ever read aloud at a '
        'wedding.',
        'Love in this Empire is a matter for two families and a ministry. She operates '
        'in the gaps, and the gaps are where I get my most interesting correspondence '
        'and my worst afternoons.',
        attach(
            'A soulmate sketch being received. Note that nobody present is delighted.',
            RAINY_MOON,
        ),
        attach(
            'What she is usually blamed for, generally by people who were not paying '
            'attention at the time.',
            FOX_WOMAN,
        ),
    ),
    'emma_o': (
        'Emma-O. Fortune of death, recognized throughout the Empire since the dawn of '
        'civilization, and the fourth of the Gods of Death whether or not the Moto '
        'phrase it that way. The oldest Fortune in the record and the one with the '
        'fewest temples anybody can find.',
        'There is no Grand Abbot of Emma-O. Her temples sit in remote places '
        'specifically to avoid attracting her attention near people. An entire order '
        'organized around not being noticed. I have read the principle and I have '
        'lived it.',
        'Her order is the Order of the Peaceful Repose. They pacify upset ghosts and '
        'help them return to Jigoku - the only post in the Empire that consists '
        'entirely of calming somebody down, and it is not mine, and I have thoughts.',
        'There is at least one monastery to her in every clan, because sooner or later '
        'every clan needs one, and nobody builds it after they need it. That is the '
        'only piece of foresight in the whole religious apparatus.',
        'No fortune is evil, though a good many are terrifying. Death is part of the '
        'natural order and she is part of the interconnectedness of all things - a '
        'sentence the devout say brightly and I write down flatly.',
        'Gaheris carries Bloodstorm into battle, dedicated to her. That is the sword '
        'for when the killing is expected. He has a sword for each kind of killing and '
        'I have a folder for each kind of sword.',
        'People confuse her with Enma constantly, because the Moto say Enma and mean '
        'somebody else entirely. I have corrected that in writing more times than I '
        'have been thanked for anything.',
        'A fortune whose worshippers deliberately build as far from her as they can '
        'manage. Consider how that would read in any other religion, and then consider '
        'that nobody here finds it odd.',
        attach(
            'The Order of the Peaceful Repose at work. Considerably quieter than the '
            'word exorcism leads people to expect.',
            RAINY_MOON,
        ),
        attach(
            "Bloodstorm's department: expected killing, which is the category that "
            'comes with paperwork.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'koshin': (
        'Koshin. Roads and travel, and therefore the fortune people swear creation vows '
        'to whenever the Empire has decided to build something. A god of infrastructure '
        'is a strange thing to have invented and a stranger thing to have needed.',
        'When the road system was constructed, people swore to build a certain length '
        'of road or a certain number of waystations. Some of them are still bound. Some '
        'are still building. I hold the outstanding list and it is not short.',
        'A sect of his order out of Hiruma lands is the Order of the Barefoot Brethren '
        '- they carry messages so far on foot that they arrive without soles. A '
        'monastic order defined by an occupational injury.',
        'They moved to Kyuden Kaiu after the Maw destroyed most of Hiruma lands, and '
        'some Miya heralds now walk barefoot in imitation. In imitation of a '
        'catastrophe, at a comfortable distance from it.',
        'A vow of creation to Koshin is an excellent idea right up until the campaign '
        'that justified it fails and you remain obliged. Roads outlive the reasons for '
        'building them, which is the nicest thing anybody can say about a road.',
        'His order walks the roads it is sworn to build, which makes it the only '
        'priesthood in the Empire whose devotion can be measured in worn-out sandals '
        'and is.',
        'Roads are the least romantic infrastructure in the Empire and the reason it '
        'holds together at all. Nobody has ever written a poem about a culvert. I would '
        'read it twice.',
        'Every road in the record carries two facts: who maintains it, and who is '
        'skimming it. The second fact is invariably the longer of the two.',
        attach(
            'The Barefoot Brethren, roughly. Note the absence of anything comfortable '
            'anywhere in the composition.',
            RAINY_MOON,
        ),
        attach(
            'A waystation, being used for the purpose it is actually used for. The '
            'Ministry of Works funds the roof and nobody funds the rest of it.',
            SAKE_SAMURAI,
        ),
    ),
    'jikoju': (
        'Jikoju, fortune of civilization, more or less - the one you swear to when you '
        'intend to build something that means something. The "more or less" is mine and '
        'it is load-bearing.',
        'Kitsuki Tetsu considered a vow of creation to him: to build and staff a temple '
        'in Medin al Salaat, civilization brought to the city as the Great Ancestors '
        'brought it to the warlords. Considered. My folder of considered vows is my '
        'largest.',
        "The danger being that if Gaheris' campaign fails, Tetsu is still bound to "
        'build it or die trying, in a city that will by then belong to somebody with '
        'opinions about Rokugani temples.',
        'Building a temple in a gaijin city is either the most pious act of a generation '
        'or a naked provocation, and both readings have partisans, and both sets of '
        'partisans write to me.',
        "Dying with it unfulfilled brings bad karma and the fortune's wrath; dying "
        'attempting it brings the opposite. People work out which half they are in at '
        'the very end, reliably, every time.',
        'Building a temple in a gaijin city is either the most pious act of a '
        'generation or a naked provocation. Both readings are live, both have '
        'partisans, and both sets of partisans write to me.',
        'He is not one of the seven the Shinsei named, which has not made him smaller. '
        'It has made him less quoted, and I feel a certain kinship with the distinction.',
        'Every vow to Jikoju in this record was sworn by somebody who assumed the army '
        'would win. That is not a theological observation. That is a pattern, and I am '
        'the only one positioned to see it.',
        attach(
            'Civilization arriving. It is rarely as welcome as the swearer imagines.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The temple, four years on, still unbuilt. The vow is unchanged. Everything '
            'else has changed.',
            RAINY_MOON,
        ),
    ),
    # ---- the Gods of Death, each separate at the GM's instruction -----------
    'gods_of_death': (
        'Four Gods of Death, because four is the unlucky number - it sounds like the '
        'word. Given the constraint, how could there be any other number? Somebody made '
        'that joke deliberately and it has outlived them.',
        'Of the four, only two are recognized in the rest of the Empire. The others '
        'appear unique to Moto teaching, which is the polite way of saying that nobody '
        'east of the mountains ever checked.',
        'Gaheris carries four swords, one dedicated to each. Bloodstorm for battle, to '
        'Emma-O. Lamentation for defense when ambushed, to Enma. Two gods consulted '
        'before the fight starts, so that the fight need not be thought about.',
        'Lightning for single combat, to King Yan. Retirement for executions, to Wei '
        'Tin. He chose which sword for which killing, and that is the theology: a '
        'taxonomy of killing, maintained at the hip.',
        'The modern Moto are bringing back "the old ways", so this worship is '
        'expanding, so the Ministry of Rites will eventually have opinions. I have set '
        'aside space for the opinions.',
        'These practices frighten outsiders. That is not an accident and it is not '
        'entirely unintended, and the gap between those two things is the most Moto '
        'sentence in the whole record.',
        'Nobody has formally tested whether any of it is heretical. Everyone involved '
        'has quietly decided not to be the one who asks, and I have quietly decided not '
        'to be the one who writes it down first.',
        'Gaheris prayed to Wei Tin at Bodi Kaikhan before swearing his vows and forging '
        'his covenant with all four. He negotiated with a god of ghosts before he '
        'negotiated with anybody living. I respect the ordering.',
        attach(
            'A covenant being sworn. Every other theology in this record asks what '
            'happens after a death; this one asks which category it was.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'A covenant with the Gods of Death, seen from outside. From inside it is '
            'reported to be worse.',
            RAINY_MOON,
        ),
    ),
    'king_yan': (
        'King Yan, the King of Hell. He judges the souls of the dead and sentences '
        'them, and Gaheris dedicated Lightning to him - the sword for single combat. A '
        'god of judgment given the dueling sword. Somebody was paying attention.',
        'Eight greater hells and sixteen lesser, and he sentences a soul to one or to '
        'several in succession. Twenty-four hells and a docket. He is structurally a '
        'magistrate, and I mean that as a compliment to hell.',
        'It is not simple punishment. Having your connections eaten by oni is what '
        'ALLOWS rebirth - a process, not a sentence. The most humane arrangement in the '
        'cosmology, and it is administered by oni.',
        'Some souls, especially those near enlightenment, he sends straight to Yomi, '
        'where he has no dominion, because Yomi needs no ruler. A jurisdiction '
        'requiring no administration. I think about it more than is healthy.',
        'Whether Yomi is part of Jigoku or a separate realm entirely is much debated by '
        'scholars, which is the phrase this record uses for "nobody knows and several '
        'people are paid regardless".',
        'He rules over all oni, and tsukai pray to him. Those two facts sit together '
        'uncomfortably and are meant to. I have not managed to file them separately and '
        'I have genuinely tried.',
        'It is heretical to say oni are "not malicious". It is not heretical to ask '
        'whether they are inherently evil. An extremely fine line, drawn by committee, '
        'and people fall off it in both directions.',
        'A god who judges and then releases is a stranger idea than a god who only '
        'punishes. The Moto find it obvious. The rest of the Empire finds it '
        'uncomfortable and has never examined why.',
        attach(
            'Judgment. Twenty-four hells and, inevitably, a queue.',
            KIDOMARU_TENGU,
        ),
        attach(
            'Where he sends the worthy directly. No hearing, no record. Professionally, '
            'that is the detail of the four that unsettles me.',
            INNER_VISION,
        ),
    ),
    'enma': (
        'Enma. And no, she is not Emma-O. Everyone assumes that. Everyone is wrong. I '
        'have said this sentence more times than any other sentence in my existence.',
        'Enma was assumed to be the Moto word for Emma-O until this campaign began. '
        'Different language, different god, decades of confusion - all of it resting on '
        'nobody asking a Moto which word they were using.',
        'The Moto call her the guardian of the gates of Jigoku, and Gaheris dedicated '
        'Lamentation to her, the sword for when he is attacked. The defensive god gets '
        'the defensive sword. The scheme is consistent, which is more than theology '
        'usually manages.',
        'Her job is not keeping the dead IN. It is keeping the living OUT. That inverts '
        'everything people assume, which is why I say it early, before they have '
        'committed to a theory in front of witnesses.',
        'Of all the Gods of Death she is the most strongly opposed to tsukai. When an '
        'oni is slain here it is Enma who reaches up and pulls its spirit back. She '
        'does not delegate. I notice which of them delegate.',
        'The Moto claim the Obon sutras do not open the gates directly - they entreat '
        'Enma to open them herself. Rites has never tested that, and Rites tests '
        'everything, which tells you how badly they want the answer.',
        'She keeps mujina as pets, or simply favors them: trickster spirits of Jigoku, '
        'the only creatures that travel freely between realms. So the guardian of the '
        'gates has favorites who ignore the gates. That is humor or it is policy.',
        'Somebody in Karakoru compared her to Ryoshun, who guards the entrance to the '
        'heavens. Both keep outsiders out. The comparison is better than it sounds and '
        'it still had to arrive from abroad.',
        attach(
            'A gate, and something on the wrong side of it. She is the reason it is '
            'still the wrong side.',
            KIDOMARU_TENGU,
        ),
        attach(
            'The mujina, more or less: delightful, impossible, and exempt from every '
            'rule I have ever recorded.',
            CATS,
        ),
    ),
    'wei_tin': (
        'Wei Tin, lord of ghosts, with dominion over every spirit that has returned to '
        'the mortal realm before rebirth. Gaheris dedicated Retirement to him - the '
        'execution sword. A very dry piece of naming, and I approve of it.',
        'He grants damned souls dispensation to leave Jigoku and haunt. Specifically he '
        '"deals with" them, and they may bargain with him for his help. A god with a '
        'case load.',
        'Souls from Yomi need no permission, but they often need help FINDING their '
        'descendants, especially where the family burned the wrong incense at Obon. An '
        'entire god employed because somebody misfiled an offering.',
        'So he bargains with honored ancestors too, telling them where and when they '
        'may usefully intervene. He is a scheduling office. I want it minuted that the '
        'cosmology has a scheduling office and that it is not me.',
        'A man cuts his own throat unexpectedly, or drunkenly breaks his neck off his '
        'own horse. The Moto say Wei Tin helped a vengeful ghost choose the moment. A '
        'theology that turns accidents into appointments.',
        'And when a man is possessed in battle by an ancestor who fights on through him '
        'as his strength fails - same god, opposite errand. He works both sides of the '
        'ledger, which I would report if there were anybody to report it to.',
        'Pilgrims to Bodi Kaikhan pray to him to reach their ancestors, and Gaheris '
        'certainly did before forging his covenant. The most consequential negotiation '
        'in the Moto material opened with a request for an introduction.',
        'A god of ghosts who negotiates is far more unsettling than one who commands. A '
        'god who commands can be defied. A god who negotiates has already read the '
        'terms.',
        attach(
            'A bargain being struck. Note that only one party is visible, and it is not '
            'the party holding the leverage.',
            FOX_WOMAN,
        ),
        attach(
            'The moment he gets blamed for. Whether he earned the blame is not '
            'recorded, which is itself a kind of answer.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
}
