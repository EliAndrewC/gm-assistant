"""Tests for pick_name.py"""

import json
import os
import tempfile

import pytest

import campaign
from pick_name import load_pool, parse_args, pick


class TestParseArgs:
    def test_no_args(self):
        assert parse_args([])[:3] == (None, 1, False)

    def test_male_full(self):
        assert parse_args(["male"])[:3] == ("male", 1, False)

    def test_female_full(self):
        assert parse_args(["female"])[:3] == ("female", 1, False)

    def test_male_shorthand(self):
        assert parse_args(["m"])[:3] == ("male", 1, False)

    def test_female_shorthand(self):
        assert parse_args(["f"])[:3] == ("female", 1, False)

    def test_peasant_full(self):
        assert parse_args(["peasant"])[:3] == (None, 1, True)

    def test_peasant_shorthand(self):
        assert parse_args(["p"])[:3] == (None, 1, True)

    def test_count_bare_number(self):
        assert parse_args(["3"])[:3] == (None, 3, False)

    def test_count_x_prefix(self):
        assert parse_args(["x5"])[:3] == (None, 5, False)

    def test_concatenated_pf3(self):
        assert parse_args(["pf3"])[:3] == ("female", 3, True)

    def test_concatenated_3mp(self):
        assert parse_args(["3mp"])[:3] == ("male", 3, True)

    def test_concatenated_m2(self):
        assert parse_args(["m2"])[:3] == ("male", 2, False)

    def test_concatenated_fp(self):
        assert parse_args(["fp"])[:3] == ("female", 1, True)

    def test_mixed_full_words(self):
        assert parse_args(["female", "x3", "peasant"])[:3] == ("female", 3, True)

    def test_mixed_full_and_short(self):
        assert parse_args(["male", "p", "5"])[:3] == ("male", 5, True)

    def test_last_gender_wins(self):
        # If both m and f appear, last one wins
        assert parse_args(["mf"])[0] == "female"
        assert parse_args(["fm"])[0] == "male"

    def test_concatenated_with_x(self):
        assert parse_args(["px5f"])[:3] == ("female", 5, True)


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
        pool_file.write_text(
            '{"name": "A", "gender": "male"}\n\n{"name": "B", "gender": "male"}\n'
        )
        result = load_pool(str(pool_file))
        assert len(result) == 2


def write_cache(path, full_names):
    """A campaign cache file (opcache shape) naming the given full names."""
    path.write_text(json.dumps({str(i): {"name": n} for i, n in enumerate(full_names)}))


class TestCampaignUsedNames:
    def test_missing_cache_is_empty_and_warns(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("campaign.CACHE_PATH", tmp_path / "none.json")
        assert campaign.used_names(refresh=False) == []
        assert "EMPTY roster" in capsys.readouterr().err

    def test_given_name_is_last_token(self, tmp_path, monkeypatch):
        cache = tmp_path / "characters.json"
        write_cache(cache, ["Matsu no Masao Agetoki", "Haruka", "Hantei Satoru"])
        monkeypatch.setattr("campaign.CACHE_PATH", cache)
        assert campaign.used_names(refresh=False) == ["Agetoki", "Haruka", "Satoru"]

    def test_fresh_cache_is_not_refreshed(self, tmp_path, monkeypatch):
        cache = tmp_path / "characters.json"
        write_cache(cache, ["Haruka"])
        monkeypatch.setattr("campaign.CACHE_PATH", cache)
        monkeypatch.setattr(
            "campaign.opcache.refresh_if_stale",
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("refreshed")),
        )
        monkeypatch.setattr("campaign.opcache.cache_age", lambda p: 10.0)
        assert campaign.used_names() == ["Haruka"]

    def test_stale_cache_warns_when_refresh_fails(self, tmp_path, monkeypatch, capsys):
        cache = tmp_path / "characters.json"
        write_cache(cache, ["Haruka"])
        monkeypatch.setattr("campaign.CACHE_PATH", cache)
        monkeypatch.setattr(
            "campaign.opcache.refresh_if_stale",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no creds")),
        )
        monkeypatch.setattr("campaign.opcache.cache_age", lambda p: 7200.0)
        assert campaign.used_names() == ["Haruka"]
        err = capsys.readouterr().err
        assert "refresh failed" in err and "2.0h old" in err

    def test_force_refresh_passes_zero_max_age(self, tmp_path, monkeypatch):
        cache = tmp_path / "characters.json"
        write_cache(cache, ["Haruka"])
        monkeypatch.setattr("campaign.CACHE_PATH", cache)
        seen = {}
        monkeypatch.setattr(
            "campaign.opcache.refresh_if_stale",
            lambda max_age, path: seen.setdefault("max_age", max_age) and False,
        )
        campaign.used_names(refresh=True)
        assert seen["max_age"] == 0.0


