# GitHub Actions workflow lockfiles

Use the official `github/gh-actions-lock` CLI (currently v0.4.0). Generate `.github/workflows/actions.lock`; never edit the generated file by hand.

```sh
gh extension install github/gh-actions-lock --pin v0.4.0
gh actions-lock --no-narrow
gh actions-lock --verify-local
gh actions-lock --verify --no-narrow
```

`--no-narrow` preserves our existing full commit SHA `uses:` references. Inspect both workflow and lockfile diffs, including repository identities, upstream refs, exact commits and transitive dependencies. Routine generation must not silently advance dependencies. Deliberate updates use a reviewed PR and provenance verification. Do not automate `--accept-moved`; investigate moved or unreachable pins before choosing a replacement.

Every repository has a read-only verification workflow. Its official Linux binary is pinned to a release and independently recorded SHA256; update both only after reviewing the release. The existing `GITHUB_TOKEN` has only `contents: read`; no additional secret is required. Do not run untrusted PR code under `pull_request_target`.

`--verify-local` checks offline coverage only. The networked `--verify` also checks source repository identity and pin provenance and must succeed before merge. Verification is read-only for repository files; the tool may write normal user-cache logs. CI does not modify or commit lockfiles. A failure is not a successful security check.

Lock all workflow definitions, including reusable definitions in `.github`. Calls at `jobs.<id>.uses` are not covered: keep those calls at full SHAs from the common repository's default-branch history. To consume locked reusable definitions, callers must reference a commit containing the defining repository's lockfile. A caller's lockfile does not lock dependencies inside an old reusable workflow commit.

Container image digests, runner images, tool downloads, build inputs and the behavior of an action are outside the lockfile's guarantee. Preserve existing digest/checksum/version controls and review dependencies themselves. This adoption does not enable an organization-wide Require lockfile policy or expand permissions.

When adding/removing workflows or changing action references, regenerate and verify the full directory, then commit all generated changes in the same PR. Dependabot updates still require review and checks. Every Dependabot update entry uses `cooldown.default-days: 7` for version updates. Preserve existing schedules and other options; a weekly schedule is separate from a seven-day release-age cooldown. Security updates are outside this cooldown. Do not add shorter SemVer overrides or exclusions. Existing unrelated Dependabot work is not a blocker. See [Dependabot cooldown](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown). Adopted from [sauna-studio/.github](https://github.com/sauna-studio/.github/blob/main/policies/workflow-lockfiles.md).

References: [GitHub concept](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles), [official generator](https://github.com/github/gh-actions-lock), [GA announcement](https://github.blog/changelog/2026-10-28-github-actions-workflow-lockfiles-are-generally-available/).
