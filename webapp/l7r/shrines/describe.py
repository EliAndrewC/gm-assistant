"""A written description of a shrine (feature 228, FR-006): a short brief plus the design, sent to
a cheap Gemini text model.

Unlike the NPC backstory (which needs the whole setting corpus and a Pro model), the design already
says everything the description may say, so the brief is a few hundred words and the model is the
cheapest Flash-Lite. Measured cost per description is in specs/228-shrine-wiki-art/plan.md.
"""

from __future__ import annotations

from l7r.shrines.catalog import Catalog, Category, Option
from l7r.shrines.design import Design

__all__ = ['BRIEF', 'design_text']

BRIEF = """\
You write short descriptions of shrines for a tabletop roleplaying campaign set in Rokugan, a land
like feudal Japan. A player has designed a small, remote shrine in the forest, one that nobody
lives at: those who honor it come to sweep it, leave offerings and pray. You are given every choice
the player made, step by step, and sometimes their own words for a step ("something else").

Write two or three short paragraphs describing the shrine as a visitor would find it: the way in,
what they see, hear and smell, what stands where, and how the place feels. Use every choice. Never
contradict one, and never add a major feature the player did not choose (no extra buildings, no
priests or keepers living there, no crowds). Where the player's own words say "instead", they
replace that step; where they say "as well", they add to it. Small sensory details that follow from
the choices are welcome.

Style: plain, concrete, unhurried prose in American English. Hyphens only, never em or en dashes.
No prices or costs, no game mechanics, no headings, no lists, no title, nothing before or after
the description. Japanese terms only where the choices use them. Present tense.
"""


def _field(obj: Category | Option, wording: str, name: str) -> str:
    """`name` (label, text, prompt) in the wording the player saw."""
    return str(obj.wording.get(wording, {}).get(name, getattr(obj, name)))


def design_text(catalog: Catalog, design: Design) -> str:
    """The design as the model reads it: the name, then each step in play with its pick(s) and
    the player's own words, in the wording the player saw (a memorial's or a kami's)."""
    w = design.wording
    lines = [f'Name of the shrine: {design.text.get("shrine_name", "")}']
    for category in catalog.categories:
        if category.key in design.inactive:
            continue
        keys = design.multi.get(category.key, ())
        if category.key in design.choices:
            keys = (design.choices[category.key],)
        other = design.others.get(category.key)
        if not keys and other is None:
            continue
        lines.append(f'\n{_field(category, w, "label")} ({_field(category, w, "prompt")})')
        for key in keys:
            option = category.option(key)
            if option is not None:
                lines.append(f'- {_field(option, w, "label")}: {_field(option, w, "text")}')
        if other is not None:
            how = 'instead of the listed choices' if other.instead else 'as well'
            lines.append(f"- The player's own words, {how}: {other.text}")
    return '\n'.join(lines)
