# GM request, verbatim (2026-09-19)

Seven messages in the "Discord repl" session, plus the session's questions between them and the
GM's answers. Nothing the GM said has been edited. **The GM dictates by voice-to-text, and says so
in message 1**: read "role(s)", "holes", "tools" and "rule(s)" as "roll(s)" wherever dice are meant,
"Don" as "Dan", and "tapped value" / "attacks" / "tech" as "tact value" / "tact" / "tact".

**THE FEATURE IS NOT FULLY SCOPED YET.** Message 3 ends: *"I have more things that I want the
feature to cover, so do not begin the implementation yet."* This file grows as the GM adds them.

## Message 1

> I would like to make some changes to refine the annotate() function we use to tag rolls made
> during conversations in the repl. Also, I am using voice to text, and so the word "rolls" is
> probably going to show up as "roles" during this conversation but I trust that you will be able
> to tell that I actually mean "rolls" when talking about this functionality. [...]
>
> Anyway: some rolls are always open rolls. For example, the pontificate school knack may only be
> made as an open roll. Athletics is also always open no matter what.
>
> Many other roles can only be made contested. For example, manipulation is always a contested
> role, and therefore there is literally no other option that should be selectable. The same is
> true for interrogation and sneaking and acting. However, something which is awkward here is the
> fact that although these things are always rolled contested, there is not necessarily an opposing
> role to contest against. For example, a sneaking role to blend into a crowd is always rolled
> contested against the investigation of anyone who can possibly observe you. However, in many
> cases, there is no specific NPC who is actually watching. And therefore, I would not actually
> register a role, even though the role is made contested. Therefore, we need some way to register
> such roles which are always contested as not actually opposed. On the other hand, Manipulation is
> always opposed by a tact role, no matter what. Even if the person doesn't have tact, even if they
> are completely overwhelmed and outclassed, there is always a role registered because the amount
> that you exceed the manipulation role by their tact role affects the outcome of the role.
> Interrogation is similarly always opposed though in many cases I do not register an actual role.
> However, I think that it might be good to begin recording in the public section where the players
> can actually see the result what they "got" from the role. For example, "didn't seem to be hiding
> anything" or "seemed sincere". In fact, I suspect that we should probably just have a default
> outcome of something like "nothing hidden detected" which is logged anytime the sincerity role
> beat the interrogation role. but then that exact same thing is registered even if I don't bother
> to roll sincerity because the person is being completely truthful. This is the thing about
> interrogation: it can be difficult to tell whether the result that you are getting is because
> someone is being honest or because they are faking sincerity.
>
> Now what is also somewhat awkward is the fact that there are several skills which are almost
> always rolled open, but which can technically be rolled contested. bragging and intimidation and
> culture and heraldry and history and underworld are almost always rolled open. Even though
> technically any one of them could be made in a contested role if someone was arguing with an NPC
> about these topics. So I think it would be good if the menu that I have available to me defaulted
> to something while allowing me to press some kind of key or maybe make some kind of keystroke
> which undoes the default selection. Like, I don't want something pre-entered such that I only
> have to hit enter in order to accept it. I would like it to already be selected but maybe if I
> hit the left arrow twice, or if I hit the backspace key twice in a row, while there is no text on
> the current line, then that undoes the selection or something. I'm not sure. But I think that
> that's the sort of thing that I want to be able to do just to make the selections easier.
>
> this is all kind of a lot, but it all sort of feeds into the same basic idea which has to do with
> how these different roles are selected and categorized and whatnot. What do you think is a good
> way forward? [...]

(The elisions are the request to save the voice-to-text memory and the question about process;
neither specifies the feature.)

### What the session proposed in reply

- One per-skill MODE table driving `annotate()`.
- The "undo" keystroke: a double backspace on an empty line is not reachable through `input()` and
  readline (readline cannot call back into Python on a key). Proposed instead: for a default-open
  skill the kind question is SKIPPED and the prompt reads `open - what was it for? >`; a bare `c`,
  `ob` or `d` as the entire answer switches kind. **The GM did not object to this in messages 2 or
  3 but has not explicitly accepted it either.**
- Flagged that `rules/02-skills.md` gave sneaking an open use, and that pontificate might not be
  captured.

## Message 2

