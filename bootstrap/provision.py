#!/usr/bin/env python3
"""Explicit, resumable GitHub bootstrap for the VinoGuessr organization.

Reads gh's existing auth; never reads tokens. Run one stage at a time:

  --stage project   create/find the Organization Project, its fields, and repo links
  --stage items     add open Issues of every repo to the Project and set Area
  --stage settings  repository merge/security settings, empty Environments, labels
  --stage rulesets  protect main with PR + required CI checks (run after checks exist)

Repo contents always change through PRs; this script only touches GitHub settings.
Only allowlisted VinoGuessr repositories may be mutated.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = 'vinoguessr'
PROJECT_TITLE = 'VinoGuessr'
REPOS = ['.github', 'vinoguessr-api', 'vinoguessr-app', 'vinoguessr-web',
         'vinoguessr-infrastructure', 'vinoguessr-docs']
AREA_BY_REPO = {
    '.github': 'github',
    'vinoguessr-api': 'api',
    'vinoguessr-app': 'apple',
    'vinoguessr-web': 'web',
    'vinoguessr-infrastructure': 'infra',
    'vinoguessr-docs': 'docs',
}
FIELDS = [
    ('Priority', ['P0', 'P1', 'P2']),
    ('Phase', ['Foundation', 'MVP', 'Integration']),
    ('Area', [AREA_BY_REPO[r] for r in REPOS]),
]
LABELS = [
    ('type:task', '1D76DB', 'Implementation or foundation task'),
    ('type:bug', 'D73A4A', 'Confirmed defect with regression verification'),
]
RULESET_NAME = 'Main PR and verified CI'
GITHUB_ACTIONS_APP_ID = 15368
# Check names as reported by GitHub Actions. A check that has never run on the
# repository blocks every merge, so rulesets are applied only after these exist.
# Path-filtered workflows (vinoguessr-api Atlas `diff`) are not required: a PR that
# does not touch those paths would never report the check and could not merge.
REQUIRED_CHECKS = {
    '.github': ['Foundation validation', 'Analyze Python tooling', 'Verify action dependency provenance'],
    'vinoguessr-api': ['policy / Repository policy', 'Verify action dependency provenance', 'lint', 'test', 'docker-build'],
    'vinoguessr-app': ['policy / Repository policy', 'Verify action dependency provenance'],
    'vinoguessr-web': ['policy / Repository policy', 'Verify action dependency provenance', 'swift / Swift build and test'],
    'vinoguessr-infrastructure': ['policy / Repository policy', 'Verify action dependency provenance', 'terraform / Terraform format and validate'],
    'vinoguessr-docs': ['policy / Repository policy', 'Verify action dependency provenance'],
}
STATE_PATH = ROOT / 'docs/provisioning-results.json'


def gh(*args, data=None):
    cmd = ['gh', *args]
    if data is not None:
        cmd += ['--input', '-']
    r = subprocess.run(cmd, input=json.dumps(data) if data is not None else None,
                       text=True, capture_output=True)
    if r.returncode:
        raise RuntimeError(f'{" ".join(args[:4])}: {r.stderr.strip()}')
    return json.loads(r.stdout) if r.stdout.strip() else None


def api(path, method='GET', data=None):
    return gh('api', path, '--method', method, data=data)


def save(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')


def pages(path):
    result = []
    for page in range(1, 101):
        part = api(f'{path}{"&" if "?" in path else "?"}per_page=100&page={page}')
        result.extend(part)
        if len(part) < 100:
            return result
    raise RuntimeError('Pagination limit exceeded')


def repository_settings():
    return {
        'has_issues': True, 'has_wiki': True, 'delete_branch_on_merge': True,
        'allow_squash_merge': True, 'allow_merge_commit': False, 'allow_rebase_merge': False,
        'security_and_analysis': {
            'secret_scanning': {'status': 'enabled'},
            'secret_scanning_push_protection': {'status': 'enabled'},
        },
    }


def ruleset_payload(checks):
    if not checks:
        raise ValueError('A ruleset needs at least one required check')
    return {
        'name': RULESET_NAME,
        'target': 'branch',
        'enforcement': 'active',
        'bypass_actors': [],
        'conditions': {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}},
        'rules': [
            {'type': 'deletion'},
            {'type': 'non_fast_forward'},
            {'type': 'pull_request', 'parameters': {
                # A single owner cannot approve their own PR; reviews are recorded in the PR instead.
                'required_approving_review_count': 0,
                'dismiss_stale_reviews_on_push': True,
                'require_code_owner_review': False,
                'require_last_push_approval': False,
                'required_review_thread_resolution': True,
                'allowed_merge_methods': ['squash'],
            }},
            {'type': 'required_status_checks', 'parameters': {
                'strict_required_status_checks_policy': True,
                'do_not_enforce_on_create': False,
                'required_status_checks': [
                    {'context': c, 'integration_id': GITHUB_ACTIONS_APP_ID} for c in checks
                ],
            }},
        ],
    }


def project(state):
    projects = gh('project', 'list', '--owner', ORG, '--format', 'json', '--limit', '100')['projects']
    matches = [p for p in projects if p['title'] == PROJECT_TITLE]
    if len(matches) > 1:
        raise RuntimeError('Ambiguous existing project')
    p = matches[0] if matches else gh('project', 'create', '--owner', ORG, '--title', PROJECT_TITLE, '--format', 'json')
    n = str(p['number'])
    state['project'] = {k: p[k] for k in ('id', 'number', 'url')}
    save(state)
    fields = gh('project', 'field-list', n, '--owner', ORG, '--format', 'json', '--limit', '100')['fields']
    for name, options in FIELDS:
        if name not in [f['name'] for f in fields]:
            gh('project', 'field-create', n, '--owner', ORG, '--name', name, '--data-type', 'SINGLE_SELECT',
               '--single-select-options', ','.join(options), '--format', 'json')
    for repo in REPOS:
        gh('project', 'link', n, '--owner', ORG, '--repo', f'{ORG}/{repo}')
    print(p['url'], flush=True)


def items(state):
    n = str(state['project']['number'])
    fields = gh('project', 'field-list', n, '--owner', ORG, '--format', 'json', '--limit', '100')['fields']
    area = next(f for f in fields if f['name'] == 'Area')
    existing = gh('project', 'item-list', n, '--owner', ORG, '--limit', '1000', '--format', 'json')['items']
    by_url = {i['content']['url']: i for i in existing if i.get('content', {}).get('url')}
    state.setdefault('items', {})
    for repo in REPOS:
        for issue in pages(f'repos/{ORG}/{repo}/issues?state=open'):
            if 'pull_request' in issue:
                continue
            url = issue['html_url']
            item = by_url.get(url) or gh('project', 'item-add', n, '--owner', ORG, '--url', url, '--format', 'json')
            # Existing Area values (including manual edits) are never overwritten on reruns.
            if not item.get('area'):
                option = next(o for o in area['options'] if o['name'] == AREA_BY_REPO[repo])
                gh('project', 'item-edit', '--project-id', state['project']['id'], '--id', item['id'],
                   '--field-id', area['id'], '--single-select-option-id', option['id'])
            state['items'][url] = item['id']
            save(state)
            print('item', url, flush=True)


def settings(state):
    state.setdefault('settings', {})
    for repo in REPOS:
        path = f'repos/{ORG}/{repo}'
        record = state['settings'].setdefault(repo, {})
        api(path, 'PATCH', repository_settings())
        for endpoint in ['vulnerability-alerts', 'automated-security-fixes', 'private-vulnerability-reporting']:
            try:
                api(path + '/' + endpoint, 'PUT')
                record[endpoint] = 'enabled'
            except RuntimeError as e:
                record[endpoint] = str(e)
        # Empty environments only: no credentials, deploys, IAM or billing resources.
        for name in ['development', 'staging', 'production']:
            api(path + '/environments/' + name, 'PUT', {'deployment_branch_policy': {'protected_branches': True, 'custom_branch_policies': False}})
        names = {label['name'] for label in pages(f'{path}/labels')}
        for name, color, description in LABELS:
            if name not in names:
                api(f'{path}/labels', 'POST', {'name': name, 'color': color, 'description': description})
        record['security_and_analysis'] = api(path)['security_and_analysis']
        save(state)
        print('settings', repo, flush=True)


def rulesets(state):
    state.setdefault('rulesets', {})
    for repo in REPOS:
        path = f'repos/{ORG}/{repo}/rulesets'
        payload = ruleset_payload(REQUIRED_CHECKS[repo])
        current = [r for r in api(path) if r['name'] == RULESET_NAME]
        result = api(f'{path}/{current[0]["id"]}', 'PUT', payload) if current else api(path, 'POST', payload)
        state['rulesets'][repo] = {'id': result['id'], 'required_checks': REQUIRED_CHECKS[repo]}
        save(state)
        print('ruleset', repo, result['id'], flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--stage', required=True, choices=['project', 'items', 'settings', 'rulesets'])
    args = p.parse_args()
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {'organization': ORG}
    globals()[args.stage](state)


if __name__ == '__main__':
    main()
