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

- `beeweave-article-illustration`：通过 `baoyu-article-illustrator` 和
  `baoyu-image-gen` 设置并运行文章配图，默认统一使用 API 图片生成，而不是各
  Agent 的运行时原生图片工具。
- `beeweave-article-writer`：起草长文、博客、文章和观点稿。
- `beeweave-article-publisher`：把完成稿移动到
  `workbench/articles/published/`，并把发布内容 ingest 进 vault。
- `beeweave-ppt-writer`：在 `workbench/ppt/` 下创建 HTML PPT 项目，需要时
  可配合 `guizang-ppt-skill` 等外部 PPT skills 使用。
- `beeweave-social-writer`：起草 X/Twitter 帖子、thread、短观点和社交文案。
- `beeweave-writing-style-initializer`：初始化 `workbench/writing/style/`
  下的写作风格资产模板。
- `beeweave-writing-style-learner`：从历史文章、写作 trace、用户改稿、AI
  按用户指令改稿和明确反馈中提炼候选写作风格规则。
- `beeweave-writing-skill-evolver`：审阅候选规则，按路由层、指令层、资源层
  分类，验证后激活、拒绝、回滚或压缩写作风格资产。
- `beeweave-url-capture`：把 URL 下载到 `workbench/inbox/web/`，形成自包含的
  原始捕获包，然后交给 `/beeweave-ingest workbench/inbox`。
- `baoyu-url-to-markdown`：`beeweave-url-capture` 使用的项目本地 URL 抽取依赖；
  它不会作为默认全局 skill 安装。

自进化写作的完整说明已拆到单独页面：见[自进化写作工作流](self-evolving-writing.md)。

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

## 文章配图 Setup

当工作区需要给文章生成配图时，使用 `beeweave-article-illustration`。该 skill
会安装并链接两个必需的 Baoyu 上游 skills：

```bash
bwe external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-article-illustrator \
  --link-project .

bwe external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-image-gen \
  --link-project .
```

setup 会在当前 workspace/project root 下的 `./.baoyu-skills/` 写入项目级 Baoyu 配置，并把
`baoyu-article-illustrator` 固定为 `preferred_image_backend:
baoyu-image-gen`。它不会配置 Codex `imagegen`、Cursor `GenerateImage`、
Hermes `image_generate` 或其它运行时原生图片工具。
固定输出布局是文章目录内的 `imgs/`：Agent 会先在需要时把 Markdown 文件整理到
文章专属目录，再让 Baoyu 插入 `imgs/NN-{type}-{slug}.png` 这样的相对链接。

图片 provider 来自 `baoyu-image-gen` 支持的 API providers，例如 OpenAI、
Google、DashScope、OpenRouter、Azure、Z.AI、MiniMax、Replicate、Jimeng、
Seedream 或 Agnes。凭证放在当前 workspace/project root 下的
`./.baoyu-skills/.env`，不要提交这个文件。自定义 provider endpoint/base URL
也通过同一个 env 文件配置，例如
`OPENAI_BASE_URL`、`GOOGLE_BASE_URL`、`OPENROUTER_BASE_URL`、
`DASHSCOPE_BASE_URL`、`ZAI_BASE_URL`、`MINIMAX_BASE_URL`、
`REPLICATE_BASE_URL`、`JIMENG_BASE_URL`、`SEEDREAM_BASE_URL`、
`AGNES_BASE_URL`，以及 Azure 必需的 `AZURE_OPENAI_BASE_URL`。

provider 配置创建或更新后，先运行非扣费 doctor：

```bash
bwe illustrate doctor --provider <provider>
```

doctor 会写入 `./.baoyu-skills/doctor.json`。后续配图请求会复用这次通过缓存；
只要 provider、模型、base URL、相关环境变量和 Baoyu skill 文件没有变化，就不重复检测。
如果用户明确同意做一次真实最小图片探测，再运行：

```bash
bwe illustrate doctor --provider <provider> --probe-image
```

`--probe-image` 可能产生 provider 费用。BeeWeave 会原样使用配置的 base URL；
不会自动补 `/v1`、推导 endpoint 或改写 URL。

setup 完成后，可以让 Agent 按固定默认值给文章配图：

```text
/beeweave-article-illustration path/to/article.md 直接生成
```

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
