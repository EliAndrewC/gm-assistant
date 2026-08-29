# The GM's request, verbatim

From 2026-08-29. Voice-dictated, so "roles" throughout means ROLLS - the GM says so
themselves at the end. Quoted as written.

## Why annotation matters

> So now here's the thing about annotating rolls: It's important. For example, if I look at my
> notes and I see that a character made a precepts roll, That doesn't help me very much because I
> might not remember what the role was about. So what that really means is that we should not
> record most roles unless they are annotated. Now we have not bothered to do this with etiquette
> because etiquette roles are presumed to be about making an introduction. So, therefore, the
> annotation is redundant because almost every etiquette role is the same. But with almost any
> other role, we need to indicate whether the role was open or contested, and we need to indicate
> what it was for. like what argument was being made. etcetera.

> In some cases, a character will make a role just to see what they understand about a situation.
> For example, if a bounty hunter is describing the capture of a fugitive, someone might make a law
> role just to assess for themselves whether or not The arrest was legal. or something. In this
> case, I think it is still useful to annotate the rules, though I often just don't bother writing
> those down. However, if we make it easy to do this, then I think that it would be useful as a
> record of the conversation, particularly if we are storing the order in which the roles were made
> because then players or me as the GM looking at a character will be able to remember the
> conversation by seeing these sequence of roles that were made.

> Also, I am using voice to text, so the word "rolls" keeps getting transcribed as "roles" but I
> trust that the true meeting is clear.

## When unannotated rolls may and may not be saved

> I don't think that I want to save unannotated roles to Obsidian portal unless the conversation is
> ending. So if I call the end_conversation() function manually, and there are unannotated roles
> which have not yet been saved that I would like for the function to raise an exception and print
> an error message saying, hey. You need to Annotate these roles before they can be saved.
> Otherwise, the conversation is not over. However, if I exit the Python REPL, that I know that
> this causes the end conversation function to be called. And in that case, I just want the non
> annotated roles to be saved because it is better for them to be saved than to be lost.

## The annotate() menu

> So let's talk about how rules get annotated. I think it probably makes sense for me to be able to
> call a function which presents me with a text menu where I can indicate whether a role was open or
> contested and where I can enter a textual description of what the role represented. If there is
> more than one role, which has not been annotated in this way, then I would first select between
> which of the roles I am locking in.

> This will be relevant when I call a function called `annotate()` which is what will present me
> with the menu of options that we are talking about. The roles which I have made will be available
> here. And then I can select whether or not any of my roles become a contested role made against
> One of the roles made by a player.

> I think being able to exit out of the annotate text menu by hitting control c and having that not
> save anything would be good.

## Capturing the GM's own opposing rolls

> Usually when a roll is contested, then I will almost always have previously made an xky roll which
> opposes it. For example, Let's imagine that a player posts a precepts role, and I have recently
> done this in the Python REPL:
>
> ```
> >>> xky(7, 4) + 8
> ```
>
> That would be the NPCs version of the precepts role. However, what I see now is being somewhat
> awkward is the fact that the bonus is captured in the REPL but not visible within the function
> itself. So my hope is that you can hook into these functions by making the xky function store its
> recent results. In particular, you can have it store all results associated with the conversation
> that has begun. And if a role such as this is made outside of the context of a conversation, then
> it does not need to be stored. However, because storing both the roles and the bonuses is
> important, then... I perhaps we could update the XKY function to be called like `xky(7, 4, 8)` or
> something. With that being said, I know that you do technically have the ability to read the
> Python history. So maybe it is not actually necessary for us to do this. It would be great if we
> could store the bonus by just passing it in the manner that I am accustomed. to saving it, like,
> if the Python history says "xky(7, 4) + 8" then Whatever process stores the result and associates
> it can look in the history to get the plus eight and then make sure that the total is what gets
> stored.

