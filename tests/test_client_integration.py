"""Integration tests for NFSeClient against producaorestrita (homologacao) environment.

These tests require:
- A valid ICP-Brasil A1 test certificate (.pfx)
- Environment variables:
  - NFSE_TEST_CERT_PATH: Path to test certificate
  - NFSE_TEST_CERT_PASSWORD: Certificate password

Run with: pytest backend/lib/pynfse_nacional/tests/test_client_integration.py -v -s

Note: producaorestrita environment may return mock/simulated responses.
"""

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from pynfse_nacional import (
    NFSeClient,
    NFSeAPIError,
    NFSeCertificateError,
)
from pynfse_nacional.models import (
    DPS,
    Prestador,
    Tomador,
    Servico,
    Endereco,
)


CERT_PATH = os.environ.get("NFSE_TEST_CERT_PATH", "")
CERT_PASSWORD = os.environ.get("NFSE_TEST_CERT_PASSWORD", "")

pytestmark = pytest.mark.skipif(
    not CERT_PATH or not os.path.exists(CERT_PATH),
    reason="Test certificate not configured. Set NFSE_TEST_CERT_PATH and NFSE_TEST_CERT_PASSWORD.",
)


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

    Uses fictional data for homologacao environment.
    """
    prestador_endereco = Endereco(
        logradouro="Rua Teste",
        numero="100",
        complemento="Sala 1",
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
        email="teste@teste.com",
        telefone="1999999999",
    )

    tomador = Tomador(
        cpf="12345678909",
        razao_social="Tomador Teste",
        email="tomador@teste.com",
        telefone="1988888888",
    )

    servico = Servico(
        codigo_lc116="4.03.03",
        discriminacao="Consulta medica de teste para homologacao",
        valor_servicos=Decimal("100.00"),
        iss_retido=False,
        aliquota_iss=Decimal("2.00"),
        aliquota_simples=Decimal("15.50"),
    )

    now = datetime.now(timezone.utc)
    competencia = now.strftime("%Y-%m")

    return DPS(
        serie="900",
        numero=int(now.timestamp()),
        competencia=competencia,
        data_emissao=now,
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        regime_tributario="simples_nacional",
        optante_simples=True,
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

        assert "not found" in str(exc_info.value).lower()

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
        """
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
                print("DPS rejected (expected in homologacao):")
                print(f"  Error Code: {response.error_code}")
                print(f"  Error Message: {response.error_message}")

                assert response.error_code is not None or response.error_message is not None

        except NFSeAPIError as e:
            print(f"API Error: {e.code} - {e.message}")
            if e.status_code:
                print(f"  HTTP Status: {e.status_code}")

            if e.code == "TIMEOUT":
                pytest.skip("API timeout - SEFIN may be unavailable")


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

        print(f"Query error (expected): {exc_info.value.code} - {exc_info.value.message}")


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

        print(f"Download error (expected): {exc_info.value.code} - {exc_info.value.message}")


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
        print(f"Cancel error (expected): {response.error_code} - {response.error_message}")


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
