"""CLI entry: `python3 -m l7r.diagram.hamletgen --seed 4 --households 15 --out wip/x`, or `--batch 24`.

`main` itself stays in `driver.py` - consumers reach `hamletgen.main`, and a `__main__.py` is not
imported by the package, so defining it here would put it out of their reach. Everything sits
INSIDE the entry guard, the same shape as `check_village/__main__.py`: the guard is what
`[tool.coverage.report] exclude_also` excludes, and a module-level import here would be a
statement no unit test can reach.
"""

if __name__ == "__main__":
    from l7r.diagram._invocation import guard

    # REFUSE unless invoked through this project's make (feature 127). At the TOP of the
    # entry point, never in a loop - the determination reads /proc and is cached per process.
    guard("l7r.diagram.hamletgen")
    from .driver import main

    raise SystemExit(main())
