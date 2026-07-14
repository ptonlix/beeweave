# Dependency Resolution

使用本 reference 安装、链接和定位 `baoyu-article-illustrator` 与 `baoyu-image-gen`。两个 skills 都是必需依赖。

## Project-Local First

对每个必需 skill 分别执行同一套流程。只要项目本地已经存在可用 `SKILL.md`，就直接使用，不要重新安装或重新链接。

先检查当前项目已经存在的 Agent skills 目录：

```text
.codex/skills/<skill>/SKILL.md
.claude/skills/<skill>/SKILL.md
.agents/skills/<skill>/SKILL.md
.cursor/skills/<skill>/SKILL.md
.windsurf/skills/<skill>/SKILL.md
.kiro/skills/<skill>/SKILL.md
.gemini/skills/<skill>/SKILL.md
.hermes/skills/<skill>/SKILL.md
.openclaw/skills/<skill>/SKILL.md
.copilot/skills/<skill>/SKILL.md
.trae/skills/<skill>/SKILL.md
.trae-cn/skills/<skill>/SKILL.md
```

只检查已经存在的 skills 目录。找到后将该目录作为上游 skill 根目录。

## Link Existing External Skill

如果项目本地没有，再检查：

```text
~/.beeweave/external/skills/<skill>/SKILL.md
```

如果存在，运行：

```bash
${BEEWEAVE_CLI:-bwe} external link <skill> --project .
```

链接完成后重新检查项目本地 skills 目录，并以项目本地路径作为上游 skill 根目录。不要直接使用 `~/.beeweave/external/skills/...` 作为运行入口；它只是安装缓存和链接源。

## Fresh Install

如果项目本地和用户级 external 都没有，先告诉用户将安装第三方 skill 到 `~/.beeweave/external/`，然后分别运行：

```bash
${BEEWEAVE_CLI:-bwe} external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-article-illustrator \
  --link-project .

${BEEWEAVE_CLI:-bwe} external install https://github.com/jimliu/baoyu-skills \
  --skill baoyu-image-gen \
  --link-project .
```

安装完成后必须重新检查项目本地 skills 目录。只有两个上游 skill 都能在项目本地解析到 `SKILL.md`，才能继续配置。

## Failure Behavior

如果 link 或 install 命令失败，停止 setup，并报告：

- 失败命令。
- 预期项目本地路径。
- 用户级 external 路径。
- 可重试命令。

不要把 Baoyu 仓库 clone 到 BeeWeave 源码树、包内 `_data/skills`、`vault/` 或 `workbench/`。
