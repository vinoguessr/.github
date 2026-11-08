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
- No admin app, admin web, or automation repositories

## Done

- Created `.github` / `vinoguessr-docs` / `vinoguessr-infrastructure` as public repositories (2026-11-08)
- Opened [vinoguessr/.github#1](https://github.com/vinoguessr/.github/pull/1) with the shared foundation

## Open items

- PRs distributing the shared files to each repository
- Apply the Project, settings, and rulesets with `bootstrap/provision.py`
- Move Terraform to the infrastructure repository
- Bootstrap the Google Cloud project `vinoguessr`
- The shared repository policy check does not yet enforce workflow hardening (SHA pinning, `permissions`, `persist-credentials`) in downstream repositories. The existing api and web workflows reference actions by tag; pin them in the distribution PRs, then decide whether to enforce it in `reusable-repository.yml`
