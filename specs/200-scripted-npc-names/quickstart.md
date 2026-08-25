# Quickstart

```bash
# pick names from the skill (refreshes the campaign cache via OAuth if older than 1h)
( cd /gm-assistant/.claude/skills/name && python3 pick_name.py f 3 )
( cd /gm-assistant/.claude/skills/name && python3 pick_name.py --refresh m )   # force a refresh

# roll a character from the engine with a pinned gender and an avoid list
( cd /gm-assistant/webapp && python3 -c "
from chargen import opcache; opcache.refresh_if_stale()
from chargen.character import Samurai
a = Samurai(base_rank=3, clan='crab', gender='female')
b = Samurai(base_rank=3, clan='crab', gender='female', avoid=[a.personal_name])
print(a.full_name, '|', b.full_name)" )

# verify the cache picked up a creation
python3 -c "import json; d=json.load(open('/gm-assistant/webapp/opcache/characters.json')); print(len(d))"
```
