"""Integration tests for NFSeClient against producaorestrita (homologacao) environment.

These tests require:
- A valid ICP-Brasil A1 test certificate (.pfx)
- `NFSE_TEST_CERT_PATH` in `.env`
- `NFSE_TEST_CERT_PASSWORD` in macOS Keychain or the environment

Run with: uv run pytest -m homologacao -v -s

Note: producaorestrita environment may return mock/simulated responses.
"""

import os
import re
from datetime import datetime
from decimal import Decimal

import pytest
from lxml import etree

import tests._cert_credentials as cert_credentials
from pynfse_nacional import (
    NFSeAPIError,
    NFSeCertificateError,
    NFSeClient,
)
from pynfse_nacional.error_codes import ErrorCode
from pynfse_nacional.models import (
    DPS,
    Endereco,
    Prestador,
    Servico,
    Tomador,
)

from ._helpers.xsd import load_dps_schema

# E1xxx = schema/structure rejections (code bugs). Never acceptable in homologação.
# SEFIN codes look like E1235; also catch multi-error strings containing E1xxx.
_SCHEMA_ERROR_CODE_RE = re.compile(r"(?:^|[,;\s])E1\d{3}\b", re.IGNORECASE)
_SCHEMA_FAILURE_MSG_RE = re.compile(
    r"invalid child element|The element \w+ has invalid",
    re.IGNORECASE,
)
_BUSINESS_ERROR_CODE_RE = re.compile(r"^E(?:0\d{3}|[23]\d{3})$", re.IGNORECASE)
_TRANSIENT_ERROR_CODES = {"500", "E999"}
_TRANSIENT_ERROR_MESSAGES = {"Erro não catalogado"}


def _normalize_error_code(error_code: str | int | None) -> str:
    """Normalize API error codes for comparison."""

    if error_code is None:
        return ""

    if isinstance(error_code, str):
        return error_code.strip()

    return str(error_code).strip()


def is_transient_homologacao_rejection(
    error_code: str | int | None,
    error_message: str | None,
) -> bool:
    """True when SEFIN returned a transient homologacao rejection."""

    code = _normalize_error_code(error_code)
    message = (error_message or "").strip()

    return code in _TRANSIENT_ERROR_CODES or message in _TRANSIENT_ERROR_MESSAGES


def is_schema_rejection(
    error_code: str | None,
    error_message: str | None = None,
) -> bool:
    """True when SEFIN rejected DPS for schema/structure reasons (E1xxx class)."""
    code = _normalize_error_code(error_code)
    if code and _SCHEMA_ERROR_CODE_RE.search(code):
        return True

    # Bare "E1" prefix with digits (E1, E12, E123, E1235, ...)
    if re.match(r"^E1\d*$", code, re.IGNORECASE):
        return True

    msg = (error_message or "").strip()
    if msg and _SCHEMA_ERROR_CODE_RE.search(msg):
        return True

    if msg and _SCHEMA_FAILURE_MSG_RE.search(msg):
        return True

    return False


def assert_dps_rejection_acceptable(
    error_code: str | None,
    error_message: str | None,
) -> None:
    """Fail hard on schema and non-business rejections."""
    if is_schema_rejection(error_code, error_message):
        pytest.fail(
            "Schema/structure rejection (code bug, not expected in homologação): "
            f"{error_code} — {error_message}"
        )

    code = _normalize_error_code(error_code)
    if code and code.isdigit():
        pytest.fail(
            "Unexpected HTTP/API rejection in homologação: "
            f"{error_code} — {error_message}"
        )

    if code and not _BUSINESS_ERROR_CODE_RE.fullmatch(code):
        pytest.fail(
            "Unexpected non-business rejection in homologação: "
            f"{error_code} — {error_message}"
        )

    assert error_code is not None or error_message is not None, (
        "Rejected DPS must include error_code or error_message"
    )


