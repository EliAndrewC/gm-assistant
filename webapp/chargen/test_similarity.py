"""Behavior tests for ``chargen.similarity`` (ported from the /name skill, feature 200)."""

from chargen.similarity import edit_distance, is_too_similar, rhymes, set_conflict


class TestEditDistance:
    def test_exact_match(self) -> None:
        assert edit_distance('hello', 'hello') == 0

    def test_case_insensitive(self) -> None:
        assert edit_distance('Hello', 'hello') == 0

    def test_single_substitution(self) -> None:
        assert edit_distance('cat', 'bat') == 1

    def test_single_insertion(self) -> None:
        assert edit_distance('cat', 'cats') == 1

    def test_single_deletion(self) -> None:
        assert edit_distance('cats', 'cat') == 1

    def test_distance_two(self) -> None:
        assert edit_distance('cat', 'dog') == 3

    def test_empty_and_nonempty(self) -> None:
        assert edit_distance('', 'abc') == 3

    def test_both_empty(self) -> None:
        assert edit_distance('', '') == 0

    def test_longer_strings(self) -> None:
        assert edit_distance('Takeshi', 'Takashi') == 1

    def test_completely_different(self) -> None:
        assert edit_distance('abc', 'xyz') == 3


class TestIsTooSimilar:
    def test_exact_match(self) -> None:
        assert is_too_similar('Chiyo', ['Chiyo']) is True

    def test_case_insensitive_match(self) -> None:
        assert is_too_similar('chiyo', ['Chiyo']) is True

    def test_edit_distance_one(self) -> None:
        assert is_too_similar('Chiyu', ['Chiyo']) is True

    def test_edit_distance_two_not_similar(self) -> None:
        assert is_too_similar('Akemi', ['Akari']) is False

    def test_prefix_match_longer(self) -> None:
        assert is_too_similar('Chiyoko', ['Chiyo']) is True

    def test_prefix_match_shorter(self) -> None:
        assert is_too_similar('Chiyo', ['Chiyoko']) is True

    def test_no_prefix_no_edit(self) -> None:
        assert is_too_similar('Haruka', ['Akari']) is False

    def test_empty_existing_list(self) -> None:
        assert is_too_similar('Anything', []) is False

    def test_multiple_existing_names(self) -> None:
        existing = ['Akari', 'Takeshi', 'Haruka']
        assert is_too_similar('Takashi', existing) is True  # edit dist 1 from Takeshi
        assert is_too_similar('Noboru', existing) is False


class TestRhymes:
    def test_shared_three_letter_suffix(self) -> None:
        assert rhymes('Naomi', 'Hitomi') is True

    def test_shared_suffix_case_insensitive(self) -> None:
        assert rhymes('MICHIKO', 'sachiko') is True

    def test_two_letter_suffix_not_rhyme(self) -> None:
        assert rhymes('Kazuki', 'Hideki') is False

    def test_no_shared_suffix(self) -> None:
        assert rhymes('Akira', 'Noboru') is False

    def test_short_name_fully_contained_in_suffix(self) -> None:
        # Common suffix "ko" is only 2 letters, below the rhyme threshold
        assert rhymes('Ko', 'Yoko') is False


class TestKoRhymeException:
    """Both names ending in "ko" need a 4-letter tail, not 3.

    Otherwise the whole "-ko" space collapses into five rhyme classes keyed on
    the preceding vowel and exhausts the female pool. See rhymes().
    """

    def test_shared_vowel_plus_ko_is_not_enough(self) -> None:
        # "iko" is a 3-letter tail, which would rhyme under the general rule.
        assert rhymes('Yuriko', 'Reiko') is False

    def test_shared_vowel_plus_ko_is_not_enough_other_vowel(self) -> None:
        # "uko" - the pair the old docstring cited as a rhyming example.
        assert rhymes('Haruko', 'Yasuko') is False

    def test_matching_penultimate_syllable_still_rhymes(self) -> None:
        # "riko" reaches past the vowel to the consonant: last two syllables match.
        assert rhymes('Yuriko', 'Mariko') is True

    def test_longer_matching_tail_still_rhymes(self) -> None:
        assert rhymes('Michiko', 'Sachiko') is True

    def test_exception_does_not_apply_when_only_one_ends_in_ko(self) -> None:
        # Sadako/Wakako share "ako" but the tail stops there, so no rhyme;
        # Naomi/Hitomi is unaffected by the exception entirely.
        assert rhymes('Sadako', 'Wakako') is False
        assert rhymes('Naomi', 'Hitomi') is True

    def test_ko_pair_still_caught_by_edit_distance(self) -> None:
        # Riko/Miko no longer "rhyme", but set_conflict still rejects them -
        # edit distance 1 is the safety net under the relaxed rhyme rule.
        assert rhymes('Riko', 'Miko') is False
        assert set_conflict('Riko', 'Miko') is True

    def test_relaxation_unblocks_a_real_generated_pair(self) -> None:
        # The pair that motivated the rule: Yuriko was already on the Reiji
        # roster, which rejected every remaining female name in the pool.
        assert set_conflict('Yuriko', 'Reiko') is False


class TestSetConflict:
    def test_same_first_letter(self) -> None:
        assert set_conflict('Kaito', 'Kenji') is True

    def test_edit_distance_one_different_initial(self) -> None:
        assert set_conflict('Sana', 'Hana') is True

    def test_rhyme_different_initial(self) -> None:
        assert set_conflict('Naomi', 'Hitomi') is True

    def test_prefix_extension_different_initial(self) -> None:
        # "Iyo" vs "Chiyo" - edit distance 2, no shared initial, suffix "iyo"
        assert set_conflict('Iyo', 'Chiyo') is True

    def test_distinct_names_pass(self) -> None:
        assert set_conflict('Noboru', 'Akari') is False

    def test_distinct_names_pass_symmetric(self) -> None:
        assert set_conflict('Akari', 'Noboru') is False
