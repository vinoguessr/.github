import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/reusable-repository.yml'
BASE = {
    'AGENTS.md': 'rules', 'CLAUDE.md': '@AGENTS.md\n', 'README.md': 'readme', '.github/CODEOWNERS': '* @owner',
    '.github/workflows/repository.yml': 'name: x', '.github/dependabot.yml': 'version: 2',
    '.claude/agents/reviewer.md': 'reviewer', '.claude/agents/security-reviewer.md': 'security',
}


def policy_script():
    steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['policy']['steps']
    return next(step['run'] for step in steps if step.get('shell') == 'python')


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
                (root / relative).write_text(text)
            subprocess.run(['git', 'add', '-A', '-f'], cwd=root, check=True)
            result = subprocess.run([sys.executable, '-c', policy_script()], cwd=root, capture_output=True, text=True)
            return result.returncode == 0, result.stdout + result.stderr

    def test_complete_repository_passes(self):
        ok, output = self.run_policy({})
        self.assertTrue(ok, output)

    def test_requires_claude_review_agents(self):
        ok, output = self.run_policy({'.claude/agents/reviewer.md': None})
        self.assertFalse(ok)
        self.assertIn('.claude/agents/reviewer.md', output)

    def test_requires_claude_md_to_import_agents(self):
        ok, output = self.run_policy({'CLAUDE.md': 'See AGENTS.md\n'})
        self.assertFalse(ok)
        self.assertIn('CLAUDE.md must import AGENTS.md', output)

    def test_rejects_env_variants_but_allows_example(self):
        self.assertFalse(self.run_policy({'.env.production': 'X=1'})[0])
        self.assertTrue(self.run_policy({'.env.example': 'X='})[0])

    def test_rejects_pem_keys(self):
        self.assertFalse(self.run_policy({'certs/pass.pem': 'key'})[0])

    def test_rejects_service_account_json_but_allows_other_json(self):
        self.assertFalse(self.run_policy({'sa.json': '{"type": "service_account", "private_key": "k"}'})[0])
        self.assertTrue(self.run_policy({'package.json': '{"name": "x"}'})[0])


if __name__ == '__main__':
    unittest.main()
