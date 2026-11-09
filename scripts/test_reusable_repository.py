import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/reusable-repository.yml'
CHECKOUT = 'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1'
REPOSITORY_WORKFLOW = """name: Repository CI
on:
  pull_request:
permissions:
  contents: read
jobs:
  policy:
    uses: vinoguessr/.github/.github/workflows/reusable-repository.yml@01fd9c61bce2139beb8ea173339d45c02d49b69f
    permissions:
      contents: read
"""
BASE = {
    'AGENTS.md': 'rules', 'CLAUDE.md': '@AGENTS.md\n', 'README.md': 'readme', '.github/CODEOWNERS': '* @owner',
    '.github/workflows/repository.yml': REPOSITORY_WORKFLOW, '.github/dependabot.yml': 'version: 2',
    '.claude/agents/reviewer.md': 'reviewer', '.claude/agents/security-reviewer.md': 'security',
}
READ_ONLY = 'permissions:\n  contents: read\n'
PINNED_CHECKOUT = f'      - uses: {CHECKOUT}\n        with:\n          persist-credentials: false\n'


def workflow(steps=PINNED_CHECKOUT, permissions=READ_ONLY, job='', on='on: pull_request\n'):
    return f'name: CI\n{on}{permissions}jobs:\n  build:\n    runs-on: ubuntu-latest\n{job}    steps:\n{steps}'


def policy_script():
    steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['policy']['steps']
    return next(step['run'] for step in steps if step.get('shell') == 'python')


