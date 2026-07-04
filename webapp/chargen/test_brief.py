"""Behavior tests for the full-corpus brief assembly (``chargen.brief``)."""

from __future__ import annotations

from pathlib import Path

import pytest

from chargen import brief

_L7R_SAMPLE = (
    '# Notes\n\n'
    '## The Setting\n\nintro\n\n'
    '### The Great Clans\n\nClans are alike.\n\n'
    '### Hierarchies\n\ntiers\n\n'
    "### Moto Khuyag's Death Detectors\n\nhorseshoes\n\n"
    '### The Nameless One\n\nfaceless\n\n'
    '### Gaijin\n\nforeigners\n\n'
    "#### Bashi's Letter on the Moto\n\nletter\n\n"
    '### The Moto\n\nsteppes\n\n'
    '#### The Gods of Death\n\nfour of them\n\n'
    '### The Imperial Road Through Minami\n\nno waystations\n\n'
    '### Wasp Clan NPCs\n\nwriteups\n\n'
    '#### Tsuruchi Tatsuki\n\namulets\n\n'
    '## The Fortunes\n\nfaith\n\n'
    '### 3rd Imperial Legion Backstories\n\nthird legion\n\n'
    '### 1st Imperial Legion Backstories\n\nfirst legion\n\n'
    '## The Structure of Rokugani Government\n\nministries\n\n'
    '### The Imperial Budget\n\nsee budgets file\n\n'
    '## The Measure of Standing and the Accordances of Rank\n\nprecedence\n\n'
    '## The Karmic Inquisitors Campaign\n\npitch\n\n'
    '### Campaign Description\n\ninquisitors\n\n'
    '### The Damasu Domain\n\nlion vassals\n\n'
    '#### Damasu Temples\n\nshrines\n\n'
    '#### Temple Daily Life\n\nchores\n\n'
    '#### Temple Relics\n\ndubious bones\n\n'
    '#### Relic Seekers\n\npilgrims\n\n'
    '## The First Toshi Ranbo Campaign\n\nviolence\n\n'
    '## Temple Organization\n\nabbots\n\n'
    '## Soothsaying\n\nomens\n\n'
    '## Oaths and Vows\n\nsworn pledges\n\n'
    '## The Peasant Campaign\n\nrice riots\n\n'
    '## The Hidden Way Campaign\n\ngardens\n\n'
    '## Next Chapter\n\nmore\n'
)

#: _L7R_SAMPLE after build_full_brief excises brief._CASTE_L7R_SECTIONS (the
#: base is caste-neutral: every caste's material comes out for everyone) and
#: brief._EXCLUDED_L7R_SECTIONS in one merged-span pass. The "Wasp Clan NPCs"
#: parent survives with only its Tatsuki subsection excised; "The Fortunes"
#: survives its excised legion-backstory subsections; the Karmic campaign
#: (with the Damasu block inside it) is gone entirely.
_L7R_TRIMMED = (
    '# Notes\n\n'
    '## The Setting\n\nintro\n\n'
    '### The Great Clans\n\nClans are alike.\n\n'
    '### Hierarchies\n\ntiers\n\n'
    '### Wasp Clan NPCs\n\nwriteups\n\n'
    '## The Fortunes\n\nfaith\n\n'
    '## Next Chapter\n\nmore'
)

#: The monk supplement built from _L7R_SAMPLE: the excised monk material,
#: verbatim, in _CASTE_L7R_SECTIONS order, under the supplement heading.
_MONK_SUPPLEMENT = (
    '# SETTING BRIEF SUPPLEMENT\n\n'
    '#### Damasu Temples\n\nshrines\n\n'
    '#### Temple Daily Life\n\nchores\n\n'
    '#### Temple Relics\n\ndubious bones\n\n'
    '## Temple Organization\n\nabbots\n\n'
    '## Soothsaying\n\nomens\n\n'
    '## Oaths and Vows\n\nsworn pledges'
)

_PEASANT_SUPPLEMENT = '# SETTING BRIEF SUPPLEMENT\n\n## The Peasant Campaign\n\nrice riots'

