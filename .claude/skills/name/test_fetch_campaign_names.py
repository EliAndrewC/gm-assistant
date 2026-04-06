"""Tests for fetch_campaign_names.py — HTML parsing only, no HTTP requests."""

from fetch_campaign_names import extract_personal_names, scrape_characters_page
import requests


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

        names, next_url = scrape_characters_page(FakeSession(), "http://example.com/characters")
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

        names, next_url = scrape_characters_page(FakeSession(), "http://example.com/characters")
        assert names == ["Moto Batu"]
        assert next_url is None

    def test_error_status_code(self, monkeypatch):
        class FakeResponse:
            status_code = 403
            text = "Forbidden"

        class FakeSession:
            def get(self, url, headers=None):
                return FakeResponse()

        names, next_url = scrape_characters_page(FakeSession(), "http://example.com/characters")
        assert names == []
        assert next_url is None
