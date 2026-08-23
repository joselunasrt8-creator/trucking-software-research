import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("acquire", ROOT / "scripts/acquire_fmcsa_census.py")
acquire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquire)


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
    def run_acquisition(self, pages, versions=(42, 42)):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        ticks = iter(f"2026-08-22T00:00:0{i}+00:00" for i in range(20))
        transport = FakeTransport(pages, versions)
        manifest = acquire.acquire(transport, root / "raw.json", root / "manifest.json", root / "schema.json",
                                    page_size=2, clock=lambda: next(ticks), sleep=lambda _: None)
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

    def test_version_change_fails_closed_without_outputs(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "changed"):
            acquire.acquire(FakeTransport({0: []}, (1, 2)), root / "raw", root / "manifest", root / "schema",
                            page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertFalse((root / "raw").exists())

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


if __name__ == "__main__":
    unittest.main()
