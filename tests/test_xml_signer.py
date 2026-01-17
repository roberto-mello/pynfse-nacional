"""Tests for XMLSigner."""

import base64
import gzip
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from backend.lib.pynfse_nacional.exceptions import NFSeCertificateError
from backend.lib.pynfse_nacional.xml_signer import (
    CRYPTOGRAPHY_AVAILABLE,
    SIGNXML_AVAILABLE,
    XMLSignerService,
)


SAMPLE_XML = """<?xml version='1.0' encoding='utf-8'?>
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infDPS Id="11222333000181NF0000000001">
    <tpAmb>2</tpAmb>
  </infDPS>
</DPS>"""


class TestXMLSignerServiceInit:
    """Tests for XMLSignerService initialization."""

    def test_stores_cert_path(self):
        """Init should store certificate path."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        assert signer.cert_path == "/path/to/cert.pfx"

    def test_stores_cert_password(self):
        """Init should store certificate password."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        assert signer.cert_password == "secret"

    def test_private_key_starts_none(self):
        """Private key should start as None (lazy loading)."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        assert signer._private_key is None

    def test_certificate_starts_none(self):
        """Certificate should start as None (lazy loading)."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        assert signer._certificate is None


class TestXMLSignerServiceCompressEncode:
    """Tests for compress_encode static method."""

    def test_compress_encode_returns_string(self):
        """compress_encode should return a string."""
        result = XMLSignerService.compress_encode(SAMPLE_XML)

        assert isinstance(result, str)

    def test_compress_encode_produces_base64(self):
        """compress_encode result should be valid base64."""
        result = XMLSignerService.compress_encode(SAMPLE_XML)

        decoded = base64.b64decode(result)

        assert decoded is not None

    def test_compress_encode_is_gzipped(self):
        """compress_encode result should decompress with gzip."""
        result = XMLSignerService.compress_encode(SAMPLE_XML)

        decoded = base64.b64decode(result)
        decompressed = gzip.decompress(decoded)

        assert decompressed.decode("utf-8") == SAMPLE_XML

    def test_compress_encode_reduces_size(self):
        """Compressed+encoded should be smaller than raw base64 for large content."""
        large_xml = SAMPLE_XML * 100

        compressed = XMLSignerService.compress_encode(large_xml)
        raw_b64 = base64.b64encode(large_xml.encode()).decode()

        assert len(compressed) < len(raw_b64)

    def test_compress_encode_handles_utf8(self):
        """compress_encode should handle UTF-8 characters."""
        xml_with_accents = "<nome>Jose da Silva</nome>"

        result = XMLSignerService.compress_encode(xml_with_accents)
        decoded = base64.b64decode(result)
        decompressed = gzip.decompress(decoded).decode("utf-8")

        assert decompressed == xml_with_accents


class TestXMLSignerServiceLoadCertificate:
    """Tests for _load_certificate method."""

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed"
    )
    def test_load_certificate_raises_on_missing_file(self):
        """_load_certificate should raise NFSeCertificateError for missing file."""
        signer = XMLSignerService(
            cert_path="/nonexistent/cert.pfx", cert_password="secret"
        )

        with pytest.raises(NFSeCertificateError) as exc_info:
            signer._load_certificate()

        assert "nao encontrado" in str(exc_info.value.message)

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed"
    )
    def test_load_certificate_raises_on_invalid_password(self):
        """_load_certificate should raise NFSeCertificateError for wrong password."""
        with tempfile.NamedTemporaryFile(suffix=".pfx", delete=False) as f:
            f.write(b"not a real certificate")
            temp_path = f.name

        try:
            signer = XMLSignerService(cert_path=temp_path, cert_password="wrong")

            with pytest.raises(NFSeCertificateError) as exc_info:
                signer._load_certificate()

            assert "Erro ao carregar" in str(exc_info.value.message)

        finally:
            os.unlink(temp_path)

    def test_load_certificate_raises_without_cryptography(self):
        """_load_certificate should raise if cryptography not available."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        with patch(
            "backend.lib.pynfse_nacional.xml_signer.CRYPTOGRAPHY_AVAILABLE", False
        ):
            with pytest.raises(NFSeCertificateError) as exc_info:
                signer._load_certificate()

            assert "cryptography" in str(exc_info.value.message).lower()

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE, reason="cryptography not installed"
    )
    def test_load_certificate_caches_result(self):
        """_load_certificate should only load once."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        mock_key = MagicMock()
        mock_cert = MagicMock()
        signer._private_key = mock_key
        signer._certificate = mock_cert

        signer._load_certificate()

        assert signer._private_key is mock_key


