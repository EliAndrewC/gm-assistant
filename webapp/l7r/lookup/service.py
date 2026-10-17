"""One question in, one private reply out: the whole lookup, with every boundary injectable.

`Lookup.answer` is what the Discord responder calls and what the evaluation
runner calls, so the two can never drift: the evaluation measures the exact path
a player's question takes, link post-processing included.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from configobj import ConfigObj

from l7r.lookup import campaign, gemini, glossary, links
from l7r.lookup.ledger import Ledger
from l7r.lookup.profiles import Profile, Profiles, from_json

WEBAPP = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent / 'data'

#: Discord's message limit is 2,000 characters; a reply should never come near it
#: given the five-line rule, but a runaway answer is cut at a line, not mid-word.
LIMIT = 1900

NOT_CONFIGURED = (
    'The lookup is not set up yet (no Gemini key on the bot). The GM knows how to fix it.'
)
CEILING = (
    "Today's lookup budget is spent, so I can't ask the model again until tomorrow. "
    'Sorry - the GM can raise the limit.'
)
FAILED = (
    'Sorry, the lookup failed just now (the model did not answer). Please try again in a moment.'
)


@dataclass(frozen=True)
class Settings:
    model: str
    thinking: str
    price: gemini.Price
    ceiling: float
    timeout: float
    groups: tuple[str, ...]
    key: str = field(default='', repr=False)

    def for_model(self, model: str, defaults: ConfigObj) -> Settings:
        """These settings with another model's thinking setting and price (evaluation)."""
        return Settings(
            model=model,
            thinking=str(defaults['lookup_models'].get(model, 'none')),
            price=_price(defaults, model),
            ceiling=self.ceiling,
            timeout=self.timeout,
            groups=self.groups,
            key=self.key,
        )


def _price(defaults: ConfigObj, model: str) -> gemini.Price:
    raw = defaults['lookup_prices'].get(model)
    if raw is None:
        raise KeyError(f'no [lookup_prices] entry for {model}; add "input, cached, output"')
    values = [float(v) for v in (raw if isinstance(raw, list) else str(raw).split(','))]
    return gemini.Price(*values)


def _list(value: Any) -> tuple[str, ...]:
    items = value if isinstance(value, list) else str(value).split(',')
    return tuple(str(v).strip() for v in items if str(v).strip())


def load_settings(
    defaults_path: Path = WEBAPP / 'development-defaults.ini',
    secrets_path: Path = WEBAPP / 'development-secrets.ini',
) -> tuple[Settings, ConfigObj]:
    """Settings from the checked-in defaults and the gitignored secrets.

    ConfigObj, not configparser: the secrets file writes keys in quotes, which
    ConfigObj strips and configparser keeps (an `API_KEY_INVALID` with a key that
    is perfectly fine, measured 2026-10-17). The key is `[lookup] gemini_api_key`
    ONLY - never `[gemini] api_key`, which also pays for portraits and backstories
    and must not reach the internet-facing box (see scripts/deploy_mention_bot.sh)."""
    defaults = ConfigObj(str(defaults_path), encoding='utf-8')
    secrets = ConfigObj(str(secrets_path), encoding='utf-8') if secrets_path.exists() else {}
    section = defaults['lookup']
    model = str(section['model'])
    settings = Settings(
        model=model,
        thinking=str(defaults['lookup_models'].get(model, 'none')),
        price=_price(defaults, model),
        ceiling=float(section['daily_ceiling_usd']),
        timeout=float(section['timeout_seconds']),
        groups=_list(section['campaign_groups']),
        key=str((secrets.get('lookup') or {}).get('gemini_api_key', '')).strip(),
    )
    return settings, defaults


@dataclass(frozen=True)
class Answer:
    text: str
    ok: bool
    usage: gemini.Usage = gemini.Usage()
    cost: float = 0.0
    seconds: float = 0.0
    dropped: tuple[str, ...] = ()


