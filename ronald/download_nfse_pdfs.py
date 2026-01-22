"""Download DANFSE PDFs for already issued NFSes.

Usage:
    python download_nfse_pdfs.py <chave_acesso> [<chave_acesso> ...]
    python download_nfse_pdfs.py --from-csv results.csv

Examples:
    python download_nfse_pdfs.py 13026032242713924000185000000000003526016636142449
    python download_nfse_pdfs.py --from-csv patients_sample_results.csv
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.client import NFSeClient
from pynfse_nacional.constants import Ambiente

# DANFSE API is on a separate domain from SEFIN
DANFSE_URLS = {
    Ambiente.HOMOLOGACAO: "https://adn.producaorestrita.nfse.gov.br",
    Ambiente.PRODUCAO: "https://adn.nfse.gov.br",
}

# Certificate configuration
CERT_PATH = Path(__file__).parent / "DR RONALDO S L80OUS6LL02XV7.pfx"
CERT_PASSWORD = "L80OUS6LL02XV7"


def download_danfse(http_client, chave_acesso: str, base_url: str, output_dir: Path) -> Path | None:
    """Download DANFSE PDF for a given chave de acesso."""

    # Try different endpoint patterns
    # ADN service uses /contribuintes/ path prefix
    endpoints = [
        f"{base_url}/contribuintes/danfse/{chave_acesso}",
        f"{base_url}/contribuintes/NFSe/{chave_acesso}/danfse",
        f"{base_url}/danfse/{chave_acesso}",
    ]

    for url in endpoints:
        print(f"Trying: {url}")

        try:
            response = http_client.get(url, headers={"Accept": "application/pdf"})
            print(f"  Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}")

            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")

                if "pdf" in content_type or response.content[:4] == b"%PDF":
                    pdf_file = output_dir / f"nfse_{chave_acesso}.pdf"
                    pdf_file.write_bytes(response.content)
                    return pdf_file
                else:
                    print(f"  Response is not PDF: {response.content[:100]}")

        except Exception as e:
            print(f"  Exception: {e}")

    print(f"Failed to download PDF for {chave_acesso}")
    return None


def extract_chaves_from_csv(csv_path: str) -> list[str]:
    """Extract chaveAcesso from a results CSV file."""

    chaves = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Check if chave_acesso column exists and has value
            if row.get("chave_acesso"):
                chaves.append(row["chave_acesso"])
                continue

            # Try to extract from error field (contains JSON response)
            error_field = row.get("error", "")

            if error_field and "chaveAcesso" in error_field:
                # Parse the JSON-like string
                try:
                    # The CSV escapes quotes as ""
                    json_str = error_field.replace('""', '"')
                    data = json.loads(json_str)
                    chave = data.get("chaveAcesso")

                    if chave:
                        chaves.append(chave)

                except json.JSONDecodeError:
                    # Try regex as fallback
                    match = re.search(r'"chaveAcesso"\s*:\s*"([^"]+)"', error_field)

                    if match:
                        chaves.append(match.group(1))

    return chaves


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    chaves = []

    if sys.argv[1] == "--from-csv":
        if len(sys.argv) < 3:
            print("Error: CSV file path required")
            sys.exit(1)

        csv_path = sys.argv[2]

        if not Path(csv_path).exists():
            print(f"Error: File not found: {csv_path}")
            sys.exit(1)

        chaves = extract_chaves_from_csv(csv_path)
        print(f"Found {len(chaves)} chaves de acesso in CSV")
    else:
        chaves = sys.argv[1:]

    if not chaves:
        print("No chaves de acesso to process")
        sys.exit(0)

    print(f"Certificate: {CERT_PATH}")

    if not CERT_PATH.exists():
        print(f"Error: Certificate not found: {CERT_PATH}")
        sys.exit(1)

    # Create output directory
    output_dir = Path(__file__).parent / "pdfs"
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Create client
    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="producao",
    )

    base_url = DANFSE_URLS[Ambiente.PRODUCAO]
    results = []

    with client._get_client() as http_client:
        for chave in chaves:
            print(f"\n{'='*60}")
            print(f"Processing: {chave}")

            pdf_file = download_danfse(http_client, chave, base_url, output_dir)

            if pdf_file:
                print(f"SUCCESS: {pdf_file}")
                results.append({"chave": chave, "success": True, "file": str(pdf_file)})
            else:
                print(f"FAILED: {chave}")
                results.append({"chave": chave, "success": False, "file": None})

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
        print("\nFailed downloads:")

        for r in failed:
            print(f"  {r['chave']}")


if __name__ == "__main__":
    main()
