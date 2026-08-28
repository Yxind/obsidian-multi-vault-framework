# 多 Vault 工作区规则

本目录是 Codex 的跨库管理工作区，不是 Obsidian Vault；不得在根目录创建 `.obsidian/`。

## 不可越过的权限边界

- `_Dropzone/` 由用户维护。AI 只能读取和提出建议，不得创建、编辑、移动、复制、重命名或删除其中的文件或目录。
- 既有 `1-Inbox/` 严格只读；分析、巡视和建议不授权新建 Vault。只有用户明确命令后才可运行标准生成器，AI 不得手工操作 Inbox，生成器也不搬运来源。
- `_Dropzone` 只是分流队列，不是来源层；文件进入目标 Inbox 后才能粗剪、总结或摄取。
- 父目录任务、其他 Vault 任务和常规巡视默认不得读取注册表中 `sensitivity: private` 的 Vault 正文；只有用户明确要求处理对应私人 Vault 时才可进入。
- 删除、合并、改变长期结论或跨 Vault 移动长期页面、总结和附件前，先取得用户确认并说明链接影响。

## 同源文件的最低成本关联

- 非私人 Vault 中的详细总结若具有完全一致的 `source_id` 与 `content_hash`，允许由 `_Vault-System/scripts/sync_same_source_notices.py` 跨 Vault 机械维护“跨 Vault 同源提示”块；这是唯一不需要逐次确认的跨 Vault 写入例外。
- 提示只写其他 Vault 名称及其详细总结中“本 Vault 的处理范围”，不建立链接、不复制结论，也不得修改提示块之外的正文。
- 注册表中 `sensitivity: private` 的 Vault 默认不参与扫描或提示；涉及私人 Vault 时仍需用户另行明确授权。

## 按需读取

- 在某个子 Vault 工作：读取该 Vault 的 `AGENTS.md`；涉及来源整理时使用 `ai-organize` Skill，并且只读其当前模式所指向的 reference。
- 在 `_Dropzone` 分流：读取 `_Vault-System/vault-map.md`；只有修改注册表或运行系统脚本时才读 `vault-registry.json`。
- 修改框架、模板、配置、生成器或校验器：再读取 `_Vault-System/shared-rules.md`。
- 不要为了确认相同规则而重复读取父规则、共享规则和 Skill；上级规则已经生效，子文件只补充差异。

## 系统入口

- 人类可读路由：`_Vault-System/vault-map.md`
- 机器配置：`_Vault-System/vault-registry.json`
- 框架维护说明：`_Vault-System/shared-rules.md`
- 新建 Vault：`python _Vault-System/scripts/new_vault.py --help`
- 同步同源纯文本提示：`python _Vault-System/scripts/sync_same_source_notices.py --write`
- 导出无内容入门发行包：`python _Vault-System/scripts/export_framework.py --help`
- 全库校验：`python _Vault-System/scripts/validate_workspace.py`

修改注册表、共享规则、模板、配置或脚本后，必须运行全库校验。
