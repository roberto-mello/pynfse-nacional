"""Central catalog of pt_BR (Brazilian Portuguese) error messages for NFSe errors."""

from __future__ import annotations

from .error_codes import ErrorCode

_ERROR_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.VALIDATION_INVALID_CHAVE_ACESSO: (
        "chave_acesso deve conter exatamente 50 dígitos numéricos."
    ),
    ErrorCode.VALIDATION_INVALID_ID_DPS: (
        "id_dps deve seguir o padrão 'DPS' + 42 dígitos."
    ),
    ErrorCode.VALIDATION_INVALID_NUMERO_DPS: (
        "O número do DPS excede o limite permitido de 15 dígitos."
    ),
    ErrorCode.CERTIFICATE_DEPENDENCY_MISSING: (
        "Biblioteca cryptography não instalada."
    ),
    ErrorCode.CERTIFICATE_FILE_NOT_FOUND: (
        "Arquivo de certificado não encontrado."
    ),
    ErrorCode.CERTIFICATE_LOAD_FAILED: "Erro ao carregar certificado.",
    ErrorCode.CERTIFICATE_CLIENT_SETUP_FAILED: (
        "Erro ao configurar cliente HTTP."
    ),
    ErrorCode.CERTIFICATE_SIGN_FAILED: "Erro ao assinar XML.",
    ErrorCode.COMMUNICATION_TIMEOUT: "Tempo esgotado ao processar a requisição.",
    ErrorCode.COMMUNICATION_ERROR: "Erro de comunicação.",
    ErrorCode.RESPONSE_INVALID_JSON: "Resposta inválida: corpo não é JSON.",
    ErrorCode.RESPONSE_INVALID_STRUCTURE: (
        "Resposta inválida: JSON não é um objeto."
    ),
    ErrorCode.RESPONSE_INVALID_XML: "Resposta XML inválida.",
    ErrorCode.PAYLOAD_TOO_LARGE: (
        "Conteúdo NFSe excede o limite permitido de descompressão."
    ),
    ErrorCode.DECODE_ERROR: "Falha ao decodificar conteúdo NFSe comprimido.",
}


def get_error_message(
    code: ErrorCode | int | None,
    default: str = "Erro desconhecido.",
) -> str:
    """Return the canonical PT-BR message for a numeric error code."""

    if code is None:
        return default

    try:
        return _ERROR_MESSAGES[ErrorCode(code)]
    except Exception:
        return default