#: The samurai supplement: l7r sections first (with the excluded Imperial
#: Budget stub stripped from the government block and the monk temple material
#: stripped from the Damasu block), then the budgets.md sections (with the
#: excluded daimyo example and Imperial aggregates stripped).
_SAMURAI_SUPPLEMENT = (
    '# SETTING BRIEF SUPPLEMENT\n\n'
    '## The Structure of Rokugani Government\n\nministries\n\n'
    '## The Measure of Standing and the Accordances of Rank\n\nprecedence\n\n'
    '### 3rd Imperial Legion Backstories\n\nthird legion\n\n'
    '### 1st Imperial Legion Backstories\n\nfirst legion\n\n'
    '### The Damasu Domain\n\nlion vassals\n\n'
    '#### Relic Seekers\n\npilgrims\n\n'
    '## Ministry budgets\n\noverheads\n\n'
    '## Example office-holder budgets\n\nworked examples\n\n'
    '## The Imperial budget\n\ntreasury\n\n'
    '### Imperial roads: a special case\n\nroads'
)


_BUDGETS_SAMPLE = (
    '# Budgets\n\n'
    'intro\n\n'
    '## The two Empire-wide multipliers\n\nmath\n\n'
    '### The most common mistake\n\noops\n\n'
    '## Domain\n\npop table\n\n'
    '### Capital city\n\nbig\n\n'
    '### Discretionary budgets\n\nspending\n\n'
    '### Hamlet\n\ntiny\n\n'
    '## Ministry budgets\n\noverheads\n\n'
    '## Example office-holder budgets\n\nworked examples\n\n'
    '### Daimyo Hida no Reiji Isao of the Reiji Domain\n\nisao flows\n\n'
    '## The Imperial budget\n\ntreasury\n\n'
    '### Imperial revenue (~34-36 million koku per year at baseline)\n\nrev\n\n'
    '### Imperial spending (~30-31 million koku per year)\n\nspend\n\n'
    '### Imperial budget scale: historical context\n\nhistory\n\n'
    '### Imperial roads: a special case\n\nroads\n\n'
    '## Land productivity\n\nrice math\n'
)

#: _BUDGETS_SAMPLE after build_full_brief applies brief._EXCLUDED_BUDGET_SECTIONS,
#: brief._CASTE_BUDGET_SECTIONS (all samurai-only now), and
#: brief._PRUNED_BUDGET_SECTIONS: only the pruned Domain block remains.
_BUDGETS_TRIMMED = '# Budgets\n\nintro\n\n## Domain\n\n### Discretionary budgets\n\nspending'


def _make_corpus(tmp_path: Path, l7r: str = _L7R_SAMPLE, budgets: str = _BUDGETS_SAMPLE) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / 'l7r.md').write_text(l7r, encoding='utf-8')
    (tmp_path / 'budgets.md').write_text(budgets, encoding='utf-8')
    return tmp_path


def test_candidate_dirs_lists_env_first_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('L7R_SETTING_DIR', '/explicit/dir')
    dirs = brief._candidate_dirs()
    assert dirs[0] == Path('/explicit/dir')
    assert dirs[1:] == [brief._MOUNT_DIR, brief._BUNDLED_DIR]


def test_candidate_dirs_omits_env_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    assert brief._candidate_dirs() == [brief._MOUNT_DIR, brief._BUNDLED_DIR]


def test_resolve_prefers_mount_over_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mount = _make_corpus(tmp_path / 'mount')
    bundle = _make_corpus(tmp_path / 'bundle')
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_MOUNT_DIR', mount)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', bundle)
    assert brief.resolve_corpus_dir() == mount


def test_resolve_prefers_env_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corpus = _make_corpus(tmp_path)
    monkeypatch.setenv('L7R_SETTING_DIR', str(corpus))
    assert brief.resolve_corpus_dir() == corpus


def test_resolve_falls_back_to_bundled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corpus = _make_corpus(tmp_path)
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', corpus)
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'nope')
    assert brief.resolve_corpus_dir() == corpus


def test_resolve_raises_when_no_corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', tmp_path / 'a')
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'b')
    with pytest.raises(brief.CorpusNotFound) as exc:
        brief.resolve_corpus_dir()
    assert 'not found' in str(exc.value)


def test_extract_section_stops_at_next_same_level() -> None:
    out = brief.extract_section(_L7R_SAMPLE, 'The Great Clans')
    assert out == '### The Great Clans\n\nClans are alike.'


def test_extract_section_swallows_lower_levels_until_higher() -> None:
    out = brief.extract_section(_L7R_SAMPLE, 'The Setting')
    assert 'The Great Clans' in out
    assert 'Hierarchies' in out
    assert 'Next Chapter' not in out


def test_extract_section_runs_to_eof_when_no_following_heading() -> None:
    assert brief.extract_section('## Only\n\nbody line\n', 'Only') == '## Only\n\nbody line'


def test_extract_section_raises_when_missing() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.extract_section(_L7R_SAMPLE, 'No Such Heading')


