"""Tests for NFSe exception defaults."""

from pynfse_nacional import ErrorCode, NFSeAPIError, NFSeCertificateError


def test_nfse_api_error_uses_catalog_message_by_code():
    error = NFSeAPIError(code=ErrorCode.COMMUNICATION_ERROR)

    assert error.code == ErrorCode.COMMUNICATION_ERROR
    assert error.message == "Erro de comunicação."
    assert str(error) == "Erro de comunicação."


def test_nfse_certificate_error_uses_catalog_message_by_code():
    error = NFSeCertificateError(code=ErrorCode.CERTIFICATE_CLIENT_SETUP_FAILED)

    assert error.code == ErrorCode.CERTIFICATE_CLIENT_SETUP_FAILED
    assert error.message == "Erro ao configurar cliente HTTP."
