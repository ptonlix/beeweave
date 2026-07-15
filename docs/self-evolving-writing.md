# Self-Evolving Writing Workflow

BeeWeave's self-evolving writing workflow is coordinated by four groups of
skills:

- writers: `beeweave-article-writer` and `beeweave-social-writer` handle
  writing, revision, current draft persistence, and trace recording.
- initializer: `beeweave-writing-style-initializer` initializes writing style
  asset templates.
- learner: `beeweave-writing-style-learner` extracts candidate rules from
  historical articles, traces, diffs, and feedback.
- evolver: `beeweave-writing-skill-evolver` reviews, validates, activates,
  rejects, rolls back, and compacts writing rules.

## First Use

Writing style assets live in the current Workbench:

```text
workbench/writing/
+-- style/
+-- traces/
+-- eval/
```

The `style/` directory stores user style assets, including author profile,
active rules, anti-patterns, examples, pending rules, rejected rules, and the
evolution log. `beeweave-writing-style-initializer` is the explicit
initialization entrypoint.

Templates live under `beeweave-writing-style-initializer/references/`.
Article and social writers do not own these templates. If style assets are not
initialized, they prompt the user to initialize them first. If the user still
wants to continue writing, writers proceed with built-in defaults. Real user
style assets are stored only under `workbench/writing/`.

## Initialize Style Assets

On first use, run the initializer to create the fixed writing style asset files:

```text
/beeweave-writing-style-initializer
```

After initialization, ask the learner to study historical articles:

```text
/beeweave-writing-style-learner workbench/articles/published
```

The initializer only creates directories and the eight fixed template files. It
does not learn from articles. The learner studies historical articles, traces,
diffs, or feedback only after initialization is complete.

## Daily Writing

When writing long-form articles or short social content, writers first read the
applicable active style rules, anti-patterns, and examples, then create a draft.
Drafts are still saved to:

```text
workbench/articles/drafts/
```

By default, one piece of content maintains a single current working draft. When
the user asks AI to revise, shorten, expand, change the opening, or revise based
on feedback, the writer updates the current `draft_path` instead of creating a
pile of `-v2`, `-v3`, or `-final` files by default.

Version history is written to:

```text
workbench/writing/traces/YYYY-MM-DD-<type>-<slug>/
+-- trace.md
+-- trace.json
```

Traces record paths, summaries, version events, diff summaries, and learning
state by default. They do not copy the full body text. Full body snapshots are
stored under trace `snapshots/` only when the user explicitly asks to save full
process snapshots, preserve a specific version, or mark a version as a learning
sample.

## AI Revisions and Manual Edits

If the user asks AI to revise a draft, for example "the opening is too grand;
make it start from a real experience", the writer records that revision as a
`revision_events` entry containing the user instruction, diff summary, and a
strong learning signal.

If the user manually edits a draft and says "this is my edited version; learn
what I changed", the learner reads the original draft, edited draft, or trace
and extracts stable editing patterns.

Signal strength is interpreted in this order:

- Manual user edits are strong signals.
- User-instructed AI revisions are strong signals.
- AI self-revisions without user confirmation are weak signals.
- Versions marked final, published, or explicitly accepted have stronger
  evidence.
- Rejected, abandoned, or unused versions can only become anti-pattern
  candidates.

## Rule Learning and Activation

By default, the learner only writes candidate rules to:

```text
workbench/writing/style/pending_rules.md
```

Each candidate includes scope, suggested layer, evidence, confidence, and
validation suggestions. The learner does not modify `active_style_rules.md` or a
writer `SKILL.md` by default.

When the user asks to activate, reject, or organize candidates, the evolver first
decides which layer each candidate belongs to:

- routing layer: adjusts skill trigger boundaries.
- instruction layer: adjusts stable workflow and quality standards.
- resource layer: adjusts Workbench style assets, examples, narrow scenarios,
  or eval cases.

Changes that affect active rules, rejected rules, source `SKILL.md` files, or
shared references require validation results or explicit user confirmation.
Validation material lives under `workbench/writing/eval/`; it can compare
outputs before and after a change using historical briefs, user final drafts,
and rubrics.

The evolver only handles rule lifecycle and style asset maintenance. It does not
publish articles, move drafts, trigger wiki ingestion, or manage trace publish
metadata during normal publishing.

## Publishing, Cleanup, and Compaction

When publishing, `beeweave-article-publisher` treats the current working draft as
the candidate final draft, moves it to `workbench/articles/published/`, updates
frontmatter, and triggers wiki ingestion.

If the draft has a corresponding trace, the publisher updates `status`,
`final_version`, `published_path`, and the cleanup summary in the trace, then
appends a `published` revision event. If the trace cannot be found or cannot be
updated, publishing and wiki ingestion are not blocked, but the final response
explains that the trace was not updated.

The publisher does not create a new base trace and does not manufacture a new
writing version for publishing. `final_version` defaults to the trace's current
version.

If a trace contains temporary `snapshots/`, the publisher does not delete any
snapshot by default. It cleans temporary snapshots only when the user explicitly
asks for post-publish cleanup, while preserving the final snapshot or snapshots
explicitly marked as learning samples. No extra cleanup is needed when there are
no snapshots.

As rules accumulate, ask `beeweave-writing-skill-evolver` to perform compaction.
It proposes a plan to merge duplicate rules, move narrow rules down into assets,
delete long-term ineffective rules, and preserve key rules. After confirmation,
it updates style assets and writes to `evolution_log.md`.
