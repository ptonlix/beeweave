---
name: beeweave-writing-skill-evolver
description: |
  审阅、验证、激活、拒绝、回滚或压缩 BeeWeave 写作风格规则和写作 skills 的 skill。当用户说“激活这些写作规则”“进化写作 skill”“整理 pending rules”“做 skill compaction”“把候选规则写入合适层级”“拒绝这条规则”时使用。涉及 active 规则、rejected 规则、source SKILL.md 或共享 references 的变更前必须获得用户确认。
---

# BeeWeave 写作 Skill 进化器

这个 skill 的职责是把候选学习结果变成可验证、可回滚、可维护的写作系统变更。它不负责普通写作生成，也不负责创建基础写作 trace。

## 任务边界

本 skill 只处理写作风格系统的演进：

- pending 规则审阅。
- pending → active。
- pending → rejected。
- active 规则整理和 compaction。
- writer `SKILL.md` 或 source references 的受控 patch 建议。
- evolution log 记录和回滚说明。

不处理：

- 普通文章写作，交给 `beeweave-article-writer` 或 `beeweave-social-writer`。
- 首次风格初始化，交给 `beeweave-writing-style-initializer`。
- 文章发布、published 文件移动、wiki ingest、发布 trace 元数据，交给 `beeweave-article-publisher`。

## 工作区定位

如果用户请求里包含 `@<name>`，只从 `~/.beeweave/config.<name>` 读取 `BEEWEAVE_WORKBENCH_PATH`。否则只从 `~/.beeweave/config` 读取 `BEEWEAVE_WORKBENCH_PATH`。

如果配置文件不存在、没有配置 `BEEWEAVE_WORKBENCH_PATH`，或 Workbench 无法访问，先向用户说明无法找到 BeeWeave workbench，不要猜测其它路径。

## 必读资产

执行前读取：

```text
$BEEWEAVE_WORKBENCH_PATH/writing/style/
├── active_style_rules.md
├── anti_patterns.md
├── pending_rules.md
├── rejected_rules.md
└── evolution_log.md
```

如果需要验证，还读取：

```text
$BEEWEAVE_WORKBENCH_PATH/writing/eval/
├── article_cases/
├── social_cases/
└── rubric.md
```

如果 `writing/style/` 或关键风格文件缺失，不要在 evolver 中初始化模板。先提示用户使用 `beeweave-writing-style-initializer` 完成初始化。evolver 只处理已经存在的 pending、active、rejected、evolution log 和 compaction 工作。

## 三层分类

每条候选必须先分类，再决定写入位置：

- 路由层，修改 `name`、`description` 或触发边界。用于解决 skill 该不该触发的问题。
- 指令层，修改 `SKILL.md` 主流程、质量检查或稳定规则。用于解决通用流程和判断标准问题。
- 资源层，修改 Workbench 风格资产、examples、references 或 eval case。用于承载用户特定风格、示例、细分场景和证据。

每次进化都必须回答：

- 改了哪一层。
- 解决什么问题。
- 用什么证据证明它更好。
- 如何回滚。

## 激活流程

1. 从 `pending_rules.md` 读取候选。
2. 检查 `active_style_rules.md` 和 `rejected_rules.md`，避免重复激活或反复提出已拒绝规则。
3. 分类为 route、instruction 或 resource。
4. 检查证据是否足够，至少包含 trace、历史文章、用户反馈、发布采纳或 before/after diff。
5. 如果 `writing/eval/` 有相关 case，用 case 和 `rubric.md` 做验证；如果没有相关 case，明确说明验证缺口。
6. 根据目标类型选择执行方式：
   - 只改 Workbench style assets：准备 active/rejected/examples/eval 的具体条目。
   - 改 writer `SKILL.md`：准备目标文件、章节、变更理由和最小 patch 摘要。
   - 改 source references：准备目标 reference、使用场景和回滚方式。
7. 输出 review summary，包含规则、scope、证据、目标文件或章节、验证结果、风险、回滚方式和准备写入的内容。
8. 只有通过验证或用户明确批准后，才能修改 active 规则、rejected 规则、writer `SKILL.md` 或 source references。
9. 修改后记录 `evolution_log.md`，并在 `pending_rules.md` 中标记该候选已处理或移动到对应状态。

## 拒绝流程

当用户拒绝候选或验证失败：

1. 把候选复制或移动到 `rejected_rules.md`。
2. 记录 rejected_by、reason、evidence。
3. 在 `evolution_log.md` 记录拒绝日期、原因和关联候选。
4. 不修改 active 规则。

## Compaction 流程

用户明确要求“压缩写作规则”“整理风格资产”“做 skill compaction”时执行：

1. 扫描 active、pending、rejected、examples 和 trace 学习摘要。
2. 找出重复、重叠、过窄、长期未触发或已经被更高层规则覆盖的规则。
3. 提出合并、下沉、删除或保留建议。
4. 对细分场景优先下沉到 examples 或 scoped sections，保持 active 主文件轻量。
5. 输出 removed、merged、moved、retained 摘要。
6. 经用户确认后执行，并在 `evolution_log.md` 记录回滚点。

## Trace 证据使用

trace 是证据来源，不是 evolver 的发布目标：

- 可以读取 trace 的 `revision_events`、`final_version`、`published_path` 和学习摘要来判断候选规则是否有证据。
- 可以在规则激活或拒绝后，把相关候选编号或演进摘要回写到 trace 的学习区。
- 不移动 draft，不发布文章，不写 published frontmatter，不触发 wiki ingest。
- 不负责普通发布时的 `published_path` 或 `cleanup` 元数据；这些由 `beeweave-article-publisher` 更新。

## Evolution Log 格式

```text
## YYYY-MM-DD HH:MM 变更标题

- action: activate | reject | rollback | compact | source_patch
- affected_layer: route | instruction | resource
- affected_files: 文件或章节
- evidence: trace、历史文章、用户反馈或 eval case
- validation: 验证结果或用户确认
- summary: 这次变更解决的问题
- rollback: 回滚方式
```

## 输出要求

最终回复用户时说明：

- 处理了哪些候选。
- 每条候选归入哪一层。
- 哪些已激活、拒绝、保留 pending 或需要补验证。
- 修改了哪些文件或章节。
- 哪些变更只是建议，尚未写入。
- 验证结果和回滚方式。

## 禁止事项

- 未经用户确认，不得修改 active 规则、rejected 规则、writer `SKILL.md` 或 source references。
- 不要把用户私有材料写入 `.skills/` 源码目录。
- 不要让单次反馈绕过 pending 生命周期直接变成长期规则。
- 不要在 compaction 中删除证据，证据可以被摘要或下沉，但必须能追溯。
- 不要执行文章发布、移动草稿或调用 wiki ingest。

## 参考资料

active rule、evolution log、eval rubric 和 trace 证据字段参考 `references/writing_style_assets.md`。首次初始化模板由 `beeweave-writing-style-initializer/references/` 持有。
