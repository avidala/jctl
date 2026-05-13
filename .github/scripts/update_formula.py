#!/usr/bin/env python3
"""Update Homebrew formula url, sha256, and auto-generated resources block.

The resources block is delimited in the formula by:
    # BEGIN AUTO-GENERATED RESOURCES ...
    ...
    # END AUTO-GENERATED RESOURCES

Resources for jeepney and secretstorage are intentionally kept in the
`on_linux do` block in the formula and are filtered out of the poet output
to avoid duplication.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# resources managed in the formula's on_linux block, not by poet
ON_LINUX_RESOURCES = {"jeepney", "secretstorage"}

BEGIN_MARKER = "# BEGIN AUTO-GENERATED RESOURCES"
END_MARKER = "# END AUTO-GENERATED RESOURCES"


def filter_resources(poet_output: str) -> str:
    """Drop resource blocks for names managed elsewhere in the formula."""
    pattern = re.compile(
        r'^\s*resource\s+"([^"]+)"\s+do\b.*?^\s*end\s*$\n?',
        re.MULTILINE | re.DOTALL,
    )

    def keep(match: re.Match[str]) -> str:
        name = match.group(1).lower().replace("_", "-")
        return "" if name in ON_LINUX_RESOURCES else match.group(0)

    return pattern.sub(keep, poet_output)


def normalize_indent(text: str) -> str:
    """Prepend the 2-space class-body indent to every non-empty line.

    Poet emits resources at column 0 (with inner lines at 2 spaces). The formula
    needs them shifted right by 2 so `resource`/`end` land at 2 spaces and inner
    `url`/`sha256` lines land at 4 spaces.
    """
    out = []
    for line in text.splitlines():
        out.append("" if not line.strip() else "  " + line)
    return "\n".join(out).rstrip() + "\n"


def replace_block(formula_text: str, new_body: str) -> str:
    pattern = re.compile(
        rf"({re.escape(BEGIN_MARKER)}[^\n]*\n)(.*?)(\s*{re.escape(END_MARKER)})",
        re.DOTALL,
    )
    if not pattern.search(formula_text):
        sys.exit(f"error: markers not found in formula ({BEGIN_MARKER!r}/{END_MARKER!r})")
    return pattern.sub(lambda m: f"{m.group(1)}{new_body}{m.group(3)}", formula_text)


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
    normalized = normalize_indent(filtered)

    formula = update_url_sha(formula, args.url, args.sha256)
    formula = replace_block(formula, normalized)

    args.formula.write_text(formula)


if __name__ == "__main__":
    main()
