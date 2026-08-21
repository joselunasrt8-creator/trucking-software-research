import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTRUMENT = ROOT / "instruments" / "qualification-attempt-v1"
spec = importlib.util.spec_from_file_location("qualification_validator", INSTRUMENT / "validate.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class QualificationAttemptV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((INSTRUMENT / "schema.json").read_text())
        cls.example = json.loads((INSTRUMENT / "example.json").read_text())

    def test_schema_is_versioned_draft_2020_12_json_schema(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.schema["properties"]["instrument_version"]["const"], "qualification-attempt-v1")
        self.assertFalse(self.schema["additionalProperties"])

    def test_schema_declares_required_vocabularies_and_confirmed_guard(self):
        serialized = json.dumps(self.schema)
        for value in validator.DECISIONS | validator.CLASSIFICATIONS | {
            "MEASURED_FACT", "CALIBRATED_RISK", "UNCERTAINTY_PROXY", "UNKNOWN_PROPRIETARY_SIGNAL"
        }:
            self.assertIn(value, serialized)
        confirmed_rule = self.schema["allOf"][0]
        self.assertEqual(confirmed_rule["if"]["properties"]["adjudication"]["properties"]["classification"]["const"], "CONFIRMED_FALSE_GATE")
        self.assertEqual(confirmed_rule["then"]["properties"]["rule"]["properties"]["predicate"]["properties"]["t0_evaluation"]["properties"]["result"]["const"], "SATISFIED")

    def test_complete_lifecycle_example_is_semantically_valid(self):
        self.assertEqual(validator.validate(self.example), [])

    def test_confirmed_false_gate_requires_satisfied_predicate(self):
        record = copy.deepcopy(self.example)
        record["rule"]["predicate"]["t0_evaluation"]["result"] = "UNKNOWN"
        self.assertIn("CONFIRMED_FALSE_GATE requires predicate satisfaction at T0", validator.validate(record))

    def test_confirmed_false_gate_requires_authoritative_t0_reference(self):
        record = copy.deepcopy(self.example)
        record["rule"]["predicate"]["t0_evaluation"]["evidence_refs"] = ["platform-001"]
        self.assertIn("CONFIRMED_FALSE_GATE predicate evidence must resolve to authoritative T0 evidence", validator.validate(record))

    def test_confirmed_false_gate_rejects_post_t0_authoritative_fact(self):
        record = copy.deepcopy(self.example)
        record["authoritative_state"]["evidence"][0]["as_of"] = "2026-07-01T14:00:01Z"
        self.assertIn("CONFIRMED_FALSE_GATE evidence must be effective by T0", validator.validate(record))

    def test_later_evidence_must_be_append_ordered_and_post_t0(self):
        record = copy.deepcopy(self.example)
        record["later_evidence"][0]["sequence"] = 2
        record["later_evidence"][0]["observed_at"] = "2026-07-01T13:59:00Z"
        errors = validator.validate(record)
        self.assertIn("later evidence sequence must be contiguous and append ordered", errors)
        self.assertIn("later evidence must be observed after T0 in chronological order", errors)

    def test_indeterminate_is_valid_without_forcing_complete_evidence(self):
        record = copy.deepcopy(self.example)
        record["adjudication"]["classification"] = "INDETERMINATE"
        record["rule"]["predicate"]["t0_evaluation"] = {"result": "UNKNOWN", "evidence_refs": []}
        self.assertEqual(validator.validate(record), [])


if __name__ == "__main__":
    unittest.main()
