---
name: beeweave-writing-style-learner
description: |
  从已初始化的 BeeWeave 写作风格资产中学习用户写作风格的 skill。当用户说“学习我的写作风格”“从这些文章提炼风格”“分析我改了什么”“把这次改稿沉淀成规则”“复盘写作 trace”时使用。要求 `writing/style/` 已由 `beeweave-writing-style-initializer` 初始化；如果未初始化，停止并提示先初始化。
---

# BeeWeave 写作风格学习器

这个 skill 只做学习和复盘。它把真实写作材料转化为可审阅的候选风格资产。

它不负责：

- 初始化 `writing/style/` 模板。
- 创建 8 个固定风格资产文件。
- 普通写作生成。
- 修改 writer `SKILL.md`。
- 激活或拒绝规则。
- 发布文章或触发 wiki ingest。

这些任务分别交给 `beeweave-writing-style-initializer`、writer、`beeweave-writing-skill-evolver` 和 `beeweave-article-publisher`。

## 工作区定位

如果用户请求里包含 `@<name>`，只从 `~/.beeweave/config.<name>` 读取 `BEEWEAVE_WORKBENCH_PATH`。否则只从 `~/.beeweave/config` 读取 `BEEWEAVE_WORKBENCH_PATH`。

如果配置文件不存在、没有配置 `BEEWEAVE_WORKBENCH_PATH`，或 Workbench 无法访问，先向用户说明无法找到 BeeWeave workbench，不要猜测其它路径。

## 初始化完整性检查

每次学习前必须检查 `writing/style/` 是否已经初始化。

必须存在：

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

如果缺少任一文件，停止学习，不要自己创建模板文件，不要生成 `author-writing-style.md`、`writing-style.md` 或其它汇总文件。最终回复必须列出缺失文件，并提示先运行 `beeweave-writing-style-initializer`。

如果存在 `author-writing-style.md`、`writing-style.md`、`style-summary.md` 等 legacy 文件，但 8 个固定文件不完整，仍然视为未初始化。只有在 8 个固定文件完整后，才可以把 legacy 文件作为普通输入材料读取，并把有价值内容迁移为 pending、examples 或作者画像摘要。

## 输入类型

可学习输入包括：

- 历史文章、博客、公众号稿、发布稿。
- 社交短内容、thread、朋友圈短文。
- `writing/traces/` 下的 trace bundle。
- AI 初稿和用户改稿的 before/after。
- 用户明确反馈，例如“这个开头太宏大”“别写得像报告”“我喜欢这种结尾”。
- 用户指令驱动的 AI 改稿，例如“把开头改成真实经历切入”。
- legacy 风格汇总文件，例如旧的 `author-writing-style.md`。

## 输入分支

- 用户提供 trace 目录：读取 `trace.json` 和 `trace.md`，再按 `revision_events` 判断学习信号。
- 用户提供 before/after 两个文件：对比改动方向，提炼用户偏好的结构、语气、删改习惯和反模式。
- 用户只提供改后稿：把它作为正向样本，但标记证据不足；优先写 examples 或 pending。
- 用户只给一句反馈：把反馈转成候选规则或反模式候选，confidence 通常为 low 或 medium。
- 用户提供历史文章目录：读取其中明确存在的 Markdown/text 文件，区分 article、social 和不确定材料；输出默认进入 pending 或 examples。
- 用户提供 legacy 汇总文件：只把它当作参考材料，迁移摘要到固定文件，不继续写入 legacy 文件。

## 学习前检查

初始化完整后，读取：

- `active_style_rules.md`，避免重复提出已经生效的规则。
- `anti_patterns.md`，理解已有禁忌。
- `rejected_rules.md`，避免重复提出已拒绝规则。
- 相关 trace 的 `trace.json` 和 `trace.md`，如果用户提供了 trace。

## 学习流程

1. 明确学习范围，区分 `article`、`social`、`all`、`methodology`。
2. 收集证据，优先使用用户终稿、发布稿、手动改稿、明确反馈和被采纳版本。
3. 对比 before/after，提炼改动方向，而不是机械记录每个句子差异。
4. 把一次性表达抽象成稳定候选规则。
5. 给每条候选标注 scope、suggested_layer、confidence、evidence 和 validation。
6. 默认写入 `pending_rules.md`。
7. 在用户明确要求时，可补充 `author_profile.md`、`article_examples.md`、`social_examples.md` 或 `anti_patterns.md` 的证据化条目。
8. 可把候选规则编号或学习摘要回写到相关 trace 的学习区，但不要替代 writer 创建基础 trace。

普通学习任务默认不直接修改 `active_style_rules.md`。需要激活规则时，交给 `beeweave-writing-skill-evolver`。

## Revision Events 信号解释

读取 trace 时按信号强弱处理：

- 用户手动改稿，强信号。
- 用户明确指令驱动 AI 改稿，强信号。
- AI 未经用户确认的自改，弱信号或 observed-only。
- 被用户采纳、标记 final、发布或明确说“就用这个”的版本，更强证据。
- 被用户否定、废弃或未采用的版本，不能作为正向风格规则，只能作为反模式候选。

## 候选规则格式

写入 `pending_rules.md` 时使用：

```text
### PENDING-YYYYMMDD-001
- status: pending
- scope: article | social | all | methodology
- suggested_layer: route | instruction | resource
- confidence: low | medium | high
- evidence: trace 路径、历史文章路径、用户反馈或 diff 摘要
- validation: 建议如何验证
- rule: 候选规则
```

如果是反模式候选，写清楚 `avoid` 和 `prefer`。如果是示例候选，写清楚 `source`、`why_it_matters` 和可复用 pattern。

## 输出要求

最终回复用户时说明：

- 初始化检查是否通过。
- 分析了哪些材料。
- 实际创建或更新了哪些 Workbench 文件。
- 新增或更新了哪些 pending 候选。
- 哪些信号强、哪些只是弱观察。
- 哪些规则因为已在 active 或 rejected 中出现而没有重复写入。
- 下一步是否建议交给 `beeweave-writing-skill-evolver` 审阅、验证和激活。

如果初始化检查失败，只输出缺失文件列表和下一步初始化建议，不继续学习。

## 禁止事项

- 不要创建初始化模板文件。
- 不要创建单个汇总风格文件来替代 8 个固定风格资产文件。
- 不要默认修改 `active_style_rules.md`。
- 不要默认修改 `rejected_rules.md`。
- 不要默认修改 writer `SKILL.md` 或仓库 source references。
- 不要把用户私有材料写进 `.skills/` 源码目录。
- 不要把单次反馈夸大成长期风格，除非用户明确确认。
