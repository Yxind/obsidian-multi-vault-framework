#!/usr/bin/env python3
"""Focused regression tests for provenance and cross-Vault validation."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sync_same_source_notices import NOTICE_START, plan_same_source_updates
from validate_vault import validate_vault
from validate_workspace import validate_workspace


class SameSourceNoticeTests(unittest.TestCase):
    def build_workspace(
        self,
        root: Path,
        *,
        second_sensitivity: str = "internal",
        exact_match: bool = True,
    ) -> tuple[Path, Path]:
        system = root / "_Vault-System"
        system.mkdir()
        registry = {
            "schema_version": 1,
            "vaults": [
                {"name": "Vault-A", "sensitivity": "internal"},
                {"name": "Vault-B", "sensitivity": second_sensitivity},
            ],
        }
        (system / "vault-registry.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        paths = []
        for name, scope, marker in (
            ("Vault-A", "只处理技术方法。", "a"),
            ("Vault-B", "只处理观点与写作。", "a" if exact_match else "b"),
        ):
            summary = root / name / "2-AI work" / "source-详细总结.md"
            summary.parent.mkdir(parents=True)
            summary.write_text(
                f'''---
type: synthesis
source_id: "src-{marker * 16}"
content_hash: "sha256:{marker * 64}"
---

# Summary

## 本 Vault 的处理范围

{scope}

## 结论先行

测试。
''',
                encoding="utf-8",
            )
            paths.append(summary)
        return paths[0], paths[1]

    def test_exact_match_generates_plain_text_notices(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = self.build_workspace(root)
            errors, updates = plan_same_source_updates(root)
            self.assertEqual(errors, [])
            self.assertEqual({path for path, _ in updates}, {first, second})
            generated = dict(updates)
            self.assertIn(NOTICE_START, generated[first])
            self.assertIn("Vault-B：只处理观点与写作。", generated[first])
            self.assertNotIn("[[Vault-B", generated[first])

            for path, text in updates:
                path.write_text(text, encoding="utf-8")
            errors, updates = plan_same_source_updates(root)
            self.assertEqual(errors, [])
            self.assertEqual(updates, [])

    def test_private_vault_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.build_workspace(root, second_sensitivity="private")
            errors, updates = plan_same_source_updates(root)
            self.assertEqual(errors, [])
            self.assertEqual(updates, [])

    def test_changed_bytes_do_not_create_an_association(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.build_workspace(root, exact_match=False)
            errors, updates = plan_same_source_updates(root)
            self.assertEqual(errors, [])
            self.assertEqual(updates, [])


class WorkspaceValidatorTests(unittest.TestCase):
    def test_empty_release_workspace_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            system = root / "_Vault-System"
            (system / "Templates-Source").mkdir(parents=True)
            (system / "vault-registry.json").write_text(
                json.dumps({"schema_version": 1, "vaults": []}),
                encoding="utf-8",
            )
            (system / "vault-map.md").write_text(
                "# Vault Map\n\n"
                "<!-- VAULT-REGISTRY:START -->\n"
                "<!-- VAULT-REGISTRY:END -->\n",
                encoding="utf-8",
            )

            errors, warnings = validate_workspace(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])


class VaultValidatorTests(unittest.TestCase):
    def build_vault(
        self,
        root: Path,
        *,
        status: str = "seed",
        source_count: int = 1,
        sources_override: str | None = None,
        reciprocal: bool = True,
        source_field_override: str | None = None,
        wiki_body_links: bool = False,
    ) -> Path:
        vault = root / "Vault"
        inbox = vault / "1-Inbox" / "Articles-Web"
        ai_work = vault / "2-AI work"
        concepts = vault / "3-Wiki" / "Concepts"
        for directory in (inbox, ai_work, concepts):
            directory.mkdir(parents=True, exist_ok=True)

        source_links: list[str] = []
        for index in range(1, source_count + 1):
            source_name = f"source-{index}.txt"
            source = inbox / source_name
            source.write_text(f"evidence {index}\n", encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            summary_name = f"source-{index}-详细总结"
            declared_source = (
                source_field_override
                if index == 1 and source_field_override is not None
                else f'"[[1-Inbox/Articles-Web/{source_name}|原文]]"'
            )
            body_links = []
            if source_field_override is not None and index == 1:
                body_links.append(f"[[1-Inbox/Articles-Web/{source_name}|原文]]")
            if reciprocal:
                body_links.append("[[3-Wiki/Concepts/Test]]")
            summary = f'''---
created: 2026-08-28
updated: 2026-08-28
type: synthesis
status: archived
source: {declared_source}
source_id: "src-{digest[:16]}"
content_hash: "sha256:{digest}"
tags: []
---

# Summary {index}

{' '.join(body_links)}
'''
            (ai_work / f"{summary_name}.md").write_text(
                summary, encoding="utf-8"
            )
            source_links.append(f'  - "[[2-AI work/{summary_name}]]"')

        sources = sources_override or "sources:\n" + "\n".join(source_links)
        body = ""
        if wiki_body_links:
            body = "\n".join(
                f"[[2-AI work/source-{index}-详细总结]]"
                for index in range(1, source_count + 1)
            )
        wiki = f'''---
created: 2026-08-28
updated: 2026-08-28
type: concept
status: {status}
{sources}
last_reviewed: 2026-08-28
aliases: []
tags: []
---

# Test

{body}
'''
        (concepts / "Test.md").write_text(wiki, encoding="utf-8")
        (vault / "3-Wiki" / "index.md").write_text(
            "[[3-Wiki/Concepts/Test]]\n", encoding="utf-8"
        )
        return vault

    def validate(self, vault: Path) -> list[str]:
        errors, _, _, _ = validate_vault(vault)
        return errors

    def test_valid_seed_with_one_detailed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(Path(temp))
            self.assertEqual(self.validate(vault), [])

    def test_sources_must_contain_real_summary_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(
                Path(temp),
                sources_override="sources: [not-a-source]",
                wiki_body_links=True,
            )
            errors = self.validate(vault)
            self.assertTrue(
                any("sources must contain detailed-summary" in item for item in errors)
            )

    def test_summary_link_must_be_reciprocal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(Path(temp), reciprocal=False)
            errors = self.validate(vault)
            self.assertTrue(any("not reciprocal" in item for item in errors))

    def test_summary_source_field_must_hold_the_inbox_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(
                Path(temp), source_field_override="not-a-link"
            )
            errors = self.validate(vault)
            self.assertTrue(
                any("source field must contain exactly one link" in item for item in errors)
            )

    def test_growing_requires_two_distinct_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(Path(temp), status="growing")
            errors = self.validate(vault)
            self.assertTrue(
                any("requires at least two distinct source_id" in item for item in errors)
            )

    def test_growing_accepts_two_distinct_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            vault = self.build_vault(
                Path(temp), status="growing", source_count=2
            )
            self.assertEqual(self.validate(vault), [])


if __name__ == "__main__":
    unittest.main()
