# 已拒绝风格规则

用途：记录用户或验证明确拒绝的候选，避免 learner 反复提出同类规则。

## Rejected Rules

暂无。

## 条目格式

```text
### REJECTED-YYYYMMDD-001
- status: rejected
- original_candidate: PENDING 编号或规则摘要
- scope: article | social | all | methodology
- rejected_by: user | validation | compaction
- reason: 拒绝原因
- evidence: 相关 trace、eval case 或反馈
```

## 使用规则

- learner 提出新候选前必须读取本文件。
- 被拒绝规则不能再次写入 pending，除非用户提供新的反向证据。
- 拒绝原因要具体，便于后续避免相同误学。

