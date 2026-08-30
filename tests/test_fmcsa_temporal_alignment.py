import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("alignment", ROOT / "scripts/verify_fmcsa_temporal_alignment.py")
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


class TemporalAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "data/fmcsa/temporal-alignment-contract.json"
        self.contract = json.loads(self.path.read_text())

    def verify_mutation(self, mutate):
        value = copy.deepcopy(self.contract)
        mutate(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(value))
            return alignment.verify(path)

    def test_repository_determination_is_blocked_without_join(self):
        result = alignment.verify(self.path)
        expected = json.loads((ROOT / "data/fmcsa/temporal-alignment-determination.json").read_text())
        self.assertEqual(result["determination"], expected["determination"])
        self.assertEqual(set(result["missing_paths"]), set(expected["missing_paths"]))

    def test_motus_artifacts_and_commit_are_exactly_bound(self):
        result = self.verify_mutation(lambda value: value["motus_input"].update(frame_sha256="0" * 64))
        self.assertIn("MOTUS frame digest mismatch", result["errors"])
        result = self.verify_mutation(lambda value: value["motus_input"].update(repository_commit="5bef755"))
        self.assertIn("MOTUS commit is not exactly bound to 5bef755", result["errors"])

    def test_alignment_math_and_limit_fail_closed(self):
        result = self.verify_mutation(lambda value: value.update(maximum_version_marker_skew_seconds=80000))
        self.assertTrue(any("temporal alignment" in error for error in result["errors"]))
        result = self.verify_mutation(lambda value: value["computed_alignment"].update(version_marker_skew_seconds=1))
        self.assertTrue(any("temporal alignment" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
