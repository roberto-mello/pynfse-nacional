"""Issue NFSe in production for patients from CSV file.

CSV Format (tab or comma separated):
patient_name,cpf,prescription_url,valor

Example:
Gabriel Éric Silva Raposo,06948277110,https://prescricao.cfm.org.br/api/consulta-documento?sw=CFMP-RE-RXKCH64C,500.00
Talita Pereira da Silva,75260867149,https://prescricao.cfm.org.br/api/consulta-documento?sw=CFMP-RE-9D7UCLXS,500.00

Usage:
    python issue_nfse_from_csv.py patients.csv
    python issue_nfse_from_csv.py patients.csv --dry-run
"""

import csv
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.utils import compress_encode
from pynfse_nacional.xml_signer import XMLSignerService
from pynfse_nacional.client import NFSeClient
from pynfse_nacional.constants import API_URLS, ENDPOINTS, Ambiente

# Certificate configuration
CERT_PATH = Path(__file__).parent / "DR RONALDO S L80OUS6LL02XV7.pfx"
CERT_PASSWORD = "L80OUS6LL02XV7"

# Prestador (Provider) configuration - Dr. Ronaldo
PRESTADOR = {
    "cnpj": "42713924000185",
    "im": "       51034401",  # Inscricao Municipal with padding
    "fone": "92991990808",
    "email": "drronaldmello@hotmail.com",
    "c_loc_emi": "1302603",  # Manaus IBGE code
}

# Service configuration
SERVICO = {
    "c_trib_nac": "040303",  # Codigo tributacao nacional - consultas medicas
    "c_trib_mun": "100",      # Codigo tributacao municipal
    "c_nbs": "123012200",     # NBS code
    "x_desc_serv": "Consultas medicas realizadas pela Dra Sonia Lafayette",
}

# Counter for DPS numbering (should be persisted in production)
DPS_SERIE = "900"
DPS_COUNTER_FILE = Path(__file__).parent / ".dps_counter"


def get_next_dps_number() -> int:
    """Get and increment DPS counter."""
    if DPS_COUNTER_FILE.exists():
        counter = int(DPS_COUNTER_FILE.read_text().strip())
    else:
        counter = 300  # Starting number

    DPS_COUNTER_FILE.write_text(str(counter + 1))
    return counter


def create_dps_xml(
    patient_name: str,
    cpf: str,
    valor: Decimal,
    dps_number: int,
    ambiente: Ambiente = Ambiente.PRODUCAO,
) -> str:
    """Create DPS XML for a patient consultation."""

    now = datetime.now()
    tp_amb = "1" if ambiente == Ambiente.PRODUCAO else "2"

    # Build the DPS ID: DPS + cLocEmi(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
    # tpInsc: 1=CPF, 2=CNPJ
    dps_id = f"DPS{PRESTADOR['c_loc_emi']}2{PRESTADOR['cnpj']}{DPS_SERIE.zfill(5)}{str(dps_number).zfill(15)}"

    # Format valor with 2 decimal places
    valor_str = f"{valor:.2f}"

    xml = f'''<?xml version="1.0" encoding="utf-8"?><DPS versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse"><infDPS Id="{dps_id}"><tpAmb>{tp_amb}</tpAmb><dhEmi>{now.strftime("%Y-%m-%dT%H:%M:%S")}-03:00</dhEmi><verAplic>pynfse-1.0</verAplic><serie>{DPS_SERIE}</serie><nDPS>{dps_number}</nDPS><dCompet>{now.strftime("%Y-%m-%d")}</dCompet><tpEmit>1</tpEmit><cLocEmi>{PRESTADOR['c_loc_emi']}</cLocEmi><prest><CNPJ>{PRESTADOR['cnpj']}</CNPJ><IM>{PRESTADOR['im']}</IM><fone>{PRESTADOR['fone']}</fone><email>{PRESTADOR['email']}</email><regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN><regEspTrib>0</regEspTrib></regTrib></prest><toma><CPF>{cpf}</CPF><xNome>{patient_name}</xNome></toma><serv><locPrest><cLocPrestacao>{PRESTADOR['c_loc_emi']}</cLocPrestacao></locPrest><cServ><cTribNac>{SERVICO['c_trib_nac']}</cTribNac><cTribMun>{SERVICO['c_trib_mun']}</cTribMun><xDescServ>{SERVICO['x_desc_serv']}</xDescServ><cNBS>{SERVICO['c_nbs']}</cNBS></cServ></serv><valores><vServPrest><vServ>{valor_str}</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun><totTrib><pTotTribSN>18.83</pTotTribSN></totTrib></trib></valores></infDPS></DPS>'''

    return xml


def read_patients_csv(csv_path: str) -> list[dict]:
    """Read patients from CSV file.

    Expected columns: patient_name, cpf, prescription_url, valor
    """
    patients = []

    with open(csv_path, "r", encoding="utf-8") as f:
        # Try to detect delimiter
        sample = f.read(1024)
        f.seek(0)

        if "\t" in sample:
            delimiter = "\t"
        else:
            delimiter = ","

        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            # Normalize column names (handle different cases)
            normalized = {}
            for key, value in row.items():
                normalized[key.lower().strip()] = value.strip() if value else ""

            # Extract required fields
            patient = {
                "name": normalized.get("patient_name") or normalized.get("name") or normalized.get("nome"),
                "cpf": normalized.get("cpf", "").replace(".", "").replace("-", ""),
                "prescription_url": normalized.get("prescription_url") or normalized.get("url") or normalized.get("link"),
                "valor": Decimal(normalized.get("valor", "500.00").replace(",", ".")),
            }

            if patient["name"] and patient["cpf"]:
                patients.append(patient)
            else:
                print(f"Warning: Skipping row with missing data: {row}")

    return patients


