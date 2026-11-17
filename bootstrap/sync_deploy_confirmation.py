#!/usr/bin/env python3
"""Apply only the shared production-confirmation policy to a clean consumer checkout."""
import argparse
import re
from pathlib import Path

import sync_foundation
import sync_workaround_tracking

OLD_APPROVAL = 'Creating billed resources, production deploys, `terraform apply`, and broad IAM grants require explicit approval.'
NEW_APPROVAL = 'Creating billed resources, `terraform apply`, and broad IAM grants require explicit approval. Production deployments do not require a separate user confirmation; existing authentication, permissions, CI, and review gates remain in force.'
OLD_ENVIRONMENT = 'Environments separate the approval boundaries of development, staging, and production.'
NEW_ENVIRONMENT = 'Environments keep development, staging, and production separated.'
OLD_CODING = 'Do not deploy production, run terraform apply, create billed resources, expand permissions, or merge your own PR without explicit authorization.'
NEW_CODING = 'Do not run terraform apply, create billed resources, expand permissions, or merge your own PR without explicit authorization. Production deployments do not require a separate user confirmation; keep existing authentication and validation gates.'
OLD_INFRASTRUCTURE = 'Do not run apply, production deploys, billed resource creation, or broad IAM grants without explicit approval.'
NEW_INFRASTRUCTURE = 'Do not run apply, billed resource creation, or broad IAM grants without explicit approval.'
CODING = Path('.codex/agents/coding.toml')


def replace_policy(text, old, new):
    if text.count(old) == 1 and new not in text:
        return text.replace(old, new)
    if old not in text and text.count(new) == 1:
        return text
    raise RuntimeError('Policy text differs or is ambiguous; reconcile it before syncing')


def updated_agents(original, sha, repo):
    updated = replace_policy(original, OLD_APPROVAL, NEW_APPROVAL)
    updated = replace_policy(updated, OLD_ENVIRONMENT, NEW_ENVIRONMENT)
    if repo == 'vinoguessr-infrastructure':
        updated = replace_policy(updated, OLD_INFRASTRUCTURE, NEW_INFRASTRUCTURE)
    sections = list(re.finditer(r'^## Security\n.*?(?=^## |\Z)', updated, re.M | re.S))
    if len(sections) != 1:
        raise RuntimeError('Expected one Security section')
    section = sections[0]
    policy = re.sub(r'^Deployment confirmation policy source: .*\n', '', section.group(), flags=re.M).rstrip()
    policy += f'\n\nDeployment confirmation policy source: `vinoguessr/.github@{sha}`.\n\n'
    return updated[:section.start()] + policy + updated[section.end():]


def sync(source, sha, repo, target):
    if NEW_APPROVAL not in (source / 'AGENTS.md').read_text() or NEW_CODING not in (source / CODING).read_text():
        raise RuntimeError('Source does not contain the expected deployment-confirmation policy')
    agents = target / 'AGENTS.md'
    coding = target / CODING
    # Validate every candidate before writing any file.
    agent_text = updated_agents(agents.read_bytes().decode(), sha, repo)
    coding_text = replace_policy(coding.read_bytes().decode(), OLD_CODING, NEW_CODING)
    candidates = [(agents, agent_text), (coding, coding_text)]
    if repo == 'vinoguessr-infrastructure':
        readme = target / 'README.md'
        readme_text = replace_policy(readme.read_bytes().decode(), OLD_INFRASTRUCTURE, NEW_INFRASTRUCTURE)
        candidates.append((readme, readme_text))
    for path, text in candidates:
        path.write_bytes(text.encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=sync_foundation.ROOT)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--repo', required=True, choices=sync_foundation.SCOPES)
    parser.add_argument('--target', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.sha):
        raise ValueError('--sha must be a full commit SHA')
    sync_foundation.ensure_durable(args.sha)
    sync_foundation.ensure_source_matches(args.source.resolve(), args.sha)
    sync_workaround_tracking.ensure_target_repository(args.target.resolve(), args.repo)
    sync_foundation.ensure_target_clean(args.target.resolve())
    sync(args.source.resolve(), args.sha, args.repo, args.target.resolve())


if __name__ == '__main__':
    main()
