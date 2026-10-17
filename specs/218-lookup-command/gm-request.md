# GM request, verbatim (2026-10-17)

Dictated. Transcription substitutions that apply: "setting nodes" = setting notes; "Imperial
Bounties paid" = the Imperial Bounties page; "WASP" = Wasp; "we has that as context" = it has that
as context. "Craig" is one of the players.

## Message 1

> One of my players has mentioned that, you know, he has trouble remembering, like, the terminology
> that we're using. So, for example, he was referring to the character Hideki and couldn't remember
> either the term "gosonin" or the term "escort". So I kind of wonder if there is an easy way we
> could do like a `/look-up` command in Discord. Now when we did our tests in Gemini for like
> prompting for NPC backstories, we found that we really did need to use kind of a somewhat
> expensive model, and we really did need to load in like all of our setting nodes, because if we
> ever did anything other than that, then we would get demonstrably worse results as determined by
> an extensive blind trial. However, I suspect that we could use a cheaper model that makes use of
> my, you know, kind of same Gemini API account thingamy. And that cheaper model would not need to
> use nearly so many tokens because I don't think that we need to load, like, the entire context of
> absolutely everything into it. And that would allow for a lookup query like Craig being able to
> say
>
> ```
> /look-up what are our minions called?
> ```
>
> And then the command would be able to give a response based on the Wasp Clan Hierarchy in which
> it says something brief like it's not going to give a three paragraph write-up or whatever but it
> would say something like
>
> ```
> The PCs are Marshals (Haribugyo, literally "magistrate of the sting")
> Their immediate subordinates are Inspectors (Metsuke, literally "one who directs their eye")
> Their staff are Escorts (gosonin, literally "transport guard")
> ```
>
> Now this is just an example, and for instance, uh, like a response might think that you were
> asking about the names of your direct subordinates, rather than asking for the terminology. So,
> you know, like, I don't know that anything that we built would give precisely the answer that I
> gave, but I'm just kind of giving an example of the type of query that someone might ask, and
> that it needs to be kind of be able to be broad, because if you don't know the term that you're
> looking up, then it's not going to help you to be able to do like a glossary search for escort or
> inspector or whatever. And this is kind of what LLMs are best at. So I would be interested in
> trying to build a tool like this and seeing if we can make it cheap enough that, like, if it only
> costs, you know, like, I think that every time I want to use the synthesize backstory button on
> the character generator web app, it costs something like 40 cents. And that's because of the size
> of the prompt and the fact that we have to use an expensive model, etc. But I feel like it's more
> likely that we would be able to get away with something significantly cheaper that's like a
> fraction of that cost. And at that point, I would love to integrate it into Discord so that that
> is a thing that someone can ask. And I would love it if the command messages the person
> privately, you know, because like, I know that when you uh, like invoke a command like that, then
> it can just post publicly to the channel, or it can just like post in the channel, but it's like
> a private message that other people don't see. Because then people don't have to feel like
> they're bothering people by spamming the channel by looking up stuff, you know?
>
> What do you think about this? Does this sound achievable? What kind of experiments do we need to
> run to measure the efficacy of whatever it is that we implement?

The session proposed: a glossary built once by an expensive model, a cheap Gemini model answering
from it, an ephemeral ("only you can see this") Discord reply, and a blind-graded question set
measuring correctness, leaks, invention, brevity, cost and latency across model tiers. It assumed
`l7r.md` held GM-only material and proposed excluding it.

## Message 2

> Yeah, that sounds good. I like the idea of building a glossary around an expensive model. Uh, I
> mean, although, to be clear, we shouldn't have it be an expensive model in Gemini. I should just
> have you build the glossary. Uh, and then Gemini is handed the glossary. But we should also make
> sure that the glossary handles, like, you know, just facts about the world. Like, the Ministry of
> Retainers should be something in the glossary, you know? But then, at the same time, uh, I don't
> know, like, hyper-specific stuff, like... The budget of a county magistrate should not, even if
> the term "county magistrate" is, etc.
>
> l7r.md is not meant to contain GM-only information, so it's not out of bounds. What in there did
> you think was out of bounds?

The session answered that nothing specific was out of bounds (a grep for GM-only/spoiler markers
found none); only Obsidian Portal's `game_master_info` fields are hidden from players. It proposed
the glossary scope (names and recognizable things in; numbers and procedures out), a Claude-built
glossary file, and feature 218 run through spec-kit.

## Message 3

> Yes, that sounds good. Please proceed with that. Um, I guess when it comes to the example
> questions, then I think a good context for this right now, to be clear, is that we are in the
> Wasp Clan campaign specifically. And that means that, like, we has that as context. And it would
> be even better if you could make sure that the player sending the command, you know, like, that
> the model or whatever knows which character that is. So, like, kind of has information about
> that character. Which, I mean, you can also probably populate, like, a lookup of that, because
> you can look at the character sheet app and then pull down that information, and uh, even though
> I think, you know, we don't exactly say, like, what people's original domains of origin were, uh,
> you should be able to, like, infer that anyone with a Lion Clan school came from the Lion Clan
> prior to being a Wasp, and anyone who had a Mantis Clan school came from the Mantis Clan prior to
> joining the Wasp Clan, etc. So, like, if somebody asks, "Who is our boss?" then that is in the
> context of the wasp campaign, and then the answer would be Tsuruchi Kyoma. I also think that
> another category of thing, and this is important, is uh, anytime we mention a person in the
> response, then we should link to that person. Now that, I think, does not have to be something
> that the LLM does, because I think that if we see something that looks like a person's name, then
> we could mechanically do a search for them and then link to them. Like, in a scriptable way, by
> basically just doing a post-processing step over the response. However, I also think that a type
> of question that someone would ask would be like, what are the imperial bounties? And then, I
> don't know that we would actually want to list all of them, but we should the link to the
> Imperial Bounties paid on Obsidian Portal. Or if somebody says, what is the WASP org chart, then
> that should link to the WASP hierarchy page on Obsidian Portal. So, like, that part probably is
> something that the LLM needs to do because people will not be able to phrase the question in a
> way that allows a mechanical response. But for things like people's names, then we could make
> that work uh, by linkifying things that the LLM outputs. Another example question would be like,
> who are the fortunes that the crab worship? And I mean, that's one where the correct answer is
> all of them, but in context, someone is really asking, like, who are the two patron fortunes of
> the crab clan? So I hope that this gives some pretty good examples of the kinds of questions
> where they need to be able to be vague and maybe even worded a little bit inaccurately, but, you
> know, it's a do what I mean and tell me what I'm looking for even if I have not properly
> expressed it kind of deal.
