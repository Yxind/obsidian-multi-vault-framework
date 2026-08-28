#!/usr/bin/env python3
"""Validate a standardized multi-Vault Obsidian workspace without modifying it."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from sync_same_source_notices import plan_same_source_updates
from validate_vault import validate_vault


VALID_SENSITIVITIES = {"public", "internal", "private"}
INBOX_CATEGORIES = {
    "00-Unsorted",
    "Personal-Private",
    "Books-Courses",
    "Media",
    "Articles-Web",
    "Papers-Reports",
    "Project-Materials",
}
MAP_RE = re.compile(
    r"(?ms)<!-- VAULT-REGISTRY:START -->.*?<!-- VAULT-REGISTRY:END -->"
)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def registry_block(vaults: list[dict[str, object]]) -> str:
    lines = ["<!-- VAULT-REGISTRY:START -->"]
    for vault in vaults:
        lines.extend(
            [
                f"## {vault['name']}",
                "",
                f"**负责**：{str(vault['scope']).rstrip('。')}。",
                "",
                f"**不负责**：{str(vault['excludes']).rstrip('。')}。",
                "",
                "**路由判断**：未来最常用的问题是“"
                + str(vault["route_question"]).rstrip("。")
                + "”时，放入本库。",
                "",
            ]
        )
    lines.append("<!-- VAULT-REGISTRY:END -->")
    return "\n".join(lines)


def validate_workspace(root: Path) -> tuple[list[str], list[str]]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    system = root / "_Vault-System"
    registry_path = system / "vault-registry.json"
    map_path = system / "vault-map.md"
    templates_source = system / "Templates-Source"

    if (root / ".obsidian").exists():
        errors.append("workspace root must not contain .obsidian")
    for required in (registry_path, map_path, templates_source):
        if not required.exists():
            errors.append(f"missing workspace system path: {required.relative_to(root)}")
    if errors:
        return errors, warnings

    try:
        registry = load_json(registry_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid vault-registry.json: {exc}")
        return errors, warnings
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        errors.append("vault-registry.json must use schema_version 1")
        return errors, warnings
    vault_entries = registry.get("vaults")
    if not isinstance(vault_entries, list):
        errors.append("vault-registry.json must contain a vaults list")
        return errors, warnings

    required_entry_keys = {
        "name",
        "display_name",
        "sensitivity",
        "daily_notes_enabled",
        "scope",
        "excludes",
        "route_question",
    }
    names: list[str] = []
    for index, entry in enumerate(vault_entries):
        if not isinstance(entry, dict):
            errors.append(f"registry vault entry {index} is not an object")
            continue
        missing = sorted(required_entry_keys - entry.keys())
        if missing:
            errors.append(
                f"registry vault entry {index} missing: " + ", ".join(missing)
            )
            continue
        name = str(entry["name"])
        names.append(name)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}", name):
            errors.append(f"invalid Vault name in registry: {name}")
        if entry["sensitivity"] not in VALID_SENSITIVITIES:
            errors.append(f"invalid Vault sensitivity for {name}: {entry['sensitivity']}")
        if not isinstance(entry["daily_notes_enabled"], bool):
            errors.append(f"daily_notes_enabled must be boolean for {name}")
    if len(names) != len(set(names)):
        errors.append("duplicate Vault name in registry")

    map_text = map_path.read_text(encoding="utf-8-sig")
    expected_block = registry_block(
        [entry for entry in vault_entries if isinstance(entry, dict)]
    )
    match = MAP_RE.search(map_text)
    if not match:
        errors.append("vault-map.md is missing registry markers")
    elif match.group(0).replace("\r\n", "\n") != expected_block:
        errors.append("vault-map.md registry block does not match vault-registry.json")

    discovered = {
        path.name
        for path in root.iterdir()
        if path.is_dir() and (path / ".obsidian").is_dir()
    }
    registered = set(names)
    for name in sorted(discovered - registered):
        errors.append(f"unregistered child Vault: {name}")
    for name in sorted(registered - discovered):
        errors.append(f"registered Vault missing or not initialized: {name}")

    master_templates = {
        path.name: path.read_bytes()
        for path in templates_source.iterdir()
        if path.is_file()
    }
    for entry in vault_entries:
        if not isinstance(entry, dict) or "name" not in entry:
            continue
        name = str(entry["name"])
        vault = root / name
        if not vault.is_dir():
            continue
        required_dirs = {
            ".obsidian",
            "1-Inbox",
            "2-AI work",
            "3-Wiki",
            "4-Outputs",
            "Templates",
            "assets",
        }
        for directory in sorted(required_dirs):
            if not (vault / directory).is_dir():
                errors.append(f"{name}: missing directory {directory}")
        for category in sorted(INBOX_CATEGORIES):
            if not (vault / "1-Inbox" / category).is_dir():
                errors.append(f"{name}: missing Inbox category {category}")

        for json_path in (vault / ".obsidian").glob("*.json"):
            try:
                load_json(json_path)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{name}: invalid JSON {json_path.name}: {exc}")
        core_path = vault / ".obsidian" / "core-plugins.json"
        if core_path.is_file():
            try:
                core = load_json(core_path)
                expected_daily = bool(entry.get("daily_notes_enabled", False))
                if not isinstance(core, dict) or core.get("daily-notes") is not expected_daily:
                    errors.append(
                        f"{name}: daily-notes setting does not match registry "
                        f"({expected_daily})"
                    )
                for required_plugin in ("templates", "file-recovery", "bases"):
                    if not isinstance(core, dict) or core.get(required_plugin) is not True:
                        errors.append(f"{name}: required core plugin disabled: {required_plugin}")
            except (OSError, json.JSONDecodeError):
                pass

        app_path = vault / ".obsidian" / "app.json"
        if app_path.is_file():
            try:
                app = load_json(app_path)
                expected_app = {
                    "newFileLocation": "folder",
                    "newFileFolderPath": "1-Inbox/00-Unsorted",
                    "attachmentFolderPath": "assets",
                    "newLinkFormat": "absolute",
                    "promptDelete": True,
                    "alwaysUpdateLinks": True,
                }
                if not isinstance(app, dict):
                    errors.append(f"{name}: app.json must contain an object")
                else:
                    for key, expected in expected_app.items():
                        if app.get(key) != expected:
                            errors.append(
                                f"{name}: app.json {key} must be {expected!r}"
                            )
            except (OSError, json.JSONDecodeError):
                pass

        templates_config = vault / ".obsidian" / "templates.json"
        if templates_config.is_file():
            try:
                config = load_json(templates_config)
                if not isinstance(config, dict) or config.get("folder") != "Templates":
                    errors.append(f"{name}: templates folder must be Templates")
            except (OSError, json.JSONDecodeError):
                pass

        vault_templates = vault / "Templates"
        for template_name, master_bytes in master_templates.items():
            copy_path = vault_templates / template_name
            if not copy_path.is_file():
                errors.append(f"{name}: missing template copy {template_name}")
            elif copy_path.read_bytes() != master_bytes:
                errors.append(f"{name}: template drift {template_name}")
        extra_templates = {
            path.name for path in vault_templates.iterdir() if path.is_file()
        } - set(master_templates)
        for template_name in sorted(extra_templates):
            warnings.append(f"{name}: local-only template {template_name}")

        vault_errors, vault_warnings, content_count, wiki_count = validate_vault(vault)
        for error in vault_errors:
            errors.append(f"{name}: {error}")
        for warning in vault_warnings:
            warnings.append(f"{name}: {warning}")
        print(
            f"{name}: {content_count} Markdown/Base files, "
            f"{wiki_count} canonical Wiki pages"
        )

    notice_errors, notice_updates = plan_same_source_updates(root)
    errors.extend(notice_errors)
    for path, _ in notice_updates:
        errors.append(
            "same-source cross-Vault notice is out of sync: "
            + path.relative_to(root).as_posix()
            + " (run sync_same_source_notices.py --write)"
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a multi-Vault workspace.")
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "workspace",
        nargs="?",
        type=Path,
        default=default_root,
        help="workspace root; defaults to the parent of _Vault-System",
    )
    args = parser.parse_args()
    if not args.workspace.is_dir():
        parser.error(f"workspace not found: {args.workspace}")

    errors, warnings = validate_workspace(args.workspace)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"OK: 0 errors, {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
