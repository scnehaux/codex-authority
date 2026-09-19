"""Validate recorded observations only; no network, approval, or live mutation."""
from datetime import datetime
import json
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'governance/evidence/provider-stale-review-001.json'


def strict_json(raw):
    def unique(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError('duplicate evidence key')
            data[key] = value
        return data
    def reject_constant(value):
        raise ValueError('non-finite evidence value')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


class ProviderStaleReviewEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = strict_json(PATH.read_bytes())

    def test_exact_accounts_and_fixture_identity(self):
        d = self.data
        self.assertEqual(d['schema_version'], 1)
        self.assertEqual(d['kind'], 'codex-provider-stale-review-observation')
        self.assertEqual(d['run_id'], '20260919t224050z-0478aef8')
        f = d['fixture']
        self.assertEqual(f['repository_id'], 1377674304)
        self.assertEqual(f['pull_request'], 1)
        self.assertEqual(f['author'], {'login': 'anshacerbia2', 'id': 108260133})
        self.assertEqual(f['reviewer'], {'login': 'scnehaux-org', 'id': 261198920, 'permission_at_review': 'write'})
        self.assertNotEqual(f['author']['id'], f['reviewer']['id'])

    def test_same_review_moves_from_approved_to_dismissed(self):
        before, after = self.data['before'], self.data['after']
        self.assertEqual(before['review_id'], 5258210954)
        self.assertEqual(before['review_id'], after['review_id'])
        self.assertEqual(before['review_state'], 'APPROVED')
        self.assertEqual(after['review_state'], 'DISMISSED')
        self.assertEqual(before['review_commit_id'], before['head_sha'])
        self.assertEqual(after['review_commit_id'], before['head_sha'])
        self.assertEqual(self.data['result'], 'OBSERVED_AUTOMATIC_DISMISSAL')

    def test_reviewable_forward_change_keeps_base_fixed(self):
        d = self.data
        self.assertEqual(d['before']['base_sha'], d['after']['base_sha'])
        self.assertEqual(d['change']['parent_sha'], d['before']['head_sha'])
        self.assertEqual(d['change']['new_head_sha'], d['after']['head_sha'])
        self.assertNotEqual(d['before']['head_sha'], d['after']['head_sha'])
        self.assertNotEqual(d['before']['fixture_content_after_baseline'], d['change']['fixture_content_after_change'])
        self.assertEqual(d['fixture']['changed_files'], ['fixture.txt'])
        self.assertIs(d['change']['force'], False)
        self.assertEqual(d['change']['status'], 200)

    def test_provider_event_binds_dismissal_to_new_commit(self):
        d, event = self.data, self.data['provider_event']
        self.assertEqual(event['id'], 31463296946)
        self.assertEqual(event['event'], 'review_dismissed')
        self.assertEqual(event['review_id'], d['before']['review_id'])
        self.assertEqual(event['dismissal_commit_id'], d['after']['head_sha'])
        self.assertEqual(event['prior_state'], 'approved')
        self.assertIsNone(event['dismissal_message'])
        self.assertLess(instant(d['before']['review_submitted_at']), instant(d['before']['recorded_at']))
        self.assertLess(instant(d['before']['recorded_at']), instant(event['created_at']))
        self.assertLess(instant(event['created_at']), instant(d['after']['recorded_at']))
        self.assertEqual([p['state'] for p in d['after']['polls']], ['APPROVED', 'DISMISSED'])

    def test_zero_approval_policy_and_isolation_are_explicit(self):
        d = self.data
        p = d['source']['copied_rule']['parameters']
        self.assertIs(p['dismiss_stale_reviews_on_push'], True)
        self.assertEqual(p['required_approving_review_count'], 0)
        self.assertEqual(d['fixture']['enforcement'], 'active')
        self.assertEqual(d['fixture']['bypass_actors'], [])
        self.assertEqual(d['fixture']['only_copied_rule'], 'pull_request')
        self.assertEqual(len(d['fixture']['omitted_rule_types']), 4)
        self.assertIs(d['fixture']['rule_matches_source_before_and_after'], True)
        self.assertIs(d['after']['merge_blocking_test_performed'], False)

    def test_cleanup_preserves_history_without_write_grant(self):
        c = self.data['cleanup']
        self.assertIs(c['pr_closed_without_merge'], True)
        self.assertEqual(c['open_prs'], 0)
        self.assertIs(c['direct_collaborator_grant_removed'], True)
        self.assertEqual(c['removal_http_status'], 204)
        self.assertEqual(c['permission_after_removal'], 'read')
        self.assertIs(c['organization_or_team_membership_changed'], False)
        self.assertIs(c['repository_archived'], True)
        self.assertIs(c['repository_deleted'], False)
        self.assertIs(c['fixture_main_unchanged'], True)

    def test_production_and_completion_claims_remain_conservative(self):
        d, claims = self.data, self.data['claims']
        self.assertEqual(d['source']['revision_before'], d['source']['revision_after'])
        self.assertEqual(d['source']['ruleset_id'], 23193929)
        self.assertIs(d['source']['complete_production_ruleset_unchanged'], True)
        self.assertIs(claims['stale_approval_dismissal_observed_in_fixture'], True)
        self.assertIs(claims['distinct_account_review_observed'], True)
        for key in ('independent_human_review_proven', 'production_mutations_performed', 'full_mirror_equivalence_proven', 'effective_enforcement_proven'):
            self.assertIs(claims[key], False)
        self.assertIs(d['after']['approval_submitted_by_assistant'], False)
        self.assertIs(d['after']['manual_dismissal_performed'], False)

    def test_capture_references_and_data_parser(self):
        capture = self.data['operator_capture']
        self.assertEqual(capture['request_outcome_pairs'], 80)
        self.assertEqual(capture['sequence_first'], '0001')
        self.assertEqual(capture['sequence_last'], '0080')
        self.assertEqual(len(capture['snapshot_files']), 4)
        self.assertEqual(strict_json(PATH.read_bytes().replace(b'\n', b'\r\n')), self.data)
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                strict_json(raw)


if __name__ == '__main__':
    unittest.main()
