#!/usr/bin/env python3
"""Prepare evidence + receipt before exporting a controlled publication permit.

No publisher credential, network-write option, or caller-selected facts/source pin.
Both public preparation gates remain disabled in checked-in Authority governance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.attested_contract import REPOSITORY, sha
from codex_authority.attested_handover import _write_bound, prepare_attested_permit
from codex_authority.controlled_evidence import prepare_bootstrap_permit
from codex_authority.model import CandidateRef


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("bootstrap-v1", "attested-v2"), required=True)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--evidence-out", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    parser.add_argument("--permit-out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        request = CandidateRef(REPOSITORY, args.pull_request, sha(args.head_sha))
        prepare = prepare_bootstrap_permit if args.mode == "bootstrap-v1" else prepare_attested_permit
        result = prepare(request, args.runtime_dir, args.evidence_out, args.receipt_out)
        if result.permit is None:
            print(json.dumps({"status": "blocked", "reasons": list(result.outcome.reasons),
                              "evidence_recorded": result.outcome.evidence_recorded}))
            return 2
        _write_bound(args.permit_out, result.permit.to_mapping())
        print(json.dumps({"status": "controlled_permit_prepared", "mode": args.mode,
                          "permit_digest": result.permit.digest,
                          "evidence_sha256": result.evidence_digest,
                          "receipt_sha256": result.receipt_digest,
                          "publication_performed": False, "effective_enforcement_proven": False}, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"status": "blocked", "message": "Controlled permit preparation failed closed; no publication was performed."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
