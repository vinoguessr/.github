import importlib.util
import unittest

import yaml
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('provision', ROOT / 'bootstrap/provision.py')
provision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provision)


class ProvisionConfigurationTests(unittest.TestCase):
    def test_every_repository_has_an_area_and_required_checks(self):
        for repo in provision.REPOS:
            self.assertIn(repo, provision.AREA_BY_REPO)
            self.assertTrue(provision.REQUIRED_CHECKS[repo])

    def test_area_field_options_match_repositories(self):
        areas = dict(provision.FIELDS)['Area']
        self.assertEqual(sorted(areas), sorted(provision.AREA_BY_REPO.values()))

    def test_path_filtered_atlas_check_is_not_required(self):
        self.assertNotIn('diff', provision.REQUIRED_CHECKS['vinoguessr-api'])

    def test_every_non_foundation_repository_requires_policy_and_lockfile_checks(self):
        for repo in provision.REPOS:
            if repo == '.github':
                continue
            self.assertIn('policy / Repository policy', provision.REQUIRED_CHECKS[repo])
            self.assertIn('Verify action dependency provenance', provision.REQUIRED_CHECKS[repo])


class RulesetPayloadTests(unittest.TestCase):
    def test_protects_main_with_pr_and_checks_without_bypass(self):
        payload = provision.ruleset_payload(['lint'])
        self.assertEqual(payload['conditions']['ref_name']['include'], ['refs/heads/main'])
        self.assertEqual(payload['bypass_actors'], [])
        types = [rule['type'] for rule in payload['rules']]
        self.assertEqual(types, ['deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'])

    def test_single_owner_can_merge_after_resolving_threads(self):
        pr = next(r for r in provision.ruleset_payload(['lint'])['rules'] if r['type'] == 'pull_request')
        self.assertEqual(pr['parameters']['required_approving_review_count'], 0)
        self.assertTrue(pr['parameters']['required_review_thread_resolution'])
        self.assertEqual(pr['parameters']['allowed_merge_methods'], ['squash'])

    def test_required_checks_are_bound_to_github_actions(self):
        checks = next(r for r in provision.ruleset_payload(['lint', 'test'])['rules']
                      if r['type'] == 'required_status_checks')['parameters']['required_status_checks']
        self.assertEqual([c['context'] for c in checks], ['lint', 'test'])
        self.assertTrue(all(c['integration_id'] == provision.GITHUB_ACTIONS_APP_ID for c in checks))

    def test_rejects_ruleset_without_checks(self):
        with self.assertRaises(ValueError):
            provision.ruleset_payload([])


class RepositorySettingsTests(unittest.TestCase):
    def test_squash_only_and_secret_scanning(self):
        settings = provision.repository_settings()
        self.assertTrue(settings['allow_squash_merge'])
        self.assertFalse(settings['allow_merge_commit'])
        self.assertFalse(settings['allow_rebase_merge'])
        self.assertEqual(settings['security_and_analysis']['secret_scanning_push_protection'], {'status': 'enabled'})


class ItemsStageTests(unittest.TestCase):
    def test_existing_area_is_not_overwritten_and_pull_requests_are_skipped(self):
        state = {'project': {'id': 'P', 'number': 1}}
        fields = {'fields': [{'name': 'Area', 'id': 'F', 'options': [
            {'name': area, 'id': f'O-{area}'} for area in provision.AREA_BY_REPO.values()]}]}
        existing = {'items': [{'id': 'I1', 'area': 'docs',
                               'content': {'url': 'https://github.com/vinoguessr/vinoguessr-api/issues/1'}}]}
        issues = {f'repos/vinoguessr/{repo}/issues?state=open': [] for repo in provision.REPOS}
        issues['repos/vinoguessr/vinoguessr-api/issues?state=open'] = [
            {'html_url': 'https://github.com/vinoguessr/vinoguessr-api/issues/1'},
            {'html_url': 'https://github.com/vinoguessr/vinoguessr-api/pull/2', 'pull_request': {}},
            {'html_url': 'https://github.com/vinoguessr/vinoguessr-api/issues/3'},
        ]
        calls = []

        def fake_gh(*args, data=None):
            calls.append(args)
            if args[:2] == ('project', 'field-list'):
                return fields
            if args[:2] == ('project', 'item-list'):
                return existing
            if args[:2] == ('project', 'item-add'):
                return {'id': 'I3'}
            return None

        with mock.patch.object(provision, 'gh', side_effect=fake_gh), \
                mock.patch.object(provision, 'pages', side_effect=lambda path: issues[path]), \
                mock.patch.object(provision, 'save'):
            provision.items(state, provision.REPOS)

        added = [a for a in calls if a[:2] == ('project', 'item-add')]
        edited = [a for a in calls if a[:2] == ('project', 'item-edit')]
        self.assertEqual(len(added), 1)
        self.assertIn('https://github.com/vinoguessr/vinoguessr-api/issues/3', added[0])
        self.assertEqual(len(edited), 1)
        self.assertIn('I3', edited[0])
        self.assertIn('O-api', edited[0])
        self.assertNotIn('https://github.com/vinoguessr/vinoguessr-api/pull/2', state['items'])


