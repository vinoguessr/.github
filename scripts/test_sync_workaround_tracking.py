import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_workaround_tracking', ROOT / 'bootstrap/sync_workaround_tracking.py')
sync = importlib.util.module_from_spec(spec)
with mock.patch.object(sys, 'path', [str(ROOT / 'bootstrap'), *sys.path]):
    spec.loader.exec_module(sync)
SHA = 'a' * 40


class WorkaroundSyncTests(unittest.TestCase):
    def test_preserves_other_rules_and_records_source(self):
        before = '# Project\r\n\r\n## Scope\r\n\r\nKeep this.\r\n\r\n'
        after = '## Security\n\nKeep secrets private.\n\n## Repository specifics\n\nKeep this too.\n'
        policy = '## Tracking workarounds\n\nUse the workaround label.\n'
        actual = sync.updated_agents(before + '## Tracking workarounds\n\nOld policy.\n\n' + after, policy, SHA)
        self.assertTrue(actual.startswith(before))
        self.assertTrue(actual.endswith(after))
        self.assertIn('Use the workaround label.', actual)
        self.assertIn(f'vinoguessr/.github@{SHA}', actual)
        self.assertEqual(sync.updated_agents(actual, policy, SHA), actual)

    def test_rejects_missing_or_ambiguous_sections(self):
        for original in ['# Project\n', '## Tracking workarounds\nx\n## Tracking workarounds\ny\n']:
            with self.assertRaises(RuntimeError):
                sync.updated_agents(original, 'new', SHA)

    def test_refuses_a_target_outside_the_selected_repository(self):
        with mock.patch.object(sync.subprocess, 'run', return_value=mock.Mock(returncode=0, stdout='https://github.com/other/repo.git\n')):
            with self.assertRaises(RuntimeError):
                sync.ensure_target_repository(Path('/tmp/target'), 'vinoguessr-api')
        for origin in ['https://github.com/vinoguessr/vinoguessr-api.git', 'git@github.com:vinoguessr/vinoguessr-api.git']:
            with mock.patch.object(sync.subprocess, 'run', return_value=mock.Mock(returncode=0, stdout=origin)):
                sync.ensure_target_repository(Path('/tmp/target'), 'vinoguessr-api')

    def test_preserves_agent_rules_when_existing_form_differs(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            agents = target / 'AGENTS.md'
            original = '## Tracking workarounds\n\nOld policy.\n'
            agents.write_text(original)
            form = target / sync.FORM
            form.parent.mkdir(parents=True)
            form.write_text('custom form')
            with self.assertRaises(RuntimeError):
                sync.sync(ROOT, SHA, target)
            self.assertEqual(agents.read_text(), original)
            self.assertEqual(form.read_text(), 'custom form')


if __name__ == '__main__':
    unittest.main()
