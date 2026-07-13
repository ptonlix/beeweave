# 写作风格资产总入口

`beeweave-writing-style-initializer` 是写作风格资产的正式初始化入口。真实用户资产写入 `$BEEWEAVE_WORKBENCH_PATH/writing/style/`，不能写入 skill 源目录。

## 初始化目标

```text
$BEEWEAVE_WORKBENCH_PATH/writing/
+-- style/
|   +-- author_profile.md
|   +-- active_style_rules.md
|   +-- anti_patterns.md
|   +-- article_examples.md
|   +-- social_examples.md
|   +-- pending_rules.md
|   +-- rejected_rules.md
|   +-- evolution_log.md
+-- traces/
+-- eval/
```

初始化完成标准：`style/` 下必须存在上述 8 个固定文件。不要创建 `author-writing-style.md`、`writing-style.md`、`style-summary.md` 或其它汇总文件来替代这些文件。

如果 `style/` 下存在非固定文件，例如 `author-writing-style.md`，不能把它当作初始化完成。处理方式是：

1. initializer 先补齐 8 个固定文件。
2. learner 后续可以把非固定文件当作 legacy source 读取。
3. learner 可将其中有价值的摘要迁移到 `author_profile.md`、`pending_rules.md` 或 examples。
4. 不要继续写入非固定文件。

## 模板文件

初始化时逐个读取本目录下的模板文件，并只创建 Workbench 中缺失的文件，不能覆盖已有用户内容。

- `author_profile.md`，作者画像模板。
- `active_style_rules.md`，已生效规则模板。
- `anti_patterns.md`，反模式模板。
- `article_examples.md`，长文示例模板。
- `social_examples.md`，社交短内容示例模板。
- `pending_rules.md`，候选规则模板。
- `rejected_rules.md`，已拒绝规则模板。
- `evolution_log.md`，演进日志模板。

## 初始化模式

### 默认初始化

创建完整目录和模板文件。`active_style_rules.md` 写入 BeeWeave 默认基础规则，并标记为 default；示例、pending、rejected 保持空占位；`evolution_log.md` 记录 initialization。

## 约束

- 不覆盖已有用户文件。
- 不把用户私有材料写入 `.skills/`。
- 不分析历史文章。
- 不提炼 pending 或 active 学习规则。
