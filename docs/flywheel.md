# Data Flywheel

BeeWeave is designed as a loop, not a one-way archive.

```text
collect -> create -> distill -> reuse context -> collect better material -> create the next piece
```

## 1. Collect

Put raw material into `workbench/`: links, notes, PDFs, exported chats,
meeting transcripts, screenshots, product briefs, source files, and findings
from agent sessions.

```text
/beeweave-ingest workbench/inbox
```

## 2. Create

Use the workbench as the drafting surface. Writing and workbench skills can
turn collected material into articles, social posts, research notes, specs, or
project output while keeping the raw sources nearby.

## 3. Distill

After work is published or a decision becomes stable, ingest the high-signal
output into the vault:

```text
/beeweave-article-publisher workbench/articles/drafts/my-article.md
/beeweave-ingest workbench/articles/published
/beeweave-update
```

Use `beeweave-article-publisher` for finished article drafts: it moves one
draft to `workbench/articles/published/`, marks it published, and ingests that
file into the wiki. Use `beeweave-ingest` directly for folders or non-article
source material.

The vault should hold durable concepts, entities, references, synthesis notes,
project decisions, and linked Markdown pages.

## 4. Reuse Context

Before the next task, query the vault so the agent starts from what you already
know:

```text
/beeweave-query what do I know about MCP security?
```

## 5. Collect Better and Create the Next Piece

Queries reveal gaps, drafts expose weak claims, and digests surface emerging
themes. Use those signals to decide what to collect next and what to create
from it.

![Data flywheel loop](assets/data-flywheel-loop.png)
