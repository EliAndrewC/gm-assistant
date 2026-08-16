"""How a pool map gets (re)generated, cached, rendered and indexed.

The build side of the skill, as opposed to the drawing side (`settlement/`, `waterfields/`,
`hamletgen/`, `compound.py`) and the checking side (`check_village/`). See CLAUDE.md in this
directory. Run these as modules from the skill root:

    python3 -m pipeline.regen pool/hamlets/sawada.gen.py
"""
