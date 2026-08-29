import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("candidate", ROOT / "scripts/verify_fmcsa_candidate_eligibility.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CandidateEligibilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.semantics = self.root / "semantics.json"
        self.freeze = self.root / "freeze.json"
        self.semantics.write_text((ROOT / candidate.SEMANTICS).read_text())
        self.freeze.write_text((ROOT / candidate.FREEZE).read_text())

    def rewrite(self, path, mutate):
        value = json.loads(path.read_text())
        mutate(value)
        path.write_text(json.dumps(value))

    def test_repository_boundary_is_verified_unfrozen_and_fail_closed(self):
        result = candidate.verify(self.semantics, self.freeze, self.root)
        self.assertFalse(result["authoritative_motus_semantics_freeze_grade"])
        self.assertFalse(result["point_in_time_protocol_valid"])
        self.assertEqual(result["eligibility_rule_status"], "ELIGIBILITY_RULE_NOT_FROZEN")

    def test_exact_candidate_values_are_immutable(self):
        self.rewrite(self.semantics, lambda x: x["candidate_bindings"][0].update(candidate_value="Property"))
        self.assertIn("exact candidate binding", " ".join(candidate.verify(self.semantics, self.freeze, self.root)["errors"]))

    def test_semantic_evidence_requires_exact_provenance_and_digest(self):
        self.rewrite(self.semantics, lambda x: x["candidate_bindings"][0].update(
            authoritative_text=candidate.VALUES["op_auth_type"], authoritative_artifact={"url": "https://www.fmcsa.dot.gov/"}))
        result = candidate.verify(self.semantics, self.freeze, self.root)
        self.assertFalse(result["authoritative_motus_semantics_freeze_grade"])
        self.assertIn("provenance is incomplete", " ".join(result["errors"]))

    def test_t0_join_protocol_is_rejected_before_semantics_are_freeze_grade(self):
        def mutate(x):
            x.update(reference_time_t0="2026-08-29T00:00:00Z",
                     admissible_company_census_artifact={}, admissible_motus_artifact={},
                     join_protocol={"cardinality": "one-to-many"})
        self.rewrite(self.freeze, mutate)
        result = candidate.verify(self.semantics, self.freeze, self.root)
        self.assertIn("before semantic prerequisite", " ".join(result["errors"]))
        self.assertFalse(result["point_in_time_protocol_valid"])

    def test_cohort_and_count_fail_closed_without_protocol(self):
        self.rewrite(self.freeze, lambda x: x.update(cohort_artifact={"path": "cohort.json"}, candidate_cohort_row_count=1))
        result = candidate.verify(self.semantics, self.freeze, self.root)
        self.assertIn("cohort exists without", " ".join(result["errors"]))
        self.assertEqual(result["eligibility_rule_status"], "ELIGIBILITY_RULE_NOT_FROZEN")

    def test_count_without_artifact_is_rejected(self):
        self.rewrite(self.freeze, lambda x: x.update(candidate_cohort_row_count=0))
        self.assertIn("row count is claimed", " ".join(candidate.verify(self.semantics, self.freeze, self.root)["errors"]))


if __name__ == "__main__":
    unittest.main()
