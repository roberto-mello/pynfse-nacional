from copy import deepcopy
from decimal import Decimal

import pytest

import tests._cert_credentials as cert_credentials
from pynfse_nacional.models import Endereco, Prestador, Servico, Tomador


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-homologacao",
        action="store_true",
        default=False,
        help="run live homologacao tests that call the external SEFIN service",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-homologacao"):
        return

    skip_live = pytest.mark.skip(
        reason="live homologacao test; pass --run-homologacao explicitly"
    )
    for item in items:
        if "homologacao" in item.keywords:
            item.add_marker(skip_live)


def pytest_configure(config: pytest.Config) -> None:
    """Load repository .env values before test collection."""

    cert_credentials.load_test_env()


@pytest.fixture
def sample_endereco() -> Endereco:
    return Endereco(
        logradouro="Rua Teste",
        numero="100",
        complemento="Sala 1",
        bairro="Centro",
        codigo_municipio=3509502,
        uf="SP",
        cep="13000000",
    )


@pytest.fixture
def sample_prestador(sample_endereco: Endereco) -> Prestador:
    return Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Clinica Teste LTDA",
        nome_fantasia="Clinica Teste",
        endereco=sample_endereco,
        email="contato@clinica.com",
        telefone="1999999999",
    )


@pytest.fixture
def sample_tomador(sample_endereco: Endereco) -> Tomador:
    return Tomador(
        cpf="52998224725",
        razao_social="Joao Silva",
        email="paciente@email.com",
        telefone="1988888888",
        endereco=sample_endereco,
    )


@pytest.fixture
def shared_sample_servico() -> Servico:
    return Servico(
        codigo_cnae="8630503",
        codigo_lc116="04.03.03",
        codigo_tributacao_municipal="123456",
        codigo_nbs="101010100",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
        aliquota_iss=Decimal("2.00"),
        aliquota_simples=Decimal("15.50"),
        valor_deducoes=Decimal("0.00"),
        valor_pis=Decimal("0.00"),
        valor_cofins=Decimal("0.00"),
        valor_inss=Decimal("0.00"),
        valor_ir=Decimal("0.00"),
        valor_csll=Decimal("0.00"),
    )


@pytest.fixture
def sample_servico(shared_sample_servico: Servico) -> Servico:
    return deepcopy(shared_sample_servico)


@pytest.fixture(scope="session")
def cert_path() -> str:
    return cert_credentials.cert_path()


@pytest.fixture(scope="session")
def cert_password() -> str:
    return cert_credentials.cert_password()