def job_names(path):
    data = yaml.load(path.read_text(), Loader=WorkflowLoader)
    return {job.get('name', job_id) for job_id, job in data['jobs'].items()}


class WorkflowLoader(yaml.SafeLoader):
    pass


WorkflowLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values if tag != 'tag:yaml.org,2002:bool']
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class RequiredCheckNameTests(unittest.TestCase):
    """A renamed job silently blocks every merge, so required names must match the workflows."""

    def test_foundation_checks_match_job_names(self):
        names = set()
        for path in (ROOT / '.github/workflows').glob('*.yml'):
            if not path.name.startswith('reusable-'):
                names |= job_names(path)
        for check in provision.REQUIRED_CHECKS['.github']:
            self.assertIn(check, names)

    def test_reusable_check_suffixes_match_reusable_job_names(self):
        reusable = {
            'policy': ROOT / '.github/workflows/reusable-repository.yml',
            'swift': ROOT / '.github/workflows/reusable-swift.yml',
            'terraform': ROOT / '.github/workflows/reusable-terraform.yml',
        }
        for repo, checks in provision.REQUIRED_CHECKS.items():
            for check in checks:
                if ' / ' not in check:
                    continue
                caller, job = check.split(' / ', 1)
                with self.subTest(repo=repo, check=check):
                    self.assertIn(caller, reusable)
                    self.assertIn(job, job_names(reusable[caller]))

    def test_lockfile_check_matches_verify_workflow(self):
        self.assertIn('Verify action dependency provenance', job_names(ROOT / '.github/workflows/verify-lockfile.yml'))


class RulesetsStageTests(unittest.TestCase):
    def run_stage(self, observed, existing):
        calls = []

        def fake_api(path, method='GET', data=None):
            calls.append((method, path))
            if path.endswith('/rulesets?includes_parents=false'):
                return existing
            if method in ('PUT', 'POST'):
                return {'id': 99}
            raise AssertionError(path)

        with mock.patch.object(provision, 'observed_checks', return_value=observed), \
                mock.patch.object(provision, 'api', side_effect=fake_api), \
                mock.patch.object(provision, 'save'):
            provision.rulesets({}, ['vinoguessr-docs'])
        return calls

    def test_refuses_when_a_required_check_has_not_run(self):
        with mock.patch.object(provision, 'observed_checks', return_value={'policy / Repository policy'}), \
                mock.patch.object(provision, 'api') as api:
            with self.assertRaises(RuntimeError) as raised:
                provision.rulesets({}, ['vinoguessr-docs'])
        self.assertIn('Verify action dependency provenance', str(raised.exception))
        api.assert_not_called()

    def test_updates_existing_repository_ruleset(self):
        observed = set(provision.REQUIRED_CHECKS['vinoguessr-docs'])
        calls = self.run_stage(observed, [{'id': 7, 'name': provision.RULESET_NAME}])
        self.assertIn(('PUT', 'repos/vinoguessr/vinoguessr-docs/rulesets/7'), calls)

    def test_creates_ruleset_when_none_exists(self):
        observed = set(provision.REQUIRED_CHECKS['vinoguessr-docs'])
        calls = self.run_stage(observed, [{'id': 7, 'name': 'Other'}])
        self.assertIn(('POST', 'repos/vinoguessr/vinoguessr-docs/rulesets'), calls)


class ProjectItemTests(unittest.TestCase):
    def test_recovers_when_github_reports_content_already_exists(self):
        url = 'https://github.com/vinoguessr/vinoguessr-api/issues/1'

        def fake_gh(*args, data=None):
            if args[:2] == ('project', 'item-add'):
                raise RuntimeError('project item-add: Content already exists in this project')
            if args[:2] == ('project', 'item-list'):
                return {'items': [{'id': 'I1', 'content': {'url': url}}]}
            raise AssertionError(args)

        with mock.patch.object(provision, 'gh', side_effect=fake_gh):
            self.assertEqual(provision.project_item('1', url, {})['id'], 'I1')

    def test_other_add_errors_propagate(self):
        with mock.patch.object(provision, 'gh', side_effect=RuntimeError('project item-add: forbidden')):
            with self.assertRaises(RuntimeError):
                provision.project_item('1', 'https://github.com/vinoguessr/vinoguessr-api/issues/1', {})

    def test_missing_area_option_names_the_option(self):
        with self.assertRaises(RuntimeError) as raised:
            provision.area_option({'options': [{'name': 'api', 'id': 'O'}]}, 'vinoguessr-docs')
        self.assertIn("'docs'", str(raised.exception))


if __name__ == '__main__':
    unittest.main()
