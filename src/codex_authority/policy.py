from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


EXPECTED_CANDIDATE_REPOSITORY = "scnehaux/codex"
EXPECTED_AUTHORITY_CHECK_CONTEXT = "Codex Governance Authority"
EXPECTED_GITHUB_APP_ID = 4864946


@dataclass(frozen=True, slots=True)
class AuthorityPolicy:
    candidate_repository: str
    authority_check_context: str
    github_app_id: int
    execution_location: str
    candidate_code_execution: bool
    candidate_may_select_effective_revision: bool
    candidate_may_auto_deploy_authority: bool
    credentials_may_be_stored_in_repository: bool


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def load_authority_policy(path: str | Path) -> AuthorityPolicy:
    data = _object(json.loads(Path(path).read_text(encoding="utf-8")), "authority")
    expected = {
        "schema_version": 1,
        "candidate_repository": EXPECTED_CANDIDATE_REPOSITORY,
        "authority_check_context": EXPECTED_AUTHORITY_CHECK_CONTEXT,
        "github_app_id": EXPECTED_GITHUB_APP_ID,
        "execution": {
            "location": "external",
            "candidate_code_execution": False,
        },
        "trust": {
            "candidate_may_select_effective_revision": False,
            "candidate_may_auto_deploy_authority": False,
            "credentials_may_be_stored_in_repository": False,
        },
    }
    if data != expected:
        raise ValueError("authority policy drifted from the fixed trust boundary")

    execution = _object(data["execution"], "execution")
    trust = _object(data["trust"], "trust")
    return AuthorityPolicy(
        candidate_repository=data["candidate_repository"],
        authority_check_context=data["authority_check_context"],
        github_app_id=data["github_app_id"],
        execution_location=execution["location"],
        candidate_code_execution=execution["candidate_code_execution"],
        candidate_may_select_effective_revision=trust[
            "candidate_may_select_effective_revision"
        ],
        candidate_may_auto_deploy_authority=trust[
            "candidate_may_auto_deploy_authority"
        ],
        credentials_may_be_stored_in_repository=trust[
            "credentials_may_be_stored_in_repository"
        ],
    )
