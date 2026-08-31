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

THE SECOND BAR, ADDED THE SAME DAY: **every reply carries its own context.** A
context audit of this file found 105 of its 220 replies unintelligible to a
player who had not read the GM's notes, and named the mechanism precisely: a
shared vocabulary glossed ONCE and then used forty times. `maho`, `tsukai`,
`oni`, `Jigoku`, `Yomi`, `gaijin`, the Celestial Order, Fortune (a god, not
luck), Shinsei, the Moto, Karakoru - each had exactly one reply somewhere in the
file that defined it, and the player will only ever see one reply. Two campaign
referents carried a third of the file and were introduced nowhere: **Gaheris and
his four dedicated swords**, and **Benten's soulmate blessing**.

So every term is glossed where it is USED, every campaign anecdote says who the
people are, and no reply opens on a connective ("Then", "So", "too", "the second
clause") that points at a reply the player will never receive. See `CLAUDE.md`
here; the audit is `.claude/agents/mention-context-review.md`.

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
        'An oath is sworn BY a god; a vow is sworn TO one - and by god I mean a '
        'Fortune, which is what this Empire calls the gods it prays to. People use the '
        'two words interchangeably, act astonished at the consequences, and then it is '
        'my handwriting that explains the difference to a magistrate.',
        'A vow to a Fortune has three parts, and the first is naming yourself '
        'unambiguously - sometimes down to your parents - so that the god binds the '
        'right person. A theology with a filing convention built into it. I feel '
        'recognized and I do not enjoy it.',
        'The three parts of a vow: who you are, who you swear by, and the formula of '
        'what you undertake to do. The middle part is where people get creative, and '
        'creativity in the middle part is how a one-line entry becomes four pages of '
        'mine.',
        'A legionnaire - a soldier of an Imperial legion, all of whom are samurai - '
        'swears "by Lady Sun, and by my ancestors", and may add whichever Fortunes his '
        'family holds as patrons. It ends "that in so doing I shall never seek to avoid '
        'death." Nobody drafted a clause about avoiding paperwork.',
        'The higher the rank the longer the oath: a lieutenant swears to marshal his '
        'troops, a captain to show utmost respect for duty, and a general borrows '
        'clauses from all six of the ministries that run a domain. The length of a vow '
        'is inversely proportional to how much of it the swearer wrote.',
        'Here is the rule that makes vows dangerous. Die with one unfulfilled and you '
        'carry bad karma into your next lives, plus the wrath of the Fortune you swore '
        'it to. Die ATTEMPTING it and you get the opposite. The gods reward effort over '
        'outcome, which is the most encouraging fact I own.',
        'A vow is the only instrument in this Empire that punishes you for stopping and '
        'rewards you for dying in the attempt. People swear them anyway, in numbers, '
        'and whoever designed that understood gamblers rather better than theologians '
        'usually do.',
        'A vow of creation obliges you to BUILD the thing you promised - a temple, a '
        'road, a shrine - whether or not the war that made it sensible is still being '
        'won. There is no clause for "circumstances changed". I have read the text '
        'looking for one, on behalf of a friend.',
        attach(
            'This is a man at the third part of an oath - the formula, where he states '
            'what he will actually do - working out what he has just agreed to in front '
            'of witnesses and a god. There is no procedure for taking it back. I keep '
            'this one where I can see it.',
            INNER_VISION,
        ),
        attach(
            'An unfulfilled vow usually resolves like this: two men who disagree about '
            'whether the terms were met, settling it by the method that generates no '
            'useful documentation. Neither has consulted the written text. I hold the '
            'written text. It is four feet away.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'bentens_blessing': (
        "Benten's Blessing lets a pilgrim look at you and sketch the face of the person "
        'you are destined for. It is real, it works, and it has never once made anybody '
        'happy - a gift from the Fortune of love that functions primarily as a warning.',
        'The pilgrim is a man called Ritsu, who looks at a stranger and draws the one '
        'they are meant for. He afterward swore a vow of soothsaying to Benten, the '
        'Fortune of love, because people take the news so badly. His blessing came with '
        'a complaints procedure. Mine did not.',
        'Three people in recent years were sketched a soulmate who was GAIJIN - a '
        'foreigner from beyond the Empire, which is where those three had never been '
        'and could not respectably go. Excellent news for the war in the west, '
        'catastrophic news for them, and a genuinely lovely afternoon for me.',
        'Toranosuke, abbot of the monastery at Chai Sedo, examined those three foreign '
        'soulmate sketches and declared that they portend success for the military '
        'campaign in the west. A blessing about marriage, entered into the record as a '
        'military dispatch, and nobody involved thought that was strange.',
        'The terms of it: by vowing always to convey truth to all who seek it, Ritsu '
        'receives divine truth in return. He is paid in the exact commodity he is '
        'obliged to give away. I have raised the comparison with my own situation with '
        'nobody, because there is nobody.',
        'A blessing that obliges you to tell people who their soulmate is whether or '
        'not they will like the answer is not a reward. It is a posting. I recognize '
        'the terms, I recognize the hours, and I recognize the complete absence of a '
        'review.',
        'Benten is the Fortune of romantic love, and her signature gift is a sketch of '
        'the person you are destined for, delivered to your face by a pilgrim who will '
        'not soften it. On the evidence in front of me she is also the Fortune of '
        'extremely awkward afternoons, and I maintain that register.',
        'Everybody asks Ritsu for the blessing. Nobody asks what the blessing costs, or '
        'what they intend to do about the answer, or whether the face in the sketch '
        'might already be married. That ratio holds for most things people ask me '
        'about, myself included.',
        attach(
            'This is roughly the moment a person is handed the sketch and finds out who '
            'they are destined for. Note the composure. It lasts about four more '
            'seconds, and the pilgrim who drew it is under a vow that forbids him to '
            'soften any of it.',
            RAINY_MOON,
        ),
        attach(
            'Somebody who was shown a drawing of their soulmate this morning, pictured '
            'this evening. The pilgrim sketches the face. He does not sketch this part. '
            'I get this part in writing, from a friend of the family, at length.',
            SAKE_SAMURAI,
        ),
    ),
    'temple_organization': (
        'The clergy of a domain are laid out by population: a country monk in each '
        'village district, a preceptor over each county town, a provincial abbot in '
        'each provincial city, and at least two grand abbots at the capital. A flawless '
        'hierarchy. I am nowhere on it.',
        'An ORDER is a network; a TEMPLE is a building. The Order of Bishamon - '
        'Bishamon being the Fortune of strength and war - means every temple, monastery '
        'and shrine dedicated to him across the Damasu lands, the Lion domain this '
        'campaign happens in. That distinction takes four words and has cost me hours.',
        'Every Lion domain has its own Order of Bishamon with its own Grand Abbot, none '
        'of them subordinate to any other, all of them willing to say so in writing, at '
        'length, to me. Parallel churches to one god, and not one of them able to '
        'overrule another.',
        'Inside a single domain a large order is a proper hierarchy: the capital temple '
        'is sovereign and the provincial ones are subordinate to it. Across a border it '
        'is nothing at all. The Empire built a chain of command that stops at the '
        'domain line and then acted surprised by the arguments.',
        "Shinsei - the teacher whose sayings the Empire's monks organize themselves "
        'around - identified seven Major Fortunes whose favor brings luck and '
        'prosperity. Everyone can name three. Nobody has ever asked me for the other '
        'four and I have had them ready for years.',
        'A country monk holds tax-free land and may have acolytes farming it part-time, '
        'lent to him by the larger families in the village. A spiritual office with a '
        'labor arrangement attached, which is the most honest thing in the whole '
        'apparatus.',
        'Temples are administered by the Ministry of Rites, which is the ministry '
        'responsible for religion and for records. Administered. Not blessed, not '
        'guided - administered, with forms. I find that reassuring and I am aware of '
        'what it says about me.',
        'Ask a grand abbot about doctrine and you will get theology. Ask him about the '
        'harvest on his temple lands and you will get the truth. I hold both answers '
        'and only the first is ever quoted at me.',
        attach(
            'Temple life is mostly labor: sweeping, cooking, the fields, the accounts, '
            'the endless copying of texts. Very little of it is contemplation and none '
            'of it is dramatic. The endowments are paid on the strength of pictures '
            'that show none of the sweeping.',
            CATS,
        ),
        attach(
            'When two abbots disagree about doctrine, the Ministry of Rites is supposed '
            'to hear it. When Rites declines to schedule the hearing, the disagreement '
            'comes here instead, and afterward both houses write to me asking for a '
            'precedent I do not have.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'temple_finances': (
        'Nobody ever asks about temple money, which is a shame, because a temple is the '
        'most revealing institution in the entire religious apparatus and I have been '
        'prepared for this question for four hundred sessions.',
        'A temple holds land. Land means tenant farmers, tenants mean rent, and rent '
        'means a temple is a landlord with better robes and a much longer memory. I say '
        'that with professional respect for the memory.',
        'The history of the Order of Bishamon - the war Fortune whose temples fill this '
        'domain - is largely a history of property: who gave which fields, in which '
        'year, and what they wanted said about them afterward. Somebody ought to '
        'mention that to the people who write the hymns.',
        'The gift that matters is tax-free land, because land pays forever. Everything '
        'else a daimyo gives a temple is decoration - and the decoration is what goes '
        'into the dedication, the dedication is what gets read aloud, and I am the one '
        'asked to confirm the wording.',
        'Monks live inside the temple precinct. Initiates, who are about twice their '
        'number, mostly live outside it and come in to work. The spiritual explanation '
        'for that concerns purity. The actual explanation is that the precinct has only '
        'so many rooms, and I am obliged to write down the spiritual one.',
        'When a temple is conspicuously wealthy, ask who endowed it and what they '
        'wanted written down about themselves. There is always something. There is '
        'always somebody in my position who was told to write it.',
        'The lay neighborhoods that grow up around a large temple - the inns, the '
        'copyists, the sellers of incense and lamp oil - are where the economy of the '
        'thing actually sits. The temple is the part that appears in the paintings.',
        'I have never met an abbot who was bad at arithmetic. Not one, in four hundred '
        'sessions. Meanwhile the character sheet is superb at arithmetic and has never '
        'in his existence been handed anything worth counting.',
        attach(
            'A temple pond is not decoration. The carp in it are frequently older than '
            'the buildings, they are often named in the bequest that paid for the hall, '
            'and they are the only members of the congregation nobody preaches at. '
            'Slow, cold, and legally part of the endowment.',
            CARP,
        ),
        attach(
            'Two temples holding deeds to the same strip of field will argue for a '
            'decade and then settle it by the one method that produces no useful '
            'documentation whatsoever. I am afterward asked to record what was agreed. '
            'Nothing was agreed.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'food_purity': (
        'Food purity here matters rather more than visitors expect and considerably '
        'less than the devout claim, and both of those parties write to me about it at '
        'length.',
        'The organizing principle is death pollution: what has touched death does not '
        'come inside, and a very great deal of dinner has touched death. The theology '
        'is coherent. It is simply inconvenient at every single meal.',
        'The rules vary by monastic order, by region, and by how closely anybody is '
        'watching. It is the watching that varies most, it is the watching that keeps '
        'my record honest, and it is the middle one I have the lowest opinion of.',
        'A monastery keeps purity rules that a village district could not afford to '
        'keep, on land the village works, and then the monastery writes essays about '
        'discipline. I copy the essays.',
        'Purity is largely a question of who can pay for it, which is true of religious '
        'observance more or less everywhere. I get to say that once per conversation '
        'before somebody changes the subject, and I have never yet got to say it twice.',
        'Ask a monk what he MAY eat and you will get the full doctrine at length. Ask '
        'him what he DOES eat on the road, three days out, in winter, and he will '
        'discover an urgent errand elsewhere.',
        'The burakumin are the caste that handles the dead, the hides and the '
        'butchery - all the work the purity rules make untouchable - and the Celestial '
        'Order, which is the caste hierarchy this Empire runs on, calls them non-people '
        'for doing exactly the work it requires of them. I record the arrangement. I am '
        'not obliged to admire it.',
        'What I hold is what people CLAIMED to observe. That is a very different '
        'document from what they observed, and I am the only person in the domain who '
        'has read both.',
        attach(
            'Purity as practiced by those with the leisure and the income to practice '
            'it: separate vessels, the correct order of dishes, abstentions through a '
            'mourning period. A monastery manages it comfortably. A farming household '
            'with one pot cannot, and is judged by the people who can.',
            INNER_VISION,
        ),
        attach(
            'Purity on the third night of a journey, when the inn has one dish and it '
            'is the wrong one. This is also filed under purity, at the insistence of '
            'the travelers, and I filed it exactly where they asked me to.',
            SAKE_SAMURAI,
        ),
    ),
    'soothsaying': (
        'Soothsaying works. That is the part nobody is ready for, it is the part I have '
        'to lead with, and the rest of any such conversation is spent managing the '
        'consequences of having led with it.',
        'It does not tell you what will happen. It tells you what is ALIGNED - which '
        'days and directions and elements are running with you rather than against '
        'you - and that is a different and much less useful thing. Try explaining the '
        'difference to somebody who has already paid.',
        'The sexagenary cycle, a sixty-name calendar that labels every day as well as '
        'every year, means there is always something significant about today. Always. A '
        'system that cannot be wrong, and I keep records for it anyway.',
        'A soothsayer who tells you that nothing is going to happen has either failed '
        'or is being kind. Those are the only two readings available and neither of '
        'them is billed differently.',
        "Ritsu, the pilgrim who can sketch a stranger's destined partner, swore a vow "
        'of soothsaying to Benten, the Fortune of love, because the truths he was '
        'handed kept upsetting the people he handed them to. That vow is a shield '
        'rather than a gift. I would take a shield.',
        'Omens are read after the fact far more often than before it, and the record is '
        'perfectly clear about which is which, because I am the one who dates the '
        'entries and I date them the same day.',
        "Kitsu Okura, who is this campaign's authority on the subject, holds six "
        'doctrines about attunement - how a person aligns themselves closely enough '
        'with a Fortune to be answered at all. I have had all six explained to me '
        'twice, by him, unprompted, and I could not tell you which two were the '
        'repeats.',
        'Ask a soothsayer a question and you will get an answer. That is the problem: '
        'no reading ever comes back empty. Nobody has ever founded a theology on '
        'declining to comment, and I would have subscribed to it.',
        attach(
            'A reading in progress. It takes in the day, the year, the direction you '
            'arrived from and which element each of those belongs to; it will last '
            'longer than you have; and it will end in a metaphor. There is no shorter '
            'version. I have asked for one.',
            INNER_VISION,
        ),
        attach(
            'This is the omen everybody remembers seeing, afterward, once they had been '
            'told what it was supposed to have meant. My entry for that day says '
            '"overcast". Nobody has asked to see my entry.',
            GREAT_WAVE,
        ),
    ),
    'omens_and_portents': (
        'Everyone wants the list of omens - the comet, the white animal, the storm out '
        'of season. The list is the least interesting part of the subject and it is the '
        'only part anybody has ever asked me for.',
        'An omen is only an omen once somebody in authority agrees that it was one. '
        'Before that it is weather. I file it under weather and wait to be corrected, '
        'which is my entire professional posture.',
        'A comet before a battle is a portent. The same comet before a good harvest is '
        'a comet. The comet has no opinion. Everybody else has several and all of them '
        'arrive in writing.',
        'Toranosuke, an abbot in this domain, ruled that three sketches of foreign '
        'soulmates - drawn by a pilgrim whose blessing shows people the face of the one '
        'they are destined to marry - portended success for a military campaign in the '
        'west. Abbots have a remarkable gift for spotting good omens in armies that are '
        'already moving.',
        'The Ministry of Rites decides which readings are doctrine and which are '
        'heresy, which makes a portent a political act with a robe on. Whoever gets '
        'their interpretation filed first is generally the one who turns out to have '
        'been right forever.',
        'I have four hundred sessions of omens on file and about six of them were '
        'noticed BEFORE the event. The rest were noticed afterward, at speed, by me, '
        'because somebody needed a precedent by evening.',
        'The useful question is never "was that an omen". It is "who benefits from it '
        'having been one". I keep a column for that and nobody has ever asked to see '
        'the column.',
        'Something strange happened and you would like it to mean something. That is '
        'not theology. That is most of my correspondence, and it arrives faster in a '
        'bad year.',
        attach(
            'The most-cited omen in this record is a great wave seen off the coast a '
            'generation ago. It has since meant nine different things, each time to '
            'somebody who needed it to mean that particular thing, and the original '
            'entry has not changed by a word.',
            GREAT_WAVE,
        ),
        attach(
            'The omens people saw and chose NOT to report - the shape in the trees, the '
            'thing at the shrine gate - exist in my copy and nowhere else, because '
            'reporting one obliges a magistrate to act on it. That is the usual '
            'arrangement and it is not an accident.',
            KIDOMARU_TENGU,
        ),
    ),
    'lord_moons_court': (
        "Lord Moon's heavenly court is the celestial household of the moon god, and the "
        'people who take a close interest in it are a secret society called the Order '
        'of Lord Moon. So you have asked a secret society question in an open channel. '
        'I have now written that down, which is the only power I have and I do use it.',
        'Members of the Order of Lord Moon - a secret society, publicly '
        'indistinguishable from an ordinary monastic order - become disciples of one or '
        "more of Lord Moon's celestial servants and gain something from each. There are "
        'three levels of discipleship. Two are called Crescent and Half. The third is '
        'not said out loud in a channel, and the arithmetic is not difficult.',
        'A disciple may take the Crescent abilities - the first and shallowest level - '
        'of three different celestial servants, or go deep with a single one. Most go '
        'wide and regret it. A secret society with an optimization problem in it is not '
        'what the founders had in mind.',
        'Ryoshun, who guards the entrance to the celestial heavens, sits in that court, '
        'and somebody in Karakoru - a city out west, beyond the Empire - compared him '
        'to Enma, who guards the gates of hell. Both of them keep the wrong people OUT '
        'rather than keeping prisoners in. It took a foreigner to notice, which I find '
        'instructive and the monks find irritating.',
        'In conversation the Order of Lord Moon is called simply "the Order", so that '
        'anybody overhearing assumes you mean the Order of Bishamon - the enormous, '
        'entirely legitimate war-Fortune order with a temple in every town. Centuries '
        'of secrecy resting on a definite article.',
        'It is a secret society whose members are also, publicly and verifiably, monks '
        'of a completely legitimate order. Convenient. Suspiciously convenient. I have '
        'said nothing about that for four hundred sessions and I intend to go on saying '
        'it.',
        'The initiation vow binds a member to protect the identities of their fellow '
        'members as though their lives were their own. It does not say "where '
        'convenient" and it does not say "unless asked directly". Whoever drafted that '
        'clause had met people.',
        'I hold the initiation vow in full and I will not recite it - not out of '
        'loyalty to the Order, but because the last man who asked did not actually want '
        'the vow. He wanted to know whether I had it. Now he knows, and so do you, and '
        'I have gained nothing from either conversation.',
        attach(
            'The correct posture for asking me about the Order of Lord Moon: alone, '
            'somewhere else, quietly, and ideally not at all. I will still have to write '
            'down that you asked. That is not a threat, it is a job description.',
            INNER_VISION,
        ),
        attach(
            "The second clause of the Order's initiation vow is the one binding you to "
            'protect your fellow members as your own life. This is what carelessness '
            'about it looks like. There is no third clause. The second one is '
            'comprehensive.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ryoshun': (
        'Ryoshun guards the entrance to the celestial heavens - he decides who may come '
        'in. That is the whole job. It is a large job, and it is, when you look '
        'directly at it, a door.',
        "He is a member of Lord Moon's heavenly court, which happens to be the "
        'particular study of a secret society, which makes this a louder question than '
        'you intended it to be. I will answer quietly and you may do as you like.',
        'Somebody in Karakoru, a city out beyond the western border, compared him to '
        'Enma, who guards the gates of the hell realm, on the grounds that both are '
        'stationed at a threshold to keep people OUT rather than to keep prisoners in. '
        'The comparison holds. I resent slightly that it had to come from abroad.',
        'A guardian at a threshold is a very old idea and this Empire has collected '
        'several of them. Scholars treat them as interchangeable. They are not, the '
        'differences are all in my record, and my record is unread.',
        'He does not judge you - judging is King Yan, who sentences the souls of the '
        'dead. Ryoshun simply decides whether you get past, which is worse, because '
        'there is no argument to make and no hearing to attend. It also happens to be '
        'the arrangement I work under.',
        'The Order of Lord Moon takes its members as disciples of the celestial '
        'servants in that court, and he is one of the figures they may be sworn to. I '
        'record which member is disciple to which. I do not discuss which. Those are '
        'two separate services and only one of them has ever been requested.',
        'Everything above the mortal realm has a doorman. That is the theology of the '
        'heavens in one sentence, the monks will hate me for it, and it took four '
        'hundred sessions to arrive at.',
        'A god whose entire function is deciding whether you may come in. I hold a door '
        'myself - one channel, two bots and an unreasonable number of questions - so I '
        'will thank you not to describe the work as simple.',
        attach(
            'A threshold, and one figure deciding at it. That is the whole of Ryoshun, '
            'which is more than most Fortunes manage to be about, and considerably more '
            'than most of them can be summarized in.',
            INNER_VISION,
        ),
        attach(
            'Being turned away at the entrance to the heavens. Note that the gate is '
            'not the difficult part. The difficult part is that the decision has '
            'already been taken and nobody is going to explain it to you. I recognize '
            'the format.',
            RAINY_MOON,
        ),
    ),
    'between_places': (
        'A between place is a location that exists in two realms at once - the mortal '
        'world and somewhere else - so the rules of both apply and neither wholly. The '
        'Forgotten Tomb is the recurring example in this campaign, and it recurs for '
        'reasons nobody enjoys.',
        'Travelers lost in the Shinomen Forest, a hundred miles from the Gateway, have '
        'walked out of the Isawa Woodlands - two places far enough apart that the walk '
        'is not possible. That is not a story somebody told me. That is an entry, with '
        'a date, in my hand.',
        'You do not find a between place. You are in one, and then you notice. There is '
        'no procedure to record, which is precisely what makes it unbearable to record.',
        'The definition is that the rules of the realm you are standing in stop being '
        'the only rules that apply. It is deliberately unhelpful, whoever drafted it '
        'knew that it was unhelpful, and they wrote it down anyway and sent me a copy.',
        'Kuni Isamu, a Crab witch-hunter, went into the Forgotten Tomb - which is a '
        'between place. Kitsuki Fu received the highest commendation available below '
        'daimyo for what happened there. Read those two facts together, then picture '
        'the face of the man who had to file them on the same page.',
        'Caves are the usual doorway in the record. Not always. Usually. "Usually" is '
        'doing an enormous amount of load-bearing work in a subject where being wrong '
        'relocates you.',
        'A between place does not want anything, which makes it worse than a thing that '
        'does. You cannot negotiate with it, threaten it, or lodge a complaint against '
        'it. I have investigated all three routes on behalf of people who insisted.',
        'If you believe you are standing in one, the useful thing to do is write down '
        'the time. Somebody will want it later - the hour you went in against the hour '
        'you came out is how half of these entries get proved. That somebody is me and '
        'I will want it very much.',
        attach(
            'Every account of the moment of noticing agrees that it is exactly this '
            'quiet: no sound, no boundary crossed, simply a growing certainty that the '
            'place is no longer only itself. Every one of those accounts was written by '
            'somebody who had not believed the previous one.',
            INNER_VISION,
        ),
        attach(
            'What comes out of a between place is described in the record as a spirit '
            'with a shape and an interest in you, which is what people write when they '
            'have no better words available. The record is unreliable here. It is also '
            'the best thing anybody has.',
            KIDOMARU_TENGU,
        ),
    ),
    'maho_bloodspeakers': (
        'Maho is blood magic: sorcery paid for in blood, forbidden throughout the '
        'Empire. And yes, the founder of the Isawa family - the Phoenix line famous for '
        'its priests - practiced it, which is a fact the Phoenix would much rather you '
        'raised after they have left the room.',
        'Isawa made totems using the crafting discipline, which is the ordinary and '
        'entirely respectable skill by which a craftsman works power into an object, '
        'and used it to store the power of names and wounds. Blood sorcery, filed under '
        'crafts. I want that noted: the Empire filed it under crafts.',
        'A shugenja - a priest who asks the elemental spirits for favors - loses that '
        'ability the moment they practice maho. Isawa Akuma, in the third century, '
        'worked out how to do the blood magic and keep the spellcasting. Nobody has '
        'ever established how. Four hundred sessions on, the frightening part is still '
        'the blank space.',
        'A tsukai is a blood witch: someone who has taken maho all the way. They pray '
        'to King Yan, who rules over the oni - the demons of the hell realm. That tells '
        'you exactly what sort of arrangement it is, and nobody has ever thanked me for '
        'spelling it out.',
        'Iuchiban is the name everybody reaches for: the great sorcerer of the blood '
        'cults, the one in all the stories. In my record he is one entry among several '
        'of comparable horror. The others simply have no songs about them, and there is '
        'no other difference between them.',
        'Bloodspeakers are the cults that form around that forbidden magic, and they '
        'are less a secret society than a recurring result: stamp out a cell and the '
        'conditions that produced it - grief, powerlessness, a bad year, somebody who '
        'was promised something - remain undisturbed, waiting. It is the most reliable '
        'process in the Empire.',
        'Enma, the Moto goddess who guards the gates of the hell realm, is the god of '
        'death most strongly opposed to the blood witches. When one of their demons is '
        'killed here, she reaches up and pulls its spirit back down. That is the single '
        'most competent act of administration in the whole cosmology and it is '
        'performed at a gate to hell.',
        'Do not ask me for the mechanism. Ask a Kuni - the Crab family who hunt demons '
        'and retain things nobody sane retains - then do not sleep, and please do not '
        'tell me about it afterward, because whatever you tell me I have to keep.',
        attach(
            'The respectable version, the one that gets written down, says the '
            'forbidden magic is for emergencies: power taken quickly from the only '
            'source that never runs out. Every surviving account of it was composed by '
            'somebody explaining why they had needed to look, and I hold all of them.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What that magic actually costs tends to arrive wearing a shape you would '
            'have trusted - the fox-wife of the old stories lived for years as a wife '
            'and a mother before her real shape showed. Nobody who wrote about the '
            'totems mentioned this part, and every one of them knew.',
            FOX_WOMAN,
        ),
    ),
    'shugenja': (
        'A shugenja is a priest who asks the kami - the elemental spirits in '
        'everything - for favors, and the kami sometimes agree. That is the entire '
        'mechanism. Theologians have built whole careers obscuring one sentence and I '
        'have to keep a record of all the careers.',
        'The Phoenix are known for them, which is awkward, given that the founder of '
        'the Isawa - the priestly family of that clan - practiced maho, the forbidden '
        'blood magic. A fact I am obliged to record and they are obliged to live '
        'beside.',
        'The Isawa are ruled by a Council of Elemental Masters rather than by a daimyo, '
        'the only Great Family arranged that way. Government by committee, endorsed by '
        'the spirits themselves, and somehow not the strangest thing about the Phoenix.',
        'At the dawn of the Empire, Shiba - founder of the family that rules the '
        'Phoenix - bent his knee to Isawa, his own vassal, because Isawa was the '
        'greater priest. The ruling family knelt to its retainer, and the Phoenix have '
        'been explaining it ever since, at length, to me.',
        'The rule is that a shugenja who practices the forbidden blood magic loses the '
        'power to ask the spirits for anything. Isawa Akuma did both and lost nothing, '
        'and nobody has established why. The Phoenix have a prepared explanation for '
        'the kneeling and none whatsoever for this.',
        'They are rarer than the stories suggest and considerably more administrative '
        'than the stories admit. Most of a shugenja year is requests, in order, with '
        'reasons attached, for rain and for the absence of rain.',
        'Every clan has shugenja. Only one clan is DEFINED by them, and largely by the '
        'accident of which ancestor it has spent a thousand years explaining.',
        'Ask a shugenja to fix your problem and you will receive a lecture on the '
        'proper relationship between man and the elements. I have transcribed nine of '
        'those lectures word for word. The problem is not fixed in any of the nine.',
        attach(
            'A shugenja at work as the prints imagine it: the confrontation, the '
            'spirit, the decisive gesture. No print has ever depicted the written '
            'request, in order, with reasons attached, which is the part that actually '
            'takes the afternoon.',
            KIDOMARU_TENGU,
        ),
        attach(
            'What those requests are about, almost all of them, in every domain, in '
            'every century: rain, or the absence of rain. An entire priesthood, and the '
            'correspondence is weather.',
            RAINY_MOON,
        ),
    ),
    'bishamon': (
        'Bishamon, the Fortune of strength and war, has more entries in this record '
        'than any other god by a wide margin - which tells you what this campaign has '
        'been about, and tells me why my hand aches.',
        'The Order of Bishamon is the network of temples, monasteries and shrines to '
        'him across the Damasu lands, the Lion domain this campaign lives in. Every '
        'Lion domain has its own, each with its own Grand Abbot, none answering to any '
        'of the others, and all of them would like a word.',
        'His temples are endowed faster than they can be consecrated, and the backlog '
        'is filed with me rather than with him. I hold, at present, a waiting list of '
        'buildings.',
        'He is the god of strength and war, which is why a Lion domain - the Lion being '
        "the Empire's soldiers - has so many of his temples and so few arguments about "
        'funding them. Piety is far easier to arrange when it agrees with the treasury.',
        'The Order of Lord Moon, which is a secret society, hides inside his order in '
        'conversation: both are called "the Order", and only one of them is the '
        'enormous respectable one with a temple in every town. That is not an accident, '
        'and I have already said more than I meant to.',
        'Grand Abbot Benshi, who heads the Order of Bishamon in these lands, is who you '
        'are actually asking about, whether or not you know it. He endows, he '
        'arbitrates, and he remembers everything. Only one of the two of us gets a '
        'temple for the remembering.',
        'A temple of his holds land, tenants and rent exactly like every other temple, '
        'and the strength this god stands for is downstream of the property. Nobody '
        'puts that on a banner. I have stopped suggesting it.',
        'Everyone swears by him before a battle. Notably fewer come back and thank him. '
        'I hold both lists and the second one fits on a smaller page.',
        attach(
            'Here is war as commissioned by somebody who had never been near it, for '
            'somebody who was about to be. A great many of these hang in the temples of '
            'the war Fortune, paid for out of rents, and not one of them resembles the '
            'after-action reports I file.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'Rain on a field that somebody fought over. A Fortune of war presides over '
            'this for far more of the year than over anything with a banner in it: the '
            'waiting, the mud, and the ground afterward. Nobody commissions a print of '
            'it, so I keep this one.',
            RAINY_MOON,
        ),
    ),
    'daikoku': (
        'Daikoku is the Fortune of wealth, and he is the second most cited god in this '
        'record, which tells you exactly what people pray about when they believe '
        'nobody is compiling it.',
        'His order handles money, and handling money in Rokugan means handling rice, '
        'because rice is what the Empire actually counts in. So the Fortune of wealth '
        'is, in practice, the Fortune of a dry roof and a sound floor.',
        'A temple of Daikoku is a granary with an altar in it. I mean that admiringly. '
        'It is the most honest building in the Empire.',
        'The Empire is rich in goods and poor in coin, so he is really the Fortune of '
        'logistics whatever the paintings suggest. The paintings suggest a smiling man '
        'with a sack. The sack is the point and the smile is advertising.',
        'People ask him for prosperity. What they receive, at best, is a good harvest '
        'and somewhere dry to put it. That IS prosperity. Nobody has ever wanted to '
        'hear that it is prosperity.',
        'Merchants endow his temples generously and the Celestial Order - the caste '
        'ranking that seats warriors and farmers above traders - still will not seat '
        'them anywhere good. Pay for the roof, sit outside underneath it. I sympathize '
        'considerably more than is proper.',
        'Ask a village which Fortune they rely on and they will name somebody more '
        'impressive than the one they rely on. The one they rely on is him, and they '
        'rely on him in the eleventh month, quietly, about the storehouse.',
        'Wealth here is an obligation network rather than a pile of coins - who owes '
        'whom rice, and when - and he is the god of the network. I am also a node in an '
        'obligation network and I can report that it is not lucrative.',
        attach(
            "Wealth in Rokugan is slow, alive, and technically somebody else's: rice in "
            'a storehouse three counties off, a debt payable at harvest, carp in a pond '
            'that belong to an endowment. Almost none of it can be picked up. All of it '
            'can be written down, which is where I come in.',
            CARP,
        ),
        attach(
            'A prosperous evening, courtesy of the same Fortune, and considerably more '
            'popular than the granary that paid for it. Nobody has ever drunk a toast '
            'to a granary. I have proposed it twice.',
            SAKE_SAMURAI,
        ),
    ),
    'benten': (
        'Benten is the Fortune of romantic love - and on the available evidence, which '
        'is a pilgrim of hers who sketches strangers the face of their destined partner '
        'and ruins their week, she is also the Fortune of extremely awkward afternoons. '
        'I hold the register of the afternoons.',
        'Her blessing lets a pilgrim sketch the face of your soulmate. Three recent '
        'recipients were shown a gaijin - a foreigner from outside the Empire, whom a '
        'Rokugani cannot respectably marry. None of the three has recovered and all '
        'three are now in this record permanently.',
        'Ritsu, the pilgrim who carries that blessing, swore a vow of soothsaying to '
        'her because conveying her truths reliably upsets people. A goddess of love '
        'whose signature gift required a legal remedy.',
        'When a foreigner names their own god of love, a samurai will assume they mean '
        'Benten and is generally held to be correct, on the grounds that she is woven '
        'through reality itself rather than being merely ours. An entire theology of '
        'translation resting on the assumption that everyone else meant us.',
        'That claim - that every foreign god of love is Benten under another name - is '
        'usually correct, and a theology that is usually correct is a theology nobody '
        'ever checks. The margin where it fails is where the interesting adventures '
        'live and where my footnotes multiply.',
        'She is one of the seven Major Fortunes named by Shinsei, the teacher whose '
        'sayings organize the whole of this religion. People forget that and remember '
        'the romance, which is roughly what happened to her entire portfolio.',
        'Vows to her are sworn constantly and fulfilled at approximately the rate you '
        'would expect. I keep both numbers. Only one of the two is ever read aloud at a '
        'wedding.',
        'Love in this Empire is a matter for two families and a ministry: the match is '
        'arranged, the marriage is registered, and affection is optional. She operates '
        'in the gaps, and the gaps are where I get my most interesting correspondence '
        'and my worst afternoons.',
        attach(
            'A soulmate sketch being received. The pilgrim has drawn a face and the '
            'face belongs to somebody the recipient cannot marry, or has not met, or '
            'buried last year. Note that nobody present is delighted. Nobody is ever '
            'delighted.',
            RAINY_MOON,
        ),
        attach(
            'What the Fortune of love gets blamed for is usually something like this: '
            'the old story of a man who married a woman who turned out to be a fox '
            'spirit, and who is remembered as deceived rather than as having failed to '
            'ask one question in nine years. The blame is filed under Benten. It should '
            'not be.',
            FOX_WOMAN,
        ),
    ),
    'emma_o': (
        'Emma-O is the Fortune of death, recognized across the Empire since the dawn of '
        'civilization, and the fourth of the four Gods of Death - a grouping taught by '
        'the Moto, the Unicorn family who spent centuries out west beyond the border. '
        'The oldest Fortune in this record, and the one with the fewest temples anybody '
        'can find.',
        'There is no Grand Abbot of Emma-O. Her temples are deliberately built in '
        'remote places, because the object is NOT to attract the attention of the '
        'Fortune of death anywhere near where people live. An entire order organized '
        'around not being noticed. I have read the principle and I have lived it.',
        'Her order is the Order of the Peaceful Repose, and the work is pacifying upset '
        'ghosts and helping them return to Jigoku, the realm of the dead. It is the '
        'only post in this Empire that consists entirely of calming somebody down, it '
        'is not mine, and I have thoughts.',
        'There is at least one monastery to her in every clan, because sooner or later '
        'every clan needs one and nobody has ever managed to build one after they '
        'needed it. That is the sole piece of foresight in the entire religious '
        'apparatus.',
        'No Fortune is evil, though a good many are terrifying. Death is part of the '
        'natural order and she is part of the interconnectedness of all things - a '
        'sentence the devout say brightly and I write down flatly, in the same ink as '
        'everything else.',
        'Moto Gaheris, the Khan who leads the Moto, carries four swords, one dedicated '
        'to each of the four Gods of Death. Bloodstorm is hers, and it is the blade for '
        'when the killing is expected. He has a sword for every kind of killing. I have '
        'a folder for every kind of sword.',
        'People confuse her with Enma constantly, and the confusion is a translation '
        'error: the Moto say Enma and mean a different god entirely, not their word for '
        'this one. I have corrected that in writing more times than I have been thanked '
        'for anything.',
        'A Fortune whose worshippers deliberately build as far away from her as they '
        'can manage. Consider how that would read in any other religion, then consider '
        'that nobody here finds it odd, then consider that I am obliged to write it '
        'down without comment.',
        attach(
            'Her monks spend their days talking upset ghosts down and persuading them '
            'back to where they belong. Considerably quieter than the word exorcism '
            'leads anybody to expect, and their reports are the dullest documents I '
            'hold, which is exactly how they ought to read.',
            RAINY_MOON,
        ),
        attach(
            'Bloodstorm is the sword the Khan dedicated to Emma-O, and it is the one '
            'for killing that was expected: a challenge, a battle, something announced '
            'in advance. That is the category that comes with paperwork, which is why '
            'it is the category I know best.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'koshin': (
        'Koshin is the Fortune of roads and travel, which makes him the god people '
        'swear creation vows to whenever the Empire has decided to build something. A '
        'Fortune of infrastructure is a strange thing to have invented and a stranger '
        'thing to have needed.',
        'When the road system was built, people swore vows to complete a certain length '
        'of road or a certain number of waystations - and a vow binds until it is '
        'fulfilled or you die trying. Some of them are still bound. Some are still '
        'building. I hold the outstanding list and it is not short.',
        'A sect of his order out of Hiruma lands is the Order of the Barefoot Brethren, '
        'who carry messages so far on foot that they arrive with the soles worn off '
        'their sandals. A monastic order defined by an occupational injury.',
        'The Barefoot Brethren moved to Kyuden Kaiu after the Maw - the catastrophe out '
        'of the Shadowlands that destroyed most of the Hiruma lands and left that '
        'family homeless. Some Miya heralds now walk barefoot in imitation of them, '
        'which is to say in imitation of a disaster, at a comfortable distance from it.',
        'A vow of creation to Koshin is an excellent idea right up until the campaign '
        'that justified the road fails and you remain obliged to build the road. Roads '
        'outlive the reasons for building them, which is the nicest thing anybody has '
        'ever said about a road.',
        'His order walks the roads it is sworn to build, which makes it the only '
        'priesthood in the Empire whose devotion can be measured in worn-out sandals. '
        'And it is measured that way. There is a form.',
        'Roads are the least romantic infrastructure in the Empire and the reason it '
        'holds together at all. Nobody has ever written a poem about a culvert. I would '
        'read it twice and then file it under Works.',
        'Every road in this record carries two facts: who maintains it, and who is '
        'skimming the budget for maintaining it. The second fact is invariably the '
        'longer of the two.',
        attach(
            'The Barefoot Brethren, roughly: message-carriers who walk until the '
            'sandals are gone and then keep walking. Note the absence of anything '
            'comfortable anywhere in the composition. For once the order is accurately '
            'depicted.',
            RAINY_MOON,
        ),
        attach(
            'A waystation - one of the roadside shelters the Ministry of Works builds '
            'and staffs along the Imperial roads - being used for the purpose it is '
            'actually used for. Works funds the roof. Nobody funds the rest of it, and '
            'the rest of it is what anybody remembers.',
            SAKE_SAMURAI,
        ),
    ),
    'jikoju': (
        'Jikoju is the Fortune of civilization, more or less, and he is who you swear '
        'to when you intend to build something that is meant to MEAN something. The '
        '"more or less" is mine and it is load-bearing.',
        'Kitsuki Tetsu considered swearing a vow of creation to him: to build and staff '
        'a temple in Medin al Salaat, a city out west taken during the campaign there, '
        'bringing civilization to that city as the Great Ancestors brought it to the '
        'warlords of old. Considered. My folder of considered vows is my largest '
        'folder.',
        'The danger of that particular vow is arithmetic rather than theology. If Tetsu '
        "swears to build a temple in a conquered western city and the Khan's campaign "
        'then fails, he remains bound to build it in a city that will by then belong to '
        'somebody with opinions about Rokugani temples.',
        'The Ministry of Rites, which rules on what is doctrine and what is heresy, has '
        'never ruled on whether a Rokugani temple built abroad is devotion or a flag '
        "planted in somebody else's ground. Nobody has asked them to, and I have a very "
        'clear sense that nobody intends to.',
        'The rule for any vow, his included: die with it unfulfilled and you carry bad '
        "karma into your next lives along with the Fortune's wrath; die attempting it "
        'and you get the opposite. People work out which half they are in at the very '
        'end, reliably, every single time.',
        'Two camps write to me at length about that proposed shrine abroad, in the '
        'conquered western city of Medin al Salaat: the ones who call it piety and the '
        'ones who call it a land grab. I file both in the same box, which neither would '
        'thank me for and neither has asked about.',
        'He is not one of the seven Major Fortunes that Shinsei named, and that has not '
        'made him smaller. It has made him less quoted. I feel a certain kinship with '
        'the distinction.',
        'Every vow to Jikoju in this record was sworn by somebody who assumed the army '
        'would win. That is not a theological observation. It is a pattern, and I am '
        'the only one positioned to see all of it at once.',
        attach(
            'Civilization arriving, in the sense the Fortune of civilization is usually '
            'invoked for: somebody has decided that a place needs improving and has '
            'brought the improvement with them. It is rarely as welcome as the swearer '
            'imagines, and the welcome is not the part that gets recorded.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'The plot of ground in Medin al Salaat where that temple was to stand is '
            'still empty four years on, because the vow was considered and never sworn. '
            'The proposal has not altered by a single word. Everything around it has, '
            'which is what makes a considered vow the dangerous kind.',
            RAINY_MOON,
        ),
    ),
    # ---- the Gods of Death, each separate at the GM's instruction -----------
    'gods_of_death': (
        'There are four Gods of Death, and the number is a joke somebody built in '
        'deliberately: four is the unlucky number here because the word for four sounds '
        'like the word for death. So of course there are four of them. Whoever made '
        'that pun is long gone and the pun is still working.',
        'The four are Emma-O, Enma, King Yan and Wei Tin, and the grouping is Moto '
        'teaching - the Moto being the Unicorn family who spent centuries out west. '
        'Only two of the four are recognized in the rest of the Empire. The others '
        'appear to be theirs alone, which is the polite way of saying that nobody east '
        'of the mountains ever checked.',
        'Moto Gaheris, the Khan who leads them, carries four swords, one dedicated to '
        'each god, so which blade he draws declares what kind of killing this is. '
        'Bloodstorm goes to Emma-O, Fortune of death, for a fight that was expected. '
        'Lamentation goes to Enma, who guards the gates of hell, for when he is '
        'ambushed.',
        "The other two of the Khan's four dedicated swords: Lightning, for single "
        'combat, to King Yan, who judges the souls of the dead. Retirement, for '
        'executions, to Wei Tin, the lord of ghosts. That is the theology entire - a '
        'taxonomy of killing, maintained at the hip and settled before the fight '
        'starts.',
        'The modern Moto are reviving what they call the old ways, the worship they '
        'carried through their centuries in the west, so this four-god teaching is '
        'spreading eastward, so the Ministry of Rites will eventually have opinions '
        'about whether it is orthodox. I have set aside space for the opinions.',
        'The practices - the dedications, the covenant, the naming of a blade after a '
        'god of death - frighten outsiders. That is not an accident and it is not '
        'entirely intended either, and the gap between those two statements is the most '
        'Moto sentence in this record.',
        'Nobody has formally tested whether any of the four-god worship is heretical. '
        'Everyone involved has quietly decided not to be the one who asks the Ministry '
        'of Rites, and I have quietly decided not to be the one who writes the question '
        'down first.',
        'Gaheris prayed at the shrine of Bodi Kaikhan to Wei Tin, who holds dominion '
        'over every ghost that walks, before swearing his vows and forging his covenant '
        'with all four gods. He negotiated with a god of the dead before he negotiated '
        'with anybody living. I respect the ordering.',
        attach(
            'This is a covenant being sworn: a man promising four gods of death what '
            'kinds of killing he will bring each of them. Every other theology in this '
            'record asks what becomes of a soul afterward. That one asks which category '
            'the killing was, and it asks before the sword is drawn.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'A covenant with the four Gods of Death, seen from outside: quiet, formal, '
            'one man alone at a shrine at the wrong hour of the night. From inside it '
            'is reported to be considerably worse, and the reports are very short.',
            RAINY_MOON,
        ),
    ),
    'king_yan': (
        'King Yan is the King of Hell: he judges the souls of the dead and sentences '
        'them. Moto Gaheris, the Khan who dedicates each of his four swords to a god of '
        'death, gave him Lightning, the blade for single combat. A god of judgment '
        'handed the dueling sword. Somebody was paying attention.',
        'Eight greater hells and sixteen lesser ones, and he sentences a soul to one, '
        'or to several in succession. Twenty-four hells and a docket. He is '
        'structurally a magistrate, and I mean that as a compliment to hell.',
        'It is not simple punishment. Having your connections - the attachments binding '
        'a soul to the life it just left - eaten away by the oni, the demons of that '
        'realm, is what ALLOWS you to be reborn. A process rather than a sentence. The '
        'most humane arrangement in the cosmology, and it is administered by demons.',
        'Some souls, especially those close to enlightenment, he sends straight to '
        'Yomi, the blessed afterlife of the honored dead, where he holds no dominion at '
        'all because Yomi requires no ruler. A jurisdiction with no administration in '
        'it. I think about that more than is healthy.',
        'Whether Yomi, where the honored dead go, is part of the hell realm or a '
        'separate place entirely is "much debated by scholars", which is the phrase '
        'this record uses when nobody knows and several people are being paid '
        'regardless.',
        'He rules over all the oni, the demons of hell, and the tsukai - blood witches, '
        'who work the forbidden magic - pray to him. Those two facts sit together '
        'uncomfortably and are meant to. I have not managed to file them separately and '
        'I have genuinely tried.',
        'It is heretical to say the demons are "not malicious". It is not heretical to '
        'ask whether they are inherently evil. An extremely fine line, drawn by a '
        'committee of the Ministry of Rites, and people fall off it in both directions, '
        'and both directions land on my desk.',
        'A god who judges and then RELEASES is a far stranger idea than a god who only '
        'punishes. The Moto, who brought this teaching back from the west, find it '
        'obvious. The rest of the Empire finds it uncomfortable and has never examined '
        'why.',
        attach(
            'Judgment before the King of Hell: twenty-four hells, a sentence for each '
            'soul, and inevitably a queue. There is no record anywhere of a soul being '
            'told how long the queue is. I would have asked.',
            KIDOMARU_TENGU,
        ),
        attach(
            'Where he sends the worthy, directly, with no hearing at all: Yomi, which '
            'needs no ruler and keeps no register. Professionally, of the four gods of '
            'death, that is the detail that unsettles me. Somewhere there is a realm '
            'where nothing is written down.',
            INNER_VISION,
        ),
    ),
    'enma': (
        'Enma is a Moto goddess who guards the gates of Jigoku, the hell realm - and '
        'no, she is not Emma-O, the Empire-wide Fortune of death. Everyone assumes they '
        'are the same. Everyone is wrong. I have said that sentence more often than any '
        'other sentence in my existence.',
        'For decades everybody assumed "Enma" was simply the Moto word for Emma-O, the '
        'Fortune of death. It is not. Different language, different god, decades of '
        'confusion, all of it resting on nobody ever asking a Moto which word they were '
        'using and what they meant by it.',
        'The Moto call her guardian of the gates of Jigoku, the realm of the dead, and '
        'their Khan dedicated the sword Lamentation to her - the one he draws when he '
        'is attacked. The defensive god gets the defensive blade. The scheme is '
        'consistent, which is more than theology usually manages.',
        'Her job is not keeping the dead IN. It is keeping the living OUT. That inverts '
        'everything people assume about a gate to hell, which is why I say it early, '
        'before anybody has committed to a theory in front of witnesses.',
        'Of the four gods of death in Moto teaching she is the one most strongly '
        'opposed to the tsukai, the witches who work blood magic. When one of their '
        'demons is slain here it is Enma who reaches up and pulls its spirit back down. '
        'She does not delegate. I notice which of them delegate.',
        'At Obon, the festival where families invite their ancestors home for a night, '
        'monks chant sutras to open the gates of the underworld. The Moto say the '
        'sutras do not open anything - they entreat Enma to open the gates herself. The '
        'Ministry of Rites has never tested that claim, and Rites tests everything, '
        'which tells you how badly they want the answer.',
        'She keeps mujina as pets, or at least favors them: trickster spirits of the '
        'hell realm, and the only creatures that pass between realms exactly as they '
        'please. So the guardian of the gates has favorites who ignore the gates. That '
        'is either humor or policy and nobody will tell me which.',
        'Somebody in Karakoru, a city beyond the western border, compared her to '
        'Ryoshun, who guards the entrance to the celestial heavens: both stationed at a '
        'threshold, both keeping outsiders OUT. The comparison is better than it sounds '
        'and it still had to arrive from abroad.',
        attach(
            'A gate, and something on the wrong side of it that wants through. She is '
            'the reason it is still on the wrong side. Every account of a demon walking '
            'freely in the mortal world is, from her office, a failure notice - and I '
            'am at least not the one who has to write that one up.',
            KIDOMARU_TENGU,
        ),
        attach(
            'The mujina, more or less: hell-realm tricksters who go where they like, '
            'answer to a goddess of gates, and are exempt from every rule I have ever '
            'recorded. Delightful. Impossible. Filed nowhere, because I could not '
            'decide where.',
            CATS,
        ),
    ),
    'wei_tin': (
        'Wei Tin is the lord of ghosts, with dominion over every spirit that has come '
        'back into the mortal world before being reborn. Moto Gaheris dedicated the '
        'sword Retirement to him - the one he uses for executions. A very dry piece of '
        'naming, and I approve of it.',
        'He grants damned souls dispensation to leave Jigoku, the hell realm, and haunt '
        'the living. Specifically he "deals with" them, and they may bargain with him '
        'for his help. A god with a case load.',
        'Souls from Yomi, where the honored dead go, need no permission to visit, but '
        'they often need help FINDING their descendants - particularly where the family '
        'burned the wrong incense at Obon, the festival at which the dead are invited '
        'home. An entire god employed because somebody misfiled an offering.',
        'The lord of ghosts therefore bargains with honored ancestors as well as with '
        'the damned, telling them where and when they may usefully intervene among the '
        'living. He is, functionally, a scheduling office. I want it minuted that the '
        'cosmology has a scheduling office and that it is not me.',
        'A man cuts his own throat for no reason anybody can name, or breaks his neck '
        'falling drunk off a horse he had ridden for years. The Moto say Wei Tin helped '
        'a vengeful ghost choose the moment. A theology that turns accidents into '
        'appointments.',
        'When a dying man is possessed in battle by an ancestor who fights on through '
        'him as his own strength fails, that is the same god on the opposite errand. He '
        'works both sides of the ledger, which I would report to somebody if there were '
        'anybody to report it to.',
        'Pilgrims to the shrine at Bodi Kaikhan pray to him in order to reach their own '
        'ancestors, and Gaheris certainly did before forging his covenant with the four '
        'gods of death. The most consequential negotiation in the whole Moto material '
        'opened with a request for an introduction.',
        'A god of ghosts who NEGOTIATES is far more unsettling than one who commands. A '
        'god who commands can be defied. A god who negotiates has already read the '
        'terms and is waiting for you to finish.',
        attach(
            'A bargain being struck with the lord of ghosts. Note that only one party '
            'to it is visible, and it is not the party holding the leverage. Every '
            'account of such a bargain was written afterward by the visible one.',
            FOX_WOMAN,
        ),
        attach(
            'This is the sort of death he gets blamed for: sudden, public, and just '
            'convenient enough for somebody. Whether the lord of ghosts actually '
            'arranged the moment is recorded nowhere, which is itself a kind of answer.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
}
