import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "issue21_environment", ROOT / "scripts/verify_fmcsa_issue21_environment.py"
)
environment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(environment)


class Issue21EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "data/fmcsa/issue-21-codex-environment-status.json"
        self.value = json.loads(self.path.read_text())

    def mutated(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text(json.dumps(value))
            return environment.verify(path)

    def test_checkout_is_blocked_but_issue_21_is_unresolved(self):
        self.assertEqual(environment.verify(self.path), {
            "environment_determination": "CODEX_ENVIRONMENT_BLOCKED",
            "issue_21": "UNRESOLVED",
            "errors": [],
        })

    def test_historical_audit_is_not_erased_by_checkout_absence(self):
        result = self.mutated(
            lambda value: value["historical_empirical_evidence"].update(status="NEVER_EXISTED")
        )
        self.assertTrue(any("historical PR #19 evidence mismatch" in error for error in result["errors"]))

    def test_checkout_cannot_promote_absence_to_terminal_issue_status(self):
        result = self.mutated(lambda value: value["issue_21"].update(authoritative_status="ELIGIBLE_FRAME_BLOCKED"))
        self.assertIn("checkout evidence must not assert a terminal Issue #21 determination", result["errors"])

    def test_presence_inventory_and_source_identity_fail_closed(self):
        result = self.mutated(
            lambda value: value["current_environment_evidence"]["required_artifacts"].pop()
        )
        self.assertIn("required artifact inventory mismatch", result["errors"])
        result = self.mutated(lambda value: value["source_dataset"].update(id="wrong"))
        self.assertIn("canonical dataset identity mismatch", result["errors"])

    def test_no_transformation_or_sampling_result_may_be_asserted(self):
        result = self.mutated(lambda value: value["issue_21"].update(eligible_frame_row_count=1))
        self.assertTrue(any("must remain null" in error for error in result["errors"]))
        result = self.mutated(lambda value: value["hard_boundaries"].update(sample_drawn=True))
        self.assertIn("hard boundary violated: sample_drawn", result["errors"])


if __name__ == "__main__":
    unittest.main()
