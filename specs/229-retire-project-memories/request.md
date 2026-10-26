# Request (the GM's words, verbatim)

## Message 1 (2026-10-26)

> It occurs to me that we probably want to turn off memories for this project. I use memories at work to keep track of things for which my own preferences differ from those of my coworkers. But those are unshared projects. This is a personal project and no one ever works on it but me. Therefore, a memory is the absolute worst place to put anything. Memories which tell us what to do in order to ensure that things happen properly should either be part of checklists, or they should be enforced by our tooling, or they should go into our project documentation. But they should not be saved as memories. Many of our memories are probably obsolete, and some of them probably are working around things which should be fixes to our tooling to ensure that we do things correctly every time without having to remember. Please do an audit of our existing memories. And see which of them can just be deleted outright and which of them should become actual changes to our documentation and which ones should be translated into fixes for our tooling.

## The audit the session answered with (summary)

29 memories: 8 delete outright (already in the repo or finished history), 14 move into documentation, 7 become
tooling, 1 (Fox secret libraries) waiting on the GM's vetting. Turn memory off with `autoMemoryEnabled: false` in
the committed `.claude/settings.json`. The per-memory table is reproduced in `spec.md` as the requirements.

## Message 2 (2026-10-26)

> I have vetted the secret libraries so they can be moved into l7r.md. After doing that, please file a feature and go ahead and make all of those changes that you have proposed, turning some of them into tooling, turning some of them into documentation, and then deleting all memories and turning off new memories for the project. Thank you.
