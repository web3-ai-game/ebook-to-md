#!/usr/bin/env python3
"""Offline demo. No API key, no MongoDB, no cloud path."""

from pathlib import Path

SAMPLE = """# Sample chapter

This is a documentation excerpt, not a private book.

- Proposition 1. The converter reads a local file.
- Proposition 2. --demo never calls a model API.
"""


def main() -> int:
    out = Path("data/demo-output")
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "sample.md"
    dest.write_text(SAMPLE, encoding="utf-8")
    print("ebook-to-md demo")
    print("mode: offline")
    print("api: none")
    print("mongo: none")
    print(f"wrote: {dest}")
    print("---")
    print(SAMPLE.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
