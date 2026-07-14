# Provider Settings

使用本 reference 选择 `baoyu-image-gen` API provider、模型、凭证变量和自定义 base URL。

## Field Meanings

向用户展示 provider 选择时，要说明每个字段影响什么，不要只列英文枚举值。

- `default_provider`：默认图片 API 供应商。BeeWeave 必须固定为用户选择的 API provider，不能设为 `null`，否则上游会按 API key 自动探测，导致不同机器行为不一致。
- `default_model.<provider>`：所选 provider 使用的具体图片模型或 Azure deployment 名称。所选 provider 对应字段必须非 `null`，否则上游会再次询问模型。
- `default_quality`：默认质量。`2k` 更适合正式文章配图、封面和信息图；`normal` 更快、更省成本，适合草稿或预览。BeeWeave 默认 `2k`。
- `default_aspect_ratio`：默认画面比例。`16:9` 适合横向文章配图和公众号/博客正文；`1:1` 适合社交平台方图；`4:3` 适合传统插图和幻灯片感；`3:4` 适合竖向图文；`9:16` 适合手机竖屏；`2.35:1` 适合电影感横幅。
- `default_image_size`：Google/OpenRouter 等 provider 的图片尺寸级别。`null` 表示由 quality 推导；`1K` 适合预览；`2K` 适合正式文章；`4K` 适合高分辨率但更慢、更贵。只有用户明确要求时写入，默认 `null`。
- `default_image_api_dialect`：OpenAI-compatible 网关的请求格式。`openai-native` 用于 OpenAI 官方或严格兼容接口；`ratio-metadata` 用于期望比例和 metadata 分辨率的兼容网关；`null` 表示使用上游默认或环境变量。
- 自定义 base URL：provider 的 API endpoint。默认不设置，使用官方 endpoint；代理网关、私有部署、OpenAI-compatible gateway 或 Azure 时需要设置。
- `batch.max_workers`：批量生成最大 worker 数。数值越大并发越高，但更容易触发限流。
- `batch.provider_limits.<provider>.concurrency`：某个 provider 同时运行的请求数上限。
- `batch.provider_limits.<provider>.start_interval_ms`：同一 provider 两次请求启动之间的最小间隔，用来避免瞬时请求过密。

## Provider Defaults

所选 provider 的 `default_model.<provider>` 必须写为非 `null`。如果用户没有指定模型，使用下面默认建议：

- `google`：Google/Gemini 图片生成 API。适合通用高质量图片、参考图能力和多模态场景。默认模型 `gemini-3-pro-image`；凭证 `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`。
- `openai`：OpenAI Images API。适合使用 OpenAI 官方图片模型和 OpenAI-compatible 生态。默认模型 `gpt-image-2`；凭证 `OPENAI_API_KEY`。
- `azure`：Azure OpenAI 图片部署。适合企业 Azure 资源、私有网络和合规部署。模型字段是 Azure deployment 名称，不一定等于底层模型名；凭证 `AZURE_OPENAI_API_KEY` 和 `AZURE_OPENAI_BASE_URL`。
- `openrouter`：OpenRouter 统一网关。适合通过一个入口访问多个多模态/图片模型，或使用 OpenRouter 计费与路由。默认模型 `google/gemini-3.1-flash-image`；凭证 `OPENROUTER_API_KEY`。
- `dashscope`：阿里云 DashScope/通义万相。适合国内网络和 Qwen Image 系列。默认模型 `qwen-image-2.0-pro`；凭证 `DASHSCOPE_API_KEY`。
- `zai`：Z.AI / 智谱 GLM-Image。适合使用 GLM 图片能力或已有智谱账号。默认模型 `glm-image`；凭证 `ZAI_API_KEY` 或 `BIGMODEL_API_KEY`。
- `minimax`：MiniMax 图片 API。适合 MiniMax 账号体系和 subject reference 相关能力。默认模型 `image-01`；凭证 `MINIMAX_API_KEY`。
- `replicate`：Replicate 模型托管平台。适合使用 Replicate 上的图片模型家族和托管生态。默认模型 `google/nano-banana-2`；凭证 `REPLICATE_API_TOKEN`。
- `jimeng`：即梦/火山引擎视觉能力。适合已有火山引擎即梦接入。默认提示用户填写当前可用即梦模型；凭证 `JIMENG_ACCESS_KEY_ID` 和 `JIMENG_SECRET_ACCESS_KEY`。
- `seedream`：豆包 Seedream/火山 ARK 图片能力。适合已有火山 ARK 接入。默认提示用户填写当前可用 Seedream 模型；凭证 `ARK_API_KEY`。
- `agnes`：Sapiens AI Agnes 图片 API。适合高信息密度、复杂布局和参考图支持。默认提示用户填写 Agnes 模型；凭证 `AGNES_API_KEY`。

