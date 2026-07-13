# 自进化写作工作流

BeeWeave 的写作自进化由三类 skill 协作完成：

- writer：`beeweave-article-writer` 和 `beeweave-social-writer` 负责写作、改稿、保存当前工作稿，并记录 trace。
- initializer：`beeweave-writing-style-initializer` 负责初始化写作风格资产模板。
- learner：`beeweave-writing-style-learner` 负责从历史文章、trace、diff 和反馈中提炼候选规则。
- evolver：`beeweave-writing-skill-evolver` 负责审阅、验证、激活、拒绝、回滚和 compaction。

## 首次使用

写作风格资产存放在当前 Workbench：

```text
workbench/writing/
+-- style/
+-- traces/
+-- eval/
```

`style/` 下保存用户风格资产，包括作者画像、生效规则、反模式、示例、候选规则、拒绝规则和演进日志。`beeweave-writing-style-initializer` 是明确的初始化入口。

模板来源放在 `beeweave-writing-style-initializer/references/` 目录里。article/social writer 不持有这些模板；
如果发现风格资产未初始化，会提示用户先用 initializer 初始化。用户仍要继续写作时，writer 使用内置默认规则继续生成。
真实用户风格资产只保存在 `workbench/writing/`。

## 初始化风格资产

第一次使用时，先运行 initializer 创建固定风格资产文件：

```text
/beeweave-writing-style-initializer
```

初始化完成后，再让 learner 从历史文章学习：

```text
/beeweave-writing-style-learner workbench/articles/published
```

initializer 只创建目录和 8 个固定模板文件，不学习文章。learner 只在初始化完成后学习历史文章、trace、diff 或反馈。

## 日常写作

写长文或社交短内容时，writer 会先读取适用的 active 风格规则、反模式和示例，再生成草稿。草稿仍保存到：

```text
workbench/articles/drafts/
```

同一篇内容默认只维护一个当前工作稿。用户让 AI 继续改、缩短、扩写、换开头或按反馈改时，writer 更新当前 `draft_path`，而不是默认生成 `-v2`、`-v3`、`-final` 一堆文件。

版本历史写入：

```text
workbench/writing/traces/YYYY-MM-DD-<type>-<slug>/
+-- trace.md
+-- trace.json
```

trace 默认记录路径、摘要、版本事件、diff summary 和学习状态，不复制完整正文。只有用户明确要求“保存完整过程快照”“保留这个版本”或标记学习样本时，才在 trace 的 `snapshots/` 下保存完整正文。

## AI 改稿和手动改稿

如果用户让 AI 改稿，例如“开头太宏大，改成真实经历切入”，writer 会把这次改稿记录为 `revision_events`，包含用户指令、diff 摘要和强学习信号。

如果用户手动改稿后说“这是我改后的版本，学习一下我改了什么”，learner 会读取原稿、改后稿或 trace，提炼稳定改动模式。

信号强弱按这个顺序判断：

- 用户手动改稿是强信号。
- 用户明确指令驱动 AI 改稿是强信号。
- 未经用户确认的 AI 自改只是弱信号。
- 被标记 final、发布或明确采纳的版本证据更强。
- 被否定、废弃或未采用的版本只能作为反模式候选。

## 规则学习与激活

learner 默认只写候选规则到：

```text
workbench/writing/style/pending_rules.md
```

每条候选包含适用范围、建议层级、证据、置信度和验证建议。learner 不会默认修改 `active_style_rules.md` 或 writer 的 `SKILL.md`。

当用户要求激活、拒绝或整理候选时，evolver 会先判断候选属于哪一层：

- 路由层：调整 skill 触发边界。
- 指令层：调整稳定流程和质量标准。
- 资源层：调整 Workbench 风格资产、示例、细分场景或 eval case。

影响 active 规则、rejected 规则、source `SKILL.md` 或共享 references 的变更，都需要验证结果或用户明确确认。验证材料放在 `workbench/writing/eval/`，可用历史 brief、用户终稿和 rubric 对比改动前后的输出。

evolver 只处理规则生命周期和风格资产维护。它不负责发布文章、不移动草稿、不触发 wiki ingest，也不负责普通发布时的 trace 发布元数据。

## 发布、清理和压缩

发布时，`beeweave-article-publisher` 以当前工作稿作为候选终稿，把文件移动到 `workbench/articles/published/`，更新 frontmatter，并触发 wiki ingest。

如果这篇草稿有对应 trace，publisher 会更新 trace 中的 `status`、`final_version`、`published_path` 和 cleanup 摘要，并追加一条 `published` revision event。找不到 trace 或 trace 更新失败时，不阻断发布和 wiki ingest，但最终回复会说明 trace 没有更新。

publisher 不会创建新的基础 trace，也不会为了发布制造新的写作版本。`final_version` 默认使用 trace 当前版本。

如果 trace 中有临时 `snapshots/`，publisher 默认不删除任何快照。只有用户明确要求发布后清理时，才清理临时快照，并保留 final 或明确标记为 learning sample 的快照。没有 snapshots 时不需要额外清理。

当规则积累变多时，可以让 `beeweave-writing-skill-evolver` 做 compaction。它会提出合并重复规则、下沉细分规则、删除长期无效规则和保留关键规则的方案，经确认后更新风格资产，并写入 `evolution_log.md`。
