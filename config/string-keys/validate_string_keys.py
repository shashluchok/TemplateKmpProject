#!/usr/bin/env python3
"""Format + allowlist checker for string resource keys, used by .githooks/pre-commit.

Two modes:
    validate_string_keys.py KEY [KEY ...]
        Validate literal keys.

    validate_string_keys.py --files PATH [PATH ...] [--staged]
        Extract keys from resource files and validate them. With --staged, file
        content is read from the git index (what's about to be committed) via
        `git show`, instead of the working tree.

Supported file formats: Android / Compose Multiplatform resource XML
(<string>, <string-array>, <plurals> name="..."), and iOS .strings ("key" = "value";).

Format rules: [dev__](screen_<name>|dialog_<name>__)component[__component_type][__property_name]
This only checks the mechanical shape and the allowlist (allowlist.txt, same folder).
Whether component_type / property_name are semantically needed is a judgment call --
see the string-resource-keys skill / naming convention doc, not this script.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

WORD = r"[a-z0-9]+(?:_[a-z0-9]+)*"
SCREEN_DIALOG = rf"(?:screen|dialog)_{WORD}"
KEY_RE = re.compile(rf"^(?:dev__)?(?:{SCREEN_DIALOG}__)?{WORD}(?:__{WORD}){{0,2}}$")
DEV_FUSED_RE = re.compile(r"^dev_(?!_)")

XML_NAME_RE = re.compile(r'<(?:string|string-array|plurals)\s+[^>]*\bname="([^"]+)"')
STRINGS_KEY_RE = re.compile(r'^\s*"([^"]+)"\s*=', re.MULTILINE)

ALLOWLIST_PATH = Path(__file__).parent / "allowlist.txt"


def load_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.exists():
        return set()
    keys = set()
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            keys.add(line)
    return keys


def check_format(key: str) -> list[str]:
    """Return mechanical problems found in `key` (empty = OK)."""
    problems = []
    stripped = key.strip()
    if key != stripped:
        problems.append("leading/trailing whitespace")
    key = stripped

    if key != key.lower():
        problems.append("must be lowercase (found uppercase characters)")
    if "___" in key:
        problems.append("triple+ underscore -- use `_` inside a part, `__` between parts")
    if re.search(r"[^a-z0-9_]", key):
        problems.append("contains characters other than [a-z0-9_]")
    if key.startswith("_") or key.endswith("_"):
        problems.append("leading/trailing underscore")
    if DEV_FUSED_RE.match(key):
        problems.append(
            "`dev` must be its own part joined with `__` (e.g. `dev__...`), "
            "not fused with the next word using a single `_`"
        )
    if not KEY_RE.match(key):
        problems.append(
            "does not match the overall shape "
            "[dev__](screen_X|dialog_X)__component[__type][__property]"
        )
    return problems


def read_file(path: str, staged: bool) -> str | None:
    if not staged:
        return Path(path).read_text(encoding="utf-8")
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def extract_keys(path: str, content: str) -> list[str]:
    if path.endswith(".strings"):
        return STRINGS_KEY_RE.findall(content)
    return XML_NAME_RE.findall(content)


def report(key: str, problems: list[str]) -> bool:
    """Print the result for one key. Returns True if it failed."""
    if problems:
        print(f"FAIL  {key}")
        for p in problems:
            print(f"      - {p}")
        return True
    print(f"OK    {key}")
    return False


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("keys", nargs="*", help="literal keys to validate")
    parser.add_argument("--files", nargs="+", default=[], help="resource files to extract keys from")
    parser.add_argument("--staged", action="store_true", help="read --files from the git index, not the working tree")
    args = parser.parse_args(argv)

    if not args.keys and not args.files:
        parser.print_help()
        return 1

    allowlist = load_allowlist()
    any_failed = False
    any_checked = False

    for key in args.keys:
        any_checked = True
        problems = [] if key in allowlist else check_format(key)
        any_failed = report(key, problems) or any_failed

    for path in args.files:
        content = read_file(path, args.staged)
        if content is None:
            print(f"SKIP  {path} (not found -- probably deleted)")
            continue
        keys = extract_keys(path, content)
        if not keys:
            continue
        print(f"-- {path} --")
        for key in keys:
            any_checked = True
            problems = [] if key in allowlist else check_format(key)
            any_failed = report(key, problems) or any_failed

    if not any_checked:
        print("No string resource keys found to check.")

    if any_failed:
        print(
            "\nMechanical check only. Whether component_type / property_name should be "
            "present is a judgment call -- see the string-resource-keys naming convention."
        )

    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
