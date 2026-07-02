"""
Backstory synthesis for NPCs using Google Gemini's text-generation API.

This is the text-mode twin of ``art.py``: where ``art`` turns a character's
attributes into a portrait, this module turns the same attributes into a short
prose "gestalt" - 1-3 paragraphs that reconcile the mechanically-generated
traits (clan, rank, honor, tags, advantages, disadvantages) into a single
coherent person.

The model id is configurable via ``[gemini] text_model`` so future model
migrations are a config edit rather than a code change, exactly as
``art.DEFAULT_IMAGE_MODEL`` works for portraits. The setting context is kept in
``synthesis_brief.md`` (a curated slice of the GM's l7r.md / budgets.md notes)
so the lore can be tuned without touching code.

Run the prompt-iteration harness against a few sample characters with:

    python3 -c "import l7r; from chargen import synthesis; synthesis._main()"

(``l7r`` is imported first only to dodge a pre-existing circular import in the
chargen package's __init__; the app itself launches the same way, via
``cherryd --import l7r``.)
"""

import os

from google import genai

from chargen import config

#: Gemini text model used when ``[gemini] text_model`` is unset. A Pro-tier
#: model is the default because synthesizing a coherent person out of traits
#: that are sometimes in tension is a reasoning task, not a quick rewrite. This
#: matches the gemini-3.1 family the portrait pipeline targets
#: (art.DEFAULT_IMAGE_MODEL is 'gemini-3.1-flash-image').
DEFAULT_TEXT_MODEL = 'gemini-3.1-pro-preview'

#: Curated setting context shipped alongside this module.
_BRIEF_PATH = os.path.join(os.path.dirname(__file__), 'synthesis_brief.md')

#: The instruction wrapped around the brief and the character on every call.
#: Kept here (not in the brief) so the lore and the task framing can be tuned
#: independently.
INSTRUCTIONS = """\
You are helping a game master flesh out a single non-player character for their
Legend of the Five Rings tabletop campaign, set in the "L7R" version of Rokugan
described in the SETTING BRIEF below.

The character's mechanical details were generated semi-randomly: clan, family,
lineage, school, rank, recognition, experience, honor, and a list of traits
(advantages, disadvantages, and physical or behavioral descriptions). Your job
is to synthesize those details into a believable individual.

Write 1 to 3 short paragraphs of prose that:

- Treat the traits as facets of one coherent person, not a checklist. Weave them
  together; do NOT restate them as a list or define them one by one.
- Actively reconcile any tensions between the traits. If a humble samurai has low
  honor, or a devout one is religiously unorthodox, decide what specific story
  makes both true at once, and commit to it.
- Commit to concrete, plausible specifics - a particular belief, habit, grudge,
  fear, relationship, or episode from their past - rather than hedging or staying
  abstract. Invented detail is welcome as long as it fits the brief and the
  character's generated details.
- When you place an event in the character's past, prefer a specific,
  setting-grounded time - a named festival, month, or season from the Rokugani
  calendar - over a vague reference like "a few years ago," wherever the brief
  gives you the detail to do so and it fits naturally. Specificity is the soul of
  a backstory; do not invent dates that contradict the brief.
- Stay grounded and mundane by default. The supernatural is real but rare and
  almost always ambiguous; do not hand this character magic, a curse, or a
  literal supernatural event unless their own details clearly point that way, and
  even then keep it uncertain.
- Never contradict the SETTING BRIEF or the character's own generated details.
- The character's stated facts are authoritative - their one-line summary, tags,
  posting, clan, family, school, rank, and recognition. Do not override them or
  invent around them. In particular, RANK is a level of peerage, not an office:
  the setting's baseline "rank N is typically held by such-and-such official" is a
  default, not a rule. A character can hold a high rank through a relative's
  standing (the family-rank rule) while holding no office at all. If the character
  is unposted, or its summary names a specific role, keep that exactly - never
  promote them into the office their rank would typically imply.

Match the GM's register: laconic, matter-of-fact, concrete. No flowery or
purple prose, no marketing tone. Use "domain" not "demesne"; use
"humans"/"inhabitants"/"population" rather than "people" for generic
demographics ("people" means samurai specifically). Use hyphens only - never
em-dashes or en-dashes. Output only the prose paragraphs, with no heading,
preamble, or bullet points.\
"""


