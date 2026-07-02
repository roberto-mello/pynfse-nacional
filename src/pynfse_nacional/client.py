import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Literal, Optional
from xml.etree.ElementTree import ParseError as XMLParseError

import httpx

from .constants import API_URLS, ENDPOINTS, PARAMETRIZACAO_URLS, Ambiente
from .exceptions import NFSeAPIError, NFSeCertificateError
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
from .utils import _redacted_repr, compress_encode, decode_decompress
from .xml_builder import XMLBuilder
from .xml_signer import XMLSignerService

_CHAVE_RE = re.compile(r"^\d{50}$")
_ID_DPS_RE = re.compile(r"^DPS\d{42}$")


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
    - ``status="error"``: the lookup itself failed (transport or API error);
      ``error`` holds the :class:`NFSeAPIError`. The caller should surface the
      original submit error.
    """

    status: Literal["success", "processing", "error"]
    result: Optional[NFSeQueryResult] = None
    error: Optional[NFSeAPIError] = None

    @property
    def recovered(self) -> bool:
        """True when recovery succeeded and ``result`` is populated."""
        return self.status == "success"


def _validate_chave_acesso(chave: str) -> None:
    """Valida que chave_acesso contém exatamente 50 dígitos numéricos."""

    if not _CHAVE_RE.match(chave):
        raise ValueError(
            "chave_acesso deve conter exatamente 50 digitos numericos; "
            f"{_redacted_repr('valor', chave)}."
        )


def _validate_id_dps(id_dps: str) -> None:
    """Valida que id_dps segue o padrão DPS + 42 dígitos."""

    if not _ID_DPS_RE.match(id_dps):
        raise ValueError(
            "id_dps deve seguir o padrão 'DPS' + 42 digitos; "
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
            raise NFSeCertificateError("cryptography library not installed")

        if self._private_key is not None:
            return self._private_key, self._certificate

        try:
            cert_path = Path(self.cert_path)

            if not cert_path.exists():
                raise NFSeCertificateError(
                    f"Certificate file not found: {self.cert_path}"
                )

            with open(cert_path, "rb") as f:
                pkcs12_data = f.read()

            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                pkcs12_data, self.cert_password.encode()
            )

            if self._private_key is None:
                raise NFSeCertificateError("Private key not found in certificate")

            if self._certificate is None:
                raise NFSeCertificateError("Certificate not found in PKCS12 file")

            return self._private_key, self._certificate

        except NFSeCertificateError:
            raise

        except Exception as e:
            raise NFSeCertificateError(f"Error loading certificate: {str(e)}")

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

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pem", delete=False
        ) as cert_file:
            cert_file.write(cert_pem)
            cert_file_path = cert_file.name

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pem", delete=False
        ) as key_file:
            key_file.write(key_pem)
            key_file_path = key_file.name

        client = None
        try:
            try:
                client = httpx.Client(
                    cert=(cert_file_path, key_file_path),
                    verify=True,
                    timeout=self.timeout,
                )
            except Exception as e:
                raise NFSeCertificateError(
                    f"Error configuring HTTP client: {str(e)}"
                ) from e

            yield client
        finally:
            if client is not None:
                client.close()
            if cert_file_path:
                Path(cert_file_path).unlink(missing_ok=True)
            if key_file_path:
                Path(key_file_path).unlink(missing_ok=True)

    def submit_dps(self, dps: DPS) -> NFSeResponse:
        """Submit DPS and receive NFSe."""
        xml = self._xml_builder.build_dps(dps)
        signed_xml = self._xml_signer.sign(xml)
        encoded_content = compress_encode(signed_xml)

        payload = {
            "dpsXmlGZipB64": encoded_content,
        }

        url = f"{self.base_url}{ENDPOINTS['submit_dps']}"

        try:
            with self._get_client() as client:
                response = client.post(url, json=payload)
                return self._parse_dps_response(response)

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao comunicar com SEFIN", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

    def _parse_dps_response(self, response: httpx.Response) -> NFSeResponse:
        """Parse API response for DPS submission."""
        try:
            data = response.json()
        except Exception:
            return NFSeResponse(
                success=False,
                error_code=str(response.status_code),
                error_message=response.text or "Erro desconhecido",
            )

        # Check for chaveAcesso to determine success
        # (API may return success on non-200 status)
        if data.get("chaveAcesso"):
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
        return NFSeResponse(
            success=False,
            error_code=data.get("codigo") or str(response.status_code),
            error_message=data.get("mensagem") or str(data),
        )

    def _query_nfse_with_client(
        self, client: httpx.Client, chave_acesso: str
    ) -> NFSeQueryResult:
        """Query NFSe by access key using an existing HTTP client."""

        url = f"{self.base_url}{ENDPOINTS['query_nfse'].format(chave=chave_acesso)}"
        response = client.get(url)

        if response.status_code != 200:
            error_data = {}

            try:
                error_data = response.json()
            except Exception:
                pass

            if not isinstance(error_data, dict):
                error_data = {}

            raise NFSeAPIError(
                error_data.get("mensagem", "Erro ao consultar NFSe"),
                code=error_data.get("codigo"),
                status_code=response.status_code,
            )

        data = response.json()

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
                "Resposta invalida ao consultar NFSe: chaveAcesso ausente",
                status_code=response.status_code,
            )

        data_emissao = data.get("dhEmi")
        if not data_emissao:
            raise NFSeAPIError(
                "Resposta invalida ao consultar NFSe: dhEmi ausente",
                status_code=response.status_code,
            )

        nfse_number = extract_nfse_number(xml_root) if xml_root is not None else None
        if nfse_number is None:
            nfse_number = data.get("nNFSe")
        if nfse_number is None:
            raise NFSeAPIError(
                "Resposta invalida ao consultar NFSe: nNFSe ausente",
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

    def query_nfse(self, chave_acesso: str) -> NFSeQueryResult:
        """Query NFSe by access key."""
        _validate_chave_acesso(chave_acesso)

        try:
            with self._get_client() as client:
                return self._query_nfse_with_client(client, chave_acesso)

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao consultar NFSe", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

    def query_nfse_by_dps(self, id_dps: str) -> NFSeQueryResult:
        """Recover an NFSe by DPS identifier, then fetch the full invoice."""

        _validate_id_dps(id_dps)
        url = f"{self.base_url}{ENDPOINTS['query_nfse_by_dps'].format(id=id_dps)}"

        try:
            with self._get_client() as client:
                response = client.get(url)

                if response.status_code != 200:
                    error_data = {}

                    try:
                        error_data = response.json()
                    except Exception:
                        pass

                    if not isinstance(error_data, dict):
                        error_data = {}

                    raise NFSeAPIError(
                        error_data.get("mensagem", "Erro ao consultar DPS"),
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                chave_acesso = _extract_chave_acesso_from_dps_response(response)
                if not chave_acesso:
                    raise NFSeAPIError(
                        "Resposta da consulta por DPS sem chave de acesso",
                        code="INVALID_RESPONSE",
                        status_code=response.status_code,
                    )

                return self._query_nfse_with_client(client, chave_acesso)

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao consultar DPS", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

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

                error_data = {}

                try:
                    error_data = response.json()
                except Exception:
                    pass

                if not isinstance(error_data, dict):
                    error_data = {}

                raise NFSeAPIError(
                    error_data.get("mensagem", "Erro ao consultar DPS"),
                    code=error_data.get("codigo"),
                    status_code=response.status_code,
                )

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao consultar DPS", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

    def recover_nfse_by_dps(self, id_dps: str) -> RecoveryOutcome:
        """Recover an NFSe by DPS identifier when submit may have already succeeded.

        High-level helper that combines :meth:`has_nfse_by_dps` and
        :meth:`query_nfse_by_dps` for the duplicate / lost-``chave_acesso``
        recovery path. Use after ``submit_dps`` failed or raised, when SEFIN
        may still have processed the DPS.

        See :class:`RecoveryOutcome` for the possible statuses.
        """
        _validate_id_dps(id_dps)

        try:
            if not self.has_nfse_by_dps(id_dps):
                return RecoveryOutcome(status="processing")
        except NFSeAPIError as e:
            return RecoveryOutcome(status="error", error=e)

        try:
            return RecoveryOutcome(
                status="success",
                result=self.query_nfse_by_dps(id_dps),
            )
        except NFSeAPIError as e:
            return RecoveryOutcome(status="error", error=e)

    def download_danfse(self, chave_acesso: str) -> bytes:
        """Download DANFSe PDF from official API.

        Note: The official DANFSE API at adn.nfse.gov.br may not be available
        or may return errors (501, 502, 429). As an alternative, use the local
        PDF generator:

            from pynfse_nacional.pdf_generator import generate_danfse_from_base64

            # After submit_dps():
            response = client.submit_dps(dps)
            if response.success and response.nfse_xml_gzip_b64:
                pdf_bytes = generate_danfse_from_base64(response.nfse_xml_gzip_b64)

        The local generator requires optional dependencies:
            pip install pynfse-nacional[pdf]
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
                    error_data = {}

                    try:
                        error_data = response.json()
                    except Exception:
                        pass

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
            raise NFSeAPIError("Timeout ao baixar DANFSe", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

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
            raise NFSeAPIError("Timeout ao cancelar NFSe", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

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
                error_message=(
                    response.text[:500] or f"HTTP {response.status_code} sem corpo"
                ),
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
                            ret_evento.get("xMotivo") or "Erro no registro do evento"
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
                error_message="; ".join(p for p in parts if p) or "Erro desconhecido",
            )

        return EventResponse(
            success=False,
            error_code=data.get("codigo") or str(response.status_code),
            error_message=data.get("mensagem") or "Erro desconhecido",
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
                    error_data = {}

                    try:
                        error_data = response.json()
                    except Exception:
                        pass

                    msg = error_data.get("mensagem") or (
                        f"Erro ao consultar convenio: HTTP {response.status_code}"
                    )
                    raise NFSeAPIError(
                        msg,
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                data = response.json()

                return ConvenioMunicipal(
                    codigo_municipio=codigo_municipio,
                    aderido=True,
                    raw_data=data,
                )

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao consultar convenio", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")
