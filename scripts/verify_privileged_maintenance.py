from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.privileged import (  # noqa: E402
    PrivilegedMaintenanceError,
    PrivilegedValidationAttestation,
    load_maintenance_policy,
)

POLICY = ROOT / "governance" / "privileged-maintenance.json"
ATTESTATION_DIR = ROOT / "governance" / "privileged-validations"


def main() -> int:
    try:
        policy = load_maintenance_policy(POLICY)
    except PrivilegedMaintenanceError as exc:
        raise SystemExit(f"privileged-maintenance policy invalid: {exc}") from None

    if not ATTESTATION_DIR.is_dir():
        raise SystemExit("privileged attestation directory is missing")

    attestations: dict[str, PrivilegedValidationAttestation] = {}
    for path in sorted(ATTESTATION_DIR.glob("*.json")):
        try:
            attestation = PrivilegedValidationAttestation.load(path)
        except PrivilegedMaintenanceError as exc:
            raise SystemExit(f"invalid privileged attestation {path.name}: {exc}") from None
        expected_name = f"{attestation.candidate.head_sha}.json"
        if path.name != expected_name:
            raise SystemExit(
                f"privileged attestation filename must equal exact candidate head SHA: {path.name}"
            )
        if attestation.candidate.head_sha in attestations:
            raise SystemExit("duplicate privileged attestation candidate head")
        attestations[attestation.candidate.head_sha] = attestation

    bootstrap = policy["bootstrap"]
    if bootstrap["enabled"] is True:
        candidate = bootstrap["candidate"]
        attestation = attestations.get(candidate["head_sha"])
        if attestation is None:
            raise SystemExit("enabled bootstrap candidate must have one committed privileged attestation")
        if attestation.candidate.pull_request != candidate["pull_request"]:
            raise SystemExit("bootstrap candidate PR does not match committed privileged attestation")

    print("[PASS] privileged maintenance is fail-closed and exact-candidate-bound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
