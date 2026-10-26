# Feature 230: the GM's request, verbatim

Dictated 2026-10-26 in the session "Discord REPL". Dictation substitutions that apply (from the
user-level table): "role(s)" = roll(s); "tack", "tacked", "attacked" (+ roll) = tact; "a post
social" / "a post knowledge" = Oppose Social / Oppose Knowledge; "tie. What is going on? To a
specific NPC" is one sentence ("tie what is going on to a specific NPC").

## Message 1

> I would like to work on our Discord integration in our Python REPL. Specifically, I would like
> to be able to add support for conversations that the PCs are having with multiple NPCs. When
> this happens, there should be a primary NPC where the roles are uploaded to. And then, for the
> other NPCs that are in the conversation, then an entry is created for the conversation that
> mentions the conversation by topic and then links to the NPC that actually holds the records
> for that conversation. For example, if a conversation is happening with Hideki and Souma, and I
> invoke it with
>
> `>>> begin_conversation('Hideki', 'Souma', 'stolen sheets')`
>
> Then because Hideki was listed first, then he would be linked to from Souma's character sheet
> for the 'stolen sheets' conversation.
>
> I think that the way that I would like to interpret what is and isn't a character name is that
> we must always list at least one string argument, and if there is only one string argument,
> then that is the name of the character, and if there are two or more, then exactly one of those
> arguments should be not the name of an NPC. And that argument is the name of the conversation.
>
> The first NPC listed has everything work exactly the way that it works now. So for example, if
> I say
>
> `>>> tact()`
>
> then that would be rolling, tacked for the main NPC for the conversation, who in this case would
> be Hideki. However, I would also be able to say
>
> `>>> hideki.tack()` or `>>> souma.tact()`
>
> And that would tie. What is going on? To a specific NPC who was declared to be in the
> conversation when it began.
>
> Similarly, by default, when I say something like
>
> `>>> xky(5, 3) - tact`
>
> then that would be presumed to be for Hideki, because it was not declared, but were I to say
>
> `>>> xky(5, 3) - tact - souma` or `>>> xky(5, 3) - souma.tact`
>
> then that would register it as belonging to Souma. I'm actually not 100% sure how well this
> will work, because I know that making certain types of rolls triggers things like uploading
> stats to an NPC. So I'm not 100% sure that marking something as attacked role and then
> afterwards marking that attacked role as belonging to Souma would not cause issues by having the
> role associated with Hideki before the role was finalized. I'm sure there is some clever way
> around this, and I would indeed like to make this work, if possible. But I want you to take this
> into account when implementing this change.

## The session's reply (summarized), which message 2 answers

Defaults proposed: the argument rule exactly as stated; `hideki` / `souma` handles at the prompt
for the conversation's life (refusing to shadow an existing name); the primary's record gets every
player roll line and the heading; each NPC's own GM-only notes get that NPC's numbers, hidden
Sincerity rolls and void points; other NPCs' records get a link entry; a contested line names the
NPC whose roll was paired, a typed total defaulting to the primary. Two rulings asked: which NPC
an Oppose Social / Knowledge penalises, and whether `/discern-honor` covers only the primary.

## Message 2

> Yes, for a post social and a post knowledge, you should default it to the primary with a way
> for me to move it to another NPC.
>
> Discern honor actually works on all NPCs in a conversation, so you should make that the
> implementation. You can file a ticket in the character sheet repository Since I have another
> Claude Code session in that container active right now and watching for whatever issue you
> create. Additionally, they have an issue for you to work, which relates to your integration
> with them anyway.
>
> I do think it is worth having a `add_to_conversation()` function defined to which I can pass any
> number of strings in order to add new NPCs to the conversation. I suppose we can also have a
> `remove_from_conversation()` function that works like that, but in reverse. And then I suppose
> if the primary NPC were removed from the conversation, then rather than making another NPC the
> primary for the conversation, we should continue uploading our results to the original primary
> NPC's Obsidian portal entry, but then roles made by them should stop working. And should raise
> an exception. So for example, if we have a conversation with Hideki and Souma, with Hideki as
> the primary, and then Hideki leaves the conversation, then I must always call e.g.
> `souma.sincerity()` rather than expecting that `sincerity()` calls will dispatch to Souma, and
> Hideki's Character entry in Obsidian Portal will continue to be where conversation roles get
> uploaded. Also, if someone is added to the conversation, then we should probably mark the point
> at which they come in on the Obsidian portal entry. So, for example, if a bunch of rules are
> made and then recorded, and then someone is added to the conversation, or for that matter, if
> they leave the conversation, then that should be noted at the point in the conversation where
> they came in or left because that is important context for looking back at rules that happened
> later.
>
> I like your approach for annotating ownership of a roll, but we should make sure that both
> `- tact - souma` and `- souma - tact` are equivalent to each other. I believe your proposal does
> make that work. I just want to make sure.
>
> I believe that that is all that you need in order to implement all of this, but please let me
> know if I am missing anything and need to explain any more. Otherwise, I believe that you are
> able to coordinate with the character sheet container through GitHub, both in your issues and
> in their issues. Thank you.
