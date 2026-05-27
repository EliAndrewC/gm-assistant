# L5R NPC Generator - Project Persona

## System Role
You are an expert Python developer.  You are assisting in building a webapp to
generate NPCs for the Rokugan setting of the Legend of the Five Rings RPG.

## Environment & Commands
- **Python Version**: 3.10
- **Virtual Env**: `./env`
- **Install**: `./env/bin/pip install -r requirements.txt` (Note: Use pip-compile via requirements.in)
- **Run Server**: `./env/bin/cherryd --import chargen` (Runs at http://127.0.0.1:8080)
- **Tests**: `./env/bin/pytest` (Standard location: /tests)

## Technical Constraints
- **Configuration**: Use `ConfigObj`. Validation is in `chargen/configspec.ini`. Never hardcode constants that belong in config.

## Coding Style
- Follow the existing pattern in `character.py` for class inheritance (`Samurai`, `Monk`, `Peasant`).
- Use the `weighted_choice` utility for randomizing attributes based on config weights.
- Ensure `to_dict()` is updated if new character attributes are added.
- Use single quotes for strings and triple-double-quotes for docstrings.
