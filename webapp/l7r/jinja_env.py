"""Shared Jinja2 environment with custom filters.

The ChoiceLoader looks in l7r/templates first, then chargen/templates so that
the existing chargen index.html can `{% extends "_layout.html" %}` from the
shared layout.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from l7r.fortunes import CLANS, FORTUNES, clan_label
from l7r.sections import SECTIONS

_HERE = Path(__file__).parent
_L7R_TEMPLATES = _HERE / 'templates'
_CHARGEN_TEMPLATES = _HERE.parent / 'chargen' / 'templates'

# Markdown-style *italic* runs. Conservative: no nesting, no asterisks adjacent to spaces.
_EM_PATTERN = re.compile(r'\*([^*\n]+)\*')


def description_html(text: str) -> Markup:
    """Render relic description prose as paragraphs with `<em>` for `*italic*`.

    Input is plain text. Paragraphs are double-newline-separated. The output
    is HTML-safe: all input is escaped before italics are applied.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    rendered: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        escaped = html.escape(para)
        with_em = _EM_PATTERN.sub(r'<em>\1</em>', escaped)
        rendered.append(f'<p>{with_em}</p>')
    return Markup('\n'.join(rendered))


def relic_type_short(relic_type: str) -> str:
    """The main category of a relic_type, dropping any '(parenthetical)' descriptor."""
    return relic_type.split('(', 1)[0].strip()


def build_environment() -> Environment:
    """Construct the shared Jinja2 environment used by all templates."""
    loader = ChoiceLoader(
        [
            FileSystemLoader(str(_L7R_TEMPLATES)),
            FileSystemLoader(str(_CHARGEN_TEMPLATES)),
        ]
    )
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters['description_html'] = description_html
    env.filters['relic_type_short'] = relic_type_short
    env.filters['clan_label'] = clan_label
    env.globals['SECTIONS'] = SECTIONS
    env.globals['FORTUNES'] = FORTUNES
    env.globals['CLANS'] = CLANS
    return env
