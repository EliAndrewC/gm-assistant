"""
Shared configuration for the synthesis prompt bakeoff.

This is a temporary, local-only evaluation harness for comparing how much (and
what kind of) setting context a backstory-synthesis prompt should carry. It is
deliberately kept out of the shipped l7r webapp.
"""

import os

#: Where the GM's canonical setting notes are bind-mounted. Override with the
#: L7R_SETTING_DIR env var if running outside the standard container.
SETTING_DIR = os.environ.get('L7R_SETTING_DIR', '/host-l7r-repo/setting')
L7R_MD = os.path.join(SETTING_DIR, 'l7r.md')
BUDGETS_MD = os.path.join(SETTING_DIR, 'budgets.md')

#: Bakeoff package dir and its data/output locations.
HERE = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(HERE, 'data')
CANDIDATES_PATH = os.path.join(DATA_DIR, 'candidates.jsonl')
TASKS_PATH = os.path.join(DATA_DIR, 'tasks.jsonl')
VOTES_PATH = os.path.join(DATA_DIR, 'votes.jsonl')
CHARACTERS_PATH = os.path.join(HERE, 'characters.json')

#: The active comparison: does the per-clan flavor summary help on top of the
#: GM's materialist "The Great Clans" framing, or is the framing alone enough?
#: BOTH arms carry the blurb (single-sourced from l7r.md); only `flavor` adds
#: flavor_clans.md on top of it. See briefs.build_tier.
TIERS = ['blurb', 'flavor']

#: The earlier context-amount sweep - t0 (shipped brief) up to t3 (whole
#: canonical corpus). Preserved so it can be re-run later by swapping it into
#: TIERS; build_tier still understands every id here. See briefs.py.
CONTEXT_TIERS = ['t0', 't1', 't2', 't3']

#: The model to generate with. The Pro-vs-Flash question was resolved in favor of
#: Pro on the smoke run: gemini-3.5-flash drifted low-honor characters toward
#: active villainy (breaking the "as good as their incentives" honor model),
#: while gemini-3.1-pro-preview held it. Flash kept here commented out in case it
#: is worth revisiting.
MODELS = ['gemini-3.1-pro-preview']
# MODELS = ['gemini-3.1-pro-preview', 'gemini-3.5-flash']

#: How many independent samples per (character, tier, model) cell. Multiple
#: samples average out the large run-to-run variance so a vote rates the prompt,
#: not one lucky draw.
SAMPLES = 3
