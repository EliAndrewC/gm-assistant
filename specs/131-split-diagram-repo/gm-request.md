# The GM's request, verbatim

**This file exists so the `spec-fidelity` reviewer grades `spec.md` against the GM's OWN WORDS**
(constitution Principle XVI). Transcription of dictated speech; do not tidy it.

Captured 2026-08-24, from the session named "AWS", while feature 130 (the CodeBuild merge gate)
was being specified. The split was the GM's idea, raised in the fourth request of that feature and
then made a feature of its own.

---

## The idea, as first raised (inside feature 130's fourth request)

> "Further, I think that we probably want to require that Anything involving the diagram skill is
> sufficiently complicated to require a spec kid feature. Changes made to other parts of this
> repository are not that complicated, but the diagram skill specifically is. Which now that I
> think about it might suggest that we should split the diagram skill out into its own repository.
> What do you think about that? It has grown into a project into its own right, and the fact that
> we are now having to do so much work in order to just distinguish the diagram skill from other
> parts of the repository with completely different rules suggests to me that it should become its
> own repo. How does that strike you?"

The session's answer (summarized, not verbatim, because it is not the GM's words): yes; feature
130 is the evidence, since half its conditions exist only to tell the diagram apart from the rest
of the repository; do it as its own spec-kit feature, before implementing 130, at a quiet point in
the hamlet work; keep the internal layout identical so the engine and the feature-127 guards do not
move; the content skills keep copies of the hooks and ritual scripts; the renders move with the
repo. Two rulings were asked for - copies vs a shared package, and whether the renders move - and
were not answered before the next request; both are recorded in the spec as the session's calls.

## The request

> "Yes, I would like to split the repos. Please write a speckit feature for the split, which we
> want to do prior to either feature 129 or 130, since those are both better implemented once we
> have moved to the separate repo. Is there a way in speckit to indicate that those two features
> depend on a specific later feature? I'm guessing this will be feature 131."

## Standing instructions from earlier the same day that bind this feature

> "you can write the SpecKit feature, you cannot actually automate it yet" (said of feature 130;
> the GM has not said it of this one, but has not said "go" either - this feature is specified and
> planned, and implementation waits for the GM's word).

> "I am definitely okay with GitHub main becoming the integration point. Presumably, this will
> involve updating our local Claude dot MD to explain how we do things after this is implemented."
