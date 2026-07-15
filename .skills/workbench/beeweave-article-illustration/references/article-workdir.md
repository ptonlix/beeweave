# Article Work Directory

使用本 reference 在文章配图前整理文章文件位置。目标是让每篇文章拥有自己的目录，避免多篇文章共享同一个 `imgs/` 目录。

## When to Apply

仅在用户提供的是 Markdown 文件路径时执行本步骤。用户未提供稳定文件路径时，不移动现有文件，也不进入配图生成；提示用户先将文章保存为 `.md` 文件并提供路径。

不要无条件移动文件。先判断文章是否已经在专属目录中。

## Why

如果多篇文章平铺在同一目录：

```text
drafts/my-article.md
drafts/another-article.md
```

而 `default_output_dir: imgs-subdir`，上游会把图片放入共享目录：

```text
drafts/imgs/
```

这会让不同文章的图片、prompt 和 outline 混在一起。

更好的结构是：

```text
drafts/my-article/
├── my-article.md
└── imgs/
    ├── outline.md
    ├── prompts/
    └── 01-infographic-xxx.png
```

这样文章、配图、prompt、outline、发布和归档都以文章为单位组织。

## Dedicated Directory Detection

如果满足任一条件，认为文章已经在专属目录中，不移动：

- 父目录名与文章文件 stem 相同或近似，例如 `my-article/my-article.md`。
- 父目录下已有该文章专属的 `imgs/`，且当前目录看起来只服务这篇文章。
- 父目录里只有这篇主 Markdown 和少量配套资产，例如 `imgs/`、`assets/`、`README.md`。
- 用户明确要求不要移动或当前路径是发布系统、Obsidian、博客框架约定的固定路径。

如果父目录包含多篇 Markdown 文章，或明显是 `drafts/`、`articles/`、`published/`、`posts/` 这类集合目录，则认为文章是散落单文件，需要创建子目录。

## Move Rules

当文章是散落单文件时：

1. 从文件名生成 slug，使用文章文件 stem 的 kebab-case 形式。
2. 在原文件同级创建 `<slug>/` 子目录。
3. 如果目标目录已存在，追加 `-v2`、`-v3`，直到找到未占用目录。
4. 将原 Markdown 文件移动到目标目录中，默认保留原文件名：

```text
drafts/my-article.md
→ drafts/my-article/my-article.md
```

不要默认改名为 `index.md`，除非用户明确要求。

## Relative Path Repair

移动 Markdown 后，相对路径可能失效。移动前扫描正文中的相对链接和图片引用：

- Markdown 图片：`![alt](relative/path.png)`
- Markdown 链接：`[text](relative/path.md)`
- HTML 图片：`<img src="relative/path.png">`

只处理相对路径；不要修改 `http://`、`https://`、`mailto:`、`#anchor`、Obsidian wikilink `[[...]]` 或绝对路径。

对仍然指向原父目录资源的相对路径，移动后加上 `../` 前缀，或计算从新文章目录到原资源的正确相对路径。例如：

```text
drafts/my-article.md 里的 ![](cover.png)
移动到 drafts/my-article/my-article.md 后改为 ![](../cover.png)
```

如果链接修复不确定，停止移动并向用户说明需要确认。不要在无法判断时批量改坏文章链接。

## Handoff Path

移动完成后，后续所有验证、交接和上游调用都使用新的文章路径。

成功摘要必须说明：

- 原文章路径。
- 新文章路径。
- 是否修复了相对链接。
- 后续配图输出目录，例如 `new-article-dir/imgs/`。

如果未移动，也要说明原因，例如“文章已在专属目录中”。
