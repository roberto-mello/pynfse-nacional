"""Generate DANFSE PDFs from results CSV containing nfseXmlGZipB64.

Usage:
    python generate_pdfs_from_results.py results.csv
    python generate_pdfs_from_results.py results.csv --header-image logo.png --header-title "Minha Empresa"

Examples:
    python generate_pdfs_from_results.py patients_sample_results.csv
    python generate_pdfs_from_results.py patients_sample_results.csv --output-dir ./pdfs
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.pdf_generator import (
    HeaderConfig,
    generate_danfse_from_base64,
)


def extract_nfse_data_from_csv(csv_path: str) -> list[dict]:
    """Extract NFSe data from results CSV file."""

    results = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            chave_acesso = None
            nfse_xml_b64 = None
            patient_name = row.get("patient", "")

            # Check if chave_acesso column exists and has value
            if row.get("chave_acesso"):
                chave_acesso = row["chave_acesso"]

            # Try to extract from error field (contains JSON response with nfseXmlGZipB64)
            error_field = row.get("error", "")

            if error_field and "nfseXmlGZipB64" in error_field:
                try:
                    # The CSV escapes quotes as ""
                    json_str = error_field.replace('""', '"')
                    data = json.loads(json_str)

                    if not chave_acesso:
                        chave_acesso = data.get("chaveAcesso")

                    nfse_xml_b64 = data.get("nfseXmlGZipB64")

                except json.JSONDecodeError:
                    # Try regex as fallback
                    if not chave_acesso:
                        match = re.search(r'"chaveAcesso"\s*:\s*"([^"]+)"', error_field)

                        if match:
                            chave_acesso = match.group(1)

                    match = re.search(r'"nfseXmlGZipB64"\s*:\s*"([^"]+)"', error_field)

                    if match:
                        nfse_xml_b64 = match.group(1)

            if chave_acesso and nfse_xml_b64:
                results.append({
                    "chave_acesso": chave_acesso,
                    "nfse_xml_b64": nfse_xml_b64,
                    "patient_name": patient_name,
                })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate DANFSE PDFs from results CSV"
    )

    parser.add_argument("csv_path", help="Path to results CSV file")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Output directory for PDFs (default: same as CSV)",
    )
    parser.add_argument(
        "--header-image",
        help="Path to custom header image",
    )
    parser.add_argument(
        "--header-title",
        help="Custom header title",
    )
    parser.add_argument(
        "--header-subtitle",
        help="Custom header subtitle",
    )
    parser.add_argument(
        "--header-phone",
        help="Custom header phone",
    )
    parser.add_argument(
        "--header-email",
        help="Custom header email",
    )

    args = parser.parse_args()

    if not Path(args.csv_path).exists():
        print(f"Error: File not found: {args.csv_path}")
        sys.exit(1)

    # Set output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(args.csv_path).parent / "pdfs"

    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Configure custom header
    header_config = None

    if any([args.header_image, args.header_title]):
        header_config = HeaderConfig(
            image_path=args.header_image,
            title=args.header_title or "",
            subtitle=args.header_subtitle or "",
            phone=args.header_phone or "",
            email=args.header_email or "",
        )
        print(f"Using custom header: {args.header_title or args.header_image}")

    # Extract NFSe data from CSV
    print(f"Reading NFSe data from: {args.csv_path}")
    nfse_list = extract_nfse_data_from_csv(args.csv_path)
    print(f"Found {len(nfse_list)} NFSe with XML data")

    if not nfse_list:
        print("No NFSe data found in CSV")
        sys.exit(0)

    # Generate PDFs
    results = []

    for nfse in nfse_list:
        chave = nfse["chave_acesso"]
        patient = nfse["patient_name"]

        print(f"\n{'='*60}")
        print(f"Processing: {patient or chave[:20]}...")

        try:
            pdf_path = output_dir / f"nfse_{chave}.pdf"

            generate_danfse_from_base64(
                nfse["nfse_xml_b64"],
                output_path=str(pdf_path),
                header_config=header_config,
            )

            print(f"SUCCESS: {pdf_path}")
            results.append({
                "chave": chave,
                "patient": patient,
                "success": True,
                "file": str(pdf_path),
            })

        except Exception as e:
            print(f"FAILED: {e}")
            results.append({
                "chave": chave,
                "patient": patient,
                "success": False,
                "error": str(e),
            })

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nPDFs saved to: {output_dir}")

    if failed:
        print("\nFailed:")

        for r in failed:
            print(f"  {r['patient'] or r['chave']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
