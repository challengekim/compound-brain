# Claude Code Skills Bundle

Companion skills for the PKM Briefing Bot. These add `/save`, `/learn`, and `/recall` commands to [Claude Code](https://claude.ai/claude-code).

## Skills

| Command | Description |
|---------|-------------|
| `/save <URL>` | Extract, summarize, categorize, and save web content to your vault |
| `/learn "lesson"` | Capture a lesson learned to a persistent database |
| `/recall keyword` | Search past lessons by keyword or category |

## Installation

### From the repo

```bash
cd skills/
bash install.sh
```

### One-liner

```bash
curl -sL https://raw.githubusercontent.com/user/pkm-briefing-bot/main/skills/install.sh | bash
```

### Manual

Copy the `.md` files to `~/.claude/commands/`:

```bash
cp save.md learn.md recall.md ~/.claude/commands/
```

## Configuration

Set your vault path in `~/.claude/CLAUDE.md` or your project's `CLAUDE.md`:

```
Vault: ~/Documents/my-knowledge
```

## Requirements

- [Claude Code](https://claude.ai/claude-code) installed
- A markdown folder (Obsidian vault, Logseq, or plain directory)
