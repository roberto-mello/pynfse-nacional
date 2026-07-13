import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from json import loads
from pathlib import Path
from types import MappingProxyType
from typing import Generator, Literal, Mapping, Optional
from xml.etree.ElementTree import ParseError as XMLParseError

import httpx

from .constants import API_URLS, ENDPOINTS, PARAMETRIZACAO_URLS, Ambiente
from .error_codes import ErrorCode
from .error_messages import get_error_message
from .exceptions import NFSeAPIError, NFSeCertificateError, NFSeError
from .models import (
    DPS,
    ConvenioMunicipal,
    EventResponse,
    NFSeQueryResult,
    NFSeResponse,
    SubstituicaoNFSe,
)
from .response_parsers import (
    extract_nfse_number,
    parse_ibscbs,
    parse_nfse_root,
)
from .utils import (
    CHAVE_ACESSO_RE,
    _redacted_repr,
    compress_encode,
    decode_decompress,
)
from .xml_builder import XMLBuilder
from .xml_signer import XMLSignerService

_CHAVE_RE = CHAVE_ACESSO_RE
_ID_DPS_RE = re.compile(r"^DPS\d{42}$")
_RAW_RESPONSE_BODY_LIMIT = 1024 * 1024
_SAFE_RESPONSE_HEADERS = frozenset(
    {
        "content-encoding",
        "content-language",
        "content-length",
        "content-type",
        "date",
        "etag",
        "last-modified",
        "retry-after",
        "server",
        "x-sefin",
    }
)


@dataclass(frozen=True)
class RecoveryOutcome:
    """Outcome of attempting NFSe recovery by DPS identifier.

    Returned by :meth:`NFSeClient.recover_nfse_by_dps` when a DPS submission
    may have already been processed by SEFIN but the caller did not persist
    the ``chave_acesso`` (e.g. duplicate ``e0014`` response, or a transport
    failure after SEFIN accepted the DPS).

    - ``status="success"``: the NFSe exists remotely; ``result`` holds the
      full invoice data and the caller should persist it.
    - ``status="processing"``: the DPS was received but the NFSe has not been
      emitted yet (SEFIN returned 202 / 404 / 409 on the lookup). The caller
      should keep the issuance retryable rather than marking it failed.
    - ``status="error"``: the lookup itself failed (transport, API, or
      certificate error); ``error`` holds the :class:`NFSeError`. The caller
      should surface the original submit error.
    """

    status: Literal["success", "processing", "error"]
    result: Optional[NFSeQueryResult] = None
    error: Optional[NFSeError] = None

    def __post_init__(self) -> None:
        if self.status == "success":
            if self.result is None or self.error is not None:
                raise ValueError(
                    "RecoveryOutcome com status='success' requer result e nenhum error."
                )
        elif self.status == "processing":
            if self.result is not None or self.error is not None:
                raise ValueError(
                    "RecoveryOutcome com status='processing' requer payload vazio."
                )
        elif self.status == "error":
            if self.error is None or self.result is not None:
                raise ValueError(
                    "RecoveryOutcome com status='error' requer error e nenhum result."
                )

    @property
    def recovered(self) -> bool:
        """True when recovery succeeded and ``result`` is populated."""
        return self.status == "success"


@dataclass(frozen=True)
class RawNFSeResponse:
    """Detached HTTP response captured by an explicit diagnostic operation.

    The response body is retained as bytes so callers can inspect the exact
    SEFIN payload after the mTLS client has been closed. NFSe responses may
    contain taxpayer and service data; callers should redact or bound
    ``body``/``text`` before logging it.
    """

    status_code: int
    headers: Mapping[str, str]
    body: bytes
    method: str
    url: str
    content_length: int
    encoding: Optional[str] = None
    truncated: bool = False

    @property
    def text(self) -> str:
        """Decode the detached body for diagnostics using the response encoding."""
        return self.body.decode(self.encoding or "utf-8", errors="replace")

    def __repr__(self) -> str:
        """Show safe metadata without including response data or identifiers."""
        return (
            "RawNFSeResponse("
            f"status_code={self.status_code!r}, "
            f"method={self.method!r}, "
            f"content_length={self.content_length!r}, "
            f"truncated={self.truncated!r})"
        )


