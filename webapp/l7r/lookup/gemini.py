"""The Gemini call, over plain REST, and what it cost.

Plain `urllib` rather than the `google-genai` SDK, deliberately: the bot runs on
a 512 MB Lightsail nano in about 21 MB on the standard library plus
`websockets` and `configobj`, and the SDK brings pydantic, httpx and more for
what is one POST. The webapp's backstory button keeps using the SDK.

THINKING is per model and lives in configuration, because the generations
disagree about what they accept (probed 2026-10-17, specs/218-lookup-command/
research.md): 3.5 Flash-Lite takes `thinkingLevel: minimal` and rejects a zero
budget; 3.8 Flash takes a zero budget and rejects `minimal`; 3.1 Pro only works
thinking and wants `low`. Thinking tokens bill as output, so they are counted.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'


class GeminiError(RuntimeError):
    """The call failed; the message is safe to log (it never contains the key)."""


@dataclass(frozen=True)
class Price:
    """US dollars per million tokens."""

    input: float
    cached: float
    output: float


@dataclass(frozen=True)
class Usage:
    prompt: int = 0
    cached: int = 0
    output: int = 0
    thoughts: int = 0

    def cost(self, price: Price) -> float:
        """Dollars. Cached prompt tokens bill at the cached rate, the rest at input."""
        fresh = max(self.prompt - self.cached, 0)
        return (
            fresh * price.input
            + self.cached * price.cached
            + (self.output + self.thoughts) * price.output
        ) / 1_000_000


@dataclass(frozen=True)
class Reply:
    text: str
    usage: Usage
    seconds: float
    model: str


def thinking_config(setting: str) -> dict[str, Any]:
    """`none` (send nothing), `budget0`, or a level name (`minimal`, `low`, ...)."""
    if setting in ('', 'none'):
        return {}
    if setting == 'budget0':
        return {'thinkingConfig': {'thinkingBudget': 0}}
    return {'thinkingConfig': {'thinkingLevel': setting}}


def parse_usage(meta: Mapping[str, Any]) -> Usage:
    return Usage(
        prompt=int(meta.get('promptTokenCount', 0)),
        cached=int(meta.get('cachedContentTokenCount', 0)),
        output=int(meta.get('candidatesTokenCount', 0)),
        thoughts=int(meta.get('thoughtsTokenCount', 0)),
    )


def generate(
    *,
    key: str,
    model: str,
    system: str,
    prompt: str,
    thinking: str = 'none',
    temperature: float = 0.2,
    timeout: float = 30.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
    clock: Callable[[], float] = time.monotonic,
) -> Reply:
    """One question, one answer. `system` is the stable prefix; `prompt` the variable tail."""
    body = {
        'systemInstruction': {'parts': [{'text': system}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': temperature, **thinking_config(thinking)},
    }
    request = urllib.request.Request(
        ENDPOINT.format(model=model),
        data=json.dumps(body).encode(),
        # The key goes in a header, never the URL, so it cannot end up in a log line.
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
        method='POST',
    )
    start = clock()
    try:
        with opener(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise GeminiError(f'{model}: HTTP {exc.code}') from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GeminiError(f'{model}: {type(exc).__name__}') from None
    candidates = data.get('candidates') or []
    parts = ((candidates[0] if candidates else {}).get('content') or {}).get('parts') or []
    text = ''.join(str(p.get('text', '')) for p in parts if not p.get('thought')).strip()
    if not text:
        reason = (candidates[0] if candidates else {}).get('finishReason', 'no candidates')
        raise GeminiError(f'{model}: empty reply ({reason})')
    return Reply(text, parse_usage(data.get('usageMetadata') or {}), clock() - start, model)
