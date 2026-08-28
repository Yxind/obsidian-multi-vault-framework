# Rough analysis

Read this reference only when creating or continuing an AI rough analysis.

Write `2-AI work/<source-basename>-AI 粗剪.md` with metadata compatible with the Vault contract, normally:

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: analysis
status: review
source: "[[1-Inbox/path/to/source|原文]]"
value: 高
tags: [主题标签]
---
```

Keep it concise and include:

- the source link;
- a high, medium, or low value judgment with a source-grounded reason;
- three to seven compressed core points;
- reusable methods, frameworks, data, checklists, or ideas with locations;
- candidate handling using link, update, create, or keep-local decisions;
- privacy or risk only when action is required;
- an empty `我的想法` section.

Use a detailed summary instead when compression would hide important structure.

## Partial-ingestion progress

- Use `<source-basename>-AI 粗剪-待继续.md` only when the user wants one portion now and intends to resume the remainder later.
- Record completed scope, remaining scope, next starting point, and last update; keep `status: review`.
- If the user says the selected portion is sufficient or abandons the remainder, the choice is complete: finalize the detailed summary and delete the rough file.
- Rough files are disposable and are never archived. Retain one only while a real review or continuation remains.
