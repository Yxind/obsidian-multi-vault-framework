# Vault System

本目录保存多 Vault 的共同维护文件，不作为 Obsidian Vault，也不存放正式知识节点。

- `vault-registry.json`：机器可读的 Vault 配置源。
- `vault-map.md`：人可读的职责地图。
- `shared-rules.md`：共同摄取、查询与隐私规则。
- `Templates-Source/`：模板母版。
- `Config-Source/`：Obsidian 基础配置母版。
- `Vault-Scaffold/`：新 Vault 的页面骨架。
- `scripts/`：新库生成、来源身份计算与校验工具。
- `scripts/sync_same_source_notices.py`：按完整哈希同步非私人 Vault 详细总结中的纯文本同源提示。
- `scripts/export_framework.py`：生成不含 Vault 内容的可移植发行包。
- `migration-checklist.md`：结构调整与迁移检查表。

正式来源必须进入某个 Vault 的 `1-Inbox/`；`_Dropzone` 与本目录都不能作为 Wiki 的来源路径。

模板、基础配置与注册表调整后必须运行工作区校验。`.obsidian/workspace.json`、`appearance.json` 等用户界面状态不属于共享配置，不得由同步工具覆盖。

## 运行环境

- Python 3.10 或更高版本。
- 只使用 Python 标准库，不需要 `pip install`。
- 新库生成器只在用户明确调用时创建一个尚不存在的 Vault，包括空的 Inbox 分类目录；日常 Agent 对既有 Inbox 没有写权限。

## 发行

运行 `python scripts/export_framework.py --help` 查看参数。默认发行包带有空的 `Courses-Learning`（`public`）和 `Personal`（`private`）两个入门 Vault、通用 Vault Map 和项目级 `.agents/skills/ai-organize`，不会复制现有 Vault、`_Dropzone` 文件或用户知识内容；使用 `--empty` 可生成无预设 Vault 的版本。