@dataclass(frozen=True)
class RawNFSeRecoveryResponse:
    """Detached responses captured by the DPS recovery diagnostic probe.

    ``nfse_response`` is ``None`` when the DPS lookup did not return a valid
    access key, including non-success and malformed successful responses.
    """

    dps_response: RawNFSeResponse
    nfse_response: Optional[RawNFSeResponse] = None

    def __repr__(self) -> str:
        """Show safe status metadata without including identifiers or bodies."""
        nfse_status = (
            self.nfse_response.status_code if self.nfse_response is not None else None
        )
        return (
            "RawNFSeRecoveryResponse("
            f"dps_status_code={self.dps_response.status_code!r}, "
            f"nfse_status_code={nfse_status!r})"
        )


def _redact_diagnostic_url(url: str) -> str:
    """Remove invoice and DPS identifiers from diagnostic URL metadata."""
    url = re.sub(r"\d{50}", "[REDACTED-ACCESS-KEY]", url)
    return re.sub(r"DPS\d{42}", "DPS[REDACTED]", url)


def _detach_response(
    response: httpx.Response,
    *,
    method: str,
    url: str,
    body: bytes,
    content_length: int,
    truncated: bool,
) -> RawNFSeResponse:
    """Detach bounded response data before the mTLS client is closed."""

    headers = getattr(response, "headers", {})
    header_items = headers.items() if hasattr(headers, "items") else ()
    safe_headers = {
        str(key): str(value)[:1024]
        for key, value in header_items
        if str(key).lower() in _SAFE_RESPONSE_HEADERS
    }

    return RawNFSeResponse(
        status_code=response.status_code,
        headers=MappingProxyType(httpx.Headers(safe_headers)),
        body=body[:_RAW_RESPONSE_BODY_LIMIT],
        method=method,
        url=_redact_diagnostic_url(url),
        content_length=content_length,
        encoding=getattr(response, "encoding", None),
        truncated=truncated,
    )


def _extract_chave_acesso_from_raw_response(
    response: RawNFSeResponse,
) -> Optional[str]:
    """Extract a valid access key from a detached DPS response."""
    try:
        data = loads(response.text)
    except Exception:
        return None

    if isinstance(data, dict):
        for key in ("chaveAcesso", "chave_acesso", "chNFSe", "chave"):
            value = data.get(key)
            if isinstance(value, str) and _CHAVE_RE.fullmatch(value):
                return value

    if isinstance(data, str) and _CHAVE_RE.fullmatch(data.strip()):
        return data.strip()

    return None


def _validate_chave_acesso(chave: str) -> None:
    """Valida que chave_acesso contém exatamente 50 dígitos numéricos."""

    if not _CHAVE_RE.match(chave):
        raise ValueError(
            "chave_acesso deve conter exatamente 50 dígitos numéricos; "
            f"{_redacted_repr('valor', chave)}."
        )


def _validate_id_dps(id_dps: str) -> None:
    """Valida que id_dps segue o padrão DPS + 42 dígitos."""

    if not _ID_DPS_RE.match(id_dps):
        raise ValueError(
            "id_dps deve seguir o padrão 'DPS' + 42 dígitos; "
            f"{_redacted_repr('valor', id_dps)}."
        )


def _extract_nfse_number_from_xml(xml_content: str) -> Optional[str]:
    """Extract nNFSe from NFSe XML content.

    Args:
        xml_content: The NFSe XML as a string.

    Returns:
        The NFSe number as string, or None if not found.
    """
    try:
        root = parse_nfse_root(xml_content)
        return extract_nfse_number(root)
    except XMLParseError:
        pass

    return None


def _extract_chave_acesso_from_dps_response(
    response: httpx.Response,
) -> Optional[str]:
    """Extract the NFSe access key from a DPS lookup response."""

    try:
        data = response.json()
    except Exception:
        text = response.text.strip()
        return text if _CHAVE_RE.fullmatch(text) else None

    if isinstance(data, dict):
        for key in ("chaveAcesso", "chave_acesso", "chNFSe", "chave"):
            value = data.get(key)
            if isinstance(value, str) and _CHAVE_RE.fullmatch(value):
                return value

    if isinstance(data, str) and _CHAVE_RE.fullmatch(data.strip()):
        return data.strip()

    return None


def _error_payload(response: httpx.Response) -> dict[str, object]:
    """Return a dict payload for error responses, or empty dict on mismatch."""

    try:
        data = response.json()
    except Exception:
        return {}

    if isinstance(data, dict):
        return data

    return {}