class TestPick:
    @pytest.fixture
    def pool_dir(self, tmp_path, monkeypatch):
        """Create temp pool files and campaign names."""
        male_pool = tmp_path / "pool-male.jsonl"
        female_pool = tmp_path / "pool-female.jsonl"
        cache = tmp_path / "characters.json"

        male_entries = [
            {
                "name": "Takeshi",
                "gender": "male",
                "format": 1,
                "explanation": "test",
                "notes": "test",
                "peasant": True,
            },
            {
                "name": "Noboru",
                "gender": "male",
                "format": 2,
                "explanation": "test",
                "notes": "test",
                "peasant": False,
            },
            {
                "name": "Isao",
                "gender": "male",
                "format": 3,
                "explanation": "test",
                "notes": "test",
                "peasant": True,
            },
        ]
        female_entries = [
            {
                "name": "Hanako",
                "gender": "female",
                "format": 1,
                "explanation": "test",
                "notes": "test",
                "peasant": True,
            },
            {
                "name": "Kimiko",
                "gender": "female",
                "format": 2,
                "explanation": "test",
                "notes": "test",
                "peasant": False,
            },
        ]

        male_pool.write_text("\n".join(json.dumps(e) for e in male_entries) + "\n")
        female_pool.write_text("\n".join(json.dumps(e) for e in female_entries) + "\n")
        write_cache(cache, ["Hantei Satoru"])

        monkeypatch.setattr("pick_name.MALE_POOL", str(male_pool))
        monkeypatch.setattr("pick_name.FEMALE_POOL", str(female_pool))
        monkeypatch.setattr("campaign.CACHE_PATH", cache)
        return tmp_path

    def _extract_names(self, output):
        """Extract bold name from markdown output lines like **Name** - ..."""
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
        # Pick 2 male peasant names - should never get Noboru (peasant=False)
        pick("male", 2, peasant=True)
        output = capsys.readouterr().out
        names = self._extract_names(output)
        for name in names:
            assert name in ("Takeshi", "Isao")

    def test_campaign_name_excluded(self, pool_dir, capsys, monkeypatch):
        """Names similar to campaign names should be filtered out."""
        # Add "Takesh" to the roster - edit distance 1 from Takeshi
        write_cache(pool_dir / "characters.json", ["Hida Takesh"])
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
        monkeypatch.setattr("campaign.CACHE_PATH", tmp_path / "none.json")
        monkeypatch.setattr("campaign.opcache.refresh_if_stale", lambda *a, **k: False)
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

    def test_batch_rejects_shared_first_letter(self, pool_dir, capsys, monkeypatch):
        """Within one batch, no two picked names may start with the same letter."""
        male_pool = pool_dir / "pool-male.jsonl"
        entries = [
            {"name": n, "gender": "male", "format": 1, "explanation": "test"}
            for n in ("Kaito", "Kenji", "Noboru")
        ]
        male_pool.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        monkeypatch.setattr("pick_name.MALE_POOL", str(male_pool))
        pick("male", 2)
        names = self._extract_names(capsys.readouterr().out)
        assert len(names) == 2
        initials = [n[0] for n in names]
        assert len(initials) == len(set(initials))

    def test_batch_rejects_rhymes(self, pool_dir, capsys, monkeypatch):
        """Within one batch, no two picked names may rhyme (3+ letter shared tail)."""
        male_pool = pool_dir / "pool-male.jsonl"
        entries = [
            {"name": n, "gender": "male", "format": 1, "explanation": "test"}
            for n in ("Naomasa", "Hiromasa", "Kenji")
        ]
        male_pool.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
        monkeypatch.setattr("pick_name.MALE_POOL", str(male_pool))
        pick("male", 2)
        names = self._extract_names(capsys.readouterr().out)
        assert len(names) == 2
        assert not ("Naomasa" in names and "Hiromasa" in names)

    def test_avoid_list_applies_set_rule(self, pool_dir, capsys):
        """--avoid names are treated as members of the set: Takeshi/Isao share
        nothing with 'Nori'... but Noboru shares its N."""
        pick("male", 3, avoid=["Nori"])
        names = self._extract_names(capsys.readouterr().out)
        assert "Noboru" not in names and names

    def test_bank_gives_n_of_each_gender_labeled(self, pool_dir, capsys):
        pick(None, 1, bank=1)
        out = capsys.readouterr().out
        names = self._extract_names(out)
        assert len(names) == 2
        assert "(male)" in out and "(female)" in out


class TestParseOptions:
    def test_defaults(self):
        assert parse_args([])[3] == {"refresh": None, "avoid": [], "bank": 0}

    def test_refresh_avoid_bank(self):
        gender, count, peasant, opts = parse_args(
            ["--refresh", "--avoid", "Izumi,Reiji", "--bank", "4", "m2"]
        )
        assert opts == {"refresh": True, "avoid": ["Izumi", "Reiji"], "bank": 4}
        assert (gender, count) == ("male", 2)

    def test_dangling_flags_are_harmless(self):
        assert parse_args(["--avoid"])[3]["avoid"] == []
        assert parse_args(["--bank"])[3]["bank"] == 0
