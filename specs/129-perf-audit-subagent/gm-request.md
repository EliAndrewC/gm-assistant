# The GM's request, verbatim

Captured BEFORE `spec.md` was written, so the spec can be graded against the GM's own words rather
than against the author's summary of them (constitution XVI). Nothing here is edited - not the
punctuation, not the dictation artifacts, not the British spellings if any. The house-style guard
exempts this file for exactly that reason.

## 2026-08-24, setting the thresholds this feature replaces

> Now that I think about it, can we make a quick change to those numbers? I think I want to diagnose
> at any increase whatsoever, even just an increase of one percent. And then I think I want five
> percent to trigger a subagent check where a subagent is doing an independent verification and
> validation that this increase is necessary and commensurate to the increase in functionaltiy and
> that there's no good way around this. I would like our tooling around running the tests to be run-in
> a way that automatically generates a profile so that that profile can be handed to the subagent. and
> then the subagent can look at the before and after and have its independent verification and
> validation based on actual data. And then if the subagent agrees that the new functionality
> legitimately genuinely does take up enough complexity and computation to justify the increase, then
> we flag it and allow it to go forward. I don't know if there is a way for our tooling to only accept
> this kind of flagging from the subagent rather than from the main session. But if this is possible,
> then I would like that. If it is not possible to strictly enforce that, then I would still like there
> to be some sort of prompting that makes it unlikely that we will bypass this flawlessly. For example,
> if the subagent is expected to run some make command, then the make command should  actually prompt
> you by saying, are you this particular subagent and not the main session. If you are the main session,
> then you should not continue. You should exit now by taking this escape hatch and then have the
> subagent run this command in order to flag this performance increase as being audited and found to be
> acceptable. Does that make sense? can you build that into Our tooling. Is that complicated enough to
> need its own feature? Or do you think that that is simple enough that you can just do it? Either way
> is fine. I don't mind it being a spec kit feature. but this is much smaller than the previous spec kit
> feature. So I figured I would ask. Just let me know what you think. Thanks.

## 2026-08-24, on profiling cost and where profiles are stored

> How much does cProfile inflate our runtime? The reason why I ask is that if the tests take a long
> time to run and then anytime we hit an increase, we need to rerun them, then that is going to take
> more time than it would have taken to just always run with cProfile. Does that make sense? Now if
> profiling really does make it take, like, twice as long or whatever, then, obviously, that's bad. But
> if it increases it by something like twenty percent, then it seems like the cost of having to rerun it
> in order to get the profile numbers is worse than just always having profiling on. This is especially
> true if there is a lot of random noise. But even if there is not, we are frequently making additions
> in which we add new things to the map. My presumption is that any new thing that we add to the map
> will increase the amount of time that we are taking because we are adding new code. We are also adding
> new unit tests for that new code. I would expect that most things would fall underneath a five percent
> increase, but it would still be good to look at this with actual profiling numbers. Now the profiling
> itself may take up so much space that we don't want to check it into source control, or maybe we
> figure out a way to do this efficiently. We can check-in zipped versions, or maybe we have a second
> repository of these. that we push to? in order to keep this repository from growing too much? that one
> seems like it might be good. because I'm sensitive to how big this repository can get, but a second
> repository of profile logs might just be okay. I'm not sure what the idiomatic way to do this is. What
> do you think? about all of this, I mean. Again, we're not implementing anything yet. We're just trying
> to settle on what the best feature design for the one twenty nine spec is prior to beginning work on
> it.

## 2026-08-24, the instruction that scoped this spec

> Do not start work on the spec. But, yes, please do hold all of this into the spec so that it will be
> present when we begin work. And, yes, that does include some measurements on the noise floor. since we
> can take those measurements prior to actually beginning the work and then already have that
> information built into the spec itself.

## 2026-08-24, THE RULING THAT SUPERSEDES THE BANDS ABOVE

Given in answer to the spec's two routed questions. It settles the ceiling question AND revises all
three bands, so it outranks the band design in the earlier request.

> Yes it is correct that there is no ceiling for allowing it to go forward so longer as the subagent
> reviewer agrees... but I think on refelction I want the three thesholds to be:
> - any increase: explanation, with a subagent reviewer confirming
> - >5%: more advanced analysis and higher level of justification required
> - >10%: I must personally sign off on this before it is committed back to main

**Two things changed from the earlier request, and the spec must follow the LATER words:**

1. **A subagent is now involved at ANY increase**, not only above 5%. The earlier request put the
   subagent check at the 5% trigger; this puts a confirming reviewer on every increase, and makes 5%
   the point where the ANALYSIS and the JUSTIFICATION BAR escalate rather than the point where review
   begins.
2. **The 10% row is now the GM's own instruction**, not the author's retained caution - and it is
   sharper than what it replaces: personal sign-off, and specifically **before it is committed back to
   main**, which names the push as the enforcement point rather than the gate.

## THE AUTHOR'S CLAIMS - not the GM's words, and the reviewer must ATTACK them

The following are the SESSION'S assertions, made in conversation and carried into the spec. They are
recorded separately so a fidelity reviewer does not mistake them for things the GM asked for. Each is
a claim to be verified or refuted, not a requirement.

1. **"cProfile is ~3x, so always-on is out."** Measured this session at +196% on the check battery and
   +242% on a pure geometry loop. VERIFY the measurement method is fair - in particular that the
   check battery is representative of what `make perf` actually times, which is generation, not
   checking.
2. **"Break-even is about one trip in three runs."** Arithmetic from a ~5 min baseline run, a ~3x
   profiled run, and two profiled runs needed per trip. VERIFY the arithmetic and the inputs.
3. **"A sampling profiler makes always-on free, and that is what the GM actually wants."** The GM did
   not ask for a sampling profiler; they asked for profiles to be generated automatically. The author
   proposed sampling as the way to satisfy that cheaply. CHECK whether this is a faithful reading or
   a substitution.
4. **"A second repository is not warranted."** The GM raised it and leaned toward it ("that one seems
   like it might be good"). The author argued against it on measured size grounds. This is the
   clearest place where the spec may be contradicting a GM preference; the reviewer should press hard
   on whether the argument actually answers the GM's stated concern (repository growth) or merely
   asserts that the numbers are small.
5. **"The >0% diagnose band should have a cheap auto-populated artifact."** The GM asked for diagnosis
   at any increase; the author added a claim about how burdensome it may be. CHECK that this does not
   quietly weaken the requirement.
