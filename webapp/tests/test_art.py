"""Tests for chargen.art.trim_whitespace - whitespace trimming of portraits."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image, UnidentifiedImageError

from chargen.art import TRIM_BORDER, trim_whitespace


def _png_bytes(img: Image.Image) -> bytes:
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def _open(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data)).convert('RGB')


def _make_bordered(
    content_size: int,
    margin: int,
    fill: tuple[int, int, int] = (255, 255, 255),
    block: tuple[int, int, int] = (10, 20, 30),
) -> Image.Image:
    """A white canvas with a solid color block inset by `margin` on every side."""
    total = content_size + 2 * margin
    img = Image.new('RGB', (total, total), fill)
    block_img = Image.new('RGB', (content_size, content_size), block)
    img.paste(block_img, (margin, margin))
    return img


def test_trims_white_border_to_content_plus_padding() -> None:
    src = _make_bordered(content_size=40, margin=30)
    result = _open(trim_whitespace(_png_bytes(src)))
    # 40px of content + TRIM_BORDER padding on each side, original margin gone.
    expected = 40 + 2 * TRIM_BORDER
    assert result.size == (expected, expected)


def test_padding_border_is_white() -> None:
    src = _make_bordered(content_size=40, margin=30)
    result = _open(trim_whitespace(_png_bytes(src)))
    assert result.getpixel((0, 0)) == (255, 255, 255)
    # Content survives in the middle.
    mid = result.size[0] // 2
    assert result.getpixel((mid, mid)) == (10, 20, 30)


def test_near_white_background_is_trimmed_via_fuzz() -> None:
    # Slightly off-white background (within the 10% fuzz) is still treated as bg.
    src = _make_bordered(content_size=40, margin=30, fill=(250, 248, 252))
    result = _open(trim_whitespace(_png_bytes(src)))
    expected = 40 + 2 * TRIM_BORDER
    assert result.size == (expected, expected)


def test_uniform_image_is_kept_and_bordered() -> None:
    src = Image.new('RGB', (50, 50), (255, 255, 255))
    result = _open(trim_whitespace(_png_bytes(src)))
    # Nothing to trim; whole image kept, border added.
    assert result.size == (50 + 2 * TRIM_BORDER, 50 + 2 * TRIM_BORDER)


def test_ignores_tiny_noise_specks() -> None:
    # Gemini image models scatter stray 2-3px specks on the white background.
    # The crop must ignore them and frame the real content, not inflate the box
    # to span from a corner speck to the figure.
    img = Image.new('RGB', (200, 200), (255, 255, 255))
    img.paste(Image.new('RGB', (40, 40), (10, 20, 30)), (80, 80))  # real content
    img.paste(Image.new('RGB', (2, 2), (0, 0, 0)), (5, 5))  # noise speck near corner
    result = _open(trim_whitespace(_png_bytes(img)))
    # Cropped to the 40px block + TRIM_BORDER, speck dropped.
    assert result.size == (40 + 2 * TRIM_BORDER, 40 + 2 * TRIM_BORDER)


def test_invalid_image_raises_rather_than_swallowing() -> None:
    # The old ImageMagick path swallowed failures and returned the input
    # untrimmed; the Pillow path must let a broken image surface.
    with pytest.raises(UnidentifiedImageError):
        trim_whitespace(b'not a real image')


# --- generate_prompt caste-awareness ---
# Peasants and monks must not come out dressed as samurai (kimono, topknot,
# swords); see infer_character_type in chargen.art.


def test_prompt_peasant_wears_work_clothes_not_kimono() -> None:
    from chargen.art import generate_prompt

    prompt = generate_prompt({'gender': 'male', 'tags': ['peasant'], 'age': 40})
    assert 'peasant commoner' in prompt
    assert 'roughspun' in prompt
    assert 'no samurai topknot' in prompt
    assert 'kimono' not in prompt.lower()


def test_prompt_monk_is_tonsured_monastic_without_swords() -> None:
    from chargen.art import generate_prompt

    prompt = generate_prompt(
        {'gender': 'female', 'order': 'Order of Daikoku', 'seat': '', 'age': 55}
    )
    assert 'Buddhist monk' in prompt
    assert 'shaved head' in prompt
    assert 'no swords and no armor' in prompt
    # The hair clause is suppressed for monks - the head is already shaved.
    assert 'unstyled black hair' not in prompt


def test_prompt_explicit_character_type_beats_dict_shape() -> None:
    from chargen.art import generate_prompt

    prompt = generate_prompt(
        {'gender': 'male', 'character_type': 'Peasant', 'school': 'hida bushi', 'age': 30}
    )
    assert 'roughspun' in prompt
    assert 'formal kimono' not in prompt


def test_prompt_samurai_wardrobe_unchanged() -> None:
    from chargen.art import generate_prompt

    prompt = generate_prompt({'gender': 'male', 'clan': 'crab', 'school': 'hida bushi', 'age': 30})
    assert 'a formal kimono and is not wearing armor' in prompt
    assert 'noble' in prompt
