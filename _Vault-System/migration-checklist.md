# Vault 结构调整检查表

## 建立阶段

- [ ] 新 Vault 建议有实际 `_Dropzone` 文件依据，而非由单个异常文件或抽象分类推导。
- [ ] 用户已经明确下达新建命令，并确认名称、范围、排除项、路由问题与 Vault 级敏感度。
- [ ] 父目录不是 Obsidian Vault，根目录没有 `.obsidian/`。
- [ ] 新 Vault 已通过 `new_vault.py` 创建并写入 `vault-registry.json` 与 `vault-map.md`。
- [ ] 每个子 Vault 有独立 `.obsidian/`、`AGENTS.md`、`Templates/`、`assets/`、`2-AI work/`、`3-Wiki/` 与 `4-Outputs/`。
- [ ] `new_vault.py` 只在用户明确调用时建立空的 `1-Inbox/` 与标准分类目录；生成后 Agent 不再写入 Inbox。
- [ ] Obsidian 已把子目录注册为 Vault。
- [ ] 新文件目录、附件目录、模板目录与链接格式已检查。
- [ ] Daily Notes 默认关闭；需要时为该 Vault 明确登记并配置目录与模板。

## 迁移阶段

- [ ] 先备份旧库，不覆盖或删除原库。
- [ ] 按来源、详细总结、下游节点与附件作为一组迁移，避免拆断来源桥接。
- [ ] 每组内容默认只选择一个目标 Vault；确有多个独立用途时可复制来源，各库独立处理。
- [ ] 为详细总结计算 `source_id` 与 `content_hash`。
- [ ] 字节一致的多库副本具有相同 `source_id` 与 `content_hash`；无需跨库登记或链接，非私人 Vault 只由同步脚本维护详细总结中的纯文本同源提示。
- [ ] 修正 Vault 根路径变化导致的完整路径 Wikilink。
- [ ] 更新各 Vault 的索引与日志。
- [ ] 含身份信息的材料只进入 `sensitivity: private` 的 Vault；跨库只使用经用户授权的脱敏内容。

## 验收阶段

- [ ] `validate_workspace.py` 返回 0 个错误。
- [ ] 所有来源桥接双向对称，Wiki 不直接链接 Inbox。
- [ ] 没有重复节点；每个 Vault 的来源桥接在本库内完整。
- [ ] 每个 Vault 的总结只摄取与本库职责相关的知识。
- [ ] 所有 Wiki 的 `sources` 与 `last_reviewed` 完整；普通页面没有冗余 `sensitivity` 属性。
- [ ] 部分摄取粗剪具有 `-待继续` 文件名与完整摄取进度。
- [ ] 新 Vault 可独立搜索、打开附件并使用模板。
- [ ] 旧库只在用户确认新库稳定后再决定是否归档。
