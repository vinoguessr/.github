# VinoGuessr foundation setup report

This report records the move to the same structure as [sauna-studio](https://github.com/sauna-studio/.github). Only finished items are listed as done; anything not yet run or verified is listed under open items.

## Decisions

- Repositories: add `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` to `vinoguessr-api` / `vinoguessr-app` / `vinoguessr-web`
- Agents: Codex by default; a Claude Code review substitutes only when Codex cannot review because of its usage limit
- Web: keep the Swift / Hummingbird stack
- Google Cloud: bootstrap the new project `vinoguessr` through Issues and PRs after this foundation and the infrastructure repository are in place
- Language: code, documentation, commit messages, labels, and PR titles in English; Issue and PR bodies in Japanese. Squash merges use the PR title as the commit subject and the commit messages as the body, so Japanese PR bodies never land in the history
- App platforms (2026-11-09): iOS and iPadOS 27.0 or later only; macOS and visionOS are deferred ([ADR-0006](https://github.com/vinoguessr/vinoguessr-docs/blob/main/docs/adr/0006-app-platforms.md))
- Production deploys (2026-11-09): vinoguessr-api and vinoguessr-web keep deploying automatically while there are no users; the owner approval gate is tracked in [.github#6](https://github.com/vinoguessr/.github/issues/6)

## Differences from sauna-studio

- `vinoguessr-api` already has its own CI (`ci.yml`), so the shared repository policy check is called from `.github/workflows/repository.yml` in every repository, and the api keeps its own `lint` / `test` / `docker-build` jobs as required checks
- `vinoguessr-web` replaces its old `ci.yml` with a `swift` job in `repository.yml` that calls `reusable-swift.yml`
- ADRs live only in `vinoguessr-docs` and are not duplicated in `.github`
- `CLAUDE.md` and `.claude/agents/` are placed in every repository for Claude Code reviews
- Shared files reach existing repositories through [bootstrap/sync_foundation.py](../bootstrap/sync_foundation.py), which keeps existing content instead of requiring empty repositories
- No admin app, admin web, or automation repositories

## Done (2026-11-08)

- Created `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` as public repositories
- Merged the shared foundation: [.github#1](https://github.com/vinoguessr/.github/pull/1) at `01fd9c61bce2139beb8ea173339d45c02d49b69f`, the SHA every repository first called reusable workflows at (bumped to `38adaa6` on 2026-11-09)
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
  - [vinoguessr-app#9](https://github.com/vinoguessr/vinoguessr-app/issues/9) Build and test VinoGuessrKit and the app in CI (P1, closed 2026-11-09)
  - [.github#2](https://github.com/vinoguessr/.github/issues/2) Enforce workflow hardening in every repository (P1, closed 2026-11-09)
- The rename PRs [vinoguessr-api#405](https://github.com/vinoguessr/vinoguessr-api/pull/405) and [vinoguessr-app#7](https://github.com/vinoguessr/vinoguessr-app/pull/7) are merged
- The six workflows the Project API reported on 2026-11-08 have been enabled since the Project was created (GitHub defaults): Auto-add sub-issues to project, Auto-close issue, Item added to project, Item closed, Pull request linked to issue, Pull request merged

## Done (2026-11-09)

- Built the Google Cloud project `vinoguessr` with the vinoguessr-infrastructure runbook ([vinoguessr-infrastructure#2](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/2)):
  - `api.vinoguessr.com` and the passkey association file on `vinoguessr.com` are served through Cloudflare, the external HTTPS load balancer, and Cloud Run; direct `*.run.app` access is rejected
  - The vinoguessr-api Deploy workflow succeeded end to end against the new project
  - Mail from `support@vinoguessr.com` passes SPF, DKIM, and DMARC through Cloudflare Email Service
- Retired BlindLog: requested deletion of the old Google Cloud project `blindlog` (restorable until about 2026-12-09), deleted the old Neon database, removed every `blindlog.me` service and mail record including `api.blindlog.me` (only SPF `v=spf1 -all` and DMARC `p=reject` remain against spoofing), and turned off auto-renewal of `blindlog.me` (it lapses on 2027-08-04)
- Served vinoguessr-web on `vinoguessr.com` from Cloud Run in the `vinoguessr` project ([vinoguessr-infrastructure#9](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/9), deployed by the Deploy workflow from [vinoguessr-web#7](https://github.com/vinoguessr/vinoguessr-web/pull/7)); `/.well-known/apple-app-site-association` stays routed to the API, as [vinoguessr-infrastructure#8](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/8) requires
- Pinned the Cloud Run app secrets to version numbers instead of `latest` ([vinoguessr-infrastructure#10](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/10), closing [vinoguessr-infrastructure#6](https://github.com/vinoguessr/vinoguessr-infrastructure/issues/6))
- vinoguessr-api serves the passkey playground only in local development ([vinoguessr-api#411](https://github.com/vinoguessr/vinoguessr-api/pull/411), closing [vinoguessr-api#409](https://github.com/vinoguessr/vinoguessr-api/issues/409))
- Workflow hardening ([.github#2](https://github.com/vinoguessr/.github/issues/2), closed):
  - vinoguessr-api's existing workflows got least-privilege `permissions` and `persist-credentials: false` ([vinoguessr-api#413](https://github.com/vinoguessr/vinoguessr-api/pull/413))
  - The shared repository policy check rejects workflows with actions not pinned to a full commit SHA, missing or writable top-level `permissions`, `read-all` / `write-all` shorthands, `actions/checkout` without `persist-credentials: false`, or `pull_request_target` ([.github#5](https://github.com/vinoguessr/.github/pull/5), merged as `38adaa6`)
  - All five other repositories call the shared workflows at `38adaa6afdfb7df020feb2a7ff93a6ddf1d79af8` and pass the new check: [vinoguessr-api#416](https://github.com/vinoguessr/vinoguessr-api/pull/416), [vinoguessr-app#22](https://github.com/vinoguessr/vinoguessr-app/pull/22), [vinoguessr-web#8](https://github.com/vinoguessr/vinoguessr-web/pull/8), [vinoguessr-docs#5](https://github.com/vinoguessr/vinoguessr-docs/pull/5), [vinoguessr-infrastructure#12](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/12)
- Narrowed the app to iOS and iPadOS ([ADR-0006](https://github.com/vinoguessr/vinoguessr-docs/blob/main/docs/adr/0006-app-platforms.md) in [vinoguessr-docs#3](https://github.com/vinoguessr/vinoguessr-docs/pull/3), targets in [vinoguessr-app#20](https://github.com/vinoguessr/vinoguessr-app/pull/20))
- App CI ([vinoguessr-app#21](https://github.com/vinoguessr/vinoguessr-app/pull/21)) builds the app and tests VinoGuessrKit on the iOS Simulator; its `Build VinoGuessr (iOS Simulator)` and `Test VinoGuessrKit (iOS Simulator)` jobs are required checks in vinoguessr-app's `Main PR and verified CI` ruleset
- Project (by the owner): enabled the "Auto-add to project" workflow and deleted the default "View 1"

## Open items

- Open PRs created before the foundation (currently [vinoguessr-api#236](https://github.com/vinoguessr/vinoguessr-api/pull/236), [#271](https://github.com/vinoguessr/vinoguessr-api/pull/271), and [#329](https://github.com/vinoguessr/vinoguessr-api/pull/329)) never report the new required checks until they are updated with main; rebase them
- The Repository CI run on vinoguessr-infrastructure main after vinoguessr-infrastructure#12 (`4c536ca`) failed the required `terraform / Terraform format and validate` check, because `terraform init` got a 504 from github.com while downloading the Cloudflare provider; re-run it (the PR's run passed)
- The "By repository" view has no grouping yet; the REST API creates views without grouping, so set "Group by: Repository" in the Project UI
- On GitHub Free a Project has one auto-add workflow, which watches a single repository, and the API does not show which repository or filter it uses. No PR opened since it was enabled has joined the Project, so add PRs, and Issues in the other repositories, by hand. The Issue Forms do not set `projects`, and "Auto-archive items" is not configured
- The GitHub wiki of `vinoguessr-docs` has not been initialized or synced from `docs/wiki`
- Production deploys of vinoguessr-api and vinoguessr-web run without owner approval, by the owner's decision while there are no users ([.github#6](https://github.com/vinoguessr/.github/issues/6))
- The shared rules and `bootstrap/sync_foundation.py` still describe the app as iOS, iPadOS, and macOS, and the sync script still verifies it with `swift test`, so a sync would revert the README and AGENTS.md text from vinoguessr-app#20 and #21 ([.github#7](https://github.com/vinoguessr/.github/issues/7), in review in [.github#9](https://github.com/vinoguessr/.github/pull/9))
- The shared repository policy check does not yet reject non-canonical action references ([.github#8](https://github.com/vinoguessr/.github/issues/8), in review in [.github#10](https://github.com/vinoguessr/.github/pull/10))
- After .github#7 and #8 merge, every repository needs another sync to the new `.github` main commit
- [vinoguessr-api#414](https://github.com/vinoguessr/vinoguessr-api/issues/414): run Deploy migrations with the `POSTGRES_PASSWORD` version Cloud Run pins
- [vinoguessr-api#415](https://github.com/vinoguessr/vinoguessr-api/issues/415): pin the Atlas installer in the Deploy workflow
- [vinoguessr-app#19](https://github.com/vinoguessr/vinoguessr-app/issues/19): pin package versions for the app build
- [vinoguessr-docs#4](https://github.com/vinoguessr/vinoguessr-docs/issues/4): update ADR-0005 now that the passkey playground is local-only
