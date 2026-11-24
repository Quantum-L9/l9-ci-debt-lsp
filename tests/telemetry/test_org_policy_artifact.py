"""The committed organization default is a working, validated policy.

`policy/org-default.telemetry-policy.json` is the artifact that arms the return
leg: without it, `TelemetryPolicyStore.DEFAULT_POLICY` keeps `mode: disabled`,
`consent: not_granted`, `endpoint: null`, and nothing the LSP observes ever
leaves the machine. With it, `telemetry-policy-apply` produces a policy whose
`delivery_enabled` is true and whose endpoint is the constellation's ingress.

These tests hold three properties: the artifact is schema-valid and
semantically valid, applying it produces a delivering policy, and a document
that would deliver outside its own allowlist is refused before it is written.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from l9_debt_lsp.telemetry.errors import TelemetryPolicyError
from l9_debt_lsp.telemetry.policy import TelemetryPolicyStore

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "policy/org-default.telemetry-policy.json"
SCHEMA = ROOT / "schemas/lsp/telemetry-policy.schema.json"


def artifact() -> dict[str, object]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


class OrgDefaultPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.policy_path = Path(self.directory.name) / "telemetry-policy.json"
        self.store = TelemetryPolicyStore(path=self.policy_path, schema_path=SCHEMA)

    def test_the_artifact_is_schema_valid(self) -> None:
        from l9_debt_lsp.contracts.schema import SchemaValidator

        SchemaValidator(SCHEMA).validate(artifact())

    def test_applying_the_artifact_produces_a_delivering_policy(self) -> None:
        policy = self.store.apply_document(artifact())
        self.assertTrue(policy.persistence_enabled)
        self.assertTrue(policy.delivery_enabled)
        self.assertEqual("user_opt_in", policy.mode)
        self.assertEqual("granted", policy.consent)
        self.assertEqual("quantum-l9-core", policy.organization_policy_id)
        self.assertEqual(
            "https://feedback.quantumaipartners.com/api/v1/events",
            policy.endpoint,
        )

    def test_the_written_policy_reloads_identically(self) -> None:
        applied = self.store.apply_document(artifact())
        reloaded = self.store.load()
        self.assertEqual(applied, reloaded)

    def test_an_endpoint_outside_the_allowlist_is_refused(self) -> None:
        document = artifact()
        document["endpoint"] = "https://collector.example.com/api/v1/events"
        with self.assertRaises(TelemetryPolicyError):
            self.store.apply_document(document)
        self.assertFalse(self.policy_path.exists())

    def test_a_document_that_violates_the_schema_is_refused(self) -> None:
        document = artifact()
        document["mode"] = "delivery"
        with self.assertRaises(Exception):
            self.store.apply_document(document)
        self.assertFalse(self.policy_path.exists())

    def test_http_endpoints_are_refused(self) -> None:
        document = artifact()
        document["endpoint"] = "http://feedback.quantumaipartners.com/api/v1/events"
        document["endpoint_allowlist"] = ["http://feedback.quantumaipartners.com/"]
        with self.assertRaises(TelemetryPolicyError):
            self.store.apply_document(document)


if __name__ == "__main__":
    unittest.main()
