# BeeWeave

[English](README.md) | [中文](README-zh.md) | [Documentation](https://ptonlix.github.io/beeweave/) | [中文文档](https://ptonlix.github.io/beeweave/zh/)

BeeWeave 是一个 **Agent 原生的创作工作台**。它围绕创作过程构建数据飞轮：获取素材，用 Agent 辅助创作，把关键内容沉淀成长期知识，复用这些上下文，再指导下一轮更好的素材获取。

<p align="center">
  <a href="https://deepwiki.com/ptonlix/beeweave"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki" /></a>
  <a href="https://github.com/ptonlix/beeweave/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  <a href="https://x.com/Baird_cfd"><img src="https://img.shields.io/badge/@CyberFD-black?logo=x&logoColor=white" alt="X" /></a>
  <a href="https://www.zhihu.com/people/baird-66"><img src="https://img.shields.io/badge/Zhihu-CyberFD-1677FF?logo=zhihu&logoColor=white" alt="Zhihu" /></a>
</p>

<p align="center">
  <img width="768" height="512" alt="BeeWeave" src="docs/assets/beeweave.png" />
</p>

```text
获取素材 -> 创作 -> 沉淀 -> 复用上下文 -> 获取更好的素材
```

## 快速开始

在你希望创建运行时 `vault/` 和 `workbench/` 的工作区里安装并运行 setup：

```bash
pip install beeweave
bwe setup
```

随后在 Agent 中使用 BeeWeave skills：

```text
/beeweave-ingest workbench/inbox
/beeweave-query what do I know about rate limiting?
/beeweave-update
```

## 重要链接

- 完整文档：<https://ptonlix.github.io/beeweave/>
- 中文文档：<https://ptonlix.github.io/beeweave/zh/>
- 快速开始：<https://ptonlix.github.io/beeweave/zh/quickstart/>
- 架构说明：<https://ptonlix.github.io/beeweave/zh/architecture/>
- CLI 参考：<https://ptonlix.github.io/beeweave/zh/cli/>

GitHub Pages 应配置为从 `gh-pages` 分支发布，发布目录选择 `/root`。

## 常用命令

```bash
bwe info
bwe list
bwe setup --agents claude,codex
bwe setup --global-extra beeweave-capture
bwe uninstall
```

`bwe uninstall` 会移除 BeeWeave 管理的 skills、bootstrap 文件和
`~/.beeweave` 配置，但不会删除你的 `vault/` 或 `workbench/` 内容。

## 仓库结构

```text
beeweave/       # Python CLI 和辅助逻辑
.skills/        # 源 skill 定义
bootstrap/      # 用户项目 bootstrap 模板
extensions/     # 浏览器扩展资源
tests/          # pytest 测试
docs/           # MkDocs 源文档
```

运行时 `vault/` 和 `workbench/` 会由 setup 在用户选择的工作区生成，不应该提交到本仓库。

## 开发

```bash
uv run pytest
uv run bwe setup --help
uv run bwe info
uv run --group docs mkdocs build --strict
```

MkDocs 本地预览和发布流程见[开发文档](https://ptonlix.github.io/beeweave/zh/development/)。

## License

MIT
