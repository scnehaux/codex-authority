# PR #43 Slice 13.2 publication result and disarm

Recorded: 2026-10-04 (Asia/Jakarta). Implementation-local, non-normative.

Codex PR #43 received the dedicated-App Authority check on exact head `1fadd8d04578e02ab29bf520ec5fec9b589e92e1` and base `e86c408fe3ec72a83a5af926c84bc63d92e961fe`, then was squash-merged as `043c1d51fd621428e59a5988cb383a857e690bd1`.

- Check: [111317124222](https://github.com/scnehaux/codex/runs/111317124222)
- Context: `Codex Governance Authority`
- App ID: `4864946`
- Conclusion: `success`
- Publisher outcome: `published`
- Installation token revoked: `true`
- Attestation: Authority PR #99, merge `3bc4434ccba394df7365ee70b17ef1cbe0ef7057`
- Activation: Authority PR #100, merge `4b2a1317d6541f8749e5fccd61c4609e89f11f56`
- Authority/publisher source: `3bc4434ccba394df7365ee70b17ef1cbe0ef7057`
- Permit digest: `76c3ae36afd6f794886a2cbc83652c6b1c813a719ccf0b22b5c380b24e1175fe`
- Evidence SHA-256: `848f95890de9413a80b5f295836ccd5b4b1a57a5ea92a13b7e69bde1990c9e4e`
- Receipt SHA-256: `6cea7adce4a8e4e1a830a096434d7c2e349aa8424cf42ff2d63c4478ee921306`
- Activation digest: `ae02b717c5d592a99b04f809151bfb11b4660f6e56f50a47ce5febb6d71bae2e`

The exported publisher kit was generated from exact Git blob bytes and verified against the activation source pins. Direct script execution under Python isolated mode could not import the sibling `publisher_contract`; a separate isolated launcher supplied the exported publisher directory on `sys.path` without changing publisher bytes. Preview returned `controlled_publication_preview` with zero remote mutations before the single successful write attempt. The durable attempt and outcome remain in `~/pub43/publication-state`. The first blocked permit preparation remains in `~/pr43/evidence-blocked-001.json`.

This change disables the completed activation (`state: disabled`, `activation: null`) and restores the disabled-configuration regression check. Registry counts remain 79 verified / 87 pending. Slice 13.2 remains ACTIVE; Governance 1.0 readiness and architecture admission are not claimed.
