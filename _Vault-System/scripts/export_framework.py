#!/usr/bin/env python3
"""Build a sanitized, self-contained release of the multi-Vault framework."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from new_vault import build_vault
from validate_workspace import registry_block, validate_workspace


ARCHIVE_ROOT = "Obsidian-Multi-Vault-Framework"
SYSTEM_DIRECTORIES = (
    "Config-Source",
    "Templates-Source",
    "Vault-Scaffold",
    "scripts",
)
SYSTEM_FILES = (
    "README.md",
    "migration-checklist.md",
    "shared-rules.md",
)
IGNORED_NAMES = {".git", "__pycache__", ".DS_Store"}
GIT_PLACEHOLDER = ".gitkeep"

STARTER_VAULTS: tuple[dict[str, object], ...] = (
    {
        "name": "Courses-Learning",
        "display_name": "Courses & Learning",
        "sensitivity": "public",
        "daily_notes_enabled": False,
        "scope": "公开课程、书籍学习、练习、实验、学习项目与可复用的学习方法",
        "excludes": "依赖具体身份、私人关系、个人状态或私人时间线的材料",
        "route_question": "如何理解、练习或应用一门课程中的知识",
    },
    {
        "name": "Personal",
        "display_name": "Personal",
        "sensitivity": "private",
        "daily_notes_enabled": False,
        "scope": "私人关系、个人状态、生活决策，以及依赖具体身份或私人时间线的资料",
        "excludes": "可公开复用的课程知识、一般方法与公开资料",
        "route_question": "这份材料是否依赖具体个人身份、私人时间线或只对个人生活有意义",
    },
)

RELEASE_README_TEMPLATE = """# Obsidian Multi-Vault Framework

这是一个不含个人知识内容的 Obsidian 多 Vault 框架。父目录用于 Codex 跨库管理，不是 Obsidian Vault。

## 获取发行版

- 可以直接克隆仓库；空目录内的 `.gitkeep` 只用于保留框架结构，不是 Inbox 来源或知识内容。
- 也可以从 GitHub Releases 下载固定版本 ZIP；ZIP 适合复制到其他电脑或交给他人部署。

{starter_section}

## 环境

- Obsidian
- Codex（使用 Agent 规则与 `ai-organize` Skill 时需要）
- Python 3.10 或更高版本；脚本仅使用标准库

## 初始化

1. 将本目录作为 Codex 项目打开。
2. 在 Obsidian 中把每个预设子目录分别打开为 Vault；不要把父目录打开为 Vault。
3. 运行 `python _Vault-System/scripts/validate_workspace.py` 验证整个工作区。
4. 需要更多 Vault 时，先用 `python _Vault-System/scripts/new_vault.py --help` 查看参数，并使用 `--dry-run` 预览。

新建 Vault 的名称、负责范围、排除项、路由问题和敏感级别应由使用者自行决定。Agent 可以提出建议，但只有用户明确下令后才能运行生成器。

## 数据边界

- `_Dropzone/` 和既有 `1-Inbox/` 由用户维护，Agent 只读。
- 预设 Vault 只有框架页面、配置和空 Inbox 分类，不包含来源、用户笔记、附件或历史记录。
- 私人内容应进入 `sensitivity: private` 的 Vault；不要把含私人历史的目录直接发布到 Git 仓库。

## 重新发行

框架维护者可运行 `python _Vault-System/scripts/export_framework.py --help` 生成新的入门发行包；使用 `--empty` 可生成无预设 Vault 的版本。
"""

VAULT_MAP_TAIL = """## 跨领域材料

1. 默认按未来主要查询问题选择一个主要归属，不按文件类型或关键词数量投票。
2. 可泛化的方法与公开信息按主要用途归领域 Vault；依赖具体身份、私人关系或私人时间线的原始材料归 `sensitivity: private` 的 Vault。
3. 私人材料需要跨库复用时，只迁出经用户授权的脱敏版本；原始来源保留在私人 Vault。
4. 归属不确定时留在 `_Dropzone`，由用户决定后再移动到目标 `1-Inbox`。
5. 同一原文确实支撑多个 Vault 的独立问题时，用户可以复制到多个 Inbox；各 Vault 只摄取本库相关部分，不要求跨库登记或链接。
6. 一组暂存材料长期不适合任何现有 Vault 时，可以提出新库建议；建议不等于创建授权，必须等待用户明确的新建命令。
"""


def render_release_readme(vaults: list[dict[str, object]]) -> str:
    if vaults:
        starter_section = """## 预设 Vault

