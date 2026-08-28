# 工作区框架说明

本文件只在修改框架、模板、配置、生成器或校验器时读取。日常粗剪、总结、摄取、查询和修复由 `ai-organize` Skill 按模式加载说明；权限以父级与当前 Vault 的 `AGENTS.md` 为准。

## 目录职责

- `1-Inbox/`：用户维护的原始证据。
- `2-AI work/`：临时粗剪与长期保留的详细总结。
- `3-Wiki/`：可复用的长期知识。
- `4-Outputs/`：交付成果，不是证据层。
- `Templates/`、`assets/`：模板副本与附件。

标准 Inbox 分类为 `00-Unsorted`、`Personal-Private`、`Books-Courses`、`Media`、`Articles-Web`、`Papers-Reports`、`Project-Materials`。

## 本地数据约定

- 同一 Vault 内所有 Markdown 与 Base 文件名唯一；Inbox 保留源文件名。
- 粗剪：`<源文件名>-AI 粗剪.md`；真正等待继续时：`<源文件名>-AI 粗剪-待继续.md`；详细总结：`<源文件名>-详细总结.md`。
- 来源桥接固定为 `Inbox 原始文件 ← 详细总结 ↔ 下游知识节点`；Wiki 不直接链接 Inbox。
- 详细总结保存一个 Inbox 来源及其 `source_id`、`content_hash`。身份写入总结，不修改 Inbox。
- `content_hash` 为完整 SHA-256；`source_id` 为 `src-<哈希前16位>`。相同 `source_id` 只算一份来源。
- 同一来源可以由用户复制到多个 Inbox；各 Vault 只处理本库范围，不建立跨库链接或人工注册表。非私人 Vault 中存在完整 `content_hash` 与 `source_id` 都一致的详细总结时，由 `sync_same_source_notices.py` 在各总结中机械维护纯文本提示，引用其他 Vault 的“本 Vault 的处理范围”；私人 Vault 默认不参与。

## 页面模型

- Topic：综合问题、场景、约束及方法组合。
- Concept：脱离当前项目仍可复用的单一机制或方法。
- Tool：可执行清单、配置、模板或验收标准。
- People：人物及其可核验观点。
- 新内容优先链接或更新规范页；只有职责独立且可长期复用时才新建页面。

Wiki 属性为 `created`、`updated`、`type`、`status`、非空 `sources`、`last_reviewed`、`aliases`、`tags`。敏感级别只存于 `vault-registry.json`，普通页面、模板和 Base 不使用 `sensitivity`。

- `seed`：单一或少量来源，仍需验证。
- `growing`：至少两个不同 `source_id` 支持并持续更新；明显相互依赖的材料仍需人工降权。
- `mature`：定义、证据、边界与复核状态稳定。

## 多 Vault 系统

- `vault-registry.json` 是脚本使用的唯一 Vault 配置源。
- `vault-map.md` 是人类与 Agent 分流时使用的职责地图；注册表区块由生成器维护。
- 一份来源默认选择一个主要问题所有者；确有多个独立用途时，由用户复制到多个 Inbox，各库独立处理。
- 注册表中 `sensitivity: private` 的 Vault 承担私人来源；原文默认不跨库，迁出内容必须由用户明确授权并先脱敏。

## 模板与配置

- `Templates-Source/` 是模板母版，各 Vault 的 `Templates/` 保持一致副本。
- `Config-Source/` 是共享 Obsidian 配置；界面状态不进入母版。
- 用户在 Obsidian 中新建的笔记默认进入 `1-Inbox/00-Unsorted/`，自动更新链接开启；AI 创建文件时必须显式选择 Inbox 之外的目标路径，且不得写入既有 Inbox。
- `Vault-Scaffold/` 是新 Vault 文本骨架；新库只能由 `new_vault.py` 生成。
- `vault-map.md` 的注册表区块与子 Vault 的领域信息由注册表和生成器维护，不手工复制现有 Vault。
- 入门发行包只能由 `export_framework.py` 按白名单生成：默认建立一个 `public` 课程 Vault 和一个 `private` 个人 Vault，但不包含现有 Vault、用户内容或暂存文件，并内置项目级 `ai-organize` Skill；确需纯空框架时使用 `--empty`。

## 校验

- 修改注册表、共享规则、模板、配置或脚本后运行 `python _Vault-System/scripts/validate_workspace.py`。
- 新建、删除或更新可能与其他非私人 Vault 同源的详细总结后，先运行 `python _Vault-System/scripts/sync_same_source_notices.py --write`，再运行全库校验。
- 日常内容写入按 Skill 指示运行当前 Vault 校验。
- 校验器负责可机械判断的结构约束；不要把同一约束再复制进父规则、子规则和 Skill。
