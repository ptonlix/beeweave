# Project Config

使用本 reference 收集 setup 问题，并创建或合并当前 workspace/project root 下的项目级 Baoyu 配置。

## Setup Questions

首次配置或配置不完整时，先把下面问题一次性问清楚。能从用户请求或现有配置可靠推断时可以使用默认值，但必须在写入前向用户汇总。

需要收集：

- API provider：`google`、`openai`、`azure`、`openrouter`、`dashscope`、`zai`、`minimax`、`replicate`、`jimeng`、`seedream`、`agnes`。
- 模型：所选 provider 的具体模型或 deployment 名称。
- 默认质量：`2k` 或 `normal`，默认 `2k`。
- 默认比例：默认 `"16:9"`；可选 `"1:1"`、`"4:3"`、`"3:4"`、`"9:16"`、`"2.35:1"`。
- 默认尺寸：通常为 `null`；只有用户明确要求 `1K`、`2K`、`4K` 或 `WxH` 时写入。
- API dialect：通常为 `null`；OpenAI 兼容网关需要时可用 `openai-native` 或 `ratio-metadata`。
- 自定义 base URL：默认不设置；当用户使用代理、兼容网关、私有部署或 Azure 时，收集所选 provider 对应的 base URL 环境变量。
- 文章配图语言：默认 `zh`；可选 `en`、`ja`、`ko`、`auto`。
- 水印：默认关闭；如开启，收集内容、位置和透明度。
- 输出目录：固定 `imgs-subdir`，不要作为 setup 问题让用户选择。
- 配图风格：默认 `sketch-notes`；也可按用户偏好选择上游支持的 style。
- 配色：默认 `macaron`。
- 批量参数：默认 `generation_batch_size: 4`，`batch.max_workers: 4`。
- 凭证和 base URL 持久化位置：当前 workspace/project root 下的 `./.baoyu-skills/.env`。

不要把 `codex-cli` 作为默认 provider 问题选项。只有用户明确要求并理解它依赖 Codex CLI 登录时，才能手动配置；BeeWeave 默认流程不使用它。

## Field Meanings

向用户提问时不要只报英文枚举值。必须说明每个字段影响什么、默认值意味着什么，以及常见选择适合什么场景。

### Output Directory

`default_output_dir` 决定图片文件、`outline.md` 和 `prompts/` 放在哪里，也决定 Markdown 中插入的图片相对路径。

- BeeWeave 固定写入 `imgs-subdir`：图片放在文章同目录下的 `imgs/` 子目录，Markdown 插入 `imgs/NN-{type}-{slug}.png`。
- 不要向用户暴露 `same-dir`、`illustrations-subdir` 或 `independent` 作为 setup 选项。BeeWeave 会先通过 `article-workdir.md` 把散落 Markdown 文件整理到文章专属子目录，再使用 `imgs-subdir`，避免多篇文章共享同一个图片目录。

BeeWeave 文章配图流程要求输入是 Markdown 文件路径。用户只提供正文内容时，先提示用户保存为 `.md` 文件；这样才能稳定执行文章目录规范化，并保证图片写入该文章目录下的 `imgs/`。

### Illustration Style

`preferred_style.name` 决定图片的整体视觉语言：线条、材质、构图、图标、字体感和适合的内容类型。BeeWeave 默认使用 `sketch-notes`，因为它对知识文章最稳：暖色纸面、手绘线条、柔和色块，适合概念解释和教育类图解。

上游支持这些 style：