DANFSE_URL = "https://adn.nfse.gov.br"


def download_danfse(http_client, chave_acesso: str) -> Path | None:
    """Download DANFSE PDF for a given chave de acesso."""

    url = f"{DANFSE_URL}/danfse/{chave_acesso}"
    print(f"Downloading PDF from: {url}")

    try:
        response = http_client.get(url)

        if response.status_code == 200:
            pdf_file = Path(__file__).parent / f"nfse_{chave_acesso}.pdf"
            pdf_file.write_bytes(response.content)
            return pdf_file
        else:
            print(f"Failed to download PDF: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"Exception downloading PDF: {e}")
        return None


def issue_nfse(patient: dict, dry_run: bool = False) -> dict:
    """Issue NFSe for a single patient."""

    dps_number = get_next_dps_number()

    print(f"\n{'='*60}")
    print(f"Processing: {patient['name']}")
    print(f"CPF: {patient['cpf']}")
    print(f"Valor: R$ {patient['valor']}")
    print(f"DPS Number: {dps_number}")

    # Build the DPS ID: DPS + cLocEmi(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
    # tpInsc: 1=CPF, 2=CNPJ
    dps_id = f"DPS{PRESTADOR['c_loc_emi']}2{PRESTADOR['cnpj']}{DPS_SERIE.zfill(5)}{str(dps_number).zfill(15)}"

    # Create XML
    xml = create_dps_xml(
        patient_name=patient["name"],
        cpf=patient["cpf"],
        valor=patient["valor"],
        dps_number=dps_number,
        ambiente=Ambiente.PRODUCAO,
    )

    if dry_run:
        # Save XML to file in dry-run mode
        xml_file = Path(__file__).parent / f"{dps_id}.xml"
        xml_file.write_text(xml, encoding="utf-8")

        print(f"\n[DRY RUN] XML saved to: {xml_file}")
        print(xml[:200], "...")
        return {
            "success": True,
            "dry_run": True,
            "patient": patient["name"],
            "dps_number": dps_number,
            "xml_file": str(xml_file),
        }

    # Sign the XML
    signer = XMLSignerService(str(CERT_PATH), CERT_PASSWORD)
    signed_xml = signer.sign(xml)

    print(f"Signed XML length: {len(signed_xml)}")

    # Compress and encode
    encoded = compress_encode(signed_xml)

    # Create client and send
    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="producao",
    )

    base_url = API_URLS[Ambiente.PRODUCAO]
    url = f"{base_url}{ENDPOINTS['submit_dps']}"

    print(f"Sending to: {url}")

    payload = {"dpsXmlGZipB64": encoded}

    try:
        with client._get_client() as http_client:
            response = http_client.post(url, json=payload)

            print(f"Status: {response.status_code}")

            data = response.json()

            # Check if response contains chaveAcesso (success indicator)
            if data.get("chaveAcesso"):
                chave_acesso = data.get("chaveAcesso")
                result = {
                    "success": True,
                    "patient": patient["name"],
                    "cpf": patient["cpf"],
                    "prescription_url": patient.get("prescription_url", ""),
                    "dps_number": dps_number,
                    "chave_acesso": chave_acesso,
                    "nfse_number": data.get("nNFSe"),
                }
                print(f"SUCCESS! Chave: {chave_acesso}")

                # Download PDF
                pdf_file = download_danfse(http_client, chave_acesso)
                if pdf_file:
                    result["pdf_file"] = str(pdf_file)
                    print(f"PDF saved: {pdf_file}")

                return result
            else:
                error_text = response.text
                print(f"ERROR: {error_text}")
                return {
                    "success": False,
                    "patient": patient["name"],
                    "error": error_text,
                }

    except Exception as e:
        print(f"Exception: {e}")
        return {
            "success": False,
            "patient": patient["name"],
            "error": str(e),
        }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    csv_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Reading patients from: {csv_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print(f"Certificate: {CERT_PATH}")

    if not CERT_PATH.exists():
        print(f"Error: Certificate not found: {CERT_PATH}")
        sys.exit(1)

    patients = read_patients_csv(csv_path)
    print(f"Found {len(patients)} patients")

    results = []
    for patient in patients:
        result = issue_nfse(patient, dry_run=dry_run)
        results.append(result)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\nSuccessful NFSe:")
        for r in successful:
            if r.get("dry_run"):
                print(f"  [DRY RUN] {r['patient']} - DPS #{r['dps_number']} -> {r.get('xml_file', 'N/A')}")
            else:
                print(f"  {r['patient']} - NFSe {r.get('nfse_number')} - Chave: {r.get('chave_acesso')}")

    if failed:
        print("\nFailed:")
        for r in failed:
            print(f"  {r['patient']}: {r.get('error', 'Unknown error')}")

    # Save results to file
    output_file = Path(csv_path).stem + "_results.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["patient", "cpf", "prescription_url", "success", "dps_number", "nfse_number", "chave_acesso", "xml_file", "error"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
