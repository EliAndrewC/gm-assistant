"""
Art generation for NPC portraits using Google Gemini's image generation API.

This module generates character portrait prompts based on NPC attributes and
uses a Gemini image-generation model to create the artwork. The model id is
configurable via ``[gemini] image_model`` so future model migrations are a
config edit rather than a code change.
"""

import base64
from io import BytesIO

from google import genai
from google.genai import types
from PIL import Image, ImageOps

from chargen import config
from chargen import constants as c
from chargen.character import random_age

#: Gemini image-generation model used when ``[gemini] image_model`` is unset.
#: Imagen 4 (imagen-4.0-*) was retired by Google on 2026-08-17; the successor
#: family is the Gemini *-flash-image models, called via generate_content
#: rather than the Imagen-only generate_images endpoint.
#:
#: Per-image cost (as of 2026-07): image output bills at $60 / 1M tokens with a
#: fixed token count per resolution, so a single portrait at the default 1K
#: (1024x1024) output is ~$0.067. Other resolutions: 512px ~$0.045, 2K ~$0.101,
#: 4K ~$0.151. Text-prompt input is negligible and there is no image input in
#: the chargen flow. Batch mode would halve the 1K price (~$0.034), but the
#: chargen button generates one image interactively, so ~$0.07/image applies.
DEFAULT_IMAGE_MODEL = 'gemini-3.1-flash-image'


def _get_client():
    """Get a configured Gemini API client."""
    api_key = config.get('gemini', {}).get('api_key', '')
    if not api_key:
        raise ValueError(
            'Gemini API key not configured. Add api_key to [gemini] in '
            'development-secrets.ini. Get your API key from '
            'https://aistudio.google.com/app/apikey'
        )
    return genai.Client(api_key=api_key)


#: Fraction of the full 0-255 channel range within which a pixel counts as
#: background. Mirrors the ImageMagick `-fuzz 10%` this used to shell out to,
#: and absorbs the slightly-off-white backgrounds AI image generators produce.
TRIM_FUZZ = 0.10

#: White padding (in pixels) added back around the trimmed content.
TRIM_BORDER = 10

#: Connected mask regions smaller than this many pixels are treated as
#: generator noise - the stray 2-3px specks Gemini image models scatter on an
#: otherwise-white background - and ignored when computing the crop box. Real
#: figure parts (even a thin held sword) are orders of magnitude larger, so
#: this floor removes noise without clipping content.
TRIM_MIN_COMPONENT_AREA = 64


def trim_whitespace(image_data: bytes) -> bytes:
    """
    Trim the near-uniform background border from around an image.

    The background color is taken from the top-left pixel; any pixel within
    ``TRIM_FUZZ`` of it (per channel) is treated as background. The remaining
    foreground is split into connected components, tiny specks below
    ``TRIM_MIN_COMPONENT_AREA`` (generator background noise) are discarded, and
    the image is cropped to the union of what survives plus a ``TRIM_BORDER``
    white margin. Dropping the specks is what keeps a couple of stray edge
    pixels from inflating the crop box back to the full frame.

    Implemented with Pillow + OpenCV (both already dependencies) rather than
    shelling out to ImageMagick, so it works wherever the app runs without an
    external binary. Any failure to decode or process the image propagates
    rather than being swallowed - a broken trim should be visible, not
    silently skipped.

    Args:
        image_data: The raw PNG image bytes

    Returns:
        bytes: The trimmed PNG image data with a white border
    """
    import cv2
    import numpy as np

    img = Image.open(BytesIO(image_data)).convert('RGB')
    arr = np.asarray(img).astype(int)

    # Mask everything that differs from the background (top-left pixel) by more
    # than the fuzz threshold, per channel.
    background = arr[0, 0]
    threshold = int(TRIM_FUZZ * 255)
    mask = (np.abs(arr - background).max(axis=2) > threshold).astype(np.uint8)

    # Split into connected components and keep only those big enough to be real
    # content; isolated noise specks are dropped before computing the box.
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= TRIM_MIN_COMPONENT_AREA]

    if keep:
        x0 = int(min(stats[i, cv2.CC_STAT_LEFT] for i in keep))
        y0 = int(min(stats[i, cv2.CC_STAT_TOP] for i in keep))
        x1 = int(max(stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] for i in keep))
        y1 = int(max(stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] for i in keep))
        trimmed = img.crop((x0, y0, x1, y1))
    else:
        # Whole image is background (or only noise); keep it as-is.
        trimmed = img

    bordered = ImageOps.expand(trimmed, border=TRIM_BORDER, fill='#FFFFFF')

    out = BytesIO()
    bordered.save(out, format='PNG')
    return out.getvalue()


