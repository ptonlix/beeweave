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

Workbench/project-local skills 包括：

- `beeweave-article-writer`：起草长文、博客、文章和观点稿。
- `beeweave-article-publisher`：把完成稿移动到
  `workbench/articles/published/`，并把发布内容 ingest 进 vault。
- `beeweave-ppt-writer`：在 `workbench/ppt/` 下创建 HTML PPT 项目，需要时
  可配合 `guizang-ppt-skill` 等外部 PPT skills 使用。
- `beeweave-social-writer`：起草 X/Twitter 帖子、thread、短观点和社交文案。
- `beeweave-url-capture`：把 URL 下载到 `workbench/inbox/web/`，形成自包含的
  原始捕获包，然后交给 `/beeweave-ingest workbench/inbox`。
- `baoyu-url-to-markdown`：`beeweave-url-capture` 使用的项目本地 URL 抽取依赖；
  它不会作为默认全局 skill 安装。

## 外部 Skills

外部 skills 是由用户安装的第三方 Agent skills，通过 `bwe external` 管理。
它们存放在 BeeWeave 运行目录之外：

```text
~/.beeweave/external/
+-- repos/       # 克隆下来的源仓库
+-- skills/      # 按 skill 名称稳定暴露的入口
+-- manifest.json
```

安装一个外部 skill，并链接到当前工作区：

```bash
bwe external install https://github.com/op7418/guizang-ppt-skill \
  --skill guizang-ppt-skill \
  --link-project .
```

对于包含多个 skills 的仓库，请使用 `--skill` 或 `--path` 明确选择；
BeeWeave 不会默认安装整个多 skill 仓库，除非你显式传入 `--all`。

外部 skills 不会被打包进 BeeWeave wheel、源码 `.skills/` 目录、vault 或
workbench。使用 `bwe external list` 和 `bwe external info <skill-name>`
可以查看本机已经安装的外部 skills。

## 命名 Profile 路由

可以创建 `~/.beeweave/config.work` 这样的命名配置。每个配置都是一套完整的 BeeWeave profile，包括 vault 路径、workbench 路径、QMD 设置和工具专用路径。然后只为单次请求使用 `@name`：

```text
beeweave-query @work what do I know about deployment rollbacks?
@research update my BeeWeave vault
```

该覆盖只影响当前请求。

如果要把某个命名 profile 设为之后不带 `@name` 时使用的默认配置，运行：

```bash
bwe profile set-default work
```

BeeWeave 会先备份已有的 `~/.beeweave/config`，再把
`~/.beeweave/config.work` 复制过去。

![技能作用范围](../assets/skills-scope-map.png)
