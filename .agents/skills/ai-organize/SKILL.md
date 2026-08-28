---
name: ai-organize
description: Organize and query Obsidian knowledge from a read-only 1-Inbox through disposable rough analyses and durable detailed summaries into source-backed, user-confirmed Wiki pages. Use for rough cuts, summaries, ingestion, source-backed queries, multi-vault routing, provenance repair, deduplication, and vault validation.
---

# AI Organize

Organize source evidence into traceable Obsidian knowledge with minimal context loading.

## Load only the active contract

1. Read the nearest applicable `AGENTS.md`; inherited parent rules already apply, so do not reopen them merely to confirm identical text.
2. Do not automatically load a workspace registry, Vault map, shared rules, every child Vault rule, or every reference. Read one only when the local `AGENTS.md` or the current mode requires it.
3. Treat the selected Vault as the write boundary. Local rules override this skill when stricter or more specific.
4. If several modes are requested, read the union of their references once. Re-read only when a file changed during the task.

## Non-negotiable defaults

- An established `1-Inbox/` is user-owned evidence: read only. The user owns source placement, copying, movement, renaming, and deletion.
- A parent `_Dropzone` is a routing queue, not an ingestion source.
- The provenance path is `Inbox source ← detailed summary ↔ downstream knowledge`; Wiki pages do not link Inbox directly.
- Creating or substantively updating Wiki requires explicit ingestion intent and a verifiable source. A query, inspection, summary, or recommendation does not authorize persistence.
- One `source_id` is one exact source. Identical copies count once within a page. Note rare rewrite, repost, series, or collection dependencies only when materially relevant.
- Do not copy secrets or unnecessary private details. Honor any Vault-specific access boundary in local rules.

## Select a mode and its references

- **Dropzone or cross-Vault routing; query:** read [references/routing-query.md](references/routing-query.md).
- **Rough analysis:** read [references/rough-analysis.md](references/rough-analysis.md) and [references/knowledge-ownership.md](references/knowledge-ownership.md).
- **Detailed summary:** read [references/detailed-summary.md](references/detailed-summary.md), [references/knowledge-ownership.md](references/knowledge-ownership.md), and [references/source-identity.md](references/source-identity.md).
- **Confirmed Wiki ingestion:** read [references/wiki-ingestion.md](references/wiki-ingestion.md) and [references/knowledge-ownership.md](references/knowledge-ownership.md). Read source identity only if the summary identity is missing or changing.
- **Repair, lint, framework validation:** read [references/repair-validation.md](references/repair-validation.md). Add a mode reference only when repairing that mode's artifacts.

Do not read unrelated references.

## Choose the least-destructive mode

1. Rough analysis for value, privacy, routing, and candidate decisions.
2. Detailed summary when important structure must be retained.
3. Wiki ingestion only after confirmation such as `摄取`, selected candidates, checked items, or `全部摄取`.
4. Repair for an explicitly requested correction, deduplication, provenance fix, or validation task.

When intent is ambiguous, stop after analysis or summary.

## Shared execution rules

- Resolve the exact source and active Vault; verify the evidence is inspectable.
- Read short sources fully. For large sources, map the structure and process bounded sections through the required scope.
- Search existing filenames, aliases, headings, index routes, and likely owners before proposing or writing a page.
- Never silently create numbered duplicates or replace user-authored material without authorization.
- Distinguish sourced fact, synthesis, inference, judgment, and pending verification.
- Run the validation required by the active mode and local workspace; fix errors and assess warnings rather than hiding them.

## Report

State the source, Vault, mode, changed files, ownership decisions, validation result, and only the next unresolved human decision.
