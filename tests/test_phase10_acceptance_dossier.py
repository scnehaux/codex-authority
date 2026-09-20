"""Validate a proposed historical dossier. No provider requests or acceptance writes.

Git is used only to read eight bounded, pinned local objects. This is not a new
runtime policy engine; passing tests do not authorize a phase transition.
"""
from copy import deepcopy
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / 'governance/evidence/phase10-acceptance-dossier-001.json'
ANCHOR = 'c21caa337fc70c44feef9f4920658e641c31a970'
CODEX = '107f0dc53e873ef6d24a9f12cd28da7348f79331'
LIMIT = 64000
PINS = {
    'isolated': ('provider-negative-001.json', 'bc69b86743bc366072215b345a0d03b8240833b9'),
    'native_git': ('provider-git-transport-001.json', '120270fe584ded7972e970e96bc33d36c3e70f7f'),
    'qualification': ('provider-qualification-negative-001.json', '29557244841665b5116dbebcf9989bccf35a4a30'),
    'runtime': ('provider-qualification-negative-001.runtime.json', '662883622642315e05b7ac72fa2f58c3a5c0f69f'),
    'stale_review': ('provider-stale-review-001.json', '1a52b9698b126311ed43246640fe492474e87e31'),
    'missing_authority': ('provider-enforcement-001.json', 'e7e48d7d16cfbebd483007244cb6dd77085459a4'),
    'wrong_source': ('provider-wrong-source-001.json', 'a3530cc0227c6584f3cb361dc90fff12916c1e2e'),
    'maintenance': ('permanent-maintenance-proof-001.json', '48fa70d93461e3b7b773ea3669445f5443f13023'),
}
OBLIGATIONS = (
    'direct-push', 'force-push', 'default-deletion', 'failing-qualification',
    'bootstrap-review', 'unresolved-thread', 'stale-review', 'merge-method',
    'configuration-parity', 'neutral-semantics',
)
CLAIMS = {
    'phase10_acceptance_completed', 'effective_enforcement_proven',
    'full_mirror_equivalence_proven', 'independent_human_review_proven',
    'new_live_behavior_tests_performed', 'production_configuration_changed',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def strict_json(raw):
    require(0 < len(raw) <= LIMIT, 'data-size')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate-key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('non-finite-value')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def validate_index(data):
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'version')
    require(data['kind'] == 'codex-phase10-acceptance-dossier', 'kind')
    require(data['state'] == 'proposed-awaiting-owner-decision', 'state')
    require(data['baselines'] == {
        'authority_repository': 'scnehaux/codex-authority', 'authority_revision': ANCHOR,
        'codex_repository': 'scnehaux/codex', 'codex_revision': CODEX}, 'baselines')
    require(data['method'] == {
        'recommendation': 'REC-D-018', 'status': 'Proposed', 'owner_decision': None,
        'full_mirror_status': 'BLOCKED', 'full_mirror_reason': 'Invalid integration ids',
        'requires_explicit_scope_transfer': True, 'requirement_waiver': False}, 'method')
    require(data['method']['requires_explicit_scope_transfer'] is True
            and data['method']['requirement_waiver'] is False, 'method-types')
    require(set(data['claims']) == CLAIMS
            and all(value is False for value in data['claims'].values()), 'claims')
    expected = {key: {'path': 'governance/evidence/' + path, 'git_blob': blob}
                for key, (path, blob) in PINS.items()}
    require(data['source_inventory'] == expected, 'source-inventory')
    rows = data['rows']
    require(type(rows) is list and len(rows) == 10, 'rows')
    for number, (row, obligation) in enumerate(zip(rows, OBLIGATIONS), 1):
        require(type(row['id']) is int and row['id'] == number, 'row-id')
        require(row['obligation'] == obligation, 'obligation')
        require(row['assessment'] == 'evidence-mapped-not-accepted', 'row-assessment')
        refs = row['evidence_sources']
        require(type(refs) is list and bool(refs) and len(refs) == len(set(refs))
                and all(ref in PINS for ref in refs), 'row-sources')
        require(all(type(row[key]) is str and bool(row[key].strip())
                    for key in ('observation', 'limit')), 'row-explanation')
    require(data['remaining_gates'] == [
        'owner-rec-d-018-scope-decision', 'fresh-complete-source-policy-cleanup-preflight',
        'governed-finalization-and-unchanged-ci'], 'remaining-gates')
    return data


