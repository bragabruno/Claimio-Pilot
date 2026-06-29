# Engineering operating model — the full map

The complete list of what makes an engineering org run like a machine, organized by domain.
Use it as the presentation skeleton. The through-line is the founder-to-team transition:
**from "everything routes through one person" to "a team can run it with order, safety, and speed."**

Each domain lists the **items/decisions**, who **owns** it where that's the real question, and a
one-line **startup-lean ↔ enterprise** contrast.

---

## The cross-cutting lens: enterprise vs move-fast startup

Same goals at both ends (legibility, safety, speed); different *mechanisms*.

- **Enterprise** reaches for **human gates**: review boards, sign-offs, change-advisory boards, formal RFCs, segregation of duties, audit trails, compliance controls. Optimizes for control and risk reduction at the cost of speed.
- **Startup** reaches for **automated gates**: CI checks, tests, linters, branch protection, lightweight written decisions. Optimizes for speed while keeping a safety floor.
- **The startup principle to state out loud:** install the **minimum viable process** that buys you safety and legibility — *automate a gate before you add an approval; write a one-page decision before you convene a committee.* Process should remove the founder as a bottleneck, not add a new one.

Every domain below can be dialed from lean to heavy. The skill is choosing the right notch for the stage.

---

## 1. Developer environment & onboarding
*Goal: a newcomer is productive on day one; every machine is identical.*
- Shared, **committed** editor config (`.vscode/`: `settings.json`, `launch.json`, `tasks.json`, `extensions.json`) so tooling ships with the repo.
- Reproducible environment: **devcontainer** or documented containerized setup.
- One-command **bootstrap script**; pinned tool/runtime versions; committed lockfiles.
- `CONTRIBUTING.md` + a **Day-1 checklist** (clone → run → first PR fast).
- **Ownership map** + access-provisioning checklist (repos, cloud, secrets, tools).
- Local secrets/config flow (`.env.example`, nothing secret in the repo).
- *Lean:* devcontainer + script + checklist. *Enterprise:* managed images, golden laptops, IT-provisioned access workflows.

## 2. Source control & PR review
*Goal: many people change the same code without stepping on each other.*
- **Branching strategy** (trunk-based / short-lived branches), commit convention, merge strategy.
- **PR template**, **branch protection** (required checks + approvals, no direct push to main, linear history).
- **PR review process**: who reviews, # approvals, **review SLA**, reviewer checklist.
- `CODEOWNERS` to route reviews to the right owners automatically.
- *Lean:* 1 approval + green CI, squash-merge. *Enterprise:* multiple approvals, security/QA sign-off, segregation of duties.

## 3. Code quality & standards
*Goal: consistency and safety enforced by tools, not vibes.*
- Linting + **format-on-save** + type checking, all enforced.
- **Pre-commit hooks** so problems die before CI.
- Coding standards doc per language; dependency vulnerability scanning + SAST.
- *Lean:* automated linters/formatters as the standard. *Enterprise:* mandated style guides, quality gates, periodic audits.

## 4. Testing
*Goal: anyone can change the code — including the money paths — without fear.*
- Documented **test strategy** (unit/integration/e2e split; what *must* be covered).
- Coverage target + CI gate; fixtures/factories; flaky-test policy.
- For AI/LLM features: **eval / golden-test harness** in CI (catch regressions in non-deterministic output).
- *Lean:* strong unit + a few integration tests on critical flows. *Enterprise:* formal test plans, QA function, UAT, contract testing.

## 5. CI/CD, environments & release
*Goal: shipping isn't a ritual only one person can perform.*
- **CI** (lint/typecheck/test on every PR) + **CD** (one-command or automatic deploy).
- **Staging + prod** with parity; Infrastructure as Code.
- **Rollback runbook**, feature flags, release/versioning/changelog, DB-migration process (zero-downtime).
- *Lean:* continuous deploy behind flags + fast rollback. *Enterprise:* release trains, change-advisory board, scheduled windows, approvals.