> I would like to update the sneaking rules to clarify this. When I said that it was rolled open in
> the rules, I guess what I really meant is that I was not actually necessarily making an opposing
> roll. However, I think that for clarity, it is better to say that sneaking is always rolled
> contested. So can you clarify this in the rules for me? [...]
>
> pontificate roles are captured, I think. But you should definitely confirm that. They definitely
> can be made, and they can be captured. So we should make sure that we are capturing them.
>
> we can interrogation when we are on the same line of questioning then I think that the way that
> we should do this is that we should have me as the GM when I am annotating interrogation holes
> label the line of questioning which is not something that we are doing currently. Then we can
> group player roles together for interrogation just like we do for etiquette. Except that with
> etiquette, we round down to the nearest increment of five and cap at the number 40. And do not
> list what their skill is because it is an open role, Whereas with interrogation, we would list
> the exact role, using the uh, <roll>@<skill> convention e.g. 32@2. But here's the thing. When the
> default option is selected of "nothing hidden detected" then we group them on the same line.
> However, if a specific PC does detect something hidden, but the others do not, then we would need
> to split them out to a separate line or otherwise indicate that they were the specific player
> character who detected something hidden. Awkwardly, we also need to be able to do this after the
> role has been registered and annotated. Because players can build up free raises over the course
> of a line of questioning.
>
> So I'm thinking that maybe we could do something like this: we ahve a `new_line_of_questioning`
> function which can be called with a description and a role. For example, I could say
> `new_line_of_questioning("Fumitake's contributibutions to the Wasp treasury", xky(8, 3) + 10)`.
> Note that I am including both the description and the sincerity roll that Fumitake is making. Any
> interrogation roll which is made after that new line of questioning and before I call another
> `new_line_of_questioning()` function (or any interrogation roll made BEFORE it if it is the first
> time new_line_of_questioning has been called after begin_converastion() was called to start the
> conversation) would be matched against that sincerity roll, and the roll itself conveys the
> sincerity skill which you can use for contested roles. Now, strictly speaking, there are two
> schools which roll one extra die on sincerity for their school. These are the Shosuro actor and
> the merchant school. Because the school of a character is listed on the character in Obsidian
> Portal, then we should be able to look for those strings mechanically and then know whether or
> not the character is specifically one of those two schools. So if someone with the merchant
> school were to roll eight dice and keep three dice, then we would know for a fact that they have
> four sincerity rather than five. But if anyone other than a merchant or a Shosoro actor makes an
> 8k3 sincerity roll, then we know for a fact that they are someone with five sincerity. And then
> we could use that to calculate the free raises on either side. Technically, there are some
> schools that allow you to select what you want your first Don extra rolled dice to be, but I
> don't think we need to worry about that because I don't think that that will actually come up in
> practice.
>
> [...]
>
> players rolling sincerity, tact, and investigation are not necessarily making those roles
> contested because while it is true that interrogation always contests sincerity, some sincerity
> roles are open. Similarly, while manipulation is always worth contested against attacks, some
> tech tools are open. And while investigation is always worth contested against sneaking,
> sometimes investigation is ruled simply to evaluate a scene. Or look for information. In fact, I
> think we should add investigation to the list of roles that when a player makes it, is presumed
> to have rolled open and that needs to be overwridden, because it is rare for a player to roll
> investigation in a conversation and not have it be open.
>
> I agree with your approach about a manipulation rule with no associated tact rule. I can just
> enter the amount of the roll. I think the option here is to actually have a default value of 15.
> So like, if there are available roles and you are not sure which one is tact then in addition to
> which available roles I am selecting to contest the manipulation, one of the available options
> for me to select would just be to enter 15 or to select the option that represents the number 15
> or whatever. Because that is kind of the default value that someone gets if they are not actively
> making a role to contest something. If I enter the number 15 in this way, then the tapped value
> is presumed to be zero. So the person rolling manipulation gets a number of free raises equal to
> their rank in the manipulation skill.
>
> I think we will treat acting as always being opposed. In fact, if we are recording acting during
> a conversation, then I think it makes sense for us to always record an opposing investigation
> roll. However, much like interrogation, you should not know what your opponent's role was. For
> example, if you are wearing a disguise, then we want to record what the opposing role was. But we
> do not want to show the players what the role was. Because then they would know whether or not
> the NPC saw through their disguise, but the NPC might see through their disguise and then not
> reveal that. So I think that acting should take an opposing role. But then also have a default
> value like interrogation does, where the default value is something like "no signs of your
> persona being seen through".

