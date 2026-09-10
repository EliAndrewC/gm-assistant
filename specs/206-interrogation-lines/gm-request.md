# GM request, verbatim (2026-09-10)

Two messages in the "Discord" session. The first is the proposal; the second accepts the session's
judgment calls on it. Nothing here has been edited (voice-dictated "role" for "roll" and "rules"
for "rolls" included).

## Message 1

> Thanks.  I've also just realized that interrogation rolls should be handled specially, because
> contested interrogation rolls are never displayed; if someone knows how high the NPC rolled on
> sincerity, then they would know whether the "doesn't seem to be holding anything back" result
> represents truthfulness or if that is simply because the interrogator didn't roll high enough.
>
> So one approach is to simply not record the interrogation role, but I think it is useful to
> record those. But because an interrogation role is always contested, but never paired with the
> opposing sincerity role, which I will simply keep to myself, then that means that we can probably
> just display it as is. However, there are a few other subtleties about interrogation, which
> probably deserve some special handling as well. First, there are two sets of conditional bonuses
> that someone can get to their sincerity role, both of which we might potentially note on the
> interrogation role. The first one is whether or not the interrogator is "grilling" the subject by
> which I mean adversarily putting them to difficult questions and not letting them control the flow
> of the conversation. players always know whether they are grilling the person. Therefore, this is
> not secret. Therefore, we could put "(grilling)" as a parenthetical footnote.
>
> Interrogation roles should probably be grouped by "lines of questioning". When a topic changes,
> then a new interrogation role is made, which means that a single character might make multiple
> interrogation roles. Multiple characters may also roll interrogation on the same line of
> questioning. Therefore, we should probably treat etiquette rules and interrogation rules similarly
> in the sense that we would group together interrogation rules for the same line of questioning,
> and Display a new interrogation role for other lines of questioning. Because interrogation is
> always world contested, we should always show the exact interrogation roll. Additionally, because
> we are showing the interrogation role but not showing the opponent's sincerity role, then we
> should show the interrogation skill attached to the role. For example, if someone with two ranks
> in their interrogation skill rolls a thirty seven, then we would show that as `37@2`.
>
> because we annotate interrogation roles, but then sometimes need to group them together, then we
> should have a menu such that when I am selecting interrogation roles, I can indicate whether a
> role by a second interrogator is part of the same topic of conversation or a new topic. This means
> that I might expect to end up with results uploaded to Obsidian Portal which basically look like
> this:
>
> interrogation (grilling): 37@2 (Jimen) / 24@1 Moriko - what Fumitake ordered his escorts to do
>
> interrogation: 25@2 (Jimen) - what Fumitake thinks of Tsuruchi
>
> How does that sound?

## The session's reply (the judgment calls the GM accepted)

The session answered that the design was sound and that the rules text (`rules/02-skills.md`,
Interrogation, line 218) settles the second conditional bonus the GM's message left open: the NPC
gets two free raises when telling a lie they believe cannot be disproven, which is secret by
construction and so never appears on the line. Situational free raises to the interrogator (a
scared or guilty subject) leak NPC state the same way, so the line shows the raw player roll with
no bonuses on either side, and the `c` path never offers a contest on an interrogation roll.

Grouping by line of questioning matches the rules ("rolled once for each line of questioning").
The menu asks, for each interrogation roll after the first, whether it belongs to an existing line
or starts a new one, and asks `grilling?` once per line rather than per roller. Interrogation rolls
stay held until annotated, unlike Etiquette, because the note is the topic.

Three calls, all cheap to change later:

- One shape for the names: drop the parentheses, number-first throughout, parallel to the open
  line - `interrogation (grilling): 37@2 Jimen / 24@1 Moriko - what Fumitake ordered his escorts
  to do`.
- Highest roll first within a line, the rule Etiquette already uses.
- Rank comes from the character-sheet app when it recorded the roll; a hand-typed roll has no
  rank, so the menu asks for it on interrogation rolls only, and a blank writes `37` with no `@`.

The GM's rolled sincerity total is not written anywhere. The reply added that if the GM later
wants it kept for their own reference, GM-only notes would be the obvious place, "but I would not
add that unless you ask" - an offer of a later addition, which the GM's reply did not take up.

The reply closed by saying this was feature-sized work for spec-kit, to be run end to end with the
three calls above as the defaults, on the GM's go.

## Message 2

> I like your judgment calls, so yes please implement that, thanks.
