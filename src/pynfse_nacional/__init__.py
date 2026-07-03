"""
pynfse-nacional - Python library for Brazilian NFSe Nacional API.

This library provides tools for integrating with the NFSe Nacional (Padrao Nacional)
API for electronic service invoice issuance in Brazil.
"""

from .client import NFSeClient, RecoveryOutcome
from .constants import (
    AMBIENTE_HOMOLOGACAO,
    AMBIENTE_PRODUCAO,
    API_URLS,
    ENDPOINTS,
    Ambiente,
)
from .error_codes import ErrorCode
from .exceptions import (
    NFSeAPIError,
    NFSeCertificateError,
    NFSeError,
    NFSeValidationError,
    NFSeXMLError,
)
from .models import (
    DPS,
    ConvenioMunicipal,
    Endereco,
    EventResponse,
    NFSe,
    NFSeQueryResult,
    NFSeResponse,
    Prestador,
    Servico,
    SubstituicaoNFSe,
    Tomador,
    ValoresServico,
)
from .models_ibscbs import (
    GIBSCBS,
    IBSCBS,
    DestIBSCBS,
    GDifIBSCBS,
    GTribRegularIBSCBS,
    ImovelIBSCBS,
    RefNFSe,
    TribIBSCBS,
    ValoresIBSCBS,
)
from .types import Money15V2, Percent2V2, Percent3V2
from .utils import (
    clean_document,
    compress_and_encode,
    compress_encode,
    decode_and_decompress,
    decode_decompress,
    format_cnpj,
    format_cpf,
    normalize_document,
    validate_cnpj,
    validate_cpf,
)

# PDF generation (optional dependency)
try:
    from . import pdf_generator as _pdf_generator

    HeaderConfig = _pdf_generator.HeaderConfig
    NFSeData = _pdf_generator.NFSeData
    parse_nfse_xml = _pdf_generator.parse_nfse_xml
    generate_danfse_pdf = _pdf_generator.generate_danfse_pdf
    generate_danfse_from_xml = _pdf_generator.generate_danfse_from_xml
    generate_danfse_from_base64 = _pdf_generator.generate_danfse_from_base64

    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

__version__ = "0.9.0"

__all__ = [
    # Client
    "NFSeClient",
    "RecoveryOutcome",
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
    "ConvenioMunicipal",
    "SubstituicaoNFSe",
    "IBSCBS",
    "RefNFSe",
    "DestIBSCBS",
    "ImovelIBSCBS",
    "ValoresIBSCBS",
    "TribIBSCBS",
    "GIBSCBS",
    "GTribRegularIBSCBS",
    "GDifIBSCBS",
    "Percent2V2",
    "Money15V2",
    "Percent3V2",
    # Exceptions
    "NFSeError",
    "NFSeAPIError",
    "NFSeValidationError",
    "NFSeCertificateError",
    "NFSeXMLError",
    "ErrorCode",
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
    __all__.extend(
        [
            "HeaderConfig",
            "NFSeData",
            "parse_nfse_xml",
            "generate_danfse_pdf",
            "generate_danfse_from_xml",
            "generate_danfse_from_base64",
        ]
    )
