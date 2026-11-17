#!/usr/bin/env python3
"""Copy only the workaround policy and Issue Form from a durable foundation commit."""
import argparse
import re
import shutil
import subprocess
from pathlib import Path

import sync_foundation

FORM = Path('.github/ISSUE_TEMPLATE/workaround.yml')


def updated_agents(original, policy, sha):
    sections = list(re.finditer(r'^## Tracking workarounds\n.*?(?=^## |\Z)', original, re.M | re.S))
    if len(sections) != 1:
        raise RuntimeError('Expected exactly one existing Tracking workarounds section')
    section = sections[0]
    replacement = policy.rstrip() + f'\n\nWorkaround policy source: `vinoguessr/.github@{sha}`.\n\n'
    return original[:section.start()] + replacement + original[section.end():]


def sync(source, sha, target):
    shared = (source / 'AGENTS.md').read_text()
    section = re.search(r'^## Tracking workarounds\n.*?(?=^## |\Z)', shared, re.M | re.S)
    if section is None:
        raise RuntimeError('Source has no Tracking workarounds section')
    agents = target / 'AGENTS.md'
    updated = updated_agents(agents.read_bytes().decode(), section.group(), sha)
    form = target / FORM
    if form.exists() and form.read_bytes() != (source / FORM).read_bytes():
        raise RuntimeError('Existing workaround form differs; reconcile it before syncing')
    form.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / FORM, form)
    agents.write_bytes(updated.encode())


def ensure_target_repository(target, repo):
    result = subprocess.run(['git', '-C', str(target), 'remote', 'get-url', 'origin'], capture_output=True, text=True)
    origin = result.stdout.strip().rstrip('/').removesuffix('.git')
    allowed = [f'https://github.com/vinoguessr/{repo}', f'git@github.com:vinoguessr/{repo}',
               f'ssh://git@github.com/vinoguessr/{repo}']
    if result.returncode or origin not in allowed:
        raise RuntimeError('Target origin does not match the selected VinoGuessr repository')


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
    ensure_target_repository(args.target.resolve(), args.repo)
    sync_foundation.ensure_target_clean(args.target.resolve())
    sync(args.source.resolve(), args.sha, args.target.resolve())


if __name__ == '__main__':
    main()
