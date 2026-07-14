# CLI

BeeWeave 提供 `bwe` 命令。

## 核心命令

```text
bwe setup             安装 skills 并写入配置
bwe profile           管理 BeeWeave profile 配置文件
bwe external          管理用户安装的外部 Agent skills
bwe uninstall         移除 BeeWeave skills 和配置
bwe upgrade           升级 BeeWeave 并刷新已安装 skills
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
bwe setup --profile work
bwe profile set-default work
bwe external install https://github.com/op7418/guizang-ppt-skill --skill guizang-ppt-skill --link-project .
bwe external list
bwe uninstall --all
bwe upgrade --check
bwe upgrade
bwe info
```

请在你希望创建运行时 `vault/` 和 `workbench/` 的工作区里运行 `bwe setup`。

默认情况下，setup 写入 `~/.beeweave/config`。使用 `--profile NAME` 会写入命名配置 `~/.beeweave/config.NAME`。setup 不负责激活命名 profile，也不会把 `~/.beeweave/config` 软链接到其它文件；在 Agent 请求里使用 `@name` 来指定命名 profile。交互式 setup 里可以选择 `new profile...`，然后输入新的 profile 名称。

如果需要把某个命名 profile 明确设为默认配置，使用 `bwe profile set-default NAME`。它会把 `~/.beeweave/config.NAME` 复制到 `~/.beeweave/config`；如果默认配置已经存在，会先创建时间戳备份，并要求输入 `YES` 后才覆盖。

如果需要卸载所有 BeeWeave profile 关联工作区中的 project-local 文件，使用
`bwe uninstall --all`。该命令仍会保留 vault 和 workbench 内容。

## 外部 Skills

使用 `bwe external` 管理第三方 Agent skills。外部 skills 不会被 vendored
进 BeeWeave 包本身，也不会写入运行时 `vault/` 或 `workbench/` 目录。

外部 skills 存放在：

```text
~/.beeweave/external/
+-- repos/       # 克隆下来的源仓库
+-- skills/      # 按 skill 名称稳定暴露的入口
+-- manifest.json
```

常用命令：

```bash
bwe external install <source> --skill <name> --link-project .
bwe external link <skill-name> --project .
bwe external list
bwe external info <skill-name>
bwe external update [skill-name]
bwe external remove <skill-name>
```

`<source>` 可以是 GitHub URL、git URL、`owner/repo` 简写、GitHub tree
URL 或本地路径。使用 `--ref` 可以指定分支、标签或 commit。

如果一个仓库里包含多个 skills，需要明确选择要安装哪一个：

```bash
bwe external install https://github.com/op7418/guizang-ppt-skill \
  --skill guizang-ppt-skill \
  --link-project .

bwe external install https://github.com/JimLiu/baoyu-skills \
  --skill baoyu-url-to-markdown

bwe external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-article-illustrator \
  --link-project .

bwe external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-image-gen \
  --link-project .

bwe external install https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-url-to-markdown
```

BeeWeave 不会默认安装多 skill 仓库里的所有 skills，除非你显式传入
`--all`。如果要把已经安装的外部 skill 链接到另一个工作区，使用
`bwe external link <skill-name> --project <path>`。

## Upgrade

使用 `bwe upgrade --check` 只检查当前安装的 BeeWeave 版本是否落后于最新包版本，不修改文件。

常规升级使用：

```bash
bwe upgrade
```

BeeWeave 会检测受支持的安装方式，并使用对应命令升级：

```bash
uv tool upgrade beeweave
python -m pip install --upgrade beeweave
```

成功升级后，BeeWeave 会复放之前 `bwe setup` 记录的安装选择，刷新对应
profile 和工作区里的 Agent skill 目录。如果没有 setup replay 状态，请手动运行一次 `bwe setup`。

源码 checkout 或暂不支持的安装方式不会被自动修改；`bwe upgrade` 会输出保守的手动升级建议。
