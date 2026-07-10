## 概要

<!-- 用 2-4 句话说明这个 PR 解决什么问题，以及采用了什么方案。 -->

Closes #

## 变更内容

<!-- 列出关键改动。保持聚焦，避免展开实现细节。 -->

- 

## 影响范围

<!-- 勾选主要影响面。 -->

- [ ] CLI / setup / profile
- [ ] Skills / Agent workflow
- [ ] Workbench / inbox
- [ ] Vault / ingest / query
- [ ] Documentation
- [ ] Browser extension
- [ ] Tests / CI
- [ ] Other

## 验证

<!-- 写明你实际运行过的检查。文档-only 变更可以说明未运行测试的原因。 -->

- [ ] `make check`
- [ ] `uv run pytest`
- [ ] `uv run bwe setup --help`
- [ ] `uv run bwe info`
- [ ] 未运行测试，原因：

## 风险和回滚

<!-- 说明潜在风险、兼容性影响、迁移成本或回滚方式。没有也请写“无已知风险”。 -->

- 

## 合并前检查

- [ ] 已关联或关闭相关 issue。
- [ ] 改动范围和 PR 目标一致，没有混入无关重构。
- [ ] 未修改用户生成的 `vault/` 或 `workbench/` 运行时目录。
- [ ] 如修改 CLI 人类可读输出，已优先使用 `beeweave/ui.py`。
- [ ] 如修改 machine-readable 命令，未破坏 JSON/plain-text 输出契约。
- [ ] 如同步或包装外部 skill，已保留上游 attribution，且未无意修改 vendored 原文。
