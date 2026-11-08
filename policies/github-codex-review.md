## Code review and merge conditions

1. Check the automatic Codex review on the PR. Verify the basis of each finding and make the required code fixes and regression tests.
2. Reply to each review thread with the fix, the commit, and the verification result. If no change is needed, explain why and do not hide open items.
3. After addressing findings, comment exactly `@codex review` on the PR to request a new review, and wait for the review of the latest commit.
4. Repeat for any new findings. Merge only after GitHub Codex reports no findings, no findings remain unaddressed, and the required CI has passed.
5. A missing review, a missing integration, or a failed run does not mean "no findings". Record the cause and the request URL, and keep the PR open. A passing independent local Review Agent does not replace this condition; the only exception is the usage-limit substitute below.

### Substitute review when Codex hits its usage limit

Only when Codex cannot review because of its usage limit (insufficient tokens), a Claude Code independent review may substitute. When substituting:

- After Codex reports its usage limit, run Claude Code's `reviewer` agent (`.claude/agents/reviewer.md`) as a separate run against the latest commit, in a context separate from the implementing agent. A review run during implementation never counts as the substitute. For PRs that change authentication, personal data, event participation authorization, scoring, or Apple Wallet pass signing, also run `security-reviewer`.
- Record in the PR the evidence that Codex was unavailable (the limit message and the URL of the request comment), the reviewed commit, and the findings and fixes.
- After fixing findings, review the latest commit again, and merge only once there are no findings and the required CI has passed.
- Reasons other than the usage limit (no response, missing integration, failed run) do not qualify for substitution. Investigate and record the cause, and keep the PR open.

This GitHub review is in addition to the independent Review Agent running in parallel during implementation and to real builds and tests. Requesting a review does not count as passing. Avoid automated replies and repeated identical requests, and record each review round and its commit in the PR.
