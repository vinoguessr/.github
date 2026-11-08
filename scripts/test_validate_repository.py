import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_repository', ROOT / 'scripts/validate_repository.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

SAFE_JOB = """
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: echo ok
"""


class ValidateRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv'))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def errors(self):
        return validator.validate(self.root)

    def assertRejected(self, fragment):
        errors = self.errors()
        self.assertTrue(any(fragment in e for e in errors), f'expected an error containing {fragment!r}, got {errors}')

    def test_repository_itself_is_valid(self):
        self.assertEqual(self.errors(), [])

    def test_rejects_pull_request_target_as_list(self):
        self.write('.github/workflows/x.yml', 'on: [pull_request_target]\npermissions:\n  contents: read\njobs:\n  a:' + SAFE_JOB)
        self.assertRejected('Unsafe trigger: x.yml')

    def test_rejects_pull_request_target_as_string(self):
        self.write('.github/workflows/x.yml', 'on: pull_request_target\npermissions:\n  contents: read\njobs:\n  a:' + SAFE_JOB)
        self.assertRejected('Unsafe trigger: x.yml')

    def test_checks_yaml_extension_workflows(self):
        self.write('.github/workflows/x.yaml', 'on: push\npermissions: write-all\njobs:\n  a:\n    runs-on: ubuntu-latest\n'
                   '    steps:\n      - uses: actions/checkout@v4\n')
        errors = self.errors()
        self.assertTrue(any('contents:read: x.yaml' in e for e in errors), errors)
        self.assertTrue(any('not SHA pinned: x.yaml' in e for e in errors), errors)
        self.assertTrue(any('Missing job timeout: x.yaml' in e for e in errors), errors)

    def test_rejects_job_level_write_all(self):
        self.write('.github/workflows/x.yml', 'on: push\npermissions:\n  contents: read\njobs:\n  a:\n    permissions: write-all' + SAFE_JOB)
        self.assertRejected('Job permissions too broad: x.yml: a')

    def test_rejects_job_level_contents_write(self):
        self.write('.github/workflows/x.yml', 'on: push\npermissions:\n  contents: read\njobs:\n  a:\n    permissions:\n      contents: write' + SAFE_JOB)
        self.assertRejected('Job permissions too broad: x.yml: a')

    def test_allows_security_events_write_only_for_codeql_jobs(self):
        codeql = ('on: push\npermissions:\n  contents: read\njobs:\n  a:\n    permissions:\n      contents: read\n'
                  '      security-events: write\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n'
                  '      - uses: github/codeql-action/init@9b3254085494b55a0f7c4c2b3d2d52cc712ce370\n')
        self.write('.github/workflows/x.yml', codeql)
        self.assertEqual(self.errors(), [])

    def test_rejects_security_events_write_outside_codeql(self):
        self.write('.github/workflows/x.yml', 'on: push\npermissions:\n  contents: read\njobs:\n  a:\n    permissions:\n'
                   '      security-events: write' + SAFE_JOB)
        self.assertRejected('Job permissions too broad: x.yml: a')

    def test_checkout_with_empty_with_is_reported_not_crashed(self):
        self.write('.github/workflows/x.yml', 'on: push\npermissions:\n  contents: read\njobs:\n  a:\n    runs-on: ubuntu-latest\n'
                   '    timeout-minutes: 5\n    steps:\n      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n        with:\n')
        self.assertRejected('Checkout credentials persist: x.yml')

    def test_rejects_write_tools_given_as_yaml_list(self):
        self.write('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: d\ntools: [Read, Write, Edit]\n---\nbody\n')
        self.assertRejected('Review agent tools must be a subset')

    def test_rejects_tools_outside_the_allowlist(self):
        self.write('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: d\ntools: Read, mcp__github__create_issue\n---\nbody\n')
        self.assertRejected('Review agent tools must be a subset')

    def test_rejects_agent_without_tools(self):
        self.write('.claude/agents/reviewer.md', '---\nname: reviewer\ndescription: d\n---\nbody\n')
        self.assertRejected('Review agent tools must be a subset')

    def test_rejects_claude_md_that_does_not_import_agents(self):
        self.write('CLAUDE.md', '# Rules\n\nSee AGENTS.md.\n')
        self.assertRejected('CLAUDE.md must import AGENTS.md')


if __name__ == '__main__':
    unittest.main()
