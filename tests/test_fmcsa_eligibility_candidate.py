import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("candidate", ROOT / "scripts/verify_fmcsa_eligibility_candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CandidateEligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "data/fmcsa/carrier-eligibility-rule-candidate.json"
        cls.value = json.loads(cls.path.read_text())

    def mutated(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(value))
            return candidate.verify(path)

    def test_repository_candidate_verifies_but_remains_unfrozen(self):
        self.assertEqual(candidate.verify(self.path)["determination"], "CANDIDATE_RULE_VERIFIED_UNFROZEN")
        self.assertFalse(self.value["rule_frozen"])

    def test_unresolved_fields_are_prohibited_and_not_dependencies(self):
        result = self.mutated(lambda value: value["minimal_fields"].append("az4n-8mr2.review_type"))
        self.assertTrue(any("minimal dependency" in error for error in result["errors"]))
        result = self.mutated(lambda value: value.update(review_type_required=True))
        self.assertTrue(any("must not be required" in error for error in result["errors"]))

    def test_missing_behavior_must_fail_closed(self):
        result = self.mutated(lambda value: value["predicates"][0].update(missing_or_other_behavior="INCLUDE"))
        self.assertTrue(any("fail closed" in error for error in result["errors"]))

    def test_candidate_evaluation_is_deterministic(self):
        company = {"status_code": "A", "carrier_operation": "A"}
        matching = [{"op_auth_type": "Motor Carrier of Property (Except Household Goods)", "op_auth_status": "Active"}]
        self.assertEqual(candidate.evaluate(company, matching), "INCLUDE")
        self.assertEqual(candidate.evaluate(company, matching), "INCLUDE")
        self.assertEqual(candidate.evaluate({"status_code": "I", "carrier_operation": "A"}, matching), "EXCLUDE")
        self.assertEqual(candidate.evaluate(company, []), "INDETERMINATE_EXCLUDE")
        self.assertEqual(candidate.evaluate(company, [{"op_auth_type": None, "op_auth_status": "Active"}]), "INDETERMINATE_EXCLUDE")


if __name__ == "__main__":
    unittest.main()
