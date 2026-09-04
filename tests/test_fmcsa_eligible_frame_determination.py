import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location(
    "eligible_determination", ROOT / "scripts/verify_fmcsa_eligible_frame_determination.py"
)
eligible = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eligible)


class EligibleFrameDeterminationTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "data/fmcsa/eligible-frame-determination.json"
        self.value = json.loads(self.path.read_text())

    def mutated(self, change):
        value = copy.deepcopy(self.value)
        change(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "determination.json"
            path.write_text(json.dumps(value))
            return eligible.verify(path)

    def test_repository_determination_is_precisely_blocked(self):
        self.assertEqual(eligible.verify(self.path), {
            "determination": "ELIGIBLE_FRAME_BLOCKED", "errors": []
        })

    def test_source_and_evidence_identity_mismatch_fail_closed(self):
        result = self.mutated(lambda value: value["source_dataset"].update(id="wrong"))
        self.assertIn("canonical dataset identity mismatch", result["errors"])
        result = self.mutated(
            lambda value: value["bound_repository_evidence"][0].update(sha256="sha256:" + "0" * 64)
        )
        self.assertTrue(any("digest mismatch" in error for error in result["errors"]))

    def test_missing_artifact_identity_cannot_be_manufactured(self):
        result = self.mutated(
            lambda value: value["required_complete_frame"].update(sha256="sha256:" + "0" * 64)
        )
        self.assertTrue(any("unverified digest" in error for error in result["errors"]))

    def test_schema_and_manifest_presence_mismatch_fail_closed(self):
        for key in ("required_schema", "required_acquisition_manifest"):
            with self.subTest(key=key):
                result = self.mutated(lambda value, key=key: value[key].update(present=True))
                self.assertTrue(any("absence assertion" in error for error in result["errors"]))

    def test_no_transformation_or_sampling_result_may_be_asserted(self):
        result = self.mutated(lambda value: value["eligible_frame"].update(row_count=1))
        self.assertTrue(any("eligible frame is asserted" in error for error in result["errors"]))
        result = self.mutated(lambda value: value.update(sample_drawn=True))
        self.assertIn("hard boundary violated: sample_drawn", result["errors"])


if __name__ == "__main__":
    unittest.main()
