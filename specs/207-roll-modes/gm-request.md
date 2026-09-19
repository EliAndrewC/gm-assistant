# GM request, verbatim (2026-09-19)

Three messages in the "Discord repl" session, plus the session's questions between them and the
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

## Rules-file edits made on the GM's instruction (2026-09-19, uncommitted; the GM handles git there)

- `rules/02-skills.md`, Sneaking: now says the skill is ALWAYS rolled contested against the
  investigation of potential observers, and that the GM need not make an opposing roll when nobody
  is actively watching.
- `rules/02-skills.md`, Acting: "contested against the interrogation of anyone speaking to the
  character" became "contested against the investigation of anyone ...".
