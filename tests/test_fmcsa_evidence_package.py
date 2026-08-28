import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "evidence_verifier", ROOT / "scripts/verify_fmcsa_evidence_package.py"
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class EvidencePackageTests(unittest.TestCase):
    def test_recovery_report_preserves_access_blocked_distinction(self):
        report = json.loads((ROOT / "data/fmcsa/recovery-report.json").read_text())
        self.assertEqual(report["historical_recovery_state"],
                         "HISTORICAL_PACKAGE_ACCESS_BLOCKED")
        self.assertEqual(report["canonical_evidence_state"],
                         "CANONICAL_EVIDENCE_PACKAGE_BLOCKED")
        classifications = {
            artifact["recovery_classification"] for artifact in report["artifacts"]
        }
        self.assertEqual(classifications,
                         {"IRRECOVERABLE_FROM_AVAILABLE_EVIDENCE", "RETRIEVAL_BLOCKED"})
        self.assertEqual(len(report["artifacts"]), 5)

    def test_reacquisition_requires_authorization_and_new_identity(self):
        requirement = json.loads(
            (ROOT / "data/fmcsa/reacquisition-requirement.json").read_text()
        )
        self.assertEqual(requirement["status"],
                         "NOT_AUTHORIZED_PENDING_RECOVERY_ACCESS")
        self.assertIn("distinct", requirement["new_object_requirements"]["acquisition_identity"])
        self.assertIsNone(
            requirement["historical_identities_to_preserve"]["artifact_digests"]
        )

    def test_repository_contract_determines_blocked_without_local_artifacts(self):
        result = verifier.verify(ROOT / "data/fmcsa/evidence-package.json", ROOT)
        self.assertEqual(result["dataset_id"], "az4n-8mr2")
        self.assertEqual(result["determination"], "CANONICAL_EVIDENCE_PACKAGE_BLOCKED")
        self.assertTrue(any("required artifact is absent" in error for error in result["errors"]))

    def test_present_artifact_without_expected_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "frame.json"
            artifact.write_text("[]\n")
            contract = {
                "contract_version": "fmcsa-canonical-evidence-package-v1",
                "dataset_identity": {"id": "az4n-8mr2"},
                "determination": "CANONICAL_EVIDENCE_PACKAGE_BLOCKED",
                "artifacts": [{
                    "artifact_id": "frame", "required": True,
                    "expected_filename": "frame.json", "expected_sha256": None,
                    "expected_byte_size": None, "dataset_id": "az4n-8mr2",
                    "status": "AVAILABLE_UNVERIFIED"
                }]
            }
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract))
            result = verifier.verify(contract_path, root)
            self.assertEqual(result["determination"], "CANONICAL_EVIDENCE_PACKAGE_BLOCKED")
            self.assertIn("artifact is present but has no bound expected digest",
                          result["artifacts"][0]["errors"])

    def test_digest_or_size_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "frame.json").write_text("[]\n")
            contract = {
                "contract_version": "fmcsa-canonical-evidence-package-v1",
                "dataset_identity": {"id": "az4n-8mr2"},
                "determination": "CANONICAL_EVIDENCE_PACKAGE_BLOCKED",
                "artifacts": [{
                    "artifact_id": "frame", "required": True,
                    "expected_filename": "frame.json",
                    "expected_sha256": "sha256:" + "0" * 64,
                    "expected_byte_size": 999, "dataset_id": "az4n-8mr2",
                    "status": "AVAILABLE_AND_VERIFIED"
                }]
            }
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract))
            result = verifier.verify(contract_path, root)
            self.assertIn("SHA-256 mismatch", result["artifacts"][0]["errors"])
            self.assertIn("byte-size mismatch", result["artifacts"][0]["errors"])


if __name__ == "__main__":
    unittest.main()
