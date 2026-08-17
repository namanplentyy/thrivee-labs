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


def load_repository_validator(repository_root: Path):
    validator_path = repository_root / "scripts" / "validate_examples.py"
    if not validator_path.is_file():
        raise ValueError(f"Repository validator not found: {validator_path}")
    spec = importlib.util.spec_from_file_location("thrivee_profile_validator", validator_path)
    if spec is None or spec.loader is None:
        raise ValueError("Unable to load the repository validator.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_schema(
    repository_root: Path, profile: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    manifest_path = repository_root / "schemas" / "schema-manifest.json"
    manifest = load_json(manifest_path)
    version = profile.get("schemaVersion")
    if not isinstance(version, str):
        raise ValueError("Profile must declare a string schemaVersion.")
    entry = manifest.get("versions", {}).get(version)
    if not isinstance(entry, dict):
        raise ValueError(f"schemaVersion {version!r} is not declared in the manifest.")
    return version, entry, manifest


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
) -> dict[str, Any]:
    profile_path = profile_path.resolve()
    profile = load_json(profile_path)
    if not isinstance(profile, dict):
        raise ValueError("Profile root must be a JSON object.")

    version, entry, manifest = resolve_schema(repository_root, profile)
    validator = load_repository_validator(repository_root)
    validator.validate_schema_manifest(manifest)

    canonical_path = repository_root / entry["canonicalSchema"]
    transport_path = repository_root / entry["transportSchema"]
    converter_path = repository_root / entry["converter"]
    canonical_schema = load_json(canonical_path)
    transport_schema = load_json(transport_path)
    validator.validate_schema(profile, canonical_schema, "CareerProfile")
    validator.validate_semantics(profile)

    transport_completed = subprocess.run(
        ["node", str(converter_path), "--to-transport", str(profile_path)],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    transport = json.loads(transport_completed.stdout)
    validator.validate_schema(transport, transport_schema, "Transport profile")

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
    if round_tripped != profile:
        raise ValueError("Canonical-to-transport-to-canonical round-trip changed the profile.")

    if require_git_ignored:
        ignored = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", str(profile_path)],
            cwd=repository_root,
        )
        if ignored.returncode != 0:
            raise ValueError("Private profile path is not ignored by Git.")

    return {
        "status": "valid",
        "schemaVersion": version,
        "schemaStatus": entry["status"],
        "canonicalSchema": entry["canonicalSchema"],
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
        "counts": {
            "identity": len(profile.get("identity", [])),
            "history": len(profile.get("history", [])),
            "skills": len(profile.get("skills", [])),
            "interests": len(profile.get("interests", [])),
            "languages": len(profile.get("languages", [])),
            "attributes": len(profile.get("attributes", [])),
            "ambiguities": len(profile.get("ambiguities", [])),
            "warnings": len(profile.get("warnings", [])),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a canonical Thrivee CareerProfile and its lossless transport round-trip."
    )
    parser.add_argument("profile", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--require-git-ignored", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile_path = args.profile.expanduser().resolve()
    if not profile_path.is_file():
        raise SystemExit(f"Profile not found: {profile_path}")
    repository_root = (
        args.repo_root.expanduser().resolve()
        if args.repo_root
        else find_repository_root(Path.cwd())
    )
    try:
        report = validate_profile(
            profile_path, repository_root, args.require_git_ignored
        )
    except Exception as error:
        raise SystemExit(f"Validation failed: {error}") from error
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
