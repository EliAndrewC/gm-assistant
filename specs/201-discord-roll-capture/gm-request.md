# The GM's request, verbatim

Assembled from the GM's messages on 2026-08-28. Quoted as written (voice-dictated, so spelling
and capitalization are theirs - "roles" means "rolls", "necks" means "knacks"). This file exists so
the spec can be graded against the request rather than against itself.

## The problem and the target format

> One of the things that slows down the game for me is that I have to take the time to transcribe
> those rolls into my notes for the NPC that they are talking to. Lately, I have taken to simply
> saving a link to the rolls that they are posting instead, But this means that I have to click on
> that link in order to jump into Discord and then scroll down to see what everyone put.

> This means that I cannot simply look at the character in obsidian portal in order to see what
> roles were made in the past. I would rather be able to have something which I've done in the
> past, which is formatted like this:
>
> ```
> Sadakichi / Moriko / Jimen / Tetsuro / Toshihiro etiquette: 35 / 25 / 25 / 20 / 15
> ```

## The recording rules

> Note that those are all rounded down to the nearest increment of five. This is because Open
> roles, I do not distinguish between, for example, a twenty five and a twenty eight. Also, open
> etiquette rolls are capped at forty. Thus, if someone rolled a sixty eight, I would simply write
> down forty. This reflects the fact that there is an upper limit to how much appropriate
> politeness you can display. Because politeness involves restraint, a very high role on etiquette
> simply cannot represent something extremely noteworthy because a thing which is noteworthy in
> most circumstances is almost definitionally impolite. Whereas this is not true for other skills.
> A gift can be perfunctory or a gift can be noteworthy. A gift can be so exceptional that someone
> will talk about it for their whole life. Therefore, recording higher roles for gift giving makes
> sense to me. Now this is particular to the etiquette skill, but other open rolls do get rounded
> down usually to increments of five. Whereas Contested rolls are compared to what the other person
> rolled. Therefore The difference between the rolls is rounded down to an increment of five, but
> the rolls themselves are not rounded.

> A contested role should show each of the two roles that are being compared after those roles are
> adjusted for bonuses on each side. and then it should show the difference between them and who
> won. The amount that the winner won by should be rounded down to the nearest increment of five,
> just like all open rolls are rounded down to the nearest increment of five. I think that is
> enough for us to begin building something even though there will be more subtleties to be added
> later.

> There are other rules which it would be good to Explain. But at a high level, this is probably
> enough to capture a basic set of requirements.

## Where it goes

> To be clear, we would put this in the character bio section of Obsidian Portal directly
> underneath their portrait. We do not need a separate GM only section for explaining things like
> rounding and why things are capped.

## How it should be driven

> what I would like to do is be able to use my existing Python REPL which is started with the
> ./scripts/repl.py script, to grab these roles from Discord.

> In particular, one of the things that we need to be able to indicate because it cannot be safely
> guessed is what NPC the players are talking to when they make various rolls. So for instance, if
> a bot or some other scripted process notices that rolls are being made, then it might need to
> save that off and wait to upload it to Obsidian portal until we know for sure which NPC the rolls
> are meant for.

> We could have a background thread or something like that, monitoring for changes, and updating
> them. And then I could communicate with that thread by calling various functions. For example, I
> might call a function indicating that we have begun a new conversation which I indicate who the
> conversation was begun with. like, it might be as simple as `begin_conversation("Otsuki")` And
> because we already have logic for translating NPC names into their Obsidian portal references
> since we already use that for some of our other functions, such as our discern honor rolls, then
> that can set the state of the conversation. And then I could have an `end_conversation()`
> function which marks the conversation as over, etc.

## The two input paths

> Note that there are two primary ways in which rolls are made. first and most common is Copying
> and pasting a dice roll result image from the character sheet app.

> other way which people post rolls is to simply say what the roll was, e.g. Craig posted this for
> that round of etiquette:
> ```
> 38 Etiquette @3
> ```
> Note that the @3 convention denotes that his character has a three in his etiquette skill, which
> does not matter for open roles, but does matter for contested roles. So many players simply post
> it just in case it ends up mattering to be in the habit of posting it when it is needed.

## The character-sheet dependency

> we will still need to integrate with the character sheet application because we will need to be
> able to look up facts about a particular character. For example, if a player posts that they
> rolled a forty four on precepts, then it would be nice if our integration could look up what
> their score in the precepts skill is because that matters if they are making a contestant roll.
> And the player may not have posted that, although it is also possible that they have.

## Scope for now

> So for now, I guess we can focus here on the initial scope that we had discussed

> I think that is enough for us to begin building something even though there will be more
> subtleties to be added later. Do you agree? If so, then please proceed with that. And then I will
> create a test Discord server shortly. and we can begin testing on that.

## Explicitly deferred (NOT this feature)

The GM was clear that slash commands and an always-on bot are future work, and that they belong in
the character-sheet repository, not this one:

> I mean, I'm not saying that we do all of this right now. But as I think about it, this is the
> kind of feature that it would be nice to be able to add. And I'm assuming that we can start off
> with the kind of small scope, easy version of this that we had originally talked about, and then
> eventually build up to something bigger.

> So it sounds like what we are going to do is eventually have a bot for each of them, and then the
> character sheet, one will allow roles, and the... g m assistant one will handle obsidian portal
> integration and such.
