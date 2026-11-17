import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_deploy_confirmation', ROOT / 'bootstrap/sync_deploy_confirmation.py')
sync = importlib.util.module_from_spec(spec)
with mock.patch.object(sys, 'path', [str(ROOT / 'bootstrap'), *sys.path]):
    spec.loader.exec_module(sync)
SHA = 'a' * 40


class DeployConfirmationSyncTests(unittest.TestCase):
    def test_preserves_unrelated_rules_and_is_idempotent(self):
        before = '# Repository\n\n## Other rules\n\nKeep these bytes.\n\n'
        security = '## Security\n\n' + sync.OLD_APPROVAL + ' Do not expose credentials.\n\n'
        after = '## Repository specifics\n\nKeep custom settings. ' + sync.OLD_ENVIRONMENT + '\n'
        updated = sync.updated_agents(before + security + after, SHA, 'vinoguessr-api')
        self.assertTrue(updated.startswith(before))
        self.assertIn('Do not expose credentials.', updated)
        self.assertIn('Keep custom settings.', updated)
        self.assertIn('billed resources, `terraform apply`, and broad IAM grants require explicit approval', updated)
        self.assertIn('existing authentication, permissions, CI, and review gates remain in force', updated)
        self.assertIn(f'vinoguessr/.github@{SHA}', updated)
        self.assertEqual(sync.updated_agents(updated, SHA, 'vinoguessr-api'), updated)

    def test_updates_the_infrastructure_specific_approval_without_removing_other_guards(self):
        original = '## Security\n\n' + sync.OLD_APPROVAL + ' ' + sync.OLD_ENVIRONMENT + '\n\n## Specifics\n\n' + sync.OLD_INFRASTRUCTURE
        actual = sync.updated_agents(original, SHA, 'vinoguessr-infrastructure')
        self.assertIn('Do not run apply, billed resource creation, or broad IAM grants without explicit approval.', actual)
        self.assertNotIn('production deploys,', actual)

    def test_refuses_missing_or_ambiguous_policy(self):
        for text in ['custom policy', sync.OLD_CODING + sync.OLD_CODING]:
            with self.assertRaises(RuntimeError):
                sync.replace_policy(text, sync.OLD_CODING, sync.NEW_CODING)

    def test_does_not_write_agents_when_coding_policy_differs(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            agents = target / 'AGENTS.md'
            original = '## Security\n\n' + sync.OLD_APPROVAL + ' ' + sync.OLD_ENVIRONMENT + '\n'
            agents.write_text(original)
            coding = target / sync.CODING
            coding.parent.mkdir(parents=True)
            coding.write_text('custom coding policy')
            with self.assertRaises(RuntimeError):
                sync.sync(ROOT, SHA, 'vinoguessr-api', target)
            self.assertEqual(agents.read_text(), original)
            self.assertEqual(coding.read_text(), 'custom coding policy')


if __name__ == '__main__':
    unittest.main()
