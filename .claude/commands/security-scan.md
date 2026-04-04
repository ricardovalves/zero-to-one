Run a comprehensive security audit of an entire project's source code.

Covers OWASP Top 10, STRIDE threat modeling, dependency scanning, and produces a prioritized remediation plan.

Usage: /security-scan <project-name>

Arguments: $ARGUMENTS

---

## Steps

You are the CEO orchestrator running a full security audit for project: $ARGUMENTS

**Step 1: Verify project exists**
Check that `workspace/{project}/src/` exists with code to scan.

**Step 2: Dependency Scanning**
Run automated dependency vulnerability checks:
```bash
# Python dependencies
cd workspace/{project}/src/backend
pip-audit --requirement requirements.txt --format=json

# Node.js dependencies
cd workspace/{project}/src/frontend
npm audit --json
```

Collect and save output for the security-engineer agent.

**Step 3: Run Security Engineer — Full Audit**
Invoke the `security-engineer` agent with:
- Full scope: all files under `workspace/{project}/src/`
- Dependency audit results from Step 2
- `workspace/{project}/technical-spec.md` for architecture context
- `workspace/{project}/api-spec.yaml` for API surface context

The agent will apply:
- OWASP Top 10 (2021) checklist to the entire codebase
- STRIDE threat model for the application architecture
- CWE classification for all findings
- Dependency CVE analysis
- Security headers and configuration review

**Step 4: Produce Remediation Plan**
Based on the security assessment, produce a prioritized remediation plan:

```markdown
# Security Remediation Plan: {project}

## Immediate (fix before next deploy)
{CRITICAL findings with exact fixes}

## This Sprint (fix within 2 weeks)
{HIGH findings with guidance}

## Next Sprint (fix within 4 weeks)
{MEDIUM findings}

## Backlog (fix when convenient)
{LOW and INFO findings}
```

**Step 5: Summary**

```
Security Audit Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:   {project}
Files:     {N} scanned
Overall:   {CRITICAL/HIGH/MEDIUM/LOW/PASS}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Findings:
  CRITICAL: {N}  ← Must fix before next deploy
  HIGH:     {N}  ← Fix this sprint
  MEDIUM:   {N}  ← Fix next sprint
  LOW/INFO: {N}  ← Backlog
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ workspace/{project}/security-audit.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Save the full report to `workspace/{project}/security-audit.md`.
