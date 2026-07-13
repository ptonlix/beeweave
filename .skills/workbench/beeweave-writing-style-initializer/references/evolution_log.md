# 写作风格演进日志

用途：记录初始化、激活、拒绝、回滚和 compaction，保证风格系统可追溯。

## Log

暂无。

## 条目格式

```text
## YYYY-MM-DD HH:MM 变更标题

- action: initialize | learn | activate | reject | rollback | compact | source_patch
- affected_layer: route | instruction | resource
- affected_files: 文件或章节
- evidence: trace、历史文章、用户反馈或 eval case
- validation: 验证结果或用户确认
- summary: 这次变更解决的问题
- rollback: 回滚方式
```

## 初始化日志示例

```text
## YYYY-MM-DD HH:MM 默认初始化

- action: initialize
- affected_layer: resource
- affected_files: writing/style/*
- evidence: user requested default initialization
- validation: not required
- summary: 创建写作风格资产模板，等待后续从历史文章和 trace 学习
- rollback: 删除本次创建且未被用户编辑的模板文件
```

