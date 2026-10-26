"""The picture of a shrine (feature 228, FR-007): a deterministic prompt and one Gemini image call.

The prompt is built from the design with no LLM in between: each option's `look` (data/looks.yaml)
in wizard order, each "Something else" in the player's own words (in place of its step's look when
it is "instead"), then fixed framing. The player sees and may edit that subject text; the chosen
style's preamble (data/art.yaml) is put in front only when drawing, so changing the style never
throws away an edit.

The image call is plain REST over urllib, like `l7r.lookup.gemini`, so tests run on saved
responses rather than a mocked SDK.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from l7r.lookup.gemini import ENDPOINT, GeminiError
from l7r.shrines.catalog import DATA_DIR, Catalog
from l7r.shrines.design import Design

__all__ = ['PROMPT_CAP', 'Style', 'draw', 'image_prompt', 'load_styles', 'style_prompt']

# A hand-edited prompt is capped (the box and the request both): plenty for any design.
PROMPT_CAP = 4000

# "Show only what is listed" because the first woodblock picture of Shizu's memorial (2026-10-26)
# gained a pair of stone lanterns he had not chosen - he chose a clearing open to the sky.
FRAMING = (
    'Show the whole shrine from the approach path, in a quiet forest far from any town. It is a '
    'small rural shrine that nobody lives at: the sanctuary is a single small bay, not a temple '
    'complex. Show only what is listed above: add no lanterns, statues, gates, buildings or '
    'ornaments of your own. No people, unless the description above asks for them. Nothing modern. '
    'Any writing appears only as small, indistinct brushed characters - no legible text, '
    'captions, signature or border.'
)


@dataclass(frozen=True, slots=True)
class Style:
    key: str
    label: str
    note: str
    preamble: str


def load_styles(path: Path = DATA_DIR / 'art.yaml') -> tuple[Style, ...]:
    with path.open(encoding='utf-8') as fh:
        raw = yaml.safe_load(fh)
    return tuple(
        Style(
            str(s['key']),
            str(s['label']),
            ' '.join(str(s['note']).split()),
            ' '.join(str(s['preamble']).split()),
        )
        for s in raw['styles']
    )


def image_prompt(catalog: Catalog, design: Design) -> str:
    """The subject of the picture: what the player chose, as an image model should read it."""
    details: list[str] = []
    for category in catalog.categories:
        other = design.others.get(category.key)
        if other is None or not other.instead:
            keys = design.multi.get(category.key, ())
            if category.key in design.choices:
                keys = (design.choices[category.key],)
            for key in keys:
                option = category.option(key)
                if option is not None and option.look:
                    details.append(option.look)
        if other is not None:
            details.append(other.text)
    lines = [
        'A small shrine in the forest of Rokugan, a land like feudal Japan.',
        'What the picture shows:',
        *(f'- {d}' for d in details),
        FRAMING,
    ]
    return '\n'.join(lines)


def style_prompt(style: Style, subject: str) -> str:
    return f'{style.preamble}\n\n{subject.strip()[:PROMPT_CAP]}'


def draw(
    *,
    key: str,
    model: str,
    prompt: str,
    timeout: float = 120.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[bytes, str]:
    """One picture, as (bytes, mime type). Raises GeminiError (never carrying the key)."""
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'responseModalities': ['IMAGE'],
            'imageConfig': {'aspectRatio': '4:3'},
        },
    }
    request = urllib.request.Request(
        ENDPOINT.format(model=model),
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
        method='POST',
    )
    try:
        with opener(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise GeminiError(f'{model}: HTTP {exc.code}') from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GeminiError(f'{model}: {type(exc).__name__}') from None
    candidates = data.get('candidates') or []
    first = candidates[0] if candidates else {}
    for part in (first.get('content') or {}).get('parts') or []:
        blob = part.get('inlineData') or {}
        if blob.get('data'):
            return base64.b64decode(blob['data']), str(blob.get('mimeType') or 'image/png')
    raise GeminiError(f'{model}: no image ({first.get("finishReason", "no candidates")})')
