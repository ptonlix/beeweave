# BeeWeave Capture

A zero-build Chrome extension that captures the active page URL and readable text into the BeeWeave workbench inbox.

## Install

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select this folder: `extensions/brain-capture`.

## Use

The extension cannot read local config files directly. Chrome requires you to
grant write access by selecting the target folder once. To locate the inbox from
the global BeeWeave config, run:

```bash
awk -F= '/^BEEWEAVE_REPO=/{gsub(/^[ \t\"]+|[ \t\"]+$/, "", $2); print $2 "/workbench/inbox/web"; exit}' "$HOME/.beeweave/config"
```

1. Open the extension popup.
2. Click **Choose workbench/inbox/web** and select `workbench/inbox/web`.
3. Open any normal web page and click **Capture current page**.
4. Or right-click a page and choose **Capture page to workbench inbox**.
5. Or select text, right-click, and choose **Capture selection to workbench inbox**.

The extension writes a markdown file named like `2026-06-17-page-title.md` into `workbench/inbox/web/`.

## Promote Captures Into The Wiki

After captures land in `workbench/inbox/web/`, run the ingest skill from your AI agent:

```text
/wiki-ingest workbench/inbox
```

The ingest skill will distill the captures into proper wiki pages and update the vault bookkeeping files.

## What Gets Captured

- YAML frontmatter with title, source URL, creation timestamp, and capture metadata.
- The page title, URL, optional user note, selected text, and readable page text.
- Content is capped at 140,000 characters to keep captures usable for later wiki ingest.
