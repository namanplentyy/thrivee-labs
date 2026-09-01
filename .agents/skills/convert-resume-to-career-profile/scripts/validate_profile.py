#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_repository_root(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(completed.stdout.strip()).resolve()


def load_repository_module(repository_root: Path, relative_path: str, module_name: str):
    module_path = repository_root / relative_path
    if not module_path.is_file():
        raise ValueError(f"Repository module not found: {module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Unable to load the repository module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_repository_validator(repository_root: Path):
    return load_repository_module(
        repository_root, "scripts/validate_examples.py", "thrivee_profile_validator"
    )


def resolve_schema(
    repository_root: Path, document: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    manifest_path = repository_root / "schemas" / "schema-manifest.json"
    manifest = load_json(manifest_path)
    version = document.get("schemaVersion")
    if not isinstance(version, str):
        raise ValueError("Document must declare a string schemaVersion.")
    entry = manifest.get("versions", {}).get(version)
    if not isinstance(entry, dict):
        raise ValueError(f"schemaVersion {version!r} is not declared in the manifest.")
    return version, entry, manifest


def document_type(document: dict[str, Any]) -> str:
    declared = document.get("@type")
    if not isinstance(declared, str):
        raise ValueError("Canonical document must declare a string @type.")
    return declared


def schema_paths(entry: dict[str, Any], declared_type: str) -> tuple[str, str]:
    """The canonical and transport schema for one document type of one version."""
    if declared_type == "CareerProfile":
        return entry["canonicalSchema"], entry["transportSchema"]
    additional = entry.get("additionalDocuments", {}).get(declared_type)
    if not isinstance(additional, dict):
        raise ValueError(
            f"Document type {declared_type!r} is not declared for this schema version."
        )
    return additional["canonicalSchema"], additional["transportSchema"]


def counts_for(document: dict[str, Any], declared_type: str) -> dict[str, int]:
    if declared_type == "OpportunityIntent":
        names = (
            "targetRoles",
            "preferredLocations",
            "employmentTypes",
            "constraints",
            "preferences",
            "taxonomyMappings",
            "ambiguities",
            "warnings",
        )
    else:
        names = (
            "identity",
            "history",
            "sharedClaims",
            "capabilities",
            "skills",
            "artifacts",
            "evidence",
            "verifications",
            "taxonomyMappings",
            "interests",
            "languages",
            "attributes",
            "ambiguities",
            "warnings",
        )
    return {name: len(document[name]) for name in names if isinstance(document.get(name), list)}


def run_semantic_checks(
    repository_root: Path,
    version: str,
    document: dict[str, Any],
    declared_type: str,
    companion_profile: dict[str, Any] | None,
) -> None:
    if version.startswith("0.1."):
        load_repository_validator(repository_root).validate_semantics(document)
        return

    v02 = load_repository_module(
        repository_root, "scripts/validate_v0_2.py", "thrivee_v0_2_validator"
    )
    if declared_type == "CareerProfile":
        v02.run_profile_checks(document)
        return
    if declared_type == "OpportunityIntent":
        if companion_profile is None:
            raise ValueError(
                "Validating an OpportunityIntent requires its CareerProfile: pass "
                "--companion-profile."
            )
        v02.run_intent_checks(document, companion_profile)
        return
    raise ValueError(f"No semantic checks are defined for document type {declared_type!r}.")


def repository_value(repository_root: Path, args: list[str]) -> str | None:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def validate_profile(
    profile_path: Path,
    repository_root: Path,
    require_git_ignored: bool = False,
    companion_profile_path: Path | None = None,
) -> dict[str, Any]:
    profile_path = profile_path.resolve()
    document = load_json(profile_path)
    if not isinstance(document, dict):
        raise ValueError("Document root must be a JSON object.")

    declared_type = document_type(document)
    version, entry, manifest = resolve_schema(repository_root, document)
    validator = load_repository_validator(repository_root)
    validator.validate_schema_manifest(manifest)

    canonical_relative, transport_relative = schema_paths(entry, declared_type)
    canonical_path = repository_root / canonical_relative
    transport_path = repository_root / transport_relative
    converter_path = repository_root / entry["converter"]
    canonical_schema = load_json(canonical_path)
    transport_schema = load_json(transport_path)

    companion_profile = (
        load_json(companion_profile_path.resolve()) if companion_profile_path else None
    )

    validator.validate_schema(document, canonical_schema, declared_type)
    run_semantic_checks(
        repository_root, version, document, declared_type, companion_profile
    )

    transport_completed = subprocess.run(
        ["node", str(converter_path), "--to-transport", str(profile_path)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    transport = json.loads(transport_completed.stdout)
    validator.validate_schema(transport, transport_schema, f"Transport {declared_type}")

    with tempfile.TemporaryDirectory(prefix="career-profile-roundtrip-") as temp_dir:
        transport_file = Path(temp_dir) / "transport.json"
        transport_file.write_text(
            json.dumps(transport, indent=2) + "\n", encoding="utf-8"
        )
        canonical_completed = subprocess.run(
            ["node", str(converter_path), "--to-canonical", str(transport_file)],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
        round_tripped = json.loads(canonical_completed.stdout)
    if round_tripped != document:
        raise ValueError("Canonical-to-transport-to-canonical round-trip changed the document.")

    if require_git_ignored:
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", str(profile_path)],
            cwd=repository_root,
        )
        if ignored.returncode != 0:
            raise ValueError("Private profile path is not ignored by Git.")

    return {
        "status": "valid",
        "documentType": declared_type,
        "schemaVersion": version,
        "schemaStatus": entry["status"],
        "canonicalSchema": canonical_relative,
        "canonicalSchemaSha256": sha256_file(canonical_path),
        "schemaManifest": "schemas/schema-manifest.json",
        "schemaManifestSha256": sha256_file(
            repository_root / "schemas" / "schema-manifest.json"
        ),
        "semanticContract": entry["semanticContract"],
        "semanticContractSha256": sha256_file(
            repository_root / entry["semanticContract"]
        ),
        "extractionContract": entry["extractionContract"],
        "extractionContractSha256": sha256_file(
            repository_root / entry["extractionContract"]
        ),
        "profileSha256": sha256_file(profile_path),
        "semanticChecksPassed": True,
        "canonicalTransportRoundTripLossless": True,
        "gitIgnored": True if require_git_ignored else None,
        "repository": {
            "url": repository_value(repository_root, ["config", "--get", "remote.origin.url"]),
            "revision": repository_value(repository_root, ["rev-parse", "HEAD"]),
            "dirty": bool(
                repository_value(
                    repository_root,
                    ["status", "--porcelain", "--untracked-files=no"],
                )
            ),
        },
        "counts": counts_for(document, declared_type),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a canonical Thrivee CareerProfile or OpportunityIntent and its lossless "
            "transport round-trip."
        )
    )
    parser.add_argument("profile", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument(
        "--companion-profile",
        type=Path,
        help="The CareerProfile an OpportunityIntent refers to. Required for intent documents.",
    )
    parser.add_argument("--require-git-ignored", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_path = args.profile.expanduser().resolve()
    if not profile_path.is_file():
        raise SystemExit(f"Document not found: {profile_path}")
    companion = args.companion_profile.expanduser() if args.companion_profile else None
    if companion is not None and not companion.is_file():
        raise SystemExit(f"Companion profile not found: {companion}")
    repository_root = (
        args.repo_root.expanduser().resolve()
        if args.repo_root
        else find_repository_root(Path.cwd())
    )
    try:
        report = validate_profile(
            profile_path, repository_root, args.require_git_ignored, companion
        )
    except Exception as error:
        raise SystemExit(f"Validation failed: {error}") from error
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
