# Repo evolution — Claude Code prompt (founder-built → team-runnable, via real git history)

> Paste this whole file into Claude Code. It builds a **real git repository** whose commit
> history tells the founder→team story: each stage is **tagged**, you can check out or diff any
> stage, and a script **materializes each stage into a snapshot folder** for side-by-side
> viewing. **The product is the history + the comparison narrative, not feature-complete code.**
> (This replaces the earlier folder-copy version.)

---

## Confirm with me first
1. **Output location** — default `~/Developer-local/repo-evolution/` (a *sibling* of `claim-pilot`, NOT inside it).
2. **App flavor** — a tiny generic service is fine; a small claims/recovery-flavored API is a nice touch for my audience. Keep it minimal either way.

## Hard scope rules (do NOT over-build)
- **ONE tiny constant feature across all stages** (e.g. a single resource with create + read, ~2 endpoints). Stages add **engineering foundation, not product features** — the feature never changes.
- Representative config / stubs / docs over volume of code. The whole thing should build quickly.
- The deliverables that matter most: the **commit history**, the **stage tags**, and **`COMPARISON.md`**. Spend the real effort there, not on app code.

## Build it as a real, intentional git history

1. **`git init`.** Build a minimal founder MVP and commit it as a few **deliberately founder-style commits** — terse/messy messages (`initial mvp`, `wip`, `quick fix`). One fat module; bare README; config/secrets inline. **No** tests, CI, `.vscode/`, ADRs, `CONTRIBUTING`, `CODEOWNERS`, linters. Add `NOTES.md` in an honest founder voice ("only I know how the deploy works"). Then **annotated tag `stage-1-founder`** with a message describing the stage.

2. **Layer up to hardening** as a series of **well-scoped Conventional Commits — one foundation per commit**, so the diff between tags is readable. For example:
   - `chore(dx): commit shared .vscode config (settings/launch/tasks/extensions)`
   - `build: add pre-commit hooks (lint, format, typecheck)`
   - `ci: add lint + typecheck + test workflow`
   - `test: add unit tests for <feature>`
   - `refactor: split the fat module into a sane structure`
   - `docs(adr): add first ADRs + index`
   - `docs: add CONTRIBUTING + PR template + branch-protection notes`
   - `chore: add .env.example + structured logging`
   Then **annotated tag `stage-2-hardening`**.

3. **Layer up to team** as more one-per-commit foundations:
   - `chore: add CODEOWNERS`
   - `chore(dx): add devcontainer + one-command bootstrap script`
   - `feat(api): add OpenAPI spec as source of truth + style guide + deprecation policy`
   - `feat(obs): add structured logging/metrics/error-tracking notes + dashboard stub`
   - `feat(sec): add secrets-manager note, RBAC, audit logging, PII handling`
   - `feat(ui): add design-system stub + design tokens` *(only if there's any UI)*
   - `docs: add architecture doc + runbook + onboarding checklist + issue/PR templates`
   Then **annotated tag `stage-3-team`**.

4. **Commit `COMPARISON.md` + a root `README.md` last on `main`.** These are meta-docs and intentionally are NOT in the stage tags.

5. **Add `scripts/snapshot.sh`** that materializes each tag into `snapshots/<tag>/` using **`git archive`** (non-destructive — never `reset --hard`), e.g. `git archive <tag> | tar -x -C snapshots/<tag>`. Run it so the three stage folders exist for side-by-side viewing.

**Commit discipline:** every commit builds; messages tell the story so `git log --oneline` reads as a clean founder→team arc (messy early, conventional later). Use **annotated** tags.

## Put these viewing commands in the README
- The story: `git log --oneline --decorate --tags`
- Foundations appearing as a diff: `git diff stage-1-founder stage-3-team --stat`
- View a stage live (non-destructive): `git checkout stage-1-founder` → `git checkout main` to return.
- Side-by-side folders: `snapshots/stage-1-founder/`, `snapshots/stage-2-hardening/`, `snapshots/stage-3-team/`.

## `COMPARISON.md` — the centerpiece (this is what gets presented)
- Short intro: the through-line is **from "routes through the founder" to "the team owns it."**
- A **capability × stage table** (✓ / –) covering at least: committed editor config, reproducible env, tests, CI/CD, pre-commit, ADRs, CONTRIBUTING/onboarding, CODEOWNERS, PR process / branch protection, API style guide + OpenAPI, observability, security/secrets/RBAC, docs/runbooks, design system.
- For **each capability, a one-line "founder bottleneck it removes"** — e.g. *committed `.vscode/` + bootstrap → a new hire is productive day one instead of pairing with the founder for a day*; *ADRs → the "why" leaves the founder's head*; *CI + tests → anyone can touch the money paths without the founder reviewing every line*.
- A 2–3 sentence narrative for each transition (stage 1→2, 2→3): what changed and why.
- The git commands above, so a reader can replay the evolution themselves.

## Build order
1. Confirm location + flavor with me.
2. Stage-1 commits → tag.
3. Stage-2 commits → tag.
4. Stage-3 commits → tag.
5. `COMPARISON.md` + `README.md` + `scripts/snapshot.sh`; run the snapshot script.
6. Show me `git log --oneline --decorate --tags`, the `git diff stage-1-founder stage-3-team --stat`, and the `snapshots/` tree.