(The elisions are the git note about the rules repo and the request to extend the voice-to-text
memory.)

### What the session asked, with its defaults

1. The rules said acting is contested against INTERROGATION; the GM said investigation. Which?
2. Where do the hidden numbers go? Default: the NPC's GM-only notes, in a block like Discern
   Honor's, never the bio.
3. May the repl print who won, privately, in the GM's terminal? Default: yes, with the PUBLIC
   outcome staying the GM's call (default text unless the GM marks a detection).
4. Unopposed sneaking written like an open line, rounded down to 5? Default: yes.

It also proposed a `detected("Jimen", "...")` style function for marking a detection later.

## Message 3

> Oh yeah, Please edit the skill to indicate that acting is opposed by investigation rather than
> interrogation. Thanks.
>
> And yes, the hidden number should go into the NPC's GM only notes in a block like discern honors
> and never in the bio. That's correct.
>
> My terminal is never screen shared, so that is not a problem. I screen share a browser window,
> but never my terminal. And I never screen share the GM only section of the notes on Obsidian
> Portal. So no worries there. Thanks.
>
> Yes, the way that you are doing unopposed sneaking sounds good.
>
> Go ahead and write this into a spec kit feature. However, I have more things that I want the
> feature to cover, so do not begin the implementation yet. I want to resolve any of your questions
> about what we have talked about so far before talking about additional aspects to this feature.

### What the session asked after writing the draft spec

1. Rolls made BEFORE their own line is declared - move them in `annotate()`, or a time window?
2. Grilling: `new_line_of_questioning(desc, roll, grilling=True)`, default not grilling?
3. Is the typed undo (`c` / `ob` / `d` as the whole answer) acceptable in place of a keystroke?
4. Does acting need a change-the-outcome-later path? Proposed: no.

## Message 4

> Most of the time, with lines of questioning, I will explicitly call
> `new_line_of_questioning("Chizuru's death", xky(8, 3) + 10)` before the players roll
> interrogation.  Sometimes on the very first line of questioning a player will roll interrogation
> before I have a chance to do this, which is why I want it denoted here.  Players always ask me
> whether it's a new line of questioning before they roll another interrogation roll... though I
> suppose if a player makes a second interrogation roll within the same line of questioning, and
> then I start a new line of questioning, then the default thing should probably be to pull that
> roll into this one. But it might be worth some kind of menu option about that. So maybe instead
> of pulling in previous interrogation rolls automatically, then when I call the new line of
> questioning function, if there is a previous interrogation roll, then for each previous
> interrogation roll, then I am prompted to say whether that role should be discarded or treated as
> part of this line of questioning.
>
> Good point about grilling. Yes. We do want to be able to specify grilling and have it false by
> default. However, sometimes a player will begin grilling an NPC midway through the line of
> questioning. In this case, I think I want to be able to call a `grilling()` function which will
> retroactively subtract the free raises which the NPC received. If I call grilling twice within
> the same line of interrogation, then the second function should just print a message saying that
> the grilling was already recorded as happening or something..
>
> I don't think that we need acting outcome to be able to be changed later. The worst case scenario
> is that I can just edit Obsidian Portal directly, so that's fine.
>
> I would really like to have keystrokes detected. So is there a way that we are able to do that by
> pulling from the TTY or something? like I know that we're using readline now but in theory we
> don't have to, right?

### What the session asked after message 4

Is the `+ 10` in `new_line_of_questioning("Chizuru's death", xky(8, 3) + 10)` the NPC's casual
free raises added by hand? Proposed: the tool adds those itself on a non-grilling line.

## Message 5

(More voice-to-text in this one: "tax", "tech" and most uses of "tapped" are "tact"; "tapped die" is
"kept die"; "error" is the Air ring; "rules" is "rolls".)

