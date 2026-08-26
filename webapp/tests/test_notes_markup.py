"""Behavior tests for l7r.notes_markup - glossary tooltips and bearer links."""

from __future__ import annotations

import json
from pathlib import Path

from l7r import notes_markup as nm


def test_glossary_term_gets_tooltip_span_case_insensitively() -> None:
    out = str(nm.render_notes('Attested samurai Nanori; the on-yomi is Genshin.'))
    assert '<span class="term" tabindex="0" data-tip="' in out
    assert '>Nanori</span>' in out
    assert '>on-yomi</span>' in out
    assert out.count('class="term"') == 2


def test_term_is_whole_word_only() -> None:
    # "nanori-ji" and "kuge" inside "kugel" must not be tagged
    out = str(nm.render_notes('nanori-ji elements; a kugel.'))
    assert 'class="term"' not in out


def test_bearer_links_longest_first_and_only_once() -> None:
    links = {
        'Yoshitsune': 'https://en.wikipedia.org/wiki/Y',
        'Minamoto no Yoshitsune': 'https://en.wikipedia.org/wiki/Minamoto_no_Yoshitsune',
    }
    out = str(nm.render_notes('Bearer: Minamoto no Yoshitsune. Also Yoshitsune again.', links))
    assert 'href="https://en.wikipedia.org/wiki/Minamoto_no_Yoshitsune"' in out
    assert 'target="_blank" rel="noopener">Minamoto no Yoshitsune</a>' in out
    assert out.count('<a ') == 2


def test_terms_inside_a_link_are_left_alone_and_html_is_escaped() -> None:
    links = {'Nanori Taro': 'https://en.wikipedia.org/wiki/N'}
    out = str(nm.render_notes('<b>Nanori Taro</b> was a nanori bearer', links))
    assert '&lt;b&gt;' in out
    assert '<b>' not in out
    assert out.count('class="term"') == 1  # the bare "nanori", not the one in the link text


def test_load_wiki_links_tolerates_missing_and_bad_files(tmp_path: Path) -> None:
    assert nm.load_wiki_links(tmp_path) == {}
    (tmp_path / 'wiki-links.json').write_text('[1, 2]')
    assert nm.load_wiki_links(tmp_path) == {}
    (tmp_path / 'wiki-links.json').write_text('{not json')
    assert nm.load_wiki_links(tmp_path) == {}
    (tmp_path / 'wiki-links.json').write_text(json.dumps({'A B': 'https://x/A_B', 'bad': 3}))
    assert nm.load_wiki_links(tmp_path) == {'A B': 'https://x/A_B'}


def test_real_links_file_is_well_formed() -> None:
    here = Path(__file__).resolve().parent.parent.parent / '.claude' / 'skills' / 'name'
    links = nm.load_wiki_links(here)
    assert 'Hojo Tokimune' in links or len(links) > 50
    assert all(u.startswith('https://en.wikipedia.org/wiki/') for u in links.values())