def _get_client():
    """Get a configured Gemini API client (mirrors art._get_client)."""
    api_key = config.get('gemini', {}).get('api_key', '')
    if not api_key:
        raise ValueError(
            'Gemini API key not configured. Add api_key to [gemini] in '
            'development-secrets.ini. Get your API key from '
            'https://aistudio.google.com/app/apikey'
        )
    return genai.Client(api_key=api_key)


def load_brief() -> str:
    """Return the full-corpus setting brief that grounds every synthesis.

    Production uses the full canonical corpus (the prompt a blind evaluation
    selected). Assembly lives in the compliant ``chargen.brief`` module; the
    shipped ``synthesis_brief.md`` here is just the design-brief layer it starts
    from.
    """
    from chargen import brief

    return brief.build_full_brief()


def format_character(character: dict) -> str:
    """
    Render a character dict into the plain-text block the LLM reads.

    This deliberately mirrors what the chargen UI already shows: the ``public``
    and ``private`` rendered descriptions (from public_info.txt / private_info.txt
    via Character.to_dict), plus the name-meaning explanation when present. When
    those rendered fields are absent (e.g. a hand-built sample), it falls back to
    assembling the same information from the raw attributes.
    """
    name = character.get('full_name') or character.get('personal_name') or 'Unknown'
    lines = [name]

    name_meaning = character.get('name_meaning', '')
    if name_meaning:
        lines.append(f'Name meaning: {name_meaning}')

    # The GM's one-line description names the character's role/posting and is
    # authoritative - surface it prominently so the model honors it.
    summary = character.get('summary', '').strip()
    if summary:
        lines.append(f'In brief: {summary}')

    # The form's tags (clan, role, location, etc.) - a comma string from the UI,
    # or a list from to_dict()/a sample. Surfaced in every path.
    tags = character.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    if tags:
        lines.append('Tags: ' + ', '.join(tags))

    # Prefer the already-rendered public/private blocks the app produces.
    public = character.get('public', '').strip()
    private = character.get('private', '').strip()
    if public or private:
        if public:
            lines += ['', public]
        if private:
            lines += ['', private]
        return '\n'.join(lines).strip()

    # Fallback: build the same shape from raw fields.
    gender = character.get('gender', '')
    school = character.get('school', '').replace('_', ' ')
    descriptor = ' '.join(filter(None, [gender, school])) or gender
    if descriptor:
        lines += ['', descriptor]

    standing = []
    if character.get('rank') is not None:
        standing.append(f'Rank: {character["rank"]}')
    if character.get('recognition') is not None:
        standing.append(f'Recognition: {character["recognition"]}')
    if standing:
        lines += [''] + standing

    meta = []
    if character.get('xp') is not None:
        meta.append(f'XP: {character["xp"]}')
    if character.get('honor') is not None:
        meta.append(f'Honor: {character["honor"]}')
    if meta:
        lines += [''] + meta

    traits = character.get('traits') or []
    if traits:
        lines += ['', '\n'.join(traits)]

    return '\n'.join(lines).strip()


def build_prompt(character: dict, brief: str = '', extra_notes: str = '') -> str:
    """
    Assemble the full prompt sent to the model.

    ``extra_notes`` is freeform steering the GM types before (re)synthesizing -
    the text equivalent of editing the art prompt before regenerating a portrait.
    It is given high priority so the GM can push the result in a direction.
    """
    brief = brief or load_brief()
    sections = [
        INSTRUCTIONS,
        '# SETTING BRIEF\n\n' + brief.strip(),
        '# CHARACTER\n\n' + format_character(character),
    ]
    if extra_notes and extra_notes.strip():
        sections.append(
            '# GM STEERING NOTES\n\n'
            'The GM has added the following guidance for this synthesis. Follow '
            'it closely where it applies, overriding the defaults above if they '
            'conflict (but never contradicting the SETTING BRIEF or the '
            "character's generated details):\n\n" + extra_notes.strip()
        )
    return '\n\n'.join(sections)


