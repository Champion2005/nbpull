---
name: adr-prd-review
description: "Create and review Architecture Decision Records (ADRs) and Product Requirements Documents (PRDs) using strict repo templates. Use this skill whenever the user mentions ADR, PRD, architecture decision, product requirements, decision record, technical decision, design decision, requirements document, reviewing a PRD, writing an ADR, or any task involving creating, reviewing, or improving planning artifacts — even if they just say 'write up the decision' or 'document the requirements'."
---

# 📝 ADR & PRD — Create and Review

This skill guides creation and review of Architecture Decision Records and Product Requirements Documents using the repo's strict templates.

## 📌 Templates

Templates live in `.github/templates/`:
- **ADR:** `.github/templates/ADR-template.md`
- **PRD:** `.github/templates/PRD-template.md`

Always read the appropriate template before creating or reviewing a document. The templates define the required structure — do not deviate from them.

## 🆕 Creating an ADR

### When to Create

Create an ADR when the team makes (or needs to make) a significant technical decision:
- Technology or framework choices
- Architecture patterns (monolith vs. microservices, event-driven vs. request-response)
- Infrastructure decisions (cloud provider, region, deployment model)
- Security or compliance approaches
- Data storage or processing strategies
- Breaking changes to existing systems

### Workflow

1. **Read the template** — `cat .github/templates/ADR-template.md`
2. **Gather context** — Ask the user:
   - What decision needs to be made?
   - What options were considered?
   - What constraints exist? (timeline, budget, team skills, compliance)
   - Who are the stakeholders / deciders?
3. **Draft the ADR** using the template structure exactly
4. **Fill every section** — no placeholders, no "[TODO]" markers
5. **Verify quality** using the review checklist below
6. **Save** to `plans/ADR-NNN-<slug>.md` with the next available number

### ADR Writing Guidance

- **Context section** should be understandable by someone unfamiliar with the project — include enough background
- **Decision section** should be clear and unambiguous — a reader should know exactly what was decided
- **Rationale section** — explain why this option was chosen over alternatives. Name the alternatives explicitly
- **Consequences** — be honest about negatives. Every decision has trade-offs; pretending otherwise undermines trust
- **Mitigations** — for each negative consequence, describe how it will be managed

## 🆕 Creating a PRD

### When to Create

Create a PRD when starting a new feature, product, or significant change:
- New product or service
- Major feature additions
- Significant workflow changes
- Cross-team initiatives
- Anything that needs stakeholder alignment before building

### Workflow

1. **Read the template** — `cat .github/templates/PRD-template.md`
2. **Gather context** — Ask the user:
   - What is being built and why?
   - Who is the audience/user?
   - What does success look like? (measurable criteria)
   - What's explicitly out of scope?
   - What are the known risks and dependencies?
3. **Draft the PRD** using the template structure exactly
4. **Fill every section** — no placeholders, no "[TODO]" markers
5. **Verify quality** using the review checklist below
6. **Save** to `plans/<project-name>-PRD.md`

### PRD Writing Guidance

- **Executive Summary** — 2-3 paragraphs understandable by non-technical stakeholders
- **Scope** — explicitly listing "Out of Scope" prevents scope creep and misaligned expectations
- **Goals** — every goal must be measurable. "Improve performance" is not a goal; "Reduce API latency to < 200ms p95" is
- **Requirements** — use unique IDs (FR-1, NFR-1) so they can be referenced in issues and PRs
- **Success Criteria** — define how each metric will be measured, not just what the target is
- **Risks** — rate impact and likelihood honestly. Missing risks is worse than over-reporting them

## 🔍 Reviewing an ADR

When reviewing an existing ADR, evaluate against these criteria:

### Completeness Checklist

| Section | Check |
|---------|-------|
| Status | Is it set? (Proposed/Approved/Deprecated/Superseded) |
| Date | Present and formatted correctly? |
| Deciders | Named specifically (not just "the team")? |
| Context | Sufficient background for an outsider to understand? |
| Decision | Clear, unambiguous statement of what was decided? |
| Rationale | Alternatives named? Trade-offs explained? |
| Consequences ✅ | At least 2 positive consequences listed? |
| Consequences ⚠️ | At least 1 negative consequence listed? (every decision has trade-offs) |
| Mitigations | Every negative consequence has a mitigation strategy? |
| Related | Links to relevant ADRs, PRDs, issues? |

### Quality Checks

- **Clarity** — Could someone not on the team understand the decision and why it was made?
- **Specificity** — Does it name specific technologies, patterns, or approaches (not vague references)?
- **Honesty** — Are trade-offs acknowledged, not glossed over?
- **Completeness** — Are there obvious gaps or "[TODO]" placeholders?
- **Consistency** — Does it contradict other ADRs? (check `plans/ADR-*.md`)
- **Actionability** — Is the decision concrete enough to act on?

### Review Output Format

```markdown
## 📋 ADR Review: [Title]

### ✅ Strengths
- [What's done well]

### ⚠️ Issues Found
- **[Section]:** [Issue description] — Suggestion: [How to fix]

### 📊 Score: X/10
- Completeness: X/5
- Clarity: X/3
- Trade-off Analysis: X/2

### 💡 Recommendations
1. [Prioritized improvement]
```

## 🔍 Reviewing a PRD

When reviewing an existing PRD, evaluate against these criteria:

### Completeness Checklist

| Section | Check |
|---------|-------|
| Executive Summary | Understandable by non-technical stakeholders? |
| In Scope | Specific deliverables listed? |
| Out of Scope | Explicit exclusions? |
| Goals | Measurable (numbers, dates, thresholds)? |
| Personas | Real roles with described interactions? |
| Functional Reqs | Unique IDs? Testable statements? |
| Non-Functional Reqs | Performance, security, accessibility covered? |
| Success Criteria | Measurement method defined for each metric? |
| Risks | Impact rated? Mitigations for high-impact risks? |
| Dependencies | External dependencies identified? |

### Quality Checks

- **Measurability** — Can you write a test for each requirement? If not, it's too vague
- **Scope discipline** — Is the "Out of Scope" section substantive? A thin out-of-scope section often means scope will creep
- **Stakeholder coverage** — Are all affected teams represented in personas?
- **Risk honesty** — Are risks realistic? "No significant risks" is almost always wrong
- **Requirement uniqueness** — Are IDs unique and traceable?
- **Consistency** — Do success criteria align with stated goals?

### Review Output Format

```markdown
## 📋 PRD Review: [Project Name]

### ✅ Strengths
- [What's done well]

### ⚠️ Issues Found
- **[Section]:** [Issue description] — Suggestion: [How to fix]

### 📊 Score: X/10
- Completeness: X/4
- Measurability: X/3
- Risk Analysis: X/2
- Clarity: X/1

### 💡 Recommendations
1. [Prioritized improvement]
```

## 🛡️ Safety Rules

- **Never fabricate requirements** — if information is missing, ask the user rather than making it up
- **Never skip sections** — every template section must be addressed, even if the answer is "N/A — [reason]"
- **Never approve a document with placeholders** — "[TODO]", "[TBD]", "[Fill in]" are review failures
- **Preserve existing decisions** — when reviewing, suggest improvements but don't unilaterally change decisions
- **Flag conflicts** — if a new ADR contradicts an existing one, surface this explicitly