def _format_dps_error_response(
    data: object,
    response: httpx.Response,
    *,
    default_message: str,
) -> tuple[str, str]:
    """Normalize SEFIN DPS error payloads from object or list shapes."""

    if isinstance(data, dict):
        erros = data.get("erros")
        if not isinstance(erros, list):
            erros = data.get("erro")
        if isinstance(erros, list) and erros:
            return _format_dps_error_entries(
                erros,
                response.status_code,
                default_message=default_message,
            )

        return (
            str(data.get("codigo") or response.status_code),
            str(data.get("mensagem") or default_message),
        )

    if isinstance(data, list) and data:
        return _format_dps_error_entries(
            data,
            response.status_code,
            default_message=default_message,
        )

    return str(response.status_code), default_message


def _format_dps_error_entries(
    entries: list[object],
    fallback_code: int,
    *,
    default_message: str,
) -> tuple[str, str]:
    """Render a SEFIN error list into the public NFSe error shape."""

    if not entries:
        return str(fallback_code), default_message

    parts: list[str] = []
    first_code: object | None = None

    def _entry_value(entry: dict[str, object], *names: str) -> object | None:
        wanted = {name.lower() for name in names}

        for key, value in entry.items():
            if str(key).lower() in wanted and value not in (None, ""):
                return value

        return None

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        if first_code is None:
            first_code = _entry_value(entry, "codigo")

        descricao = (
            str(_entry_value(entry, "descricao", "mensagem") or "")
            .strip()[:255]
        )
        complemento = str(_entry_value(entry, "complemento") or "").strip()[:255]

        if descricao or complemento:
            parts.append(f"{descricao}: {complemento}" if complemento else descricao)

    return (
        str(first_code or fallback_code),
        "; ".join(parts) or default_message,
    )


def _require_json_object(
    response: httpx.Response, *, context: str
) -> dict[str, object]:
    """Parse a JSON object response or raise a structured NFSeAPIError."""

    try:
        data = response.json()
    except Exception as e:
        raise NFSeAPIError(
            f"Resposta inválida {context}: corpo não é JSON.",
            code=ErrorCode.RESPONSE_INVALID_JSON,
            status_code=response.status_code,
        ) from e

    if not isinstance(data, dict):
        raise NFSeAPIError(
            f"Resposta inválida {context}: JSON não é um objeto.",
            code=ErrorCode.RESPONSE_INVALID_STRUCTURE,
            status_code=response.status_code,
        )

    return data


