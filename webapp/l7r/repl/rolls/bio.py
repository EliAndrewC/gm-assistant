"""Splice a roll line into an Obsidian Portal character bio.

The GM was specific about placement: *"we would put this in the character bio
section of Obsidian Portal directly underneath their portrait."*

"Underneath the portrait" has a concrete anchor. Every character record in the
campaign opens its public `bio` with a Textile file embed carrying the full-body
portrait (research.md R10):

    [[File:1515940  | class=media-item-align-none | Tsuruchi.png]]

so the line goes immediately after that embed. A record with no embed - the GM has
not portrait-ed it yet - gets the line at the top instead, which is the same
intent applied to a record whose portrait is absent rather than elsewhere.

Everything already in the bio is preserved byte for byte (FR-015). This module
never rewrites, reflows, or "tidies" the GM's existing text; it inserts one line
and returns the whole body.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence

#: The Textile file embed. Obsidian Portal writes it with irregular internal
#: spacing (`[[File:1515940  | class=...`), so the pattern is deliberately loose
#: about whitespace and does not assume the trailing filename is present.
#:
#: Matched against ONE LINE at a time rather than against the whole body with
#: `re.M`. Measured 2026-08-28: an anchored `\s*$` pattern split the record's CRLF
#: line endings - `$` matches before the `\n` while `\s*` had already eaten the
#: `\r`, so the insert landed mid-newline and produced `\r\n\r\r\n`. Working
#: line-wise makes the offset arithmetic unnecessary instead of merely correct.
EMBED = re.compile(r'\[\[File:[^\]]*\]\]')

#: Obsidian Portal bodies use CRLF (see the intake workflow in CLAUDE.md). Matching
#: the surrounding convention keeps a diff of the record readable.
NEWLINE = '\r\n'


def already_present(bio: str, line: str) -> bool:
    """True when this exact line is already in the bio.

    The write path is re-runnable - a failed OP call is retried, and a poller can
    close the same conversation twice if the GM is quick - so an idempotent check
    is what keeps a retry from doubling the line (FR-015).
    """
    target = line.strip()
    return any(existing.strip() == target for existing in bio.splitlines())


def remove_lines(bio: str, lines: Sequence[str]) -> str:
    """Drop each of `lines` from the body ONCE, leaving everything else untouched.

    Once, and the FIRST occurrence: the lines being removed are the open
    conversation's own block, which always sits directly under the portrait, above
    every earlier conversation. An earlier conversation can hold an identical line -
    the same heading, or `Jimen etiquette: 25` twice - and removing every copy would
    delete it from that conversation's record.
    """
    targets = Counter(line.strip() for line in lines if line.strip())
    if not targets:
        return bio
    # Each line was spliced WITH a blank line after it, so removing only the line
    # leaves the blank behind and the body grows a stray newline on every rewrite.
    # Measured 2026-08-28 before this: three writes produced `\r\n\r\n\r\n`.
    source = bio.splitlines(keepends=True)
    kept: list[str] = []
    index = 0
    while index < len(source):
        if targets[source[index].strip()] > 0:
            targets[source[index].strip()] -= 1
            index += 1
            if index < len(source) and not source[index].strip():
                index += 1
            continue
        kept.append(source[index])
        index += 1
    return ''.join(kept)


def rewrite(bio: str, previous: Sequence[str], lines: Sequence[str]) -> str:
    """Replace the block this conversation wrote before with its current form.

    The conversation writes as it goes, so the same conversation writes repeatedly
    with a growing set of rolls, and possibly a growing set of SKILLS - one line
    each. Removing what we wrote last time and re-splicing keeps exactly this
    conversation's lines under the portrait, with everything else in the bio
    untouched.

    Lines are inserted in reverse because `insert` always puts a line directly under
    the embed, so the last one inserted ends up first.

    `insert`, not `splice`: a line an EARLIER conversation already wrote is still
    this conversation's line to write. Measured 2026-09-29: with `splice`'s "already
    present" check, a second conversation's `h4.` heading of the same name, or its
    own `Jimen etiquette: 25`, was silently never written.
    """
    body = remove_lines(bio, previous)
    for line in reversed([x for x in lines if x.strip()]):
        body = insert(body, line)
    return body


def splice(bio: str, line: str) -> str:
    """Return `bio` with `line` inserted directly under the portrait embed.

    Idempotent: a line already present is not added again. An empty bio becomes
    just the line.
    """
    if not line.strip():
        raise ValueError('refusing to splice an empty line into a bio')
    if already_present(bio, line):
        return bio
    return insert(bio, line)


def insert(bio: str, line: str) -> str:
    """`splice` without the idempotency check: `line` goes in even if present."""
    if not line.strip():
        raise ValueError('refusing to splice an empty line into a bio')
    if not bio.strip():
        return line

    # Anchor on the FIRST embed, not the last. A bio may carry further images
    # further down (a map, a mon, a second portrait), and "underneath their
    # portrait" means the one at the top of the record, not the last picture in it.
    lines = bio.splitlines(keepends=True)
    index = next((i for i, text in enumerate(lines) if EMBED.search(text)), None)
    if index is None:
        return line + NEWLINE + NEWLINE + bio

    head = ''.join(lines[: index + 1])
    tail = ''.join(lines[index + 1 :])
    if not head.endswith(('\n', '\r')):
        head += NEWLINE
    return head + NEWLINE + line + NEWLINE + tail
