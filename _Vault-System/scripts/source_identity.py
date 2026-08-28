#!/usr/bin/env python3
"""Calculate deterministic source identity fields without modifying the source."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_identity(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"source file not found: {resolved}")
    digest = sha256_file(resolved)
    return {
        "source_id": f"src-{digest[:16]}",
        "content_hash": f"sha256:{digest}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate source_id and SHA-256."
    )
    parser.add_argument("path", type=Path, help="source file to inspect")
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of YAML lines"
    )
    args = parser.parse_args()

    try:
        identity = source_identity(args.path)
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(identity, ensure_ascii=False, indent=2))
    else:
        for key, value in identity.items():
            print(f'{key}: "{value}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
