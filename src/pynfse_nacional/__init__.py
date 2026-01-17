"""
pynfse-nacional - Python library for Brazilian NFSe Nacional API.

This library provides tools for integrating with the NFSe Nacional (Padrao Nacional)
API for electronic service invoice issuance in Brazil.
"""

from .client import NFSeClient
from .models import (
    DPS,
    NFSe,
    Prestador,
    Tomador,
    Servico,
    Endereco,
    ValoresServico,
    NFSeResponse,
    EventResponse,
    NFSeQueryResult,
)
from .exceptions import (
    NFSeError,
    NFSeAPIError,
    NFSeValidationError,
    NFSeCertificateError,
    NFSeXMLError,
)
from .constants import (
    Ambiente,
    AMBIENTE_HOMOLOGACAO,
    AMBIENTE_PRODUCAO,
    API_URLS,
    ENDPOINTS,
)
from .utils import (
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

__version__ = "0.1.0"

__all__ = [
    # Client
    "NFSeClient",
    # Models
    "DPS",
    "NFSe",
    "Prestador",
    "Tomador",
    "Servico",
    "Endereco",
    "ValoresServico",
    "NFSeResponse",
    "EventResponse",
    "NFSeQueryResult",
    # Exceptions
    "NFSeError",
    "NFSeAPIError",
    "NFSeValidationError",
    "NFSeCertificateError",
    "NFSeXMLError",
    # Constants
    "Ambiente",
    "AMBIENTE_HOMOLOGACAO",
    "AMBIENTE_PRODUCAO",
    "API_URLS",
    "ENDPOINTS",
    # Utils
    "compress_encode",
    "compress_and_encode",
    "decode_decompress",
    "decode_and_decompress",
    "validate_cnpj",
    "validate_cpf",
    "format_cnpj",
    "format_cpf",
    "normalize_document",
    "clean_document",
]
