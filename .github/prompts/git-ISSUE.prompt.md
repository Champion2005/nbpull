---
description: "Create, view, or triage GitHub issues. Supports bulk triage and linking issues to branches or PRs."
argument-hint: "Issue title, number to view, or 'triage' to review open issues"
tools: [execute, agent, vscode/askQuestions]
model: Claude Sonnet 4.6 (copilot)
---

# 🐛 ISSUE

Spawn **`github` subagent** based on the request:

## Create an issue

Gather from the user if not provided:
- Title (one line, imperative)
- Type: bug / feature / chore / question
- Description: what, expected behaviour, actual behaviour (for bugs); goal and context (for features)
- Labels and assignee if known

Create with `gh issue create`. Return the issue URL and number.

## View / comment on an issue

```bash
gh issue view <number>
gh issue comment <number> --body "<text>"
```

## Triage open issues

List open issues: `gh issue list --state open --limit 50`

Group by type/label and present a summary. For each uncategorised issue, suggest:
- Label to apply
- Priority (blocking / high / normal / low)
- Whether it maps to an existing plan artifact in `plans/`

**Gate:** *"Does this triage look right? I'll apply labels and assignments after your confirmation."*

## Link issue to current work

Close or reference an issue in a commit message:
- `fix(<scope>): <message> (closes #<N>)` — closes on merge
- `ref #<N>` — links without closing
