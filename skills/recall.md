# Recall

Search your lesson database for relevant past learnings.

## Usage

```
/recall keyword
/recall category:build
/recall --all
```

## How It Works

1. Read `~/.claude/lessons/index.json`
2. If the file doesn't exist, report "No lessons saved yet. Use /learn to capture your first lesson."
3. Search by:
   - **Keyword**: Match against lesson text and tags (case-insensitive)
   - **Category prefix** (`category:build`): Filter by category first, then optionally by keyword
   - **`--all`**: List all lessons grouped by category
4. Display matching lessons in a readable format:
   ```
   [build] 2024-01-15 -- Always include @types/node in devDependencies
   [debug] 2024-01-10 -- Check CORS headers before debugging fetch failures
   ```
5. If no matches found, suggest related categories or broader search terms

## Output Format

Group results by category. Show date and lesson text. If more than 10 results, show count and ask if the user wants to see all.

```
Found 3 lessons matching "typescript":

[build] 2024-01-15 -- Always include @types/node in devDependencies
[pattern] 2024-01-12 -- Use discriminated unions instead of optional fields
[convention] 2024-01-08 -- Prefer interface over type for public APIs

Tip: Use /learn to add new lessons.
```
