Plan the next sprint for a project in Linear. Reads the roadmap and existing issues to determine what should be in the next sprint.

Usage: /sprint <project-name>

Arguments: $ARGUMENTS

---

## Steps

You are the CEO orchestrator running sprint planning for project: $ARGUMENTS

**Step 1: Verify prerequisites**
Check that `workspace/{project}/roadmap.md` exists. If not, invoke `project-manager` first.

**Step 2: Gather context**
Read:
- `workspace/{project}/roadmap.md`
- `workspace/{project}/prd.md` (for priority context)

If LINEAR_API_KEY is set, list current issues:
```bash
python .claude/tools/linear_client.py list-issues --project {project}
```

**Step 3: Invoke Project Manager for Sprint Planning**
Invoke the `project-manager` agent with:
- Task: "Plan the next 2-week sprint for {project}"
- Context: roadmap.md, current Linear issue statuses, any completed/in-progress items

The agent will:
- Identify which sprint this is (based on roadmap)
- Select issues for the sprint based on RICE priority and dependencies
- Calculate capacity (assume 70% of team week available)
- Create sprint in Linear (if API key is set)
- Output sprint plan to `workspace/{project}/sprint-{N}.md`

**Step 4: Completion Summary**

```
Sprint Planning Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:   {project}
Sprint:    {N} ({start date} — {end date})
Issues:    {N} issues, {X} story points
Teams:     Backend: {N}pts | Frontend: {N}pts | Infra: {N}pts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ workspace/{project}/sprint-{N}.md
  {✓ Linear sprint created | ⚠ Set LINEAR_API_KEY to sync to Linear}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
