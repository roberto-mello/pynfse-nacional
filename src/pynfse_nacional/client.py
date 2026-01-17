import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import httpx

from .constants import API_URLS, ENDPOINTS, Ambiente
from .exceptions import NFSeAPIError, NFSeCertificateError
from .models import DPS, NFSeResponse, EventResponse, NFSeQueryResult
from .xml_builder import XMLBuilder
from .xml_signer import XMLSignerService
from .utils import compress_encode, decode_decompress

try:
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

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
                raise NFSeCertificateError(f"Certificate file not found: {self.cert_path}")

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

        try:
            client = httpx.Client(
                cert=(cert_file_path, key_file_path),
                verify=True,
                timeout=self.timeout,
            )

            yield client
            client.close()

        except Exception as e:
            raise NFSeCertificateError(f"Error configuring HTTP client: {str(e)}")

        finally:
            Path(cert_file_path).unlink(missing_ok=True)
            Path(key_file_path).unlink(missing_ok=True)

    def submit_dps(self, dps: DPS) -> NFSeResponse:
        """Submit DPS and receive NFSe."""
        xml = self._xml_builder.build_dps(dps)
        signed_xml = self._xml_signer.sign(xml)
        encoded_content = compress_encode(signed_xml)

        payload = {
            "dps": encoded_content,
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
        if response.status_code == 200:
            data = response.json()

            nfse_xml = None

            if data.get("nfse"):
                try:
                    nfse_xml = decode_decompress(data["nfse"])
                except Exception:
                    nfse_xml = data.get("nfse")

            return NFSeResponse(
                success=True,
                chave_acesso=data.get("chaveAcesso"),
                nfse_number=data.get("nNFSe"),
                xml_nfse=nfse_xml,
            )

        try:
            error_data = response.json()
            return NFSeResponse(
                success=False,
                error_code=error_data.get("codigo") or str(response.status_code),
                error_message=error_data.get("mensagem") or "Erro desconhecido",
            )

        except Exception:
            return NFSeResponse(
                success=False,
                error_code=str(response.status_code),
                error_message=response.text or "Erro desconhecido",
            )

    def query_nfse(self, chave_acesso: str) -> NFSeQueryResult:
        """Query NFSe by access key."""
        url = f"{self.base_url}{ENDPOINTS['query_nfse'].format(chave=chave_acesso)}"

        try:
            with self._get_client() as client:
                response = client.get(url)

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    raise NFSeAPIError(
                        error_data.get("mensagem", "Erro ao consultar NFSe"),
                        code=error_data.get("codigo"),
                        status_code=response.status_code,
                    )

                data = response.json()

                xml_nfse = None

                if data.get("nfse"):
                    try:
                        xml_nfse = decode_decompress(data["nfse"])
                    except Exception:
                        xml_nfse = data.get("nfse")

                return NFSeQueryResult(
                    chave_acesso=data["chaveAcesso"],
                    nfse_number=data["nNFSe"],
                    status=data.get("situacao", "emitida"),
                    data_emissao=data["dhEmi"],
                    valor_servicos=data.get("vServPrest", 0),
                    prestador_cnpj=data.get("CNPJPrest", ""),
                    tomador_documento=data.get("CPFToma") or data.get("CNPJToma"),
                    xml_nfse=xml_nfse,
                )

        except NFSeAPIError:
            raise

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao consultar NFSe", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

    def download_danfse(self, chave_acesso: str) -> bytes:
        """Download DANFSe PDF."""
        url = f"{self.base_url}{ENDPOINTS['download_danfse'].format(chave=chave_acesso)}"

        try:
            with self._get_client() as client:
                response = client.get(url)

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    raise NFSeAPIError(
                        error_data.get("mensagem", "Erro ao baixar DANFSe"),
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

    def cancel_nfse(self, chave_acesso: str, reason: str) -> EventResponse:
        """Cancel NFSe by access key."""
        url = f"{self.base_url}{ENDPOINTS['events']}"

        payload = {
            "tpEvento": "110111",  # Cancelamento
            "chNFSe": chave_acesso,
            "xMotivo": reason,
        }

        try:
            with self._get_client() as client:
                response = client.post(url, json=payload)
                return self._parse_event_response(response)

        except httpx.TimeoutException:
            raise NFSeAPIError("Timeout ao cancelar NFSe", code="TIMEOUT")

        except httpx.RequestError as e:
            raise NFSeAPIError(f"Erro de comunicacao: {str(e)}", code="COMM_ERROR")

    def _parse_event_response(self, response: httpx.Response) -> EventResponse:
        """Parse API response for event registration."""
        if response.status_code in (200, 201):
            data = response.json()

            return EventResponse(
                success=True,
                protocolo=data.get("protocolo"),
            )

        try:
            error_data = response.json()

            return EventResponse(
                success=False,
                error_code=error_data.get("codigo") or str(response.status_code),
                error_message=error_data.get("mensagem") or "Erro desconhecido",
            )

        except Exception:
            return EventResponse(
                success=False,
                error_code=str(response.status_code),
                error_message=response.text or "Erro desconhecido",
            )
