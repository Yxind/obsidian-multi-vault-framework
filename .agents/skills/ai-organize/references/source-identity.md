# Source identity

Read this reference when creating a detailed summary.

## Fields

- `content_hash`: the complete SHA-256 of the source file bytes, formatted as `sha256:<64 lowercase hex characters>`.
- `source_id`: the exact source-version identity, formatted as `src-<first 16 characters of SHA-256>`.

Calculate the default values without modifying Inbox:

```powershell
python "<skill-folder>\scripts\source_identity.py" "<source-file>"
```

## Independence rules

- Byte-identical copies have the same hash and `source_id` and count once.
- Changed content has a new hash and `source_id`.
- In this multi-Vault workspace, a plain-text same-source notice may be generated only when both the complete `content_hash` and `source_id` match. Do not infer exact identity from filenames, titles, URLs, or `source_id` alone.
- When rewrites, reposts, series entries, or collections are obviously dependent, record that relationship in the detailed summary and do not present them as independent corroboration. No routine metadata field is required.
- Detailed summaries, Wiki pages, answers, and outputs are provenance or synthesis artifacts, not new evidence.
