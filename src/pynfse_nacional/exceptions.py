class NFSeError(Exception):
    """Base exception for NFSe operations."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code


class NFSeAPIError(NFSeError):
    """Exception for API communication errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message, code)
        self.status_code = status_code
        self.response_body = response_body


class NFSeValidationError(NFSeError):
    """Exception for validation errors before API submission."""

    pass


class NFSeCertificateError(NFSeError):
    """Exception for certificate-related errors."""

    pass


class NFSeXMLError(NFSeError):
    """Exception for XML building or signing errors."""

    pass