> w.r.t. the grilling question, I would never apply the "lack of grilling" bonuses manually, so you
> can assume that grilling bonuses are only ever applied by the grilling flag which is false by
> default (thus assigning the bonuses of +10 to the NPC's roll).  I agree with you - any bonuses I
> add manually should be things which do not get adjusted, e.g. in this case the +10 was from
> Fumitake having 2 acting, whhich results in +10 to his sincerity roll.
>
> Okay, so here's another big thing that I want as part of this feature. A problem that I have
> sometimes is remembering what skill I have assigned to an NPC. For example, let's say that the
> players talk to someone, and then I make a tact roll. And then the players come back a few weeks
> of real-world time later, even if maybe within the game it's the same day or something. And then
> I have to make another tact roll for that NPC. I would like to use the same tact skill and not
> have the NPC's tact vary from session to session. However, this requires me currently to either
> write down what I did or to just remember. And I'm not going to be able to remember every skill
> for every NPC. Now, I think that we can probably do something about this. Obviously, I do not
> want to show what the NPC's skills are to the players. However, there is a GM-only section where
> this data could be stored in a parsable manner. So that mechanically, our code can grab it.
>
> Now, one thing I would like to get into the habit of doing is annotating the rules when I make
> them. For example, instead of saying
>
> >>> xky(8, 3) + 10
>
> I will try to start saying
>
> >>> xky(8, 3) + 10 - sincerity
>
> Now note that we will have to do some trickery in order to make this work. Thankfully, I believe
> that it is already the case that `xky()` returns an instance of a class with operator overloading
> to accept things like the plus 10. And then we can have that still also return an instance of the
> same class, which is then able to accept things like `- sincerity`. And then, of course, we will
> have to define a `sincerity` variable which is itself an instance of a class which and have
> operator overloading combine it with our rolls in order to mark what type of roll they are.
>
> Now, when this happens, I want a couple of things to occur. First of all, if we are in a
> conversation with an NPC, and then I do something like
>
> >>> xky(5, 3) - tact
>
> then we should immediately check what is on Obsidian Portal (or what we have cached from
> downloading it at the start of the conversation - we do not need to check every time, we can
> assume that nothing will update this in Obsidian portal besides our own repl, and I have only one
> repl going at a time), And that I am making different tech skill than what was there previously,
> then I should be notified of this and then given the option to either correct the skill that is
> there or cancel the skill. I would like to be able to cancel either by hitting Ctrl+c and having
> that actually caught and recorded as indicating that I made a mistake and that I will redo the
> skill correctly. Or I should be able to indicate that what was previously there was wrong and I
> am now entering something new.
>
> Note that for the purpose of this feature, we are assuming that the players are only ever talking
> to one NPC at a time. This is not strictly true, and a later feature will likely add the ability
> to track different NPCs. To the extent that this informs our implementation choices today, then
> we should be aware of it, but it is perfectly fine for now. for our implementation to just assume
> that whoever we have begun the conversation with is the only NPC whose skills are being rolled.
>
> Now, of course, the default and most common thing that will happen is that when I make a role
> such as the one above, then there will not already be a tapped skill recorded for that NPC, so we
> should record one. And then for the rest of this conversation, further tapped roles which I make
> should be checked against this value because we will have updated our local cache even if we have
> not yet persisted it to Obsidian Portal, since I believe that happens on some kind of debounced
> timer where we do it every 30 seconds or every two minutes or something.
>
> Also note that we need to record not only what the individual skills are, but also what the ring
> values are. For example, in this case, the NPC is rolling tact, which is an air skill, and
> therefore their air ring should be presumed to be three. And that also should be checked. such
> that if I enter the wrong value, then I am prompted about whether this was a mistake or whether
> it should be corrected. For example, I might have made a roll previously in which I just added on
> an extra one die to the rolled and kept dice because I knew that the NPC was spending a void
> point and then I did not bother to denote what had happened and therefore this is an example of
> needing to make a correction.
>
> I would also like for these skill instances like `sincerity` or `tact` to be callable. for
> example, if I say `tact()` And the NPC already has a tact skill recorded, then it can roll tax for
> them. ( Please update your memory about common voice-to-text errors to note that the word "tact"
> is often transcribed as "tax".) If I say `tact(vp)` then that should be rolling tapped while
> spending a void point, which is to say giving one extra rolled and also one extra kept die.
> (Also, the Voice to text appears to keep mistaking the word kept for the word tapped. So if you
> see me saying tapped, then your memory should indicate that this probably means kept.)  This means
> that `vp` must also be a class instance which is defined to indicate that a void point is spent
> in these cases and I should be able to also say `tact(vp * 2)` to denote that two void points are
> being spent, etc.
>
> early in a conversation when I have not yet rolled enough rolls for the functions to be able to
> know what ring and skill values are then the function can prompt me. For example, if I say
> `sincerity()` and you know that the NPC has three error, but you do not know their rank in the
> sincerity skill, then you can ask me what it is, and I can enter a number, between zero and five
> inclusive. I would also like to be able to say `sincerity(5, 3)` and have that be the same as if
> I had said `xky(5, 3) - sincerity`, doing the appropriate saving of values and also checks
> against previously saved values. However, I would also like to be able to enter a single number
> by saying `sincerity(2)` in which I am indicating that the character has a sincerity value of
> two. and that you should make a roll with whatever error they already have recorded or prompting
> me for what their error value is, which will be a value between two and six inclusive, if you do
> not already have it.
>
> Another great thing about tracking what types of roles we have made is that when I am annotating
> things, then you will often already know what role was opposing something. For example, if a
> player rolled manipulation and I have a tact roll, then when I call the annotate() function, then
> you can pre-pair the tact and manipulation rules against each other such that the only thing that
> I am asked to annotate is adding the note about what the manipulation rule represented, like what
> way in which someone was trying to twist another character's words or whatever. And then your
> default selections can be overcome with things like hitting the backspace key twice or whatever.

### What the session asked after message 5

A. A third answer at the disagreement prompt - "a void point was spent" - when the roll is exactly
   one die up in both rolled and kept?
B. With acting recorded, should `sincerity()` add acting's free raises itself?

## Message 6

> Oh yeah, good point about a void point answer. If I make a roll and then it seems to be wrong but
> it is wrong by exactly 1k1 or 2k2 either above or below what we previously had, then I guess we
> should have a void point option where the void point option is something like, based on the
> particulars, "The previous roll spent a void point" or "The previous roll spent 2 void points" or
> "This roll spent a void point" or "This roll spent 2 void points".
>
> And yes, good point about acting being recorded. So I want to be able to say `sincerity()` and
> have that automatically add acting bonuses. Along those same lines, history also gives bonuses to
> law and strategy, so we should apply that automatically as well once an NPC is recorded as having
> history. I guess that raises the question of how I actually do record such a thing. I guess the
> easiest thing is that we've already established that if I say `acting(2)` or `history(2)` then
> that will be recorded as something that the NPC has. I think I would further like to make a rule,
> then, that acting and history are never rolled by NPCs in that way, i.e. me saying `acting(2)` or
> `history(3)` do not actually generate roles the way that they do for every other skill. Instead,
> that serves only to record that the NPC has that rank in the skill. Remember that acting also
> gives free raises to intimidation. So we should apply that as well. we do not need to worry about
> acting giving bonuses to sneaking because that is conditional. The same thing is true for history
> giving bonuses to culture because that is also conditional. And so we should presume in both
> cases that that will not apply and that I will apply those bonuses manually if and when it comes
> up.

### What the session asked after message 6

C. Do the automatic raises also land on `xky(8, 3) - sincerity`, or only on `sincerity()`?
D. The rules make history's raises on CULTURE unconditional and on HERALDRY conditional - the
   reverse of what message 6 said. Which?

## Message 7

> The automatic raises should only be applied when we roll with the skill function and not when I
> roll with the xky function. So in your example, `xky(8, 3) - sincerity` should not get an
> automatic acting bonus, but `sincerity()` should.
>
> Oh, yeah, sorry. Uh, my bad on the history and culture. Uh, you are right and I had misremembered.
> So, yes, please always apply it to culture and law and strategy. And then do not ever apply it to
> heraldry because I can do that for them when appropriate.

## Rules-file edits made on the GM's instruction (2026-09-19, uncommitted; the GM handles git there)

- `rules/02-skills.md`, Sneaking: now says the skill is ALWAYS rolled contested against the
  investigation of potential observers, and that the GM need not make an opposing roll when nobody
  is actively watching.
- `rules/02-skills.md`, Acting: "contested against the interrogation of anyone speaking to the
  character" became "contested against the investigation of anyone ...".
