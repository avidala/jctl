#!/usr/bin/env python3
"""Update Homebrew formula url, sha256, and auto-generated resources block.

The resources block is delimited in the formula by:
    # BEGIN AUTO-GENERATED RESOURCES ...
    ...
    # END AUTO-GENERATED RESOURCES

Resources for jeepney and secretstorage are intentionally kept in the
`on_linux do` block in the formula and are filtered out of the poet output
to avoid duplication. The formula's own package ("jctl") is also filtered
out so brew audit doesn't complain about a self-referential resource.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# resources managed in the formula's on_linux block, not by poet
ON_LINUX_RESOURCES = {"jeepney", "secretstorage"}
# the formula's own package — poet emits it as a resource, brew audit rejects.
SELF_RESOURCE = "jctl"

BEGIN_MARKER = "# BEGIN AUTO-GENERATED RESOURCES"
END_MARKER = "# END AUTO-GENERATED RESOURCES"


def canonical_name(name: str) -> str:
    """Canonical PyPI/Homebrew resource name: lowercase, dots and underscores → hyphens.

    Brew audit rejects resource names containing dots/underscores (e.g.
    `jaraco.classes`, `pydantic_core`) — the canonical form is hyphenated
    (`jaraco-classes`, `pydantic-core`).
    """
    return name.lower().replace("_", "-").replace(".", "-")


def filter_resources(poet_output: str) -> str:
    """Drop resource blocks for names managed elsewhere in the formula."""
    drop = ON_LINUX_RESOURCES | {SELF_RESOURCE}
    pattern = re.compile(
        r'^\s*resource\s+"([^"]+)"\s+do\b.*?^\s*end\s*$\n?',
        re.MULTILINE | re.DOTALL,
    )

    def keep(match: re.Match[str]) -> str:
        return "" if canonical_name(match.group(1)) in drop else match.group(0)

    return pattern.sub(keep, poet_output)


def normalize_resource_names(text: str) -> str:
    """Rewrite each `resource "raw" do` line to use the canonical hyphenated name."""

    def rename(match: re.Match[str]) -> str:
        return f'{match.group(1)}"{canonical_name(match.group(2))}"{match.group(3)}'

    return re.sub(
        r'^(\s*resource\s+)"([^"]+)"(\s+do\b)',
        rename,
        text,
        flags=re.MULTILINE,
    )


def normalize_indent(text: str) -> str:
    """Normalize the resource block to `resource`/`end` at 2 spaces, inner lines at 4.

    Poet's output indent has varied across versions: older releases emitted at
    column 0, current releases emit pre-indented by 2 spaces. We dedent to a
    known baseline first, then prepend exactly 2 spaces to every non-empty
    line — this is correct regardless of poet's chosen base indent.
    """
    import textwrap

    dedented = textwrap.dedent(text)
    out = []
    for line in dedented.splitlines():
        out.append("" if not line.strip() else "  " + line)
    return "\n".join(out).rstrip() + "\n"


def replace_block(formula_text: str, new_body: str) -> str:
    """Splice `new_body` between BEGIN/END markers, idempotently.

    The substitution always emits exactly one blank line between the body and
    the END marker line, regardless of how many blank lines (if any) the prior
    state had. Without this, each rerun accumulates an extra blank line because
    `new_body` ends with `\n` and `\s*END_MARKER` greedily captured the prior
    gap — brew style `Layout/EmptyLines` then trips on the second run.
    """
    # group(2) ends with `\n` (the line break before the END marker's line);
    # group(3) is the END marker line's own indent + literal. `\s*` between
    # them is wrong — it greedily eats the END marker's indent, leaving the
    # marker at column 0.
    pattern = re.compile(
        rf"({re.escape(BEGIN_MARKER)}[^\n]*\n)(.*?\n)([ \t]*{re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(formula_text):
        sys.exit(f"error: markers not found in formula ({BEGIN_MARKER!r}/{END_MARKER!r})")
    # new_body ends with a single \n; we add one more \n to produce exactly one
    # blank line between the last `end` and the END marker.
    return pattern.sub(
        lambda m: f"{m.group(1)}{new_body.rstrip()}\n\n{m.group(3)}",
        formula_text,
    )


def update_url_sha(formula_text: str, url: str, sha256: str) -> str:
    formula_text, url_count = re.subn(
        r'^(\s*url\s+)"[^"]*"', rf'\1"{url}"', formula_text, count=1, flags=re.MULTILINE
    )
    formula_text, sha_count = re.subn(
        r'^(\s*sha256\s+)"[^"]*"', rf'\1"{sha256}"', formula_text, count=1, flags=re.MULTILINE
    )
    if url_count != 1 or sha_count != 1:
        sys.exit("error: failed to update url or sha256 line")
    return formula_text


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--formula", required=True, type=Path)
    p.add_argument("--url", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--resources", required=True, type=Path)
    args = p.parse_args()

    formula = args.formula.read_text()
    poet = args.resources.read_text()

    filtered = filter_resources(poet)
    renamed = normalize_resource_names(filtered)
    normalized = normalize_indent(renamed)

    formula = update_url_sha(formula, args.url, args.sha256)
    formula = replace_block(formula, normalized)

    args.formula.write_text(formula)


if __name__ == "__main__":
    main()