def test_remove_section_excises_block_and_its_subsections() -> None:
    out = brief.remove_section(_L7R_SAMPLE, 'Gaijin')
    assert 'Gaijin' not in out
    assert "Bashi's Letter" not in out
    assert 'The Moto' in out  # the following same-level section survives
    assert 'Clans are alike.' in out


def test_remove_section_preserves_surrounding_text_exactly() -> None:
    text = '## A\n\nbody a\n\n## B\n\nbody b\n\n## C\n\nbody c\n'
    assert brief.remove_section(text, 'B') == '## A\n\nbody a\n\n## C\n\nbody c'


def test_remove_section_runs_to_eof_when_no_following_heading() -> None:
    text = '## A\n\nbody a\n\n## B\n\nbody b\n'
    assert brief.remove_section(text, 'B') == '## A\n\nbody a\n'


def test_remove_section_raises_when_missing() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.remove_section(_L7R_SAMPLE, 'No Such Heading')


def test_remove_sections_handles_nested_titles_in_any_order() -> None:
    text = '## Outer\n\nbody\n\n### Inner\n\ninner body\n\n## After\n\nafter body\n'
    for titles in (['Outer', 'Inner'], ['Inner', 'Outer']):
        assert brief.remove_sections(text, titles) == '## After\n\nafter body'


def test_remove_sections_raises_on_any_missing_title() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.remove_sections('## A\n\nx\n', ['A', 'No Such Heading'])


def test_remove_present_skips_absent_titles() -> None:
    text = '## A\n\na\n\n## B\n\nb\n'
    assert brief._remove_present(text, ['B', 'Not There']) == '## A\n\na\n'


def test_remove_section_except_keeps_heading_and_named_subsection() -> None:
    out = brief.remove_section_except(_BUDGETS_SAMPLE, 'Domain', ('Discretionary budgets',))
    assert '## Domain\n\n### Discretionary budgets\n\nspending' in out
    assert 'pop table' not in out  # the section's own body goes
    assert 'Capital city' not in out  # preceding sibling goes
    assert 'Hamlet' not in out  # following sibling goes
    assert 'rice math' in out  # the next same-level section survives


def test_remove_section_except_preserves_order_of_multiple_keeps() -> None:
    text = '## P\n\nbody\n\n### A\n\na\n\n### B\n\nb\n\n### C\n\nc\n\n## Q\n\nq\n'
    out = brief.remove_section_except(text, 'P', ('A', 'C'))
    assert out == '## P\n\n### A\n\na\n\n### C\n\nc\n\n## Q\n\nq'


def test_remove_section_except_raises_when_section_missing() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.remove_section_except(_BUDGETS_SAMPLE, 'No Such Heading', ())


def test_remove_section_except_raises_when_kept_subsection_missing() -> None:
    with pytest.raises(ValueError, match='heading not found'):
        brief.remove_section_except(_BUDGETS_SAMPLE, 'Domain', ('No Such Subsection',))


def test_build_full_brief_assembles_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('DESIGN BRIEF\n', encoding='utf-8')
    flavor_md.write_text('FLAVOR SUMMARY\n', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)

    out = brief.build_full_brief(corpus)

    expected = '\n\n'.join(
        [
            'DESIGN BRIEF',
            '### The Great Clans\n\nClans are alike.',
            'FLAVOR SUMMARY',
            '# FULL CANONICAL NOTES\n\n'
            + _L7R_TRIMMED
            + '\n\n# BUDGETS AND ECONOMIC MODEL (budgets.md)\n\n'
            + _BUDGETS_TRIMMED,
        ]
    )
    assert out == expected


def test_build_full_brief_excises_campaign_irrelevant_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('B', encoding='utf-8')
    flavor_md.write_text('F', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)

    out = brief.build_full_brief(corpus)

    for title in brief._EXCLUDED_L7R_SECTIONS:
        assert title not in out
    assert 'Gods of Death' not in out  # subsection goes with its parent
    assert 'Hierarchies' in out  # neighboring lore survives
    for title in brief._EXCLUDED_BUDGET_SECTIONS:
        assert title not in out
    assert 'Discretionary budgets' in out  # kept subsection of pruned Domain
    assert 'Capital city' not in out  # dropped sibling of the kept subsection
    assert 'The Karmic Inquisitors Campaign' not in out  # fully excluded now
    assert 'lion vassals' not in out  # the Damasu block moved to the samurai supplement
    assert 'faith' in out  # The Fortunes survives its excised legion subsections
    for sections in (brief._CASTE_L7R_SECTIONS, brief._CASTE_BUDGET_SECTIONS):
        for group in sections.values():
            for title in group:
                assert title not in out  # caste material is out of the base for everyone


