# GM request - feature 211

Received 2026-09-20, in the gm-assistant session "Discord repl". Reproduced verbatim, voice-dictation
artifacts included ("role" is "roll" throughout - see the project's mistranscription table). This is
the text the `spec-fidelity` review grades [spec.md](spec.md) against.

---

I am interested in updating my Discord integration in order to have more commands available. In particular, while we already have a `/etiquette` command, It would be great if there was a generic `/roll` command with auto completion where you could roll any skill and then also indicate void points and such. This would not need to handle discretionary bonuses that you apply after you see a role because you would be able to mark those on your character sheet after the role is posted.

it would also be nice if there was a slash command for individual skills like `/precepts` and `/sincerity` etc. I know there is some upper limit on how many commands a single bot can register, but I think it's something like 100. So I think that's totally fine for us to have individual slash commands for each individual skill.

We will leave out combat skills for now. But I do also want a /initiative command to roll initiative. like other roles that we make this should affect someone's character sheet so for example just as spending a void point when making a role from Discord it should actually mark the void point as spent on the character sheet (and someone should not be able to spend more void points than they currently have), Rolling initiative resets the combat round for that character And then we should be able to see the action dice on their character sheet if we go to it, etc.

This seems like a significant enough feature to warrant a spec kit feature, so please go ahead and plan this out.