## 6. Architecture & technical decisions  — *ownership question*
*Goal: significant decisions are deliberate, recorded, and not bottlenecked on one head.*
- **Who owns architecture** — the explicit question. Patterns: a single architect / staff engineer; a small architecture group; or "owner of the affected area decides, reviewed by peers." Pick and document it.
- **ADR process** (decisions written down — the "why" leaves the founder's head) + an index.
- **RFC / design-doc process** for big changes; **tech radar / approved-tech list**; **tech-debt register** + paydown cadence.
- *Lean:* lightweight ADRs + peer review; a tech lead owns calls. *Enterprise:* architecture review board, formal RFC sign-off, standards bodies.

## 7. API design  — *how APIs get designed*
*Goal: APIs are consistent, documented, and safe to evolve.*
- **API style guide**: REST conventions, resource naming, **versioning**, pagination, error format, auth/authz.
- **Contract-first** workflow: an **OpenAPI spec as the source of truth**, auto-generated docs.
- An **API design-review** step before building a surface; backward-compat & **deprecation policy**.
- Internal vs public/partner API governance (public surfaces get stricter rules).
- *Lean:* a style guide + spec + a quick design check. *Enterprise:* API governance board, formal versioning/deprecation contracts, partner SLAs.

## 8. UI & design system  — *ownership + single source of truth*
*Goal: all UI derives from one consistent system, not ad-hoc screens.*
- **Who owns the design system** — the explicit question (design + frontend, jointly or a named owner).
- **Single source of truth**: **design tokens** (color, type, spacing) that every component derives from.
- **Component library** (e.g. Storybook) with versioning + a consumption pattern; **Figma ↔ code handoff** process.
- **Accessibility** standards (WCAG) checked in review; visual/brand consistency governance.
- *Lean:* a token set + shared component library + Storybook. *Enterprise:* a dedicated design-systems team, formal contribution model, multi-brand theming.

## 9. Documentation
*Goal: knowledge lives in the repo/wiki, not in one person's memory.*
- Where docs live + documentation standards; "**docs updated**" in the Definition of Done.
- Current **architecture docs**, **runbooks**, **API docs**, **ADR index**, onboarding docs, changelog.
- *Lean:* docs-as-code in the repo, kept current as part of the work. *Enterprise:* managed knowledge base, doc owners, review/approval of docs.

## 10. Observability & incident response
*Goal: when something breaks, anyone can see where — not just the founder.*
- **Structured logging** (levels, correlation IDs, **PII redaction**); metrics + dashboards; error tracking.
- Alerting + **on-call**; **SLOs/SLIs** for critical paths.
- **Incident-response process** + **blameless postmortems**; data-quality monitoring for data-heavy systems.
- *Lean:* logging + error tracking + a simple on-call + postmortem template. *Enterprise:* full SRE practice, error budgets, formal incident command, status pages.

## 11. Security & compliance
*Goal: a safety and trust floor — non-negotiable for fintech / PII.*
- **Secrets management** (vault), **RBAC / least privilege**, **audit logging**, **PII/data-handling policy**.
- Dependency + container scanning; a security-review step for sensitive changes; threat modeling.
- Compliance posture (SOC 2, etc.) sized to the stage and customers.
- *Lean:* secrets manager + least privilege + scanning + audit trails. *Enterprise:* security team, formal compliance program, pen tests, vendor risk reviews.

## 12. Data & ML / AI  *(if relevant to the product)*
*Goal: data and models are trustworthy and reproducible.*
- Data pipeline standards; **data quality / validation**; data governance & privacy.
- For ML/LLM: **eval harnesses**, prompt/model **versioning**, reproducibility, cost/latency tracking, human-in-the-loop guardrails.
- *Lean:* validation + evals + versioned prompts. *Enterprise:* data platform team, model governance, lineage, model-risk management.

## 13. Delivery process & rituals  — *project management*
*Goal: predictable flow of work; everyone knows what's happening.*
- Issue tracking with clear **workflow states** + conventions; **Definition of Ready / Definition of Done**.
- Planning cadence (cycles/sprints), estimation, backlog grooming, prioritization.
- Standups / async updates, retros, roadmap & milestone tracking, stakeholder status reporting.
- *Lean:* short cycles, a tidy board, lightweight planning. *Enterprise:* formal Agile/Scrum or SAFe, PMO, detailed reporting.

## 14. Team, roles, ownership & communication  — *the org layer*
*Goal: clear ownership and decision rights so nothing routes through one person by default.*
- **RACI / roles & responsibilities**; a **decision-making framework** (DACI/RAPID — who decides what).
- Code & area **ownership map**; on-call rotation.
- Communication norms (Slack/meetings/async); hiring & interview process + scorecards; knowledge sharing (tech talks).
- Career ladders / growth expectations (as the team grows).
- *Lean:* a clear owner per area + a simple decision model. *Enterprise:* org charts, formal RACI, governance committees, leveling frameworks.

---

## How to use this in the room
- It maps 1:1 to the pain the founder named: each domain converts something that "routes through them" into something **the team owns**.
- Lead with the **lean** column — you're advising a startup, so the headline is *minimum viable process, automated gates over approvals*, not enterprise bureaucracy.
- The **ownership questions** (architecture · API design · design system) are the ones to ask, not answer, on a first pass — they reveal how decisions get made today.
