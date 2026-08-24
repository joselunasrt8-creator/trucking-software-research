import importlib.util
import gc
import json
import tempfile
import unittest
import weakref
from pathlib import Path
from urllib.error import URLError

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("acquire", ROOT / "scripts/acquire_fmcsa_census.py")
acquire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquire)
audit_spec = importlib.util.spec_from_file_location("audit", ROOT / "scripts/audit_fmcsa_census.py")
audit = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit)


COLUMNS = [
    {"fieldName": "dot_number", "name": "USDOT Number", "description": "Unique identifier assigned to a company.", "dataTypeName": "number"},
    {"fieldName": "legal_name", "name": "Legal Name", "description": None, "dataTypeName": "text"},
]


class FakeTransport:
    def __init__(self, pages, versions=(42, 42)):
        self.pages = pages
        self.versions = iter(versions)
        self.urls = []

    def get_json(self, url):
        self.urls.append(url)
        if url == acquire.VIEW:
            return {"rowsUpdatedAt": next(self.versions)}
        if url == acquire.SCHEMA_URL:
            return COLUMNS
        offset = int(url.split("%24offset=")[1].split("&")[0])
        return self.pages[offset]


class CompleteFrameTests(unittest.TestCase):
    def run_acquisition(self, pages, versions=(42, 42), page_size=2):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        ticks = iter(f"2026-08-22T00:00:0{i}+00:00" for i in range(20))
        transport = FakeTransport(pages, versions)
        manifest = acquire.acquire(transport, root / "raw.json", root / "manifest.json", root / "schema.json",
                                    page_size=page_size, clock=lambda: next(ticks), sleep=lambda _: None)
        return root, transport, manifest

    def test_deterministic_pagination_provenance_and_digest(self):
        pages = {0: [{"dot_number": "1", "legal_name": "A"}, {"dot_number": "2", "legal_name": "B"}],
                 2: [{"dot_number": "3", "legal_name": "C"}]}
        root, transport, first = self.run_acquisition(pages)
        self.assertEqual([p["offset"] for p in first["pages"]], [0, 2])
        self.assertEqual([p["row_count"] for p in first["pages"]], [2, 1])
        self.assertTrue(all("%24order=dot_number+ASC" in url for url in transport.urls if url.startswith(acquire.BASE)))
        self.assertEqual(first["row_count"], 3)
        self.assertEqual(first["content_digest"], "sha256:" + acquire.hashlib.sha256((root / "raw.json").read_bytes()).hexdigest())
        _, _, second = self.run_acquisition(pages)
        self.assertEqual(first["content_digest"], second["content_digest"])
        self.assertEqual([p["content_digest"] for p in first["pages"]], [p["content_digest"] for p in second["pages"]])

    def test_streamed_artifact_is_exact_canonical_json_array(self):
        rows = [{"legal_name": "Café", "dot_number": "1"}, {"z": 2, "dot_number": "2", "a": 1}]
        root, _, manifest = self.run_acquisition({0: rows, 2: []})
        expected = acquire.canonical_json(rows) + b"\n"
        self.assertEqual((root / "raw.json").read_bytes(), expected)
        self.assertEqual(manifest["content_digest"], "sha256:" + acquire.hashlib.sha256(expected).hexdigest())

    def test_page_size_does_not_change_logical_frame(self):
        rows = [{"dot_number": str(number), "name": chr(64 + number)} for number in range(1, 6)]
        root_two, _, manifest_two = self.run_acquisition(
            {0: rows[:2], 2: rows[2:4], 4: rows[4:]}, page_size=2)
        root_three, _, manifest_three = self.run_acquisition(
            {0: rows[:3], 3: rows[3:]}, page_size=3)
        self.assertEqual((root_two / "raw.json").read_bytes(), (root_three / "raw.json").read_bytes())
        self.assertEqual(manifest_two["content_digest"], manifest_three["content_digest"])

    def test_exact_multiple_requests_empty_terminal_page(self):
        _, _, manifest = self.run_acquisition({0: [{"dot_number": "1"}, {"dot_number": "2"}], 2: []})
        self.assertEqual(manifest["page_count"], 2)
        self.assertEqual(manifest["pages"][-1]["row_count"], 0)

    def test_rejects_out_of_order_response(self):
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "ordering"):
            self.run_acquisition({0: [{"dot_number": "2"}, {"dot_number": "1"}], 2: []})

    def test_duplicate_and_missing_identifiers_fail_closed(self):
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "duplicate"):
            self.run_acquisition({0: [{"dot_number": "1"}, {"dot_number": "1"}], 2: []})
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "missing"):
            self.run_acquisition({0: [{"dot_number": "1"}, {}], 2: []})

    def test_malformed_identifier_fails_closed(self):
        for malformed in ("not-a-number", 1.5, True):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "integer identifier"):
                    self.run_acquisition({0: [{"dot_number": malformed}]})

    def test_version_change_fails_closed_without_outputs(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "changed"):
            acquire.acquire(FakeTransport({0: []}, (1, 2)), root / "raw", root / "manifest", root / "schema",
                            page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertFalse((root / "raw").exists())

    def test_failure_does_not_replace_existing_artifacts(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        paths = [root / name for name in ("raw", "manifest", "schema")]
        for path, content in zip(paths, (b"old raw", b"old manifest", b"old schema")):
            path.write_bytes(content)
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "changed"):
            acquire.acquire(FakeTransport({0: [{"dot_number": "1"}]}, (1, 2)), *paths,
                            page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertEqual([path.read_bytes() for path in paths], [b"old raw", b"old manifest", b"old schema"])
        self.assertEqual(list(root.glob("*.tmp")), [])

    def test_completed_pages_are_released_during_acquisition(self):
        class Page(list):
            pass

        class GeneratingTransport:
            def __init__(self):
                self.version_calls = 0
                self.references = []
                self.prior_pages_alive = []

            def get_json(inner_self, url):
                if url == acquire.VIEW:
                    inner_self.version_calls += 1
                    return {"rowsUpdatedAt": 42}
                if url == acquire.SCHEMA_URL:
                    return COLUMNS
                gc.collect()
                inner_self.prior_pages_alive.append(sum(reference() is not None for reference in inner_self.references))
                offset = int(url.split("%24offset=")[1].split("&")[0])
                page = Page([] if offset == 10 else [
                    {"dot_number": str(offset + 1)}, {"dot_number": str(offset + 2)}])
                inner_self.references.append(weakref.ref(page))
                return page

        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        transport = GeneratingTransport()
        acquire.acquire(transport, root / "raw", root / "manifest", root / "schema",
                        page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertTrue(transport.prior_pages_alive)
        self.assertLessEqual(max(transport.prior_pages_alive), 1)

    def test_schema_preserves_authoritative_metadata_and_unresolved_definition(self):
        binding = acquire.schema_binding(COLUMNS, "now")
        self.assertEqual(binding["fields"][0]["authoritative_label"], "USDOT Number")
        self.assertIn("no description", binding["fields"][1]["unresolved_definition"])
        self.assertEqual(binding["content_digest"], acquire.digest(COLUMNS))

    def test_retry_exhaustion_is_blocked(self):
        class Broken:
            def get_json(self, _): raise URLError("offline")
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "3 attempt"):
            acquire.retry_get(Broken(), "fixture://offline", retries=2, sleep=lambda _: None)

    def test_audit_verifies_frame_and_schema_provenance_chain(self):
        root, _, manifest = self.run_acquisition({0: [{"dot_number": "1"}]})
        result = audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")
        self.assertEqual(result["content_digest"], manifest["content_digest"])

    def test_audit_rejects_missing_and_malformed_schema(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        (root / "schema.json").unlink()
        with self.assertRaises(FileNotFoundError):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")
        (root / "schema.json").write_text("not json")
        with self.assertRaises(json.JSONDecodeError):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")

    def test_audit_rejects_tampered_schema(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        schema_path = root / "schema.json"
        schema = json.loads(schema_path.read_text())
        schema["fields"][0]["authoritative_label"] = "tampered"
        schema_path.write_text(json.dumps(schema))
        with self.assertRaisesRegex(ValueError, "artifact digest"):
            audit.audit(root / "raw.json", root / "manifest.json", schema_path)

    def test_audit_rejects_dataset_and_source_identity_changes(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["dataset_identity"]["id"] = "wrong-id"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "dataset identity"):
            audit.audit(root / "raw.json", manifest_path, root / "schema.json")

        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema_identity"]["source_url"] = "https://example.invalid/schema"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "source identity"):
            audit.audit(root / "raw.json", manifest_path, root / "schema.json")


if __name__ == "__main__":
    unittest.main()
