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
  - `settings`: squash merge only (PR title and commit messages), branch deletion on merge, secret scanning and push protection, Dependabot alerts and security updates, private vulnerability reporting, empty development / staging / production Environments, `type:task` / `type:bug` labels
- Tracking Issues for follow-up work (Phase Foundation):
  - [vinoguessr-infrastructure#2](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/2) Bootstrap the Google Cloud project vinoguessr (P0)
  - [vinoguessr-api#407](https://github.com/vinoguessr/vinoguessr-api/issues/407) Remove Terraform after the move to vinoguessr-infrastructure (P1)
  - [vinoguessr-app#9](https://github.com/vinoguessr/vinoguessr-app/issues/9) Build and test VinoGuessrKit and the app in CI (P1)
  - [.github#2](https://github.com/vinoguessr/.github/issues/2) Enforce workflow hardening in every repository (P1)

## Open items

- `--stage rulesets` has not been run; it needs the owner's approval. `vinoguessr-api` already has a ruleset named `main` (PR, squash only, required `test` / `lint` / `docker-build` / `terraform`); applying the new ruleset should replace it rather than stack on top of it, and `terraform` must leave the required checks before vinoguessr-api#407 removes that job
- Project workflows such as "Auto-add sub-issues to project" are set in the Project settings UI; they are not configured yet
- The GitHub wiki of `vinoguessr-docs` has not been initialized or synced from `docs/wiki`
- vinoguessr-api#405 and vinoguessr-app#7 (the BlindLog to VinoGuessr rename) are still open
- The Google Cloud project `vinoguessr` is not built yet (vinoguessr-infrastructure#2). The api Deploy workflow has failed since the repository transfer, because the old project's Workload Identity Federation only trusts `zunda-pixel/blindlog-api`
- The shared repository policy check does not yet enforce workflow hardening in downstream repositories (.github#2)
