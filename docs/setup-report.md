# VinoGuessr foundation setup report

This report records the move to the same structure as [sauna-studio](https://github.com/sauna-studio/.github). Only finished items are listed as done; anything not yet run or verified is listed under open items.

## Decisions

- Repositories: add `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` to `vinoguessr-api` / `vinoguessr-app` / `vinoguessr-web`
- Agents: Codex by default; a Claude Code review substitutes only when Codex cannot review because of its usage limit
- Web: keep the Swift / Hummingbird stack
- Google Cloud: bootstrap the new project `vinoguessr` through Issues and PRs after this foundation and the infrastructure repository are in place
- Language: code, documentation, commit messages, labels, and PR titles in English; Issue and PR bodies in Japanese. Squash merges use the PR title as the commit subject and the commit messages as the body, so Japanese PR bodies never land in the history

## Differences from sauna-studio

- `vinoguessr-api` already has its own CI (`ci.yml`), so the shared repository policy check is called from `.github/workflows/repository.yml` in every repository, and the api keeps its own `lint` / `test` / `docker-build` jobs as required checks
- `vinoguessr-web` replaces its old `ci.yml` with a `swift` job in `repository.yml` that calls `reusable-swift.yml`
- ADRs live only in `vinoguessr-docs` and are not duplicated in `.github`
- `CLAUDE.md` and `.claude/agents/` are placed in every repository for Claude Code reviews
- Shared files reach existing repositories through [bootstrap/sync_foundation.py](../bootstrap/sync_foundation.py), which keeps existing content instead of requiring empty repositories
- No admin app, admin web, or automation repositories

## Done (2026-11-08)

- Created `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` as public repositories
- Merged the shared foundation: [.github#1](https://github.com/vinoguessr/.github/pull/1) at `01fd9c61bce2139beb8ea173339d45c02d49b69f`, the SHA every repository calls reusable workflows at
- Merged the distribution PRs, each with GitHub Codex review, an independent Claude Code review, and passing required CI:
  - [vinoguessr-docs#1](https://github.com/vinoguessr/vinoguessr-docs/pull/1): foundation, ADR-0001 to ADR-0004, wiki source
  - [vinoguessr-infrastructure#1](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/1): foundation, Terraform moved from the api, runbook for a new project
  - [vinoguessr-app#8](https://github.com/vinoguessr/vinoguessr-app/pull/8): foundation, SwiftUI policy, first CI
  - [vinoguessr-web#1](https://github.com/vinoguessr/vinoguessr-web/pull/1): foundation, shared Swift CI
  - [vinoguessr-api#406](https://github.com/vinoguessr/vinoguessr-api/pull/406): foundation, existing workflows pinned to commit SHAs
- `bootstrap/provision.py` (results in [provisioning-results.json](provisioning-results.json)):
  - `project`: [VinoGuessr Project](https://github.com/orgs/vinoguessr/projects/1) with Priority, Phase, and Area fields, linked to all six repositories
  - `views`: Backlog, Development board, Roadmap, By repository, Blocked, Release readiness
  - `items`: all open Issues added with Area set (33 existing Issues and 4 tracking Issues)
  - `settings`: squash merge only (PR title and commit messages), branch deletion on merge, secret scanning and push protection, Dependabot alerts and security updates, private vulnerability reporting, empty development / staging / production Environments, `type:task` / `type:bug` / `release` labels
  - `rulesets` (owner-approved): `Main PR and verified CI` on `main` of all six repositories (PR required, required checks up to date and passing, threads resolved, no force pushes or deletion, squash only, no bypass). The required checks had all run on main or a merged PR first. vinoguessr-api's older `main` ruleset was deleted, since the new ruleset already requires its `lint` / `test` / `docker-build`, and its `terraform` requirement would have blocked vinoguessr-api#407
- Tracking Issues for follow-up work (Phase Foundation):
  - [vinoguessr-infrastructure#2](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/2) Bootstrap the Google Cloud project vinoguessr (P0, closed 2026-11-09)
  - [vinoguessr-api#407](https://github.com/vinoguessr/vinoguessr-api/issues/407) Remove Terraform after the move to vinoguessr-infrastructure (P1, closed 2026-11-08)
  - [vinoguessr-app#9](https://github.com/vinoguessr/vinoguessr-app/issues/9) Build and test VinoGuessrKit and the app in CI (P1)
  - [.github#2](https://github.com/vinoguessr/.github/issues/2) Enforce workflow hardening in every repository (P1)
- The rename PRs [vinoguessr-api#405](https://github.com/vinoguessr/vinoguessr-api/pull/405) and [vinoguessr-app#7](https://github.com/vinoguessr/vinoguessr-app/pull/7) are merged
- The six workflows the Project API reports have been enabled since the Project was created (GitHub defaults): Auto-add sub-issues to project, Auto-close issue, Item added to project, Item closed, Pull request linked to issue, Pull request merged

## Done (2026-11-09)

- Built the Google Cloud project `vinoguessr` with the vinoguessr-infrastructure runbook ([vinoguessr-infrastructure#2](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/2)):
  - `api.vinoguessr.com` and the passkey association file on `vinoguessr.com` are served through Cloudflare, the external HTTPS load balancer, and Cloud Run; direct `*.run.app` access is rejected
  - The vinoguessr-api Deploy workflow succeeded end to end against the new project
  - Mail from `support@vinoguessr.com` passes SPF, DKIM, and DMARC through Cloudflare Email Service
- Retired BlindLog: requested deletion of the old Google Cloud project `blindlog` (restorable until about 2026-12-09), deleted the old Neon database, removed every `blindlog.me` service and mail record including `api.blindlog.me` (only SPF `v=spf1 -all` and DMARC `p=reject` remain against spoofing), and turned off auto-renewal of `blindlog.me` (it lapses on 2027-08-04)

## Open items

- Open PRs created before the foundation (Dependabot and older feature PRs) never report the new required checks until they are updated with main; rebase them (for Dependabot, comment `@dependabot rebase`)
- The "By repository" view has no grouping yet; the REST API creates views without grouping, so set "Group by: Repository" in the Project UI
- The Project still has the default "View 1" next to the provisioned views
- The Project workflows "Auto-add to project" and "Auto-archive items" are not configured, and the Issue Forms do not set `projects`, so new top-level Issues and PRs join the Project only when added by hand; only sub-issues of Project items are added automatically
- The GitHub wiki of `vinoguessr-docs` has not been initialized or synced from `docs/wiki`
- No website is served: `blindlog-web` went away with the old project, and `vinoguessr.com` serves only the passkey association file until vinoguessr-web is deployed there ([vinoguessr-infrastructure#8](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/8))
- Cloud Run resolves the app secrets at `latest` when each instance starts, so a new secret version mixes old and new values within one revision, and rolling back a revision does not restore the old value ([vinoguessr-infrastructure#6](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/6))
- The shared repository policy check now rejects workflows with actions not pinned to a full commit SHA, missing or writable top-level `permissions`, `read-all` / `write-all` shorthands, `actions/checkout` without `persist-credentials: false`, or `pull_request_target`, but the other five repositories still call it at `01fd9c61bce2139beb8ea173339d45c02d49b69f`; bump each `repository.yml` to a main commit that contains the check ([.github#2](https://github.com/vinoguessr/.github/issues/2))