try:
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        pkcs12,
    )

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class NFSeClient:
    """Client for NFSe Nacional API with mTLS support.

    Uses PKCS12 (.pfx/.p12) certificates for mutual TLS authentication
    with the NFSe Nacional SEFIN API.
    """

    def __init__(
        self,
        cert_path: str,
        cert_password: str,
        ambiente: str = "homologacao",
        timeout: float = 30.0,
    ):
        """Initialize NFSe client.

        Args:
            cert_path: Path to PKCS12 certificate file (.pfx/.p12)
            cert_password: Certificate password
            ambiente: API environment ('homologacao' or 'producao')
            timeout: HTTP request timeout in seconds
        """
        self.cert_path = cert_path
        self.cert_password = cert_password
        self.ambiente = Ambiente(ambiente)
        self.timeout = timeout
        self.base_url = API_URLS[self.ambiente]
        self.parametrizacao_url = PARAMETRIZACAO_URLS[self.ambiente]
        self._xml_builder = XMLBuilder(ambiente=self.ambiente)
        self._xml_signer = XMLSignerService(cert_path, cert_password)
        self._private_key = None
        self._certificate = None

    def _load_pkcs12(self) -> tuple:
        """Load and cache PKCS12 certificate data.

        Returns:
            Tuple of (private_key, certificate)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_DEPENDENCY_MISSING),
                code=ErrorCode.CERTIFICATE_DEPENDENCY_MISSING,
            )

        if self._private_key is not None:
            return self._private_key, self._certificate

        try:
            cert_path = Path(self.cert_path)

            if not cert_path.exists():
                raise NFSeCertificateError(
                    f"Arquivo de certificado não encontrado: {self.cert_path}",
                    code=ErrorCode.CERTIFICATE_FILE_NOT_FOUND,
                )

            with open(cert_path, "rb") as f:
                pkcs12_data = f.read()

            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                pkcs12_data, self.cert_password.encode()
            )

            if self._private_key is None:
                raise NFSeCertificateError(
                    "Chave privada não encontrada no certificado.",
                    code=ErrorCode.CERTIFICATE_LOAD_FAILED,
                )

            if self._certificate is None:
                raise NFSeCertificateError(
                    "Certificado não encontrado no arquivo PKCS12.",
                    code=ErrorCode.CERTIFICATE_LOAD_FAILED,
                )

            return self._private_key, self._certificate

        except NFSeCertificateError:
            raise

        except Exception as e:
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_LOAD_FAILED),
                code=ErrorCode.CERTIFICATE_LOAD_FAILED,
            ) from e

    @contextmanager
    def _get_client(self) -> Generator[httpx.Client, None, None]:
        """Create HTTP client with mTLS configuration.

        Creates temporary PEM files from PKCS12 certificate for httpx mTLS.
        Files are securely deleted after use.
        """
        private_key, certificate = self._load_pkcs12()

        key_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption(),
        )

        cert_pem = certificate.public_bytes(Encoding.PEM)

        cert_file_path = None
        key_file_path = None

        client = None

        def _cleanup() -> None:
            if client is not None:
                client.close()
            if cert_file_path:
                Path(cert_file_path).unlink(missing_ok=True)
            if key_file_path:
                Path(key_file_path).unlink(missing_ok=True)

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".pem", delete=False
            ) as cert_file:
                cert_file_path = cert_file.name
                cert_file.write(cert_pem)

            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".pem", delete=False
            ) as key_file:
                key_file_path = key_file.name
                key_file.write(key_pem)

            client = httpx.Client(
                cert=(cert_file_path, key_file_path),
                verify=True,
                timeout=self.timeout,
            )
        except NFSeCertificateError:
            _cleanup()
            raise

        except Exception as e:
            _cleanup()
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_CLIENT_SETUP_FAILED),
                code=ErrorCode.CERTIFICATE_CLIENT_SETUP_FAILED,
            ) from e

        try:
            yield client
        finally:
            _cleanup()

    def submit_dps(self, dps: DPS) -> NFSeResponse:
        """Submit DPS and receive NFSe."""
        url, payload = self._build_submit_request(dps)

        try:
            with self._get_client() as client:
                response = self._post_submit_dps(client, url, payload)
                return self._parse_dps_response(response)

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao comunicar com a SEFIN.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com a SEFIN.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def _build_submit_request(self, dps: DPS) -> tuple[str, dict[str, str]]:
        """Build the canonical URL and payload used by submit operations."""
        if not isinstance(dps, DPS):
            raise TypeError("dps deve ser uma instância de DPS.")

        xml = self._xml_builder.build_dps(dps)
        signed_xml = self._xml_signer.sign(xml)
        encoded_content = compress_encode(signed_xml)

        return (
            f"{self.base_url}{ENDPOINTS['submit_dps']}",
            {"dpsXmlGZipB64": encoded_content},
        )

    @staticmethod
    def _post_submit_dps(
        client: httpx.Client,
        url: str,
        payload: dict[str, str],
    ) -> httpx.Response:
        """Send the canonical DPS submission request."""
        return client.post(url, json=payload)

    @contextmanager
    def _raw_request_client(
        self, timeout_message: str
    ) -> Generator[httpx.Client, None, None]:
        """Open a diagnostic client and normalize transport failures."""
        try:
            with self._get_client() as client:
                yield client

        except httpx.TimeoutException:
            raise NFSeAPIError(
                timeout_message,
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com a SEFIN.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    @staticmethod
    def _stream_raw_response(
        client: httpx.Client,
        method: str,
        url: str,
        **kwargs: object,
    ) -> RawNFSeResponse:
        """Stream a diagnostic response while retaining only a bounded body."""
        with client.stream(method, url, **kwargs) as response:
            retained = bytearray()
            content_length = 0

            for chunk in response.iter_bytes():
                content_length += len(chunk)
                remaining = _RAW_RESPONSE_BODY_LIMIT - len(retained)
                if remaining > 0:
                    retained.extend(chunk[:remaining])

            return _detach_response(
                response,
                method=method,
                url=url,
                body=bytes(retained),
                content_length=content_length,
                truncated=content_length > _RAW_RESPONSE_BODY_LIMIT,
            )

    def submit_dps_raw_response(self, dps: DPS) -> RawNFSeResponse:
        """Submit a DPS and return the detached raw SEFIN response.

        This is an explicit diagnostic operation for inspecting the exact
        response returned by the submit endpoint. It follows the same build,
        sign, compression, payload, mTLS, and timeout path as
        :meth:`submit_dps`, but does not parse or normalize the response.
        Response bodies can contain taxpayer and service data; redact or bound
        them before logging.
        """
        url, payload = self._build_submit_request(dps)

        with self._raw_request_client(
            "Tempo esgotado ao comunicar com a SEFIN."
        ) as client:
            return self._stream_raw_response(client, "POST", url, json=payload)

    def _parse_dps_response(self, response: httpx.Response) -> NFSeResponse:
        """Parse API response for DPS submission."""
        try:
            data = response.json()
        except Exception:
            return NFSeResponse(
                success=False,
                error_code=str(response.status_code),
                error_message=get_error_message(ErrorCode.RESPONSE_INVALID_JSON),
            )

        # Check for chaveAcesso to determine success
        # (API may return success on non-200 status)
        if isinstance(data, dict) and data.get("chaveAcesso"):
            nfse_xml = None
            nfse_xml_b64 = data.get("nfseXmlGZipB64")

            if nfse_xml_b64:
                try:
                    nfse_xml = decode_decompress(nfse_xml_b64)
                except Exception:
                    pass

            chave_acesso = data.get("chaveAcesso")
            nfse_number = None

            # Priority 1: Extract nNFSe from the XML (most reliable source)
            if nfse_xml:
                nfse_number = _extract_nfse_number_from_xml(nfse_xml)

            # Priority 2: Get nNFSe from JSON response
            if not nfse_number:
                nfse_number = data.get("nNFSe")

            return NFSeResponse(
                success=True,
                chave_acesso=chave_acesso,
                nfse_number=nfse_number,
                nfse_xml_gzip_b64=nfse_xml_b64,
                xml_nfse=nfse_xml,
            )

        # Error response
        error_code, error_message = _format_dps_error_response(
            data,
            response,
            default_message=get_error_message(ErrorCode.RESPONSE_INVALID_STRUCTURE),
        )
        return NFSeResponse(
            success=False,
            error_code=error_code,
            error_message=error_message,
        )

    def _query_nfse_with_client(
        self, client: httpx.Client, chave_acesso: str
    ) -> NFSeQueryResult:
        """Query NFSe by access key using an existing HTTP client."""

        response = self._get_nfse_response(client, chave_acesso)

        if response.status_code != 200:
            error_data = _error_payload(response)

            raise NFSeAPIError(
                error_data.get("mensagem") or "Erro ao consultar NFSe.",
                code=error_data.get("codigo"),
                status_code=response.status_code,
            )

        data = _require_json_object(response, context="ao consultar NFSe")

        xml_nfse = None
        xml_root = None

        if data.get("nfse"):
            try:
                xml_nfse = decode_decompress(data["nfse"])
            except Exception:
                xml_nfse = data.get("nfse")

        if xml_nfse:
            try:
                xml_root = parse_nfse_root(xml_nfse)
            except XMLParseError:
                xml_root = None

        chave_retorno = data.get("chaveAcesso")
        if not chave_retorno:
            raise NFSeAPIError(
                "Resposta inválida ao consultar NFSe: chaveAcesso ausente",
                status_code=response.status_code,
            )

        data_emissao = data.get("dhEmi")
        if not data_emissao:
            raise NFSeAPIError(
                "Resposta inválida ao consultar NFSe: dhEmi ausente",
                status_code=response.status_code,
            )

        nfse_number = extract_nfse_number(xml_root) if xml_root is not None else None
        if nfse_number is None:
            nfse_number = data.get("nNFSe")
        if nfse_number is None:
            raise NFSeAPIError(
                "Resposta inválida ao consultar NFSe: nNFSe ausente",
                status_code=response.status_code,
            )

        return NFSeQueryResult(
            chave_acesso=chave_retorno,
            nfse_number=nfse_number,
            status=data.get("situacao", "emitida"),
            data_emissao=data_emissao,
            valor_servicos=data.get("vServPrest", 0),
            prestador_cnpj=data.get("CNPJPrest", ""),
            tomador_documento=data.get("CPFToma") or data.get("CNPJToma"),
            xml_nfse=xml_nfse,
            ibscbs=(
                parse_ibscbs(root=xml_root) if xml_root is not None else None
            ),
        )

    def _get_nfse_response(
        self, client: httpx.Client, chave_acesso: str
    ) -> httpx.Response:
        """Issue the canonical NFSe-by-access-key request."""
        return client.get(self._nfse_url(chave_acesso))

    def _nfse_url(self, chave_acesso: str) -> str:
        """Build the canonical NFSe-by-access-key URL."""
        return f"{self.base_url}{ENDPOINTS['query_nfse'].format(chave=chave_acesso)}"

    def query_nfse_raw_response(self, chave_acesso: str) -> RawNFSeResponse:
        """Query by access key and return the detached raw SEFIN response.

        This explicit diagnostic operation preserves the response status,
        headers, and body without applying the normal NFSe parsing contract.
        The access key is validated with the same rule as :meth:`query_nfse`.
        """
        _validate_chave_acesso(chave_acesso)
        url = self._nfse_url(chave_acesso)

        with self._raw_request_client("Tempo esgotado ao consultar NFSe.") as client:
            return self._stream_raw_response(client, "GET", url)

    def query_nfse(self, chave_acesso: str) -> NFSeQueryResult:
        """Query NFSe by access key."""
        _validate_chave_acesso(chave_acesso)

        try:
            with self._get_client() as client:
                return self._query_nfse_with_client(client, chave_acesso)

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao consultar NFSe.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com a SEFIN.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def query_nfse_by_dps(self, id_dps: str) -> NFSeQueryResult:
        """Recover an NFSe by DPS identifier, then fetch the full invoice."""

        _validate_id_dps(id_dps)

        try:
            with self._get_client() as client:
                response = self._get_dps_response(client, id_dps)

                if response.status_code != 200:
                    error_data = _error_payload(response)

                    raise NFSeAPIError(
                        error_data.get("mensagem") or "Erro ao consultar DPS.",
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                chave_acesso = _extract_chave_acesso_from_dps_response(response)
                if not chave_acesso:
                    raise NFSeAPIError(
                        "Resposta da consulta por DPS sem chave de acesso",
                        code=ErrorCode.RESPONSE_INVALID_STRUCTURE,
                        status_code=response.status_code,
                    )

                return self._query_nfse_with_client(client, chave_acesso)

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao consultar DPS.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com a SEFIN.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def _get_dps_response(
        self, client: httpx.Client, id_dps: str
    ) -> httpx.Response:
        """Issue the canonical DPS lookup request."""
        return client.get(self._dps_url(id_dps))

    def _dps_url(self, id_dps: str) -> str:
        """Build the canonical DPS lookup URL."""
        return f"{self.base_url}{ENDPOINTS['query_nfse_by_dps'].format(id=id_dps)}"

    def query_nfse_by_dps_raw_response(self, id_dps: str) -> RawNFSeResponse:
        """Query by DPS identifier and return the detached raw response.

        This captures only the DPS lookup request. Use
        :meth:`recover_nfse_by_dps_raw_response` when both the DPS lookup and
        the subsequent access-key lookup are needed.
        """
        _validate_id_dps(id_dps)
        url = self._dps_url(id_dps)

        with self._raw_request_client("Tempo esgotado ao consultar DPS.") as client:
            return self._stream_raw_response(client, "GET", url)

    def recover_nfse_by_dps_raw_response(
        self, id_dps: str
    ) -> RawNFSeRecoveryResponse:
        """Capture the raw DPS and access-key recovery responses.

        The operation performs ``GET /dps/{id}`` and, when that response
        contains a valid ``chaveAcesso``, follows it with the same
        ``GET /nfse/{chaveAcesso}`` request used by :meth:`query_nfse_by_dps`.
        Non-success or malformed DPS responses are returned unchanged and do
        not raise a domain parsing error. Transport and certificate failures
        still use the client's normal :class:`NFSeAPIError` contract.
        """
        _validate_id_dps(id_dps)
        dps_url = self._dps_url(id_dps)

        with self._raw_request_client("Tempo esgotado ao consultar DPS.") as client:
            detached_dps = self._stream_raw_response(client, "GET", dps_url)

            if detached_dps.status_code != 200:
                return RawNFSeRecoveryResponse(dps_response=detached_dps)

            chave_acesso = _extract_chave_acesso_from_raw_response(detached_dps)
            if not chave_acesso:
                return RawNFSeRecoveryResponse(dps_response=detached_dps)

            nfse_url = self._nfse_url(chave_acesso)
            detached_nfse = self._stream_raw_response(client, "GET", nfse_url)
            return RawNFSeRecoveryResponse(
                dps_response=detached_dps,
                nfse_response=detached_nfse,
            )

    def has_nfse_by_dps(self, id_dps: str) -> bool:
        """Check whether an NFSe exists for a DPS identifier."""

        _validate_id_dps(id_dps)
        url = f"{self.base_url}{ENDPOINTS['query_nfse_by_dps'].format(id=id_dps)}"

        try:
            with self._get_client() as client:
                response = client.head(url)

                if response.status_code in (200, 204):
                    return True

                if response.status_code in (202, 404, 409):
                    return False

                error_data = _error_payload(response)

                raise NFSeAPIError(
                    error_data.get("mensagem") or "Erro ao consultar DPS.",
                    code=error_data.get("codigo"),
                    status_code=response.status_code,
                )

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao consultar DPS.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com a SEFIN.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def recover_nfse_by_dps(self, id_dps: str) -> RecoveryOutcome:
        """Recover an NFSe by DPS identifier when submit may have already succeeded.

        High-level helper that combines :meth:`has_nfse_by_dps` and
        :meth:`query_nfse_by_dps` for the duplicate / lost-``chave_acesso``
        recovery path. Use after ``submit_dps`` failed or raised, when SEFIN
        may still have processed the DPS. Swallows NFSeError failures from the
        lookup path and wraps XML parse failures into ``status="error"``.

        See :class:`RecoveryOutcome` for the possible statuses.
        """
        try:
            if not self.has_nfse_by_dps(id_dps):
                return RecoveryOutcome(status="processing")

            return RecoveryOutcome(
                status="success",
                result=self.query_nfse_by_dps(id_dps),
            )
        except XMLParseError as e:
            error = NFSeAPIError(
                "Resposta XML inválida ao consultar NFSe.",
                code=ErrorCode.RESPONSE_INVALID_XML,
            )
            error.__cause__ = e
            return RecoveryOutcome(
                status="error",
                error=error,
            )
        except NFSeError as e:
            return RecoveryOutcome(status="error", error=e)

    def download_danfse(self, chave_acesso: str) -> bytes:
        """Download DANFSe PDF from official API.

        Note: The official DANFSE API at adn.nfse.gov.br may not be available
        or may return errors (501, 502, 429). As an alternative, use the local
        PDF generator helper from ``pynfse_nacional.pdf_generator`` when the
        submit response includes ``nfse_xml_gzip_b64``. That path requires the
        optional ``pynfse-nacional[pdf]`` extra.
        """
        _validate_chave_acesso(chave_acesso)

        # DANFSE API is on a different domain than SEFIN
        danfse_base_url = self.base_url.replace("sefin.", "adn.").replace(
            "/SefinNacional", ""
        )
        url = (
            f"{danfse_base_url}"
            f"{ENDPOINTS['download_danfse'].format(chave=chave_acesso)}"
        )

        try:
            with self._get_client() as client:
                response = client.get(url)

                if response.status_code != 200:
                    error_data = _error_payload(response)

                    msg = error_data.get("mensagem") or (
                        f"Erro ao baixar DANFSe: HTTP {response.status_code}"
                    )
                    raise NFSeAPIError(
                        msg,
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                return response.content

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao baixar DANFSe.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação com o convênio municipal.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def substitute_nfse(
        self,
        chave_acesso_original: str,
        new_dps: DPS,
        motivo: str,
        codigo_motivo: int = 99,
    ) -> NFSeResponse:
        """Substitute an existing NFSe with a new one.

        This operation cancels the original NFSe and creates a new one
        with the updated information. The new NFSe will be linked to the
        original as a substitution.

        Args:
            chave_acesso_original: Access key of the NFSe to be substituted (50 digits)
            new_dps: New DPS with updated information (do not set substituicao field)
            motivo: Reason for substitution (15-255 characters)
            codigo_motivo: Reason code (1-99, default 99 for "outros")

        Returns:
            NFSeResponse with the new NFSe data

        Raises:
            NFSeAPIError: If the API returns an error
            ValueError: If the original NFSe cannot be substituted

        Note:
            - Substitution must be done within 35 days of the original emission
            - Cannot substitute NFSe where tomador was not identified
            - Cannot change the tomador to a different person/company
        """
        substituicao = SubstituicaoNFSe(
            chave_nfse_substituida=chave_acesso_original,
            codigo_motivo=codigo_motivo,
            motivo=motivo,
        )

        dps_with_subst = new_dps.model_copy(update={"substituicao": substituicao})

        return self.submit_dps(dps_with_subst)

    def cancel_nfse(
        self,
        chave_acesso: str,
        reason: str,
        codigo_motivo: int = 1,
        cnpj_prestador: str = "",
    ) -> EventResponse:
        """Cancel NFSe by access key.

        Args:
            chave_acesso: 50-digit NFSe access key.
            reason: Free-text cancellation reason (max 255 chars).
            codigo_motivo: Cancellation reason code (1=erro na emissão,
                2=serviço não prestado, 4=duplicidade). Default 1.
            cnpj_prestador: CNPJ of the service provider (14 digits, digits only).
                Required by SEFIN to identify the cancellation author. Without
                this, SEFIN returns 404 on the /eventos endpoint.

        Returns:
            EventResponse with protocolo on success.
        """
        _validate_chave_acesso(chave_acesso)
        url = f"{self.base_url}{ENDPOINTS['events'].format(chave=chave_acesso)}"

        xml = self._xml_builder.build_cancel_event(
            chave_acesso, reason, codigo_motivo, cnpj_prestador
        )
        signed_xml = self._xml_signer.sign(xml)
        encoded_content = compress_encode(signed_xml)

        payload = {"pedidoRegistroEventoXmlGZipB64": encoded_content}

        try:
            with self._get_client() as client:
                response = client.post(url, json=payload)
                return self._parse_event_response(response)

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao cancelar NFSe.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação ao cancelar NFSe.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e

    def _parse_event_response(self, response: httpx.Response) -> EventResponse:
        """Parse API response for event registration.

        SEFIN returns either:
          - 200: {retEvento: {cStat: 144, xMotivo: "...", idEvento: "..."}, ...}
          - 200: {protocolo: "..."} (legacy)
          - 4xx: {erro: [{codigo: "...", descricao: "...", complemento: "..."}]}
          - 4xx: {codigo: "...", mensagem: "..."} (legacy error format)
        """
        try:
            data = response.json()
        except Exception:
            return EventResponse(
                success=False,
                error_code=str(response.status_code),
                error_message=get_error_message(ErrorCode.RESPONSE_INVALID_JSON),
            )

        if response.status_code in (200, 201):
            ret_evento = data.get("retEvento")

            if ret_evento is not None:
                # cStat 144 = evento recebido com sucesso
                c_stat = ret_evento.get("cStat")

                if c_stat is not None and str(c_stat) != "144":
                    return EventResponse(
                        success=False,
                        error_code=str(c_stat),
                        error_message=(
                            ret_evento.get("xMotivo")
                            or "Erro no registro do evento."
                        ),
                    )

                return EventResponse(
                    success=True,
                    protocolo=ret_evento.get("idEvento"),
                )

            # Legacy shape: {protocolo: "..."}
            return EventResponse(
                success=True,
                protocolo=data.get("protocolo"),
            )

        # Error response — try SEFIN's erro array format first
        erros = data.get("erro")
        if isinstance(erros, list) and erros:
            parts = []

            for e in erros:
                d = (e.get("descricao") or "")[:255]
                c = (e.get("complemento") or "")[:255]
                parts.append(f"{d}: {c}" if c else d)

            return EventResponse(
                success=False,
                error_code=(erros[0].get("codigo") or str(response.status_code)),
                error_message="; ".join(p for p in parts if p) or "Erro desconhecido.",
            )

        return EventResponse(
            success=False,
            error_code=data.get("codigo") or str(response.status_code),
            error_message=data.get("mensagem") or "Erro desconhecido.",
        )

    def query_convenio_municipal(self, codigo_municipio: int) -> ConvenioMunicipal:
        """Consulta se um municipio tem convenio com o sistema nacional.

        Args:
            codigo_municipio: Codigo IBGE do municipio (7 digitos)

        Returns:
            ConvenioMunicipal com informacoes do convenio

        Raises:
            NFSeAPIError: Se ocorrer erro na consulta
        """
        url = f"{self.parametrizacao_url}/{codigo_municipio}/convenio"

        try:
            with self._get_client() as client:
                response = client.get(url)

                if response.status_code == 404:
                    return ConvenioMunicipal(
                        codigo_municipio=codigo_municipio,
                        aderido=False,
                    )

                if response.status_code != 200:
                    error_data = _error_payload(response)

                    msg = error_data.get("mensagem") or (
                        f"Erro ao consultar convênio: HTTP {response.status_code}"
                    )
                    raise NFSeAPIError(
                        msg,
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                data = _require_json_object(
                    response, context="ao consultar convênio"
                )

                return ConvenioMunicipal(
                    codigo_municipio=codigo_municipio,
                    aderido=True,
                    raw_data=data,
                )

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError(
                "Tempo esgotado ao consultar convênio.",
                code=ErrorCode.COMMUNICATION_TIMEOUT,
            )

        except httpx.RequestError as e:
            raise NFSeAPIError(
                "Erro de comunicação ao consultar convênio municipal.",
                code=ErrorCode.COMMUNICATION_ERROR,
            ) from e
