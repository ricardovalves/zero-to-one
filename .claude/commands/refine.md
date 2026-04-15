Refine a specific document in an existing project based on user feedback.

Use this when a phase has already run but the output isn't right — a weak PRD, a misaligned architecture, a design that missed the mark. Reruns the responsible agent with the original inputs plus your feedback, then offers to re-propagate downstream.

Usage: /refine <project> <document>

Valid documents: business-analysis, prd, design-spec, technical-spec

Arguments: $ARGUMENTS

---

## Pipeline

### STEP 1: Parse and validate

Parse $ARGUMENTS: first word = {project}, second word = {document}.

If either is missing, ask the user:
```
Which project and document would you like to refine?

  /refine <project> <document>

Valid documents:
  business-analysis  → reruns business-expert
  prd                → reruns product-manager
  design-spec        → reruns ux-designer
  technical-spec     → reruns cto-architect
```

Map document name to agent and file:

| Document | Agent | File |
|---|---|---|
| `business-analysis` | `business-expert` | `workspace/{project}/business-analysis.md` |
| `prd` | `product-manager` | `workspace/{project}/prd.md` |
| `design-spec` | `ux-designer` | `workspace/{project}/design-spec.md` |
| `technical-spec` | `cto-architect` | `workspace/{project}/technical-spec.md` |

Verify the file exists. If it doesn't, tell the user which command to run first.

Read the current file and the relevant handoff: `workspace/{project}/handoffs/{agent-name}.md`.

---

### STEP 2: Get feedback

Show the user a brief summary of what the current document contains (3–5 bullet points from the handoff file), then ask:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFINE — {document} ({project})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current version summary:
  • {bullet from handoff}
  • {bullet from handoff}
  • {bullet from handoff}

What would you like changed? Be as specific as possible.
Examples:
  "The target persona is wrong — it should be enterprise ops teams, not solo users"
  "The TAM feels inflated — use a more conservative bottom-up estimate"
  "The PRD is missing a proper opportunity map"
  "The architecture chose the wrong database — we need something that handles real-time"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for explicit feedback. Do not proceed without it.

---

### STEP 3: Rerun the agent

Launch the responsible agent with:
- All original inputs (idea-brief.md, prior handoffs, etc.)
- The user's feedback appended as a **Refinement Brief** at the top of the agent's context

Write the refinement brief to `workspace/{project}/refinements/{document}-{n}.md` before launching:

```markdown
# Refinement Brief — {document}

**Round:** {N} (increment each time this document is refined)
**Requested:** {datetime}

## User Feedback

{verbatim user feedback}

## Instruction to Agent

This is a refinement run. The previous version of {file} exists at {path}. You are not starting from scratch — you are improving a specific aspect based on the feedback above. Preserve everything that was not mentioned in the feedback. Only change what the feedback explicitly targets.

Read the previous version first. Identify what stays, what changes, and what the feedback implies about the direction. Then rewrite the document.
```

Launch the agent. Wait for completion.

---

### STEP 4: Show the diff and ask about propagation

After the agent completes, read the new handoff and summarise what changed:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFINEMENT COMPLETE — {document}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
What changed:
  • {key change 1}
  • {key change 2}
  • {key change 3}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then ask about downstream impact based on which document was refined:

| Document refined | Downstream that may need updating |
|---|---|
| `business-analysis` | prd, design-spec, technical-spec (everything) |
| `prd` | design-spec, technical-spec |
| `design-spec` | nothing (leaf node) |
| `technical-spec` | nothing (leaf node) |

If there are downstream documents:

```
This change may affect downstream documents:
  {list of affected documents}

Would you like to re-run those agents now? (yes / no / select specific ones)
```

Wait for the user's response. If yes (or specific selection), rerun the affected agents in parallel where possible, passing the updated upstream handoffs.

---

### STEP 5: Update assumptions log

Append to `workspace/{project}/assumptions.md`:

```markdown
## Refinement — {document} — {datetime}

**Feedback:** {summary of what the user asked to change}
**What changed:** {key changes made}
**Downstream re-run:** {yes — which agents / no}
```