def synthesize(character: dict, extra_notes: str = '', brief: str = '', model: str = '') -> str:
    """
    Generate a 1-3 paragraph backstory gestalt for the given character.

    Args:
        character: a character dict (as produced by Character.to_dict, or a
            compatible hand-built dict).
        extra_notes: optional freeform GM steering text.
        brief: optional setting brief to use instead of the production
            full-corpus brief (mainly useful in tests).
        model: optional model id override; falls back to the configured
            ``[gemini] text_model`` and then DEFAULT_TEXT_MODEL.

    Returns:
        The synthesized prose.
    """
    client = _get_client()
    model = model or config.get('gemini', {}).get('text_model', '') or DEFAULT_TEXT_MODEL
    prompt = build_prompt(character, brief=brief, extra_notes=extra_notes)
    response = client.models.generate_content(model=model, contents=prompt)
    return (response.text or '').strip()


# Sample characters for prompt iteration. These mirror the shape of
# Character.to_dict() closely enough to exercise format_character / build_prompt.
# The first is the GM's own worked example (Tsuruchi Hideki).
SAMPLES = [
    {
        'full_name': 'Tsuruchi Hideki',
        'name_meaning': (
            'Hideki means "excellent tree" or "splendid wood", suggesting a '
            'strong foundation - a steadfast, dependable person drawn to roles '
            'where they provide support and stability.'
        ),
        'gender': 'male',
        'school': 'peasantborn',
        'clan': 'wasp',
        'family': 'tsuruchi',
        'lineage': 'ami',
        'tags': ['Wasp Clan', 'Ami Lineage', 'Escort', 'Shiro Reiji'],
        'rank': 5.0,
        'recognition': 6.0,
        'xp': 115,
        'honor': 1,
        'traits': [
            'Bad Reputation',
            'Humble',
            'Peasantborn',
            'bearded',
            'boisterous',
            'frayed seams and hems',
            'religiously unorthodox',
            'unusual haircut',
        ],
    },
    {
        'full_name': 'Doji Ayako',
        'name_meaning': 'Ayako means "colorful child" or "child of design".',
        'gender': 'female',
        'school': 'courtier',
        'clan': 'crane',
        'family': 'doji',
        'tags': ['Crane Clan', 'Doji Family', 'Courtier', 'Kyuden Doji'],
        'rank': 7.5,
        'recognition': 9.0,
        'xp': 265,
        'honor': 4,
        'traits': [
            'Famous',
            'Proud',
            'Idealistic',
            'elegant',
            'sharp-tongued',
            'fine makeup',
        ],
    },
    {
        'full_name': 'Hida Tetsuo',
        'name_meaning': 'Tetsuo means "philosophical man" or "wise hero".',
        'gender': 'male',
        'school': 'hida_bushi',
        'clan': 'crab',
        'family': 'hida',
        'tags': ['Crab Clan', 'Hida Family', 'Wall Veteran', 'Kyuden Hida'],
        'rank': 4.0,
        'recognition': 3.0,
        'xp': 240,
        'honor': 2,
        'traits': [
            'Battle-Scarred',
            'Grim',
            'Superstitious',
            'missing an eye',
            'heavy drinker',
            'touched by the supernatural',
        ],
    },
    {
        'full_name': 'Kitsune',
        'name_meaning': '',
        'gender': 'female',
        'school': '',
        'tags': ['Order of Jurojin'],
        'rank': 5,
        'recognition': 6.0,
        'xp': 190,
        'honor': 3,
        'traits': [
            'Country Monk',
            'eccentric',
            'herbalist',
            'speaks to animals',
        ],
    },
]


def _main() -> None:
    brief = load_brief()
    approx_brief_tokens = len(brief) // 4
    print(f'Loaded brief: {len(brief)} chars (~{approx_brief_tokens} tokens)')
    model = config.get('gemini', {}).get('text_model', '') or DEFAULT_TEXT_MODEL
    print(f'Model: {model}\n')

    for character in SAMPLES:
        print('=' * 78)
        print(format_character(character))
        print('-' * 78)
        try:
            print(synthesize(character))
        except Exception as exc:  # noqa: BLE001 - harness should keep going
            print(f'[error: {exc}]')
        print()


if __name__ == '__main__':
    _main()