- `Courses-Learning/`：`public`，用于公开课程、学习资料、练习和可复用方法。
- `Personal/`：`private`，用于依赖个人身份、私人关系或私人时间线的资料。

两个 Vault 都已完成标准初始化，可以直接在 Obsidian 中分别打开。"""
    else:
        starter_section = """## 预设 Vault

本版本未预设 Vault。请先使用 `new_vault.py` 创建第一个 Vault。"""
    return RELEASE_README_TEMPLATE.format(starter_section=starter_section)


def render_vault_map(vaults: list[dict[str, object]]) -> str:
    return (
        "# Vault Map\n\n"
        "本页的 Vault 职责区块由 `vault-registry.json` 与新库生成器维护；"
        "跨领域规则人工维护。\n\n"
        + registry_block(vaults)
        + "\n\n"
        + VAULT_MAP_TAIL
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ignore_generated(_: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in IGNORED_NAMES or name.endswith((".pyc", ".pyo"))
    }


def copy_directory(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise FileNotFoundError(f"required directory is missing: {source}")
    shutil.copytree(source, destination, ignore=ignore_generated)


def find_skill(root: Path, explicit: Path | None) -> Path:
    candidates = []
    if explicit is not None:
        candidates.append(explicit)
    candidates.extend(
        [
            root / ".agents" / "skills" / "ai-organize",
            Path.home() / ".agents" / "skills" / "ai-organize",
            Path.home() / ".codex" / "skills" / "ai-organize",
        ]
    )
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if (resolved / "SKILL.md").is_file():
            return resolved
    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"ai-organize Skill was not found; checked: {checked}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def add_git_placeholders(root: Path) -> None:
    """Keep intentionally empty release directories visible to Git clones."""
    empty_directories = [
        path
        for path in root.rglob("*")
        if path.is_dir() and not any(path.iterdir())
    ]
    for directory in empty_directories:
        write_text(directory / GIT_PLACEHOLDER, "")


def build_release(
    staging: Path,
    workspace: Path,
    skill: Path,
    vaults: list[dict[str, object]],
) -> None:
    system_source = workspace / "_Vault-System"
    system_target = staging / "_Vault-System"
    system_target.mkdir(parents=True)

    shutil.copy2(workspace / "AGENTS.md", staging / "AGENTS.md")
    write_text(staging / "README.md", render_release_readme(vaults))
    (staging / "_Dropzone").mkdir()

    for name in SYSTEM_DIRECTORIES:
        copy_directory(system_source / name, system_target / name)
    for name in SYSTEM_FILES:
        source = system_source / name
        if not source.is_file():
            raise FileNotFoundError(f"required framework file is missing: {source}")
        shutil.copy2(source, system_target / name)

    write_text(
        system_target / "vault-registry.json",
        json.dumps(
            {"schema_version": 1, "vaults": vaults},
            ensure_ascii=False,
            indent=2,
        ),
    )
    write_text(system_target / "vault-map.md", render_vault_map(vaults))
    copy_directory(skill, staging / ".agents" / "skills" / "ai-organize")
    for entry in vaults:
        build_vault(staging / str(entry["name"]), system_target, entry)


def audit_release(staging: Path, vaults: list[dict[str, object]]) -> None:
    allowed_root_files = {"AGENTS.md", "README.md"}
    allowed_root_directories = {
        ".agents",
        "_Dropzone",
        "_Vault-System",
        *(str(entry["name"]) for entry in vaults),
    }
    for path in staging.iterdir():
        if path.is_file() and path.name not in allowed_root_files:
            raise RuntimeError(f"unexpected release root file: {path.name}")
        if path.is_dir() and path.name not in allowed_root_directories:
            raise RuntimeError(f"unexpected release root directory: {path.name}")

    dropzone_entries = list((staging / "_Dropzone").iterdir())
    if any(path.name != GIT_PLACEHOLDER for path in dropzone_entries):
        raise RuntimeError("release _Dropzone may contain only .gitkeep")
    if not (staging / ".agents" / "skills" / "ai-organize" / "SKILL.md").is_file():
        raise RuntimeError("release is missing the project-scoped ai-organize Skill")

    registry = json.loads(
        (staging / "_Vault-System" / "vault-registry.json").read_text(
            encoding="utf-8-sig"
        )
    )
    if registry != {"schema_version": 1, "vaults": vaults}:
        raise RuntimeError("release registry does not match the selected starter Vaults")

    privacy_rule = (
        "只有用户明确要求处理本 Vault 时，Agent 才可进入本目录或读取正文。"
    )
    for entry in vaults:
        vault = staging / str(entry["name"])
        for relative in ("1-Inbox", "2-AI work", "4-Outputs", "assets"):
            files = [
                path
                for path in (vault / relative).rglob("*")
                if path.is_file() and path.name != GIT_PLACEHOLDER
            ]
            if files:
                raise RuntimeError(
                    f"starter Vault contains user-data files in {entry['name']}/{relative}"
                )
        agents_text = (vault / "AGENTS.md").read_text(encoding="utf-8-sig")
        has_privacy_rule = privacy_rule in agents_text
        if (entry["sensitivity"] == "private") != has_privacy_rule:
            raise RuntimeError(
                f"starter Vault privacy rule mismatch: {entry['name']}"
            )

    errors, warnings = validate_workspace(staging)
    if errors or warnings:
        details = [*(f"ERROR: {item}" for item in errors)]
        details.extend(f"WARNING: {item}" for item in warnings)
        raise RuntimeError("release validation failed:\n" + "\n".join(details))


def write_manifest(staging: Path) -> None:
    files = []
    for path in sorted(item for item in staging.rglob("*") if item.is_file()):
        relative = path.relative_to(staging).as_posix()
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "format_version": 1,
        "generated": date.today().isoformat(),
        "archive_root": ARCHIVE_ROOT,
        "files": files,
    }
    write_text(
        staging / "RELEASE-MANIFEST.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )


def write_archive(staging: Path, output: Path) -> None:
    temporary = output.with_name(output.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/", b"")
        for directory in sorted(
            item for item in staging.rglob("*") if item.is_dir()
        ):
            relative = directory.relative_to(staging).as_posix()
            archive.writestr(f"{ARCHIVE_ROOT}/{relative}/", b"")
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            relative = path.relative_to(staging).as_posix()
            archive.write(path, f"{ARCHIVE_ROOT}/{relative}")
    temporary.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a sanitized, self-contained framework release ZIP."
    )
    default_workspace = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--workspace",
        type=Path,
        default=default_workspace,
        help="workspace root; defaults to the parent of _Vault-System",
    )
    parser.add_argument(
        "--skill-source",
        type=Path,
        help="ai-organize Skill directory; normally detected automatically",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="output ZIP path; defaults beside the workspace directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing ZIP and checksum with the same name",
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="build a framework with no preset Vaults",
    )
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    if not (workspace / "_Vault-System").is_dir():
        parser.error(f"standardized workspace not found: {workspace}")
    output = (
        args.output.expanduser().resolve()
        if args.output
        else workspace.parent
        / f"Obsidian-Multi-Vault-Framework-{date.today():%Y%m%d}.zip"
    )
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    if not output.parent.is_dir():
        parser.error(f"output directory does not exist: {output.parent}")
    if not args.force and (output.exists() or checksum_path.exists()):
        parser.error("output already exists; choose another path or use --force")

    try:
        skill = find_skill(workspace, args.skill_source)
        vaults = [] if args.empty else [dict(entry) for entry in STARTER_VAULTS]
        with tempfile.TemporaryDirectory(prefix="obsidian-framework-release-") as temp:
            staging = Path(temp) / ARCHIVE_ROOT
            staging.mkdir()
            build_release(staging, workspace, skill, vaults)
            add_git_placeholders(staging)
            audit_release(staging, vaults)
            write_manifest(staging)
            write_archive(staging, output)
        checksum = sha256_file(output)
        write_text(checksum_path, f"{checksum}  {output.name}")
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"CREATED: {output}")
    print(f"SHA256: {checksum}")
    print(f"CHECKSUM FILE: {checksum_path}")
    if vaults:
        print("CONTENTS: Courses-Learning (public), Personal (private), empty _Dropzone")
    else:
        print("CONTENTS: empty registry, no Vaults, empty _Dropzone")
    print("SKILL: bundled project-scoped ai-organize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
