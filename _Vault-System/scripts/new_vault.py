#!/usr/bin/env python3
"""Create a new standardized child Vault without placing files in Inbox."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path

from validate_vault import validate_vault
from validate_workspace import MAP_RE, registry_block, validate_workspace


INBOX_CATEGORIES = (
    "00-Unsorted",
    "Personal-Private",
    "Books-Courses",
    "Media",
    "Articles-Web",
    "Papers-Reports",
    "Project-Materials",
)
VAULT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,63}$")


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def render_template(path: Path, values: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8-sig")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
    if unresolved:
        raise ValueError(
            f"unresolved scaffold placeholders in {path.name}: "
            + ", ".join(unresolved)
        )
    return text


def build_vault(build_root: Path, system: Path, entry: dict[str, object]) -> None:
    for relative in (
        ".obsidian",
        "1-Inbox",
        "2-AI work",
        "3-Wiki",
        "4-Outputs",
        "Templates",
        "assets",
    ):
        (build_root / relative).mkdir(parents=True, exist_ok=True)
    for category in INBOX_CATEGORIES:
        (build_root / "1-Inbox" / category).mkdir()

    for source in (system / "Templates-Source").iterdir():
        if source.is_file():
            shutil.copy2(source, build_root / "Templates" / source.name)
    for source in (system / "Config-Source").iterdir():
        if source.is_file():
            shutil.copy2(source, build_root / ".obsidian" / source.name)

    values = {
        "DATE": date.today().isoformat(),
        "VAULT_NAME": str(entry["name"]),
        "DISPLAY_NAME": str(entry["display_name"]),
        "SCOPE": str(entry["scope"]),
        "EXCLUDES": str(entry["excludes"]),
        "ROUTE_QUESTION": str(entry["route_question"]),
        "PRIVACY_RULE": (
            "只有用户明确要求处理本 Vault 时，Agent 才可进入本目录或读取正文。"
            if entry["sensitivity"] == "private"
            else ""
        ),
    }
    scaffold = system / "Vault-Scaffold"
    rendered = {
        build_root / "AGENTS.md": scaffold / "AGENTS.md.template",
        build_root / "知识库首页.md": scaffold / "知识库首页.md.template",
        build_root / "3-Wiki" / "index.md": scaffold / "index.md.template",
        build_root / "3-Wiki" / "log.md": scaffold / "log.md.template",
    }
    for destination, template in rendered.items():
        destination.write_text(
            render_template(template, values), encoding="utf-8", newline="\n"
        )
    shutil.copy2(
        scaffold / "知识库视图.base",
        build_root / "3-Wiki" / "知识库视图.base",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create and register a standardized child Obsidian Vault."
    )
    parser.add_argument("--name", required=True, help="ASCII Vault directory name")
    parser.add_argument("--display-name", required=True, help="human-readable title")
    parser.add_argument("--scope", required=True, help="what this Vault owns")
    parser.add_argument("--excludes", required=True, help="what belongs elsewhere")
    parser.add_argument(
        "--route-question",
        required=True,
        help="future-use question that selects this Vault",
    )
    parser.add_argument(
        "--sensitivity",
        choices=("public", "internal", "private"),
        default="internal",
        help="Vault-level privacy boundary",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="workspace root; defaults to the parent of _Vault-System",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="show the plan without writing"
    )
    args = parser.parse_args()

    if not VAULT_NAME_RE.fullmatch(args.name):
        parser.error("--name must use ASCII letters, digits, and hyphens")
    root = args.workspace.resolve()
    system = root / "_Vault-System"
    target = root / args.name
    if not root.is_dir() or not system.is_dir():
        parser.error(f"standardized workspace not found: {root}")
    if target.exists():
        parser.error(f"target already exists: {target}")

    registry_path = system / "vault-registry.json"
    map_path = system / "vault-map.md"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read vault registry: {exc}")
    vaults = registry.get("vaults") if isinstance(registry, dict) else None
    if not isinstance(vaults, list):
        parser.error("vault registry is missing its vaults list")
    if any(isinstance(item, dict) and item.get("name") == args.name for item in vaults):
        parser.error(f"Vault is already registered: {args.name}")

    pre_errors, pre_warnings = validate_workspace(root)
    if pre_errors:
        print("Workspace must pass validation before a new Vault is created.")
        for error in pre_errors:
            print(f"ERROR: {error}")
        return 1
    for warning in pre_warnings:
        print(f"WARNING: {warning}")

    entry: dict[str, object] = {
        "name": args.name,
        "display_name": args.display_name,
        "sensitivity": args.sensitivity,
        "daily_notes_enabled": False,
        "scope": args.scope.rstrip("。"),
        "excludes": args.excludes.rstrip("。"),
        "route_question": args.route_question.rstrip("。"),
    }
    new_registry = dict(registry)
    new_vaults = list(vaults) + [entry]
    new_registry["vaults"] = new_vaults
    registry_text = json.dumps(new_registry, ensure_ascii=False, indent=2) + "\n"

    map_text = map_path.read_text(encoding="utf-8-sig")
    if not MAP_RE.search(map_text):
        parser.error("vault-map.md is missing registry markers")
    new_map = MAP_RE.sub(registry_block(new_vaults), map_text, count=1)

    print(f"New Vault: {target}")
    print(f"Sensitivity: {args.sensitivity}")
    print("Inbox: empty standard category directories only")
    print("Daily Notes: disabled")
    if args.dry_run:
        print("DRY RUN: no files changed")
        return 0

    build_root = Path(tempfile.mkdtemp(prefix=f".{args.name}-build-", dir=root))
    original_registry = registry_path.read_text(encoding="utf-8-sig")
    original_map = map_text
    committed = False
    try:
        build_vault(build_root, system, entry)
        build_errors, build_warnings, _, _ = validate_vault(build_root)
        for warning in build_warnings:
            print(f"WARNING: {warning}")
        if build_errors:
            for error in build_errors:
                print(f"ERROR: {error}")
            raise RuntimeError("generated Vault failed validation")

        build_root.replace(target)
        committed = True
        atomic_write(registry_path, registry_text)
        atomic_write(map_path, new_map)

        final_errors, final_warnings = validate_workspace(root)
        for warning in final_warnings:
            print(f"WARNING: {warning}")
        if final_errors:
            for error in final_errors:
                print(f"ERROR: {error}")
            raise RuntimeError("workspace failed validation after creation")
    except Exception as exc:
        if committed and target.exists():
            shutil.rmtree(target)
        elif build_root.exists():
            shutil.rmtree(build_root)
        atomic_write(registry_path, original_registry)
        atomic_write(map_path, original_map)
        print(f"FAILED: {exc}")
        return 1

    print(f"CREATED: {target}")
    print("Next: open the new directory as a Vault in Obsidian.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
