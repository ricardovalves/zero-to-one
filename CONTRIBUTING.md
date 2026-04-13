# Contributing to Zero-to-One

Thank you for your interest in improving this framework. Contributions that make the agents smarter, more resilient, or more useful are always welcome.

---

## What We're Looking For

| Type | Examples |
|---|---|
| **Agent improvements** | New "Known Failure Mode" entries backed by a real build failure; stronger quality bar sections; better output examples |
| **New agents** | `mobile-engineer`, `data-engineer`, `seo-engineer` — must meet the quality bar below |
| **New slash commands** | New pipeline phases or workflows that don't exist yet |
| **Pattern fixes** | A generic bug pattern discovered during a real build that the current agents don't prevent |
| **Reference projects** | A complete `workspace/{project}/` example that demonstrates an underrepresented product type |
| **Bug reports** | An agent prompt that consistently produces wrong, incomplete, or low-quality output |

We are **not** looking for:
- Your `workspace/` project files — those stay local
- Technology opinions that override framework defaults without documented rationale
- Prompts that hard-code a specific stack where a generic principle works
- Vague improvements ("make this agent better") without a concrete before/after

---

## Workflow

```bash
# 1. Fork and clone
git clone https://github.com/your-fork/zero-to-one.git
cd zero-to-one

# 2. Create a branch
git checkout -b feat/improve-backend-agent
# or: fix/scope-auto-resolution-pattern
# or: agent/mobile-engineer

# 3. Make your changes
# 4. Open a pull request against main
```

Branch naming: `feat/`, `fix/`, `agent/`, or `docs/` prefix followed by a short description.

Commit style: plain descriptive English — no strict conventional commits required, but be specific. "Add bcrypt async pattern to backend agent" is good. "Update agent" is not.

---

## Agent Prompt Quality Bar

Every agent in `.claude/agents/` must meet this bar before merging. Use existing agents (especially `backend-engineer.md` and `frontend-engineer.md`) as the reference.

**Required sections:**
- **Role and seniority** — who this agent is, what worldview they bring
- **Communication rules** — reads from filesystem, writes to filesystem, no direct agent calls
- **Context management protocol** — in what order to read inputs (most compressed first)
- **Inputs** — exact file paths to read before writing anything
- **Standards** — the specific, opinionated rules this agent follows (not generic advice)
- **Known failure modes** — classes of bugs this agent must prevent, with root cause and fix
- **Output** — exact file paths written, format, what must be included
- **Quality bar** — the checklist used to decide if the output is done

**What makes a prompt good:**

- Opinionated and specific — "use `selectinload` for relationship loading in async SQLAlchemy" beats "load relationships efficiently"
- Generic where possible — the principle should apply beyond one stack
- Grounded in real failures — every "Known Failure Mode" entry should come from an actual build
- No placeholder content — every example must be a real, runnable snippet

**Minimum length:** ~600 words. Shorter prompts are almost always too vague to produce consistent output.

---

## Submitting a New Agent

1. Create `.claude/agents/{name}.md` following the frontmatter schema:

```markdown
---
name: your-agent-name
description: >
  One or two sentences describing when to invoke this agent.
  Written from the orchestrator's perspective ("Use when you need...").
tools:
  - Read
  - Write
  - Bash      # only if the agent needs to run shell commands
  - WebSearch # only if the agent needs to search for current practices
---
```

2. Add the agent to the team table in `CLAUDE.md` (Strategic, Execution, or Quality Gate layer)
3. Add it to the team list in `README.md`
4. Add an invocation example in the "Individual Agents" section of `README.md`
5. Write a handoff note convention: every agent must produce `workspace/{project}/handoffs/{agent-name}.md` — a 10-bullet summary of key decisions for downstream agents

---

## Adding a Known Failure Mode

This is the highest-value contribution. A "Known Failure Mode" is a class of bug that:
- Was discovered in a real build
- The agent should have prevented but didn't
- Will affect future projects if not documented

**Where it goes:** inside the existing relevant section of the agent file — not appended at the bottom as a "lessons learned" block.

**Format:**
```markdown
**{Concise name of the failure pattern}**
Root cause: {why it happens}
Symptom: {what the developer sees — error message, blank screen, wrong HTTP status}
Fix: {the correct pattern, with a code example if helpful}
```

**Rules:**
- Generic — no project-specific names, entity types, or values
- Tech-agnostic at the principle level — a stack-specific code example is fine as illustration, but the rule itself must apply broadly (e.g. "scope IDs must be auto-resolved server-side from the auth token" — not "workspace_id must be an optional FastAPI Query param")
- Not already covered — check for existing similar entries and update rather than duplicate

---

## Testing a Contribution

There are no automated tests for prompt quality — you validate by running the pipeline.

**For agent prompt changes:**
1. Run `/startup "a simple idea"` end-to-end and verify the modified agent's output is more correct or complete than before
2. If you added a "Known Failure Mode" entry, demonstrate that following the new guidance prevents the failure (show the before/after in your PR description)

**For new slash commands:**
1. Run the command against a real project in `workspace/`
2. Verify it produces its expected outputs without manual intervention
3. Verify it handles missing prerequisites gracefully (tells the user what to run first)

**For new agents:**
1. Invoke the agent directly: `@your-agent-name <task>` in Claude Code
2. Verify the output meets the quality bar defined in the agent file itself
3. Run the full pipeline with the new agent included and confirm no regressions

Include a brief description of how you tested in your PR.

---

## Reporting Issues

### Agent produces wrong or low-quality output

Include:
- The exact input given (idea, project, or task description)
- The agent invoked and the relevant section of the prompt
- The actual output received
- What the correct output should look like

The more specific, the faster it gets fixed.

### Missing failure mode pattern

Include:
- The symptom you saw (error message, wrong HTTP status, blank screen, etc.)
- The root cause once you diagnosed it
- The fix you applied
- Which agent should have prevented it

This is the exact information needed to add a "Known Failure Mode" entry.

### Pipeline breaks between agents

Include:
- Which handoff failed (which agent produced an output the next agent couldn't use)
- The contents of the relevant `handoffs/{agent}.md` file
- What the downstream agent expected vs. what it received

---

## Code of Conduct

Be direct, specific, and respectful. Vague feedback ("this prompt is bad") is not useful. Concrete feedback ("this prompt doesn't handle the case where a user has no workspace yet — here's the pattern that fixes it") is.

Contributions that introduce placeholder content, hard-coded project-specific values, or prompts that haven't been validated against a real pipeline run will be sent back for revision.
