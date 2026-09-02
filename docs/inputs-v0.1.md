# LSP upstream inputs in constellation v0.1

## Active

| Contract | Producer | Status |
|---|---|---|
| `l9.debt-defense/v1` | `Quantum-L9/l9-ci-debt-intelligence` | Active |

Defense-pack consumption is the editor path in v0.1. This is the one
cross-repository contract pair in the constellation whose producer and consumer
schemas actually agree: `schemas/lsp/defense-pack-consumer.schema.json` is a
deliberately looser copy of the intelligence producer schema — consumer-looser
being the safe direction — with one field where it is stricter,
`SDK_contract_version`, and that value matches.

## Inactive / planned

| Contract | Producer | Status |
|---|---|---|
| `l9.sdk-finding/v1` | none | Planned |

Direct consumption of SDK findings is **not** active in v0.1.

`schemas/lsp/sdk-finding-consumer.schema.json` requires
`schema_version: const "l9.sdk-finding/v1"`. Nothing emits it. The SDK's tokens
are `l9.finding-bundle/v1`, `l9.observation`, `l9.gate-result/v1`, and
`l9.agent-review-projection/v1`.

Validation for this contract is real code and stays in place — the
`sdk_finding_validation` capability is not a false claim about *validation*.
What would be false is presenting it as a live input, which is why
`phase_capabilities()` now carries an `input_status` block and
`tests/runtime/test_capabilities.py` asserts it.

### Why this is not a renaming exercise

Activating this seam needs an explicit projection contract, not a field map.
The shapes disagree structurally: this consumer requires `canonical_rule_id`
(optional in the SDK), a singular `source_location` carrying
`document_identity` with zero-based coordinates (the SDK has a `locations`
tuple with one-based lines), and `evidence` as objects with `kind` and
`summary` (the SDK carries `evidence_ids` strings).

The severity vocabularies barely intersect:

| | Values |
|---|---|
| This consumer accepts | `critical`, `error`, `warning`, `information`, `info`, `hint`, `unknown` |
| The SDK produces | `critical`, `high`, `medium`, `low`, `informational`, `unknown` |
| Common | `critical`, `unknown` |

Four of the six real SDK severities are invalid to this consumer. Mapping them
by coincidence of spelling would silently mis-rank findings, so the mapping has
to be published by the SDK's projection layer — alongside its assurance
projection — and reviewed as a contract.

## Closing this

Either the SDK publishes `l9.sdk-finding/v1` with an explicit severity
projection and this moves to active, or this consumer is retargeted onto
`l9.finding-bundle/v1`, which exists today. Until then the entry stays declared
and inactive rather than implying a live editor integration.
