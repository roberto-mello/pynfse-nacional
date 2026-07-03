"""Central catalog of numeric error codes.

Error codes are grouped by category so callers can branch on the leading
range:

- 1000s: validation errors
- 2000s: certificate/signing errors
- 3000s: communication/transport errors
- 4000s: response/parse errors
- 5000s: compression/decoding errors
"""

from enum import IntEnum


class ErrorCode(IntEnum):
    """Stable numeric error codes exported by the library."""

    VALIDATION_INVALID_CHAVE_ACESSO = 1001
    VALIDATION_INVALID_ID_DPS = 1002
    VALIDATION_INVALID_NUMERO_DPS = 1003

    CERTIFICATE_DEPENDENCY_MISSING = 2001
    CERTIFICATE_FILE_NOT_FOUND = 2002
    CERTIFICATE_LOAD_FAILED = 2003
    CERTIFICATE_CLIENT_SETUP_FAILED = 2004
    CERTIFICATE_SIGN_FAILED = 2005

    COMMUNICATION_TIMEOUT = 3001
    COMMUNICATION_ERROR = 3002

    RESPONSE_INVALID_JSON = 4001
    RESPONSE_INVALID_STRUCTURE = 4002
    RESPONSE_INVALID_XML = 4003

    PAYLOAD_TOO_LARGE = 5001
    DECODE_ERROR = 5002
