"""Prepare disposable provider test payloads. No network, credentials or live writes.

Plans are not evidence, permits or execution authorization. Production rulesets
are input only. Read the acceptance runbook before any separate admin operation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

PRODUCTION = "scnehaux/codex"
RULESET_ID = 23193929
APP_ID = 4864946
RUN_ID = re.compile(r"[0-9]{8}t[0-9]{6}z-[0-9a-f]{8}")
SHA = re.compile(r"[0-9a-f]{40}")
RULE_TYPES = {"deletion", "non_fast_forward", "required_linear_history",
              "pull_request", "required_status_checks"}
LIMIT = 128_000


class PlanError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise PlanError(code)


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def decode(raw: bytes) -> dict:
    require(0 < len(raw) <= LIMIT, "snapshot-size")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate-json-key")
            result[key] = value
        return result
    def invalid_constant(value):
        raise PlanError("non-finite-json")
    try:
        result = json.loads(raw, object_pairs_hook=unique,
                            parse_constant=invalid_constant)
    except (UnicodeError, ValueError) as exc:
        raise PlanError("snapshot-json") from exc
    require(isinstance(result, dict), "snapshot-object")
    return result


def validated_rules(snapshot: dict) -> dict[str, dict]:
    require(type(snapshot.get("id")) is int and snapshot["id"] == RULESET_ID,
            "source-ruleset-id")
    require(snapshot.get("source") == PRODUCTION and
            snapshot.get("source_type") == "Repository", "source-repository")
    require(snapshot.get("name") == "main-governance" and
            snapshot.get("target") == "branch" and
            snapshot.get("enforcement") == "active", "source-state")
    require(snapshot.get("bypass_actors") == [], "source-bypass")
    require(snapshot.get("conditions") == {
        "ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "source-selector")
    items = snapshot.get("rules")
    require(isinstance(items, list) and len(items) == len(RULE_TYPES), "source-rule-set")
    require(all(isinstance(item, dict) and isinstance(item.get("type"), str)
                for item in items), "source-rule-shape")
    rules = {item["type"]: deepcopy(item) for item in items}
    require(set(rules) == RULE_TYPES, "source-rule-types")
    p = rules["pull_request"].get("parameters", {})
    require(isinstance(p, dict), "review-parameters")
    require(type(p.get("required_approving_review_count")) is int and
            p["required_approving_review_count"] == 0, "review-bootstrap-changed")
    require(p.get("dismiss_stale_reviews_on_push") is True and
            p.get("required_review_thread_resolution") is True and
            p.get("require_code_owner_review") is False and
            p.get("require_last_push_approval") is False and
            p.get("allowed_merge_methods") == ["squash"], "review-policy-changed")
    q = rules["required_status_checks"].get("parameters", {})
    require(isinstance(q, dict), "check-parameters")
    require(q.get("strict_required_status_checks_policy") is True and
            q.get("do_not_enforce_on_create") is False, "check-policy-changed")
    checks = q.get("required_status_checks")
    require(isinstance(checks, list) and len(checks) == 2 and
            all(isinstance(c, dict) and isinstance(c.get("context"), str) for c in checks), "source-checks")
    by_context = {c.get("context"): c for c in checks}
    require(set(by_context) == {"Governance Qualification", "Codex Governance Authority"},
            "source-check-contexts")
    authority = by_context["Codex Governance Authority"]
    require(type(authority.get("integration_id")) is int and
            authority["integration_id"] == APP_ID, "authority-source-changed")
    return rules


def make_payload(snapshot: dict, *, name: str, selector: str, types: set[str]) -> dict:
    return {"name": name, "target": "branch", "enforcement": "active",
            "bypass_actors": [],
            "conditions": {"ref_name": {"include": [selector], "exclude": []}},
            "rules": [deepcopy(r) for r in snapshot["rules"] if r["type"] in types]}


def prepare(raw: bytes, revision: str, run_id: str) -> dict:
    require(isinstance(revision, str) and SHA.fullmatch(revision) is not None,
            "source-revision")
    require(isinstance(run_id, str) and RUN_ID.fullmatch(run_id) is not None, "run-id")
    snapshot = decode(raw)
    validated_rules(snapshot)
    target = "scnehaux/codex-provider-proof-" + run_id
    mirror = make_payload(snapshot, name="proof-mirror-" + run_id,
                          selector="~DEFAULT_BRANCH", types=RULE_TYPES)
    experiments = []
    for rule_type in ("deletion", "non_fast_forward", "pull_request"):
        experiments.append({
            "scope": "control-isolation-not-full-equivalence",
            "retained_rule_types": [rule_type],
            "omitted_rule_types": sorted(RULE_TYPES - {rule_type}),
            "selector_delta": "disposable named branch instead of default branch",
            "payload": make_payload(snapshot, name="proof-" + rule_type + "-" + run_id,
                                    selector="refs/heads/isolate-" + rule_type,
                                    types={rule_type}),
        })
    return {
        "schema_version": 1, "kind": "codex-provider-acceptance-plan",
        "state": "planned-not-executed",
        "source": {"repository": PRODUCTION, "revision": revision,
                   "ruleset_id": RULESET_ID, "snapshot_sha256": sha256(raw).hexdigest(),
                   "rules_sha256": sha256(canonical(snapshot["rules"])).hexdigest()},
        "target": {"repository": target, "repository_id": None,
                   "must_be_created_by_this_run": True, "reuse_existing": False,
                   "default_branch": "main", "content": "synthetic-fixtures-only"},
        "exact_mirror": {"scope": "disposable-default-branch", "payload": mirror,
                         "app_installation_must_not_be_widened": True},
        "isolation_experiments": experiments,
        "cleanup": {"mode": "archive-created-repository-after-evidence",
                    "requires_recorded_repository_id": True,
                    "production_mutations_allowed": False},
        "claims": {"live_tests_executed": False, "disposable_equivalence_proven": False,
                   "production_behavior_proven": False, "effective_enforcement_proven": False},
        "pending": ["admin-browser-authorization", "repository-identity-binding",
                    "full-rule-readback", "causal-negative-and-positive-controls",
                    "independent-reviewer-for-stale-approval", "production-parity-recheck",
                    "durable-observations-and-cleanup", "reviewed-phase10-acceptance"],
    }


def write_new(path: Path, data: dict) -> None:
    # Exclusive creation makes a resumed run inspect its previous plan, not replace it.
    require(not path.is_symlink(), "output-symlink")
    require(path.parent.is_dir(), "output-parent")
    with path.open("xb") as stream:
        stream.write(canonical(data) + b"\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-ruleset", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        require(args.source_ruleset.is_file() and not args.source_ruleset.is_symlink(),
                "snapshot-file")
        with args.source_ruleset.open("rb") as stream:
            raw = stream.read(LIMIT + 1)
        plan = prepare(raw, args.source_revision, args.run_id)
        write_new(args.output, plan)
    except (PlanError, OSError) as exc:
        print(json.dumps({"status": "blocked", "reason": type(exc).__name__,
                          "remote_mutations": 0}))
        return 2
    print(json.dumps({"status": "plan_prepared", "target": plan["target"]["repository"],
                      "plan_sha256": sha256(canonical(plan)).hexdigest(),
                      "remote_mutations": 0, "effective_enforcement_proven": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
