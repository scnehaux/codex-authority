"""Integrity and scope checks over recorded live observations; never runs live tests."""
from hashlib import sha256
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'governance' / 'evidence'


def serialized_response(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate evidence key')
            value[key] = item
        return value
    data = json.loads(raw, object_pairs_hook=unique)
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii') + b'\n'


class ProviderNegativeObservationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((BASE / 'provider-negative-001.json').read_bytes())
        cls.raw = (BASE / cls.data['response_artifact']['path']).read_bytes()
        cls.records = json.loads(cls.raw)['records']
        cls.by_id = {r['sequence']: r for r in cls.records}

    def record(self, number):
        return self.by_id[f'{number:04d}']

    def body(self, number):
        return self.record(number)['response']['body_projection']

    def test_checkout_line_endings_preserve_data_digest(self):
        expected = self.data['response_artifact']['sha256']
        self.assertEqual(sha256(serialized_response(self.raw.replace(b'\n', b'\r\n'))).hexdigest(), expected)
        changed = json.loads(self.raw)
        changed['records'][0]['response']['http_status'] = 201
        self.assertNotEqual(sha256(serialized_response(json.dumps(changed).encode())).hexdigest(), expected)

    def test_duplicate_evidence_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            serialized_response(b'{"a":1,"a":2}')

    def test_response_digest_and_complete_request_pairs(self):
        self.assertEqual(sha256(serialized_response(self.raw)).hexdigest(), self.data['response_artifact']['sha256'])
        self.assertEqual(len(self.records), self.data['response_artifact']['record_count'])
        self.assertEqual(len(self.by_id), len(self.records))
        self.assertEqual(list(self.by_id), [f'{i:04d}' for i in range(1, 167)])
        for r in self.records:
            self.assertIsInstance(r['response']['http_status'], int)
            self.assertTrue(r['response']['headers'].get('x-github-request-id'))

    def test_no_production_mutations_or_repository_deletion(self):
        fixture = self.data['fixture']['full_name']
        for r in self.records:
            method, endpoint = r['intent']['method'], r['intent']['endpoint']
            if method == 'GET':
                continue
            if endpoint == 'orgs/scnehaux/repos':
                self.assertEqual(r['intent']['body']['name'], fixture.split('/')[1])
            elif endpoint == 'graphql':
                q = r['intent']['body']['query']
                self.assertTrue(fixture.split('/')[1] in q or self.data['thread_test']['thread_id'] in q)
            else:
                self.assertTrue(endpoint == 'repos/' + fixture or endpoint.startswith('repos/' + fixture + '/'))
                self.assertFalse(method == 'DELETE' and endpoint == 'repos/' + fixture)

    def test_exact_mirror_failure_is_not_counted_as_equivalence(self):
        self.assertEqual(self.record(40)['response']['http_status'], 422)
        self.assertIn('Invalid integration ids', str(self.body(40)))
        self.assertEqual(self.data['full_mirror']['status'], 'BLOCKED')
        self.assertIs(self.data['claims']['full_mirror_equivalence_proven'], False)
        self.assertIs(self.data['claims']['authority_app_scope_widened'], False)

    def test_production_rules_and_revision_are_unchanged(self):
        source = self.data['source']
        self.assertEqual(source['ruleset_before'], source['ruleset_after'])
        self.assertEqual(source['effective_rules_before'], source['effective_rules_after'])
        self.assertEqual(self.body(2)['object']['sha'], self.body(163)['object']['sha'])
        self.assertEqual(source['ruleset_before']['bypass_actors'], [])
        self.assertIs(source['main_unchanged'], True)
        self.assertIs(self.data['claims']['production_mutations_performed'], False)

    def test_direct_update_denial_has_same_actor_positive_control(self):
        self.assertEqual(self.record(55)['response']['http_status'], 200)
        self.assertEqual(self.record(59)['response']['http_status'], 422)
        self.assertIn('pull request', self.body(59)['message'])
        self.assertEqual(self.body(57)['object']['sha'], self.body(60)['object']['sha'])
        self.assertIs(self.record(59)['intent']['body']['force'], False)

    def test_real_non_fast_forward_denial_and_positive_controls(self):
        self.assertEqual(self.record(67)['response']['http_status'], 200)
        self.assertEqual(self.record(71)['response']['http_status'], 200)
        self.assertEqual(self.record(74)['response']['http_status'], 422)
        self.assertIn('Cannot force-push', self.body(74)['message'])
        self.assertIs(self.record(74)['intent']['body']['force'], True)
        target = self.record(74)['intent']['body']['sha']
        self.assertEqual(self.body(65)['parents'][0]['sha'], target)
        self.assertEqual(self.body(72)['object']['sha'], self.body(75)['object']['sha'])
        self.assertNotEqual(self.body(75)['object']['sha'], target)

    def test_custom_and_native_deletion_observations_are_distinct(self):
        self.assertEqual(self.record(77)['response']['http_status'], 204)
        self.assertEqual(self.record(80)['response']['http_status'], 422)
        self.assertIn('Cannot delete this branch', self.body(80)['message'])
        self.assertEqual(self.body(83), [])
        self.assertIn('default branch', self.body(85)['message'])
        self.assertIs(self.data['ref_tests']['default-branch-deletion']['custom_ruleset_attribution'], False)

    def test_unresolved_thread_denies_then_same_candidate_merges(self):
        self.assertEqual(self.record(97)['response']['http_status'], 405)
        self.assertIn('conversation must be resolved', self.body(97)['message'])
        self.assertIs(self.body(101)['data']['resolveReviewThread']['thread']['isResolved'], True)
        self.assertIs(self.body(104)['merged'], True)
        self.assertEqual(self.record(97)['intent']['body'], self.record(104)['intent']['body'])

    def test_ruleset_merge_methods_not_repository_settings_block(self):
        self.assertTrue(all(self.body(106)[k] for k in ['allow_merge_commit', 'allow_squash_merge', 'allow_rebase_merge']))
        self.assertEqual(self.body(118), [])
        self.assertEqual(self.record(120)['response']['http_status'], 405)
        self.assertEqual(self.record(123)['response']['http_status'], 405)
        self.assertIs(self.body(126)['merged'], True)
        heads = [self.record(n)['intent']['body']['sha'] for n in [120, 123, 126]]
        self.assertEqual(len(set(heads)), 1)
        self.assertEqual(self.data['merge_methods']['approval_reviews_observed'], 0)

    def test_failure_and_success_status_use_same_candidate(self):
        self.assertEqual(self.record(143)['intent']['body']['state'], 'failure')
        self.assertEqual(self.record(150)['intent']['body']['state'], 'success')
        self.assertEqual(self.record(143)['intent']['endpoint'], self.record(150)['intent']['endpoint'])
        self.assertIn('Provider Proof Qualification', self.body(146)['message'])
        self.assertEqual(self.record(146)['response']['http_status'], 405)
        self.assertIs(self.body(154)['merged'], True)
        self.assertEqual(self.record(146)['intent']['body'], self.record(154)['intent']['body'])
        self.assertIs(self.data['failing_check']['real_codex_qualification_test'], False)
        self.assertIs(self.data['failing_check']['dedicated_app_authority_test'], False)

    def test_cleanup_archives_only_fixture_with_no_open_prs(self):
        fixture_id = self.data['fixture']['id']
        self.assertEqual(fixture_id, 1377645819)
        self.assertEqual(self.body(156), [])
        self.assertEqual(self.body(160)['id'], fixture_id)
        self.assertIs(self.body(160)['archived'], True)
        self.assertIs(self.body(161)['archived'], True)
        self.assertIs(self.data['cleanup']['repository_deleted'], False)

    def test_missing_reviewer_and_completion_are_not_overclaimed(self):
        self.assertEqual(self.data['stale_review']['status'], 'PENDING_NONAUTHOR_REVIEWER')
        self.assertIs(self.data['stale_review']['approval_created'], False)
        self.assertIs(self.data['claims']['stale_approval_proven'], False)
        self.assertIs(self.data['claims']['effective_enforcement_proven'], False)
        self.assertIn('behavioral enforcement proof: NOT CLAIMED', self.data['production_observer']['stdout'])


if __name__ == '__main__':
    unittest.main()
