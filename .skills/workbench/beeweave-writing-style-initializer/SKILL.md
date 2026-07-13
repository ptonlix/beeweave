---
name: beeweave-writing-style-initializer
description: |
  初始化 BeeWeave 写作风格资产的 skill。当用户说“初始化写作风格”“建立写作风格库”“创建 writing/style 模板”“修复缺失的写作风格文件”时使用。只负责创建目录和 8 个固定模板文件，不分析文章、不提炼风格、不写 pending 规则。
---

# BeeWeave 写作风格初始化器

这个 skill 只做写作风格资产初始化。它是文件系统建模任务，不是内容学习任务。

## 职责边界

本 skill 负责：

- 定位 BeeWeave Workbench。
- 创建 `writing/style/`、`writing/traces/`、`writing/eval/` 目录。
- 创建缺失的 8 个固定风格资产文件。
- 从本 skill 的 `references/` 逐个复制模板内容。
- 检查初始化是否完整。

本 skill 不负责：

- 阅读历史文章并总结风格。
- 从 trace、diff、反馈中提炼规则。
- 写入 `pending_rules.md` 的学习候选。
- 激活或拒绝规则。
- 修改 writer `SKILL.md`。
- 发布文章或触发 wiki ingest。

这些任务分别交给 `beeweave-writing-style-learner`、`beeweave-writing-skill-evolver` 和 `beeweave-article-publisher`。

## 工作区定位

如果用户请求里包含 `@<name>`，只从 `~/.beeweave/config.<name>` 读取 `BEEWEAVE_WORKBENCH_PATH`。否则只从 `~/.beeweave/config` 读取 `BEEWEAVE_WORKBENCH_PATH`。

如果配置文件不存在、没有配置 `BEEWEAVE_WORKBENCH_PATH`，或 Workbench 无法访问，先向用户说明无法找到 BeeWeave workbench，不要猜测其它路径。

## 初始化目标

必须确保这些目录存在：

```text
$BEEWEAVE_WORKBENCH_PATH/writing/
├── style/
├── traces/
└── eval/
```

必须确保 `style/` 下存在 8 个固定文件：

```text
$BEEWEAVE_WORKBENCH_PATH/writing/style/
├── author_profile.md
├── active_style_rules.md
├── anti_patterns.md
├── article_examples.md
├── social_examples.md
├── pending_rules.md
├── rejected_rules.md
└── evolution_log.md
```

这 8 个文件是唯一的初始化完成标准。不要创建 `author-writing-style.md`、`writing-style.md`、`style-summary.md` 或其它汇总文件来替代它们。

## 模板来源

逐个读取本 skill 的模板文件：

- `references/author_profile.md`
- `references/active_style_rules.md`
- `references/anti_patterns.md`
- `references/article_examples.md`
- `references/social_examples.md`
- `references/pending_rules.md`
- `references/rejected_rules.md`
- `references/evolution_log.md`

只创建 Workbench 中缺失的文件。已有文件不能覆盖，也不要合并重写。

## 执行流程

1. 定位 Workbench。
2. 创建 `writing/style/`、`writing/traces/`、`writing/eval/`，如果它们不存在。
3. 检查 8 个固定文件。
4. 对每个缺失文件，读取同名 reference 模板并写入 Workbench。
5. 如果存在非固定 legacy 文件，例如 `author-writing-style.md`，不要删除；只在最终回复里说明它不是 canonical 文件，可后续交给 learner 作为参考材料迁移。
6. 再次检查 8 个固定文件是否全部存在。
7. 输出初始化清单。

## 完成输出

最终回复必须列出 8 个固定文件的状态：

```text
初始化完成：

- author_profile.md: created | exists | failed
- active_style_rules.md: created | exists | failed
- anti_patterns.md: created | exists | failed
- article_examples.md: created | exists | failed
- social_examples.md: created | exists | failed
- pending_rules.md: created | exists | failed
- rejected_rules.md: created | exists | failed
- evolution_log.md: created | exists | failed
```

如果任一文件 failed，初始化不算完成，停止并说明原因。

## 下一步提示

初始化完成后，提示用户下一步可以运行：

```text
beeweave-writing-style-learner workbench/articles/published
```

用历史文章学习风格。

