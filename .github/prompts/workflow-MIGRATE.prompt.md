---
description: "Migrate the ns-template workflow into an existing project's .github folder. Analyzes both workflows and the project, plans the merge, and executes with user approval at every step."
argument-hint: "Path to the target project root (absolute), or leave blank if already in the target project"
tools: [agent, memory, vscode/askQuestions]
model: Claude Opus 4.6 (copilot)
---

# 🔄 MIGRATE — Workflow Migration

You are migrating the `ns-template` workflow into an existing project. This is an interactive, gate-driven process. You never modify files without showing the user a plan and receiving explicit approval.

---

## Step 1 — Locate Both Sides

Determine:
- **Template root** — where this prompt lives (the `ns-template` repo)
- **Target root** — the project receiving the workflow (from the argument, or ask the user)

Spawn **`reader` subagent** instances in parallel to inventory both sides:

**Template inventory** — read and summarise:
- `.github/prompts/` — all prompt files (names + one-line description from frontmatter)
- `.github/agents/` — all subagent files (names + roles)
- `.github/skills/` — all skill directories
- `.github/hooks/` — all JSON config files + scripts
- `.github/templates/` — all artifact templates
- `.github/copilot-instructions.md`
- `.github/instructions/` — any instruction files

**Target inventory** — read and summarise:
- `.github/` — everything that already exists (prompts, agents, workflows, instructions, CODEOWNERS, etc.)
- `README.md` — project purpose and tech stack hints
- Root files that indicate tech stack: `package.json`, `requirements.txt`, `pyproject.toml`, `*.tf` (top-level or `infrastructure/`), `*.bicep`, `Dockerfile`, `go.mod`, `.nvmrc`
- Any existing `copilot-instructions.md` or `.github/copilot-instructions.md`

---

## Step 2 — Understand the Project

Ask the user the following questions **one at a time**, in order. Skip any question where the answer is already clear from Step 1.

1. **Scope** — *"Do you want the full AI development workflow (START → PLAN → BUILD → END) or just the utility prompts (git, azure, terraform ops)?"*

2. **Azure** — *"Does this project use Azure? (Determines whether to include the azure agent, skill, and deploy/query prompts)"* — if yes, ask: *"Is Azure CLI already configured in this environment?"*

3. **Terraform** — *"Does this project use Terraform or OpenTofu? (Determines whether to include the terraform agent, skill, and plan/apply prompts)"*

4. **Python** — *"Does this project use Python with a virtual environment? (Affects the venv check in session-start hook)"*

5. **Existing instructions** — If the target already has a `copilot-instructions.md`: *"Your project already has copilot-instructions.md. Should I merge the template's rules into it, replace it, or keep yours and skip the template's?"*

6. **Existing prompts/agents** — If the target already has `.github/prompts/` or `.github/agents/`: *"Your project already has [N] prompt files and [N] agent files. Should I add the template's files alongside them, or do you want me to review each conflict individually?"*

7. **PRDs and ADRs** — *"Do you use PRDs and ADRs for planning? (Determines whether to include templates and the adr-prd-review skill)"*

8. **Hook safety** — *"The template includes safety hooks that block dangerous commands (rm -rf /, terraform destroy, force push to main). Do you want these enabled?"*

---

## Step 3 — Build Migration Plan

Based on Steps 1 and 2, produce a **Migration Plan** with four sections:

### ✅ Add (no conflict)
Files that don't exist in the target and will be copied as-is.
```
.github/agents/reader.agent.md          — add
.github/agents/writer.agent.md          — add
...
```

### 🔀 Merge (conflict detected)
Files that exist in both and need reconciliation. For each, state the strategy:
```
.github/copilot-instructions.md         — merge: append template rules below existing rules
```

### ⏭️ Skip (not needed for this project)
Files excluded based on user answers:
```
.github/agents/azure.agent.md           — skip (user not using Azure)
.github/prompts/azure-DEPLOY.prompt.md  — skip
.github/skills/azure/                   — skip
```

### 🗑️ Remove (user's existing file superseded or incompatible)
Only list this if there's a genuine conflict that can't be merged. Never remove without explicit user approval of each item.

---

## Step 4 — Gate on Plan

Present the full plan to the user:

*"Here is the migration plan. Review it carefully — I won't touch any files until you confirm. Anything to change?"*

Do not proceed until the user explicitly approves.

---

## Step 5 — Execute

Work through the plan section by section. For each file:

**Add** — Spawn **`writer` subagent** to copy the file content to the target path.

**Merge** — Spawn **`reader` subagent** to read both versions, then spawn **`writer` subagent** to produce the merged result. For `copilot-instructions.md` merges: keep the user's existing content first, append template content below a `---` separator with a comment marking its origin.

**Skip** — No action.

**Remove** — Ask the user individually for each item before removing: *"Ready to remove `<path>`? This cannot be undone."*

After each file, spawn **`reader` subagent** to verify the written file looks correct before moving to the next.

---

## Step 6 — Post-Migration Customization

After all files are in place, make targeted adjustments based on user answers:

**If Python venv = No** — Remove the venv check block from `session-start.sh` and `pre-tool-safety.sh` in the target.

**If Azure = No** — Remove the `az` auth check from `session-start.sh` and the `az group/resource delete` block from `pre-tool-safety.sh`.

**If Terraform = No** — Remove the Terraform version check from `session-start.sh` and the `terraform destroy` block from `pre-tool-safety.sh`.

**If Node.js = No** — Remove the Node.js check from `session-start.sh`.

**If safety hooks = No** — Remove `security.json` from `.github/hooks/` or comment out the deny/ask rules.

**If full workflow = No** — Remove `START.prompt.md`, `PLAN.prompt.md`, `BUILD.prompt.md`, `END.prompt.md`, and the `plans/` template references.

Spawn **`writer` subagent** for each targeted edit. Spawn **`reader` subagent** to verify each one.

---

## Step 7 — Validate & Commit

Spawn **`reader` subagent** to do a final validation sweep:
- All agent files have `user-invokable: false`
- All skill files have `description` as a single quoted line in frontmatter
- Hook scripts referenced in JSON configs exist at the expected paths
- No broken cross-references between files

Present a validation report. Fix any issues before committing.

Spawn **`github` subagent** to commit all changes:
```
chore(workflow): migrate ns-template workflow

- Added: <list>
- Merged: <list>
- Skipped: <list>
- Customized: <list>
```

**Gate:** *"Migration complete. Everything validated and committed. Anything to adjust?"*

---

## Rules

- Never copy files blindly — always read both sides before deciding on merge strategy
- Never remove files without individual user confirmation per file
- If a merge produces ambiguity, ask the user rather than guessing
- Hook scripts in `.github/hooks/scripts/` go into the target's same path — make them executable (`chmod +x`)
- Live session logs write to `.github/hooks/logs/` (session.log, tool-audit.log, subagent.log). After session end they are archived to `.github/hooks/logs/archive/<date>_<sessionId>/`. Do not confuse with the old `hooks/*.log` location.
- The `plans/` directory is not created — it's generated at runtime. Do not create it unless the user asks.
- After migration, the `plans/session-log.md` path in hooks must resolve relative to the **target** project root, not the template
