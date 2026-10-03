# GM request - feature 214

Received 2026-10-03, in the gm-assistant session "Discord repl". Reproduced verbatim, voice-dictation
artifacts included. Substitutions that apply (the user-level mistranscription table): "role(s)" is
"roll(s)"; "DON" / "DOM" is "Dan"; "Asawa Ishii" is "Isawa Ishi". "Marshall" in message 1 is a
player addressing someone at the table and names nothing in the code. This is the text the
`spec-fidelity` review grades [spec.md](spec.md) against.

---

## Message 1

I would like to work on our Discord integration. One of my players, who has the character Tadashi, is playing an Isawa Ishi. Therefore, the third DON technique ( And apparently we should add DOM and DON to the list of words that map to "dan" in voice to text in our user-level CLAUDE.md) is very useful and I would like to even see it integrated in with the other roles that get recorded. So for example, let's say that someone records an etiquette role. And then Tadashi decides that he will boost their etiquette. I would like for him to be able to not only trigger one of these roles, but indicate who he is boosting, and then have that automatically add to the role. So for example, let's say that someone rolls a 13 on their etiquette roll, and then Tadashi rolls a 8 on his Asawa Ishii third dan technique. ("Isawa Ishi" became "Asawa Ishii" in voice to text). This means that their role would be effectively a 20. Now this is important because note that etiquette rolls get rounded down to the nearest increment of 5 before being recorded after all bonuses are added. But we must take care to make sure that when we add a bonus after the fact, we add it before the rounding down. So it is entirely possible for someone to make an etiquette roll and then we ingest the etiquette roll and then we record the etiquette roll in Obsidian Portal. And then someone says, hey Marshall, can you have Tadashi boost that etiquette roll? And then he says yes. So if he were to add plus eight to a role that had already been rounded down to 10, then that would make the role a 15. But the role would actually be a 20 because the rounding down should happen based on adding a bonus to the original actual role. I hope that makes sense.

So the question is, how do we denote what the role is for? And I think that there are a couple of ways that we could do this. One is that I would like to have a `/ishi-3rd-dan-technique` action someone can take in Discord And if they reply to someone's message in which that person made a role, then we can always assume that that is the role that was being boosted. The same thing would apply if they posted a copy-pasted role as a message reply. And then if they just post it as a free-floating message, then we should consume it as a bonus where when I am annotating things, I would annotate which role the bonus applies to. So like when selecting that as the role being annotated, I would then be presented with a list of roles, both roles that have already been annotated and roles that have not yet been annotated, where I can select in the menu which one it is that I am applying the bonus to. How does that sound? Does that seem doable?

## The session's answer to message 1 (summarized - this is what message 2 says yes to)

1. Rounding already happens at write time on the raw total, and each write replaces the
   conversation's earlier lines, so a boost stored on the roll re-rounds from the raw total (13 + 8
   = 21 -> 20), even after a 10 was already written - provided the conversation is still open.
2. Discord cannot invoke a slash command AS a reply; the reply reference is dropped. The fix is a
   MESSAGE command: right-click / long-press the roll, Apps, "Ishi 3rd Dan", and the bot receives
   the exact target message.
3. Three paths: the message command on the roll (target exact); a typed or pasted roll posted as a
   genuine reply (target from the reply); the plain `/ishi-3rd-dan-technique` or any boost with no
   target, held for `annotate()`, which offers an arrow-key list of every roll in the conversation,
   annotated or not.
4. The sheet app owns the commands (it knows Precepts and Void, rolls Xk1, spends the void point);
   gm-assistant collects, attaches, enforces once per roll, and adds before rounding, before the
   contest margin, and into the exact interrogation total. The sheet half goes as a requirements
   document.

## Message 2

I think "Ishii" should be mapped to "Ishi" as well just in general.

That plan all sounds right, so please proceed with that and take it through to implement and deploy it. Are you able to deploy character sheet things from here? Or do I need to open up like a separate Claude Code thing in the character sheet container and then figure out a way to have you talk to that container? remember how we've done this in the past.
