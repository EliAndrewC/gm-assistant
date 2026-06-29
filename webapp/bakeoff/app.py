"""
Local blind-eval webapp for the synthesis prompt bakeoff.

Serves one blind comparison task at a time: the character sheet plus the four
tier outputs shuffled into opaque A/B/C/D cards. You pick the best (optionally
with quick-tags and notes), and the choice is appended to data/votes.jsonl. The
tier and model behind each card are never sent to the browser, so the evaluation
stays blind; analyze.py joins the votes back to the truth afterwards.

This app is deliberately standalone - it reads only the bakeoff data files and
has no dependency on the chargen package or the Gemini SDK.

Run (from webapp/):

    python3 -m bakeoff.app

Then open the printed URL. Progress persists; restart and you resume where you
left off. Re-voting a task overwrites your earlier vote for it.
"""

import json
import os
import time

import cherrypy
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bakeoff import config

_TEMPLATES = Environment(
    loader=FileSystemLoader(os.path.join(config.HERE, 'templates')),
    autoescape=select_autoescape(['html']),
)

#: Quick rubric tags offered on each screen (optional, multi-select).
QUICK_TAGS = [
    'great detail',
    'reconciled the tensions',
    'incoherent',
    'too generic',
    'wrong tone',
    'lore error',
    'contradicts the sheet',
    'too long',
]


def _load_tasks() -> list[dict]:
    tasks = []
    if os.path.exists(config.TASKS_PATH):
        with open(config.TASKS_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))
    return tasks


def _voted_ids() -> set[str]:
    voted = set()
    if os.path.exists(config.VOTES_PATH):
        with open(config.VOTES_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    voted.add(json.loads(line)['task_id'])
    return voted


def _append_vote(record: dict) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.VOTES_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def _collect_option_tags(form: dict) -> dict:
    """Pull per-option quick-tags out of the submitted form.

    Each option's checkboxes post under ``tag_<label>`` (e.g. ``tag_A``). A group
    with a single box checked arrives as a bare string; a group with none checked
    is absent from the form entirely.
    """
    out = {}
    for key, val in form.items():
        if not key.startswith('tag_'):
            continue
        label = key[len('tag_') :]
        out[label] = [val] if isinstance(val, str) else list(val)
    return out


class Bakeoff:
    @cherrypy.expose
    def index(self):
        tasks = _load_tasks()
        voted = _voted_ids()
        remaining = [t for t in tasks if t['task_id'] not in voted]
        done_n = len(tasks) - len(remaining)
        if not tasks:
            return _TEMPLATES.get_template('done.html').render(empty=True, done_n=0, total=0)
        if not remaining:
            return _TEMPLATES.get_template('done.html').render(
                empty=False, done_n=done_n, total=len(tasks)
            )
        task = remaining[0]
        # Hand the template only what is safe to show - never tier or model.
        options = [{'label': o['label'], 'text': o['text']} for o in task['options']]
        return _TEMPLATES.get_template('vote.html').render(
            task_id=task['task_id'],
            character_name=task['character_name'],
            character_sheet=task['character_sheet'],
            options=options,
            quick_tags=QUICK_TAGS,
            done_n=done_n,
            total=len(tasks),
            position=done_n + 1,
        )

    @cherrypy.expose
    def vote(self, task_id=None, choice=None, notes='', action='submit', **kwargs):
        option_tags = _collect_option_tags(kwargs)
        if action == 'submit' and choice:
            _append_vote(
                {
                    'task_id': task_id,
                    'choice': choice,
                    'notes': notes.strip(),
                    'option_tags': option_tags,
                    'skipped': False,
                    'ts': time.time(),
                }
            )
        elif action == 'skip':
            _append_vote(
                {
                    'task_id': task_id,
                    'choice': None,
                    'notes': notes.strip(),
                    'option_tags': option_tags,
                    'skipped': True,
                    'ts': time.time(),
                }
            )
        raise cherrypy.HTTPRedirect('/')


def _host() -> str:
    in_container = os.path.exists('/run/.containerenv') or os.path.exists('/.dockerenv')
    return '0.0.0.0' if in_container else '127.0.0.1'  # noqa: S104 - intentional in-container bind


def main() -> None:
    port = int(os.environ.get('BAKEOFF_PORT', '8090'))
    host = os.environ.get('BAKEOFF_HOST', _host())
    cherrypy.config.update({'server.socket_host': host, 'server.socket_port': port})
    print(f'bakeoff blind-eval running at http://{host}:{port}/')
    cherrypy.quickstart(Bakeoff())


if __name__ == '__main__':
    main()
