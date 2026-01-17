"""Tests for utils module."""

import pytest

from backend.lib.pynfse_nacional.utils import (
    compress_encode,
    compress_and_encode,
    decode_decompress,
    decode_and_decompress,
    validate_cnpj,
    validate_cpf,
    format_cnpj,
    format_cpf,
    normalize_document,
    clean_document,
)


class TestCompression:
    """Tests for GZip compression and Base64 encoding."""

    def test_compress_encode_basic(self):
        """Test basic compression and encoding."""
        data = "Hello, World!"
        encoded = compress_encode(data)

        assert isinstance(encoded, str)
        assert encoded != data

    def test_decode_decompress_basic(self):
        """Test basic decoding and decompression."""
        original = "Hello, World!"
        encoded = compress_encode(original)
        decoded = decode_decompress(encoded)

        assert decoded == original

    def test_compress_and_encode_alias(self):
        """Test that compress_and_encode is an alias for compress_encode."""
        data = "Test data"

        assert compress_and_encode(data) == compress_encode(data)

    def test_decode_and_decompress_alias(self):
        """Test that decode_and_decompress is an alias for decode_decompress."""
        data = "Test data"
        encoded = compress_encode(data)

        assert decode_and_decompress(encoded) == decode_decompress(encoded)

    def test_roundtrip_xml(self):
        """Test roundtrip with XML-like content."""
        xml = '<?xml version="1.0"?><root><item>Test</item></root>'
        encoded = compress_encode(xml)
        decoded = decode_decompress(encoded)

        assert decoded == xml

    def test_roundtrip_unicode(self):
        """Test roundtrip with Unicode characters."""
        data = "Servico de saude - Consulta medica R$ 150,00"
        encoded = compress_encode(data)
        decoded = decode_decompress(encoded)

        assert decoded == data


class TestCNPJValidation:
    """Tests for CNPJ validation."""

    def test_valid_cnpj(self):
        """Test valid CNPJ numbers."""
        assert validate_cnpj("11222333000181") is True
        assert validate_cnpj("11.222.333/0001-81") is True

    def test_invalid_cnpj_wrong_digits(self):
        """Test CNPJ with wrong check digits."""
        assert validate_cnpj("11222333000182") is False

    def test_invalid_cnpj_repeated_digits(self):
        """Test CNPJ with all repeated digits."""
        assert validate_cnpj("11111111111111") is False
        assert validate_cnpj("00000000000000") is False

    def test_invalid_cnpj_wrong_length(self):
        """Test CNPJ with wrong length."""
        assert validate_cnpj("1122233300018") is False
        assert validate_cnpj("112223330001811") is False


class TestCPFValidation:
    """Tests for CPF validation."""

    def test_valid_cpf(self):
        """Test valid CPF numbers."""
        assert validate_cpf("52998224725") is True
        assert validate_cpf("529.982.247-25") is True

    def test_invalid_cpf_wrong_digits(self):
        """Test CPF with wrong check digits."""
        assert validate_cpf("52998224726") is False

    def test_invalid_cpf_repeated_digits(self):
        """Test CPF with all repeated digits."""
        assert validate_cpf("11111111111") is False
        assert validate_cpf("00000000000") is False

    def test_invalid_cpf_wrong_length(self):
        """Test CPF with wrong length."""
        assert validate_cpf("5299822472") is False
        assert validate_cpf("529982247255") is False


class TestFormatting:
    """Tests for document formatting."""

    def test_format_cnpj(self):
        """Test CNPJ formatting."""
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_format_cnpj_already_formatted(self):
        """Test formatting already formatted CNPJ."""
        assert format_cnpj("11.222.333/0001-81") == "11.222.333/0001-81"

    def test_format_cnpj_wrong_length(self):
        """Test formatting CNPJ with wrong length returns as-is."""
        assert format_cnpj("1122233300018") == "1122233300018"

    def test_format_cpf(self):
        """Test CPF formatting."""
        assert format_cpf("52998224725") == "529.982.247-25"

    def test_format_cpf_already_formatted(self):
        """Test formatting already formatted CPF."""
        assert format_cpf("529.982.247-25") == "529.982.247-25"

    def test_format_cpf_wrong_length(self):
        """Test formatting CPF with wrong length returns as-is."""
        assert format_cpf("5299822472") == "5299822472"


class TestNormalizeDocument:
    """Tests for document normalization."""

    def test_normalize_cnpj(self):
        """Test normalizing CNPJ."""
        assert normalize_document("11.222.333/0001-81") == "11222333000181"

    def test_normalize_cpf(self):
        """Test normalizing CPF."""
        assert normalize_document("529.982.247-25") == "52998224725"

    def test_clean_document_alias(self):
        """Test that clean_document is an alias for normalize_document."""
        doc = "11.222.333/0001-81"

        assert clean_document(doc) == normalize_document(doc)

    def test_normalize_already_clean(self):
        """Test normalizing already clean document."""
        assert normalize_document("11222333000181") == "11222333000181"
