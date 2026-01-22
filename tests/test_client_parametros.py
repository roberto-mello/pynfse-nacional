"""Unit tests for NFSeClient parametros_municipais methods.

These tests mock HTTP responses to test the client logic without
making real API calls.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from pynfse_nacional import NFSeClient, NFSeAPIError
from pynfse_nacional.models import ParametrosMunicipais, ServicoMunicipal


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


class TestQueryParametrosMunicipais:
    """Tests for query_parametros_municipais method."""

    def test_municipio_aderido_com_servicos_lista(self, mock_client):
        """Test successful query returning list of services."""
        mock_response = MockResponse(
            status_code=200,
            json_data=[
                {"cTribNac": "040301", "descricao": "Medicina", "aliquota": 5.0},
                {"cTribNac": "040302", "descricao": "Analises", "aliquota": 3.0},
            ],
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_parametros_municipais(1302603)

            assert isinstance(result, ParametrosMunicipais)
            assert result.codigo_municipio == 1302603
            assert result.aderido is True
            assert len(result.servicos) == 2
            assert result.servicos[0].codigo_servico == "040301"
            assert result.servicos[0].descricao == "Medicina"
            assert result.servicos[0].aderido is True
            assert result.servicos[1].codigo_servico == "040302"

    def test_municipio_aderido_com_dados_objeto(self, mock_client):
        """Test successful query returning object with municipality data."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "nomeMunicipio": "Manaus",
                "uf": "AM",
                "aderido": True,
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_parametros_municipais(1302603)

            assert result.nome_municipio == "Manaus"
            assert result.uf == "AM"
            assert result.aderido is True

    def test_municipio_nao_aderido_404(self, mock_client):
        """Test 404 response for non-adhered municipality."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_parametros_municipais(9999999)

            assert result.codigo_municipio == 9999999
            assert result.aderido is False
            assert len(result.servicos) == 0

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
                mock_client.query_parametros_municipais(1302603)

            assert exc_info.value.code == "ERRO500"
            assert "interno" in exc_info.value.message

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


class TestQueryServicoMunicipal:
    """Tests for query_servico_municipal method."""

    def test_servico_aderido_lista(self, mock_client):
        """Test successful query returning list with service data."""
        mock_response = MockResponse(
            status_code=200,
            json_data=[
                {"cTribNac": "040301", "descricao": "Medicina geral", "aliquota": 5.0},
            ],
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_servico_municipal(1302603, "040301")

            assert isinstance(result, ServicoMunicipal)
            assert result.codigo_servico == "040301"
            assert result.descricao == "Medicina geral"
            assert result.aliquota == 5.0
            assert result.aderido is True

    def test_servico_aderido_objeto(self, mock_client):
        """Test successful query returning object with service data."""
        mock_response = MockResponse(
            status_code=200,
            json_data={"cTribNac": "040301", "descricao": "Medicina", "aliquota": 2.5},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_servico_municipal(1302603, "040301")

            assert result.codigo_servico == "040301"
            assert result.aliquota == 2.5
            assert result.aderido is True

    def test_servico_nao_aderido_404(self, mock_client):
        """Test 404 response for non-adhered service."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_servico_municipal(1302603, "999999")

            assert result.codigo_servico == "999999"
            assert result.aderido is False

    def test_codigo_servico_com_pontos(self, mock_client):
        """Test that service code with dots is cleaned."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_servico_municipal(1302603, "04.03.01")

            assert result.codigo_servico == "040301"

            call_args = mock_http.get.call_args[0][0]
            assert "040301" in call_args
            assert "04.03.01" not in call_args

    def test_erro_api_422(self, mock_client):
        """Test API error handling for validation error."""
        mock_response = MockResponse(
            status_code=422,
            json_data={"codigo": "E0001", "mensagem": "Codigo de municipio invalido"},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(NFSeAPIError) as exc_info:
                mock_client.query_servico_municipal(1234, "040301")

            assert exc_info.value.code == "E0001"


class TestListarServicosAderidos:
    """Tests for listar_servicos_aderidos method."""

    def test_listar_servicos_com_dados(self, mock_client):
        """Test listing services from a municipality."""
        mock_response = MockResponse(
            status_code=200,
            json_data=[
                {"cTribNac": "040301", "descricao": "Medicina", "aliquota": 5.0},
                {"cTribNac": "040302", "descricao": "Analises", "aliquota": 3.0},
                {"cTribNac": "040303", "descricao": "Cirurgia", "aliquota": 2.0},
            ],
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.listar_servicos_aderidos(1302603)

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(s, ServicoMunicipal) for s in result)
            assert result[0].codigo_servico == "040301"
            assert result[2].codigo_servico == "040303"

    def test_listar_servicos_municipio_sem_servicos(self, mock_client):
        """Test listing services from municipality with no adhered services."""
        mock_response = MockResponse(status_code=200, json_data=[])

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.listar_servicos_aderidos(1302603)

            assert result == []

    def test_listar_servicos_municipio_nao_aderido(self, mock_client):
        """Test listing services from non-adhered municipality."""
        mock_response = MockResponse(status_code=404)

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.listar_servicos_aderidos(9999999)

            assert result == []


class TestParametrosMunicipaisModel:
    """Tests for ParametrosMunicipais model."""

    def test_create_parametros_minimo(self):
        """Test creating ParametrosMunicipais with minimum fields."""
        params = ParametrosMunicipais(codigo_municipio=1302603)

        assert params.codigo_municipio == 1302603
        assert params.nome_municipio is None
        assert params.uf is None
        assert params.aderido is False
        assert params.servicos == []

    def test_create_parametros_completo(self):
        """Test creating ParametrosMunicipais with all fields."""
        servicos = [
            ServicoMunicipal(codigo_servico="040301", descricao="Medicina", aliquota=Decimal("5.00")),
        ]

        params = ParametrosMunicipais(
            codigo_municipio=1302603,
            nome_municipio="Manaus",
            uf="AM",
            aderido=True,
            servicos=servicos,
            raw_data={"test": "data"},
        )

        assert params.nome_municipio == "Manaus"
        assert params.uf == "AM"
        assert params.aderido is True
        assert len(params.servicos) == 1
        assert params.raw_data == {"test": "data"}


class TestServicoMunicipalModel:
    """Tests for ServicoMunicipal model."""

    def test_create_servico_minimo(self):
        """Test creating ServicoMunicipal with minimum fields."""
        servico = ServicoMunicipal(codigo_servico="040301")

        assert servico.codigo_servico == "040301"
        assert servico.descricao is None
        assert servico.aliquota is None
        assert servico.aderido is True

    def test_create_servico_completo(self):
        """Test creating ServicoMunicipal with all fields."""
        servico = ServicoMunicipal(
            codigo_servico="040301",
            descricao="Medicina e biomedicina",
            aliquota=Decimal("5.00"),
            aderido=True,
        )

        assert servico.codigo_servico == "040301"
        assert servico.descricao == "Medicina e biomedicina"
        assert servico.aliquota == Decimal("5.00")
        assert servico.aderido is True

    def test_create_servico_nao_aderido(self):
        """Test creating ServicoMunicipal as not adhered."""
        servico = ServicoMunicipal(codigo_servico="999999", aderido=False)

        assert servico.codigo_servico == "999999"
        assert servico.aderido is False