- `sketch-notes`：柔和手绘笔记风，暖色纸面、黑色手绘线条、浅色块。适合教育、知识总结、概念解释、onboarding。BeeWeave 默认值。
- `vector-illustration`：干净的扁平矢量插画，形状清晰、层级明确。适合知识文章、教程、技术内容。
- `notion`：极简手绘线稿，轻量、亲和。适合知识分享、SaaS、生产力工具、产品指南。
- `blueprint`：蓝图/工程示意风，网格和技术线条明显。适合系统设计、架构、工程、API、技术深潜。
- `editorial`：杂志信息图风，数据和新闻感更强。适合数据报道、技术解释、调查文章。
- `scientific`：学术精确图示风。适合科研、实验、医学、生物、化学和技术研究。
- `elegant`：精致、克制、专业。适合商业、战略、思想领导力、历史时间线。
- `warm`：温暖友好、有生活感。适合个人成长、叙事、生活方式、教育。
- `watercolor`：水彩和柔边艺术感。适合旅行、生活方式、创意、自然主题。
- `minimal`：极简、留白、禅意。适合哲学、极简主义和核心概念表达。
- `screen-print`：大胆海报、半调纹理、有限色。适合观点文章、文化评论、电影感叙事、对立观点。
- `ink-notes`：白底黑墨、少量语义强调色、专业视觉笔记。适合 before/after、职业/技术宣言、框架类比、思维转变。
- `chalkboard`：课堂黑板粉笔风。适合教学、解释型内容。
- `fantasy-animation`：童话/动画感手绘。适合故事、魔法感、情绪化内容。
- `flat`：现代几何扁平图形。适合数字产品、现代商业和当代主题。
- `flat-doodle`：可爱扁平涂鸦，轮廓更强。适合轻松、友好、教育内容。
- `intuition-machine`：旧纸张技术简报感。适合技术 brief、学术说明、复杂概念拆解。
- `nature`：自然、有机、土色系。适合环保、健康、自然主题。
- `pixel-art`：复古 8-bit 游戏像素风。适合游戏、复古技术、怀旧主题。
- `playful`：俏皮粉彩涂鸦。适合轻松、有趣、面向大众的教育内容。
- `retro`：80/90 年代霓虹几何。适合怀旧、流行文化、复古科技。
- `sketch`：原始铅笔笔记风。适合头脑风暴、创意探索、草图感表达。
- `vintage`：旧纸/历史档案感。适合历史、遗产、复古叙事。

如果用户不知道怎么选，按内容信号推荐：

- 通用知识文章：`sketch-notes`
- 教程/知识库：`sketch-notes`、`vector-illustration`、`notion`
- 技术/API/系统：`blueprint`、`vector-illustration`
- 架构/模型/方法论：`blueprint`、`vector-illustration`、`sketch-notes`
- 数据/指标/调查：`editorial`、`blueprint`
- 对比/评测：`vector-illustration`、`notion`、`sketch-notes`
- 叙事/个人经历：`warm`、`watercolor`
- 历史/演化：`elegant`、`warm`
- 观点/评论/文化：`screen-print`
- 科研/医学/实验：`scientific`
- 职业宣言/思维转变/专业视觉笔记：`ink-notes`

### Palette

`preferred_palette` 会覆盖 style 自带的默认颜色。它只改变色彩和背景，不改变 style 的线条、构图和材质规则。

上游支持这些 palette：

- `macaron`：柔和马卡龙色块，常见浅蓝、薄荷、薰衣草、蜜桃，暖米色背景。适合教育、知识总结、教程。BeeWeave 默认值。
- `warm`：暖色大地色，橙、陶土、金色、柔桃背景，避免冷色。适合品牌、产品、生活方式、温暖叙事。
- `neon`：深紫背景上的粉、青、黄等霓虹高饱和色。适合游戏、复古、流行文化、强视觉冲击。
- `mono-ink`：纯白背景、黑墨线条，少量语义强调色如珊瑚红、灰蓝绿、尘紫。适合专业视觉笔记、before/after、宣言、框架类比。
- `null`：不覆盖配色，使用所选 style 自带颜色。适合用户只想固定风格、不想强行套用统一色板。

### Language

`language` 决定图片内文字、短标签和 alt text 的默认语言。

- `zh`：中文，适合中文文章和中文知识库。BeeWeave 默认值。
- `en`：英文，适合英文文章或面向国际读者。
- `ja`：日文。
- `ko`：韩文。
- `auto`：让上游根据文章语言自动判断。适合多语言 workspace，但如果文章语言和用户偏好不一致，上游可能仍会在文章级步骤中确认。

### Watermark

`watermark` 决定是否在生成图上加轻量水印。默认关闭，避免污染图片。

