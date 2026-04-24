#!/bin/bash
# bootstrap.sh — seed a new project repo with the Zero-to-One framework
#
# Usage:
#   ./bootstrap.sh /path/to/my-new-project
#   ./bootstrap.sh ~/projects/my-app
#
# What it does:
#   1. Creates the target directory if it doesn't exist
#   2. Copies .claude/ (agents + commands) into the project
#   3. Copies CLAUDE.md (framework rules) into the project
#   4. Copies tools/ (Linear client, utilities) into the project
#   5. Copies templates/ (document templates used by agents) into the project
#   6. Copies references/ (checklists and patterns used by agents) into the project
#   7. Creates a starter .gitignore
#   8. Runs git init if the target isn't already a git repo
#
# After running this, open Claude Code in the target directory and run:
#   /startup <your-project-name>

set -euo pipefail

FRAMEWORK_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"

# ── Validate ────────────────────────────────────────────────────────────────

if [[ -z "$TARGET" ]]; then
  echo "Usage: ./bootstrap.sh /path/to/new-project"
  exit 1
fi

if [[ "$TARGET" == "$FRAMEWORK_DIR" ]]; then
  echo "Error: target cannot be the framework directory itself."
  exit 1
fi

# ── Copy framework files ─────────────────────────────────────────────────────

echo "Bootstrapping Zero-to-One framework into: $TARGET"
echo ""

mkdir -p "$TARGET"

echo "  → Copying .claude/ (agents + commands)..."
cp -r "$FRAMEWORK_DIR/.claude" "$TARGET/"

echo "  → Copying CLAUDE.md (framework rules)..."
cp "$FRAMEWORK_DIR/CLAUDE.md" "$TARGET/"

if [[ -d "$FRAMEWORK_DIR/tools" ]]; then
  echo "  → Copying tools/ (Linear client, utilities)..."
  cp -r "$FRAMEWORK_DIR/tools" "$TARGET/"
fi

if [[ -d "$FRAMEWORK_DIR/templates" ]]; then
  echo "  → Copying templates/ (document templates for agents)..."
  cp -r "$FRAMEWORK_DIR/templates" "$TARGET/"
fi

if [[ -d "$FRAMEWORK_DIR/references" ]]; then
  echo "  → Copying references/ (checklists and patterns for agents)..."
  cp -r "$FRAMEWORK_DIR/references" "$TARGET/"
fi

# ── Starter .gitignore ───────────────────────────────────────────────────────

if [[ ! -f "$TARGET/.gitignore" ]]; then
  echo "  → Creating .gitignore..."
  cat > "$TARGET/.gitignore" << 'EOF'
# Project workspaces — each project's src/ has its own git repo
workspace/

# Environment files (secrets)
.env
.env.*.local

# Claude Code local settings (machine-specific)
.claude/settings.local.json

# Node / Next.js
node_modules/
.next/
.vercel/
out/

# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/
dist/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/

# macOS
.DS_Store
EOF
fi

# ── Git init ─────────────────────────────────────────────────────────────────

if [[ ! -d "$TARGET/.git" ]]; then
  echo "  → Initialising git repo..."
  git -C "$TARGET" init -q
  git -C "$TARGET" add -A
  git -C "$TARGET" commit -q -m "init: bootstrap Zero-to-One framework"
  echo "  → Initial commit created."
fi

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Done. Framework is ready in: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Open Claude Code in $TARGET"
echo "  2. Run: /startup <your-project-name>"
echo "  3. The framework will guide you from idea → working prototype."
echo ""
echo "Framework source: $FRAMEWORK_DIR"
echo "Updates: re-run bootstrap.sh to refresh .claude/ from the latest framework."
