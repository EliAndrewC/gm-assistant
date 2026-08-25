# Data Model

- **Pool entry** (`l7r.names.GeneratedName`): `name`, `gender` (`male`|`female`), `format`, `explanation`, `peasant`, `notes`. Read from `pool-male.jsonl` / `pool-female.jsonl`. Unchanged.
- **Cache entry** (`opcache` JSON, id-keyed): `updated_at`, `name`, `tags`, `bio`, `game_master_info`. Unchanged shape; new atomic write.
- **Used given name**: `entry['name'].split()[-1]` for every cache entry with a non-empty name. Derived at read time (`opcache.used_given_names`), memoized by file mtime, unioned with the in-process `constants.USED_NAMES`.
- **Avoid list**: given names already picked in the current set; strict rule (`set_conflict`).
- **Pick**: `namepool.pick_name(gender, pool, used, avoid, rng)` -> `GeneratedName`; candidates = pool[gender] minus `is_too_similar(name, used)` minus any `set_conflict(name, a)` for a in avoid; empty -> `NamePoolExhausted(gender, n_pool, n_used, n_avoid)`.