> Another slightly awkward thing is that we need to be able to apply bonuses after seeing the
> results of a call because some characters have that ability. For example, many schools have a 3rd
> dan technique which lets them apply free raises after they see the result of a role. So I think we
> can define a "apply_bonus_to_previous_roll()" function, which adds an extra bonus onto whatever
> the previous x k y role was. so that if I say, `apply_bonus_to_previous_roll(15)` then you know to
> update that result.

## Scope

> How does all of this sound? I think I've given you enough description for you to be able to
> implement something at which point we can begin testing it out and seeing whether it matches my
> needs.

## Later in the same exchange (2026-08-29)

These two statements came after the spec was first drafted, in reply to questions about it. They are
recorded here because the spec rests on them - FR-013 in particular has no other authority, and a
quote a future reviewer cannot check against this file is worth less than one they can.

### Ruling on the gate, given the project's rule against pre-review gates

Asked directly whether `end_conversation()` refusing to close was the same shape as the pre-review
gates the GM had previously had removed from `/chargen`:

> As for the gate on end conversation, I understand that this is different than what I wanted for
> that other skill, but I think it makes sense here. So please accept my ruling and judgment that it
> is indeed something which should gate the end of a conversation when I call the end conversation
> function manually and there are still non annotated rolls.

### Replacing `apply_bonus_to_previous_roll()` with `_ + 15`

On being shown that an int subclass would capture `xky(7, 4) + 8`, the GM saw a consequence of it
that had not been proposed and chose it over their own earlier suggestion:

> That's a great idea about the int subclass. I love that. it also allows me to be able to do `_ +
> 15` as the mechanism For applying a bonus after seeing the results of the role, which is perfect.
> that can be the thing that we do instead of the `apply_bonus_to_previous_roll()` function, which
> is even better.

## Follow-up requirements (2026-08-29, after first use)

Three changes, given after the first version was built and tried.

### Rolls made BEFORE the conversation opens must be available

This REVERSES FR-011 as originally written, and the reversal comes from the GM's actual workflow
rather than a change of mind about the principle:

> I would like to be able to roll the NPCs side before opening. That is actually the most common
> workflow is that by the time I go to annotate something, I have already made the role, which I
> expect to mark as being paired with a role made by a player character that I am about to annotate.

### Discarding a roll made in error

> When selecting a role to annotate, I should also be able to discard the role. Like, if somebody
> made it in error, then I should be able to mark it as something which gets ignored and not
> recorded.

### Contested rolls carry automatic bonuses

> One last thing about recording contested roles is that contested roles automatically get some
> bonuses. The most notable one is that whoever's skill is higher gets a number of free raises equal
> to the difference between the two skills. So for example, if two people are making a contested law
> roll, and one character has two points of the law skill, and a different character has four points
> of the law skill, then that character will get a plus ten to their role because their law skill is
> two points higher than the other, which is two free raises, which is plus ten.

> Thus, when I select a role as being contested, you should present me with a menu selection, which
> allows me to indicate what the bonus that is applied to one side or the other is. You should select
> a default value based on the two roles that were made. For example, if one character made a 7k4 Law
> roll, then we can infer that their loss skill is probably three. By doing this for each character,
> we can. infer what the total net bonus was to one side or another. This is not completely reliable
> because there are things that can cause extra dice to be rolled. Therefore, I should be able to
> override this default value by entering my own value.

> This is also important because there are other things that can add to or subtract from these
> various roles. For example, a player who has used the Oppose Knowledge skill might be applying a
> penalty to the NPC, though in this case I would track that with a `_ - 6` (if the amount subtracted
> was 6) from the NPC roll. But other things can provice bonuses, including circumstances and role
> playing and the result of previous roles, which there would not be a good general purpose way to
> track. Therefore, what is probably easiest is for me to be able to indicate the total net bonus or
> penalty being applied to both sides.

> It is important that we track the difference between bonuses and penalties because, for example, a
> player whose Opponent received two free raises. should not have this reflected by having minus ten
> applied to their own role because the value of their own role is still significant in end of
> itself. It makes a difference whether they got a 30 or a 40 even if This is "only" an accounting
> mechanism and the difference between their role and their opponent's role did not change.