def hyphenate(text: str) -> str:
    """The project's house style (hyphens only) applied to the model's prose.

    Gemini writes em and en dashes freely; a spaced em dash becomes " - ", a bare
    one or an en dash (number ranges) becomes "-"."""
    em, en = chr(0x2014), chr(0x2013)
    return text.replace(f' {em} ', ' - ').replace(em, ' - ').replace(en, '-')


def trim(text: str, limit: int = LIMIT) -> str:
    if len(text) <= limit:
        return text
    cut = text.rfind('\n', 0, limit)
    return text[: cut if cut > 0 else limit].rstrip()


class Lookup:
    def __init__(
        self,
        settings: Settings,
        entries: list[glossary.Entry],
        people: list[links.Person],
        profiles: Profiles,
        ledger: Ledger | None = None,
        *,
        generate: Callable[..., gemini.Reply] = gemini.generate,
    ) -> None:
        self.settings = settings
        self.people = people
        self.profiles = profiles
        self.ledger = ledger
        self._generate = generate
        self._system = campaign.system(glossary.render(entries))
        self._allowed = glossary.links(entries) | {p.url for p in people}

    @property
    def system(self) -> str:
        return self._system

    def answer(self, question: str, discord_id: str = '', asker: str = '') -> Answer:
        """The private reply to `question` from Discord account `discord_id`."""
        if not self.settings.key:
            return Answer(NOT_CONFIGURED, ok=False)
        if self.ledger is not None and not self.ledger.allows():
            return Answer(CEILING, ok=False)
        mine: list[Profile] = self.profiles.for_discord(discord_id) if discord_id else []
        try:
            reply = self._generate(
                key=self.settings.key,
                model=self.settings.model,
                system=self._system,
                prompt=campaign.prompt(question, mine),
                thinking=self.settings.thinking,
                timeout=self.settings.timeout,
            )
        except gemini.GeminiError as exc:
            if self.ledger is not None:
                self.ledger.log({'asker': asker, 'question': question, 'error': str(exc)})
            return Answer(FAILED, ok=False)
        text, dropped = links.scrub(hyphenate(reply.text), self._allowed)
        text = trim(links.linkify(text, self.people))
        cost = reply.usage.cost(self.settings.price)
        if self.ledger is not None:
            self.ledger.charge(cost)
            self.ledger.log(
                {
                    'asker': asker,
                    'characters': [p.name for p in mine],
                    'question': question,
                    'reply': text,
                    'model': reply.model,
                    'tokens': reply.usage.__dict__,
                    'usd': round(cost, 6),
                    'seconds': round(reply.seconds, 2),
                    'dropped_links': dropped,
                }
            )
        return Answer(text, True, reply.usage, cost, reply.seconds, tuple(dropped))


def load_people(path: Path = DATA / 'roster.json') -> list[links.Person]:
    if not path.exists():
        return []
    return [links.Person(p['name'], p['url']) for p in json.loads(path.read_text('utf-8'))]


def load_profiles(path: Path = DATA / 'profiles.json') -> list[Profile]:
    if not path.exists():
        return []
    return [from_json(p) for p in json.loads(path.read_text('utf-8'))]


def build(
    defaults_path: Path = WEBAPP / 'development-defaults.ini',
    secrets_path: Path = WEBAPP / 'development-secrets.ini',
    data: Path = DATA,
) -> Lookup:
    """The Lookup the bot runs: shipped glossary, baked roster and profiles, ledger beside them."""
    settings, _ = load_settings(defaults_path, secrets_path)
    data.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(data / 'spend.json', data / 'log.jsonl', settings.ceiling)
    entries = glossary.load()
    if (data / 'people.jsonl').exists():
        entries = glossary.merge(entries, glossary.load(data / 'people.jsonl'))
    return Lookup(
        settings,
        entries,
        load_people(data / 'roster.json'),
        Profiles(load_profiles(data / 'profiles.json')),
        ledger,
    )
