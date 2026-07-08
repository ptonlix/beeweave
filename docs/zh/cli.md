# CLI

BeeWeave 提供 `bwe` 命令。

## 核心命令

```text
bwe setup             安装 skills 并写入配置
bwe uninstall         移除 BeeWeave skills 和配置
bwe list              列出内置 skills
bwe info              查看安装路径、版本和配置
```

## 知识与图谱辅助命令

```text
bwe graph-query       查询 vault wikilink index
bwe graph-analyse     分析 vault 图结构
bwe batch-plan        规划并行 ingest batches
```

## 缓存和源码辅助命令

```text
bwe cache-check       根据 .manifest.json 检查素材变化
bwe cache-update      ingest 后记录素材 hash
bwe cache-hash        计算素材 hash
bwe ast-extract       无需 LLM，提取代码结构
```

## Setup 示例

```bash
bwe setup --agents claude,codex
bwe setup --global-extra beeweave-capture
bwe setup --profile work --activate
bwe info
```

请在你希望创建运行时 `vault/` 和 `workbench/` 的工作区里运行 `bwe setup`。

默认情况下，setup 写入 `~/.beeweave/config`。使用 `--profile NAME` 会写入命名配置 `~/.beeweave/config.NAME`。再加 `--activate` 会让 `~/.beeweave/config` 指向这个命名 profile。交互式 setup 里可以选择 `new profile...`，然后输入新的 profile 名称。
