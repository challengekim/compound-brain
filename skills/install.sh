#!/bin/bash
set -e

SKILLS_DIR="$HOME/.claude/commands"
mkdir -p "$SKILLS_DIR"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp "$SCRIPT_DIR/save.md" "$SKILLS_DIR/save.md"
cp "$SCRIPT_DIR/learn.md" "$SKILLS_DIR/learn.md"
cp "$SCRIPT_DIR/recall.md" "$SKILLS_DIR/recall.md"

echo "Done. Skills installed to $SKILLS_DIR"
echo ""
echo "Usage in Claude Code:"
echo "  /save https://example.com/article"
echo "  /learn \"Lesson learned about X\""
echo "  /recall \"keyword to search\""
