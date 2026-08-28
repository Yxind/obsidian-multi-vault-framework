# Repair and validation

Read this reference for explicit repair, deduplication, provenance correction, framework maintenance, or linting.

## Repair boundaries

- Restore the standard provenance topology and reciprocal links without modifying Inbox.
- Repair canonical ownership, filenames, aliases, metadata, and index routes only within the authorized scope.
- Preserve user-authored material unless replacement is explicitly requested.
- Obtain confirmation before destructive deletion, merging, cross-Vault movement, or changing a durable conclusion when local rules require it.

## Validation routing

- After shared rules, templates, configuration, registry, scripts, or cross-Vault changes, use the workspace validator when available.
- For ordinary changes in one Vault, use the workspace's Vault validator or the bundled fallback:

```powershell
python "<skill-folder>\scripts\validate_vault.py" "<active-vault-path>"
```

Fix errors. Review warnings on their merits instead of adding weak links or dummy metadata.

## Obsidian CLI

- When `obsidian` is available and connected to the target Vault, use it for relevant read-only native checks of links, properties, Bases, and history; identify the Vault explicitly.
- CLI checks supplement rather than replace the workspace validators. If unavailable, fall back without blocking the task.
- Write, rename, delete, and restore commands still require task authorization and must never modify `_Dropzone` or an established `1-Inbox`.

## Direct checks

Confirm only the checks relevant to the write:

- source and internal links resolve;
- YAML types and filenames follow the local contract;
- detailed summaries link one verifiable Inbox source and reciprocally list downstream pages;
- canonical Wiki pages have real sources and review dates and do not link Inbox directly;
- completed or rejected rough analyses are removed;
- every `-待继续` rough file contains complete progress and remains under review;
- index and log reflect actual changes;
- private or secret content did not cross its boundary;
- machine-generated same-source notice blocks match exact `source_id` plus full `content_hash`, contain no links, and exclude private Vaults by default;
- Inbox files remain byte-for-byte untouched.
