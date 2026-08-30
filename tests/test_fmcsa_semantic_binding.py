import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "semantic_verifier", ROOT / "scripts/verify_fmcsa_semantic_binding.py"
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class SemanticBindingVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding_path = ROOT / "data/fmcsa/company-census-semantic-binding.json"
        cls.binding = json.loads(cls.binding_path.read_text())

    def verify_mutation(self, mutate):
        binding = copy.deepcopy(self.binding)
        mutate(binding)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "binding.json"
            path.write_text(json.dumps(binding))
            return verifier.verify(path, ROOT)

    def test_repository_binding_and_attachment_identity_verify(self):
        result = verifier.verify(self.binding_path, ROOT)
        self.assertEqual(result["determination"], "SEMANTIC_BINDING_PARTIALLY_BOUND")
        self.assertEqual(result["errors"], [])

    def test_digest_size_and_missing_artifact_fail_closed(self):
        result = self.verify_mutation(lambda b: b["sources"][1].update(sha256="sha256:" + "0" * 64))
        self.assertTrue(any("SHA-256 mismatch" in error for error in result["errors"]))
        result = self.verify_mutation(lambda b: b["sources"][1].update(byte_size=1))
        self.assertTrue(any("byte size mismatch" in error for error in result["errors"]))
        result = self.verify_mutation(lambda b: b["sources"][1].update(artifact_path="data/fmcsa/authoritative/missing.pdf"))
        self.assertTrue(any("artifact is absent" in error for error in result["errors"]))
        result = self.verify_mutation(lambda b: b["sources"][3].update(sha256="sha256:" + "0" * 64))
        self.assertTrue(any("SHA-256 mismatch" in error for error in result["errors"]))

    def test_non_authoritative_source_and_broken_citation_fail_closed(self):
        result = self.verify_mutation(lambda b: b["sources"][1].update(source_url="https://example.com/dictionary.pdf"))
        self.assertTrue(any("not on an authoritative" in error for error in result["errors"]))
        result = self.verify_mutation(lambda b: b["fields"][0]["definition_citation"].update(source_id="missing"))
        self.assertTrue(any("citation does not resolve" in error for error in result["errors"]))

    def test_available_transition_with_unresolved_code_fails_closed(self):
        def mutate(binding):
            field = next(item for item in binding["fields"] if item["field"] == "docket1_status_code")
            field["definition_status"] = "AUTHORITATIVE_DEFINITION_AVAILABLE"
            field["eligibility_use"] = "PERMITTED_AFTER_RULE_FREEZE"
        result = self.verify_mutation(mutate)
        self.assertTrue(any("AVAILABLE requires" in error for error in result["errors"]))

    def test_unavailable_transition_without_blocker_fails_closed(self):
        def mutate(binding):
            field = next(item for item in binding["fields"] if item["field"] == "review_type")
            field["unresolved_code_values"] = []
        result = self.verify_mutation(mutate)
        self.assertTrue(any("UNAVAILABLE requires" in error for error in result["errors"]))

    def test_inference_and_eligibility_freeze_are_rejected(self):
        result = self.verify_mutation(lambda b: b["fields"][0].update(inference_policy="INFERENCE_ALLOWED"))
        self.assertTrue(any("inference policy" in error for error in result["errors"]))
        result = self.verify_mutation(lambda b: b.update(eligibility_rule_status="FROZEN"))
        self.assertTrue(any("must remain not frozen" in error for error in result["errors"]))

    def test_duplicate_or_incomplete_field_inventory_fails_closed(self):
        result = self.verify_mutation(lambda b: b["fields"].pop())
        self.assertTrue(any("each required coded field exactly once" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