def run_script(root):
    result = subprocess.run([sys.executable, '-c', policy_script()], cwd=root, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr


class ReusableRepositoryPolicyTests(unittest.TestCase):
    """Runs the policy step that downstream repositories execute against fixture repositories."""

    def run_policy(self, overrides):
        files = {**BASE, **overrides}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            for relative, text in files.items():
                if text is None:
                    continue
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                if isinstance(text, bytes):
                    (root / relative).write_bytes(text)
                else:
                    (root / relative).write_text(text)
            subprocess.run(['git', 'add', '-A', '-f'], cwd=root, check=True)
            return run_script(root)

    def assertRejected(self, overrides, *fragments):
        ok, output = self.run_policy(overrides)
        self.assertFalse(ok, output)
        for fragment in fragments:
            self.assertIn(fragment, output)

    def test_complete_repository_passes(self):
        ok, output = self.run_policy({})
        self.assertTrue(ok, output)

    def test_foundation_repository_passes(self):
        ok, output = run_script(ROOT)
        self.assertTrue(ok, output)

    def test_requires_claude_review_agents(self):
        self.assertRejected({'.claude/agents/reviewer.md': None}, '.claude/agents/reviewer.md')

    def test_requires_claude_md_to_import_agents(self):
        self.assertRejected({'CLAUDE.md': 'See AGENTS.md\n'}, 'CLAUDE.md must import AGENTS.md')

    def test_reports_missing_claude_md(self):
        self.assertRejected({'CLAUDE.md': None}, "Missing repository policy files: ['CLAUDE.md']")

    def test_rejects_env_variants_but_allows_example(self):
        self.assertRejected({'.env.production': 'X=1'}, "Unexpected sensitive files: ['.env.production']")
        self.assertTrue(self.run_policy({'.env.example': 'X='})[0])

    def test_rejects_pem_keys(self):
        self.assertRejected({'certs/pass.pem': 'key'}, "Unexpected sensitive files: ['certs/pass.pem']")

    def test_rejects_service_account_json_but_allows_other_json(self):
        self.assertRejected({'sa.json': '{"type": "service_account", "private_key": "k"}'},
                            "Unexpected sensitive files: ['sa.json']")
        self.assertTrue(self.run_policy({'package.json': '{"name": "x"}'})[0])

    def test_hardened_workflows_pass(self):
        deploy = workflow(
            permissions='permissions: {}\n',
            job='    permissions:\n      contents: read\n      id-token: write\n',
            steps=PINNED_CHECKOUT + '      - uses: ./.github/actions/build\n      - run: echo deploy\n',
        )
        ok, output = self.run_policy({'.github/workflows/ci.yml': workflow(), '.github/workflows/deploy.yaml': deploy})
        self.assertTrue(ok, output)

    def test_rejects_actions_not_pinned_to_a_full_commit_sha(self):
        steps = ('      - uses: actions/checkout@v7.0.1\n        with:\n          persist-credentials: false\n'
                 '      - uses: actions/setup-python@6d4fd22\n')
        self.assertRejected({'.github/workflows/ci.yml': workflow(steps=steps)},
                            '.github/workflows/ci.yml: job build: actions/checkout@v7.0.1 is not pinned to a full commit SHA',
                            'actions/setup-python@6d4fd22 is not pinned')

    def test_rejects_reusable_workflow_calls_not_pinned_to_a_full_commit_sha(self):
        caller = REPOSITORY_WORKFLOW.replace('@01fd9c61bce2139beb8ea173339d45c02d49b69f', '@main')
        self.assertRejected({'.github/workflows/repository.yml': caller},
                            'job policy: vinoguessr/.github/.github/workflows/reusable-repository.yml@main is not pinned')

    def test_requires_top_level_permissions(self):
        self.assertRejected({'.github/workflows/ci.yml': workflow(permissions='')},
                            '.github/workflows/ci.yml: top-level permissions must list read-only scopes')

    def test_rejects_write_or_shorthand_permissions_at_the_top_level(self):
        for permissions in ['permissions:\n  contents: write\n', 'permissions: write-all\n', 'permissions: read-all\n']:
            with self.subTest(permissions=permissions):
                self.assertRejected({'.github/workflows/ci.yml': workflow(permissions=permissions)},
                                    'top-level permissions must list read-only scopes')

    def test_rejects_shorthand_permissions_on_a_job(self):
        for shorthand in ['write-all', 'read-all']:
            with self.subTest(shorthand=shorthand):
                self.assertRejected({'.github/workflows/ci.yml': workflow(job=f'    permissions: {shorthand}\n')},
                                    f"job build: permissions must list scopes, not '{shorthand}'")

    def test_requires_checkout_without_persisted_credentials(self):
        for checkout in [f'      - uses: {CHECKOUT}\n', f'      - uses: {CHECKOUT}\n        with:\n',
                         f'      - uses: {CHECKOUT}\n        with: nope\n',
                         f'      - uses: {CHECKOUT}\n        with:\n          persist-credentials: true\n',
                         f'      - uses: {CHECKOUT}\n        with:\n          persist-credentials: false\n'
                         '          Persist-Credentials: true\n']:
            with self.subTest(checkout=checkout):
                self.assertRejected({'.github/workflows/ci.yml': workflow(steps=checkout)},
                                    'job build: actions/checkout must set persist-credentials: false')

    def test_recognizes_checkout_in_any_letter_case(self):
        for spelling in ['Actions/Checkout@', 'ACTIONS/CHECKOUT@']:
            with self.subTest(spelling=spelling):
                steps = f'      - uses: {CHECKOUT.replace("actions/checkout@", spelling)}\n'
                self.assertRejected({'.github/workflows/ci.yml': workflow(steps=steps)},
                                    'job build: actions/checkout must set persist-credentials: false')

    def test_rejects_non_canonical_action_references(self):
        # Each spelling is pinned and sets persist-credentials: false, so only its spelling is wrong.
        # U+0441 is CYRILLIC SMALL LETTER ES and U+FF43 is FULLWIDTH LATIN SMALL LETTER C; both look like "c".
        for spelling in ['actions/check%6Fut', 'actions/checkout.git', 'actions/checkout.GIT', 'actions//checkout',
                         'actions\\checkout', 'actions\\checkout/x', '/actions/checkout', 'actions/checkout/',
                         'actions/checkout/.', 'actions/checkout/../checkout', 'actions/checkout/ x',
                         'actions/\u0441heckout', 'actions/\uff43heckout', 'checkout']:
            with self.subTest(spelling=spelling):
                ref = CHECKOUT.replace('actions/checkout', spelling)
                # A JSON string is a YAML double-quoted scalar, so every spelling survives the YAML parser intact.
                steps = f'      - uses: {json.dumps(ref)}\n        with:\n          persist-credentials: false\n'
                shown = ref.encode('ascii', 'backslashreplace').decode()  # The log escapes non-ASCII characters.
                self.assertRejected({'.github/workflows/ci.yml': workflow(steps=steps)},
                                    f'job build: {shown} is not a canonical owner/repo[/path] reference')

    def test_escapes_control_characters_so_a_reference_cannot_start_a_log_line(self):
        ref = CHECKOUT + '\n::warning::injected'
        steps = f'      - uses: {json.dumps(ref)}\n        with:\n          persist-credentials: false\n'
        ok, output = self.run_policy({'.github/workflows/ci.yml': workflow(steps=steps)})
        self.assertFalse(ok, output)
        self.assertIn(f'{CHECKOUT}\\n::warning::injected is not pinned to a full commit SHA', output)
        self.assertFalse(any(line.startswith('::') for line in output.splitlines()), output)

    def test_rejects_non_canonical_reusable_workflow_calls(self):
        caller = REPOSITORY_WORKFLOW.replace('vinoguessr/.github/.github/', 'vinoguessr/.github//.github/')
        self.assertRejected({'.github/workflows/repository.yml': caller},
                            'job policy: vinoguessr/.github//.github/workflows/reusable-repository.yml@01fd9c61bce2139beb8ea173339d45c02d49b69f '
                            'is not a canonical owner/repo[/path] reference')

    def test_accepts_canonical_and_local_references(self):
        sha = CHECKOUT.rpartition('@')[2]
        steps = (PINNED_CHECKOUT + f'      - uses: github/codeql-action/init@{sha}\n'
                 f'      - uses: Some-Owner/repo.name_2/sub-dir/action.v1@{sha}\n'
                 '      - uses: ./.github/actions/build\n')
        local_call = ('name: Local\non: pull_request\npermissions:\n  contents: read\njobs:\n'
                      '  call:\n    uses: ./.github/workflows/ci.yml\n')
        ok, output = self.run_policy({'.github/workflows/ci.yml': workflow(steps=steps),
                                      '.github/workflows/local.yml': local_call})
        self.assertTrue(ok, output)

    def test_accepts_any_spelling_of_false_for_persist_credentials(self):
        for line in ['persist-credentials: "false"', 'persist-credentials: False', 'Persist-Credentials: false']:
            with self.subTest(line=line):
                steps = f'      - uses: {CHECKOUT}\n        with:\n          {line}\n'
                ok, output = self.run_policy({'.github/workflows/ci.yml': workflow(steps=steps)})
                self.assertTrue(ok, output)

    def test_checks_yaml_extension_workflows(self):
        self.assertRejected({'.github/workflows/ci.yaml': workflow(permissions='')}, '.github/workflows/ci.yaml')

    def test_rejects_pull_request_target(self):
        for on in ['on: pull_request_target\n', 'on: [push, pull_request_target]\n', 'on:\n  pull_request_target:\n']:
            with self.subTest(on=on):
                self.assertRejected({'.github/workflows/ci.yml': workflow(on=on)}, 'pull_request_target')

    def test_reports_invalid_workflow_yaml(self):
        self.assertRejected({'.github/workflows/ci.yml': 'jobs: [\n'}, '.github/workflows/ci.yml: invalid YAML', 'line 2')

    def test_reports_unreadable_workflows(self):
        for overrides in [{'.github/workflows/ci.yml': b'name: \xff\n'}, {'.github/workflows/ci.yml/README.md': 'x'}]:
            with self.subTest(overrides=overrides):
                ok, output = self.run_policy(overrides)
                self.assertFalse(ok, output)
                self.assertNotIn('Traceback', output)
                self.assertIn('.github/workflows/ci.yml: cannot read the workflow', output)

    def test_reports_malformed_workflows_instead_of_crashing(self):
        cases = {
            'on: push\n': 'ci.yml: expected a workflow mapping with jobs',
            workflow().replace('  build:\n    runs-on: ubuntu-latest\n', '  build: nope\n  other:\n    runs-on: x\n'):
                'ci.yml: job build: expected a mapping',
            workflow().split('    steps:')[0] + '    steps: 5\n': None,
        }
        for text, fragment in cases.items():
            with self.subTest(text=text):
                ok, output = self.run_policy({'.github/workflows/ci.yml': text})
                self.assertNotIn('Traceback', output)
                if fragment is not None:
                    self.assertFalse(ok, output)
                    self.assertIn(fragment, output)

    def test_reports_every_violation_in_one_run(self):
        self.assertRejected({'.github/workflows/a.yml': workflow(permissions=''),
                             '.github/workflows/b.yml': workflow(steps=f'      - uses: {CHECKOUT}\n'),
                             '.env': 'X=1'},
                            '.github/workflows/a.yml: top-level permissions', '.github/workflows/b.yml: job build',
                            "Unexpected sensitive files: ['.env']")


if __name__ == '__main__':
    unittest.main()
