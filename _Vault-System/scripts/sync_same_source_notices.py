#!/usr/bin/env python3
"""Synchronize exact same-source notices across non-private Vault summaries."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


NOTICE_START = "<!-- SAME-SOURCE-VAULTS:START -->"
NOTICE_END = "<!-- SAME-SOURCE-VAULTS:END -->"
NOTICE_RE = re.compile(
    rf"(?ms)\n*{re.escape(NOTICE_START)}.*?{re.escape(NOTICE_END)}\n*"
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.S)
SCOPE_RE = re.compile(
    r"(?ms)^##\s+本 Vault 的处理范围\s*$\n(.*?)(?=^##\s+|\Z)"
)
SOURCE_ID_RE = re.compile(r"^src-[0-9a-f]{16}$")
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TEMPLATE_SCOPE_PREFIX = "说明本页只提取哪些领域知识"


@dataclass(frozen=True)
class SummaryRecord:
    vault: str
    path: Path
    source_id: str
    content_hash: str
    scope: str


def clean_value(value: str) -> str:
    return value.strip().strip("\"'")


def frontmatter_fields(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if item:
            fields[item.group(1)] = clean_value(item.group(2))
    return fields


def strip_notice(text: str) -> str:
    return NOTICE_RE.sub("\n\n", text)


def normalize_scope(text: str) -> str:
    cleaned = strip_notice(text)
    match = SCOPE_RE.search(cleaned)
    if not match:
        return ""
    scope = " ".join(line.strip() for line in match.group(1).splitlines() if line.strip())
    if not scope or scope.startswith(TEMPLATE_SCOPE_PREFIX):
        return ""
    return scope


def render_notice(other_scopes: dict[str, list[str]]) -> str:
    lines = [
        NOTICE_START,
        "## 跨 Vault 同源提示",
        "",
        "以下内容由完整 `content_hash` 与 `source_id` 双重匹配后自动生成；"
        "只说明其他 Vault 的处理范围，不建立跨 Vault 链接。",
        "",
    ]
    for vault in sorted(other_scopes, key=str.casefold):
        scopes = "；".join(sorted(set(other_scopes[vault]), key=str.casefold))
        lines.append(f"- {vault}：{scopes}")
    lines.append(NOTICE_END)
    return "\n".join(lines)


def apply_notice(text: str, notice: str) -> str:
    had_notice = NOTICE_START in text and NOTICE_END in text
    cleaned = strip_notice(text)
    if not notice:
        return cleaned.rstrip() + "\n" if had_notice else text
    scope_match = SCOPE_RE.search(cleaned)
    if not scope_match:
        return cleaned
    before = cleaned[: scope_match.end()].rstrip()
    after = cleaned[scope_match.end() :].lstrip("\r\n")
    result = before + "\n\n" + notice
    if after:
        result += "\n\n" + after
    return result.rstrip() + "\n"


def load_non_private_records(root: Path) -> tuple[list[SummaryRecord], list[str]]:
    errors: list[str] = []
    registry_path = root / "_Vault-System" / "vault-registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"cannot read Vault registry for same-source notices: {exc}"]
    vaults = registry.get("vaults") if isinstance(registry, dict) else None
    if not isinstance(vaults, list):
        return [], ["Vault registry has no vaults list for same-source notices"]

    records: list[SummaryRecord] = []
    for entry in vaults:
        if not isinstance(entry, dict) or entry.get("sensitivity") == "private":
            continue
        vault_name = str(entry.get("name", ""))
        ai_work = root / vault_name / "2-AI work"
        if not ai_work.is_dir():
            continue
        for path in ai_work.rglob("*.md"):
            text = path.read_text(encoding="utf-8-sig")
            fields = frontmatter_fields(text)
            is_summary = (
                fields.get("type") == "synthesis" or path.stem.endswith("-详细总结")
            )
            if not is_summary:
                continue
            source_id = fields.get("source_id", "")
            content_hash = fields.get("content_hash", "")
            if not SOURCE_ID_RE.fullmatch(source_id) or not CONTENT_HASH_RE.fullmatch(
                content_hash
            ):
                continue
            records.append(
                SummaryRecord(
                    vault=vault_name,
                    path=path,
                    source_id=source_id,
                    content_hash=content_hash,
                    scope=normalize_scope(text),
                )
            )
    return records, errors


def plan_same_source_updates(root: Path) -> tuple[list[str], list[tuple[Path, str]]]:
    root = root.resolve()
    records, errors = load_non_private_records(root)
    hashes_by_source_id: dict[str, set[str]] = defaultdict(set)
    for record in records:
        hashes_by_source_id[record.source_id].add(record.content_hash)
    for source_id, hashes in hashes_by_source_id.items():
        if len(hashes) > 1:
            errors.append(
                f"source_id collision or inconsistent content_hash across Vaults: {source_id}"
            )

    groups: dict[tuple[str, str], list[SummaryRecord]] = defaultdict(list)
    for record in records:
        groups[(record.source_id, record.content_hash)].append(record)

    updates: list[tuple[Path, str]] = []
    for group in groups.values():
        distinct_vaults = {record.vault for record in group}
        if len(distinct_vaults) > 1:
            for record in group:
                if not record.scope:
                    errors.append(
                        "same-source summary needs a short plain-text '本 Vault 的处理范围': "
                        + record.path.relative_to(root).as_posix()
                    )
                elif "[[" in record.scope or "]]" in record.scope:
                    errors.append(
                        "same-source scope must not contain Wikilinks: "
                        + record.path.relative_to(root).as_posix()
                    )
                elif len(record.scope) > 300:
                    errors.append(
                        "same-source scope is too long (maximum 300 characters): "
                        + record.path.relative_to(root).as_posix()
                    )
            if any(not record.scope or "[[" in record.scope or len(record.scope) > 300 for record in group):
                continue

        for record in group:
            other_scopes: dict[str, list[str]] = defaultdict(list)
            for other in group:
                if other.vault != record.vault:
                    other_scopes[other.vault].append(other.scope)
            notice = render_notice(other_scopes) if other_scopes else ""
            original = record.path.read_text(encoding="utf-8-sig")
            expected = apply_notice(original, notice)
            if expected != original:
                updates.append((record.path, expected))
    return errors, updates


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".same-source.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or synchronize exact same-source notices across non-private Vaults."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="workspace root; defaults to the parent of _Vault-System",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the generated notice blocks; default is check-only",
    )
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"workspace not found: {root}")

    errors, updates = plan_same_source_updates(root)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED: {len(errors)} error(s); no files changed.")
        return 1
    if not updates:
        print("OK: same-source notices are synchronized; private Vaults were skipped.")
        return 0
    if not args.write:
        for path, _ in updates:
            print(f"OUT OF SYNC: {path.relative_to(root).as_posix()}")
        print("Run again with --write to synchronize the generated notice blocks.")
        return 1

    for path, text in updates:
        atomic_write(path, text)
        print(f"UPDATED: {path.relative_to(root).as_posix()}")
    print(f"OK: synchronized {len(updates)} detailed summary file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
