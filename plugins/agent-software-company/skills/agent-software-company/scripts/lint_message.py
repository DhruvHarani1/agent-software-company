#!/usr/bin/env python3
"""Validate AAP v1 comments. Style suggestions never affect exit status."""
import argparse
import re
import sys
from lib.protocol import validate_message


def lint(text: str) -> list[str]:
    return validate_message(text)


def style_warnings(text: str) -> list[str]:
    warnings = []
    if len(text) > 1800:
        warnings.append("long message: consider linking detailed evidence")
    if re.search(r"\b(i would like to|please note that|basically|just|really|simply|i think that)\b", text, re.I):
        warnings.append("consider shortening filler where clarity permits")
    return warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.file:
            with open(args.file, encoding="utf-8-sig") as handle:
                data = handle.read()
        else:
            data = sys.stdin.read()
    except OSError as exc:
        print(f"cannot read message: {exc}", file=sys.stderr)
        return 1
    errors = lint(data)
    for error in errors:
        print("error: " + error)
    for warning in style_warnings(data):
        print("warning: " + warning)
    if not errors:
        print("ok")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
