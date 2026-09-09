# Scnehaux Codex Authority

Independent runtime and GitHub App publisher for the `scnehaux/codex` governance authority.

This repository exists to keep the effective external authority source, deployment path, and credentials outside the candidate repository it evaluates.

## Trust boundary

- `scnehaux/codex` remains the governed candidate/control-plane repository.
- `scnehaux/codex-authority` contains the independently administered authority runtime and publisher.
- Candidate changes must never select the effective authority revision or auto-deploy authority code.
- GitHub App credentials must never be committed to either repository.
- Production authority publication remains disabled until a reviewed authority revision and controlled live publisher proof exist.

The initial repository state is intentionally minimal. Authority implementation is introduced through reviewed pull requests after this bootstrap commit.