def generate_prompt(character: dict) -> str:
    """
    Generate an art prompt based on character attributes.

    Args:
        character: A dict containing character attributes (from Character.to_dict())

    Returns:
        str: A prompt suitable for image generation
    """
    # Determine gender pronouns
    gender = character.get('gender', 'male')
    pronoun = 'he' if gender == 'male' else 'she'
    possessive = 'his' if gender == 'male' else 'her'

    # Get clan colors if available
    clan = character.get('clan', '').title()
    clan_colors = c.CLAN_COLORS.get(clan, '')

    # The character's generated age drives the portrait, so the art matches
    # the sheet and the synthesized backstory. Rolling one here is only a
    # fallback for requests that predate the age field.
    age = character.get('age') or random_age(character.get('xp', 50))

    # Build character description from traits
    # Only traits that would be visually apparent in a portrait are included
    traits = character.get('traits', [])
    trait_descriptions = []
    for trait in traits:
        trait_lower = trait.lower()

        # Hair and facial hair
        if trait_lower in ['balding', 'bearded', 'long beard', 'bushy beard', 'mustachioed']:
            trait_descriptions.append(f'{pronoun} has {trait_lower} features')
        elif trait_lower == 'unusual haircut':
            trait_descriptions.append(f'{pronoun} has an unusual, distinctive hairstyle')

        # Body type
        elif trait_lower in ['thin', 'fat', 'short', 'tall']:
            trait_descriptions.append(f'{pronoun} is {trait_lower}')
        elif trait_lower == 'pregnant':
            trait_descriptions.append(f'{pronoun} is visibly pregnant')

        # Facial features
        elif trait_lower == 'big nose':
            trait_descriptions.append(f'{pronoun} has a notably large nose')
        elif trait_lower == 'big ears':
            trait_descriptions.append(f'{pronoun} has notably large ears')
        elif trait_lower == 'dark circles under eyes':
            trait_descriptions.append(f'{pronoun} has dark circles under {possessive} eyes')
        elif trait_lower == 'hairy arms':
            trait_descriptions.append(f'{pronoun} has notably hairy arms')
        elif trait_lower == 'sweaty':
            trait_descriptions.append(f'{pronoun} appears sweaty with glistening perspiration')

        # Injuries and marks
        elif trait_lower == 'scarred':
            trait_descriptions.append(f'{pronoun} has visible scars')
        elif trait_lower == 'tattooed':
            trait_descriptions.append(f'{pronoun} has visible tattoos')
        elif trait_lower == 'permanent wound':
            trait_descriptions.append(f'{pronoun} shows signs of an old injury')
        elif trait_lower == 'missing tooth':
            trait_descriptions.append(f'{pronoun} has a missing tooth')
        elif trait_lower == 'missing finger':
            trait_descriptions.append(f'{pronoun} has a missing finger')
        elif trait_lower == 'missing eye':
            trait_descriptions.append(f'{pronoun} has a missing eye')
        elif trait_lower == 'missing ear':
            trait_descriptions.append(f'{pronoun} has a missing ear')

        # Expressions
        elif trait_lower in ['jolly', 'happy', 'lighthearted', 'mirthful', 'upbeat']:
            trait_descriptions.append(f'{pronoun} has a warm, cheerful expression')
        elif trait_lower in ['dour', 'scowling', 'furrowed', 'frowny', 'squinty']:
            trait_descriptions.append(f'{pronoun} has a stern, serious expression')
        elif trait_lower == 'intense expression':
            trait_descriptions.append(f'{pronoun} has an intense, piercing expression')
        elif trait_lower == 'thoughtful expression':
            trait_descriptions.append(f'{pronoun} has a thoughtful, contemplative expression')
        elif trait_lower == 'pensive':
            trait_descriptions.append(f'{pronoun} has a pensive, contemplative expression')
        elif trait_lower == 'annoyed':
            trait_descriptions.append(f'{pronoun} has an irritated, annoyed expression')
        elif trait_lower == 'embittered':
            trait_descriptions.append(f'{pronoun} has a bitter, hardened expression')
        elif trait_lower == 'skeptical':
            trait_descriptions.append(f'{pronoun} has a skeptical, doubting expression')
        elif trait_lower == 'contemptuous':
            trait_descriptions.append(f'{pronoun} has a contemptuous, disdainful expression')
        elif trait_lower == 'kind eye':
            trait_descriptions.append(f'{pronoun} has kind, warm eyes')
        elif trait_lower == 'paranoid':
            trait_descriptions.append(f'{pronoun} has a wary, suspicious look')

        # Eyes and gaze
        elif trait_lower == 'eyes darting':
            trait_descriptions.append(f'{pronoun} has alert, darting eyes')
        elif trait_lower == 'always looking up':
            trait_descriptions.append(f'{pronoun} is gazing upward')
        elif trait_lower == 'always turning to the side':
            trait_descriptions.append(f'{possessive.title()} head is turned slightly to the side')
        elif trait_lower == 'flinching':
            trait_descriptions.append(f'{pronoun} has a flinching, guarded posture')
        elif trait_lower == 'twitchy':
            trait_descriptions.append(f'{pronoun} appears nervous and twitchy')

        # Posture
        elif trait_lower == 'military posture':
            trait_descriptions.append(f'{pronoun} has rigid, upright military posture')
        elif trait_lower == 'slouches':
            trait_descriptions.append(f'{pronoun} has a slouching posture')

        # Clothing and appearance
        elif trait_lower == 'garishly dressed':
            trait_descriptions.append(f'{pronoun} wears flamboyant, eye-catching clothing')
        elif trait_lower == 'vain':
            trait_descriptions.append(f'{pronoun} has an impeccably groomed appearance')
        elif trait_lower == 'unkempt':
            trait_descriptions.append(f'{pronoun} has a disheveled, untidy appearance')
        elif trait_lower in [
            'visibly torn and sewn clothing',
            'visibly patched clothing',
            'visibly stained clothing',
            'frayed seams and hems',
            'frayed collar',
            'faded clothes',
        ]:
            trait_descriptions.append(f'{pronoun} wears {trait_lower}')

        # Accessories and adornment
        elif trait_lower == 'fine makeup':
            trait_descriptions.append(f'{pronoun} wears elegant makeup')
        elif trait_lower == 'inexpert makeup':
            trait_descriptions.append(f'{pronoun} wears poorly applied makeup')
        elif trait_lower == 'jewelried':
            trait_descriptions.append(f'{pronoun} wears fine jewelry')
        elif trait_lower == 'wears charms and amulets':
            trait_descriptions.append(f'{pronoun} wears various charms and amulets')

        # Samurai-specific visual traits
        elif trait_lower == 'hides hands in sleeves':
            trait_descriptions.append(
                f'{possessive.title()} hands are hidden inside {possessive} sleeves'
            )
        elif trait_lower == 'sword-calloused':
            trait_descriptions.append(f'{pronoun} has rough, calloused hands')
        elif trait_lower == 'ink-stained cuticles':
            trait_descriptions.append(f'{pronoun} has ink stains on {possessive} fingers')

        # Collector trait - use the art-specific description
        elif trait_lower.startswith('collects '):
            collects_art = character.get('collects_art', '')
            if collects_art:
                trait_descriptions.append(f'{pronoun} has {collects_art}')

    # Determine clothing/role - always use kimono for samurai to avoid armor
    school = character.get('school', '').lower()
    if 'bushi' in school:
        clothing = 'a formal kimono and is not wearing armor'
    elif 'courtier' in school or 'diplomat' in school or 'artisan' in school:
        clothing = 'elegant formal court robes'
    elif 'merchant' in school:
        clothing = 'practical but quality merchant attire'
    else:
        clothing = 'a traditional kimono'

    # Check if character has fine makeup trait
    has_fine_makeup = 'fine makeup' in [t.lower() for t in traits]

    # Build the prompt
    lines = [
        f'A portrait of a {"noble" if clan else "person"} from {"the " + clan + " clan" if clan else "Rokugan"}.',
        '',
        f'-> {pronoun.title()} is {age} years old',
    ]

    if clan_colors:
        lines.append(f'-> {pronoun.title()} is wearing {clan} clan colors of {clan_colors}')

    lines.append(f'-> {pronoun.title()} is dressed in {clothing}')

    # For women, specify no makeup unless they have the fine makeup trait
    if gender == 'female' and not has_fine_makeup:
        lines.append(
            f'-> {pronoun.title()} is not wearing any makeup and has plain unstyled black hair'
        )

    if trait_descriptions:
        lines.append(f'-> {"; ".join(trait_descriptions)}')

    lines.extend(
        [
            '',
            'Make a colored, photo-realistic, life-like rendering, matching the Legend of '
            'the Five Rings setting of Rokugan, based on Edo-period Japan with period-appropriate '
            'clothing and possessions being shown. Show the figure as if cut out and isolated '
            'on a pure white (#FFFFFF) background: the entire area around the figure on all four '
            'sides must be uniform solid pure white. Do NOT render any floor, ground, surface, '
            'horizon line, studio backdrop, vignette, gradient, or cast shadow - the subject '
            'must appear to float on plain white with no setting of any kind.',
        ]
    )

    return '\n'.join(lines)


