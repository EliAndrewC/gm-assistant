"""Tests for pick_name.py"""

import json
import os
import tempfile

import pytest

from pick_name import parse_args, load_pool, load_campaign_names, pick


class TestParseArgs:
    def test_no_args(self):
        assert parse_args([]) == (None, 1, False)

    def test_male_full(self):
        assert parse_args(["male"]) == ("male", 1, False)

    def test_female_full(self):
        assert parse_args(["female"]) == ("female", 1, False)

    def test_male_shorthand(self):
        assert parse_args(["m"]) == ("male", 1, False)

    def test_female_shorthand(self):
        assert parse_args(["f"]) == ("female", 1, False)

    def test_peasant_full(self):
        assert parse_args(["peasant"]) == (None, 1, True)

    def test_peasant_shorthand(self):
        assert parse_args(["p"]) == (None, 1, True)

    def test_count_bare_number(self):
        assert parse_args(["3"]) == (None, 3, False)

    def test_count_x_prefix(self):
        assert parse_args(["x5"]) == (None, 5, False)

    def test_concatenated_pf3(self):
        assert parse_args(["pf3"]) == ("female", 3, True)

    def test_concatenated_3mp(self):
        assert parse_args(["3mp"]) == ("male", 3, True)

    def test_concatenated_m2(self):
        assert parse_args(["m2"]) == ("male", 2, False)

    def test_concatenated_fp(self):
        assert parse_args(["fp"]) == ("female", 1, True)

    def test_mixed_full_words(self):
        assert parse_args(["female", "x3", "peasant"]) == ("female", 3, True)

    def test_mixed_full_and_short(self):
        assert parse_args(["male", "p", "5"]) == ("male", 5, True)

    def test_last_gender_wins(self):
        # If both m and f appear, last one wins
        assert parse_args(["mf"])[0] == "female"
        assert parse_args(["fm"])[0] == "male"

    def test_concatenated_with_x(self):
        assert parse_args(["px5f"]) == ("female", 5, True)


class TestLoadPool:
    def test_missing_file(self):
        assert load_pool("/nonexistent/path.jsonl") == []

    def test_valid_file(self, tmp_path):
        pool_file = tmp_path / "pool.jsonl"
        entries = [
            {"name": "Takeshi", "gender": "male", "format": 1, "explanation": "test"},
            {"name": "Hanako", "gender": "female", "format": 2, "explanation": "test"},
        ]
        pool_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        result = load_pool(str(pool_file))
        assert len(result) == 2
        assert result[0]["name"] == "Takeshi"

    def test_empty_lines_skipped(self, tmp_path):
        pool_file = tmp_path / "pool.jsonl"
        pool_file.write_text('{"name": "A", "gender": "male"}\n\n{"name": "B", "gender": "male"}\n')
        result = load_pool(str(pool_file))
        assert len(result) == 2


class TestLoadCampaignNames:
    def test_missing_file(self, monkeypatch):
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", "/nonexistent/path.txt")
        assert load_campaign_names() == []

    def test_valid_file(self, tmp_path, monkeypatch):
        names_file = tmp_path / "names.txt"
        names_file.write_text("Agetoki\nHaruka\nSatoru\n")
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", str(names_file))
        result = load_campaign_names()
        assert result == ["Agetoki", "Haruka", "Satoru"]

    def test_empty_lines_skipped(self, tmp_path, monkeypatch):
        names_file = tmp_path / "names.txt"
        names_file.write_text("Agetoki\n\nHaruka\n\n")
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", str(names_file))
        assert len(load_campaign_names()) == 2


class TestPick:
    @pytest.fixture
    def pool_dir(self, tmp_path, monkeypatch):
        """Create temp pool files and campaign names."""
        male_pool = tmp_path / "pool-male.jsonl"
        female_pool = tmp_path / "pool-female.jsonl"
        campaign = tmp_path / "campaign-names.txt"

        male_entries = [
            {"name": "Takeshi", "gender": "male", "format": 1, "explanation": "test", "notes": "test", "peasant": True},
            {"name": "Noboru", "gender": "male", "format": 2, "explanation": "test", "notes": "test", "peasant": False},
            {"name": "Isao", "gender": "male", "format": 3, "explanation": "test", "notes": "test", "peasant": True},
        ]
        female_entries = [
            {"name": "Hanako", "gender": "female", "format": 1, "explanation": "test", "notes": "test", "peasant": True},
            {"name": "Kimiko", "gender": "female", "format": 2, "explanation": "test", "notes": "test", "peasant": False},
        ]

        male_pool.write_text("\n".join(json.dumps(e) for e in male_entries) + "\n")
        female_pool.write_text("\n".join(json.dumps(e) for e in female_entries) + "\n")
        campaign.write_text("Satoru\n")

        monkeypatch.setattr("pick_name.MALE_POOL", str(male_pool))
        monkeypatch.setattr("pick_name.FEMALE_POOL", str(female_pool))
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", str(campaign))
        return tmp_path

    def _extract_names(self, output):
        """Extract bold name from markdown output lines like **Name** — ..."""
        import re
        return re.findall(r"\*\*(\w+)\*\*", output)

    def test_pick_one_male(self, pool_dir, capsys):
        pick("male", 1)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        assert len(names) == 1
        assert names[0] in ("Takeshi", "Noboru", "Isao")

    def test_pick_one_female(self, pool_dir, capsys):
        pick("female", 1)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        assert len(names) == 1
        assert names[0] in ("Hanako", "Kimiko")

    def test_pick_peasant_only(self, pool_dir, capsys):
        # Pick 2 male peasant names — should never get Noboru (peasant=False)
        pick("male", 2, peasant=True)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        for name in names:
            assert name in ("Takeshi", "Isao")

    def test_campaign_name_excluded(self, pool_dir, capsys, monkeypatch):
        """Names similar to campaign names should be filtered out."""
        # Add "Takesh" to campaign names — edit distance 1 from Takeshi
        campaign = pool_dir / "campaign-names.txt"
        campaign.write_text("Takesh\n")
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", str(campaign))
        pick("male", 3)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        assert "Takeshi" not in names

    def test_pick_random_gender(self, pool_dir, capsys):
        """With no gender specified, should pick successfully."""
        pick(None, 3)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        assert len(names) >= 1

    def test_empty_pool_error(self, tmp_path, monkeypatch, capsys):
        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        monkeypatch.setattr("pick_name.MALE_POOL", str(empty))
        monkeypatch.setattr("pick_name.CAMPAIGN_NAMES", str(tmp_path / "none.txt"))
        pick("male", 1)
        # No output for empty pool (error goes to stdout as JSON still)
        output = capsys.readouterr().out.strip()
        assert "error" in output.lower() or "no" in output.lower()

    def test_no_duplicates_in_batch(self, pool_dir, capsys):
        """Picking multiple names shouldn't return the same name twice."""
        pick("male", 3)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        assert len(names) == len(set(names))
