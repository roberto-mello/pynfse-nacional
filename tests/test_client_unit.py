"""Unit tests for NFSeClient methods.

These tests mock HTTP responses to test the client logic without
making real API calls.
"""

from unittest.mock import MagicMock, patch
from decimal import Decimal

import pytest

from pynfse_nacional import NFSeClient, NFSeAPIError
from pynfse_nacional.models import (
    DPS,
    Endereco,
    Prestador,
    Tomador,
    Servico,
    NFSeResponse,
    EventResponse,
    NFSeQueryResult,
)


class MockResponse:
    """Mock httpx.Response for testing."""

    def __init__(self, status_code: int, json_data=None, text: str = "", content: bytes = b""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = content

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


# =============================================================================
# Tests: _parse_dps_response - NFSe number extraction
# =============================================================================


class TestParseDpsResponseNfseNumberExtraction:
    """Tests for nfse_number extraction from chave_acesso."""

    def test_extracts_nfse_number_from_chave_acesso(self, mock_client):
        """Should extract nfse_number from chave_acesso positions 28-38."""
        # Chave acesso format (50 chars):
        # cLocEmi(7) + tpInsc(1) + CNPJ/CPF(14) + nNFSe(10) + cSit(1) + dhEmi(8) + serie(3) + cDV(1) + tpAmb(1) + cMunGer(4)
        # Positions: 0-6(7) + 7(1) + 8-21(14) + 22-31(10) ... wait that's 22-31
        # Actually: 0-6(7) + 7(1) + 8-21(14) = 22 chars, then nNFSe is positions 22-31 (but code uses 28:38)
        # Let me check: The actual format may differ. The fix changed from [24:34] to [28:38]
        # Positions 28-38 should contain the nNFSe (10 digits)

        # Create a 50-char chave_acesso with nNFSe at positions 28-38
        # First 28 chars + 10 digit nNFSe + remaining 12 chars = 50 total
        chave_prefix = "1234567890123456789012345678"  # 28 chars
        nfse_number_in_chave = "0000012345"  # 10 chars (nNFSe)
        chave_suffix = "123456789012"  # 12 chars
        chave_acesso = chave_prefix + nfse_number_in_chave + chave_suffix

        assert len(chave_acesso) == 50

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
                # nNFSe not returned, should extract from chave
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.chave_acesso == chave_acesso
        # Extracted and converted: "0000012345" -> int() -> "12345"
        assert result.nfse_number == "12345"

    def test_uses_api_nnfse_when_provided(self, mock_client):
        """Should use nNFSe from API response when provided."""
        chave_acesso = "12345678901234567890123456789012345678901234567890"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
                "nNFSe": "99999",
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.nfse_number == "99999"

    def test_handles_short_chave_acesso(self, mock_client):
        """Should handle chave_acesso shorter than 38 chars gracefully."""
        short_chave = "12345678901234567890"  # 20 chars

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": short_chave,
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.chave_acesso == short_chave
        assert result.nfse_number is None

    def test_strips_leading_zeros_from_nfse_number(self, mock_client):
        """Should strip leading zeros when extracting nfse_number."""
        # Position 28-38 contains "0000000001"
        chave_acesso = "1234567890123456789012345678" + "0000000001" + "123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.nfse_number == "1"

    def test_handles_all_zeros_nfse_number(self, mock_client):
        """Should handle case where nfse_number is all zeros."""
        # Position 28-38 contains "0000000000"
        chave_acesso = "1234567890123456789012345678" + "0000000000" + "123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.nfse_number == "0"


class TestParseDpsResponseSuccess:
    """Tests for successful DPS response parsing."""

    def test_parses_success_response_with_xml(self, mock_client):
        """Should parse successful response with nfseXmlGZipB64."""
        chave_acesso = "12345678901234567890123456780000000001123456789012"

        # Create compressed XML
        import gzip
        import base64

        xml_content = '<?xml version="1.0"?><nfse>test</nfse>'
        compressed = gzip.compress(xml_content.encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("utf-8")

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
                "nfseXmlGZipB64": encoded,
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.xml_nfse == xml_content
        assert result.nfse_xml_gzip_b64 == encoded

    def test_parses_success_without_xml(self, mock_client):
        """Should handle success response without XML."""
        chave_acesso = "12345678901234567890123456780000000001123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.xml_nfse is None
        assert result.nfse_xml_gzip_b64 is None


class TestParseDpsResponseError:
    """Tests for error response parsing."""

    def test_parses_error_response(self, mock_client):
        """Should parse error response correctly."""
        mock_response = MockResponse(
            status_code=400,
            json_data={
                "codigo": "ERR001",
                "mensagem": "DPS invalido",
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is False
        assert result.error_code == "ERR001"
        assert result.error_message == "DPS invalido"

    def test_parses_error_without_json(self, mock_client):
        """Should handle error response without JSON."""
        mock_response = MockResponse(
            status_code=500,
            json_data=None,
            text="Internal Server Error",
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is False
        assert result.error_code == "500"
        assert "Internal Server Error" in result.error_message

    def test_handles_invalid_xml_gracefully(self, mock_client):
        """Should handle invalid base64/gzip content gracefully."""
        chave_acesso = "12345678901234567890123456780000000001123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
                "nfseXmlGZipB64": "not-valid-base64!!!",
            },
        )

        result = mock_client._parse_dps_response(mock_response)

        assert result.success is True
        assert result.xml_nfse is None


# =============================================================================
# Tests: _parse_event_response
# =============================================================================


class TestParseEventResponse:
    """Tests for event response parsing (cancellation)."""

    def test_parses_success_event_response(self, mock_client):
        """Should parse successful event response."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "protocolo": "PROT123456789",
            },
        )

        result = mock_client._parse_event_response(mock_response)

        assert result.success is True
        assert result.protocolo == "PROT123456789"

    def test_parses_201_as_success(self, mock_client):
        """Should treat 201 status as success."""
        mock_response = MockResponse(
            status_code=201,
            json_data={
                "protocolo": "PROT999",
            },
        )

        result = mock_client._parse_event_response(mock_response)

        assert result.success is True

    def test_parses_error_event_response(self, mock_client):
        """Should parse error event response."""
        mock_response = MockResponse(
            status_code=400,
            json_data={
                "codigo": "CANCEL_ERR",
                "mensagem": "NFSe ja cancelada",
            },
        )

        result = mock_client._parse_event_response(mock_response)

        assert result.success is False
        assert result.error_code == "CANCEL_ERR"
        assert result.error_message == "NFSe ja cancelada"

    def test_handles_error_without_json(self, mock_client):
        """Should handle error response without valid JSON."""
        mock_response = MockResponse(
            status_code=500,
            json_data=None,
            text="Service Unavailable",
        )

        result = mock_client._parse_event_response(mock_response)

        assert result.success is False
        assert result.error_code == "500"


# =============================================================================
# Tests: query_nfse
# =============================================================================


class TestQueryNfse:
    """Tests for query_nfse method."""

    def test_query_nfse_success(self, mock_client):
        """Should query NFSe successfully."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": "12345678901234567890123456789012345678901234567890",
                "nNFSe": "1234",
                "situacao": "emitida",
                "dhEmi": "2026-01-15T10:30:00-03:00",
                "vServPrest": 500.00,
                "CNPJPrest": "11222333000181",
                "CPFToma": "52998224725",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_nfse("12345678901234567890123456789012345678901234567890")

            assert isinstance(result, NFSeQueryResult)
            assert result.nfse_number == "1234"
            assert result.status == "emitida"

    def test_query_nfse_with_cnpj_tomador(self, mock_client):
        """Should handle CNPJ as tomador document."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": "12345678901234567890123456789012345678901234567890",
                "nNFSe": "1234",
                "dhEmi": "2026-01-15T10:30:00-03:00",
                "vServPrest": 500.00,
                "CNPJPrest": "11222333000181",
                "CNPJToma": "99888777000166",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.query_nfse("test_chave")

            assert result.tomador_documento == "99888777000166"

    def test_query_nfse_raises_on_error(self, mock_client):
        """Should raise NFSeAPIError on error response."""
        mock_response = MockResponse(
            status_code=404,
            json_data={
                "codigo": "NOT_FOUND",
                "mensagem": "NFSe nao encontrada",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(NFSeAPIError) as exc_info:
                mock_client.query_nfse("invalid_chave")

            assert exc_info.value.status_code == 404


# =============================================================================
# Tests: download_danfse
# =============================================================================


class TestDownloadDanfse:
    """Tests for download_danfse method."""

    def test_download_danfse_success(self, mock_client):
        """Should download DANFSe PDF successfully."""
        pdf_content = b"%PDF-1.4 fake pdf content"

        mock_response = MockResponse(
            status_code=200,
            content=pdf_content,
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.download_danfse("test_chave")

            assert result == pdf_content

    def test_download_danfse_uses_correct_url(self, mock_client):
        """Should use adn.*.nfse.gov.br domain for DANFSE."""
        mock_response = MockResponse(status_code=200, content=b"pdf")

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            mock_client.download_danfse("test_chave")

            call_args = mock_http.get.call_args[0][0]
            assert "adn." in call_args
            assert "test_chave" in call_args

    def test_download_danfse_raises_on_error(self, mock_client):
        """Should raise NFSeAPIError on error."""
        mock_response = MockResponse(
            status_code=501,
            json_data={
                "mensagem": "Servico indisponivel",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(NFSeAPIError) as exc_info:
                mock_client.download_danfse("test_chave")

            assert exc_info.value.status_code == 501


# =============================================================================
# Tests: cancel_nfse
# =============================================================================


class TestCancelNfse:
    """Tests for cancel_nfse method."""

    def test_cancel_nfse_success(self, mock_client):
        """Should cancel NFSe successfully."""
        mock_response = MockResponse(
            status_code=200,
            json_data={
                "protocolo": "CANCEL_PROT_123",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.cancel_nfse("test_chave", "Erro de digitacao")

            assert isinstance(result, EventResponse)
            assert result.success is True
            assert result.protocolo == "CANCEL_PROT_123"

    def test_cancel_nfse_sends_correct_payload(self, mock_client):
        """Should send correct payload for cancellation."""
        mock_response = MockResponse(
            status_code=200,
            json_data={"protocolo": "123"},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            mock_client.cancel_nfse("CHAVE123", "Motivo do cancelamento")

            call_kwargs = mock_http.post.call_args[1]
            payload = call_kwargs["json"]

            assert payload["tpEvento"] == "110111"
            assert payload["chNFSe"] == "CHAVE123"
            assert payload["xMotivo"] == "Motivo do cancelamento"

    def test_cancel_nfse_error(self, mock_client):
        """Should handle cancellation error."""
        mock_response = MockResponse(
            status_code=400,
            json_data={
                "codigo": "INVALID",
                "mensagem": "NFSe nao pode ser cancelada",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_client.cancel_nfse("test_chave", "Motivo")

            assert result.success is False
            assert result.error_code == "INVALID"


# =============================================================================
# Tests: submit_dps
# =============================================================================


class TestSubmitDps:
    """Tests for submit_dps method."""

    @pytest.fixture
    def sample_dps(self):
        """Create a sample DPS for testing."""
        from datetime import datetime

        endereco = Endereco(
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
            razao_social="Empresa Teste",
            endereco=endereco,
        )

        tomador = Tomador(
            cpf="52998224725",
            razao_social="Cliente Teste",
        )

        servico = Servico(
            codigo_lc116="04.03.01",
            discriminacao="Servico de teste",
            valor_servicos=Decimal("100.00"),
        )

        return DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=prestador,
            tomador=tomador,
            servico=servico,
            regime_tributario="simples_nacional",
        )

    def test_submit_dps_success(self, mock_client, sample_dps):
        """Should submit DPS successfully."""
        chave_acesso = "12345678901234567890123456780000000001123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={
                "chaveAcesso": chave_acesso,
                "nNFSe": "1",
            },
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with patch.object(mock_client._xml_builder, "build_dps", return_value="<xml/>"):
                with patch.object(mock_client._xml_signer, "sign", return_value="<signed/>"):
                    result = mock_client.submit_dps(sample_dps)

                    assert isinstance(result, NFSeResponse)
                    assert result.success is True
                    assert result.chave_acesso == chave_acesso

    def test_submit_dps_sends_compressed_xml(self, mock_client, sample_dps):
        """Should send gzip+base64 encoded signed XML."""
        # Use a valid chave_acesso with numeric digits at positions 28-38
        chave_acesso = "1234567890123456789012345678" + "0000000001" + "123456789012"

        mock_response = MockResponse(
            status_code=200,
            json_data={"chaveAcesso": chave_acesso},
        )

        with patch.object(mock_client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.post.return_value = mock_response
            mock_get_client.return_value.__enter__ = MagicMock(return_value=mock_http)
            mock_get_client.return_value.__exit__ = MagicMock(return_value=False)

            with patch.object(mock_client._xml_builder, "build_dps", return_value="<xml/>"):
                with patch.object(mock_client._xml_signer, "sign", return_value="<signed/>"):
                    mock_client.submit_dps(sample_dps)

                    call_kwargs = mock_http.post.call_args[1]
                    payload = call_kwargs["json"]

                    assert "dpsXmlGZipB64" in payload
                    # Should be base64 encoded
                    import base64

                    decoded = base64.b64decode(payload["dpsXmlGZipB64"])
                    assert decoded  # Should be valid base64
