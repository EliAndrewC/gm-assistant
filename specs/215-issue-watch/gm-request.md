# GM request - feature 215

Received 2026-10-03, in the gm-assistant session "Discord repl", after feature 214 landed.
Reproduced verbatim, dictation artifacts included (a trailing "Uh," / "Um," is a dictation
artifact, not an unfinished message - user-level mistranscription table). This is the text the
`spec-fidelity` review grades [spec.md](spec.md) against.

---

## Message 1 (the idea)

Gotcha. Okay. Um, so let's say that we did want to monitor a GitLab work item. Um, I see what you're saying about like it wastes tokens and stuff to tell it to pull every 15 minutes or whatever, but is that something where you could have like a script running in the background? like we do have a GitLab skill and we also have a skill for interacting with our tickets. So I wonder if there could just be a script in one of those skills where when we know that we are working an item, then we automatically run that script in the background in a way that the script will pull for new comments or for edits or whatever on the item and then notify us at the appropriate time kind of at the stage in the workflow where it makes sense like we could even have hooks in place to make sure that we receive this message from our script that's running in the background and don't just ignore it but also the hook can make sure that we are not interrupted like that we do this at an appropriate time or whatever I don't know Does that sound like it is a good approach?

## The session's answer to message 1 (summarized)

Sound design: a token-free watcher writes new comments and edits to an inbox; a hook on the GM's
next prompt delivers them as context; an end-of-turn (`Stop`) hook blocks once while unread items
exist; the watcher must not wake the session by exiting; injected comments are framed as data from
someone else, not instructions; deliveries are trimmed.

## Message 2 (the request)

Hmm, actually, yeah, I think I would probably like to try building that here, since, as you say, GitHub versus GitLab. are going to be pretty much the same, so really just the API calls are the only things that would differ. Um, so how would we do that? Like, I think I actually would like to use this work, this task, as an example of doing that. So like we could use GitHub issues for this, where there's a GitHub issue that both you and the character sheet could post to. Um, I actually don't remember whether you use the same GitHub personal access token or not. If you use different ones, then I can update their access in order to make sure that they are both able to post to the issues. Or does GitHub call them issues? What are they even called for GitHub? Either way, I can update the permissions on those personal access tokens to make sure that they can do what we need to do. And then we could basically build this process into our hooks and scripts for the GM assistant repo and the character sheet repo. I don't think we need to do this with the diagram repo or any of our other repositories. So it's really just these two for now that would be doing this. I don't know how that affects the design, but I guess it does kind of mean that whatever we do for our hooks must be shared in some way, but also must not be firing and not be doing stuff for other projects, even if they are shared hooks. What do you think makes sense there? Uh,

## The session's answer to message 2 (summarized - what message 3 confirms)

`~/.claude` is a host mount shared by every container, and `memwatch-hook.sh` there is a working
exemplar (shared folder -> per-session delivery as context; an async `Stop` hook that wakes an idle
session). Proposal: ONE copy of the code, developed and tested here, installed into the shared
`~/.claude/hooks`; the OPT-IN is a small config file in each participating repo; the hooks exit at
once unless the current repo has that file and the session has an active watch. Separate tokens:
ours can write issues on gm-assistant and is refused on character-sheet; the sheet's is in its
`.env`, untested. The GM grants Issues read/write on both repos to both tokens. Hidden per-agent
markers so each side skips its own comments; the live test is the feature 214 handoff.

## Message 3

Also, I've noticed that my voice-to-text puts a trailing "Uh," at the end of a lot of my messages, which I'm not really sure what that is because I don't think I am trailing with an uh, but can you maybe add something on the Claude.md voice transcription table that explains that a trailing uh such as that should just always be ignored. It does not mean that my message was incomplete.
I can confirm that the hooks directory is shared between containers for what it's worth. I mean, you can check the launch container script, but the launch container script just volumes in my host dot claud directory and such.

## Message 4 (2026-10-04, after the first issue was opened)

I would like to be able to just say something like `please implement https://github.com/EliAndrewC/character-sheet/issues/2` have have its instructions know what to od about it.  Can you make sure the CLAUDE.md is good enough to instruct it what to do in cases like this?  Where working on an issue means you're watching it until it's done?
