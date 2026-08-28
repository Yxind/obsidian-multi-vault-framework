# Obsidian Multi-Vault Framework

这是一个不含个人知识内容的 Obsidian 多 Vault 框架。父目录用于 Codex 跨库管理，不是 Obsidian Vault。

## 获取发行版

- 可以直接克隆仓库；空目录内的 `.gitkeep` 只用于保留框架结构，不是 Inbox 来源或知识内容。
- 也可以从 GitHub Releases 下载固定版本 ZIP；ZIP 适合复制到其他电脑或交给他人部署。

## 预设 Vault

- `Courses-Learning/`：`public`，用于公开课程、学习资料、练习和可复用方法。
- `Personal/`：`private`，用于依赖个人身份、私人关系或私人时间线的资料。

两个 Vault 都已完成标准初始化，可以直接在 Obsidian 中分别打开。

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
