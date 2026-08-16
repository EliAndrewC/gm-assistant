# Quickstart: scatter_audit (108)

For a settlement-review DELTA pass on a scatter/ground-cover change (or any session checking scrub placement):

```bash
cd .claude/skills/diagram
python3 scatter_audit.py pool/hamlets/inashiro          # human report, seconds
python3 scatter_audit.py pool/hamlets/inashiro --json   # machine-readable
```

- Exit 0 + `violations: 0` = every parsed scatter base honors the water/cut-bank and crop margins as the ENGINE currently defines them.
- Exit 1 = each violation is listed with position, family, and owning keep-out - crop those positions with `crop_map.py` and look.
- Exit 2 = the audit could not run (missing artifact, or zero bases parsed - suspect styling drift in the engine's scatter emission, and treat the audit as BROKEN, not the map as clean).
- The density bands are for the sterile-halo judgment: roughly flat bands beyond the keep-out mean scrub resumes at natural density; a depressed near band means over-clearing.

Reviewer independence: run it yourself, read its output yourself. The author's own audit run is a claim to re-verify, not evidence. The script only covers the water/cut-bank + crop families - its `checked:` line says exactly what ran; everything else (halos, corridors, form/legibility, place-ness) is still yours.
