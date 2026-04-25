#!/usr/bin/env node

import { cpSync, existsSync, mkdirSync, writeFileSync } from "fs";
import { execSync } from "child_process";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dir = dirname(fileURLToPath(import.meta.url));
const framework = resolve(__dir, "..");
const target = process.argv[2] ? resolve(process.argv[2]) : null;

if (!target) {
  console.error("\nUsage: npx zero-to-one /path/to/new-project\n");
  process.exit(1);
}

if (target === framework) {
  console.error("\nError: target cannot be the framework directory itself.\n");
  process.exit(1);
}

console.log(`\nBootstrapping Zero-to-One into: ${target}\n`);

mkdirSync(target, { recursive: true });

const copy = (src, label) => {
  const full = resolve(framework, src);
  if (existsSync(full)) {
    console.log(`  → Copying ${label}...`);
    cpSync(full, resolve(target, src), { recursive: true });
  }
};

mkdirSync(resolve(target, ".claude"), { recursive: true });
copy(".claude/agents", "agents");
copy(".claude/commands", "commands");
copy("CLAUDE.md", "framework rules");
copy("tools", "Linear client + utilities");
copy("templates", "document templates");
copy("references", "checklists + patterns");

if (!existsSync(resolve(target, ".gitignore"))) {
  console.log("  → Creating .gitignore...");
  writeFileSync(
    resolve(target, ".gitignore"),
    [
      "# Project workspaces",
      "workspace/",
      "",
      "# Environment files (secrets)",
      ".env",
      ".env.*.local",
      "",
      "# Claude Code local settings",
      ".claude/settings.local.json",
      "",
      "# Node / Next.js",
      "node_modules/",
      ".next/",
      ".vercel/",
      "out/",
      "",
      "# Python",
      "__pycache__/",
      "*.py[cod]",
      ".venv/",
      "*.egg-info/",
      "dist/",
      ".ruff_cache/",
      ".pytest_cache/",
      ".coverage",
      "htmlcov/",
      "",
      "# macOS",
      ".DS_Store",
    ].join("\n") + "\n"
  );
}

if (!existsSync(resolve(target, ".git"))) {
  console.log("  → Initialising git repo...");
  execSync("git init -q", { cwd: target });
  execSync("git add -A", { cwd: target });
  execSync('git commit -q -m "init: bootstrap Zero-to-One framework"', { cwd: target });
  console.log("  → Initial commit created.");
}

console.log(`
✓ Done. Framework ready in: ${target}

Next steps:
  1. Open Claude Code in ${target}
  2. /prototype "your idea"   — validate fast, show to real users
  3. /startup "your idea"     — full pipeline when you're ready to build

Framework source: ${framework}
`);
