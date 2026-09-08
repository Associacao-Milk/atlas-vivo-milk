import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from atlas_integrations.cli import migration_status
from atlas_integrations.connectors import FIWAREConnector, ManualAuthorityGate
from atlas_integrations.models import AtlasRecord
from atlas_integrations.mistral import AgentEnvelope, CloudPolicyError, EngineeringWorkflow, MistralOrchestrator


def record(**updates):
    base = {"record_id":"milk-1", "title":"Atlas", "record_type":"dataset",
            "classification":"publico", "approval":"APROVADO", "consent_public":True,
            "licence":"CC-BY-4.0", "creators":["Associação MILK"],
            "provenance":{"source_id":"drive-1", "source_system":"Google Drive",
                          "sha256":"a"*64}}
    base.update(updates)
    return AtlasRecord.model_validate(base)


class KernelTests(unittest.TestCase):
    def test_public_gate_rejects_missing_consent(self):
        with self.assertRaises(ValidationError):
            record(consent_public=False)

    def test_canonical_hash_is_stable(self):
        self.assertEqual(record().canonical_hash(), record().canonical_hash())

    def test_fiware_is_dry_run_by_default(self):
        receipt = FIWAREConnector("https://broker.example.org").create_entity(record())
        self.assertTrue(receipt.dry_run)
        self.assertFalse(receipt.executed)

    def test_authorities_never_claim_registration(self):
        receipt = ManualAuthorityGate().dossier("IGAC", record())
        self.assertEqual(receipt.status, "DOSSIER_PREPARADO")
        self.assertIsNone(receipt.external_id)

    def test_migration_manifest_counts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"m.json"
            p.write_text(json.dumps({"summary":{"files":4870,"folders":397,"bytes":16011662239}}))
            status = migration_status(str(p))
            self.assertEqual(status.discovered_files, 4870)
            self.assertEqual(status.transferred, 0)

    def test_mistral_cloud_blocks_personal_data(self):
        envelope = AgentEnvelope(task_id="t1", target_agent="codificador_modulos",
            action="teste", data_classification="dados_pessoais", log_ref="audit/t1.json")
        with self.assertRaises(CloudPolicyError):
            MistralOrchestrator().prepare(envelope)

    def test_mistral_workflow_covers_engineering(self):
        plan = EngineeringWorkflow().plan("atlas", "integrar", ["drive:manifest"], {})
        self.assertEqual(len(plan), 10)
        self.assertEqual(plan[0].target_agent, "arquiteto_ecossistema")
        result = MistralOrchestrator().run(plan[0])
        self.assertEqual(result["status"], "VALIDADO_SEM_EXECUTAR")

    def test_mistral_redacts_secrets_and_identifiers(self):
        payload = MistralOrchestrator._redact({
            "token": "never-send", "nested": {"client_secret": "also-never"},
            "contact": "person@example.org", "nif": "123456789"})
        self.assertEqual(payload["token"], "[DADO_REMOVIDO]")
        self.assertEqual(payload["nested"]["client_secret"], "[DADO_REMOVIDO]")
        self.assertNotIn("example.org", payload["contact"])
        self.assertNotIn("123456789", payload["nif"])


if __name__ == "__main__":
    unittest.main()
