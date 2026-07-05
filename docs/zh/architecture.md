# 架构

BeeWeave 有两条关键边界：仓库源码文件和运行时工作区文件。

## 源码仓库

```text
beeweave/       # Python CLI 和辅助逻辑
.skills/        # 源 skill 定义
bootstrap/      # Agent bootstrap 模板
extensions/     # 浏览器扩展资源
tests/          # pytest 测试
openspec/       # 提案和活跃变更
docs/           # MkDocs 源文档
```

Python 包提供 `bwe` CLI。Wheel 会把源 skills 和 bootstrap 模板作为包数据打进去，这样用户不需要克隆仓库也能安装 Agent 文件。

## 运行时工作区

运行时目录由 `bwe setup` 在用户选择的工作区创建：

```text
project/
+-- vault/                  # 稳定 Markdown 知识库
+-- workbench/              # 捕获、素材、草稿和 inbox 内容
```

这些目录是用户数据，不是源码文档，也不应该提交到 BeeWeave 仓库根目录。

## 主要组件

- CLI：`beeweave/cli.py` 提供 setup、uninstall、info、list、graph、cache、batch 和 AST 辅助命令。
- Skills：`.skills/wiki/` 和 `.skills/workbench/` 保存安装到 Agent 的源 skill 包。
- Bootstrap：`bootstrap/` 保存复制到用户工作区的 Agent 规则和说明。
- 浏览器扩展：`extensions/brain-capture/` 把网页选中内容捕获到 workbench inbox。
- OpenSpec：`openspec/` 在实现前记录提案、设计、规格和任务。

## 设计边界

MkDocs 从 `docs/` 构建本 wiki，并输出到 `site/`。`site/` 是本地构建产物，由 CI 发布到 `gh-pages`，不作为 `main` 分支源码维护。

![架构边界](../assets/architecture-boundaries.png)
