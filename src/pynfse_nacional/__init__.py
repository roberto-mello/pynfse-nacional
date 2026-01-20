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

# PDF generation (optional dependency)
try:
    from .pdf_generator import (
        HeaderConfig,
        NFSeData,
        parse_nfse_xml,
        generate_danfse_pdf,
        generate_danfse_from_xml,
        generate_danfse_from_base64,
    )

    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

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

# Add PDF exports if available
if _PDF_AVAILABLE:
    __all__.extend([
        "HeaderConfig",
        "NFSeData",
        "parse_nfse_xml",
        "generate_danfse_pdf",
        "generate_danfse_from_xml",
        "generate_danfse_from_base64",
    ])
