import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
acquire_spec = importlib.util.spec_from_file_location("bounded_acquire", SCRIPTS / "acquire_fmcsa_census_bounded.py")
acquire = importlib.util.module_from_spec(acquire_spec)
acquire_spec.loader.exec_module(acquire)
audit_spec = importlib.util.spec_from_file_location("bounded_audit", SCRIPTS / "audit_fmcsa_census_bounded.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)


class FakeTransport:
    def __init__(self, rows):
        self.rows = rows
        self.urls = []

    def get_json(self, url):
        self.urls.append(url)
        return self.rows


class BoundedCohortTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.raw = self.root / "raw.json"
        self.manifest_path = self.root / "manifest.json"

    def acquire(self, rows=None, limit=3):
        transport = FakeTransport(rows or [{"dot_number": "1"}, {"dot_number": "2"}])
        manifest = acquire.acquire(
            limit, transport, self.raw, self.manifest_path,
            clock=lambda: "2026-08-28T00:00:00+00:00",
        )
        return transport, manifest

    def rewrite_manifest(self, mutate):
        manifest = json.loads(self.manifest_path.read_text())
        mutate(manifest)
        self.manifest_path.write_text(json.dumps(manifest))

    def rewrite_rows_and_reseal(self, rows, counts=(0, 0)):
        raw_bytes = acquire.canonical_json(rows) + b"\n"
        self.raw.write_bytes(raw_bytes)
        def mutate(manifest):
            manifest["row_count"] = len(rows)
            manifest["content_digest"] = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
            manifest["missing_dot_number_count"], manifest["duplicate_dot_number_count"] = counts
        self.rewrite_manifest(mutate)

    def test_acquisition_records_exact_query_limit_digest_and_scope(self):
        transport, manifest = self.acquire()
        self.assertEqual(transport.urls, [acquire.BASE + "?%24limit=3&%24offset=0&%24order=dot_number+ASC"])
        self.assertEqual(manifest["requested_limit"], 3)
        self.assertEqual(manifest["row_count"], 2)
        self.assertEqual(manifest["content_digest"], "sha256:" + hashlib.sha256(self.raw.read_bytes()).hexdigest())
        self.assertEqual(manifest["scope"], acquire.SCOPE)
        self.assertEqual(audit.audit(self.raw, self.manifest_path, 3)["status"], "BOUNDED_COHORT_AUDIT_PASSED")

    def test_acquisition_rejects_ordering_duplicates_and_missing_dot_numbers(self):
        cases = [
            ([{"dot_number": "2"}, {"dot_number": "1"}], "ordering"),
            ([{"dot_number": "1"}, {"dot_number": "1"}], "duplicate"),
            ([{"legal_name": "missing"}], "missing"),
        ]
        for rows, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                self.acquire(rows)

    def test_malformed_and_incomplete_manifests_fail_closed(self):
        self.acquire()
        self.manifest_path.write_text("{")
        with self.assertRaisesRegex(ValueError, "malformed JSON"):
            audit.audit(self.raw, self.manifest_path)
        self.acquire()
        self.rewrite_manifest(lambda value: value.pop("query_contract"))
        with self.assertRaisesRegex(ValueError, "query identity"):
            audit.audit(self.raw, self.manifest_path)

    def test_query_dataset_limit_and_scope_tampering_fail_closed(self):
        mutations = [
            (lambda m: m["dataset_identity"].update(id="wrong"), "dataset identity"),
            (lambda m: m["query_contract"]["parameters"].update({"$order": "dot_number DESC"}), "query identity"),
            (lambda m: m.update(requested_limit=4), "query identity"),
            (lambda m: m["scope"].update(representative=True), "disclaim"),
        ]
        for mutation, message in mutations:
            with self.subTest(message=message):
                self.acquire()
                self.rewrite_manifest(mutation)
                with self.assertRaisesRegex(ValueError, message):
                    audit.audit(self.raw, self.manifest_path)

    def test_expected_limit_is_independently_enforced(self):
        self.acquire()
        with self.assertRaisesRegex(ValueError, "requested limit"):
            audit.audit(self.raw, self.manifest_path, expected_limit=100)

    def test_ordering_violation_fails_even_with_matching_digest(self):
        self.acquire()
        self.rewrite_rows_and_reseal([{"dot_number": "2"}, {"dot_number": "1"}])
        with self.assertRaisesRegex(ValueError, "ordering"):
            audit.audit(self.raw, self.manifest_path)

    def test_duplicate_and_missing_dot_numbers_fail_even_when_counts_are_declared(self):
        self.acquire()
        self.rewrite_rows_and_reseal([{"dot_number": "1"}, {"dot_number": "1"}], counts=(0, 1))
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            audit.audit(self.raw, self.manifest_path)
        self.acquire()
        self.rewrite_rows_and_reseal([{"dot_number": "1"}, {"legal_name": "missing"}], counts=(1, 0))
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            audit.audit(self.raw, self.manifest_path)

    def test_digest_and_row_count_mismatches_fail_closed(self):
        self.acquire()
        self.raw.write_bytes(self.raw.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "digest"):
            audit.audit(self.raw, self.manifest_path)
        self.acquire()
        self.rewrite_manifest(lambda m: m.update(row_count=99))
        with self.assertRaisesRegex(ValueError, "row count"):
            audit.audit(self.raw, self.manifest_path)

    def test_repository_cohort_passes_exact_100_row_audit(self):
        result = audit.audit(
            ROOT / "data/raw/fmcsa/company-census-bounded-100.json",
            ROOT / "data/derived/fmcsa/bounded-100-manifest.json", 100,
        )
        self.assertEqual((result["requested_limit"], result["row_count"]), (100, 100))


class SemanticBindingTests(unittest.TestCase):
    def test_unresolved_coded_fields_are_explicitly_noninferential(self):
        binding = json.loads((ROOT / "data/fmcsa/company-census-semantic-binding.json").read_text())
        expected = {"status_code", "carrier_operation", "docket1_status_code", "safety_rating", "review_type"}
        self.assertEqual({field["field"] for field in binding["fields"]}, expected)
        for field in binding["fields"]:
            self.assertEqual(field["definition_status"], "AUTHORITATIVE_DEFINITION_UNAVAILABLE")
            self.assertIsNone(field["authoritative_definition"])
            self.assertIsNone(field["authoritative_source"])
            self.assertEqual(field["inference_policy"], "PROHIBITED_INFERENCE")
            self.assertEqual(field["eligibility_use"], "BLOCKED_PENDING_AUTHORITATIVE_DEFINITION")
        self.assertEqual(binding["eligibility_rule_status"], "NOT_FROZEN_SEMANTIC_DEPENDENCIES_UNRESOLVED")

    def test_semantic_binding_is_bound_to_exact_official_metadata_bytes(self):
        binding = json.loads((ROOT / "data/fmcsa/company-census-semantic-binding.json").read_text())
        metadata = (ROOT / binding["metadata_evidence"]["path"]).read_bytes()
        self.assertEqual(binding["metadata_evidence"]["sha256"], "sha256:" + hashlib.sha256(metadata).hexdigest())

    def test_schema_distinguishes_available_unavailable_and_prohibited_inference(self):
        schema = json.loads((ROOT / "data/fmcsa/semantic-binding-schema.json").read_text())
        serialized = json.dumps(schema)
        for value in ("AUTHORITATIVE_DEFINITION_AVAILABLE", "AUTHORITATIVE_DEFINITION_UNAVAILABLE", "PROHIBITED_INFERENCE"):
            self.assertIn(value, serialized)


if __name__ == "__main__":
    unittest.main()
