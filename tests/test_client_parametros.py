"""Unit tests for NFSeClient parametrizacao methods.

These tests mock HTTP responses to test the client logic without
making real API calls.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from pynfse_nacional import NFSeClient, NFSeAPIError
from pynfse_nacional.models import AliquotaServico, ConvenioMunicipal


class MockResponse:
    """Mock httpx.Response for testing."""

    def __init__(self, status_code: int, json_data=None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON data")

        return self._json_data


@pytest.fixture
def mock_client():
    """Create a mock NFSeClient without certificate loading."""
    with patch.object(NFSeClient, "_load_pkcs12") as mock_load:
        mock_load.return_value = (MagicMock(), MagicMock())

        client = NFSeClient(
            cert_path="/fake/cert.pfx",
            cert_password="fake_password",
            ambiente="homologacao",
        )

        yield client


class TestQueryAliquotaServico:
    """Tests for query_aliquota_servico method."""

    def test_servico_aderido_com_aliquota_dict(self, mock_client):
        """Test successful query returning dict with aliquota."""
        mock_response = MockResponse(
            status_code=200,
            json_data={"aliquota": 5.0, "vlAliq": 5.0},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_aliquota_servico(1302603, "040301", "2026-01")

            assert isinstance(result, AliquotaServico)
            assert result.codigo_municipio == 1302603
            assert result.codigo_servico == "040301000"  # Padded to 9 digits
            assert result.competencia == "2026-01"
            assert result.aliquota == 5.0
            assert result.aderido is True

    def test_servico_aderido_com_aliquota_numero(self, mock_client):
        """Test successful query returning just a number."""
        mock_response = MockResponse(
            status_code=200,
            json_data=3.5,
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_aliquota_servico(1302603, "040302", "2026-01")

            assert result.aliquota == 3.5
            assert result.aderido is True

    def test_servico_nao_aderido_404(self, mock_client):
        """Test 404 response for non-adhered service."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_aliquota_servico(1302603, "999999", "2026-01")

            assert result.codigo_servico == "999999000"  # Padded to 9 digits
            assert result.aderido is False
            assert result.aliquota is None

    def test_codigo_servico_com_pontos(self, mock_client):
        """Test that service code with dots is cleaned."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_aliquota_servico(1302603, "04.03.01", "2026-01")

            assert result.codigo_servico == "040301000"  # Padded to 9 digits

            call_args = mock_http.get.call_args[0][0]
            assert "040301000" in call_args  # 9-digit code in URL
            assert "04.03.01" not in call_args

    def test_url_format_correct(self, mock_client):
        """Test that URL is formatted correctly."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            mock_client.query_aliquota_servico(1302603, "040301", "2026-01")

            call_args = mock_http.get.call_args[0][0]
            assert "/1302603/040301000/2026-01/aliquota" in call_args  # 9-digit code

    def test_erro_api_500(self, mock_client):
        """Test API error handling for 500 response."""
        mock_response = MockResponse(
            status_code=500,
            json_data={"codigo": "ERRO500", "mensagem": "Erro interno do servidor"},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(NFSeAPIError) as exc_info:
                mock_client.query_aliquota_servico(1302603, "040301", "2026-01")

            assert exc_info.value.code == "ERRO500"

    def test_url_homologacao(self, mock_client):
        """Test that homologacao URL is used correctly."""
        assert "producaorestrita" in mock_client.parametrizacao_url
        assert "adn.producaorestrita.nfse.gov.br" in mock_client.parametrizacao_url

    def test_url_producao(self):
        """Test that producao URL is used correctly."""
        with patch.object(NFSeClient, "_load_pkcs12") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())

            client = NFSeClient(
                cert_path="/fake/cert.pfx",
                cert_password="fake_password",
                ambiente="producao",
            )

            assert "producaorestrita" not in client.parametrizacao_url
            assert "adn.nfse.gov.br" in client.parametrizacao_url


class TestQueryConvenioMunicipal:
    """Tests for query_convenio_municipal method."""

    def test_municipio_com_convenio(self, mock_client):
        """Test successful query for municipality with convenio."""
        mock_response = MockResponse(
            status_code=200,
            json_data={"aderido": True, "dataAdesao": "2025-01-01"},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_convenio_municipal(1302603)

            assert isinstance(result, ConvenioMunicipal)
            assert result.codigo_municipio == 1302603
            assert result.aderido is True
            assert result.raw_data is not None

    def test_municipio_sem_convenio_404(self, mock_client):
        """Test 404 response for municipality without convenio."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_convenio_municipal(9999999)

            assert result.codigo_municipio == 9999999
            assert result.aderido is False

    def test_url_format_correct(self, mock_client):
        """Test that URL is formatted correctly."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            mock_client.query_convenio_municipal(1302603)

            call_args = mock_http.get.call_args[0][0]
            assert "/1302603/convenio" in call_args


class TestVerificarServicoAderido:
    """Tests for verificar_servico_aderido method."""

    def test_servico_aderido_retorna_true(self, mock_client):
        """Test that adhered service returns True."""
        mock_response = MockResponse(
            status_code=200,
            json_data={"aliquota": 5.0},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.verificar_servico_aderido(1302603, "040301", "2026-01")

            assert result is True

    def test_servico_nao_aderido_retorna_false(self, mock_client):
        """Test that non-adhered service returns False."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.verificar_servico_aderido(1302603, "999999", "2026-01")

            assert result is False


class TestAliquotaServicoModel:
    """Tests for AliquotaServico model."""

    def test_create_aliquota_minimo(self):
        """Test creating AliquotaServico with minimum fields."""
        aliq = AliquotaServico(
            codigo_municipio=1302603,
            codigo_servico="040301",
            competencia="2026-01",
        )

        assert aliq.codigo_municipio == 1302603
        assert aliq.codigo_servico == "040301"
        assert aliq.competencia == "2026-01"
        assert aliq.aliquota is None
        assert aliq.aderido is True

    def test_create_aliquota_completo(self):
        """Test creating AliquotaServico with all fields."""
        aliq = AliquotaServico(
            codigo_municipio=1302603,
            codigo_servico="040301",
            competencia="2026-01",
            aliquota=Decimal("5.00"),
            aderido=True,
            raw_data={"test": "data"},
        )

        assert aliq.aliquota == Decimal("5.00")
        assert aliq.raw_data == {"test": "data"}

    def test_create_aliquota_nao_aderido(self):
        """Test creating AliquotaServico as not adhered."""
        aliq = AliquotaServico(
            codigo_municipio=1302603,
            codigo_servico="999999",
            competencia="2026-01",
            aderido=False,
        )

        assert aliq.aderido is False


class TestConvenioMunicipalModel:
    """Tests for ConvenioMunicipal model."""

    def test_create_convenio_minimo(self):
        """Test creating ConvenioMunicipal with minimum fields."""
        conv = ConvenioMunicipal(codigo_municipio=1302603)

        assert conv.codigo_municipio == 1302603
        assert conv.aderido is False
        assert conv.raw_data is None

    def test_create_convenio_aderido(self):
        """Test creating ConvenioMunicipal as adhered."""
        conv = ConvenioMunicipal(
            codigo_municipio=1302603,
            aderido=True,
            raw_data={"dataAdesao": "2025-01-01"},
        )

        assert conv.aderido is True
        assert conv.raw_data is not None
