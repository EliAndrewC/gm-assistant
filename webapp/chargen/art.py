"""
Art generation for NPC portraits using Google Gemini's image generation API.

This module generates character portrait prompts based on NPC attributes and
uses Gemini 2.5 Flash Image to create the artwork.
"""

import base64
import subprocess
import sys

from google import genai
from google.genai import types

from chargen import config
from chargen import constants as c


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


def trim_whitespace(image_data: bytes) -> bytes:
    """
    Trim whitespace from around an image using ImageMagick.

    Uses a 10% fuzz factor to handle near-white backgrounds from AI image
    generators, then adds back 10px of padding for a clean border.

    Args:
        image_data: The raw PNG image bytes

    Returns:
        bytes: The trimmed PNG image data with 10px padding
    """
    try:
        result = subprocess.run(
            [
                'convert',
                'png:-',
                '-fuzz',
                '10%',
                '-trim',
                '+repage',
                '-bordercolor',
                '#FFFFFF',
                '-border',
                '10',
                'png:-',
            ],
            input=image_data,
            capture_output=True,
        )

        if result.returncode != 0:
            print(f'Warning: Failed to trim image: {result.stderr.decode()}', file=sys.stderr)
            return image_data

        return result.stdout

    except FileNotFoundError:
        print('Warning: ImageMagick not installed, skipping whitespace trim', file=sys.stderr)
        return image_data


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

    # Random age on a bell curve centered around mid-30s, shifted by XP
    # Higher XP characters tend to be older (~5 years per 75 XP above baseline)
    import random

    age_options = [
        'late teens',
        'early 20s',
        'late 20s',
        'early 30s',
        'mid-30s',
        'late 30s',
        'early 40s',
        'late 40s',
        '50s',
        '60s or older',
    ]
    # Bell curve weights centered on index 4 (mid-30s)
    base_weights = [5, 15, 25, 35, 40, 35, 25, 15, 10, 5]

    # Calculate XP-based shift (50 XP = baseline, +75 XP = +1 age bracket)
    xp = character.get('xp', 50)
    xp_shift = (xp - 50) / 75.0

    # Pick from base distribution, then apply XP shift
    base_index = random.choices(range(len(age_options)), weights=base_weights)[0]
    shifted_index = base_index + xp_shift
    # Add a little randomness to the shift (+/- 0.5 brackets)
    shifted_index += random.uniform(-0.5, 0.5)
    # Clamp to valid range
    final_index = max(0, min(len(age_options) - 1, round(shifted_index)))
    age_desc = age_options[final_index]

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
        f'-> {pronoun.title()} is in {possessive} {age_desc}',
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
            'clothing and possessions being shown. The background must be completely blank '
            'without any features - use a solid white background.',
        ]
    )

    return '\n'.join(lines)


def generate_image(prompt: str) -> bytes:
    """
    Generate an image from a prompt using Google Imagen 4.

    Args:
        prompt: The text prompt describing the image to generate

    Returns:
        bytes: The PNG image data
    """
    from io import BytesIO

    client = _get_client()

    response = client.models.generate_images(
        model='imagen-4.0-generate-001',
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio='1:1',  # Square for portraits
        ),
    )

    if not response.generated_images:
        raise ValueError('No image was generated. The model may have refused the prompt.')

    # Get the PIL image and convert to PNG bytes
    img = response.generated_images[0].image
    buffer = BytesIO()
    img._pil_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()

    # Trim whitespace from around the generated image
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
