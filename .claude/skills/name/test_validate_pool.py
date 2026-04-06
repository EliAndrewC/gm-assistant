"""Tests for validate_pool.py and fix_pool.py"""

import json
import os
import sys

import pytest


def write_pool(path, entries):
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def read_pool(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture
def pool_env(tmp_path, monkeypatch):
    """Set up temp pool files and campaign names, patch modules to use them."""
    male_path = tmp_path / "pool-male.jsonl"
    female_path = tmp_path / "pool-female.jsonl"
    campaign_path = tmp_path / "campaign-names.txt"

    # Write empty defaults
    male_path.write_text("")
    female_path.write_text("")
    campaign_path.write_text("")

    # Patch SKILL_DIR for both validate_pool and fix_pool
    monkeypatch.setattr("validate_pool.SKILL_DIR", str(tmp_path))
    monkeypatch.setattr("fix_pool.SKILL_DIR", str(tmp_path))

    return tmp_path, male_path, female_path, campaign_path


class TestValidatePool:
    def test_valid_pool_no_exit(self, pool_env, capsys):
        """A valid pool should not call sys.exit(1)."""
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [{"name": "Takeshi", "gender": "male"}])
        write_pool(female_path, [{"name": "Hanako", "gender": "female"}])

        from validate_pool import validate
        # validate() only calls sys.exit(1) on error, otherwise returns normally
        validate()  # Should not raise
        output = capsys.readouterr().out
        assert "ALL CHECKS PASSED" in output

    def test_duplicate_detected(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [
            {"name": "Takeshi", "gender": "male"},
            {"name": "Takeshi", "gender": "male"},
        ])
        write_pool(female_path, [])

        from validate_pool import validate
        with pytest.raises(SystemExit):
            validate()
        output = capsys.readouterr().out
        assert "DUPLICATE" in output

    def test_campaign_similarity_detected(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [{"name": "Satoru", "gender": "male"}])
        write_pool(female_path, [])
        campaign_path.write_text("Satoru\n")

        from validate_pool import validate
        with pytest.raises(SystemExit):
            validate()
        output = capsys.readouterr().out
        assert "TOO SIMILAR TO CAMPAIGN" in output

    def test_cross_pool_similarity_detected(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [{"name": "Chiyo", "gender": "male"}])
        write_pool(female_path, [{"name": "Chiyoko", "gender": "female"}])

        from validate_pool import validate
        with pytest.raises(SystemExit):
            validate()
        output = capsys.readouterr().out
        assert "TOO SIMILAR IN POOL" in output


class TestFixPool:
    def test_removes_campaign_conflicts(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [
            {"name": "Satoru", "gender": "male"},
            {"name": "Takeshi", "gender": "male"},
        ])
        write_pool(female_path, [])
        campaign_path.write_text("Satoru\n")

        from fix_pool import fix
        fix()

        remaining = read_pool(male_path)
        names = [e["name"] for e in remaining]
        assert "Satoru" not in names
        assert "Takeshi" in names

    def test_removes_cross_pool_conflicts(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [{"name": "Chiyo", "gender": "male"}])
        write_pool(female_path, [{"name": "Chiyoko", "gender": "female"}])

        from fix_pool import fix
        fix()

        male_remaining = read_pool(male_path)
        female_remaining = read_pool(female_path)
        # Chiyo is processed first (male pool first), so Chiyoko should be removed
        assert len(male_remaining) == 1
        assert male_remaining[0]["name"] == "Chiyo"
        assert len(female_remaining) == 0

    def test_no_changes_when_clean(self, pool_env, capsys):
        tmp_path, male_path, female_path, campaign_path = pool_env
        write_pool(male_path, [{"name": "Takeshi", "gender": "male"}])
        write_pool(female_path, [{"name": "Hanako", "gender": "female"}])

        from fix_pool import fix
        fix()
        output = capsys.readouterr().out
        assert "0 removed" in output
