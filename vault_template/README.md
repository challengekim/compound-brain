# Knowledge Vault Structure

This is your personal knowledge base. Save articles, notes, and ideas here as markdown files with YAML frontmatter.

## Directory Structure

- `00_Inbox/Read Later/` -- Articles to read later (unsorted)
- `10_Knowledge/References/` -- Categorized knowledge by topic
- `20_Projects/AI Ideas/` -- AI-generated project ideas (auto-populated by the bot)

## Frontmatter Format

Each `.md` file should have YAML frontmatter for the scanner to process it:

```yaml
---
title: Article Title
description: One-line description
source: https://example.com/article
author: Author Name
saved: 2024-01-15
tags: [ai, startup]
---

Article content here...
```

## Compatible Tools

This vault works with any markdown editor:
- [Obsidian](https://obsidian.md) (free for personal use)
- [Logseq](https://logseq.com)
- VS Code / any text editor
- Just a file browser + text editor
