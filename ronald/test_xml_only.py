"""Test sending unsigned XML to check structure without signature issues."""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.xml_builder import XMLBuilder
from pynfse_nacional.utils import compress_encode
from pynfse_nacional.models import (
    DPS,
    Endereco,
    Prestador,
    Servico,
    Tomador,
)
from pynfse_nacional.client import NFSeClient

CERT_PATH = Path(__file__).parent / "DR RONALDO S L80OUS6LL02XV7.pfx"
CERT_PASSWORD = "L80OUS6LL02XV7"


def create_sample_dps() -> DPS:
    """Create a sample DPS for testing."""

    prestador_endereco = Endereco(
        logradouro="Av Borba",
        numero="1626",
        complemento="",
        bairro="Cachoeirinha",
        codigo_municipio=1302603,
        uf="AM",
        cep="69065030",
    )

    prestador = Prestador(
        cnpj="42713924000185",
        inscricao_municipal="51034401",
        razao_social="Ronald Cesar Barbosa Mello",
        nome_fantasia="Corpo e Mente Neuropsiquiatria",
        endereco=prestador_endereco,
        email="contato@corpoementemanaus.com.br",
        telefone="9236644038",
    )

    tomador = Tomador(
        cpf="52998224725",
        razao_social="Cliente Teste",
        email="cliente@teste.com.br",
    )

    servico = Servico(
        codigo_lc116="04.03.03",
        codigo_cnae="8630503",
        discriminacao="Consultas psiquiatricas realizadas pela Dra Sonia Lafayette",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
    )

    now = datetime.now()
    competencia = now.strftime("%Y-%m")
    numero = 100
    serie = "900"

    cnpj = prestador.cnpj
    cLocEmi = str(prestador_endereco.codigo_municipio)

    # DPS ID format: DPS + cLocEmi(7) + tpAmb(1) + CNPJ(14) + serie(5) + nDPS(15)
    tpAmb = "2"  # Homologacao
    serie_padded = serie.zfill(5)

    id_dps = f"DPS{cLocEmi}{tpAmb}{cnpj}{serie_padded}{numero:015d}"

    dps = DPS(
        id_dps=id_dps,
        serie=serie,
        numero=numero,
        competencia=competencia,
        data_emissao=now,
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        regime_tributario="simples_nacional",
        optante_simples=True,
        incentivador_cultural=False,
    )

    return dps


def test_unsigned():
    """Test sending unsigned XML."""

    print("Creating sample DPS...")
    dps = create_sample_dps()

    print(f"DPS ID: {dps.id_dps}")

    builder = XMLBuilder()
    xml = builder.build_dps(dps)

    print("\nUnsigned XML:")
    print(xml)

    # Compress and encode without signing
    encoded = compress_encode(xml)

    print(f"\nEncoded length: {len(encoded)}")

    # Try sending to API
    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
    )

    import httpx
    from pynfse_nacional.constants import API_URLS, ENDPOINTS, Ambiente

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


if __name__ == "__main__":
    test_unsigned()
