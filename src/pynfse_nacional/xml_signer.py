import base64
import gzip

from .exceptions import NFSeCertificateError

try:
    from cryptography.hazmat.primitives.serialization import pkcs12

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    from signxml import XMLSigner, methods

    SIGNXML_AVAILABLE = True
except ImportError:
    SIGNXML_AVAILABLE = False


class XMLSignerService:
    """Sign XML documents with ICP-Brasil certificate."""

    def __init__(self, cert_path: str, cert_password: str):
        self.cert_path = cert_path
        self.cert_password = cert_password
        self._private_key = None
        self._certificate = None

    def _load_certificate(self) -> None:
        """Load certificate from file."""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise NFSeCertificateError("cryptography library not installed")

        if self._private_key is not None:
            return

        try:
            with open(self.cert_path, "rb") as f:
                cert_data = f.read()

            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                cert_data, self.cert_password.encode()
            )

            if self._certificate is None:
                raise NFSeCertificateError("Certificado nao encontrado no arquivo")

        except FileNotFoundError:
            raise NFSeCertificateError(
                f"Arquivo de certificado nao encontrado: {self.cert_path}"
            )

        except NFSeCertificateError:
            raise

        except Exception as e:
            raise NFSeCertificateError(f"Erro ao carregar certificado: {str(e)}")

    def sign(self, xml: str) -> str:
        """Sign XML document with certificate."""
        if not SIGNXML_AVAILABLE:
            raise NFSeCertificateError("signxml library not installed")

        self._load_certificate()

        try:
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
            )

            signed_xml = signer.sign(
                xml,
                key=self._private_key,
                cert=self._certificate,
            )

            if isinstance(signed_xml, bytes):
                return signed_xml.decode("utf-8")

            return signed_xml

        except Exception as e:
            raise NFSeCertificateError(f"Erro ao assinar XML: {str(e)}")

    def sign_and_encode(self, xml: str) -> str:
        """Sign XML, compress with GZip, and encode with Base64."""
        signed_xml = self.sign(xml)
        return self.compress_encode(signed_xml)

    @staticmethod
    def compress_encode(data: str) -> str:
        """Compress with GZip and encode with Base64."""
        compressed = gzip.compress(data.encode("utf-8"))
        return base64.b64encode(compressed).decode("ascii")
