#!/usr/bin/env python3
"""Validate one standardized Obsidian Vault without modifying it."""

from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path


WIKI_FOLDER_TYPES = {
    "Concepts": "concept",
    "Topics": "topic",
    "Tools": "tool",
    "People": "person",
}
CANONICAL_TYPES = set(WIKI_FOLDER_TYPES.values())
INBOX_CATEGORIES = {
    "00-Unsorted",
    "Personal-Private",
    "Books-Courses",
    "Media",
    "Articles-Web",
    "Papers-Reports",
    "Project-Materials",
}
REQUIRED_WIKI_KEYS = {
    "created",
    "updated",
    "type",
    "status",
    "sources",
    "last_reviewed",
    "aliases",
    "tags",
}
REQUIRED_SUMMARY_KEYS = {
    "created",
    "updated",
    "type",
    "status",
    "source",
    "source_id",
    "content_hash",
    "tags",
}
VALID_WIKI_STATUSES = {"seed", "growing", "mature"}
VALID_SUMMARY_STATUSES = {"review", "archived"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SOURCE_ID_RE = re.compile(r"^src-([0-9a-f]{16})$")
HASH_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
LINK_RE = re.compile(r"!?\[\[([^\]]+)\]\]")


def normalize(text: str) -> str:
    return text.replace("\\", "/").strip("/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
    if not match:
        return {}, ""
    raw = match.group(1)
    data: dict[str, str] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if key_match:
            current_key = key_match.group(1)
            data[current_key] = key_match.group(2).strip()
        elif current_key and re.match(r"^\s+-\s+", line):
            data[current_key] += "\n" + line.strip()
    return data, raw


def clean_value(value: str) -> str:
    return value.strip().strip("\"'")


def parse_aliases(raw_frontmatter: str) -> list[str]:
    inline = re.search(r"(?m)^aliases:\s*\[(.*?)\]\s*$", raw_frontmatter)
    if inline:
        return [
            item.strip().strip("\"'")
            for item in inline.group(1).split(",")
            if item.strip()
        ]
    block = re.search(
        r"(?ms)^aliases:\s*$\n((?:\s+-\s+.*(?:\n|$))*)",
        raw_frontmatter,
    )
    if not block:
        return []
    return [
        line.strip()[2:].strip().strip("\"'")
        for line in block.group(1).splitlines()
        if line.strip().startswith("- ")
    ]


def clean_link_target(raw_target: str) -> str:
    target = (
        raw_target.split("|", 1)[0]
        .split("#", 1)[0]
        .split("^", 1)[0]
        .strip()
    )
    return normalize(target)


def resolve_link_path(
    raw_target: str,
    files_by_path: dict[str, str],
    files_by_stem: dict[str, list[str]],
) -> str | None:
    target = clean_link_target(raw_target)
    if not target:
        return ""
    if "/" in target or target.endswith((".md", ".base")):
        candidates = [target]
        if not target.endswith((".md", ".base")):
            candidates.extend([target + ".md", target + ".base"])
        for candidate in candidates:
            resolved = files_by_path.get(candidate.casefold())
            if resolved:
                return resolved
        return None
    candidates = files_by_stem.get(Path(target).stem.casefold(), [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def link_resolves(
    raw_target: str,
    files_by_path: dict[str, str],
    files_by_stem: dict[str, list[str]],
) -> bool:
    return resolve_link_path(raw_target, files_by_path, files_by_stem) is not None


def resolved_targets(
    text: str,
    files_by_path: dict[str, str],
    files_by_stem: dict[str, list[str]],
) -> set[str]:
    targets: set[str] = set()
    for raw_target in LINK_RE.findall(text):
        resolved = resolve_link_path(raw_target, files_by_path, files_by_stem)
        if resolved:
            targets.add(resolved.casefold())
    return targets


def section_body(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def validate_vault(vault: Path) -> tuple[list[str], list[str], int, int]:
    vault = vault.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    all_content_files = [
        path
        for path in vault.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".base"}
        and ".obsidian" not in path.parts
    ]
    linkable_suffixes = {
        ".md", ".base", ".pdf", ".png", ".jpg", ".jpeg", ".webp",
        ".gif", ".svg", ".mp3", ".wav", ".mp4", ".mov", ".docx",
        ".xlsx", ".pptx", ".txt", ".csv",
    }
    all_linkable_files = [
        path
        for path in vault.rglob("*")
        if path.is_file()
        and path.suffix.lower() in linkable_suffixes
        and ".obsidian" not in path.parts
    ]
    files_by_path = {
        normalize(path.relative_to(vault).as_posix()).casefold():
        normalize(path.relative_to(vault).as_posix())
        for path in all_linkable_files
    }
    files_by_stem: dict[str, list[str]] = defaultdict(list)
    for path in all_linkable_files:
        relative = normalize(path.relative_to(vault).as_posix())
        files_by_stem[path.stem.casefold()].append(relative)

    node_files_by_stem: dict[str, list[str]] = defaultdict(list)
    for path in all_content_files:
        relative = normalize(path.relative_to(vault).as_posix())
        node_files_by_stem[path.stem.casefold()].append(relative)
    for paths in node_files_by_stem.values():
        unique_paths = sorted(set(paths))
        if len(unique_paths) > 1:
            errors.append(
                f"duplicate node basename '{Path(unique_paths[0]).stem}': "
                + ", ".join(unique_paths)
            )

    for path in all_content_files:
        relative = normalize(path.relative_to(vault).as_posix())
        if path.stat().st_size == 0:
            errors.append(f"empty file: {relative}")

    for path in all_linkable_files:
        relative = normalize(path.relative_to(vault).as_posix())
        if relative.startswith("1-Inbox/"):
            parts = relative.split("/")
            if len(parts) < 3 or parts[1] not in INBOX_CATEGORIES:
                warnings.append(
                    "Inbox source is outside the standard categories: " + relative
                )

    canonical_paths: dict[str, Path] = {}
    wiki_source_targets: dict[str, set[str]] = {}
    wiki_statuses: dict[str, str] = {}
    identity_map: dict[str, list[str]] = defaultdict(list)
    wiki_root = vault / "3-Wiki"
    if wiki_root.exists():
        for path in wiki_root.rglob("*.md"):
            relative_path = path.relative_to(vault)
            if path.name in {"index.md", "log.md"}:
                continue
            text = path.read_text(encoding="utf-8-sig")
            data, raw_frontmatter = frontmatter(text)
            note_type = clean_value(data.get("type", ""))
            folder_type = None
            relative_to_wiki = path.relative_to(wiki_root)
            if len(relative_to_wiki.parts) > 1:
                folder_type = WIKI_FOLDER_TYPES.get(relative_to_wiki.parts[0])
            if note_type not in CANONICAL_TYPES and folder_type is None:
                continue
            relative = normalize(relative_path.as_posix()).casefold()
            canonical_paths[relative] = path
            missing = sorted(REQUIRED_WIKI_KEYS - data.keys())
            if missing:
                errors.append(
                    f"metadata missing in {relative_path.as_posix()}: "
                    + ", ".join(missing)
                )
            if "sensitivity" in data:
                errors.append(
                    "page-level sensitivity is redundant; use Vault registry: "
                    + relative_path.as_posix()
                )
            if folder_type and note_type and note_type != folder_type:
                errors.append(
                    f"type mismatch in {relative_path.as_posix()}: "
                    f"expected {folder_type}, got {note_type}"
                )
            status = clean_value(data.get("status", ""))
            wiki_statuses[relative] = status
            if status and status not in VALID_WIKI_STATUSES:
                errors.append(
                    f"invalid Wiki status in {relative_path.as_posix()}: {status}"
                )
            sources = data.get("sources", "").strip()
            declared_sources: set[str] = set()
            if not sources or sources in {"[]", "null", "~"}:
                errors.append("empty sources in " + relative_path.as_posix())
            else:
                source_links = LINK_RE.findall(sources)
                if not source_links:
                    errors.append(
                        "Wiki sources must contain detailed-summary Wikilinks: "
                        + relative_path.as_posix()
                    )
                for raw_target in source_links:
                    resolved = resolve_link_path(
                        raw_target, files_by_path, files_by_stem
                    )
                    if not resolved:
                        errors.append(
                            "unresolved Wiki source in "
                            + relative_path.as_posix()
                            + f": [[{raw_target}]]"
                        )
                    else:
                        declared_sources.add(resolved.casefold())
            wiki_source_targets[relative] = declared_sources
            if "4-Outputs/".casefold() in sources.casefold():
                errors.append(
                    "Wiki sources must not use 4-Outputs as evidence: "
                    + relative_path.as_posix()
                )
            reviewed = clean_value(data.get("last_reviewed", ""))
            if reviewed and not ISO_DATE_RE.fullmatch(reviewed):
                errors.append(
                    "invalid last_reviewed date in "
                    + relative_path.as_posix()
                    + f": {reviewed}"
                )
            identity_map[path.stem.casefold()].append(relative_path.as_posix())
            for alias in parse_aliases(raw_frontmatter):
                identity_map[alias.casefold()].append(relative_path.as_posix())

    for identity, paths in sorted(identity_map.items()):
        unique_paths = sorted(set(paths))
        if len(unique_paths) > 1:
            warnings.append(
                f"duplicate name or alias '{identity}': " + ", ".join(unique_paths)
            )

    index_path = wiki_root / "index.md"
    index_text = (
        index_path.read_text(encoding="utf-8-sig") if index_path.exists() else ""
    )
    for path in canonical_paths.values():
        relative_without_suffix = normalize(
            path.relative_to(vault).with_suffix("").as_posix()
        )
        if relative_without_suffix not in index_text:
            errors.append(f"missing from index: {relative_without_suffix}")

    active_markdown = [
        path
        for path in all_content_files
        if path.suffix.lower() == ".md"
        and "1-Inbox" not in path.relative_to(vault).parts
        and "Templates" not in path.relative_to(vault).parts
    ]
    for path in active_markdown:
        text = path.read_text(encoding="utf-8-sig")
        for raw_target in LINK_RE.findall(text):
            if not link_resolves(raw_target, files_by_path, files_by_stem):
                errors.append(
                    f"broken link in {path.relative_to(vault).as_posix()}: "
                    f"[[{raw_target}]]"
                )

    summary_paths: dict[str, Path] = {}
    summary_targets: dict[str, set[str]] = {}
    summary_source_id_by_path: dict[str, str] = {}
    summary_source_ids: dict[str, list[str]] = defaultdict(list)
    ai_work = vault / "2-AI work"
    if ai_work.exists():
        for path in ai_work.rglob("*.md"):
            text = path.read_text(encoding="utf-8-sig")
            data, _ = frontmatter(text)
            note_type = clean_value(data.get("type", ""))
            status = clean_value(data.get("status", ""))
            relative_path = path.relative_to(vault)
            relative = normalize(relative_path.as_posix()).casefold()

            if "sensitivity" in data:
                errors.append(
                    "page-level sensitivity is redundant; use Vault registry: "
                    + relative_path.as_posix()
                )

            if note_type == "analysis":
                if status != "review":
                    errors.append(
                        "rough analysis must use status: review: "
                        + relative_path.as_posix()
                    )
                targets = resolved_targets(text, files_by_path, files_by_stem)
                inbox_targets = {
                    target for target in targets if target.startswith("1-inbox/")
                }
                if len(inbox_targets) != 1:
                    errors.append(
                        "rough analysis must link exactly one Inbox source: "
                        f"{relative_path.as_posix()} (found {len(inbox_targets)})"
                    )
                if path.stem.endswith("-AI 粗剪-待继续"):
                    progress = section_body(text, "摄取进度")
                    for field in ("已摄取范围", "待继续范围", "下一起点", "最后更新"):
                        if not re.search(
                            rf"(?m)^-\s*{field}：\s*\S+", progress
                        ):
                            errors.append(
                                f"pending rough analysis missing {field}: "
                                + relative_path.as_posix()
                            )
                continue

            is_summary = note_type == "synthesis" or path.stem.endswith("-详细总结")
            if not is_summary:
                continue

            summary_paths[relative] = path
            targets = resolved_targets(text, files_by_path, files_by_stem)
            summary_targets[relative] = targets
            missing = sorted(REQUIRED_SUMMARY_KEYS - data.keys())
            if missing:
                errors.append(
                    f"summary metadata missing in {relative_path.as_posix()}: "
                    + ", ".join(missing)
                )
            if status and status not in VALID_SUMMARY_STATUSES:
                errors.append(
                    f"invalid summary status in {relative_path.as_posix()}: {status}"
                )
            source_links = LINK_RE.findall(data.get("source", ""))
            source_relative: str | None = None
            if len(source_links) != 1:
                errors.append(
                    "detailed summary source field must contain exactly one link: "
                    f"{relative_path.as_posix()} (found {len(source_links)})"
                )
            else:
                resolved_source = resolve_link_path(
                    source_links[0], files_by_path, files_by_stem
                )
                if not resolved_source:
                    errors.append(
                        "detailed summary source field does not resolve: "
                        + relative_path.as_posix()
                    )
                elif not resolved_source.casefold().startswith("1-inbox/"):
                    errors.append(
                        "detailed summary source field must point to Inbox: "
                        + relative_path.as_posix()
                    )
                else:
                    source_relative = resolved_source.casefold()

            inbox_targets = {
                target for target in targets if target.startswith("1-inbox/")
            }
            if source_relative is None:
                continue
            if inbox_targets != {source_relative}:
                errors.append(
                    "detailed summary must reference only its declared Inbox source: "
                    f"{relative_path.as_posix()} (found {len(inbox_targets)})"
                )

            expected_stem = Path(source_relative).stem + "-详细总结"
            if path.stem.casefold() != expected_stem.casefold():
                errors.append(
                    "detailed summary filename must match its source: "
                    f"{relative_path.as_posix()} (expected {expected_stem}.md)"
                )

            source_actual = files_by_path.get(source_relative)
            if not source_actual:
                continue
            source_path = vault / Path(source_actual)
            digest = sha256_file(source_path)
            expected_source_id = f"src-{digest[:16]}"
            expected_hash = f"sha256:{digest}"
            source_id = clean_value(data.get("source_id", ""))
            content_hash = clean_value(data.get("content_hash", ""))
            if not SOURCE_ID_RE.fullmatch(source_id):
                errors.append(
                    "invalid source_id in " + relative_path.as_posix()
                )
            elif source_id != expected_source_id:
                errors.append(
                    f"source_id does not match source bytes in {relative_path.as_posix()}: "
                    f"expected {expected_source_id}"
                )
            if not HASH_RE.fullmatch(content_hash):
                errors.append(
                    "invalid content_hash in " + relative_path.as_posix()
                )
            elif content_hash != expected_hash:
                errors.append(
                    "content_hash does not match source bytes in "
                    + relative_path.as_posix()
                )
            if source_id and source_id == expected_source_id:
                summary_source_ids[source_id].append(source_actual)
                summary_source_id_by_path[relative] = source_id

    for source_id, source_paths in summary_source_ids.items():
        unique_sources = sorted(set(source_paths))
        if len(unique_sources) > 1:
            warnings.append(
                f"same source_id appears on multiple Inbox paths: {source_id}: "
                + ", ".join(unique_sources)
            )

    wiki_targets: dict[str, set[str]] = {}
    for relative, path in canonical_paths.items():
        text = path.read_text(encoding="utf-8-sig")
        targets = resolved_targets(text, files_by_path, files_by_stem)
        wiki_targets[relative] = targets
        inbox_targets = {
            target for target in targets if target.startswith("1-inbox/")
        }
        if inbox_targets:
            errors.append(
                "canonical Wiki page links Inbox directly; use a detailed summary: "
                + path.relative_to(vault).as_posix()
            )

    for summary, targets in summary_targets.items():
        for wiki in targets & canonical_paths.keys():
            if summary not in wiki_targets.get(wiki, set()):
                errors.append(
                    "detailed summary/Wiki link is not reciprocal: "
                    f"{summary} -> {wiki}"
                )
    for wiki, targets in wiki_targets.items():
        for summary in targets & summary_paths.keys():
            if wiki not in summary_targets.get(summary, set()):
                errors.append(
                    "Wiki/detailed summary link is not reciprocal: "
                    f"{wiki} -> {summary}"
                )

    for wiki, declared_sources in wiki_source_targets.items():
        non_summaries = declared_sources - summary_paths.keys()
        for target in sorted(non_summaries):
            errors.append(
                "Wiki sources must point to detailed summaries: "
                f"{wiki} -> {target}"
            )
        linked_summaries = wiki_targets.get(wiki, set()) & summary_paths.keys()
        undeclared = linked_summaries - declared_sources
        for target in sorted(undeclared):
            errors.append(
                "Wiki links a detailed summary outside its sources field: "
                f"{wiki} -> {target}"
            )
        source_ids = {
            summary_source_id_by_path[target]
            for target in declared_sources & summary_paths.keys()
            if target in summary_source_id_by_path
        }
        if wiki_statuses.get(wiki) == "growing" and len(source_ids) < 2:
            errors.append(
                "growing Wiki page requires at least two distinct source_id values: "
                + wiki
            )

    outbound: dict[str, set[str]] = defaultdict(set)
    inbound: dict[str, set[str]] = defaultdict(set)
    for relative, path in canonical_paths.items():
        text = path.read_text(encoding="utf-8-sig")
        for raw_target in LINK_RE.findall(text):
            resolved = resolve_link_path(raw_target, files_by_path, files_by_stem)
            if not resolved:
                continue
            target = resolved.casefold()
            if target in canonical_paths and target != relative:
                outbound[relative].add(target)
                inbound[target].add(relative)
    for relative, path in sorted(canonical_paths.items()):
        if not outbound[relative] and not inbound[relative]:
            warnings.append(
                "standalone canonical Wiki page (no Wiki-to-Wiki link): "
                + path.relative_to(vault).as_posix()
            )

    return errors, warnings, len(all_content_files), len(canonical_paths)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_vault.py <vault-path>")
        return 2
    vault = Path(sys.argv[1]).resolve()
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}")
        return 2

    errors, warnings, content_count, wiki_count = validate_vault(vault)
    print(
        f"Validated {content_count} Markdown/Base files; "
        f"{wiki_count} canonical Wiki pages."
    )
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
