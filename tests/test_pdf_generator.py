"""Tests for pdf_generator module.

These tests verify the DANFSE PDF generation functionality.
Note: Some tests require the optional [pdf] dependencies (reportlab, qrcode).
"""

import base64
import gzip
import pytest

# Check if PDF dependencies are available
try:
    from pynfse_nacional.pdf_generator import (
        HeaderConfig,
        NFSeData,
        parse_nfse_xml,
        generate_danfse_pdf,
        generate_danfse_from_xml,
        generate_danfse_from_base64,
        _format_datetime,
        _format_date,
        _format_phone,
        _format_currency,
        _format_cep,
        _get_simples_nacional_desc,
        _get_regime_apuracao_desc,
        _get_trib_issqn_desc,
        _get_retencao_issqn_desc,
    )

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not PDF_AVAILABLE,
    reason="PDF dependencies not installed. Install with: pip install pynfse-nacional[pdf]",
)


# =============================================================================
# Sample XML for testing
# =============================================================================

SAMPLE_NFSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
    <infNFSe Id="NFS12345678901234567890123456789012345678901234567890">
        <nNFSe>12345</nNFSe>
        <dhProc>2026-01-15T10:30:00-03:00</dhProc>
        <xLocEmi>Campinas</xLocEmi>
        <xLocIncid>Campinas</xLocIncid>
        <DPS>
            <infDPS>
                <nDPS>1</nDPS>
                <serie>900</serie>
                <dhEmi>2026-01-15T10:00:00-03:00</dhEmi>
                <dCompet>2026-01-15</dCompet>
                <prest>
                    <CNPJ>11222333000181</CNPJ>
                    <IM>12345</IM>
                    <fone>1999999999</fone>
                    <email>empresa@teste.com</email>
                    <regTrib>
                        <opSimpNac>3</opSimpNac>
                        <regApTribSN>1</regApTribSN>
                    </regTrib>
                </prest>
                <toma>
                    <CPF>52998224725</CPF>
                    <xNome>Joao Silva</xNome>
                    <fone>1988888888</fone>
                    <email>joao@email.com</email>
                </toma>
                <serv>
                    <cServ>
                        <cTribNac>040303</cTribNac>
                        <cTribMun>123456</cTribMun>
                        <xDescServ>Consulta medica de rotina</xDescServ>
                        <cNBS>101010100</cNBS>
                    </cServ>
                    <locPrest>
                        <cLocPrestacao>3509502</cLocPrestacao>
                    </locPrest>
                </serv>
                <valores>
                    <vServPrest>
                        <vServ>500.00</vServ>
                    </vServPrest>
                    <trib>
                        <tribMun>
                            <tribISSQN>1</tribISSQN>
                            <tpRetISSQN>1</tpRetISSQN>
                        </tribMun>
                        <totTrib>
                            <pTotTribSN>15.50</pTotTribSN>
                        </totTrib>
                    </trib>
                </valores>
            </infDPS>
        </DPS>
        <emit>
            <CNPJ>11222333000181</CNPJ>
            <IM>12345</IM>
            <xNome>Clinica Medica Teste LTDA</xNome>
            <fone>1999999999</fone>
            <email>empresa@teste.com</email>
            <enderNac>
                <xLgr>Rua Teste</xLgr>
                <nro>100</nro>
                <xBairro>Centro</xBairro>
                <UF>SP</UF>
                <CEP>13000000</CEP>
            </enderNac>
        </emit>
        <valores>
            <vBC>500.00</vBC>
            <pAliqAplic>2.00</pAliqAplic>
            <vISSQN>10.00</vISSQN>
            <vLiq>500.00</vLiq>
        </valores>
    </infNFSe>