def assert_dps_xml_validates(client: NFSeClient, dps: DPS) -> None:
    """Assert the signed DPS XML validates against the official XSD."""

    schema = load_dps_schema()
    xml = client._xml_builder.build_dps(dps)
    schema.assertValid(etree.fromstring(xml.encode("utf-8")))

    signed_xml = client._xml_signer.sign(xml)
    schema.assertValid(etree.fromstring(signed_xml.encode("utf-8")))

CERT_PATH = cert_credentials.cert_path()
CERT_PASSWORD = cert_credentials.cert_password()

pytestmark = [
    pytest.mark.homologacao,
    pytest.mark.skipif(
        not CERT_PATH or not os.path.exists(CERT_PATH) or not CERT_PASSWORD,
        reason=(
            "Test certificate not configured. Set NFSE_TEST_CERT_PATH in .env and "
            "NFSE_TEST_CERT_PASSWORD in macOS Keychain or env."
        ),
    ),
]


@pytest.fixture
def client():
    """Create NFSeClient configured for homologacao."""
    return NFSeClient(
        cert_path=CERT_PATH,
        cert_password=CERT_PASSWORD,
        ambiente="homologacao",
        timeout=60.0,
    )


@pytest.fixture
def sample_dps():
    """Create a sample DPS for testing.

    Uses synthetic data for the homologacao environment.
    """
    prestador_endereco = Endereco(
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        codigo_municipio=3509502,
        uf="SP",
        cep="13000000",
    )

    prestador = Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Empresa Teste LTDA",
        nome_fantasia="Empresa Teste",
        endereco=prestador_endereco,
    )

    tomador = Tomador(
        cnpj="11222333000181",
        razao_social="Tomador de homologacao",
        endereco=Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3509502,
            uf="SP",
            cep="13000000",
        ),
    )

    servico = Servico(
        codigo_lc116="04.01.01",
        codigo_tributacao_municipal="100",
        codigo_nbs="123012200",
        discriminacao="Consulta medica para homologacao.",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
        aliquota_iss=Decimal("2.00"),
    )

    return DPS(
        serie="900",
        numero=616,
        competencia="2026-06",
        data_emissao=datetime.fromisoformat("2026-06-09T15:05:14-03:00"),
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        regime_tributario="simples_nacional",
        op_simp_nac="3",
        reg_ap_trib_sn="1",
        incentivador_cultural=False,
    )


class TestNFSeClientCertificateLoading:
    """Tests for certificate loading functionality."""

    def test_load_valid_certificate(self, client):
        """Test that a valid certificate loads successfully."""
        private_key, cert = client._load_pkcs12()

        assert private_key is not None
        assert cert is not None

    def test_invalid_certificate_path(self):
        """Test error handling for non-existent certificate."""
        client = NFSeClient(
            cert_path="/nonexistent/path.pfx",
            cert_password="password",
            ambiente="homologacao",
        )

        with pytest.raises(NFSeCertificateError) as exc_info:
            client._load_pkcs12()

        assert exc_info.value.code == ErrorCode.CERTIFICATE_FILE_NOT_FOUND

    def test_invalid_certificate_password(self):
        """Test error handling for wrong certificate password."""
        if not CERT_PATH:
            pytest.skip("Certificate not configured")

        client = NFSeClient(
            cert_path=CERT_PATH,
            cert_password="wrong_password_12345",
            ambiente="homologacao",
        )

        with pytest.raises(NFSeCertificateError):
            client._load_pkcs12()


class TestNFSeClientHTTP:
    """Tests for HTTP client configuration."""

    def test_client_creation_with_mtls(self, client):
        """Test that HTTP client is created with mTLS configuration."""
        with client._get_client() as http_client:
            assert http_client is not None
            assert http_client.timeout is not None


