"""Test with signed XML matching the real NFSe structure."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.utils import compress_encode
from pynfse_nacional.xml_signer import XMLSignerService
from pynfse_nacional.client import NFSeClient
from pynfse_nacional.constants import API_URLS, ENDPOINTS, Ambiente

CERT_PATH = Path(__file__).parent / "DR RONALDO S L80OUS6LL02XV7.pfx"
CERT_PASSWORD = "L80OUS6LL02XV7"


def create_xml_like_real_nfse():
    """Create XML matching the structure from the real NFSe."""

    now = datetime.now()

    # Match the exact format from the real DPS
    xml = f'''<?xml version="1.0" encoding="utf-8"?><DPS versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse"><infDPS Id="DPS130260324271392400018500900000000000000300"><tpAmb>2</tpAmb><dhEmi>{now.strftime("%Y-%m-%dT%H:%M:%S")}-03:00</dhEmi><verAplic>pynfse-1.0</verAplic><serie>900</serie><nDPS>300</nDPS><dCompet>{now.strftime("%Y-%m-%d")}</dCompet><tpEmit>1</tpEmit><cLocEmi>1302603</cLocEmi><prest><CNPJ>42713924000185</CNPJ><IM>       51034401</IM><fone>92991990808</fone><email>drronaldmello@hotmail.com</email><regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN><regEspTrib>0</regEspTrib></regTrib></prest><toma><CPF>52998224725</CPF><xNome>Cliente Teste</xNome></toma><serv><locPrest><cLocPrestacao>1302603</cLocPrestacao></locPrest><cServ><cTribNac>040303</cTribNac><cTribMun>100</cTribMun><xDescServ>Consultas medicas realizadas pela Dra Sonia Lafayette</xDescServ><cNBS>123012200</cNBS></cServ></serv><valores><vServPrest><vServ>500.00</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun><totTrib><pTotTribSN>18.83</pTotTribSN></totTrib></trib></valores></infDPS></DPS>'''

    return xml


if __name__ == "__main__":
    print("Creating manual XML...")

    xml = create_xml_like_real_nfse()

    print("\nUnsigned XML:")
    print(xml[:500], "...")

    # Sign the XML
    signer = XMLSignerService(str(CERT_PATH), CERT_PASSWORD)
    signed_xml = signer.sign(xml)

    print(f"\nSigned XML length: {len(signed_xml)}")

    # Compress and encode
    encoded = compress_encode(signed_xml)

    print(f"\nEncoded length: {len(encoded)}")

    # Try sending to API
    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
    )

    base_url = API_URLS[Ambiente.HOMOLOGACAO]
    url = f"{base_url}{ENDPOINTS['submit_dps']}"

    print(f"\nSending to: {url}")

    payload = {"dps": encoded}

    try:
        with client._get_client() as http_client:
            response = http_client.post(url, json=payload)
            print(f"\nStatus: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")
