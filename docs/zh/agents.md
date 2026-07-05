# Agent

BeeWeave 会在 setup 时把共享上下文和 skills 安装到你选择的 Agent。

## 支持目标

```text
claude, cursor, windsurf, generic, pi, kiro, gemini, antigravity,
codex, hermes, openclaw, copilot, trae, trae-cn
```

项目本地 setup 会安装完整 BeeWeave skills 和 bootstrap 文件。全局 setup 保持克制，避免其它项目无意继承完整 BeeWeave 工作台。

## Bootstrap 文件

根据选择的目标，setup 可能写入：

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `HERMES.md`
- Cursor rules
- Windsurf rules
- Kiro steering
- Antigravity rules 与 workflows
- Copilot instructions

这些文件会告诉 Agent 如何使用同一套 `vault/` 和 `workbench/`，避免上下文困在某一次聊天或某一个工具里。

## 安装策略

- 全局安装：默认 portable skills 和显式选择的高级 skills。
- 项目本地安装：为选中的工作区安装完整 BeeWeave skill 集。
- 运行时数据：在用户工作区创建，不在本仓库创建。

![Agent 安装目标](../assets/agent-install-targets.png)
