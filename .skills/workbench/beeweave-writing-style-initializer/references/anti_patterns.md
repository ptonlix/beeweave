# 反模式

用途：记录用户明确拒绝、历史改稿中稳定删除或验证失败的写法。

## 默认反模式

### ANTI-DEFAULT-001
- status: active
- scope: all
- evidence: BeeWeave 默认初始化
- avoid: 空泛套话，例如“随着技术的发展”“值得注意的是”“综上所述”。
- prefer: 直接从具体事件、判断、场景或问题切入。

### ANTI-DEFAULT-002
- status: active
- scope: all
- evidence: BeeWeave 默认初始化
- avoid: 未经证实的“我朋友”“有一次”“我亲测”等编造式例子。
- prefer: 使用用户提供的真实经历；没有经历时明确说还没验证。

## Learned Anti-patterns

暂无。

## 条目格式

```text
### ANTI-YYYYMMDD-001
- status: active
- scope: article | social | all
- evidence: trace 路径、用户反馈或 before/after diff
- avoid: 需要避免的写法
- prefer: 推荐替代方式
```