def _extract_image_bytes(response: types.GenerateContentResponse) -> bytes:
    """
    Pull the first inline image out of a generate_content response.

    Gemini image models return the picture as an inline_data part rather than
    a dedicated images list. If the model refused or answered with text only,
    that text is surfaced in the error to aid debugging.
    """
    text_parts: list[str] = []
    for candidate in response.candidates or []:
        content = candidate.content
        if content is None:
            continue
        for part in content.parts or []:
            blob = part.inline_data
            if blob is not None and blob.data:
                return blob.data
            if part.text:
                text_parts.append(part.text)

    detail = ' '.join(text_parts).strip()
    raise ValueError(
        'No image was generated. The model may have refused the prompt.'
        + (f' Model response: {detail}' if detail else '')
    )


def generate_image(prompt: str) -> bytes:
    """
    Generate an image from a prompt using a Gemini image-generation model.

    The model id comes from ``[gemini] image_model`` (defaulting to
    ``DEFAULT_IMAGE_MODEL``). Gemini image models are driven through
    generate_content with an IMAGE response modality - unlike the retired
    Imagen 4 endpoints, which used generate_images.

    Args:
        prompt: The text prompt describing the image to generate

    Returns:
        bytes: The PNG image data
    """
    client = _get_client()
    model = config.get('gemini', {}).get('image_model', '') or DEFAULT_IMAGE_MODEL

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(aspect_ratio='1:1'),  # Square for portraits
        ),
    )

    image_bytes = _extract_image_bytes(response)

    # Trim whitespace from around the generated image (also normalises to PNG).
    return trim_whitespace(image_bytes)


