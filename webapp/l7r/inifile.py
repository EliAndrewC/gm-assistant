"""The one way this project reads an INI file: ConfigObj, as chargen does.

`development-secrets.ini` writes values in quotes; ConfigObj strips them and configparser keeps
them (a quoted Gemini key reached Google with its quotes, twice). `tests/test_ini_reader.py` fails
on any configparser import and says why.
"""

from __future__ import annotations

from pathlib import Path

from configobj import ConfigObj

__all__ = ['read_ini']


def read_ini(path: Path | str) -> dict[str, dict[str, str]]:
    """`{section: {key: value}}`, keys in their own case, quotes stripped, `%` literal. Keys above
    the first section sit under `''`. A missing file is `{}`. An unquoted comma, which ConfigObj
    reads as a list, is refused with the fix in the message."""
    path = Path(path)
    if not path.exists():
        return {}
    config = ConfigObj(str(path), encoding='utf-8', interpolation=False)
    result: dict[str, dict[str, str]] = {}
    for name, value in config.items():
        section, items = (name, value.items()) if isinstance(value, dict) else ('', [(name, value)])
        result.setdefault(section, {})  # an empty section still exists, as ConfigObj says
        for key, item in items:
            if not isinstance(item, str):
                raise ValueError(
                    f'{path.name} [{section}] {key}: a value with a comma must be written in '
                    f'quotes, e.g. {key} = "a, b"'
                )
            result.setdefault(section, {})[key] = item
    return result
