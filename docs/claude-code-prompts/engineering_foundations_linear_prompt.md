# Engineering Foundations — Claude Code prompt (create Linear tickets)

> Paste this whole file into Claude Code (it has the Linear MCP).
> It creates a structured backlog for turning a founder-built codebase into something a
> team can run. Written so you confirm a couple of choices, then it builds everything.

---

## What I want you to do

Use the **Linear MCP** to create an **"Engineering Foundations"** initiative: a project with
epics (parent issues) and child issues, so we have an actionable backlog for making this
codebase team-runnable (fast onboarding, safe-to-change, no single-person bottleneck).

## Before you create anything (confirm with me)

1. Call `list_teams` and show me the teams; **confirm which team** this goes in.
2. Ask me the **process posture** and tag every issue accordingly:
   - `lean` (move-fast startup — the default): automate gates instead of adding human approvals; lightweight written decisions instead of committees. Create all issues but mark heavyweight ones `posture:enterprise` and set them to a low priority / backlog.
   - `standard`
   - `enterprise` (formal reviews, sign-offs, compliance gates).
   Default to **lean** if I don't say.
3. Ask which **repo(s)** these apply to (so acceptance criteria can reference real paths).

## How to structure it

- Create a project: **"Engineering Foundations"** with a one-paragraph description
  (goal: from "everything routes through the founder" to "a team runs it like a machine").
- Create **one parent issue per epic** below, then the child issues under it.
- For **every child issue** write: a 1–3 sentence description, **acceptance criteria as a
  checklist**, an estimate, a priority (P0/P1/P2), and labels from:
  `dev-env`, `ci-cd`, `quality`, `testing`, `architecture`, `api`, `design-system`, `docs`,
  `observability`, `security`, `process`, `org`, plus the `posture:*` tag.
- Set priorities so the **P0 set forms a sensible first cycle** (call it "Foundations — Cycle 1"):
  the items that unblock onboarding and make main safe to merge into come first.
- If the Linear MCP is unavailable, output the entire project + epics + issues as a **markdown
  checklist** I can paste in manually.

---

## Epics and tickets to create

### Epic 1 — Developer environment & onboarding  *(mostly P0)*
- Commit a shared `.vscode/` to the repo: `settings.json` (format-on-save, default interpreter), `launch.json` (run/debug configs), `tasks.json` (db/migrate/seed tasks).
- Add `.vscode/extensions.json` with recommended extensions so VS Code prompts new devs to install them.
- Reproducible dev environment: a **devcontainer** (`.devcontainer/`) OR a documented Docker-based path so every machine is identical.
- One-command bootstrap script (`scripts/setup`) that installs deps, tools, and git hooks.
- Pin tool/runtime versions (e.g. `mise`/`asdf` `.tool-versions`, language version files, lockfiles committed).
- `CONTRIBUTING.md` + a **Day-1 onboarding checklist** (clone → run → first PR in under ~30 min).
- `CODEOWNERS` + an **ownership map** doc (who owns what area).
- Access-provisioning checklist (repos, cloud, secrets, third-party tools) for a new hire.
- `.env.example` committed + a documented local secrets/config flow (no secrets in the repo).

### Epic 2 — Source control & PR review  *(P0)*
- Decide and document the **branching strategy** (e.g. trunk-based / short-lived branches).
- Add a **PR template** (what/why, testing, risk, screenshots).
- Configure **branch protection** on main: required status checks, required approvals, no direct pushes, linear history.
- Define **PR review process**: who reviews, # of approvals, review SLA, and a reviewer checklist.
- Adopt a **commit convention** (e.g. Conventional Commits) and merge strategy (squash).

### Epic 3 — Code quality & standards  *(P0/P1)*
- Linting + formatting wired and enforced (auto-format on save via the committed settings).
- Type checking enforced.
- **Pre-commit hooks** (lint, format, typecheck) so issues are caught before CI.
- Dependency vulnerability scanning (Dependabot/Snyk) + basic SAST.
- A short **coding standards** doc per language.

