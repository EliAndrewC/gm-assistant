#!/usr/bin/env python3
"""Register the /look-up slash command in the GM's Discord server (feature 218).

    ./scripts/register_lookup_command.py

Idempotent: it PUTs the full command set for the listener application in each
guild named by `[lookup] guild_ids` in webapp/development-defaults.ini, so
running it twice changes nothing. A guild command appears at once, but only in
the guilds it is registered in.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webapp"))

from configobj import ConfigObj  # noqa: E402

from l7r.mention import gateway, load_fleet  # noqa: E402


def main() -> int:
    webapp = Path(__file__).resolve().parent.parent / "webapp"
    guilds = ConfigObj(str(webapp / "development-defaults.ini"))["lookup"]["guild_ids"]
    fleet = load_fleet()
    for guild in [guilds] if isinstance(guilds, str) else guilds:
        gateway.register_commands(fleet.listener, guild, fleet.listener_token, [gateway.LOOKUP_COMMAND])
        print(f"registered /{gateway.LOOKUP} for application {fleet.listener} in guild {guild}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
