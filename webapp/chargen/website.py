import os
import json
import base64
import re
import traceback
from functools import wraps

import jinja2
import cherrypy

from chargen import config, op, art, constants as c
from chargen.character import Character
from chargen import ministry

# `current_user` is supplied by the l7r auth tool when chargen is mounted
# inside the l7r toolkit. We import it lazily so chargen still imports
# standalone (the legacy `cherryd --import chargen` path), in which case
# every request looks anonymous to the templates.
try:
    from l7r.auth_routes import current_user as _l7r_current_user
except ImportError:  # pragma: no cover — only hit by the standalone path

    def _l7r_current_user():  # type: ignore[no-redef]
        return None


jinja_loader = jinja2.FileSystemLoader(os.path.join(c.HERE, 'templates'))
jinja_env = jinja2.Environment(loader=jinja_loader)


def ajax(func):
    """
    Decorator which takes a function and converts it to one which converts its
    return value to JSON and sets the Content-Type response header.
    """

    @cherrypy.expose
    @wraps(func)
    def wrapped(*args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps(func(*args, **kwargs)).encode('UTF-8')

    return wrapped


# Sections that ConfigObj merges in from development-secrets.ini and that
# the chargen frontend does NOT need. Filtered out before the config dict
# is serialized into the HTML so secrets don't leak via view-source.
# Add new secret sections here whenever development-secrets.ini grows.
_SECRET_CONFIG_SECTIONS = frozenset(
    {
        'auth',
        'discord',
        'discord_whitelist',
        'gemini',
        'gm_whitelist',
        'obsidian_portal',
    }
)


def _safe_config_for_frontend() -> dict:
    """Return the chargen config dict with secret sections stripped."""
    full = config.dict()
    return {k: v for k, v in full.items() if k not in _SECRET_CONFIG_SECTIONS}


class Root:
    @cherrypy.expose
    def index(self):
        return (
            jinja_env.get_template('index.html')
            .render(
                {
                    'config': _safe_config_for_frontend(),
                    'types': list(Character.types().keys()),
                    'current_user': _l7r_current_user(),
                }
            )
            .encode('UTF-8')
        )

    @ajax
    def generate(self, type: str, **params):
        """
        This is invoked when the frontend wants to make a character; we return a
        randomly generated character of the given type (e.g. "samurai").
        """
        return Character.types()[type](**params).to_dict()

    @ajax
    def upload(self, **kwargs):
        # Handle JSON POST data
        if cherrypy.request.method == 'POST' and cherrypy.request.headers.get(
            'Content-Type', ''
        ).startswith('application/json'):
            body = cherrypy.request.body.read()
            data = json.loads(body)
        else:
            data = kwargs

        name = data.get('name', '')
        summary = data.get('summary', '')
        public = data.get('public', '')
        private = data.get('private', '')
        tags = data.get('tags', '')
        image_data = data.get('image_data', '')
        image_embed = ''  # will be set if we upload the image

        slug = name.lower().replace(' ', '-')
        tags_list = list(filter(bool, map(str.strip, tags.split(','))))

        description = public

        # If we have image data, upload it for both avatar and bio
        avatar_upload_id = ''
        headshot_crop = data.get('headshot_crop', None)
        if image_data:
            try:
                # Decode base64 image data
                image_bytes = base64.b64decode(image_data)

                # Create a safe filename from the character name
                safe_name = re.sub(r'[^a-zA-Z0-9]', '', name.replace(' ', ''))
                filename = f'{safe_name}.png'

                # Create headshot crop for avatar if crop coordinates provided
                if headshot_crop:
                    headshot_bytes = art.crop_headshot(
                        image_bytes,
                        int(headshot_crop['x']),
                        int(headshot_crop['y']),
                        int(headshot_crop['width']),
                        int(headshot_crop['height']),
                    )
                else:
                    headshot_bytes = image_bytes

                # Upload headshot as avatar (for character thumbnail)
                avatar_info = op.upload_avatar(headshot_bytes, filename)
                avatar_upload_id = str(avatar_info.get('id', ''))

                # Upload full image as file (for bio embed)
                file_info = op.upload_image(image_bytes, filename)
                file_id = file_info.get('id')

                if file_id:
                    image_embed = f'[[File:{file_id} | class=media-item-align-none | {filename}]]'

            except Exception as e:
                cherrypy.log(f'Failed to upload image: {e}\n{traceback.format_exc()}')
                raise

        r = op.create_character(
            name,
            summary=summary,
            tags=tags_list,
            description=description,
            bio=image_embed,
            gm_info=private,
            avatar_upload_id=avatar_upload_id,
        )
        return {
            'view_url': config['campaign_url'] + '/characters/' + slug,
            'edit_url': config['campaign_url'] + '/characters/' + slug + '/edit',
        }

    @ajax
    def art_prompt(self, **character_data):
        """
        Generate a suggested art prompt based on character data.
        The frontend sends the character dict and we return a prompt string.
        """
        # Convert string representations back to appropriate types
        if 'traits' in character_data and isinstance(character_data['traits'], str):
            character_data['traits'] = [
                t.strip() for t in character_data['traits'].split(',') if t.strip()
            ]
        if 'xp' in character_data:
            character_data['xp'] = int(character_data['xp'])
        return {'prompt': art.generate_prompt(character_data)}

    @ajax
    def generate_art(self, prompt: str):
        """
        Generate an image from the given prompt.
        Returns base64-encoded image data plus suggested headshot crop coordinates.
        """
        try:
            image_data = art.generate_image_base64(prompt)
            # Get suggested headshot crop from the generated image
            image_bytes = base64.b64decode(image_data)
            crop_x, crop_y, crop_w, crop_h = art.get_headshot_crop(image_bytes)
            return {
                'image': image_data,
                'headshot_crop': {'x': crop_x, 'y': crop_y, 'width': crop_w, 'height': crop_h},
                'error': None,
            }
        except Exception as e:
            return {'image': None, 'headshot_crop': None, 'error': str(e)}

    @cherrypy.expose
    def ministry(self):
        """Bulk ministry generator page."""
        return (
            jinja_env.get_template('ministry.html')
            .render(
                {
                    'config': _safe_config_for_frontend(),
                    'current_user': _l7r_current_user(),
                }
            )
            .encode('UTF-8')
        )

    @ajax
    def ministry_generate(self, base_rank: str, clan='', family='', house=''):
        """
        Generate 6 ministers for bulk ministry creation.
        Returns a list of 6 character dicts.
        """
        roster = ministry.generate_ministry_roster(
            rank=int(base_rank), clan=clan or None, family=family or None, house=house or None
        )
        return {'characters': roster}

    @ajax
    def ministry_upload_bulk(self, **kwargs):
        """
        Upload multiple characters in sequence.
        Expects JSON POST with 'characters' array.
        Returns status for each character.
        """
        if cherrypy.request.method == 'POST':
            body = cherrypy.request.body.read()
            data = json.loads(body)
        else:
            data = kwargs

        characters = data.get('characters', [])
        results = []

        for char_data in characters:
            try:
                name = char_data.get('name', '')
                summary = char_data.get('summary', '')
                public = char_data.get('public', '')
                private = char_data.get('private', '')
                tags = char_data.get('tags', [])
                if isinstance(tags, str):
                    tags = list(filter(bool, map(str.strip, tags.split(','))))
                image_data = char_data.get('image_data', '')

                image_embed = ''
                avatar_upload_id = ''
                headshot_crop = char_data.get('headshot_crop', None)
                if image_data:
                    try:
                        image_bytes = base64.b64decode(image_data)
                        safe_name = re.sub(r'[^a-zA-Z0-9]', '', name.replace(' ', ''))
                        filename = f'{safe_name}.png'

                        # Create headshot crop for avatar if crop coordinates provided
                        if headshot_crop:
                            headshot_bytes = art.crop_headshot(
                                image_bytes,
                                int(headshot_crop['x']),
                                int(headshot_crop['y']),
                                int(headshot_crop['width']),
                                int(headshot_crop['height']),
                            )
                        else:
                            headshot_bytes = image_bytes

                        # Upload headshot as avatar (for character thumbnail)
                        avatar_info = op.upload_avatar(headshot_bytes, filename)
                        avatar_upload_id = str(avatar_info.get('id', ''))

                        # Upload full image as file (for bio embed)
                        file_info = op.upload_image(image_bytes, filename)
                        file_id = file_info.get('id')
                        if file_id:
                            image_embed = (
                                f'[[File:{file_id} | class=media-item-align-none | {filename}]]'
                            )
                    except Exception as e:
                        cherrypy.log(f'Failed to upload image for {name}: {e}')
                        # Continue without image

                response = op.create_character(
                    name,
                    summary=summary,
                    tags=tags,
                    description=public,
                    bio=image_embed,
                    gm_info=private,
                    avatar_upload_id=avatar_upload_id,
                )

                slug = name.lower().replace(' ', '-')
                results.append(
                    {
                        'success': True,
                        'name': name,
                        'view_url': config['campaign_url'] + '/characters/' + slug,
                        'edit_url': config['campaign_url'] + '/characters/' + slug + '/edit',
                        'error': None,
                    }
                )
            except Exception as e:
                cherrypy.log(
                    f'Failed to upload {char_data.get("name", "unknown")}: {e}\n{traceback.format_exc()}'
                )
                results.append(
                    {'success': False, 'name': char_data.get('name', 'Unknown'), 'error': str(e)}
                )

        return {'results': results}


cherrypy.tree.mount(Root(), '/')