Provider 选择建议：

- 想要默认稳妥、参考图支持和通用质量：优先 `google`。
- 已有 OpenAI API key 或 OpenAI-compatible 网关：选 `openai`，必要时配置 `OPENAI_BASE_URL` 和 `default_image_api_dialect`。
- 企业 Azure 环境：选 `azure`，必须提供 deployment 和 `AZURE_OPENAI_BASE_URL`。
- 国内云服务或 Qwen Image：选 `dashscope`。
- 需要统一模型网关：选 `openrouter`。
- 想使用 Replicate 模型生态：选 `replicate`。
- 已有智谱、MiniMax、火山、Agnes 账号时，按对应 provider 选择。

## Custom Base URL

`baoyu-image-gen` 通过环境变量读取自定义 endpoint/base URL，而不是通过 `EXTEND.md` 读取统一的 `base_url` 字段。因此本技能必须把 base URL 写入当前 workspace/project root 下的 `./.baoyu-skills/.env`，让 Baoyu 从项目级 env 文件读取。

支持的 base URL 变量：

- `openai`：`OPENAI_BASE_URL`。
- `azure`：`AZURE_OPENAI_BASE_URL`，这是 Azure 的必需变量，可以是 resource endpoint 或 deployment endpoint。
- `google`：`GOOGLE_BASE_URL`。
- `openrouter`：`OPENROUTER_BASE_URL`。
- `dashscope`：`DASHSCOPE_BASE_URL`。
- `zai`：`ZAI_BASE_URL`，兼容别名 `BIGMODEL_BASE_URL`。
- `minimax`：`MINIMAX_BASE_URL`。
- `replicate`：`REPLICATE_BASE_URL`。
- `jimeng`：`JIMENG_BASE_URL`。
- `seedream`：`SEEDREAM_BASE_URL`。
- `agnes`：`AGNES_BASE_URL`。

规则：

- 默认不写 base URL，让上游使用 provider 官方 endpoint。
- 如果用户选择“自定义供应商”“OpenAI-compatible gateway”“代理网关”“私有 endpoint”或明确给出 URL，必须写入所选 provider 对应的 base URL 变量。
- 对 `openai` 兼容网关，通常还要确认 `default_image_api_dialect`：OpenAI 官方或严格兼容接口用 `openai-native`，只支持比例/metadata 的网关用 `ratio-metadata`。
- 对 `azure`，`AZURE_OPENAI_BASE_URL` 必须存在；如果 URL 已包含 `/openai/deployments/<deployment>`，仍建议把 `default_model.azure` 写为同一个 deployment 名称，避免上游再次询问模型。
- 不要把自定义 base URL 写入 `baoyu-image-gen/EXTEND.md`，除非上游未来明确新增该 schema 字段。

## Env File

凭证和 base URL 检查以当前 workspace/project root 下的 `./.baoyu-skills/.env` 为准。当前进程环境变量可以作为运行时已存在凭证被识别，但 BeeWeave setup 的持久化配置目标始终是 workspace/project root 下的 `./.baoyu-skills/`，并且不应把 secrets 写入 `EXTEND.md`。不要打印 secret 值；base URL 可以打印主机名或完整 URL 供用户核对，但不要打印 API key。

如果所选 provider 的必需变量缺失，停止 setup，并展示精确变量名和目标文件：

```text
./.baoyu-skills/.env
```

示例：

```dotenv
# 不要提交这个文件
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
```

提醒用户不要提交当前 workspace/project root 下的 `./.baoyu-skills/.env`，必要时检查项目 `.gitignore` 是否覆盖 `./.baoyu-skills/.env` 或 `./.baoyu-skills/`。
