import base64
import gzip

from lxml import etree

from .error_codes import ErrorCode
from .error_messages import get_error_message
from .exceptions import NFSeCertificateError

try:
    from cryptography.hazmat.primitives.serialization import pkcs12

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    from signxml import XMLSigner, methods
    from signxml import namespaces as signxml_namespaces

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
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_DEPENDENCY_MISSING),
                code=ErrorCode.CERTIFICATE_DEPENDENCY_MISSING,
            )

        if self._private_key is not None:
            return

        try:
            with open(self.cert_path, "rb") as f:
                cert_data = f.read()

            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                cert_data, self.cert_password.encode()
            )

            if self._certificate is None:
                raise NFSeCertificateError(
                    "Certificado não encontrado no arquivo.",
                    code=ErrorCode.CERTIFICATE_LOAD_FAILED,
                )

        except FileNotFoundError:
            raise NFSeCertificateError(
                f"Arquivo de certificado não encontrado: {self.cert_path}",
                code=ErrorCode.CERTIFICATE_FILE_NOT_FOUND,
            )

        except NFSeCertificateError:
            raise

        except Exception as e:
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_LOAD_FAILED),
                code=ErrorCode.CERTIFICATE_LOAD_FAILED,
            ) from e

    def sign(self, xml: str) -> str:
        """Sign XML document with certificate.

        Locates the signed info element (infDPS for DPS, infPedReg for events)
        and produces an enveloped signature referencing its Id attribute.
        Per the XSD schema, the Signature element is a sibling of the info element.
        """

        if not SIGNXML_AVAILABLE:
            raise NFSeCertificateError(
                "Biblioteca signxml não instalada.",
                code=ErrorCode.CERTIFICATE_DEPENDENCY_MISSING,
            )

        self._load_certificate()

        try:
            parser = etree.XMLParser(
                resolve_entities=False, no_network=True, huge_tree=False
            )
            xml_element = etree.fromstring(xml.encode("utf-8"), parser=parser)

            ns = "http://www.sped.fazenda.gov.br/nfse"
            signed_info = xml_element.find(f".//{{{ns}}}infDPS")

            if signed_info is None:
                signed_info = xml_element.find(f".//{{{ns}}}infPedReg")

            if signed_info is None:
                raise NFSeCertificateError(
                    "Elemento assinado (infDPS ou infPedReg) não encontrado no XML.",
                    code=ErrorCode.RESPONSE_INVALID_XML,
                )

            inf_dps_id = signed_info.get("Id")

            if not inf_dps_id:
                raise NFSeCertificateError(
                    "Atributo Id do infDPS não encontrado.",
                    code=ErrorCode.RESPONSE_INVALID_XML,
                )

            # Use exclusive canonicalization with comments as seen in real NFSe
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
            )

            # Remove ds: prefix from signature namespace (NFSe API requires unprefixed)
            signer.namespaces = {None: signxml_namespaces.ds}

            signed_xml = signer.sign(
                xml_element,
                key=self._private_key,
                cert=[self._certificate],
                reference_uri=f"#{inf_dps_id}",
            )

            xml_bytes = etree.tostring(
                signed_xml, encoding="utf-8", xml_declaration=True
            )

            return xml_bytes.decode("utf-8")

        except NFSeCertificateError:
            raise

        except Exception as e:
            raise NFSeCertificateError(
                get_error_message(ErrorCode.CERTIFICATE_SIGN_FAILED),
                code=ErrorCode.CERTIFICATE_SIGN_FAILED,
            ) from e

    def sign_and_encode(self, xml: str) -> str:
        """Sign XML, compress with GZip, and encode with Base64."""
        signed_xml = self.sign(xml)
        return self.compress_encode(signed_xml)

    @staticmethod
    def compress_encode(data: str) -> str:
        """Compress with GZip and encode with Base64."""
        compressed = gzip.compress(data.encode("utf-8"))
        return base64.b64encode(compressed).decode("ascii")
