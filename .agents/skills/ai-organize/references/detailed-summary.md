# Detailed summary

Read this reference only when creating or updating the durable source bridge.

Write `2-AI work/<source-basename>-详细总结.md` with:

- dates, `type: synthesis`, `status: review`, one Inbox `source`, and tags;
- `source_id` and `content_hash` calculated according to `source-identity.md` without modifying Inbox.

Include:

1. a conclusion-first overview;
2. a section, chapter, or task map;
3. concrete knowledge grouped by topic rather than transcript order;
4. contradictions, confidence limits, time-sensitive claims, privacy exclusions, and any known rewrite, repost, series, or collection dependency;
5. candidate decisions using the ownership reference;
6. downstream pages, ingestion progress, and a clear statement when no Wiki ingestion has occurred.

Keep `本 Vault 的处理范围` to one or two short plain-text sentences without cross-Vault links. When the same exact source has detailed summaries in more than one non-private Vault, run the workspace's `sync_same_source_notices.py --write`; its generated block may quote that scope text in the other summaries. Do not edit the generated block manually. Private Vaults remain excluded unless the user gives separate explicit authorization.

The summary links exactly one verifiable Inbox source. Every downstream page links back to it, and it lists every downstream page.

Retain the summary after the final decision. Keep `status: review` during genuine partial ingestion; use `archived` after the selected scope is complete or explicitly declined.
