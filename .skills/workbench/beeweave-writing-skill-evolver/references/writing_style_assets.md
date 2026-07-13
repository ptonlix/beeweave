# 写作风格资产模板

本文件是 `beeweave-writing-skill-evolver` 的本地参考模板。真实用户资产写入 `$BEEWEAVE_WORKBENCH_PATH/writing/`，不能写入 skill 源目录。

## Active Rule Format

```text
### RULE-YYYYMMDD-001
- status: active
- scope: article | social | all | methodology
- layer: instruction | resource | route
- evidence: trace 路径、历史文章路径或用户反馈摘要
- validated_by: eval case、人工确认或发布采纳
- rule: 具体规则
```

## Evolution Log Format

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

## Eval Rubric

- 风格贴合度，是否更像用户确认过的表达。
- 信息质量，是否保留事实、观点和关键细节。
- 平台格式，长文是否适合文章阅读，社交内容是否适合对应平台。
- 反模式规避，是否减少用户明确拒绝的写法。
- 可读性，是否更顺、更清晰、更有节奏。

## Trace Evidence Fields

evolver 可以读取 trace 中的这些字段作为规则证据，但不负责在发布时更新它们：

- `revision_events`
- `learning_status`
- `final_version`
- `published_path`
- `candidate_rules`
- `learning_summary`
