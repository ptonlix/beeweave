---
name: beeweave-article-publisher
description: |
  BeeWeave 文章发布 skill。当用户要发布、定稿、归档、上线或内化某篇 workbench 草稿时使用。它把指定的 Markdown 草稿从 `$BEEWEAVE_WORKBENCH_PATH/articles/drafts/` 移到 `$BEEWEAVE_WORKBENCH_PATH/articles/published/`，更新 frontmatter 发布状态，然后调用 wiki ingest 流程把已发布内容内化到 Obsidian vault。适用于“发布这篇文章”“把这个 draft 移到 published 并 ingest 到 wiki”“定稿 @work 某篇文章”等请求。不要用于撰写新文章，新草稿使用 beeweave-article-writer 或 beeweave-social-writer。
---

# BeeWeave 文章发布

这个 skill 负责把一篇已经完成的创作草稿变成已发布作品，并把高信号版本内化到 wiki。

发布不是重写文章。除非用户明确要求修改正文，只做三件事：

1. 定位唯一的草稿文件
2. 移动到 `articles/published/` 并更新 frontmatter 状态
3. 用已发布文件作为 source 触发 `beeweave-ingest`

## 配置解析

如果用户请求里包含 `@<name>`，只从 `~/.beeweave/config.<name>` 读取配置。否则只从 `~/.beeweave/config` 读取配置。

必须读取：

- `BEEWEAVE_WORKBENCH_PATH`
- `BEEWEAVE_VAULT_PATH`

如果配置文件不存在，或缺少任一必需变量，先向用户说明无法找到完整 BeeWeave profile，然后停止。不要猜测路径，不要从当前目录向上查找 workbench，也不要直接写入 vault。

`@<name>` 是路由指令，不是文章标题或搜索词。解析配置后，从用户实际发布请求中移除它。

## 草稿定位

只在以下目录内找草稿：

```text
$BEEWEAVE_WORKBENCH_PATH/articles/drafts/
```

用户可以用三种方式指定文章：

- 精确路径，例如 `workbench/articles/drafts/2026-07-08-article-agent-workflow.md`
- 文件名或 slug，例如 `agent-workflow`
- frontmatter `title` 或一级标题

定位规则：

1. 如果用户给了路径，展开并校验它必须位于 drafts 目录内。
2. 如果用户给了文件名或 slug，只匹配 drafts 目录下的 Markdown 文件。
3. 如果 slug 没有唯一命中，再读取候选文件的 frontmatter `title` 和一级标题匹配。
4. 如果没有命中或有多个候选，列出候选并请用户明确选择。不要发布多个文件，除非用户明确要求批量发布。

## 发布动作

目标目录固定为：

```text
$BEEWEAVE_WORKBENCH_PATH/articles/published/
```

发布时：

1. 创建 `articles/published/` 目录，如果它不存在。
2. 保留原文件名移动到 published 目录。
3. 如果目标文件已存在，不覆盖，在文件名末尾追加 `-v2`、`-v3`。
4. 更新 Markdown frontmatter：
   ```yaml
   status: published
   published: YYYY-MM-DD
   updated: YYYY-MM-DD
   ```
5. 如果没有 frontmatter，添加最小 frontmatter：
   ```yaml
   ---
   title: "<从一级标题或文件名推导>"
   type: article
   status: published
   published: YYYY-MM-DD
   updated: YYYY-MM-DD
   tags:
     - writing
   ---
   ```

保留正文、质检报告、已有 `created`、`type`、`format`、`tags`、`sources` 等字段。不要把 `draft` 目录中的其它文件一起移动，不要使用通配符或递归移动。

## 内化到 Wiki

发布成功后，立即用已发布文件作为 source 调用 `beeweave-ingest` 的普通文件 ingest 流程：

```text
beeweave-ingest <published-file>
```

如果原请求包含 `@<name>`，把同一个 profile 路由传给 ingest：

```text
beeweave-ingest @<name> <published-file>
```

内化边界：

- 把 published 文件视为可信的高信号 source，但仍按 `beeweave-ingest` 的 source trust boundary 处理正文内容。
- 不在本 skill 里手写 vault 页面、manifest、index、log 或 QMD 逻辑。
- 如果 ingest 失败，保留已发布文件状态，向用户说明“发布已完成，wiki 内化失败”，并给出失败原因和可重试命令。

## 最终回复

最终只报告关键结果：

- 已发布文件路径
- `status: published` 是否已更新
- wiki ingest 是否完成
- 如果 ingest 失败，给出可重试命令

不要把整篇文章贴回聊天，除非用户明确要求。