class TestXMLSignerServiceSign:
    """Tests for sign method."""

    def test_sign_raises_without_signxml(self):
        """sign should raise if signxml not available."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        with patch("backend.lib.pynfse_nacional.xml_signer.SIGNXML_AVAILABLE", False):
            with pytest.raises(NFSeCertificateError) as exc_info:
                signer.sign(SAMPLE_XML)

            assert "signxml" in str(exc_info.value.message).lower()

    @pytest.mark.skipif(
        not (CRYPTOGRAPHY_AVAILABLE and SIGNXML_AVAILABLE),
        reason="cryptography or signxml not installed",
    )
    def test_sign_calls_load_certificate(self):
        """sign should call _load_certificate."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        with patch.object(signer, "_load_certificate") as mock_load:
            mock_load.side_effect = NFSeCertificateError("Test")

            with pytest.raises(NFSeCertificateError):
                signer.sign(SAMPLE_XML)

            mock_load.assert_called_once()


class TestXMLSignerServiceSignAndEncode:
    """Tests for sign_and_encode method."""

    def test_sign_and_encode_calls_sign(self):
        """sign_and_encode should call sign method."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        signed_xml = "<signed>content</signed>"

        with patch.object(signer, "sign", return_value=signed_xml) as mock_sign:
            result = signer.sign_and_encode(SAMPLE_XML)

            mock_sign.assert_called_once_with(SAMPLE_XML)

    def test_sign_and_encode_compresses_result(self):
        """sign_and_encode should compress and encode the signed XML."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        signed_xml = "<signed>content</signed>"

        with patch.object(signer, "sign", return_value=signed_xml):
            result = signer.sign_and_encode(SAMPLE_XML)

            decoded = base64.b64decode(result)
            decompressed = gzip.decompress(decoded).decode("utf-8")

            assert decompressed == signed_xml

    def test_sign_and_encode_returns_string(self):
        """sign_and_encode should return a string."""
        signer = XMLSignerService(cert_path="/path/to/cert.pfx", cert_password="secret")

        with patch.object(signer, "sign", return_value="<signed/>"):
            result = signer.sign_and_encode(SAMPLE_XML)

            assert isinstance(result, str)


class TestXMLSignerServiceIntegration:
    """Integration tests for XMLSignerService with real certificate (if available)."""

    @pytest.fixture
    def test_cert_path(self):
        """Path to test certificate if available."""
        cert_path = os.environ.get("NFSE_TEST_CERT_PATH")

        if not cert_path or not os.path.exists(cert_path):
            pytest.skip("Test certificate not available (set NFSE_TEST_CERT_PATH)")

        return cert_path

    @pytest.fixture
    def test_cert_password(self):
        """Password for test certificate."""
        password = os.environ.get("NFSE_TEST_CERT_PASSWORD")

        if not password:
            pytest.skip("Test certificate password not set (set NFSE_TEST_CERT_PASSWORD)")

        return password

    @pytest.mark.skipif(
        not (CRYPTOGRAPHY_AVAILABLE and SIGNXML_AVAILABLE),
        reason="cryptography or signxml not installed",
    )
    def test_sign_with_real_certificate(self, test_cert_path, test_cert_password):
        """Test signing with real certificate."""
        signer = XMLSignerService(
            cert_path=test_cert_path, cert_password=test_cert_password
        )

        signed_xml = signer.sign(SAMPLE_XML)

        assert "<Signature" in signed_xml or "<ds:Signature" in signed_xml
        assert "SignatureValue" in signed_xml

    @pytest.mark.skipif(
        not (CRYPTOGRAPHY_AVAILABLE and SIGNXML_AVAILABLE),
        reason="cryptography or signxml not installed",
    )
    def test_sign_and_encode_with_real_certificate(
        self, test_cert_path, test_cert_password
    ):
        """Test sign_and_encode with real certificate."""
        signer = XMLSignerService(
            cert_path=test_cert_path, cert_password=test_cert_password
        )

        result = signer.sign_and_encode(SAMPLE_XML)

        decoded = base64.b64decode(result)
        decompressed = gzip.decompress(decoded).decode("utf-8")

        assert "<Signature" in decompressed or "<ds:Signature" in decompressed