### Epic 4 — Testing  *(P0/P1)*
- Document the **test strategy** (unit/integration/e2e split, what must be tested).
- Set a coverage target and a CI coverage gate.
- Test data/fixtures/factories pattern.
- (If AI/LLM in the product) an **eval/golden-test harness** run in CI.
- Flaky-test policy.

### Epic 5 — CI/CD, environments & release  *(P0/P1)*
- **CI pipeline**: lint + typecheck + tests on every PR (required check).
- **Staging + prod environments** with parity; document differences.
- **CD pipeline**: one-command (or automatic) deploy + a written **rollback runbook**.
- Infrastructure as Code for environments (Terraform or equivalent).
- Release/versioning/changelog process.
- **DB migration process** (review, zero-downtime expectations).
- Feature-flag mechanism for safe progressive rollout.

### Epic 6 — Architecture & technical decisions  *(P1)*
- Formalize the **ADR process**: template, `docs/adr/` index, when an ADR is required.
- **RFC / design-doc process** for significant changes (template + review path).
- **Define architecture ownership**: who owns architecture decisions and how they're reviewed.
- A **tech radar / approved-tech list** (what we use, what needs sign-off).
- A **tech-debt register** + a regular paydown cadence.

### Epic 7 — API design  *(P1)*
- An **API style guide**: REST conventions, resource naming, versioning, pagination, error format, auth/authz.
- **API design review** step before building a new endpoint/surface.
- **Contract-first workflow**: OpenAPI spec as source of truth + auto-generated docs.
- Backward-compatibility & deprecation policy.

### Epic 8 — UI & design system  *(P1, if there's a UI)*
- Establish the **single source of truth for UI**: design tokens (color/type/spacing) all components derive from.
- Stand up a **component library** (e.g. Storybook) with versioning and a consumption pattern.
- **Figma ↔ code handoff** process (how design and dev stay in sync).
- **Accessibility standards** (WCAG target) + a check in review.
- **Define design-system ownership** (who owns the system and approves changes).

### Epic 9 — Documentation  *(P1)*
- Decide where docs live and the documentation standards.
- Add "**docs updated**" to the Definition of Done.
- Keep **architecture docs** current (diagram set + system overview).
- **Runbooks** for operational tasks.
- Onboarding docs linked from `CONTRIBUTING.md`.

### Epic 10 — Observability & incident response  *(P1)*
- **Structured logging** standard (levels, correlation IDs, **PII redaction**).
- Metrics + dashboards for the key flows.
- Error tracking (e.g. Sentry) + alerting + an on-call expectation.
- Define **SLOs/SLIs** for critical paths.
- **Incident response process** + a **blameless postmortem** template.
- (If data-heavy) **data-quality monitoring**.

### Epic 11 — Security & compliance  *(P1/P2; raise if fintech/PII)*
- **Secrets management** (a vault/manager, not the repo).
- **RBAC / least-privilege** access model.
- **Audit logging** of sensitive actions.
- **PII / data-handling policy**.
- Dependency + container scanning in CI.
- A lightweight **security review** step for sensitive changes.
- Compliance roadmap (e.g. SOC 2) — `posture:enterprise` unless I say otherwise.

### Epic 12 — Delivery process & rituals  *(P1)*
- Standardize **Linear workflow states** + conventions + **Definition of Ready / Definition of Done**.
- Planning cadence (cycles) + estimation approach.
- Standups / async updates + retros.
- Roadmap & milestone tracking.
- Status-reporting format for stakeholders.

### Epic 13 — Team, roles & communication  *(P1/P2)*
- A **RACI / roles & responsibilities** doc (who's responsible for what).
- A **decision-making framework** (e.g. DACI/RAPID) — who decides what.
- On-call rotation.
- Communication norms (Slack/meetings/async expectations).
- Hiring/interview process + scorecards.
- Knowledge sharing (tech talks / brown bags).

---

## Kickoff

Confirm the team, posture, and repo(s) with me first. Then create the project, the 13 epics,
and their child issues with full descriptions + acceptance criteria, set priorities so the P0
items form "Foundations — Cycle 1," and finish by showing me a summary grouped by epic with
issue counts and the proposed Cycle 1.
