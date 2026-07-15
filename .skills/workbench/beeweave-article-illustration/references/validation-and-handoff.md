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
8. 当前 workspace/project root 下存在 `./.baoyu-skills/doctor.json`，且它是由 `${BEEWEAVE_CLI:-bwe} illustrate doctor --provider <provider>` 写入的通过结果，并匹配当前 provider、model、base URL、API dialect、相关 env 指纹和上游 Baoyu skill 文件指纹。

任一步失败都停止当前流程。失败回复必须包含失败命令或检查项、预期路径和可重试命令。文章配图路径中遇到失败时，不要继续生成图片。

如果失败原因是缺少 provider、模型、凭证或必需 base URL，读取 `provider-settings.md` 的 `Missing Configuration Prompt`，按模板向用户收集必要信息。

## Provider Doctor Gate

Provider 配置创建或更新后，先运行不生成图片的检测：

```bash
${BEEWEAVE_CLI:-bwe} illustrate doctor --provider <provider>
```

该命令只检查项目级配置、凭证变量是否存在、上游 Baoyu skill 完整性、`bun`/`npx` 可用性，以及所选 provider 的 base URL 是否已按原值配置。默认不会调用可能生成图片的 endpoint，也不会替用户追加、推导或改写 base URL。

项目根解析顺序：

1. 如果传入 `--project <path>`，使用该路径作为 workspace/project root。
2. 否则从当前目录向上查找包含 `./.baoyu-skills/`、`workbench/` + `vault/` 或项目本地 Agent skills 的目录。
3. 如果当前目录不在 BeeWeave workspace 内，则从 `${BEEWEAVE_CLI:-bwe}` 当前 profile 的 `~/.beeweave/config` 读取 `BEEWEAVE_WORKBENCH_PATH` 或 `BEEWEAVE_VAULT_PATH`，并取其父目录作为 workspace/project root。

因此 doctor 可以从任意目录运行；摘要中的 `Project` 和 `Project source` 会说明实际检测的是哪个 workspace。

当 provider 配置首次创建或更新，且不生成图片的 doctor 已通过后，询问用户是否需要做一次真实小图主动探测。说明该探测会真实请求 provider，可能产生费用；只有用户同意后才运行：

```bash
${BEEWEAVE_CLI:-bwe} illustrate doctor --provider <provider> --probe-image
```

`--probe-image` 会发起一次真实小图请求，可能产生 provider 费用。不要静默执行，也不要把它作为默认必跑步骤；如果用户拒绝或暂不确认，保留不生成图片的 doctor 通过缓存即可。

doctor 结果写入：

```text
./.baoyu-skills/doctor.json
```

正式交接给 `baoyu-article-illustrator` 前按以下规则处理：

- 如果存在匹配当前配置的通过缓存，复用该缓存，不重复检测。
- 如果缓存缺失、失败、过期，或 provider/model/base URL/API dialect/env/upstream 文件指纹发生变化，停止正式生成，要求先重新运行 doctor。
- 如果用户明确要求跳过 doctor gate，必须在回复中说明风险：正式图片生成可能在扣费后才暴露 provider 或下载链路问题。
- 不要打印或写入 API key 值；doctor 只记录凭证存在性和不可逆指纹。

如果 `--probe-image` 因 base URL 错误失败，提示用户检查所选 provider 对应的 base URL 环境变量，例如 `OPENAI_BASE_URL`、`AZURE_OPENAI_BASE_URL`、`DASHSCOPE_BASE_URL` 等。doctor 不会自动尝试另一个推导出来的 endpoint，避免让本地缓存和用户实际配置不一致。

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
