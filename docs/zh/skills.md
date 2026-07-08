# 技能

BeeWeave skills 是面向 Agent 的工作流，用来在 workbench、vault 和当前项目上下文之间移动素材。

## 默认全局技能

- `beeweave-update`：把项目中的有用知识同步到 vault。
- `beeweave-query`：基于编译后的 vault 上下文回答问题。
- `beeweave-ingest`：把素材处理成可长期保存的笔记。

这些 skills 默认全局安装，因为它们跨项目可复用。

## 可选高级全局技能

高级技能需要显式安装：

```bash
bwe setup --global-extra beeweave-capture,beeweave-status
```

示例：

- `beeweave-capture`
- `beeweave-context-pack`
- `beeweave-digest`
- `beeweave-status`
- `beeweave-memory-bridge`

## 项目本地技能

完整 BeeWeave skill 集会安装到你选择的项目本地 Agent 目录中。这样其它项目保持干净，而 BeeWeave 工作区拥有完整工作流能力。

## 命名 Profile 路由

可以创建 `~/.beeweave/config.work` 这样的命名配置。每个配置都是一套完整的 BeeWeave profile，包括 vault 路径、workbench 路径、QMD 设置和工具专用路径。然后只为单次请求使用 `@name`：

```text
beeweave-query @work what do I know about deployment rollbacks?
@research update my BeeWeave vault
```

该覆盖只影响当前请求。

![技能作用范围](../assets/skills-scope-map.png)