</NFSe>"""


# =============================================================================
# Tests: HeaderConfig
# =============================================================================


class TestHeaderConfig:
    """Tests for HeaderConfig dataclass."""

    def test_default_values(self):
        """Should have correct default values."""
        config = HeaderConfig()

        assert config.image_path is None
        assert config.title == ""
        assert config.subtitle == ""
        assert config.phone == ""
        assert config.email == ""

    def test_has_custom_header_false_by_default(self):
        """Should return False when no custom header set."""
        config = HeaderConfig()

        assert config.has_custom_header() is False

    def test_has_custom_header_true_with_title(self):
        """Should return True when title is set."""
        config = HeaderConfig(title="My Company")

        assert config.has_custom_header() is True

    def test_has_custom_header_true_with_image(self):
        """Should return True when image_path is set."""
        config = HeaderConfig(image_path="/path/to/logo.png")

        assert config.has_custom_header() is True


# =============================================================================
# Tests: NFSeData
# =============================================================================


class TestNFSeData:
    """Tests for NFSeData dataclass."""

    def test_default_values(self):
        """Should have empty string defaults."""
        data = NFSeData()

        assert data.chave_acesso == ""
        assert data.numero_nfse == ""
        assert data.emit_cnpj == ""
        assert data.valor_servico == ""

    def test_can_set_values(self):
        """Should allow setting all values."""
        data = NFSeData(
            chave_acesso="12345678901234567890123456789012345678901234567890",
            numero_nfse="12345",
            emit_cnpj="11222333000181",
            valor_servico="500.00",
        )

        assert data.chave_acesso == "12345678901234567890123456789012345678901234567890"
        assert data.numero_nfse == "12345"


# =============================================================================
# Tests: Formatting functions
# =============================================================================


class TestFormatDatetime:
    """Tests for _format_datetime function."""

    def test_formats_iso_datetime(self):
        """Should format ISO datetime to Brazilian format."""
        result = _format_datetime("2026-01-15T10:30:00-03:00")

        assert result == "15/01/2026 10:30:00"

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        result = _format_datetime("")

        assert result == ""

    def test_handles_utc_datetime(self):
        """Should handle Z timezone suffix."""
        result = _format_datetime("2026-01-15T13:30:00Z")

        assert "15/01/2026" in result


class TestFormatDate:
    """Tests for _format_date function."""

    def test_formats_iso_date(self):
        """Should format ISO date to Brazilian format."""
        result = _format_date("2026-01-15")

        assert result == "15/01/2026"

    def test_handles_datetime_with_time(self):
        """Should extract date from datetime."""
        result = _format_date("2026-01-15T10:30:00")

        assert result == "15/01/2026"

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        result = _format_date("")

        assert result == ""


class TestFormatPhone:
    """Tests for _format_phone function."""

    def test_formats_11_digit_phone(self):
        """Should format 11-digit mobile phone."""
        result = _format_phone("11999999999")

        assert result == "(11) 99999-9999"

    def test_formats_10_digit_phone(self):
        """Should format 10-digit landline phone."""
        result = _format_phone("1133334444")

        assert result == "(11) 3333-4444"

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        result = _format_phone("")

        assert result == ""

    def test_strips_non_digits(self):
        """Should strip non-digit characters and return raw if not 10-11 digits."""
        # When phone has 13 digits (with country code), returns unformatted
        result = _format_phone("+55 (11) 99999-9999")

        assert result == "5511999999999"

    def test_formats_after_stripping(self):
        """Should format correctly after stripping non-digits."""
        # 11 digits after stripping
        result = _format_phone("(11) 99999-9999")

        assert result == "(11) 99999-9999"


class TestFormatCurrency:
    """Tests for _format_currency function."""

    def test_formats_decimal_value(self):
        """Should format as Brazilian currency."""
        result = _format_currency("500.00")

        assert result == "R$ 500,00"

    def test_formats_large_value(self):
        """Should format large values with thousand separator."""
        result = _format_currency("1234567.89")

        assert result == "R$ 1.234.567,89"

    def test_handles_empty_string(self):
        """Should return dash for empty input."""
        result = _format_currency("")

        assert result == "-"


class TestFormatCep:
    """Tests for _format_cep function."""

    def test_formats_8_digit_cep(self):
        """Should format CEP with dash."""
        result = _format_cep("13000000")

        assert result == "13000-000"

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        result = _format_cep("")

        assert result == ""


# =============================================================================
# Tests: Description functions
# =============================================================================


class TestGetSimplesNacionalDesc:
    """Tests for _get_simples_nacional_desc function."""

    def test_mei(self):
        """Should return MEI description."""
        result = _get_simples_nacional_desc("1")

        assert "MEI" in result

    def test_me_epp_excesso(self):
        """Should return ME/EPP excesso description."""
        result = _get_simples_nacional_desc("2")

        assert "Excesso" in result

    def test_me_epp(self):
        """Should return ME/EPP description."""
        result = _get_simples_nacional_desc("3")

        assert "ME/EPP" in result

    def test_nao_optante(self):
        """Should return non-optante description."""
        result = _get_simples_nacional_desc("4")

        assert "Nao Optante" in result

    def test_unknown(self):
        """Should return dash for unknown code."""
        result = _get_simples_nacional_desc("99")

        assert result == "-"


class TestGetTribIssqnDesc:
    """Tests for _get_trib_issqn_desc function."""

    def test_tributavel(self):
        """Should return tributavel description."""
        result = _get_trib_issqn_desc("1")

        assert "Tributavel" in result

    def test_imunidade(self):
        """Should return imunidade description."""
        result = _get_trib_issqn_desc("2")

        assert "Imunidade" in result

    def test_exportacao(self):
        """Should return exportacao description."""
        result = _get_trib_issqn_desc("3")

        assert "Exportacao" in result

    def test_nao_incidencia(self):
        """Should return nao incidencia description."""
        result = _get_trib_issqn_desc("4")

        assert "Nao Incidencia" in result


class TestGetRetencaoIssqnDesc:
    """Tests for _get_retencao_issqn_desc function."""

    def test_nao_retido(self):
        """Should return not retained description."""
        result = _get_retencao_issqn_desc("1")

        assert "Nao Retido" in result

    def test_retido_tomador(self):
        """Should return retained by tomador description."""
        result = _get_retencao_issqn_desc("2")

        assert "Tomador" in result

    def test_retido_intermediario(self):
        """Should return retained by intermediario description."""
        result = _get_retencao_issqn_desc("3")

        assert "Intermediario" in result


# =============================================================================
# Tests: parse_nfse_xml
# =============================================================================


class TestParseNfseXml:
    """Tests for parse_nfse_xml function."""

    def test_parses_chave_acesso(self):
        """Should extract chave_acesso from infNFSe Id."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.chave_acesso == "12345678901234567890123456789012345678901234567890"

    def test_parses_numero_nfse(self):
        """Should extract numero_nfse."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.numero_nfse == "12345"

    def test_parses_emitente_cnpj(self):
        """Should extract emitente CNPJ."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.emit_cnpj == "11222333000181"

    def test_parses_emitente_nome(self):
        """Should extract emitente name."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.emit_nome == "Clinica Medica Teste LTDA"

    def test_parses_tomador_cpf(self):
        """Should extract tomador CPF."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.toma_cpf == "52998224725"

    def test_parses_tomador_nome(self):
        """Should extract tomador name."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.toma_nome == "Joao Silva"

    def test_parses_valor_servico(self):
        """Should extract service value."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.valor_servico == "500.00"

    def test_parses_cod_trib_nac(self):
        """Should extract national tributation code."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.cod_trib_nac == "040303"

    def test_parses_descricao_servico(self):
        """Should extract service description."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.descricao_servico == "Consulta medica de rotina"

    def test_parses_municipio(self):
        """Should extract municipality."""
        data = parse_nfse_xml(SAMPLE_NFSE_XML)

        assert data.emit_municipio == "Campinas"

    def test_raises_on_invalid_xml(self):
        """Should raise ValueError for XML without infNFSe."""
        invalid_xml = '<?xml version="1.0"?><root>invalid</root>'

        with pytest.raises(ValueError) as exc_info:
            parse_nfse_xml(invalid_xml)

        assert "infNFSe" in str(exc_info.value)


