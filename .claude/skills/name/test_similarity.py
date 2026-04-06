"""Tests for similarity.py"""

from similarity import edit_distance, is_too_similar


class TestEditDistance:
    def test_exact_match(self):
        assert edit_distance("hello", "hello") == 0

    def test_case_insensitive(self):
        assert edit_distance("Hello", "hello") == 0

    def test_single_substitution(self):
        assert edit_distance("cat", "bat") == 1

    def test_single_insertion(self):
        assert edit_distance("cat", "cats") == 1

    def test_single_deletion(self):
        assert edit_distance("cats", "cat") == 1

    def test_distance_two(self):
        assert edit_distance("cat", "dog") == 3

    def test_empty_and_nonempty(self):
        assert edit_distance("", "abc") == 3

    def test_both_empty(self):
        assert edit_distance("", "") == 0

    def test_longer_strings(self):
        assert edit_distance("Takeshi", "Takashi") == 1

    def test_completely_different(self):
        assert edit_distance("abc", "xyz") == 3


class TestIsTooSimilar:
    def test_exact_match(self):
        assert is_too_similar("Chiyo", ["Chiyo"]) is True

    def test_case_insensitive_match(self):
        assert is_too_similar("chiyo", ["Chiyo"]) is True

    def test_edit_distance_one(self):
        assert is_too_similar("Chiyu", ["Chiyo"]) is True

    def test_edit_distance_two_not_similar(self):
        assert is_too_similar("Akemi", ["Akari"]) is False

    def test_prefix_match_longer(self):
        assert is_too_similar("Chiyoko", ["Chiyo"]) is True

    def test_prefix_match_shorter(self):
        assert is_too_similar("Chiyo", ["Chiyoko"]) is True

    def test_no_prefix_no_edit(self):
        assert is_too_similar("Haruka", ["Akari"]) is False

    def test_empty_existing_list(self):
        assert is_too_similar("Anything", []) is False

    def test_multiple_existing_names(self):
        existing = ["Akari", "Takeshi", "Haruka"]
        assert is_too_similar("Takashi", existing) is True  # edit dist 1 from Takeshi
        assert is_too_similar("Noboru", existing) is False
