"""Tests for fetch_campaign_names.py - HTML parsing only, no HTTP requests."""

import os

import pytest

import fetch_campaign_names
from fetch_campaign_names import (
    extract_personal_names,
    load_session_cookie,
    request_headers,
    scrape_characters_page,
)


class TestCookieIsNotNeededToImport:
    """The cookie is loaded on demand, not at import (2026-08-25). Importing this module used to
    `sys.exit(1)` on any machine with no `.env`, so pytest could not even COLLECT this file on a
    fresh container. The module-level constant that did it is gone; pin its absence."""

    def test_no_module_level_cookie_or_headers(self):
        assert not hasattr(fetch_campaign_names, "SESSION_COOKIE")
        assert not hasattr(fetch_campaign_names, "HEADERS")

    def test_missing_cookie_exits_only_when_asked(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OBSIDIAN_SESSION_COOKIE", raising=False)
        monkeypatch.setattr(fetch_campaign_names, "ENV_PATH", str(tmp_path / ".env"))
        with pytest.raises(SystemExit):
            load_session_cookie()

    def test_cookie_from_env_var_then_dotenv(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OBSIDIAN_SESSION_COOKIE", "from-env")
        assert load_session_cookie() == "from-env"
        monkeypatch.delenv("OBSIDIAN_SESSION_COOKIE")
        env = tmp_path / ".env"
        env.write_text("OBSIDIAN_SESSION_COOKIE='from-file'\n")
        monkeypatch.setattr(fetch_campaign_names, "ENV_PATH", str(env))
        assert load_session_cookie() == "from-file"

    def test_headers_carry_the_cookie(self):
        assert request_headers("abc=1")["Cookie"] == "abc=1"

    def test_output_path_is_beside_the_script(self):
        assert os.path.isabs(fetch_campaign_names.SKILL_DIR)
        assert os.path.basename(fetch_campaign_names.SKILL_DIR) == "name"


class TestExtractPersonalNames:
    def test_multi_word_names(self):
        full_names = ["Akodo no Damasu Chiho", "Bayushi Taka", "Moto Batu"]
        assert extract_personal_names(full_names) == ["Chiho", "Taka", "Batu"]

    def test_single_word_names(self):
        assert extract_personal_names(["Haruka"]) == ["Haruka"]

    def test_whitespace_handling(self):
        assert extract_personal_names(["  Akodo Taka  "]) == ["Taka"]

    def test_empty_list(self):
        assert extract_personal_names([]) == []

    def test_empty_string_in_list(self):
        # Empty string splits to [""], which has no parts after strip
        assert extract_personal_names([""]) == []


class TestScrapeCharactersPage:
    """Test HTML parsing with fixture HTML. Does not make real HTTP requests."""

    FIXTURE_HTML = """
    <html><body>
    <div class="content-list-item">
        <h4 class="character-name"><a href="/characters/akodo-taka">Akodo Taka</a></h4>
    </div>
    <div class="content-list-item">
        <h4 class="character-name"><a href="/characters/bayushi-kana">Bayushi Kana</a></h4>
    </div>
    <a class="next_page" href="/characters?page=2">Next</a>
    </body></html>
    """

    FIXTURE_LAST_PAGE = """
    <html><body>
    <div class="content-list-item">
        <h4 class="character-name"><a href="/characters/moto-batu">Moto Batu</a></h4>
    </div>
    </body></html>
    """

    def test_extracts_names_from_fixture(self, monkeypatch):
        class FakeResponse:
            status_code = 200
            text = self.FIXTURE_HTML

        class FakeSession:
            def get(self, url, headers=None):
                return FakeResponse()

        names, next_url = scrape_characters_page(
            FakeSession(), "http://example.com/characters"
        )
        assert names == ["Akodo Taka", "Bayushi Kana"]
        assert next_url is not None
        assert "page=2" in next_url

    def test_last_page_no_next(self, monkeypatch):
        class FakeResponse:
            status_code = 200
            text = self.FIXTURE_LAST_PAGE

        class FakeSession:
            def get(self, url, headers=None):
                return FakeResponse()

        names, next_url = scrape_characters_page(
            FakeSession(), "http://example.com/characters"
        )
        assert names == ["Moto Batu"]
        assert next_url is None

    def test_error_status_code(self, monkeypatch):
        class FakeResponse:
            status_code = 403
            text = "Forbidden"

        class FakeSession:
            def get(self, url, headers=None):
                return FakeResponse()

        names, next_url = scrape_characters_page(
            FakeSession(), "http://example.com/characters"
        )
        assert names == []
        assert next_url is None
