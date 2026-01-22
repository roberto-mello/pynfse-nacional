"""Test without XML declaration."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.utils import compress_encode
from pynfse_nacional.xml_signer import XMLSignerService
from pynfse_nacional.client import NFSeClient
from pynfse_nacional.constants import API_URLS, ENDPOINTS, Ambiente
from lxml import etree

CERT_PATH = Path(__file__).parent / "DR RONALDO S L80OUS6LL02XV7.pfx"
CERT_PASSWORD = "L80OUS6LL02XV7"


def create_xml():
    """Create XML without declaration."""

    now = datetime.now()

    # XML WITHOUT declaration
    xml = f'''<DPS versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse"><infDPS Id="DPS130260324271392400018500900000000000000400"><tpAmb>2</tpAmb><dhEmi>{now.strftime("%Y-%m-%dT%H:%M:%S")}-03:00</dhEmi><verAplic>pynfse-1.0</verAplic><serie>900</serie><nDPS>400</nDPS><dCompet>{now.strftime("%Y-%m-%d")}</dCompet><tpEmit>1</tpEmit><cLocEmi>1302603</cLocEmi><prest><CNPJ>42713924000185</CNPJ><IM>       51034401</IM><fone>92991990808</fone><email>drronaldmello@hotmail.com</email><regTrib><opSimpNac>3</opSimpNac><regApTribSN>1</regApTribSN><regEspTrib>0</regEspTrib></regTrib></prest><toma><CPF>52998224725</CPF><xNome>Cliente Teste</xNome></toma><serv><locPrest><cLocPrestacao>1302603</cLocPrestacao></locPrest><cServ><cTribNac>040303</cTribNac><cTribMun>100</cTribMun><xDescServ>Consultas medicas realizadas</xDescServ><cNBS>123012200</cNBS></cServ></serv><valores><vServPrest><vServ>500.00</vServ></vServPrest><trib><tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun><totTrib><pTotTribSN>18.83</pTotTribSN></totTrib></trib></valores></infDPS></DPS>'''

    return xml


def sign_xml_no_declaration(xml: str) -> str:
    """Sign XML and return without declaration."""

    signer = XMLSignerService(str(CERT_PATH), CERT_PASSWORD)
    signer._load_certificate()

    from signxml import XMLSigner, methods

    xml_element = etree.fromstring(xml.encode("utf-8"))

    infDPS = xml_element.find(".//{http://www.sped.fazenda.gov.br/nfse}infDPS")
    infDPS_id = infDPS.get("Id")

    xml_signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
    )

    signed_xml = xml_signer.sign(
        xml_element,
        key=signer._private_key,
        cert=[signer._certificate],
        reference_uri=f"#{infDPS_id}",
    )

    # Return WITHOUT xml_declaration
    return etree.tostring(signed_xml, encoding="unicode")


if __name__ == "__main__":
    print("Creating XML without declaration...")

    xml = create_xml()

    print(f"\nUnsigned XML (first 300 chars):")
    print(xml[:300])

    # Sign without declaration
    signed_xml = sign_xml_no_declaration(xml)

    print(f"\nSigned XML (first 500 chars):")
    print(signed_xml[:500])

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
