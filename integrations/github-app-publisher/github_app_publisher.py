#!/usr/bin/env python3
"""Credential-isolated GitHub App publisher for Codex Governance Authority.

Default execution is an offline permit preview. Remote publication remains impossible
while governed config is `disabled`. Candidate code is never evaluated here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from publisher_contract import (
    APP_ID, CHECK_CONTEXT, Config, EXPECTED_EVALUATOR_SOURCE_REVISION,
    EXPECTED_RUNTIME_SOURCE_REVISION, INSTALLATION_ID, PERMIT_KIND, Permit,
    PublisherError, REPOSITORY, load_permit, verify_exported_publisher,
)
from publisher_transport import (
    REQUIRED_INSTALLATION_PERMISSIONS, TOKEN_PERMISSIONS, check_payload, default_key_path,
    issue_token, make_jwt, preflight_app, request_json, verify_candidate_pr, verify_check,
)

def publish(
    config: Config,
    permit: Permit,
    key_path: Path,
    *,
    config_path: Path,
    permit_path: Path,
    request: Callable[..., dict[str, Any]] = request_json,
) -> dict[str, Any]:
    if config.write_mode == "disabled":
        raise PublisherError("publisher-disabled", "Publisher remote writes are disabled by governed config.")
    if config.expected_authority_service_source_revision != permit.authority_service_source_revision:
        raise PublisherError("permit-authority-source", "Authority-service source is not the promoted revision.")
    if config.write_mode != "proof":
        raise PublisherError("publisher-mode", "Standalone remote publication is restricted to governed proof mode.")
    if config.proof_head_sha != permit.head_sha:
        raise PublisherError("proof-candidate", "Proof mode is bound to one exact candidate SHA.")
    if config.proof_permit_digest != permit.digest:
        raise PublisherError("proof-permit", "Proof mode is bound to one exact promoted publication permit digest.")

    verify_exported_publisher(config_path, permit_path, config)
    app_jwt = make_jwt(key_path, config.client_id)
    preflight_app(config, app_jwt, request)
    installation_token = issue_token(config, app_jwt, request)
    revoked = False
    try:
        pr = request(f"/repos/{config.repository}/pulls/{permit.pull_request}", installation_token)
        verify_candidate_pr(pr, permit)
        raw_check = request(
            f"/repos/{config.repository}/check-runs",
            installation_token,
            method="POST",
            body=check_payload(permit),
        )
        check_run_id = verify_check(raw_check, config, permit)
        request("/installation/token", installation_token, method="DELETE")
        revoked = True
    finally:
        if not revoked:
            try:
                request("/installation/token", installation_token, method="DELETE")
            except Exception:
                pass
    if not revoked:
        raise PublisherError("token-revocation", "Installation token revocation was not proven after publication.")
    return {
        "status": "authority_check_published",
        "repository": permit.repository,
        "pull_request": permit.pull_request,
        "candidate_sha": permit.head_sha,
        "check_context": config.check_context,
        "check_run_id": check_run_id,
        "integration_id": config.app_id,
        "conclusion": "success",
        "permit_digest": permit.digest,
        "source_verified": True,
        "exact_candidate_binding": True,
        "credentials_isolated": True,
        "candidate_code_executed": False,
        "token_revoked": True,
        "remote_mutations": 3,
        "effective_enforcement_proven": False,
    }


def preview(config: Config, permit: Permit) -> dict[str, Any]:
    return {
        "status": "preview_only",
        "write_mode": config.write_mode,
        "repository": permit.repository,
        "pull_request": permit.pull_request,
        "candidate_sha": permit.head_sha,
        "check_context": config.check_context,
        "conclusion": "success",
        "permit_digest": permit.digest,
        "remote_mutations": 0,
        "publisher_live_proven": config.live_proven,
        "effective_enforcement_proven": False,
    }


def _print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, sort_keys=True))
        return
    for key, value in report.items():
        print(f"{key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish the fixed Codex Governance Authority check from a governed permit.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--permit", type=Path, required=True)
    parser.add_argument("--private-key", type=Path, default=default_key_path())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--confirm-repository")
    parser.add_argument("--confirm-sha")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = Config.load(args.config)
        permit = load_permit(args.permit, config)
        if not args.write:
            _print_report(preview(config, permit), args.json)
            return 0
        if config.write_mode == "disabled":
            raise PublisherError("publisher-disabled", "Governed config has not promoted any remote publisher write.")
        if args.confirm_repository != config.repository or args.confirm_sha != permit.head_sha:
            raise PublisherError("operator-confirmation", "Write requires exact repository and candidate-SHA confirmations.")
        _print_report(
            publish(
                config,
                permit,
                args.private_key,
                config_path=args.config,
                permit_path=args.permit,
            ),
            args.json,
        )
        return 0
    except PublisherError as exc:
        if args.json:
            print(json.dumps({"status": "blocked", "code": exc.code, "message": str(exc)}, sort_keys=True))
        else:
            print(f"BLOCKED [{exc.code}]: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