def pinned_source(key):
    path, expected = PINS[key]
    spec = ANCHOR + ':governance/evidence/' + path
    def git(*args):
        return subprocess.run(
            ['git', '--no-replace-objects', '-C', str(ROOT), 'cat-file', *args],
            check=True, capture_output=True, timeout=10).stdout
    size = int(git('-s', spec).strip())
    require(0 < size <= LIMIT, 'object-size')
    raw = git('blob', spec)
    require(len(raw) == size and sha1(f'blob {size}\0'.encode() + raw).hexdigest()
            == expected, 'object-identity')
    return strict_json(raw)


class DossierIndexTests(unittest.TestCase):
    def setUp(self):
        self.data = strict_json(DOSSIER.read_bytes())

    def test_all_ten_obligations_are_mapped_not_accepted(self):
        validate_index(self.data)

    def test_missing_duplicate_and_boolean_row_ids_rejected(self):
        for operation in ('missing', 'duplicate', 'boolean'):
            data = deepcopy(self.data)
            if operation == 'missing': data['rows'].pop()
            if operation == 'duplicate': data['rows'][1] = data['rows'][0]
            if operation == 'boolean': data['rows'][0]['id'] = True
            with self.assertRaises(ValueError): validate_index(data)

    def test_unknown_sources_and_paths_rejected(self):
        data = deepcopy(self.data)
        data['rows'][0]['evidence_sources'] = ['invented']
        with self.assertRaises(ValueError): validate_index(data)
        data = deepcopy(self.data)
        data['source_inventory']['runtime']['path'] = '../runtime.json'
        with self.assertRaises(ValueError): validate_index(data)

    def test_source_pin_mutation_rejected(self):
        self.data['source_inventory']['runtime']['git_blob'] = '0' * 40
        with self.assertRaises(ValueError): validate_index(self.data)

    def test_unrecorded_owner_approval_cannot_be_inferred(self):
        self.data['method']['owner_decision'] = {'status': 'accepted'}
        with self.assertRaises(ValueError): validate_index(self.data)

    def test_scope_waiver_and_mirror_success_rejected(self):
        for key, value in [('requirement_waiver', True), ('full_mirror_status', 'PASS')]:
            data = deepcopy(self.data); data['method'][key] = value
            with self.assertRaises(ValueError): validate_index(data)

    def test_completion_flags_and_numeric_false_rejected(self):
        for value in (True, 0):
            data = deepcopy(self.data); data['claims']['effective_enforcement_proven'] = value
            with self.assertRaises(ValueError): validate_index(data)

    def test_accepted_row_and_erased_limit_rejected(self):
        for key, value in [('assessment', 'accepted'), ('limit', '')]:
            data = deepcopy(self.data); data['rows'][0][key] = value
            with self.assertRaises(ValueError): validate_index(data)

    def test_strict_parser_rejects_duplicates_nonfinite_and_oversize(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b' ' * (LIMIT + 1)):
            with self.assertRaises(ValueError): strict_json(raw)

    def test_outer_checkout_line_endings_do_not_change_json_data(self):
        self.assertEqual(strict_json(DOSSIER.read_bytes().replace(b'\n', b'\r\n')), self.data)


class DossierSourceLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = validate_index(strict_json(DOSSIER.read_bytes()))
        cls.sources = {key: pinned_source(key) for key in PINS}

    def test_current_evidence_data_matches_immutable_sources(self):
        for key, item in self.d['source_inventory'].items():
            current = strict_json((ROOT / item['path']).read_bytes())
            self.assertEqual(canonical(current), canonical(self.sources[key]))

    def test_qualification_to_runtime_to_refusal_is_bound(self):
        q, r = self.sources['qualification'], self.sources['runtime']
        self.assertEqual(q['candidate']['head_sha'], r['decision_record']['request']['head_sha'])
        self.assertEqual(q['candidate']['head_sha'], q['merge_attempt']['body']['sha'])
        self.assertEqual(q['issuer']['decision'], 'fail')
        self.assertEqual(r['decision_record']['reasons'], ['candidate-qualification-failed'])
        self.assertIs(q['issuer']['permit_issued'], False)
        self.assertEqual(q['merge_attempt']['http_status'], 405)
        self.assertIs(q['merge_attempt']['qualification_only_causal_isolation'], False)
        self.assertEqual(sha256(r['runtime_result_json'].encode()).hexdigest(), r['runtime_result_sha256'])

    def test_native_git_and_rest_deletion_claims_remain_distinct(self):
        g, i = self.sources['native_git'], self.sources['isolated']
        self.assertIs(g['claims']['native_direct_update_denial_observed_in_fixture'], True)
        self.assertIs(g['claims']['native_non_fast_forward_denial_observed_in_fixture'], True)
        self.assertIs(g['claims']['native_default_deletion_proven'], False)
        self.assertEqual(i['ref_tests']['default-branch-deletion']['status'], 'OBSERVED_NATIVE_GUARD_ONLY')
        self.assertIs(i['ref_tests']['default-branch-deletion']['custom_ruleset_attribution'], False)
        self.assertIs(g['final_native_deletion_sequence']['proof_credit'], False)

    def test_stale_review_is_later_evidence_not_a_rewrite(self):
        i, s = self.sources['isolated'], self.sources['stale_review']
        self.assertEqual(i['stale_review']['status'], 'PENDING_NONAUTHOR_REVIEWER')
        self.assertEqual(s['result'], 'OBSERVED_AUTOMATIC_DISMISSAL')
        self.assertEqual(s['before']['review_id'], s['after']['review_id'])
        self.assertEqual(s['provider_event']['dismissal_commit_id'], s['after']['head_sha'])
        self.assertIs(s['claims']['independent_human_review_proven'], False)
        self.assertIs(s['after']['merge_blocking_test_performed'], False)

    def test_source_bound_negatives_and_maintenance_are_separate(self):
        for key in ('missing_authority', 'wrong_source'):
            self.assertEqual(self.sources[key]['negative_proof']['mergeable_state'], 'blocked')
        m = self.sources['maintenance']
        self.assertIs(m['provider_enforcement']['merge_completed'], True)
        self.assertIs(m['authority']['bootstrap_enabled'], False)
        self.assertEqual(m['publication']['app']['id'], 4864946)

    def test_configuration_recheck_matches_original_but_is_not_complete_preflight(self):
        observed = self.d['connector_recheck']
        original = self.sources['isolated']['source']['ruleset_after']
        self.assertEqual(observed['ruleset_id'], original['id'])
        self.assertEqual(observed['rule_types'], [r['type'] for r in original['rules']])
        self.assertEqual(observed['required_status_checks'], original['rules'][-1]['parameters']['required_status_checks'])
        self.assertEqual(observed['required_approving_review_count'], 0)
        self.assertIs(observed['complete_live_preflight'], False)
        self.assertIs(observed['observer_reexecuted'], False)
        self.assertTrue(all(f['archived'] is True for f in observed['fixture_archives']))
        self.assertEqual([f['id'] for f in observed['fixture_archives']], [1377645819, 1377674304, 1378442804])

    def test_exact_main_ci_is_historical_success_not_a_new_execution(self):
        ci = self.d['exact_main_ci']
        self.assertEqual(ci['head_sha'], CODEX)
        self.assertEqual(ci['run_id'], 35466444121)
        self.assertEqual(ci['job_id'], 105959532913)
        self.assertEqual(ci['conclusion'], 'success')
        self.assertEqual(ci['qualify_governance_control_plane'], 'success')
        self.assertIs(ci['reexecuted'], False)
        self.assertEqual(len(self.d['external_source_anchors']), 2)
        self.assertTrue(all(s['revision'] == CODEX for s in self.d['external_source_anchors']))


if __name__ == '__main__':
    unittest.main()
