---
name: skill-finder
description: "Discover, search, and recommend Agent Skills from agentskills.io and the anthropics/skills GitHub repository. Use whenever a user asks what skills are available, wants to find a skill for a specific task, asks 'what can you do' or 'what tools do you have', wants to browse the skill catalog, or mentions installing/adding new capabilities. Also triggers when the user seems to need a capability that might exist as a skill — even if they don't explicitly ask for one."
license: Apache-2.0
metadata:
  author: ns-template-repo
  version: "1.1"
---

# 🔍 Skill Finder

A meta-skill for discovering and recommending Agent Skills.

## Purpose

Help users find the right skill for their task by searching the Agent Skills ecosystem.

## Skill Discovery Sources

1. **This repository** — check `.github/skills/` for locally installed skills
2. **anthropics/skills** — browse at https://github.com/anthropics/skills/tree/main/skills
3. **agentskills.io** — the official Agent Skills registry and specification at https://agentskills.io

## Workflow

### When user asks "what skills are available?"

1. List skills installed in this repo (`.github/skills/`)
2. Summarize what each skill does in one sentence
3. Mention that more skills are available at https://github.com/anthropics/skills

### When user asks for a skill for a specific task

1. Check locally installed skills first — recommend if a match exists
2. If no local match, search https://github.com/anthropics/skills/tree/main/skills
3. Present top 1–3 recommendations with:
   - Skill name
   - What it does
   - How to install (copy the skill folder into `.github/skills/`)

### When user wants to install a new skill

Provide these instructions:

```
1. Browse available skills at: https://github.com/anthropics/skills/tree/main/skills
2. Copy the skill's folder into .github/skills/ in your repo
3. The skill is now available to any compatible agent working in this repo
```

Or via Claude Code plugin marketplace:
```
/plugin marketplace add anthropics/skills
```

## 📦 Skills Available in This Repository

| Skill | Description |
|-------|-------------|
| `skill-finder` | 🔍 (this skill) Discover and recommend Agent Skills |
| `skill-creator` | 🛠️ Create new skills and iteratively improve existing ones |
| `doc-coauthoring` | 📝 Structured workflow for co-authoring documentation |
| `github` | 🐙 Git/GitHub ops — commits, PRs, issues, releases, health checks |
| `adr-prd-review` | 📋 Create and review ADRs and PRDs using strict templates |

## Notable Skills Not Yet Installed

Point users to these if relevant to their task:

- **xlsx** — Read/write Excel spreadsheets
- **pdf** — Extract text/tables from PDFs, fill forms
- **pptx** — Create and edit PowerPoint presentations
- **brand-guidelines** — Apply brand guidelines to content
- **internal-comms** — Write status reports, newsletters, incident reports
- **frontend-design** — Build polished frontend UI
- **algorithmic-art** — Generate SVG/canvas-based artwork
- **theme-factory** — Create color themes and design tokens
- **canvas-design** — Design layouts and visual compositions
- **slack-gif-creator** — Create animated GIFs for Slack
- **web-artifacts-builder** — Build interactive web artifacts

## Tips

- Skills follow the Agent Skills open format (https://agentskills.io/specification)
- A skill is just a folder with a `SKILL.md` file — easy to create and version control
- Use the `skill-creator` skill in this repo to build a custom skill
- Skills are agent-agnostic: the same skill works across Claude Code, Claude.ai, and the API
