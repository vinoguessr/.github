# VinoGuessr foundation setup report

This report records the move to the same structure as [sauna-studio](https://github.com/sauna-studio/.github). Only finished items are listed as done; anything not yet run or verified is listed under open items. Status was checked on 2026-11-10 (JST).

## Decisions

- Repositories: add `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` to `vinoguessr-api` / `vinoguessr-app` / `vinoguessr-web`
- Agents: Codex by default; an independent Claude Code review substitutes when Codex cannot review because of its usage limit. For the 2026-11-10 handoff, the owner also allowed substitution when a repository environment is missing
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
- Merged the shared foundation: [.github#1](https://github.com/vinoguessr/.github/pull/1) at `01fd9c61bce2139beb8ea173339d45c02d49b69f`, the SHA every repository first called reusable workflows at (bumped to `38adaa6` on 2026-11-09, then `13fb975` on 2026-11-10)
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
  - All five other repositories were updated to `38adaa6afdfb7df020feb2a7ff93a6ddf1d79af8` and passed the new check: [vinoguessr-api#416](https://github.com/vinoguessr/vinoguessr-api/pull/416), [vinoguessr-app#22](https://github.com/vinoguessr/vinoguessr-app/pull/22), [vinoguessr-web#8](https://github.com/vinoguessr/vinoguessr-web/pull/8), [vinoguessr-docs#5](https://github.com/vinoguessr/vinoguessr-docs/pull/5), [vinoguessr-infrastructure#12](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/12)
- Narrowed the app to iOS and iPadOS ([ADR-0006](https://github.com/vinoguessr/vinoguessr-docs/blob/main/docs/adr/0006-app-platforms.md) in [vinoguessr-docs#3](https://github.com/vinoguessr/vinoguessr-docs/pull/3), targets in [vinoguessr-app#20](https://github.com/vinoguessr/vinoguessr-app/pull/20))
- App CI ([vinoguessr-app#21](https://github.com/vinoguessr/vinoguessr-app/pull/21)) builds the app and tests VinoGuessrKit on the iOS Simulator; its `Build VinoGuessr (iOS Simulator)` and `Test VinoGuessrKit (iOS Simulator)` jobs are required checks in vinoguessr-app's `Main PR and verified CI` ruleset
- Updated the shared app platform description and simulator verification instructions ([.github#9](https://github.com/vinoguessr/.github/pull/9), `13fb975`); the app-specific text and SwiftUI policy now agree on iOS and iPadOS only
- Rejected non-canonical action references in the shared workflow policy ([.github#10](https://github.com/vinoguessr/.github/pull/10), `29d4647`), closing [.github#8](https://github.com/vinoguessr/.github/issues/8)
- Made Deploy migrations use the `POSTGRES_PASSWORD` version Cloud Run pins ([vinoguessr-api#417](https://github.com/vinoguessr/vinoguessr-api/pull/417))
- Pinned the app build to `VinoGuessrKit/Package.resolved` ([vinoguessr-app#23](https://github.com/vinoguessr/vinoguessr-app/pull/23)), closing [vinoguessr-app#19](https://github.com/vinoguessr/vinoguessr-app/issues/19)
- Updated ADR-0005 to describe the local-only passkey playground ([vinoguessr-docs#6](https://github.com/vinoguessr/vinoguessr-docs/pull/6)), closing [vinoguessr-docs#4](https://github.com/vinoguessr/vinoguessr-docs/issues/4)
- Confirmed that the retried infrastructure main check after #12 passed ([Repository CI, attempt 2](https://github.com/vinoguessr/vinoguessr-infrastructure/actions/runs/42579235708)); no retry remains pending
- Project (by the owner): enabled the "Auto-add to project" workflow and deleted the default "View 1"

## Done (2026-11-10)

- Documented the serialization of Deploy and Cloud Run changes in `terraform apply` ([vinoguessr-infrastructure#13](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/13)). Disabled workflow runs are included in every `gh run list --workflow deploy.yml` check with `--all`. Together with api #417, this completed [vinoguessr-api#414](https://github.com/vinoguessr/vinoguessr-api/issues/414), which was closed manually after the README change merged
- Installed a pinned, checksum-verified Atlas Community release ([vinoguessr-api#418](https://github.com/vinoguessr/vinoguessr-api/pull/418), closing [vinoguessr-api#415](https://github.com/vinoguessr/vinoguessr-api/issues/415)). The [production Deploy](https://github.com/vinoguessr/vinoguessr-api/actions/runs/42760427684) verified the checksum, reported Atlas Community v1.3.6, and completed migrations and the Cloud Run image update
- Synced all five product repositories to `vinoguessr/.github@13fb97569cc4d4323a439db52f55ce962e63c12f`: [api#420](https://github.com/vinoguessr/vinoguessr-api/pull/420), [app#24](https://github.com/vinoguessr/vinoguessr-app/pull/24), [web#9](https://github.com/vinoguessr/vinoguessr-web/pull/9), [docs#7](https://github.com/vinoguessr/vinoguessr-docs/pull/7), and [infrastructure#14](https://github.com/vinoguessr/vinoguessr-infrastructure/pull/14). All are merged, call the pinned shared policy, and passed required CI and independent reviews. The app-specific instructions and README were preserved apart from the source SHA and the README end marker; its SwiftUI policy matches the shared source. Closed [.github#7](https://github.com/vinoguessr/.github/issues/7) after verifying the five merges and deployments
- After the owner's explicit approval, deployed the sync merges to production: [API Deploy](https://github.com/vinoguessr/vinoguessr-api/actions/runs/42764336801) and [Web Deploy](https://github.com/vinoguessr/vinoguessr-web/actions/runs/42764343729) both succeeded. Cloud Run reports `vinoguessr-api-00012-kzj` and `vinoguessr-web-00005-5rh` ready, each serving 100% of traffic with its corresponding main image. Results are recorded on the PRs

## Open items

- The owner will resume the pre-foundation PRs [vinoguessr-api#236](https://github.com/vinoguessr/vinoguessr-api/pull/236), [#271](https://github.com/vinoguessr/vinoguessr-api/pull/271), and [#329](https://github.com/vinoguessr/vinoguessr-api/pull/329) later. They need the current main and required checks before they can merge; this handoff leaves them untouched
- The owner approval gate for production deploys remains deferred by the owner's decision ([.github#6](https://github.com/vinoguessr/.github/issues/6)). The workflows still deploy automatically; agent-initiated production deploys and merges to api/web main require the owner's approval for each operation
- Update the pinned Atlas version by 2027-03-26 ([vinoguessr-api#419](https://github.com/vinoguessr/vinoguessr-api/issues/419))
- Owner: decide whether to create the missing Codex cloud environments. Several review requests still return "create an environment for this repo"; substitute review evidence is recorded on the affected PRs
- Owner: save "Group by: Repository" in the Project's "By repository" view. Its grouping is still empty in the API
- Check Project membership when opening Issues or PRs. "Auto-add to project" is enabled, but the API does not expose its repository/filter configuration; the Issue Forms do not set `projects`. The five sync PRs were added explicitly. "Auto-archive items" is not configured
- Owner: initialize the GitHub wiki of `vinoguessr-docs` with its first page, then sync `docs/wiki`. The repository has Wiki enabled, but the wiki git endpoint still returns "Repository not found"
- Owner: rename the local checkout folder `blindlog-api` to `vinoguessr-api`
