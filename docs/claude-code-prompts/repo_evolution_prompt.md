# Repo evolution — Claude Code prompt (founder-built → team-runnable)

> Paste this whole file into Claude Code. It builds a **teaching artifact**: one small app
> shown at three maturity stages, side by side, so I can show how a repo evolves from
> founder-owned to team-owned. **The product is the contrast and the narrative, not
> feature-complete code.** Read the scope rules before building.

---

## Confirm with me first
1. **Output location** — default `~/Developer-local/repo-evolution/` (a *sibling* of `Claimio-Pilot`, NOT inside it). Confirm or change.
2. **App flavor** — a tiny generic service is fine; a small claims/recovery-flavored API is a nice touch for my audience. Keep it minimal either way.
3. **Layout** —
   - **(A)** three sibling folders `stage-1-founder/`, `stage-2-hardening/`, `stage-3-team/` (easiest to show side by side). **Default.**
   - **(B)** one git repo with tags `stage-1` / `stage-2` / `stage-3`, so `git diff stage-1 stage-3` literally shows the foundations appear.
   - Build A unless I ask for B (or both).

## Hard scope rules (do NOT over-build)
- **Same tiny feature in all three stages.** Pick ONE small capability (e.g. a single resource with create + read, ~2 endpoints). Do **not** add product features across stages — the feature is constant; only the *engineering foundation around it* changes.
- Every stage runnable but minimal. No real integrations. Favor representative config + stubs + docs over volume of code. The whole thing should build quickly.
- **`COMPARISON.md` at the root is the centerpiece.** Spend the real effort there, not on app code.

## The three stages (what differs is the foundation, not the feature)

**`stage-1-founder/` — it works, but everything is in the founder's head.**
- One fat module; bare `README`; config/secrets inline or ad-hoc (a hardcoded value + a comment).
- No tests (or one trivial). No `.vscode/`. No CI. No ADRs. No `CONTRIBUTING`. No `CODEOWNERS`. No linter/formatter config.
- Add a `NOTES.md` in an honest founder voice (TODOs, "only I know how the deploy works," "need to clean this up") so the bottleneck is visible on the page.

**`stage-2-hardening/` — first hires; making it safe to change.**
- Module split into a sane structure; `.env.example`; **committed `.vscode/`** (`settings.json`, `launch.json`, `tasks.json`, `extensions.json`).
- Tests + a **CI workflow** (lint + typecheck + test); pre-commit hooks; structured logging.
- First **ADRs** (`docs/adr/`) + index; `CONTRIBUTING.md`; a **PR template**; branch-protection notes in the README.

**`stage-3-team/` — team-runnable at scale.**
- **Devcontainer** + one-command bootstrap; **`CODEOWNERS`**; full ADR set + an RFC/design-doc template.
- **API style guide** + an **OpenAPI spec as source of truth** + auto-generated docs + a deprecation-policy note.
- **Observability** (logging/metrics/error-tracking notes + a dashboard stub); **security posture** (secrets-manager note, RBAC, audit logging, PII handling).
- **Docs structure** (architecture doc + a runbook + an onboarding checklist); issue + PR templates; a **design-system stub + tokens** if there's any UI.

## `COMPARISON.md` — the thing that gets presented
- Short intro: the through-line is **from "routes through the founder" to "the team owns it."**
- A **capability × stage table** (✓ / –) covering at least: committed editor config, reproducible env, tests, CI/CD, pre-commit, ADRs, CONTRIBUTING/onboarding, CODEOWNERS, PR process / branch protection, API style guide + OpenAPI, observability, security/secrets/RBAC, docs/runbooks, design system.
- For **each capability, a one-line "founder bottleneck it removes"** — e.g. *committed `.vscode/` + bootstrap → a new hire is productive on day one instead of pairing with the founder for a day*; *ADRs → the "why" leaves the founder's head*; *CI + tests → anyone can change the money paths without the founder reviewing every line*.
- A 2–3 sentence narrative for each transition (stage 1→2, 2→3): what changed and why.
- If layout B: include the exact `git diff stage-1 stage-3` command so the foundations show up as a diff.

## Build order
1. Confirm location / flavor / layout with me.
2. Build `stage-1-founder/` (minimal).
3. **Copy it forward** and layer up to `stage-2`, then `stage-3`, so the progression is real (not three unrelated trees).
4. Write `COMPARISON.md` and a root `README.md` explaining how to view the artifact (open the three trees side by side, or the git-diff command).
5. Show me the three directory trees side by side + the comparison table.
