"""Unit tests for NFSeClient parametrizacao methods.

These tests mock HTTP responses to test the client logic without
making real API calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from pynfse_nacional import NFSeClient, NFSeAPIError
from pynfse_nacional.models import ConvenioMunicipal


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


class TestQueryConvenioMunicipal:
    """Tests for query_convenio_municipal method."""

    def test_municipio_com_convenio(self, mock_client):
        """Test successful query for municipality with convenio."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "parametrosConvenio": {
                    "aderenteAmbienteNacional": 1,
                    "aderenteEmissorNacional": 1,
                },
                "mensagem": "Parametros do convenio recuperados com sucesso.",
            },
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
            assert "parametrosConvenio" in result.raw_data

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
                mock_client.query_convenio_municipal(1302603)

            assert exc_info.value.code == "ERRO500"


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
            raw_data={"parametrosConvenio": {"aderenteEmissorNacional": 1}},
        )

        assert conv.aderido is True
        assert conv.raw_data is not None
