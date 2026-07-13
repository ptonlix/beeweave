# 生效风格规则

用途：保存已经确认或高置信的长期写作规则。writer skills 只应把这里的匹配 scope 规则当作用户生效风格。

## 默认规则

### RULE-DEFAULT-001
- status: active
- scope: all
- layer: instruction
- evidence: BeeWeave 默认初始化
- validated_by: default
- rule: 用自然、具体、有判断力的中文表达，优先写真实观察、明确判断和可感知细节，避免空泛套话。

### RULE-DEFAULT-002
- status: active
- scope: all
- layer: instruction
- evidence: BeeWeave 默认初始化
- validated_by: default
- rule: 不编造第一手经历、人物、数据或使用结果；缺少事实时先标明不确定或向用户补问。

## Learned Rules

暂无。

## 条目格式

```text
### RULE-YYYYMMDD-001
- status: active
- scope: article | social | all | methodology
- layer: instruction | resource | route
- evidence: trace 路径、历史文章路径或用户反馈摘要
- validated_by: eval case、人工确认或发布采纳
- rule: 具体规则
```