- `watermark.enabled: false`：不加水印。推荐默认值。
- `watermark.enabled: true`：加水印，需要同时设置 `content`。
- `watermark.content`：水印文字，例如作者名、品牌名或 `@handle`。
- `watermark.position`：位置。上游支持 `bottom-right`、`bottom-left`、`bottom-center`、`top-right`。默认 `bottom-right`。
- `watermark.opacity`：透明度，BeeWeave 模板默认 `0.7`。数值越低越淡。

### Batch Parameters

`generation_batch_size` 是 `baoyu-article-illustrator` 在可并行时每批分发的图片数量。上游会将无效值限制在 1-8 内；BeeWeave 默认 `4`。

- `1`：最稳、最慢，适合 provider 限流严格或调试。
- `2-4`：推荐范围，速度和稳定性平衡。
- `5-8`：更快，但更容易触发 provider 限流或本地资源压力。

`batch.max_workers` 是 `baoyu-image-gen` 批量生成时的 worker 上限。BeeWeave 默认 `4`，并配合 provider-specific concurrency 和 start interval 控制请求节奏。

## Config Paths

默认写入当前 workspace/project root 下的项目级配置。下面路径都相对于当前 workspace/project root，例如在 `~/workstation/Wiki/craftbench` 中运行时，实际路径就是 `~/workstation/Wiki/craftbench/.baoyu-skills/...`。

```text
./.baoyu-skills/baoyu-article-illustrator/EXTEND.md
./.baoyu-skills/baoyu-image-gen/EXTEND.md
./.baoyu-skills/.env
```

如果配置文件已存在，先读取并汇总相关字段，再询问用户是否覆盖、合并或保留。除非用户明确要求，不要覆盖已有非空配置。需要修改时优先做最小改动，保证关键字段完整。

## Article Illustrator EXTEND.md

写入模板：

```yaml
---
version: 1
watermark:
  enabled: false
  content: ""
  position: bottom-right
  opacity: 0.7
preferred_style:
  name: sketch-notes
  description: ""
preferred_palette: macaron
default_output_dir: imgs-subdir
language: zh
preferred_image_backend: baoyu-image-gen
generation_batch_size: 4
custom_styles: []
---
```

必须保持：

```yaml
preferred_image_backend: baoyu-image-gen
```

不要写 `auto`、`ask`、`codex-imagegen`、`imagegen`、`GenerateImage` 或 `image_generate` 作为 BeeWeave 默认路径。

## Image Gen EXTEND.md

写入完整 frontmatter。将 `<provider>` 和 `<model>` 替换为用户选择值，并保证所选 provider 的 `default_model` 非 `null`。

```yaml
---
version: 1
default_provider: <provider>
default_quality: 2k
default_aspect_ratio: "16:9"
default_image_size: null
default_image_api_dialect: null
default_model:
  google: null
  openai: null
  azure: null
  openrouter: null
  dashscope: null
  zai: null
  minimax: null
  replicate: null
  jimeng: null
  seedream: null
  codex-cli: null
  agnes: null
batch:
  max_workers: 4
  provider_limits:
    google:
      concurrency: 3
      start_interval_ms: 1100
    openai:
      concurrency: 3
      start_interval_ms: 1100
    azure:
      concurrency: 3
      start_interval_ms: 1100
    openrouter:
      concurrency: 3
      start_interval_ms: 1100
    dashscope:
      concurrency: 3
      start_interval_ms: 1100
    zai:
      concurrency: 3
      start_interval_ms: 1100
    minimax:
      concurrency: 2
      start_interval_ms: 1500
    replicate:
      concurrency: 2
      start_interval_ms: 1500
    jimeng:
      concurrency: 2
      start_interval_ms: 1500
    seedream:
      concurrency: 2
      start_interval_ms: 1500
    agnes:
      concurrency: 2
      start_interval_ms: 1500
---
```

例如 OpenAI：

```yaml
default_provider: openai
default_model:
  openai: gpt-image-2
```

如果 `default_provider` 为 `null`，上游会按 API key 自动探测 provider；本技能不要这样写。如果所选 provider 的 `default_model.<provider>` 为 `null`，上游会继续询问模型；本技能不要这样写。
