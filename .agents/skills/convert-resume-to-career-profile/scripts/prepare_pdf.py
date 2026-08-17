#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract page-bounded text and render a private resume PDF for inspection."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--pdftoppm", type=Path)
    parser.add_argument("--dpi", type=int, default=144)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.pdf.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    repository_root = args.repo_root.expanduser().resolve()

    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise SystemExit("Input must be an existing PDF file.")
    with source.open("rb") as handle:
        signature = handle.read(5)
    if signature != b"%PDF-":
        raise SystemExit("Input does not have a PDF file signature.")
    if args.dpi < 72 or args.dpi > 600:
        raise SystemExit("--dpi must be between 72 and 600.")
    try:
        output_dir.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise SystemExit("Temporary PDF artifacts must be written outside the repository.")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit("Output directory must be empty to avoid mixing private runs.")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_dir.chmod(0o700)

    try:
        import pdfplumber
    except ImportError as error:
        raise SystemExit(
            "pdfplumber is required. Install the repository development requirements."
        ) from error

    try:
        with pdfplumber.open(source) as document:
            pages = []
            cursor = 0
            page_separator = "\f\n"
            for page_number, page in enumerate(document.pages, start=1):
                text = page.extract_text(layout=True) or ""
                start = cursor
                end = start + len(text)
                pages.append(
                    {
                        "page": page_number,
                        "charStart": start,
                        "charEnd": end,
                        "text": text,
                        "textNormalization": "extraction-substitution",
                        "renderedImage": None,
                    }
                )
                cursor = end + len(page_separator)
    except Exception as error:
        raise SystemExit(f"Unable to read the PDF: {error}") from error

    renderer = args.pdftoppm
    if renderer is None:
        discovered = shutil.which("pdftoppm")
        renderer = Path(discovered) if discovered else None
    if renderer is not None:
        renderer = renderer.expanduser().resolve()
        if not renderer.is_file():
            raise SystemExit(f"pdftoppm executable not found: {renderer}")

    rendering = {"status": "unavailable", "renderer": None, "dpi": args.dpi}
    if renderer is not None:
        render_dir = output_dir / "rendered-pages"
        render_dir.mkdir(mode=0o700)
        prefix = render_dir / "page"
        subprocess.run(
            [str(renderer), "-png", "-r", str(args.dpi), str(source), str(prefix)],
            check=True,
            capture_output=True,
            text=True,
        )
        images = sorted(render_dir.glob("page-*.png"))
        if len(images) != len(pages):
            raise SystemExit(
                f"Rendered {len(images)} pages but extracted {len(pages)} pages."
            )
        for page, image in zip(pages, images, strict=True):
            page["renderedImage"] = str(image.relative_to(output_dir))
        rendering = {
            "status": "completed",
            "renderer": str(renderer),
            "dpi": args.dpi,
        }

    source_hash = sha256_file(source)
    inventory = {
        "inventoryVersion": "1",
        "source": {
            "mediaType": "application/pdf",
            "sha256": source_hash,
            "contentDigest": f"sha256:{source_hash}",
            "sourceDocumentId": f"source:resume-{source_hash[:12]}",
            "pageCount": len(pages),
            "extractionMethod": "document-parser",
        },
        "extraction": {
            "tool": "pdfplumber",
            "toolVersion": pdfplumber.__version__,
            "pageSeparator": "\f\n",
            "rendering": rendering,
        },
        "pages": pages,
        "warnings": [],
    }
    if renderer is None:
        inventory["warnings"].append(
            "PDF rendering was unavailable; visual inspection remains required."
        )
    if not any(page["text"].strip() for page in pages):
        inventory["warnings"].append(
            "No extractable text was found; OCR is required before conversion."
        )

    inventory_path = output_dir / "source-inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    inventory_path.chmod(0o600)
    print(
        json.dumps(
            {
                "inventory": str(inventory_path),
                "sourceDigest": inventory["source"]["contentDigest"],
                "pageCount": len(pages),
                "rendering": rendering["status"],
                "hasText": any(page["text"].strip() for page in pages),
            }
        )
    )


if __name__ == "__main__":
    main()
