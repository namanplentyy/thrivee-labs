#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from validate_profile import find_repository_root, load_json, sha256_file, validate_profile


def git_ignored(repository_root: Path, path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", str(path)],
        cwd=repository_root,
    )
    return completed.returncode == 0


def parse_timestamp(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Finalize a validated CareerProfile in a private, collision-resistant run directory."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--timestamp", help="UTC timestamp in YYYYMMDDTHHMMSSZ form")
    parser.add_argument(
        "--visual-review-status",
        required=True,
        choices=("completed", "unavailable-user-approved"),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = (
        args.repo_root.expanduser().resolve()
        if args.repo_root
        else find_repository_root(Path.cwd())
    )
    source_pdf = args.pdf.expanduser().resolve()
    profile_path = args.profile.expanduser().resolve()
    inventory_path = args.inventory.expanduser().resolve()
    for path, label in (
        (source_pdf, "PDF"),
        (profile_path, "profile"),
        (inventory_path, "source inventory"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} not found: {path}")
    for path, label in ((profile_path, "Draft profile"), (inventory_path, "Inventory")):
        try:
            path.relative_to(repository_root)
        except ValueError:
            continue
        raise SystemExit(f"{label} must remain outside the repository until finalization.")

    inventory = load_json(inventory_path)
    profile = load_json(profile_path)
    source_hash = sha256_file(source_pdf)
    expected_digest = f"sha256:{source_hash}"
    source = inventory.get("source", {})
    if source.get("contentDigest") != expected_digest:
        raise SystemExit("Source inventory digest does not match the supplied PDF.")
    if source.get("pageCount") != len(inventory.get("pages", [])):
        raise SystemExit("Source inventory page count is inconsistent.")
    if not any(page.get("text", "").strip() for page in inventory.get("pages", [])):
        raise SystemExit("Source inventory has no extractable text; OCR is required.")
    rendering_status = (
        inventory.get("extraction", {}).get("rendering", {}).get("status")
    )
    if args.visual_review_status == "completed" and rendering_status != "completed":
        raise SystemExit("Visual review cannot be completed because rendering is unavailable.")
    if (
        args.visual_review_status == "unavailable-user-approved"
        and rendering_status != "unavailable"
    ):
        raise SystemExit(
            "Use visual-review status 'completed' when rendered pages are available."
        )

    matching_documents = [
        document
        for document in profile.get("sourceDocuments", [])
        if document.get("contentDigest") == expected_digest
    ]
    if len(matching_documents) != 1:
        raise SystemExit("Profile must contain exactly one source document matching the PDF.")
    if matching_documents[0].get("pageCount") != source.get("pageCount"):
        raise SystemExit("Profile source page count does not match the prepared PDF.")
    if matching_documents[0].get("id") != source.get("sourceDocumentId"):
        raise SystemExit("Profile source document ID does not match the prepared PDF.")

    validation = validate_profile(profile_path, repository_root)
    repository = validation["repository"]
    if not args.dry_run:
        if not repository["url"] or not repository["revision"]:
            raise SystemExit(
                "Finalization requires a committed Git repository with a configured remote."
            )
        if repository["dirty"]:
            raise SystemExit(
                "Finalization requires a clean tracked worktree so the recorded revision is reproducible."
            )
    timestamp = parse_timestamp(args.timestamp)
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    run_name = f"{stamp}--src-{source_hash[:12]}"
    output_root = repository_root / "private" / "career-profile-runs"
    run_dir = output_root / timestamp.strftime("%Y") / timestamp.strftime("%m") / run_name
    version_parts = validation["schemaVersion"].split(".")
    version_label = ".".join(version_parts[:2])
    output_name = f"career-profile.v{version_label}.jsonld"
    output_profile = run_dir / output_name
    if not git_ignored(repository_root, output_profile):
        raise SystemExit("Refusing to write because the private output path is not ignored by Git.")
    validation["gitIgnored"] = True
    if run_dir.exists():
        raise SystemExit(f"Run directory already exists: {run_dir}")

    skill_path = (
        repository_root
        / ".agents"
        / "skills"
        / "convert-resume-to-career-profile"
        / "SKILL.md"
    )
    rendering = inventory.get("extraction", {}).get("rendering", {})
    metadata = {
        "runId": f"run:{run_name}",
        "generatedAt": timestamp.isoformat().replace("+00:00", "Z"),
        "status": "completed",
        "source": {
            "mediaType": "application/pdf",
            "sha256": source_hash,
            "pageCount": source["pageCount"],
            "sourceDocumentId": source.get("sourceDocumentId"),
            "originalCopied": False,
        },
        "output": {
            "schemaVersion": validation["schemaVersion"],
            "profileId": profile.get("profileId"),
            "fileName": output_name,
            "sha256": validation["profileSha256"],
        },
        "authority": {
            "repository": repository["url"],
            "repositoryRevision": repository["revision"],
            "repositoryDirty": repository["dirty"],
            "schemaManifestPath": validation["schemaManifest"],
            "schemaManifestSha256": validation["schemaManifestSha256"],
            "schemaPath": validation["canonicalSchema"],
            "schemaSha256": validation["canonicalSchemaSha256"],
            "semanticContractPath": validation["semanticContract"],
            "semanticContractSha256": validation["semanticContractSha256"],
            "extractionContractPath": validation["extractionContract"],
            "extractionContractSha256": validation["extractionContractSha256"],
            "skillPath": str(skill_path.relative_to(repository_root)),
            "skillSha256": sha256_file(skill_path),
        },
        "extraction": {
            "process": "two-pass-source-inventory-and-graph-assembly",
            "parser": inventory.get("extraction", {}).get("tool"),
            "parserVersion": inventory.get("extraction", {}).get("toolVersion"),
            "renderingStatus": rendering.get("status"),
            "visualReviewStatus": args.visual_review_status,
            "renderingDpi": rendering.get("dpi"),
            "externalBrowsingUsed": False,
            "sourceDocumentTreatedAsUntrustedData": True,
            "inventorySha256": sha256_file(inventory_path),
        },
        "validation": validation,
        "privacy": {
            "containsPersonalData": True,
            "originalResumeCopied": False,
            "repositoryPathIgnoredByGit": True,
        },
    }

    result = {
        "runDirectory": str(run_dir),
        "profile": str(output_profile),
        "metadata": str(run_dir / "run-metadata.json"),
        "dryRun": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(result, indent=2))
        return

    run_dir.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary_dir = run_dir.parent / f".{run_name}.tmp"
    if temporary_dir.exists():
        raise SystemExit(f"Temporary run directory already exists: {temporary_dir}")
    temporary_dir.mkdir(mode=0o700)
    try:
        shutil.copyfile(profile_path, temporary_dir / output_name)
        (temporary_dir / output_name).chmod(0o600)
        metadata_path = temporary_dir / "run-metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        metadata_path.chmod(0o600)
        os.replace(temporary_dir, run_dir)
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise

    validate_profile(output_profile, repository_root, require_git_ignored=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
