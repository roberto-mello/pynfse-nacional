"""Central catalog of numeric error codes.

Error codes are grouped by category so callers can branch on the leading
range:

- 100s: validation errors
- 200s: certificate/signing errors
- 300s: communication/transport errors
- 400s: response/parse errors
- 500s: compression/decoding errors
"""

from enum import IntEnum


class ErrorCode(IntEnum):
    """Stable numeric error codes exported by the library."""

    VALIDATION_INVALID_CHAVE_ACESSO = 101
    VALIDATION_INVALID_ID_DPS = 102
    VALIDATION_INVALID_NUMERO_DPS = 103

    CERTIFICATE_DEPENDENCY_MISSING = 201
    CERTIFICATE_FILE_NOT_FOUND = 202
    CERTIFICATE_LOAD_FAILED = 203
    CERTIFICATE_CLIENT_SETUP_FAILED = 204
    CERTIFICATE_SIGN_FAILED = 205

    COMMUNICATION_TIMEOUT = 301
    COMMUNICATION_ERROR = 302

    RESPONSE_INVALID_JSON = 401
    RESPONSE_INVALID_STRUCTURE = 402
    RESPONSE_INVALID_XML = 403

    PAYLOAD_TOO_LARGE = 501
    DECODE_ERROR = 502
