# 开发

修改 BeeWeave 本身时使用源码 checkout。

## 仓库结构

```text
beeweave/       # Python CLI 和辅助逻辑
.skills/        # 源 skill 定义
bootstrap/      # 用户项目 bootstrap 模板
extensions/     # 浏览器扩展和资源
tests/          # pytest 测试
openspec/       # 提案和活跃变更规格
docs/           # MkDocs 源文档
```

## 检查命令

标准本地质量检查使用 Makefile：

```bash
make format
make check
```

这些目标会依次运行 Ruff 格式化 / lint、mypy 类型检查和 pytest：

```bash
uv run ruff format beeweave tests
uv run ruff check beeweave tests --fix
uv run ruff format --check beeweave tests
uv run ruff check beeweave tests
uv run mypy
uv run python -m pytest
```

快速检查 CLI 时，也运行：

```bash
uv run bwe setup --help
uv run bwe info
```

## 本地 CLI 安装

把当前源码 checkout 安装为开发中的 `bwe` 工具：

```bash
make dev-install
```

该命令会基于 Makefile 所在位置自动解析仓库根目录，并执行
`uv tool install --reinstall --editable <repo-root>`。只有需要把新安装包里的
agent skills 刷新到目标工作区时，才在之后手动运行 `bwe setup`。

## 文档

MkDocs 工具只属于文档开发和 CI，不属于 BeeWeave 运行时依赖：

```bash
uv sync --group docs
```

也可以在文档环境中用 pip 安装：

```bash
pip install "mkdocs-material>=9.6,<9.7"
```

本地预览：

```bash
uv run --group docs mkdocs serve
```

严格构建：

```bash
uv run --group docs mkdocs build --strict
```

生成的 `site/` 是构建产物，不应该提交到 `main` 分支。

## GitHub Pages

文档发布地址是 <https://ptonlix.github.io/beeweave/>。GitHub 仓库设置中 Pages 应配置为：

- Source: Deploy from a branch
- Branch: `gh-pages`
- Folder: `/root`

Workflow 会从源文件构建站点，并把生成结果发布到 `gh-pages` 分支。

## OpenSpec

行为或工作流变更使用 OpenSpec 管理：

```bash
openspec validate <change-name> --strict
```

只有在实现和验证都完成后才归档变更。
