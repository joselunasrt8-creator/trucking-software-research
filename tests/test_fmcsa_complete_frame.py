import importlib.util
import gc
import http.client
import json
import ssl
import tempfile
import unittest
import weakref
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

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
        result = self.pages[offset]
        if isinstance(result, BaseException):
            raise result
        return result


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

    def interrupted_acquisition(self, existing_outputs=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        paths = [root / name for name in ("raw.json", "manifest.json", "schema.json")]
        if existing_outputs:
            for path, content in zip(paths, existing_outputs):
                path.write_bytes(content)
        transport = FakeTransport({
            0: [{"dot_number": "1"}, {"dot_number": "2"}],
            2: [{"dot_number": "3"}, {"dot_number": "4"}],
            4: http.client.IncompleteRead(b'[{"dot_number":"5"}', 100),
        }, versions=(42,))
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "1 attempt"):
            acquire.acquire(
                transport, *paths, page_size=2, retries=0,
                clock=lambda: "2026-08-22T00:00:00+00:00", sleep=lambda _: None,
            )
        return root, paths

    def resume_interrupted(self, root, versions=(42, 42), pages=None, page_size=2):
        paths = [root / name for name in ("raw.json", "manifest.json", "schema.json")]
        transport = FakeTransport(
            pages or {4: [{"dot_number": "5"}]}, versions=versions,
        )
        manifest = acquire.acquire(
            transport, *paths, page_size=page_size,
            clock=lambda: "2026-08-22T01:00:00+00:00", sleep=lambda _: None,
        )
        return transport, manifest

    def test_deterministic_pagination_provenance_and_digest(self):
        pages = {0: [{"dot_number": "1", "legal_name": "A"}, {"dot_number": "2", "legal_name": "B"}],
                 2: [{"dot_number": "3", "legal_name": "C"}]}
        root, transport, first = self.run_acquisition(pages)
        self.assertEqual([p["offset"] for p in first["pages"]], [0, 2])
        self.assertEqual([p["row_count"] for p in first["pages"]], [2, 1])
        self.assertTrue(all("%24order=dot_number+ASC" in url for url in transport.urls if url.startswith(acquire.BASE)))
        self.assertEqual(first["row_count"], 3)
        self.assertEqual(first["ordering_contract"], {
            "field": "dot_number",
            "direction": "ascending",
            "strict": True,
            "missing_identifiers": "reject",
            "duplicate_identifiers": "reject",
        })
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

    def test_page_larger_than_requested_limit_fails_closed(self):
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "exceeds its requested limit"):
            self.run_acquisition({
                0: [{"dot_number": "1"}, {"dot_number": "2"}, {"dot_number": "3"}],
            })

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

    def test_incomplete_read_retry_succeeds_with_only_the_complete_response(self):
        class Flaky:
            def __init__(self):
                self.calls = 0

            def get_json(inner_self, _):
                inner_self.calls += 1
                if inner_self.calls == 1:
                    raise http.client.IncompleteRead(b'[{"dot_number":', 50)
                return [{"dot_number": "1"}]

        sleeps = []
        transport = Flaky()
        result = acquire.retry_get(transport, "fixture://page", retries=2, sleep=sleeps.append)
        self.assertEqual(result, [{"dot_number": "1"}])
        self.assertEqual(transport.calls, 2)
        self.assertEqual(sleeps, [1])

    def test_repeated_incomplete_read_exhausts_retries(self):
        class Truncated:
            def __init__(self):
                self.calls = 0

            def get_json(inner_self, _):
                inner_self.calls += 1
                raise http.client.IncompleteRead(b"partial", 100)

        transport = Truncated()
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "3 attempt"):
            acquire.retry_get(transport, "fixture://page", retries=2, sleep=lambda _: None)
        self.assertEqual(transport.calls, 3)

    def test_retry_classification_covers_socket_ssl_and_http_transients(self):
        transient = [
            ConnectionResetError("reset"),
            TimeoutError("timeout"),
            ssl.SSLEOFError(8, "unexpected EOF"),
            HTTPError("fixture://page", 429, "rate limited", {}, None),
            HTTPError("fixture://page", 503, "unavailable", {}, None),
        ]
        self.assertTrue(all(acquire.is_retryable(error) for error in transient))
        self.assertFalse(acquire.is_retryable(
            ssl.SSLCertVerificationError(1, "certificate rejected")
        ))
        self.assertFalse(acquire.is_retryable(URLError(
            ssl.SSLCertVerificationError(1, "certificate rejected")
        )))
        self.assertFalse(acquire.is_retryable(
            HTTPError("fixture://page", 400, "bad request", {}, None)
        ))

    def test_resume_after_completed_pages_preserves_state_and_starts_at_exact_next_offset(self):
        root, _ = self.interrupted_acquisition()
        checkpoint_path = acquire.checkpoint_path_for(root / "raw.json")
        checkpoint = json.loads(checkpoint_path.read_text())
        state = checkpoint["state"]
        self.assertEqual(state["next_offset"], 4)
        self.assertEqual(state["row_count"], 4)
        self.assertEqual(state["previous_dot_number"], 4)
        self.assertEqual([page["offset"] for page in state["pages"]], [0, 2])

        transport, manifest = self.resume_interrupted(root)
        page_requests = [url for url in transport.urls if url.startswith(acquire.BASE)]
        self.assertEqual(page_requests, [acquire.page_url(2, 4)])
        self.assertEqual([page["offset"] for page in manifest["pages"]], [0, 2, 4])
        self.assertEqual(manifest["row_count"], 5)

    def test_resume_does_not_duplicate_rows(self):
        root, _ = self.interrupted_acquisition()
        self.resume_interrupted(root)
        rows = json.loads((root / "raw.json").read_text())
        identifiers = [int(row["dot_number"]) for row in rows]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(identifiers, [1, 2, 3, 4, 5])

    def test_resume_does_not_skip_rows(self):
        root, _ = self.interrupted_acquisition()
        self.resume_interrupted(root)
        identifiers = [
            int(row["dot_number"])
            for row in json.loads((root / "raw.json").read_text())
        ]
        self.assertEqual(identifiers, list(range(1, 6)))

    def test_resume_discards_only_uncheckpointed_tail_bytes(self):
        root, _ = self.interrupted_acquisition()
        partial_path = acquire.partial_path_for(root / "raw.json")
        with partial_path.open("ab") as stream:
            stream.write(b',{"dot_number":"999"}')
        self.resume_interrupted(root)
        identifiers = [
            int(row["dot_number"])
            for row in json.loads((root / "raw.json").read_text())
        ]
        self.assertEqual(identifiers, [1, 2, 3, 4, 5])

    def test_checkpoint_integrity_corruption_is_rejected(self):
        root, _ = self.interrupted_acquisition()
        checkpoint_path = acquire.checkpoint_path_for(root / "raw.json")
        checkpoint = json.loads(checkpoint_path.read_text())
        checkpoint["state"]["previous_dot_number"] = 999
        checkpoint_path.write_bytes(acquire.canonical_json(checkpoint) + b"\n")
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "integrity digest"):
            self.resume_interrupted(root, versions=(42,))

    def test_stale_checkpoint_is_rejected_when_dataset_mutated_across_resume(self):
        root, _ = self.interrupted_acquisition()
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "stale checkpoint.*rowsUpdatedAt"):
            self.resume_interrupted(root, versions=(43,))
        self.assertTrue(acquire.checkpoint_path_for(root / "raw.json").exists())
        self.assertFalse((root / "raw.json").exists())

    def test_incompatible_checkpoint_output_identity_is_rejected(self):
        root, paths = self.interrupted_acquisition()
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "incompatible checkpoint"):
            acquire.acquire(
                FakeTransport({4: [{"dot_number": "5"}]}, versions=(42, 42)),
                paths[0], root / "different-manifest.json", paths[2], page_size=2,
                clock=lambda: "now", sleep=lambda _: None,
                checkpoint_path=acquire.checkpoint_path_for(paths[0]),
            )

    def test_page_size_order_and_query_mismatches_are_rejected(self):
        root, paths = self.interrupted_acquisition()
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "incompatible checkpoint"):
            self.resume_interrupted(root, versions=(42,), page_size=3)

        root, paths = self.interrupted_acquisition()
        with mock.patch.object(acquire, "ORDER", "dot_number DESC"):
            with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "incompatible checkpoint"):
                self.resume_interrupted(root, versions=(42,))

        root, paths = self.interrupted_acquisition()
        checkpoint_path = acquire.checkpoint_path_for(paths[0])
        checkpoint = json.loads(checkpoint_path.read_text())
        checkpoint["contract"]["query_contract"]["endpoint"] = "https://example.invalid/query"
        unsealed = dict(checkpoint)
        unsealed.pop("checkpoint_digest")
        checkpoint["checkpoint_digest"] = acquire.digest(unsealed)
        checkpoint_path.write_bytes(acquire.canonical_json(checkpoint) + b"\n")
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "incompatible checkpoint"):
            self.resume_interrupted(root, versions=(42,))

    def test_checkpoint_and_partial_are_removed_only_after_successful_finalization(self):
        root, _ = self.interrupted_acquisition()
        checkpoint_path = acquire.checkpoint_path_for(root / "raw.json")
        partial_path = acquire.partial_path_for(root / "raw.json")
        self.assertTrue(checkpoint_path.exists())
        self.assertTrue(partial_path.exists())
        self.resume_interrupted(root)
        self.assertFalse(checkpoint_path.exists())
        self.assertFalse(partial_path.exists())
        self.assertTrue((root / "raw.json").exists())
        self.assertTrue((root / "manifest.json").exists())
        self.assertTrue((root / "schema.json").exists())

    def test_failed_resumed_acquisition_preserves_existing_published_outputs(self):
        old = (b"old raw", b"old manifest", b"old schema")
        root, paths = self.interrupted_acquisition(existing_outputs=old)
        with self.assertRaisesRegex(acquire.CompleteFrameBlocked, "changed during pagination"):
            self.resume_interrupted(root, versions=(42, 43))
        self.assertEqual(tuple(path.read_bytes() for path in paths), old)
        self.assertTrue(acquire.checkpoint_path_for(paths[0]).exists())
        self.assertTrue(acquire.partial_path_for(paths[0]).exists())

    def test_resumed_and_uninterrupted_acquisitions_have_identical_exact_output(self):
        all_pages = {
            0: [{"dot_number": "1"}, {"dot_number": "2"}],
            2: [{"dot_number": "3"}, {"dot_number": "4"}],
            4: [{"dot_number": "5"}],
        }
        uninterrupted_root, _, uninterrupted_manifest = self.run_acquisition(all_pages)
        resumed_root, _ = self.interrupted_acquisition()
        _, resumed_manifest = self.resume_interrupted(resumed_root)
        self.assertEqual(
            (uninterrupted_root / "raw.json").read_bytes(),
            (resumed_root / "raw.json").read_bytes(),
        )
        self.assertEqual(
            uninterrupted_manifest["content_digest"], resumed_manifest["content_digest"]
        )

    def test_audit_verifies_frame_and_schema_provenance_chain(self):
        root, _, manifest = self.run_acquisition({0: [{"dot_number": "1"}]})
        result = audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")
        self.assertEqual(result["content_digest"], manifest["content_digest"])

    def test_audit_accepts_preserved_manifest_ordering_representation(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.pop("ordering_contract")
        manifest_path.write_text(json.dumps(manifest))
        result = audit.audit(root / "raw.json", manifest_path, root / "schema.json")
        self.assertEqual(result["row_count"], 1)

    def test_audit_rejects_noncanonical_ordering_contracts(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["query_contract"]["order"] = "dot_number DESC"
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "ordering query"):
            audit.audit(root / "raw.json", manifest_path, root / "schema.json")

        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["ordering_contract"]["strict"] = False
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "ordering contract"):
            audit.audit(root / "raw.json", manifest_path, root / "schema.json")

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

    def rewrite_audit_frame(self, root, rows, **manifest_overrides):
        raw_path = root / "raw.json"
        raw_path.write_bytes(acquire.canonical_json(rows) + b"\n")
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        identifiers = [str(row["dot_number"]) for row in rows
                       if row.get("dot_number") not in (None, "")]
        seen = set()
        duplicate_count = 0
        for identifier in identifiers:
            if identifier in seen:
                duplicate_count += 1
            else:
                seen.add(identifier)
        manifest.update({
            "content_digest": "sha256:" + acquire.hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "row_count": len(rows),
            "missing_dot_number_count": sum(
                row.get("dot_number") in (None, "") for row in rows
            ),
            "duplicate_dot_number_count": duplicate_count,
            **manifest_overrides,
        })
        manifest_path.write_text(json.dumps(manifest))
        return raw_path, manifest_path

    def test_audit_streams_raw_frame_without_read_bytes(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": str(number), "payload": "x" * 100} for number in range(10000)]
        )
        original = Path.read_bytes

        def reject_raw_read_bytes(path):
            if path == raw_path:
                raise AssertionError("audit loaded the complete frame with read_bytes")
            return original(path)

        with mock.patch.object(Path, "read_bytes", reject_raw_read_bytes):
            result = audit.audit(raw_path, manifest_path, root / "schema.json")
        self.assertEqual(result["row_count"], 10000)

    def test_audit_ordered_unique_identifiers(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": str(number)} for number in range(1, 101)]
        )
        result = audit.audit(raw_path, manifest_path, root / "schema.json")
        self.assertEqual(result["duplicate_dot_number_count"], 0)

    def test_audit_exactly_counts_adjacent_duplicates(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": "1"}, {"dot_number": 1}, {"dot_number": "2"}]
        )
        result = audit.audit(raw_path, manifest_path, root / "schema.json")
        self.assertEqual(result["duplicate_dot_number_count"], 1)

    def test_audit_rejects_identifier_ordering_violation(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": "1"}, {"dot_number": "3"}, {"dot_number": "2"}]
        )
        with self.assertRaisesRegex(ValueError, "ascending dot_number ordering"):
            audit.audit(raw_path, manifest_path, root / "schema.json")

    def test_audit_rejects_malformed_identifier(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": "not-a-number"}]
        )
        with self.assertRaisesRegex(ValueError, "integer identifier"):
            audit.audit(raw_path, manifest_path, root / "schema.json")

    def test_audit_exactly_counts_missing_identifiers(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(
            root, [{"dot_number": "1"}, {}, {"dot_number": "2"}, {"dot_number": ""}]
        )
        result = audit.audit(raw_path, manifest_path, root / "schema.json")
        self.assertEqual(result["missing_dot_number_count"], 2)

    def test_audit_rejects_malformed_json(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        (root / "raw.json").write_bytes(b'[{"dot_number":"1"}')
        with self.assertRaisesRegex(ValueError, "separator|incomplete"):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")
        with mock.patch("builtins.print") as output:
            self.assertEqual(audit.main([
                "--raw", str(root / "raw.json"),
                "--manifest", str(root / "manifest.json"),
                "--schema", str(root / "schema.json"),
            ]), 2)
        self.assertTrue(output.call_args.args[0].startswith("COMPLETE_FRAME_BLOCKED:"))

    def test_audit_rejects_trailing_and_invalid_utf8_input(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        (root / "raw.json").write_bytes(b'[{"dot_number":"1"}] trailing')
        with self.assertRaisesRegex(ValueError, "content after"):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")

        (root / "raw.json").write_bytes(b'[{"dot_number":"1\xff"}]')
        with self.assertRaisesRegex(ValueError, "valid UTF-8"):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")

    def test_audit_rejects_non_object_array_records(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        (root / "raw.json").write_bytes(b'[1]\n')
        with self.assertRaisesRegex(ValueError, "array of objects"):
            audit.audit(root / "raw.json", root / "manifest.json", root / "schema.json")

    def test_audit_rejects_digest_and_row_count_mismatches(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        raw_path, manifest_path = self.rewrite_audit_frame(root, [{"dot_number": "2"}])
        manifest = json.loads(manifest_path.read_text())
        manifest["content_digest"] = "sha256:" + "0" * 64
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "content digest"):
            audit.audit(raw_path, manifest_path, root / "schema.json")

        manifest["content_digest"] = "sha256:" + acquire.hashlib.sha256(raw_path.read_bytes()).hexdigest()
        manifest["row_count"] = 2
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "row count"):
            audit.audit(raw_path, manifest_path, root / "schema.json")

    def test_audit_exactly_counts_missing_and_duplicate_identifiers(self):
        root, _, _ = self.run_acquisition({0: [{"dot_number": "1"}]})
        rows = [{"dot_number": "1"}, {}, {"dot_number": "1"},
                {"dot_number": 2}, {"dot_number": "2"}, {"dot_number": ""}]
        raw_path, manifest_path = self.rewrite_audit_frame(root, rows)
        result = audit.audit(raw_path, manifest_path, root / "schema.json")
        self.assertEqual(result["missing_dot_number_count"], 2)
        self.assertEqual(result["duplicate_dot_number_count"], 2)

        manifest = json.loads(manifest_path.read_text())
        manifest["missing_dot_number_count"] = 0
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "identifier audit"):
            audit.audit(raw_path, manifest_path, root / "schema.json")

        manifest["missing_dot_number_count"] = 2
        manifest["duplicate_dot_number_count"] = 0
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "identifier audit"):
            audit.audit(raw_path, manifest_path, root / "schema.json")


if __name__ == "__main__":
    unittest.main()
