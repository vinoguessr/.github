# VinoGuessr · Organization foundation

VinoGuessr is a service for blind wine tasting: people create events, set questions, answer them, get scored, and build a season rating.

This repository is the source of truth for the shared development rules, the organization profile, Issue Forms, the PR template, reusable workflows, and the Codex and Claude Code agent definitions.

| Repository | Responsibility |
| --- | --- |
| [vinoguessr-api](https://github.com/vinoguessr/vinoguessr-api) | Swift 6 / Hummingbird / PostgreSQL / PostgresNIO / Valkey / Atlas / OpenAPI |
| [vinoguessr-app](https://github.com/vinoguessr/vinoguessr-app) | SwiftUI app for players / iOS, iPadOS, and macOS 27.0 or later |
| [vinoguessr-web](https://github.com/vinoguessr/vinoguessr-web) | Web for players / Swift and Hummingbird |
| [vinoguessr-infrastructure](https://github.com/vinoguessr/vinoguessr-infrastructure) | Terraform / Google Cloud Run / Cloudflare / OpenTelemetry |
| [vinoguessr-docs](https://github.com/vinoguessr/vinoguessr-docs) | Design documents / ADRs / wiki |
| [.github](https://github.com/vinoguessr/.github) | Shared settings, templates, and Actions |

Sign-in uses passkeys and email one-time codes. The VinoGuessr API and PostgreSQL are the source of truth for users, events, questions, answers, and scores.

Before developing, read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md), satisfy the Issue's dependencies, and change things through a branch and a PR. Run an independent Review Agent in parallel while implementing. PRs are reviewed by GitHub Codex; only when Codex cannot review because of its usage limit does a Claude Code review substitute ([review policy](policies/github-codex-review.md)).

Shared files are not necessarily inherited. `AGENTS.md`, `CLAUDE.md`, CODEOWNERS, CI, and the license are placed explicitly in each repository and updated through follow-up PRs when the shared rules change. Reusable workflows are called by a reviewed commit SHA.

`vinoguessr-app`, which implements SwiftUI, carries the body of the [SwiftUI policy](policies/swiftui.md) and its source commit in its AGENTS.md. The policy document alone never counts as verifying UI behavior or performance.

Code and documentation are written in English; Issue and PR bodies are written in Japanese.

This structure is based on [sauna-studio/.github](https://github.com/sauna-studio/.github).

Local verification (Python 3.11 or later; if the macOS system Python is older, use one from Homebrew or similar):

```sh
python3 -m venv /tmp/vinoguessr-foundation-venv
/tmp/vinoguessr-foundation-venv/bin/pip install -r scripts/validation-requirements.txt
/tmp/vinoguessr-foundation-venv/bin/python scripts/validate_repository.py
/tmp/vinoguessr-foundation-venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
actionlint
```

This repository does not deploy to production or create billed resources. GitHub settings are applied with [bootstrap/provision.py](bootstrap/provision.py), and the results and open items are recorded in [docs/setup-report.md](docs/setup-report.md).

- [Workflow dependency lockfiles](policies/workflow-lockfiles.md): generated coverage and provenance verification alongside existing SHA pins.
