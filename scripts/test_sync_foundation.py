import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_foundation', ROOT / 'bootstrap/sync_foundation.py')
sync_foundation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_foundation)

SHA = '0' * 40
OTHER_SHA = '1' * 40


class SyncFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.target = Path(self.tmp.name) / 'repo'
        self.target.mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=self.target, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def sync(self, repo='vinoguessr-web', sha=SHA):
        with mock.patch('builtins.print'):
            sync_foundation.sync(ROOT, sha, repo, self.target)

    def test_every_scoped_repository_is_a_known_repository(self):
        spec = importlib.util.spec_from_file_location('provision', ROOT / 'bootstrap/provision.py')
        provision = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(provision)
        self.assertEqual(set(sync_foundation.SCOPES), set(provision.REPOS) - {'.github'})

    def test_copies_shared_files_verbatim(self):
        self.sync()
        for relative in ['CLAUDE.md', 'CONTRIBUTING.md', 'SECURITY.md', '.github/CODEOWNERS',
                         '.github/pull_request_template.md', '.claude/agents/reviewer.md',
                         '.codex/agents/coding.toml', '.github/workflows/verify-lockfile.yml', 'LICENSE']:
            with self.subTest(file=relative):
                self.assertEqual((self.target / relative).read_text(), (ROOT / relative).read_text())

    def test_agents_is_shared_rules_plus_repository_section(self):
        self.sync()
        agents = (self.target / 'AGENTS.md').read_text()
        self.assertTrue(agents.startswith((ROOT / 'AGENTS.md').read_text().rstrip()))
        self.assertIn(f'## vinoguessr-web specifics\n\nShared rules source: `vinoguessr/.github@{SHA}`.', agents)
        self.assertNotIn('SwiftUI policy', agents)

    def test_app_agents_embeds_the_swiftui_policy(self):
        self.sync('vinoguessr-app')
        agents = (self.target / 'AGENTS.md').read_text()
        self.assertIn((ROOT / 'policies/swiftui.md').read_text().rstrip(), agents)
        self.assertIn(f'SwiftUI policy source: `vinoguessr/.github@{SHA}:policies/swiftui.md`.', agents)

    def test_repository_workflow_pins_reusable_workflows_to_the_sha(self):
        self.sync('vinoguessr-infrastructure')
        workflow = (self.target / '.github/workflows/repository.yml').read_text()
        self.assertIn(f'reusable-repository.yml@{SHA}', workflow)
        self.assertIn(f'reusable-terraform.yml@{SHA}', workflow)

    def test_never_overwrites_an_existing_license_or_dependabot(self):
        (self.target / 'LICENSE').write_text('custom license')
        (self.target / '.github').mkdir()
        (self.target / '.github/dependabot.yml').write_text('custom dependabot')
        self.sync()
        self.assertEqual((self.target / 'LICENSE').read_text(), 'custom license')
        self.assertEqual((self.target / '.github/dependabot.yml').read_text(), 'custom dependabot')

    def test_readme_section_is_appended_once_and_replaced_on_resync(self):
        (self.target / 'README.md').write_text('# repo\n\nExisting text.\n')
        self.sync()
        self.sync(sha=OTHER_SHA)
        readme = (self.target / 'README.md').read_text()
        self.assertTrue(readme.startswith('# repo\n\nExisting text.\n'))
        self.assertEqual(readme.count(sync_foundation.README_MARKER), 1)
        self.assertIn(OTHER_SHA[:12], readme)
        self.assertNotIn(SHA[:12], readme)

    def test_readme_text_after_the_generated_section_is_kept(self):
        (self.target / 'README.md').write_text('# repo\n')
        self.sync()
        with (self.target / 'README.md').open('a') as readme:
            readme.write('\nDesign documents: kept.\n')
        self.sync(sha=OTHER_SHA)
        self.assertTrue((self.target / 'README.md').read_text().endswith('\nDesign documents: kept.\n'))

    def test_gitignore_baseline_is_appended_under_a_heading_without_duplicates(self):
        (self.target / '.gitignore').write_text('.env\ncustom/\n')
        self.sync()
        self.sync()
        lines = (self.target / '.gitignore').read_text().splitlines()
        self.assertEqual(lines[:2], ['.env', 'custom/'])
        self.assertEqual(lines.count(sync_foundation.GITIGNORE_HEADING), 1)
        self.assertEqual(lines.count('.env'), 1)
        self.assertIn('__pycache__/', lines)

    def test_rejects_a_non_sha(self):
        with self.assertRaises(ValueError):
            sync_foundation.sync(ROOT, 'main', 'vinoguessr-web', self.target)


class EnsureDurableTests(unittest.TestCase):
    def run_compare(self, payload, returncode=0):
        result = subprocess.CompletedProcess([], returncode, stdout=json.dumps(payload), stderr='boom')
        with mock.patch.object(sync_foundation.subprocess, 'run', return_value=result):
            sync_foundation.ensure_durable(SHA)

    def test_accepts_a_sha_in_main_history(self):
        self.run_compare({'status': 'ahead', 'merge_base_commit': {'sha': SHA}})

    def test_rejects_an_unmerged_branch_sha(self):
        with self.assertRaises(RuntimeError):
            self.run_compare({'status': 'diverged', 'merge_base_commit': {'sha': OTHER_SHA}})

    def test_rejects_when_the_comparison_fails(self):
        with self.assertRaises(RuntimeError):
            self.run_compare({}, returncode=1)


if __name__ == '__main__':
    unittest.main()
