"""
Test script for NFSe Nacional API using homologacao environment.
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional import NFSeClient
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
        #codigo_municipio=3550308,  # Sao Paulo
        codigo_municipio=1302603,
        uf="AM",
        cep="69065030",
    )

    prestador = Prestador(
        cnpj="42713924000185",  # From certificate
        inscricao_municipal="51034401",
        razao_social="Ronald Cesar Barbosa Mello",
        nome_fantasia="Corpo e Mente Neuropsiquiatria",
        endereco=prestador_endereco,
        email="contato@corpoementemanaus.com.br",
        telefone="9236644038",
    )

    tomador = Tomador(
        cpf="51762419866",  # Real CPF from previous NFSe
        razao_social="ULLIAN DOS SANTOS SILVA",
        email="cliente@teste.com.br",
    )

    servico = Servico(
        codigo_lc116="04.03.03",  # Clínicas, sanatórios, manicômios, casas de saúde
        codigo_cnae="8630503",  # Atividade médica ambulatorial restrita a consultas
        discriminacao="Consultas psiquiátricas realizadas pela Dra Sônia Lafayette",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
        # aliquota_iss=Decimal("2.00"),
    )

    now = datetime.now()
    competencia = now.strftime("%Y-%m")
    numero = 500  # Use different number to avoid duplicates
    serie = "900"  # Match the serie format from real NFSe

    cnpj = prestador.cnpj
    cLocEmi = str(prestador_endereco.codigo_municipio)

    # DPS ID format: DPS + cLocEmi(7) + tpAmb(1) + CNPJ(14) + serie(5) + nDPS(15)
    # tpAmb: 1=Producao, 2=Homologacao
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


def test_submit_dps():
    """Test DPS submission."""

    print("Initializing NFSe client (homologacao)...")

    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
        timeout=60.0,
    )

    print("Creating sample DPS...")

    dps = create_sample_dps()

    print(f"DPS ID: {dps.id_dps}")
    print(f"Prestador: {dps.prestador.razao_social}")
    print(f"Tomador: {dps.tomador.razao_social}")
    print(f"Valor: R$ {dps.servico.valor_servicos}")

    print("\nSubmitting DPS to SEFIN...")

    try:
        response = client.submit_dps(dps)

        if response.success:
            print("\nNFSe emitida com sucesso!")
            print(f"Chave de Acesso: {response.chave_acesso}")
            print(f"Numero NFSe: {response.nfse_number}")
        else:
            print(f"\nErro ao emitir NFSe:")
            print(f"Codigo: {response.error_code}")
            print(f"Mensagem: {response.error_message}")

        return response

    except Exception as e:
        print(f"\nExcecao: {type(e).__name__}: {e}")
        raise


def test_query_nfse(chave_acesso: str):
    """Test NFSe query."""

    print(f"\nConsultando NFSe: {chave_acesso}")

    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
    )

    try:
        result = client.query_nfse(chave_acesso)

        print(f"Status: {result.status}")
        print(f"Numero: {result.nfse_number}")
        print(f"Data Emissao: {result.data_emissao}")
        print(f"Valor: R$ {result.valor_servicos}")

        return result

    except Exception as e:
        print(f"Erro na consulta: {e}")
        raise


def test_download_danfse(chave_acesso: str):
    """Test DANFSE PDF download."""

    print(f"\nBaixando DANFSE: {chave_acesso}")

    client = NFSeClient(
        cert_path=str(CERT_PATH),
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
    )

    try:
        pdf_content = client.download_danfse(chave_acesso)

        output_path = Path(__file__).parent / f"danfse_{chave_acesso}.pdf"
        output_path.write_bytes(pdf_content)

        print(f"DANFSE salvo em: {output_path}")
        print(f"Tamanho: {len(pdf_content)} bytes")

        return output_path

    except Exception as e:
        print(f"Erro ao baixar DANFSE: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("NFSe Nacional - Test Script (Homologacao)")
    print("=" * 60)

    print(f"\nCertificado: {CERT_PATH}")

    if not CERT_PATH.exists():
        print("ERRO: Certificado nao encontrado!")
        sys.exit(1)

    response = test_submit_dps()

    if response.success and response.chave_acesso:
        test_query_nfse(response.chave_acesso)
        test_download_danfse(response.chave_acesso)