def test_build_caste_supplement_returns_monk_material_in_order(tmp_path: Path) -> None:
    corpus = _make_corpus(tmp_path)
    assert brief.build_caste_supplement('monk', corpus) == _MONK_SUPPLEMENT


def test_build_caste_supplement_is_case_insensitive_to_dropdown_value(tmp_path: Path) -> None:
    corpus = _make_corpus(tmp_path)
    assert brief.build_caste_supplement(' Monk ', corpus) == _MONK_SUPPLEMENT


def test_build_caste_supplement_returns_peasant_material(tmp_path: Path) -> None:
    corpus = _make_corpus(tmp_path)
    assert brief.build_caste_supplement('Peasant', corpus) == _PEASANT_SUPPLEMENT


def test_build_caste_supplement_returns_samurai_material(tmp_path: Path) -> None:
    corpus = _make_corpus(tmp_path)
    assert brief.build_caste_supplement('Samurai', corpus) == _SAMURAI_SUPPLEMENT


def test_build_caste_supplement_empty_for_types_without_sections(tmp_path: Path) -> None:
    corpus = _make_corpus(tmp_path)
    assert brief.build_caste_supplement('', corpus) == ''
    assert brief.build_caste_supplement('unknown', corpus) == ''


def test_build_caste_supplement_resolves_corpus_when_not_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', corpus)
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'nope')
    assert brief.build_caste_supplement('Monk') == _MONK_SUPPLEMENT


def test_build_caste_supplement_raises_when_corpus_incomplete(tmp_path: Path) -> None:
    (tmp_path / 'l7r.md').write_text(_L7R_SAMPLE, encoding='utf-8')  # no budgets.md
    with pytest.raises(brief.CorpusNotFound):
        brief.build_caste_supplement('Monk', tmp_path)


def test_base_plus_supplement_reconstruct_all_monk_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The supplement is exactly what the base gave up - nothing lost for monks."""
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('B', encoding='utf-8')
    flavor_md.write_text('F', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)

    base = brief.build_full_brief(corpus)
    supplement = brief.build_caste_supplement('Monk', corpus)
    for body in ('shrines', 'chores', 'dubious bones', 'abbots', 'omens', 'sworn pledges'):
        assert body not in base
        assert body in supplement

    samurai = brief.build_caste_supplement('Samurai', corpus)
    for body in ('ministries', 'precedence', 'third legion', 'first legion', 'lion vassals'):
        assert body not in base
        assert body in samurai
    for body in ('overheads', 'worked examples', 'treasury', 'roads'):
        assert body not in base
        assert body in samurai
    assert 'see budgets file' not in samurai  # excluded l7r Imperial Budget stub stays out
    assert 'isao flows' not in samurai  # excluded daimyo example stays out
    assert 'dubious bones' not in samurai  # monk material does not leak into samurai


def test_build_full_brief_raises_when_excluded_section_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path, l7r='## The Great Clans\n\nx\n')
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('B', encoding='utf-8')
    flavor_md.write_text('F', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)

    with pytest.raises(ValueError, match='heading not found'):
        brief.build_full_brief(corpus)


def test_build_full_brief_resolves_when_no_corpus_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus = _make_corpus(tmp_path)
    brief_md = tmp_path / 'brief.md'
    flavor_md = tmp_path / 'flavor.md'
    brief_md.write_text('B', encoding='utf-8')
    flavor_md.write_text('F', encoding='utf-8')
    monkeypatch.setattr(brief, '_BRIEF_PATH', brief_md)
    monkeypatch.setattr(brief, '_FLAVOR_PATH', flavor_md)
    monkeypatch.delenv('L7R_SETTING_DIR', raising=False)
    monkeypatch.setattr(brief, '_BUNDLED_DIR', corpus)
    monkeypatch.setattr(brief, '_MOUNT_DIR', tmp_path / 'nope')

    out = brief.build_full_brief()
    assert out.startswith('B\n\n### The Great Clans')
    assert out.endswith('spending')


def test_build_full_brief_raises_when_corpus_dir_incomplete(tmp_path: Path) -> None:
    (tmp_path / 'l7r.md').write_text('## The Great Clans\n\nx\n', encoding='utf-8')
    with pytest.raises(brief.CorpusNotFound):
        brief.build_full_brief(tmp_path)
