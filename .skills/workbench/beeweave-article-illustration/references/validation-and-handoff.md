# Validation and Handoff

使用本 reference 完成运行前检查、失败处理和交接给 `baoyu-article-illustrator`。

## Upstream Integrity

解析到项目本地根目录后，检查必需文件。

`baoyu-article-illustrator` 必须存在：

```text
<ARTICLE_ILLUSTRATOR_ROOT>/SKILL.md
<ARTICLE_ILLUSTRATOR_ROOT>/references/
<ARTICLE_ILLUSTRATOR_ROOT>/references/workflow.md
<ARTICLE_ILLUSTRATOR_ROOT>/references/prompt-construction.md
<ARTICLE_ILLUSTRATOR_ROOT>/references/style-presets.md
```

`baoyu-image-gen` 必须存在：

```text
<IMAGE_GEN_ROOT>/SKILL.md
<IMAGE_GEN_ROOT>/scripts/main.ts
<IMAGE_GEN_ROOT>/scripts/build-batch.ts
<IMAGE_GEN_ROOT>/scripts/types.ts
<IMAGE_GEN_ROOT>/scripts/providers/
<IMAGE_GEN_ROOT>/references/usage-examples.md
```

如果缺失，停止 setup，并建议用户运行：

```bash
${BEEWEAVE_CLI:-bwe} external update <skill>
```

更新后仍需重新检查项目本地路径，不要带着不完整上游 skill 继续生成。

## Bun-Compatible Runtime

在声明 `baoyu-image-gen` 可运行前，先检查：

```bash
command -v bun
```

如果 `bun` 不存在，再检查：

```bash
command -v npx
```

可用运行器解析规则：

```text
bun 存在 -> BUN_X=bun
bun 不存在但 npx 存在 -> BUN_X="npx -y bun"
二者都不存在 -> 停止 setup
```

如果二者都不可用，停止，并告诉用户 `baoyu-image-gen` 需要 `bun` 或 `npx -y bun`。

## Readiness Gate

初始化、修复和文章配图前都按顺序验证：

1. 两个上游 skills 都能解析到项目本地 `SKILL.md`。
2. 上游必需文件完整。
3. `bun` 或 `npx` 可用。
4. 项目级 `baoyu-article-illustrator/EXTEND.md` 存在，且 `preferred_image_backend: baoyu-image-gen`。
5. 项目级 `baoyu-image-gen/EXTEND.md` 存在，且 `default_provider` 非空，所选 provider 的 `default_model` 非空。
6. 所选 provider 的必需凭证变量存在于当前 workspace/project root 下的 `./.baoyu-skills/.env`，或已由当前进程环境变量提供。
7. 如果用户配置了自定义 base URL，所选 provider 对应的 base URL 变量存在于当前 workspace/project root 下的 `./.baoyu-skills/.env`；如果 provider 是 `azure`，`AZURE_OPENAI_BASE_URL` 必须存在。

任一步失败都停止当前流程。失败回复必须包含失败命令或检查项、预期路径和可重试命令。文章配图路径中遇到失败时，不要继续生成图片。

## Handoff

setup 成功后，如果用户已经提供 Markdown 文章文件路径或明确要求现在生成，先处理文章工作目录：

- 用户提供 Markdown 文件路径时，读取 `references/article-workdir.md`，必要时先创建文章专属子目录并移动文章文件。
- 用户未提供 Markdown 文件路径时，不进入配图生成；提示用户先保存文章为 `.md` 文件并提供路径。

文章工作目录就绪后，读取项目本地：

```text
<ARTICLE_ILLUSTRATOR_ROOT>/SKILL.md
```

然后按 `baoyu-article-illustrator` 的流程继续当前文章配图任务。

调用或转述给上游时必须明确这些语义：

```text
使用当前项目已固定的 BeeWeave 配置直接生成：
- backend 使用 baoyu-image-gen
- provider/model/quality/aspect/output/language/watermark 使用当前 workspace/project root 下 `./.baoyu-skills/` 中的默认值
- 不要重新选择图片后端
- 不要重新询问 provider 或 model
- 除非文章本身需要判断或用户没有提供参考图路径，否则跳过重复 setup 交互
```

如果用户希望减少 `baoyu-article-illustrator` Step 3 的确认，需要在当前请求中显式包含“直接生成”“不用确认”“跳过确认”或“按默认出图”等语义。没有这些语义时，尊重上游确认策略。

如果用户提供参考图但没有文件路径，仍然需要让用户补齐路径；这是文章级输入，不属于 provider/backend/model setup。

## Success Summary

setup 完成后回复必须包含：

- 已链接的两个上游 skills 和项目本地路径。
- 文章工作目录状态：已在专属目录，或已从散落文件移动。
- 所选 API provider 和模型。
- 自定义 base URL 状态：未设置，或已从当前 workspace/project root 下 `./.baoyu-skills/.env` 读取。
- 写入或复用的配置文件路径。
- 凭证状态：只说变量存在或缺失，不打印值。
- Bun-compatible runner：`bun` 或 `npx -y bun`。
- 下一步调用方式。
