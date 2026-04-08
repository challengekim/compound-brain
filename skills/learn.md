# Learn

Capture a lesson learned to your persistent knowledge base.

## Usage

```
/learn "Lesson description"
/learn "Category: lesson description"
/learn
```

If called without arguments, ask the user what they learned.

## Categories

- `build` -- Build system, CI/CD, deployment issues
- `debug` -- Debugging techniques, error patterns
- `pattern` -- Code patterns, architectural decisions
- `security` -- Security gotchas, auth issues
- `perf` -- Performance optimization insights
- `convention` -- Naming, style, project conventions

If the user prefixes with a category (e.g. "build: Always include @types/node"), use that category. Otherwise, infer the most appropriate category from the content.

## Storage

Lessons are saved to `~/.claude/lessons/index.json`.

### File Format

```json
{
  "lessons": [
    {
      "id": "uuid",
      "category": "build",
      "lesson": "Always include @types/node in devDependencies -- CI fails without it",
      "date": "2024-01-15",
      "project": "project-name",
      "tags": ["typescript", "ci"]
    }
  ]
}
```

## Workflow

1. Parse the input for an optional `category:` prefix
2. If no category prefix, infer the category from content
3. Generate 2-4 tags from the lesson text
4. Read `~/.claude/lessons/index.json` (create if missing)
5. Append the new lesson with a UUID, current date, and detected project name
6. Write back the file
7. Confirm: "Lesson saved: [category] -- [first 60 chars]..."

## Limits

- Maximum 50 lessons in `index.json`
- If at capacity, show the oldest lesson and ask if it can be replaced
- Keep lessons concise -- one sentence per lesson ideally

## Deduplication

Before saving, check if a similar lesson already exists (same category + overlapping keywords). If found, ask the user whether to update the existing one or add as new.