def generate_image_base64(prompt: str) -> str:
    """
    Generate an image and return it as a base64-encoded string.

    Args:
        prompt: The text prompt describing the image to generate

    Returns:
        str: Base64-encoded PNG image data (suitable for data: URLs)
    """
    image_bytes = generate_image(prompt)
    return base64.b64encode(image_bytes).decode('utf-8')


def get_headshot_crop(image_data: bytes) -> tuple[int, int, int, int]:
    """
    Detect the face in an image and return suggested headshot crop coordinates.

    Uses OpenCV's Haar cascade face detection to find the face, then expands
    the region to include hair and shoulders for a nice portrait crop.

    Args:
        image_data: The raw PNG image bytes

    Returns:
        tuple: (x, y, width, height) of the suggested crop region
    """
    import cv2
    import numpy as np

    # Decode image from bytes
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]

    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    # Convert to grayscale for detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))

    if len(faces) == 0:
        # Fallback: crop top-center portion of image
        crop_w = w // 2
        crop_h = h // 2
        crop_x = w // 4
        crop_y = 0
        return (int(crop_x), int(crop_y), int(crop_w), int(crop_h))

    # Pick the topmost face (smallest y value) - heads are usually at the top
    faces = sorted(faces, key=lambda f: f[1])
    fx, fy, fw, fh = faces[0]

    # Expand to create a nice headshot (space above head, include shoulders)
    expand_top = int(fh * 0.6)
    expand_bottom = int(fh * 0.8)
    expand_sides = int(fw * 0.6)

    crop_x = max(0, fx - expand_sides)
    crop_y = max(0, fy - expand_top)
    crop_x2 = min(w, fx + fw + expand_sides)
    crop_y2 = min(h, fy + fh + expand_bottom)

    # Convert numpy int32 to plain Python int for JSON serialization
    return (int(crop_x), int(crop_y), int(crop_x2 - crop_x), int(crop_y2 - crop_y))


def crop_headshot(image_data: bytes, x: int, y: int, width: int, height: int) -> bytes:
    """
    Crop an image to the specified region for use as a headshot/avatar.

    Args:
        image_data: The raw PNG image bytes
        x: Left edge of crop region
        y: Top edge of crop region
        width: Width of crop region
        height: Height of crop region

    Returns:
        bytes: The cropped PNG image data
    """
    import cv2
    import numpy as np
    from io import BytesIO

    # Decode image from bytes
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Crop
    cropped = img[y : y + height, x : x + width]

    # Encode back to PNG
    success, encoded = cv2.imencode('.png', cropped)
    if not success:
        raise ValueError('Failed to encode cropped image')

    return encoded.tobytes()
