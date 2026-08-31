"""Religion, cosmology, and the four Gods of Death. GM Assistant only.

Annoyance first, then a fact from `l7r.md` (FR-002). The four Gods of Death each
have their own category at the GM's explicit instruction (FR-005); Emma-O is
here rather than with the other three because she is a Fortune recognized
Empire-wide, not a Moto-only god - she is still the fourth.
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
        'interchangeably and then are surprised by the consequences.',
        'The format is fixed: name yourself unambiguously first, so the fortune does '
        'not bind the wrong person. Sometimes that means naming your parents.',
        'Then name who you swear by. Then the formula. Three parts, every time, and '
        'the middle one is where people get creative and regret it.',
        'A legionnaire swears "by Lady Sun, and by my ancestors" - and may add their '
        'family patrons. The formula ends "that in so doing I shall never seek to '
        'avoid death."',
        'Higher rank, longer oath. Lieutenants marshal troops. Captains show utmost '
        'respect for duty. Generals borrow clauses from all six ministries.',
        'Dying with a vow unfulfilled brings bad karma into your next lives and the '
        'wrath of the fortune. Dying ATTEMPTING to fulfill it brings the opposite.',
        'That asymmetry is the whole reason vows are dangerous and the whole reason '
        'people swear them anyway.',
        'A vow of creation obliges you to build the thing whether or not the war that '
        'made it sensible is still being won.',
        attach(
            'This is a man in the third part of an oath, discovering what he has just agreed to.',
            INNER_VISION,
        ),
        attach(
            'And this is how an unfulfilled vow usually resolves.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'bentens_blessing': (
        "Benten's Blessing. Yes. It is real and it is inconvenient to everyone it touches.",
        'Ritsu the pilgrim was blessed with the ability to look at a person and sketch '
        'their soulmate. He then swore the vow of soothsaying to Benten, because '
        'people take the news badly.',
        'Three people in recent years received sketches of GAIJIN soulmates. Good news '
        "for Gaheris' campaign. Very bad news for those three.",
        'Toranosuke, abbot of Chai Sedo, declared it portends success. Abbots declare '
        'things portend success when armies are already moving.',
        'By vowing to always convey truth to all who seek it, Ritsu receives divine '
        'truth in return. That is how the blessing sustains itself.',
        'A blessing that obliges you to tell people things they do not want to hear is '
        'not a reward, it is a posting.',
        'Benten is the fortune of romantic love. She is also, in my experience, the '
        'fortune of extremely awkward afternoons.',
        'People ask for the blessing. Nobody asks what the blessing costs.',
        attach(
            'Somebody receiving the news about their soulmate. Note the composure.',
            RAINY_MOON,
        ),
        attach(
            'And this is the same person that evening.',
            SAKE_SAMURAI,
        ),
    ),
    'temple_organization': (
        'A country monk in every village district, a preceptor in every county town, a '
        'provincial abbot in every provincial city, at least two grand abbots in every '
        'capital. There. That is the structure.',
        'An ORDER is the network. A TEMPLE is a building. The Order of Bishamon is all '
        'the temples, monasteries and shrines to Bishamon in Damasu lands.',
        'Every domain in Lion lands has its own Order of Bishamon with its own Grand '
        'Abbot. They are not subordinate to each other and they are very clear about '
        'it.',
        'For a large network the capital temple is the sovereign temple and the '
        'provincial ones are subordinate. Within a domain. Only within a domain.',
        'The Shinsei identified seven Major Fortunes whose favor brings luck and '
        'prosperity. Everyone can name three.',
        'The country monk holds tax-free land and may have acolytes farming it '
        'part-time, on loan from the larger families in the village.',
        'Temples are administered by the Ministry of Rites, which means they are '
        'administered, which is not what people imagine when they imagine temples.',
        'Ask a grand abbot about doctrine and he will give you theology. Ask him about '
        'the harvest and he will give you the truth.',
        attach(
            'Temple life. Considerably more sweeping than the prints suggest.',
            CATS,
        ),
        attach(
            'And this is a doctrinal disagreement between two orders.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'temple_finances': (
        'Temple finances. Nobody asks about this and it is the most revealing thing in '
        'the entire religious apparatus.',
        'A temple holds land, and land means tenants, and tenants mean rent, and rent '
        'means a temple is a landlord with better robes.',
        'The Temple of Bishamon has a history and it is largely a history of property.',
        'Tax-free land is the gift that matters. Everything else a daimyo gives a '
        'temple is decoration.',
        'Monks live inside the precinct. Initiates - about twice their number - mostly '
        'live out. That is a housing arrangement, not a spiritual one.',
        'When a temple is wealthy, ask who endowed it and what they wanted written '
        'down about themselves.',
        'The lay neighborhoods around a large temple are where the actual economy is.',
        'I have never met an abbot who was bad at arithmetic. Not once.',
        attach(
            'The endowment, in its usual form. Slow, cold, and older than the building.',
            CARP,
        ),
        attach(
            'And this is a dispute over temple land.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'food_purity': (
        'Food purity. Fine. It matters more than visitors expect and less than the devout claim.',
        'Death pollution is the organizing principle. What has touched death does not '
        'come inside, and that includes a great deal of dinner.',
        'The rules vary by order, by region, and by how closely anybody is watching.',
        'A monastery keeps purity rules a village district could not afford to keep.',
        'Purity is largely a question of who can pay for it. This is true of most '
        'religious observance and nobody enjoys hearing it.',
        'Ask a monk what he may eat and he will tell you. Ask him what he DOES eat on '
        'the road and he will change the subject.',
        'The burakumin handle what nobody else may touch, and eat what nobody else will.',
        'I record what people claimed to observe. That is a different document from '
        'what they observed.',
        attach(
            'Purity, as observed by those with the leisure for it.',
            INNER_VISION,
        ),
        attach(
            'And this is purity on the third night of a journey.',
            SAKE_SAMURAI,
        ),
    ),
    'soothsaying': (
        'Soothsaying. Yes, it works. That is the part people are not ready for.',
        'It does not tell you what will happen. It tells you what is ALIGNED, which is '
        'a different and much less useful thing.',
        'The sexagenary cycle names the day as well as the year, so there is always '
        'something significant about today. Always.',
        'A soothsayer who tells you nothing is going to happen has either failed or is being kind.',
        'Ritsu swore the vow of soothsaying to Benten because the truth he was given '
        'kept upsetting people. The vow is a shield, not a gift.',
        'Omens are read after the fact more often than before it, and the record is '
        'quite clear about which.',
        'Kitsu Okura has six doctrines about attunement and I have had all six '
        'explained to me twice.',
        'Ask a soothsayer a question and you will get an answer. That is the problem.',
        attach(
            'A reading in progress. It will take longer than you have.',
            INNER_VISION,
        ),
        attach(
            'And this is the omen everybody claims to have seen afterward.',
            GREAT_WAVE,
        ),
    ),
    'omens_and_portents': (
        'Omens. Everyone wants a list. The list is the least interesting part.',
        'An omen is only an omen once somebody in authority agrees it was one. Before '
        'that it is weather.',
        'A comet before a battle is a portent. A comet before a good harvest is a '
        'comet. Same comet.',
        'Toranosuke declared gaijin soulmates portended success for a military '
        'campaign. Abbots declare things portend success when armies are already '
        'moving.',
        'The Ministry of Rites decides which readings are doctrine and which are '
        'heresy, so a portent is also a political act.',
        'I have four hundred sessions of omens and about six of them were noticed '
        'before the event.',
        'The useful question is never "was that an omen". It is "who benefits from it '
        'having been one".',
        'Something strange happened and you want it to mean something. That is not '
        'theology, that is Tuesday.',
        attach(
            'The single most-cited omen in the record. It means whatever the person '
            'citing it needs.',
            GREAT_WAVE,
        ),
        attach(
            'And this is the one people actually saw and did not report.',
            KIDOMARU_TENGU,
        ),
    ),
    'lord_moons_court': (
        "Lord Moon's heavenly court. Careful. That is a secret society question and I "
        'notice you asked it in an open channel.',
        "Members of the Order become disciples of one or more of Lord Moon's celestial "
        'servants. Three levels: Crescent, Half, and the third.',
        'You may mix and match - take the Crescent abilities of three different '
        'servants, or go deeper with one. Most people go wide and regret it.',
        'Ryoshun guards the entrance to the celestial heavens. Somebody in Karakoru '
        'compared him to Enma, which is closer than it sounds.',
        'The Order of Lord Moon is called "the Order" in conversation so that anyone '
        'overhearing assumes you mean the Order of Bishamon. That is deliberate.',
        'It is a secret society whose members are also, publicly, members of a '
        'completely legitimate monastic order. Convenient.',
        'The initiation vow binds you to protect the identities of your fellow members '
        'as if their lives were your own. It does not say "if convenient".',
        'I have the vow written out in full. I am not going to recite it here.',
        attach(
            'This is the correct posture for asking me about the Order. Alone, and somewhere else.',
            INNER_VISION,
        ),
        attach(
            'And this is what happens when a member is careless about the second clause.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'ryoshun': (
        'Ryoshun. He guards the entrance to the celestial heavens. That is the whole '
        'job and it is a large job.',
        "He is a member of Lord Moon's heavenly court, which means asking about him "
        'in public is a slightly louder question than you intended.',
        'Somebody in Karakoru compared him to Enma, on the grounds that both keep '
        'people OUT rather than keeping prisoners in. That comparison holds.',
        'A guardian at a threshold is a very old idea and this Empire has several. '
        'They are not interchangeable and scholars pretend otherwise.',
        'He does not judge. King Yan judges. Ryoshun simply decides who gets past, which is worse.',
        'The Order takes disciples of the court. I record which, and I do not discuss it.',
        'Everything above the mortal realm has a doorman. That is the theology in one '
        'sentence and the monks will hate me for it.',
        'Ask me something with a magistrate in it.',
        attach(
            'A threshold, and somebody deciding. That is the whole of him.',
            INNER_VISION,
        ),
        attach(
            'And this is what being turned away looks like.',
            RAINY_MOON,
        ),
    ),
    'between_places': (
        'The between places. Places coexistent between two realms. The Forgotten Tomb '
        'is the recurring example and it is recurring for bad reasons.',
        'People have been lost in the Shinomen Forest a hundred miles from the Gateway '
        'and walked out of the Isawa Woodlands. That is not a story, that is an entry.',
        'You do not find a between place. You are in one, and then you notice.',
        'The rules of the realm you are in stop being the only rules that apply. That '
        'is the definition and it is deliberately unhelpful.',
        'Kuni Isamu went into the Forgotten Tomb. Kitsuki Fu got a commendation for '
        'it. Read those two facts together.',
        'Caves are the usual doorway in the record. Not always. Usually.',
        'A between place does not want anything. That is what makes it worse than a '
        'thing that does.',
        'If you think you are in one, the useful action is to write down the time. '
        'Somebody will want it later.',
        attach(
            'This is the moment of noticing. It is always this quiet.',
            INNER_VISION,
        ),
        attach(
            'And this is the shape most of them take in the record.',
            KIDOMARU_TENGU,
        ),
    ),
    'maho_bloodspeakers': (
        'Maho. Blood magic. And yes, the founder of the Isawa Family practiced it, '
        'which the Phoenix would rather you did not raise.',
        'Isawa made totems with the crafting discipline and performed rituals to store '
        'the power of names and wounds. That is in the record.',
        'Isawa Akuma, third century, worked out how to wield maho WITHOUT losing his '
        'spellcasting ability. Nobody knows how. That is the frightening part.',
        'A tsukai is a witch. They pray to King Yan, who rules over all oni, which '
        'tells you what sort of arrangement it is.',
        'Iuchiban is the name people reach for and Iuchiban is only the most famous one.',
        'Bloodspeakers are not a secret society so much as a recurring result. Stamp '
        'them out and the conditions that made them remain.',
        'Enma is the god of death most strongly opposed to tsukai. When an oni is slain '
        'here, she reaches up and pulls its spirit back.',
        'Do not ask me for the mechanism. Ask a Kuni, and then do not sleep well.',
        attach(
            'The respectable version of what maho is for.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what it actually costs, wearing a shape you would trust.',
            FOX_WOMAN,
        ),
    ),
    'shugenja': (
        'Shugenja. They ask the kami for favors and the kami sometimes agree. That is '
        'the entire mechanism and theologians have built careers on obscuring it.',
        'The Phoenix are known for them, which is awkward, given that the founder of '
        'the Isawa practiced maho.',
        'The Isawa are ruled by the Council of Elemental Masters rather than a daimyo. '
        'The only Great Family in the Empire arranged that way.',
        'Shiba bent his knee to Isawa at the dawn of the Empire. The ruling family '
        'knelt to its own vassal and the Phoenix have been explaining it ever since.',
        'A shugenja who practices maho loses their spellcasting. Isawa Akuma did not, '
        'and nobody has established why.',
        'They are rarer than the stories suggest and more administrative than the stories admit.',
        'Every clan has them. Only one clan is defined by them, and mostly by '
        'accident of who they had to explain.',
        'Ask a shugenja to fix your problem and you will get a lecture about the '
        'relationship between man and the elements.',
        attach(
            'A shugenja at work, as the prints imagine it.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what the request usually concerns. Rain, or the absence of it.',
            RAINY_MOON,
        ),
    ),
    'bishamon': (
        'Bishamon. The one with the most entries in this record by a wide margin, '
        'which should tell you something about what this campaign has been about.',
        'The Order of Bishamon is the network of temples, monasteries and shrines in '
        'Damasu lands. Every Lion domain has its own, with its own Grand Abbot.',
        'Those Grand Abbots are not subordinate to one another, and are extremely '
        'clear about it whenever the question is raised.',
        'Fortune of strength and war. Which is why a Lion domain has so many of his '
        'temples and so few arguments about funding them.',
        'The Order of Lord Moon hides inside the Order of Bishamon in conversation. '
        'That is not an accident and I have said too much.',
        'Grand Abbot Benshi is the one you are actually asking about, whether or not you know it.',
        'A temple of Bishamon holds land, tenants and rent, like every other temple. '
        'The strength is downstream of the property.',
        'Everyone swears by him before a battle. Rather fewer thank him afterward.',
        attach(
            "Bishamon's department, accurately depicted.",
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is his other department, which nobody puts on a banner.',
            RAINY_MOON,
        ),
    ),
    'daikoku': (
        'Daikoku. Fortune of wealth. Second-most cited in this record, which tells you '
        'what people actually pray about.',
        'His order handles money, and handling money in Rokugan means handling rice, '
        'which means warehouses.',
        'A temple of Daikoku is a granary with an altar in it. I mean that admiringly.',
        'The Empire is wealth-rich and coin-poor. Daikoku is therefore the fortune of '
        'logistics, whatever the paintings suggest.',
        'People ask him for prosperity. What they receive, at best, is a good harvest '
        'and somewhere dry to keep it.',
        'Merchants endow his temples generously and the Celestial Order still will not '
        'let them sit anywhere good.',
        'Ask which fortune a village actually relies on and it is him, and they will '
        'name someone more impressive.',
        'Wealth in this Empire is an obligation network, not a pile. He is the fortune '
        'of the network.',
        attach(
            "Wealth in Rokugan. Slow, alive, and technically somebody else's.",
            CARP,
        ),
        attach(
            'And this is a prosperous evening, courtesy of the same fortune.',
            SAKE_SAMURAI,
        ),
    ),
    'benten': (
        'Benten. Romantic love. And, in my experience, extremely awkward afternoons.',
        'Her blessing lets a pilgrim sketch your soulmate. Three recent recipients got '
        'gaijin. Nobody has recovered.',
        'Ritsu swore the vow of soothsaying to her, because conveying her truths '
        'reliably upsets people.',
        'If a gaijin names their god of love, a samurai will assume it is Benten. They '
        'will probably be right - she is part of the fabric of reality and therefore '
        'everywhere.',
        '"Probably right" is doing a great deal of work in that sentence, and the room '
        'for error is where the interesting adventures live.',
        'She is one of the seven Major Fortunes the Shinsei identified. People forget '
        'that and remember the romance.',
        'Vows to her are sworn constantly and fulfilled at about the rate you would expect.',
        'Love in this Empire is a matter for two families and a ministry. She operates '
        'in the gaps.',
        attach(
            'A soulmate sketch being received. Note that nobody is delighted.',
            RAINY_MOON,
        ),
        attach(
            'And this is what she is usually blamed for.',
            FOX_WOMAN,
        ),
    ),
    'emma_o': (
        'Emma-O. Fortune of death, recognized throughout the Empire since the dawn of '
        'civilization, and the fourth of the Gods of Death whether or not the Moto '
        'phrase it that way.',
        'There is no Grand Abbot of Emma-O. Her temples are all in remote places, '
        'specifically to avoid attracting her attention near people.',
        'Think about that. An entire order sited on the principle of not being noticed.',
        'Her order is the Order of the Peaceful Repose. They pacify upset ghosts and '
        'help them return to Jigoku.',
        'There is at least one monastery to her in every clan, because sooner or later '
        'every clan needs them.',
        'No fortune is evil, though many are terrifying. Death is part of the natural '
        'order and she is part of the interconnectedness of all things.',
        'Gaheris carries Bloodstorm into battle, dedicated to her. That is the sword '
        'he uses when the killing is expected.',
        'People confuse her with Enma constantly, because the Moto say Enma and mean '
        'somebody else entirely.',
        attach(
            'The Order of the Peaceful Repose at work. It is quieter than exorcism sounds.',
            RAINY_MOON,
        ),
        attach(
            "And this is Bloodstorm's department.",
            DUEL_ON_THE_BRIDGE,
        ),
    ),
    'koshin': (
        'Koshin. Roads and travel. The fortune people swear creation vows to when the '
        'Empire is building something.',
        'When the road system was constructed, people swore to build a certain length '
        'of road or a certain number of waystations. Some of them are still bound.',
        'A sect of his order out of Hiruma lands is the Order of the Barefoot Brethren '
        '- they walk so much carrying messages that they arrive without soles.',
        'They moved to Kyuden Kaiu after the Maw destroyed most of Hiruma lands. Some '
        'Miya heralds walk barefoot in imitation.',
        'A vow of creation to Koshin is a good idea right up until the campaign that '
        'justified it fails and you are still obliged.',
        'Hantei the Tenth outlawed tolls on Imperial roads. Koshin got the credit and '
        'the Ministry of Works got the bill.',
        'Roads are the least romantic infrastructure and the reason the Empire holds together.',
        'Ask me about a road and I will tell you who maintains it and who is skimming it.',
        attach(
            'The Barefoot Brethren, roughly. Note the absence of anything comfortable.',
            RAINY_MOON,
        ),
        attach(
            'And this is what a waystation is for.',
            SAKE_SAMURAI,
        ),
    ),
    'jikoju': (
        'Jikoju. Fortune of civilization, more or less, and the one you swear to when '
        'you intend to build something that means something.',
        'Kitsuki Tetsu considered a vow of creation to him: to build and staff a temple '
        'in Medin al Salaat. Symbolizing civilization brought to the city, as the '
        'Great Ancestors brought it to the pre-Imperial warlords.',
        "The danger being that if Gaheris' campaign fails, Tetsu is still bound to "
        'build it or die trying.',
        'A vow does not care whether the war it assumed is still being won.',
        "Dying with it unfulfilled brings bad karma and the fortune's wrath. Dying "
        'attempting it brings the opposite. People forget which half they are in.',
        'Building a temple in a gaijin city is either the most pious act of a '
        'generation or a provocation. Both readings are live.',
        'He is not one of the seven the Shinsei named, which does not make him small.',
        'Ask me about a vow to Jikoju and I will ask you what happens if the army loses.',
        attach(
            'Civilization arriving. It is rarely as welcome as the swearer imagines.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is the temple, four years later, still unbuilt.',
            RAINY_MOON,
        ),
    ),
    # ---- the Gods of Death, each separate at the GM's instruction -----------
    'gods_of_death': (
        'Four Gods of Death, because four is the unlucky number - it sounds like the '
        'word. Given that, how could there be any other number?',
        'Of the four, only two are recognized in the rest of the Empire. The others '
        'appear unique to Moto teaching.',
        'Gaheris carries four swords, one dedicated to each. Bloodstorm for battle, to '
        'Emma-O. Lamentation for defense when ambushed, to Enma.',
        'Lightning for single combat, to King Yan. Retirement for executions, to Wei '
        'Tin. He chose which sword for which killing and that is the theology.',
        'The modern Moto are bringing back "the old ways", which means this worship is '
        'expanding, which means the Ministry of Rites will eventually have opinions.',
        'These practices frighten outsiders. That is not an accident and it is not '
        'entirely unintended.',
        'Nobody has formally tested whether any of it is heretical. Do not be the one who asks.',
        'Gaheris prayed to Wei Tin at Bodi Kaikhan before swearing his vows and forging '
        'his covenant with all four.',
        attach(
            'Four swords, four gods, one man deciding which killing this is.',
            DUEL_ON_THE_BRIDGE,
        ),
        attach(
            'And this is what a covenant with the Gods of Death looks like from outside.',
            RAINY_MOON,
        ),
    ),
    'king_yan': (
        'King Yan. The King of Hell. He judges the souls of the dead and sentences '
        'them, and Gaheris dedicated Lightning to him - the sword for single combat.',
        'Eight greater hells and sixteen lesser. He sentences a soul to one, or to '
        'several in succession.',
        'That is not simple punishment. Having your connections eaten by oni is what '
        'ALLOWS rebirth. It is a process, not a sentence.',
        'Some souls, especially those near enlightenment, he sends straight to Yomi. '
        'He has no dominion there - Yomi needs no ruler.',
        'Whether Yomi is part of Jigoku or a separate realm entirely is much debated '
        'by scholars, which means nobody knows.',
        'He rules over all oni. Tsukai pray to him. Those two facts sit together '
        'uncomfortably and are meant to.',
        'It is heretical to say oni are "not malicious". It is not heretical to ask '
        'whether they are inherently evil. That is a very fine line and people fall '
        'off it.',
        'A god who judges and then releases is a stranger idea than a god who only '
        'punishes. The Moto find it obvious.',
        attach(
            'Judgment. Twenty-four hells and a queue.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And this is what he is said to send the worthy directly to.',
            INNER_VISION,
        ),
    ),
    'enma': (
        'Enma. And no, she is not Emma-O. Everyone assumes that. Everyone is wrong.',
        'Enma was thought to be the Moto word for Emma-O until the campaign started. '
        'Different language, different god, decades of confusion.',
        'The Moto call her the guardian of the gates of Jigoku. Gaheris dedicated '
        'Lamentation to her - the sword for when he is attacked.',
        'Her job is not keeping the dead IN. It is keeping the living OUT. That '
        'inverts everything people assume.',
        'Of all the Gods of Death she is the most strongly opposed to tsukai. When an '
        'oni is slain here, it is Enma who reaches up and pulls its spirit back.',
        'The Moto claim the Obon sutras do not open the gates directly - they entreat '
        'Enma to open them herself. Rites has never tested that.',
        'She keeps mujina as pets, or simply favors them. They are the trickster '
        'spirits of Jigoku, and the only creatures that travel freely between realms.',
        'Somebody in Karakoru compared her to Ryoshun, who guards the entrance to the '
        'heavens. Both keep outsiders out. That comparison is better than it sounds.',
        attach(
            'A gate, and something on the wrong side of it.',
            KIDOMARU_TENGU,
        ),
        attach(
            'And these are the mujina, more or less, being delightful and impossible.',
            CATS,
        ),
    ),
    'wei_tin': (
        'Wei Tin. Lord of ghosts. Dominion over every spirit that has returned to the '
        'mortal realm before rebirth. Gaheris dedicated Retirement to him - the '
        'execution sword.',
        'He grants damned souls dispensation to leave Jigoku and haunt. Specifically '
        'he "deals with" them, and they may bargain with him for his help.',
        'Souls from Yomi do not need his permission, but they often need his help '
        'FINDING their descendants - especially if the family burned the wrong '
        'incense at Obon.',
        'So he bargains with honored ancestors too, telling them where and when they '
        'may usefully intervene.',
        'A man cuts his own throat unexpectedly, or drunkenly breaks his neck off his '
        'own horse. The Moto say Wei Tin helped a vengeful ghost pick the moment.',
        'And when a man is possessed in battle by an ancestor who fights through him '
        'as his strength fails - same god, opposite errand.',
        'Pilgrims to Bodi Kaikhan pray to him to reach their ancestors. Gaheris '
        'certainly did before forging his covenant.',
        'A god of ghosts who negotiates is far more unsettling than one who commands.',
        attach(
            'A bargain being struck. Note that only one party is visible.',
            FOX_WOMAN,
        ),
        attach(
            'And this is the moment he is blamed for.',
            DUEL_ON_THE_BRIDGE,
        ),
    ),
}
