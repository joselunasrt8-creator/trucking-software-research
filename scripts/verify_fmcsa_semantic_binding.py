#!/usr/bin/env python3
"""Fail-closed verifier for authoritative FMCSA coded-field bindings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

BINDING = Path("data/fmcsa/company-census-semantic-binding.json")
EXPECTED_FIELDS = {
    "status_code", "carrier_operation", "docket1_status_code", "safety_rating", "review_type"
}
OFFICIAL_HOSTS = {"data.transportation.gov", "fmcsa.dot.gov", "www.fmcsa.dot.gov", "safer.fmcsa.dot.gov"}
AVAILABLE = "AUTHORITATIVE_DEFINITION_AVAILABLE"
UNAVAILABLE = "AUTHORITATIVE_DEFINITION_UNAVAILABLE"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def verify(binding_path=BINDING, root=Path(".")):
    errors = []
    try:
        binding = json.loads(Path(binding_path).read_text())
    except (OSError, json.JSONDecodeError) as error:
        return {"determination": "SEMANTIC_BINDING_BLOCKED", "errors": [f"binding unreadable or malformed: {error}"]}
    if not isinstance(binding, dict) or binding.get("artifact_format") != "fmcsa-semantic-binding-v2":
        errors.append("unsupported or missing semantic-binding format")
    if binding.get("dataset_id") != "az4n-8mr2":
        errors.append("binding dataset identity is not az4n-8mr2")

    sources = binding.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("authoritative source inventory is missing")
        sources = []
    source_map = {}
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source entry is malformed")
            continue
        source_id = source.get("source_id")
        if not source_id or source_id in source_map:
            errors.append("source ID is missing or duplicated")
            continue
        source_map[source_id] = source
        if urlparse(source.get("source_url", "")).hostname not in OFFICIAL_HOSTS:
            errors.append(f"{source_id}: source URL is not on an authoritative FMCSA/U.S. DOT host")
        artifact = root / source.get("artifact_path", "")
        if not artifact.is_file():
            errors.append(f"{source_id}: preserved source artifact is absent")
            continue
        if source.get("byte_size") != artifact.stat().st_size:
            errors.append(f"{source_id}: preserved source byte size mismatch")
        if source.get("sha256") != sha256(artifact):
            errors.append(f"{source_id}: preserved source SHA-256 mismatch")

    metadata_sources = [source for source in sources if source.get("dataset_id") == "az4n-8mr2"
                        and source.get("title") == "Company Census File dataset metadata"]
    dictionary_sources = [source for source in sources if source.get("dataset_id") == "az4n-8mr2"
                          and source.get("document_revision")]
    if len(metadata_sources) != 1 or len(dictionary_sources) != 1:
        errors.append("exactly one dataset metadata source and one revisioned dictionary source are required")
    elif all((root / source["artifact_path"]).is_file() for source in (metadata_sources[0], dictionary_sources[0])):
        try:
            metadata = json.loads((root / metadata_sources[0]["artifact_path"]).read_text())
            attachments = metadata.get("metadata", {}).get("attachments", [])
        except (OSError, json.JSONDecodeError, AttributeError) as error:
            errors.append(f"dataset metadata artifact is malformed: {error}")
        else:
            dictionary = dictionary_sources[0]
            matches = [item for item in attachments if item.get("assetId") == dictionary.get("asset_id")]
            if metadata.get("id") != "az4n-8mr2" or len(matches) != 1:
                errors.append("dataset metadata does not bind the dictionary attachment identity")

    motus_metadata = [source for source in sources if source.get("dataset_id") == "inys-ebih"
                      and source.get("title") == "Motus Carrier - All With History dataset metadata"]
    motus_dictionaries = [source for source in sources if source.get("dataset_id") == "inys-ebih"
                          and source.get("document_revision")]
    if len(motus_metadata) != 1 or len(motus_dictionaries) != 1:
        errors.append("exactly one MOTUS metadata source and one MOTUS dictionary source are required")
    elif all((root / source["artifact_path"]).is_file() for source in (motus_metadata[0], motus_dictionaries[0])):
        try:
            metadata = json.loads((root / motus_metadata[0]["artifact_path"]).read_text())
            attachments = metadata.get("metadata", {}).get("attachments", [])
        except (OSError, json.JSONDecodeError, AttributeError) as error:
            errors.append(f"MOTUS metadata artifact is malformed: {error}")
        else:
            dictionary = motus_dictionaries[0]
            matches = [item for item in attachments if item.get("assetId") == dictionary.get("asset_id")]
            if metadata.get("id") != "inys-ebih" or len(matches) != 1:
                errors.append("MOTUS metadata does not bind the dictionary attachment identity")

    fields = binding.get("fields")
    if not isinstance(fields, list):
        errors.append("field bindings are missing")
        fields = []
    names = [field.get("field") for field in fields if isinstance(field, dict)]
    if set(names) != EXPECTED_FIELDS or len(names) != len(EXPECTED_FIELDS):
        errors.append("field bindings must contain each required coded field exactly once")
    field_results = []
    for field in fields:
        if not isinstance(field, dict):
            errors.append("field binding is malformed")
            continue
        name = field.get("field", "unknown")
        field_errors = []
        status = field.get("definition_status")
        if status not in {AVAILABLE, UNAVAILABLE}:
            field_errors.append("definition status is invalid")
        if field.get("inference_policy") != "PROHIBITED_INFERENCE":
            field_errors.append("inference policy must remain prohibited")
        codes = field.get("code_values")
        unresolved = field.get("unresolved_code_values")
        if not isinstance(codes, list) or not isinstance(unresolved, list):
            field_errors.append("code-value or unresolved-code inventory is malformed")
            codes, unresolved = [], []
        code_names = [code.get("value") for code in codes if isinstance(code, dict)]
        if len(code_names) != len(set(code_names)):
            field_errors.append("bound code values are duplicated")
        if set(code_names) & set(unresolved):
            field_errors.append("a code value cannot be both bound and unresolved")
        citations = [field.get("definition_citation")] + [code.get("citation") for code in codes if isinstance(code, dict)]
        for citation in citations:
            if not isinstance(citation, dict) or citation.get("source_id") not in source_map:
                field_errors.append("definition or code citation does not resolve to a preserved source")
                break
            pages = citation.get("pages")
            if not isinstance(pages, list) or not pages or any(isinstance(page, bool) or not isinstance(page, int) or page < 1 for page in pages):
                field_errors.append("citation page locator is invalid")
                break
        if status == AVAILABLE:
            if not field.get("authoritative_definition") or unresolved:
                field_errors.append("AVAILABLE requires a definition and no unresolved code values")
            if field.get("eligibility_use") != "PERMITTED_AFTER_RULE_FREEZE":
                field_errors.append("AVAILABLE eligibility disposition is invalid")
        if status == UNAVAILABLE:
            if not unresolved or not field.get("limitation"):
                field_errors.append("UNAVAILABLE requires explicit unresolved values and limitation")
            if field.get("eligibility_use") != "BLOCKED_PENDING_AUTHORITATIVE_DEFINITION":
                field_errors.append("UNAVAILABLE eligibility disposition is invalid")
        errors.extend(f"{name}: {message}" for message in field_errors)
        field_results.append({"field": name, "definition_status": status, "errors": field_errors})

    if binding.get("eligibility_rule_status") not in {
        "NOT_FROZEN_SEMANTIC_DEPENDENCIES_UNRESOLVED",
        "NOT_FROZEN_CANDIDATE_INPUT_DATA_UNAVAILABLE",
    }:
        errors.append("eligibility rule must remain not frozen while semantic dependencies are unresolved")
    if not any(item.get("definition_status") == UNAVAILABLE for item in field_results):
        errors.append("v2 determination expects at least one explicitly unresolved field")
    determination = "SEMANTIC_BINDING_PARTIALLY_BOUND" if not errors else "SEMANTIC_BINDING_BLOCKED"
    return {"determination": determination, "fields": field_results, "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", type=Path, default=BINDING)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    result = verify(args.binding, args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["determination"] == "SEMANTIC_BINDING_PARTIALLY_BOUND" else 2


if __name__ == "__main__":
    raise SystemExit(main())
