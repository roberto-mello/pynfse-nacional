"""Debug script to show generated XML before submission."""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.xml_builder import XMLBuilder
from pynfse_nacional.xml_signer import XMLSignerService
from pynfse_nacional.utils import compress_encode
from pynfse_nacional.models import (
    DPS,
    Endereco,
    Prestador,
    Servico,
    Tomador,
)

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
    numero = 1

    cnpj = prestador.cnpj
    cLocEmi = str(prestador_endereco.codigo_municipio)

    serie_padded = "NF".rjust(5, "0")

    id_dps = f"DPS{cLocEmi}1{cnpj}{serie_padded}{numero:015d}"

    dps = DPS(
        id_dps=id_dps,
        serie="NF",
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


if __name__ == "__main__":
    print("=" * 60)
    print("XML Debug - NFSe Nacional")
    print("=" * 60)

    dps = create_sample_dps()
    print(f"\nDPS ID: {dps.id_dps}")
    print(f"ID Length: {len(dps.id_dps)}")

    builder = XMLBuilder()
    xml = builder.build_dps(dps)

    print("\n" + "=" * 60)
    print("UNSIGNED XML:")
    print("=" * 60)
    print(xml)

    signer = XMLSignerService(str(CERT_PATH), CERT_PASSWORD)
    signed_xml = signer.sign(xml)

    print("\n" + "=" * 60)
    print("SIGNED XML:")
    print("=" * 60)
    print(signed_xml)

    encoded = compress_encode(signed_xml)

    print("\n" + "=" * 60)
    print("ENCODED (first 200 chars):")
    print("=" * 60)
    print(encoded[:200])
