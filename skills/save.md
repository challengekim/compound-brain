# Save

Save a web link to your knowledge vault as structured markdown with AI-generated summaries.

## Usage

```
/save <URL>
/save <URL> <optional notes>
```

## Configuration

Set your vault path in your project's `CLAUDE.md` or `~/.claude/CLAUDE.md`:

```
Vault: ~/Documents/my-knowledge
```

If no vault path is configured, the skill will prompt you to set one.

## Workflow

When the user provides a URL:

### Step 1: Extract Content

Try extraction methods in order:
1. **defuddle** (if installed): `npx @anthropics/defuddle <URL>` -- best quality extraction
2. **WebFetch tool** (fallback): Use the built-in WebFetch tool to fetch the page content
3. **curl** (last resort): `curl -sL <URL>` and parse the HTML

### Step 2: Analyze and Categorize

Use your AI capabilities to:
- Generate a concise **title** (if not extracted)
- Write a 2-3 sentence **description**
- Determine the **category** from: `AI Engineering`, `AI Tools`, `Business`, `Engineering`, `Marketing`, or create a new one if none fit
- Generate 3-7 **tags** as lowercase keywords
- Write **key takeaways** (3-5 bullet points)
- Write **application points** -- how this applies to the user's current projects

### Step 3: Determine File Location

Based on the category:
- `AI Engineering` -> `10_Knowledge/References/AI Engineering/`
- `AI Tools` -> `10_Knowledge/References/AI Tools/`
- `Business` -> `10_Knowledge/References/Business/`
- `Engineering` -> `10_Knowledge/References/Engineering/`
- `Marketing` -> `10_Knowledge/References/Marketing/`
- Unknown -> `00_Inbox/Read Later/`

### Step 4: Create Markdown File

Filename: sanitized title with date prefix, e.g. `2024-01-15-building-rag-pipelines.md`

```markdown
---
title: "Article Title Here"
description: "One-line description"
source: https://example.com/article
author: Author Name
saved: YYYY-MM-DD
tags: [tag1, tag2, tag3]
category: AI Engineering
---

## Summary

2-3 sentence summary of the article.

## Key Takeaways

- Takeaway 1
- Takeaway 2
- Takeaway 3

## Application Points

- How this applies to your current work
- Potential project ideas inspired by this

## Original Content

(Extracted article content, cleaned up)
```

### Step 5: Save and Confirm

1. Write the file to the vault
2. Report: file path, category, tags, and a one-line summary
3. If there are related notes in the vault, mention them

## Notes

- The skill searches for vault path in this order: `CLAUDE.md` in project root, then `~/.claude/CLAUDE.md`
- Look for a line matching `Vault:` or `vault_path:` followed by a path
- Expand `~` to the user's home directory
- If the vault directory doesn't exist, create it with the standard structure from `vault_template/`