class TestNFSeClientSubmitDPS:
    """Tests for DPS submission to producaorestrita."""

    @pytest.mark.integration
    def test_submit_dps_homologacao(self, client, sample_dps):
        """Test DPS submission to homologacao environment.

        Note: This test makes a real API call to producaorestrita.
        The response may vary depending on SEFIN's test environment status.

        Rejection policy (Layer 2 gate from pynfse-a90):
        - E1xxx / schema-structure failures → test FAIL (code bug).
        - E0xxx / E2xxx / E3xxx business-rule failures → allowed with assertions.
        """
        assert_dps_xml_validates(client, sample_dps)

        try:
            response = client.submit_dps(sample_dps)

            if response.success:
                assert response.chave_acesso is not None
                assert len(response.chave_acesso) == 50

                assert response.nfse_number is not None

                print("NFSe issued successfully:")
                print(f"  Chave Acesso: {response.chave_acesso}")
                print(f"  NFSe Number: {response.nfse_number}")

            else:
                print("DPS rejected:")
                print(f"  Error Code: {response.error_code}")
                print(f"  Error Message: {response.error_message}")

                if is_transient_homologacao_rejection(
                    response.error_code,
                    response.error_message,
                ):
                    pytest.skip(
                        "SEFIN homologacao returned a transient JSON error for a "
                        "valid signed DPS; likely server-side instability."
                    )

                assert_dps_rejection_acceptable(
                    response.error_code,
                    response.error_message,
                )

        except NFSeAPIError as e:
            print(f"API Error: {e.code} - {e.message}")
            if e.status_code:
                print(f"  HTTP Status: {e.status_code}")

            if e.code == "TIMEOUT":
                pytest.skip("API timeout - SEFIN may be unavailable")

            if e.code == ErrorCode.RESPONSE_INVALID_STRUCTURE:
                pytest.skip(
                    "SEFIN homologacao returned opaque non-JSON error after the "
                    "signed DPS validated against the official XSD."
                )

            assert_dps_rejection_acceptable(e.code, e.message)


class TestNFSeClientQueryNFSe:
    """Tests for NFSe query functionality."""

    @pytest.mark.integration
    def test_query_nonexistent_nfse(self, client):
        """Test querying a non-existent NFSe.

        Should return an error since the chave doesn't exist.
        """
        fake_chave = "00000000000000000000000000000000000000000000000000"

        with pytest.raises(NFSeAPIError) as exc_info:
            client.query_nfse(fake_chave)

        print(
            f"Query error (expected): {exc_info.value.code} - {exc_info.value.message}"
        )


class TestNFSeClientDownloadDANFSe:
    """Tests for DANFSe PDF download."""

    @pytest.mark.integration
    def test_download_nonexistent_danfse(self, client):
        """Test downloading DANFSe for non-existent NFSe.

        Should return an error since the chave doesn't exist.
        """
        fake_chave = "00000000000000000000000000000000000000000000000000"

        with pytest.raises(NFSeAPIError) as exc_info:
            client.download_danfse(fake_chave)

        error_message = (
            f"Download error (expected): {exc_info.value.code} - "
            f"{exc_info.value.message}"
        )
        print(error_message)


class TestNFSeClientCancelNFSe:
    """Tests for NFSe cancellation."""

    @pytest.mark.integration
    def test_cancel_nonexistent_nfse(self, client):
        """Test cancelling a non-existent NFSe.

        Should fail since there's nothing to cancel.
        """
        fake_chave = "00000000000000000000000000000000000000000000000000"

        response = client.cancel_nfse(fake_chave, "Teste de cancelamento")

        assert response.success is False
        print(
            f"Cancel error (expected): {response.error_code} - {response.error_message}"
        )


class TestNFSeClientEnvironments:
    """Tests for different API environments."""

    def test_homologacao_base_url(self):
        """Test that homologacao uses producaorestrita URL."""
        client = NFSeClient(
            cert_path=CERT_PATH,
            cert_password=CERT_PASSWORD,
            ambiente="homologacao",
        )

        assert "producaorestrita" in client.base_url

    def test_producao_base_url(self):
        """Test that producao uses production URL."""
        client = NFSeClient(
            cert_path=CERT_PATH,
            cert_password=CERT_PASSWORD,
            ambiente="producao",
        )

        assert "producaorestrita" not in client.base_url
        assert "sefin.nfse.gov.br" in client.base_url
