# CLI Contract: scatter_audit.py (108)

```
python3 scatter_audit.py <pool-map-path> [--json]
```

- `<pool-map-path>`: a pool map stem or path with/without extension (`pool/hamlets/inashiro`, `pool/hamlets/inashiro.json`, `pool/hamlets/inashiro.svg` all resolve to the same pair). Both `<stem>.json` and `<stem>.svg` must exist.
- `--json`: emit the Report as a single JSON object instead of human text.

## Exit codes

| code | meaning |
|---|---|
| 0 | parsed and adjudicated; zero violations |
| 1 | parsed and adjudicated; one or more violations (each listed) |
| 2 | usage error, missing artifact, missing `meta.ftpx`, or ZERO bases parsed (loud failure - a silent parser is forbidden) |

## Human output (default)

```
scatter_audit: pool/hamlets/inashiro
parsed: blade=218412 dot=11927 pine=1053 crown=NNN reed=NNNN (total 231392)
checked: families blade/dot/pine/crown vs keep-outs water+cutbank, crop  (reed: report-only)
violations: 0
density beyond water keep-out: 0-15px=772 15-30px=651 30-45px=747
```

On violations, one line each: `VIOLATION family=dot at (x, y) inside water+cutbank`.

## JSON output (`--json`)

The Report entity from data-model.md, verbatim keys: `map`, `families_checked`, `counts`, `violations`, `density_bands`.

## Stability promises

- Verdicts move with the engine's rules automatically (keep-outs are obtained from engine code at run time) - the contract is the FORMAT, never the margin values.
- The script never writes; committed pool bytes are untouched by any invocation.