# =============================================================================
# Tests: generate_danfse_pdf
# =============================================================================


class TestGenerateDanfsePdf:
    """Tests for generate_danfse_pdf function."""

    def test_returns_bytes(self):
        """Should return PDF content as bytes."""
        data = NFSeData(
            chave_acesso="12345678901234567890123456789012345678901234567890",
            numero_nfse="12345",
            emit_nome="Empresa Teste",
            valor_servico="500.00",
        )

        result = generate_danfse_pdf(data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_starts_with_correct_header(self):
        """Should generate valid PDF with correct header."""
        data = NFSeData(
            chave_acesso="12345678901234567890123456789012345678901234567890",
            numero_nfse="12345",
        )

        result = generate_danfse_pdf(data)

        # PDF files start with %PDF
        assert result[:4] == b"%PDF"

    def test_accepts_custom_header(self):
        """Should accept custom header configuration."""
        data = NFSeData(
            chave_acesso="12345678901234567890123456789012345678901234567890",
        )

        header = HeaderConfig(
            title="My Company",
            subtitle="Medical Services",
            phone="11999999999",
            email="contact@company.com",
        )

        result = generate_danfse_pdf(data, header_config=header)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestGenerateDanfseFromXml:
    """Tests for generate_danfse_from_xml function."""

    def test_generates_pdf_from_xml(self):
        """Should generate PDF from XML content."""
        result = generate_danfse_from_xml(SAMPLE_NFSE_XML)

        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"


class TestGenerateDanfseFromBase64:
    """Tests for generate_danfse_from_base64 function."""

    def test_generates_pdf_from_base64_gzip(self):
        """Should generate PDF from base64-encoded gzipped XML."""
        compressed = gzip.compress(SAMPLE_NFSE_XML.encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("utf-8")

        result = generate_danfse_from_base64(encoded)

        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_roundtrip_with_api_format(self):
        """Should work with format returned by API (nfseXmlGZipB64)."""
        xml_content = SAMPLE_NFSE_XML
        compressed = gzip.compress(xml_content.encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("utf-8")

        result = generate_danfse_from_base64(encoded)

        assert isinstance(result, bytes)
        assert len(result) > 1000  # Should be a reasonable PDF size
