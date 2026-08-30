import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("motus", ROOT / "scripts/acquire_fmcsa_motus.py")
motus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motus)

COLUMNS = [
    {"fieldName": "usdot_number", "name": "USDOT", "dataTypeName": "number"},
    {"fieldName": "op_auth_type", "name": "Authority type", "dataTypeName": "text"},
    {"fieldName": "op_auth_status", "name": "Authority status", "dataTypeName": "text"},
    {"fieldName": "docket_number", "name": "Docket", "dataTypeName": "text"},
]


def row(identity, usdot="10", docket="MC1"):
    return {":id": identity, "usdot_number": usdot, "docket_number": docket,
            "op_auth_type": "A", "op_auth_status": "ACTIVE"}


class FakeTransport:
    def __init__(self, pages, versions=(1787999953, 1787999953)):
        self.pages = pages
        self.versions = iter(versions)
        self.urls = []

    def get_json(self, url):
        self.urls.append(url)
        if url == motus.VIEW:
            return {"rowsUpdatedAt": next(self.versions)}
        if url == motus.SCHEMA_URL:
            return COLUMNS
        offset = int(url.split("%24offset=")[1].split("&")[0])
        value = self.pages[offset]
        if isinstance(value, BaseException):
            raise value
        return value


class MotusAcquisitionTests(unittest.TestCase):
    def paths(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        return root, (root / "raw.json", root / "manifest.json", root / "schema.json")

    def acquire(self, pages, versions=(1787999953, 1787999953), ticks=None):
        root, paths = self.paths()
        ticks = iter(ticks or [f"2026-08-30T04:42:{n:02d}Z" for n in range(20)])
        manifest = motus.acquire(FakeTransport(pages, versions), *paths, page_size=2,
                                 clock=lambda: next(ticks), sleep=lambda _: None)
        return root, paths, manifest

    def test_duplicate_usdot_and_docket_rows_are_preserved(self):
        root, _, manifest = self.acquire({0: [row("a"), row("b")], 2: []})
        rows = json.loads((root / "raw.json").read_text())
        self.assertEqual(len(rows), 2)
        self.assertEqual([r["usdot_number"] for r in rows], ["10", "10"])
        self.assertIn("preserved without deduplication", manifest["duplicate_semantics"])

    def test_duplicate_id_is_rejected(self):
        root, paths = self.paths()
        with self.assertRaisesRegex(motus.CompleteFrameBlocked, "duplicate :id"):
            motus.acquire(FakeTransport({0: [row("a"), row("a")]}), *paths,
                          page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertFalse(paths[0].exists())
        self.assertFalse(paths[1].exists())

    def test_missing_id_is_rejected(self):
        bad = row("a"); bad.pop(":id")
        with self.assertRaisesRegex(motus.CompleteFrameBlocked, ":id"):
            self.acquire({0: [bad]})

    def test_missing_and_invalid_usdot_are_rejected(self):
        for value in (None, "", "x", "0", -1, True):
            with self.subTest(value=value):
                bad = row("a", value)
                with self.assertRaisesRegex(motus.CompleteFrameBlocked, "usdot_number"):
                    self.acquire({0: [bad]})

    def test_version_change_blocks_publication(self):
        root, paths = self.paths()
        with self.assertRaisesRegex(motus.CompleteFrameBlocked, "changed during pagination"):
            motus.acquire(FakeTransport({0: [row("a")]}, (1, 2)), *paths,
                          page_size=2, clock=lambda: "now", sleep=lambda _: None)
        self.assertFalse(paths[0].exists())
        self.assertFalse(paths[1].exists())
        self.assertTrue(motus.checkpoint_path_for(paths[0]).exists())

    def test_checkpoint_resume_integrity_and_exact_next_offset(self):
        root, paths = self.paths()
        first = FakeTransport({0: [row("a"), row("b")], 2: RuntimeError("stop")}, (7,))
        with self.assertRaisesRegex(RuntimeError, "stop"):
            motus.acquire(first, *paths, page_size=2, clock=lambda: "same", sleep=lambda _: None)
        resumed = FakeTransport({2: [row("c")]}, (7, 7))
        manifest = motus.acquire(resumed, *paths, page_size=2,
                                 clock=lambda: "same", sleep=lambda _: None)
        self.assertEqual([r[":id"] for r in json.loads(paths[0].read_text())], ["a", "b", "c"])
        self.assertEqual([u for u in resumed.urls if u.startswith(motus.BASE)], [motus.page_url(2, 2)])
        self.assertEqual(manifest["row_count"], 3)

    def test_deterministic_artifact_and_manifest(self):
        pages = {0: [row("z9", "11"), row("a1", "12")], 2: []}
        ticks = ["fixed"] * 20
        one, _, first = self.acquire(pages, ticks=ticks)
        two, _, second = self.acquire(pages, ticks=ticks)
        self.assertEqual((one / "raw.json").read_bytes(), (two / "raw.json").read_bytes())
        # Output paths are intentionally provenance-bound; normalize them when comparing manifests.
        self.assertEqual(first, second)
        self.assertEqual((one / "manifest.json").read_bytes(), (two / "manifest.json").read_bytes())

    def test_candidate_rule_remains_unfrozen(self):
        candidate = json.loads((ROOT / "data/fmcsa/carrier-eligibility-rule-candidate.json").read_text())
        self.assertEqual(candidate["status"], "CANDIDATE_ONLY")
        self.assertIs(candidate["rule_frozen"], False)


if __name__ == "__main__":
    unittest.main()
