# 候选风格规则

用途：保存 learner 从文章、trace、diff、反馈中提炼出的待审候选。默认学习结果先写这里。

## Pending Rules

暂无。

## 条目格式

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

## 写入规则

- 单次反馈、低置信观察、未验证模式写入 pending。
- 用户手动改稿和用户指令驱动 AI 改稿是强信号，但仍需判断是否稳定。
- 被发布、标记 final 或明确采纳的版本可以提高 confidence。

