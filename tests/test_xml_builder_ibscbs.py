"""IBSCBS XML builder validation tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree
from pydantic import ValidationError

from pynfse_nacional.models import DPS, Prestador, Servico, Tomador
from pynfse_nacional.models_ibscbs import (
    GIBSCBS,
    IBSCBS,
    DestIBSCBS,
    EnderecoIBSCBS,
    GDifIBSCBS,
    GTribRegularIBSCBS,
    ImovelIBSCBS,
    ListaDocDFeIBSCBS,
    ListaDocIBSCBS,
    RefNFSe,
    TribIBSCBS,
    ValoresIBSCBS,
)
from pynfse_nacional.xml_builder import XMLBuilder
from pynfse_nacional.xml_signer import (
    CRYPTOGRAPHY_AVAILABLE,
    SIGNXML_AVAILABLE,
    XMLSignerService,
)

from ._helpers.xsd import load_dps_schema

NS = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}
DS_NS = "http://www.w3.org/2000/09/xmldsig#"


@pytest.fixture
def sample_servico(shared_sample_servico):
    servico = deepcopy(shared_sample_servico)
    servico.codigo_lc116 = "04.03.01"
    servico.codigo_tributacao_municipal = "123"
    servico.discriminacao = "Consulta medica"
    servico.valor_servicos = Decimal("10.00")
    servico.aliquota_simples = None
    return servico


@pytest.fixture
def sample_ibscbs() -> IBSCBS:
    return IBSCBS(
        fin_nfse="0",
        c_ind_op="020101",
        ind_dest="0",
        valores=ValoresIBSCBS(
            g_ree_rep_res=[
                ListaDocIBSCBS(
                    d_fe_nacional=ListaDocDFeIBSCBS(
                        tipo_chave_dfe="2",
                        chave_dfe="NFE1234567890",
                    ),
                    dt_emi_doc=date(2026, 1, 15),
                    dt_comp_doc=date(2026, 1, 15),
                    tp_ree_rep_res="01",
                    vlr_ree_rep_res=Decimal("10.00"),
                )
            ],
            trib=TribIBSCBS(
                g_ibscbs=GIBSCBS(
                    cst="001",
                    c_class_trib="123456",
                )
            ),
        ),
    )


@pytest.fixture
def sample_dps(
    sample_prestador: Prestador,
    sample_tomador: Tomador,
    sample_servico: Servico,
    sample_ibscbs: IBSCBS,
) -> DPS:
    return DPS(
        serie="3",
        numero=52,
        competencia="2025-12",
        data_emissao=datetime(2025, 12, 10, 9, 38, 0),
        prestador=sample_prestador,
        tomador=sample_tomador,
        servico=sample_servico,
        regime_tributario="normal",
        op_simp_nac="1",
        ibscbs=sample_ibscbs,
    )


@pytest.fixture
def sample_dps_with_optional_ibscbs(sample_dps: DPS) -> DPS:
    dps = deepcopy(sample_dps)
    dps.ibscbs = IBSCBS(
        fin_nfse="0",
        c_ind_op="100301",
        ind_dest="0",
        tp_oper="2",
        tp_ente_gov="4",
        g_ref_nfse=RefNFSe(
            ref_nfse=[
                "12345678901234567890123456789012345678901234567890",
            ]
        ),
        dest=DestIBSCBS(
            cnpj="11222333000181",
            x_nome="Cliente Teste LTDA",
            end=EnderecoIBSCBS(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio=3509502,
                uf="SP",
                cep="13000000",
            ),
        ),
        imovel=ImovelIBSCBS(
            c_cib="12345678",
        ),
        valores=ValoresIBSCBS(
            g_ree_rep_res=[
                ListaDocIBSCBS(
                    d_fe_nacional=ListaDocDFeIBSCBS(
                        tipo_chave_dfe="2",
                        chave_dfe="NFE1234567890",
                    ),
                    dt_emi_doc=date(2026, 1, 15),
                    dt_comp_doc=date(2026, 1, 15),
                    tp_ree_rep_res="01",
                    vlr_ree_rep_res=Decimal("10.00"),
                )
            ],
            trib=TribIBSCBS(
                g_ibscbs=GIBSCBS(
                    cst="001",
                    c_class_trib="123456",
                    c_cred_pres="01",
                    g_trib_regular=GTribRegularIBSCBS(
                        cst_reg="123",
                        c_class_trib_reg="123456",
                    ),
                    g_dif=GDifIBSCBS(
                        p_dif_uf=Decimal("12.34"),
                        p_dif_mun=Decimal("45.67"),
                        p_dif_cbs=Decimal("89.01"),
                    ),
                )
            ),
        ),
    )
    return dps


def _build_signed_xml(xml: str, cert_path: str, cert_password: str) -> str:
    signer = XMLSignerService(cert_path=cert_path, cert_password=cert_password)
    return signer.sign(xml)


@pytest.fixture
def test_certificate(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "pynfse-test"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    pfx_bytes = pkcs12.serialize_key_and_certificates(
        name=b"pynfse-test",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(b"secret"),
    )
    cert_path = tmp_path / "test-cert.pfx"
    cert_path.write_bytes(pfx_bytes)

    return cert_path, "secret"


def test_builder_minimal_ibscbs_validates_against_official_xsd(sample_dps: DPS):
    xml_str = XMLBuilder().build_dps(sample_dps)
    schema = load_dps_schema()

    schema.assertValid(etree.fromstring(xml_str.encode("utf-8")))


def test_builder_simples_ibscbs_validates_against_official_xsd(
    sample_dps: DPS,
):
    """opSimpNac=3 emits regApTribSN only; no regApIBSCBSSN."""

    dps = deepcopy(sample_dps)
    dps.regime_tributario = "simples_nacional"
    dps.op_simp_nac = "3"
    dps.reg_ap_trib_sn = "1"

    xml_str = XMLBuilder().build_dps(dps)
    schema = load_dps_schema()
    root = etree.fromstring(xml_str.encode("utf-8"))

    schema.assertValid(root)
    assert (
        root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:regApIBSCBSSN", NS) is None
    )


def test_builder_rejects_op_simp_nac_4(sample_dps: DPS):
    """opSimpNac=4 is not official; model must reject before emission."""

    payload = sample_dps.model_dump()
    payload.update(
        {
            "regime_tributario": "simples_nacional",
            "op_simp_nac": "4",
            "reg_ap_trib_sn": "1",
        }
    )

    with pytest.raises(ValidationError):
        DPS(**payload)


def test_builder_ibscbs_with_optional_groups_validates_against_official_xsd(
    sample_dps_with_optional_ibscbs: DPS,
):
    xml_str = XMLBuilder().build_dps(sample_dps_with_optional_ibscbs)
    schema = load_dps_schema()

    schema.assertValid(etree.fromstring(xml_str.encode("utf-8")))

    root = etree.fromstring(xml_str.encode("utf-8"))
    documentos = root.find(
        "nfse:infDPS/nfse:IBSCBS/nfse:valores/nfse:gReeRepRes/nfse:documentos", NS
    )

    assert documentos is not None
    assert documentos.find("nfse:dFeNacional", NS) is not None
    assert documentos.find("nfse:item", NS) is None


@pytest.mark.skipif(
    not (CRYPTOGRAPHY_AVAILABLE and SIGNXML_AVAILABLE),
    reason="cryptography or signxml not installed",
)
def test_post_sign_ibscbs_inside_infdps_envelope(sample_dps: DPS, test_certificate):
    cert_path, cert_password = test_certificate
    signed_xml = _build_signed_xml(
        XMLBuilder().build_dps(sample_dps), str(cert_path), cert_password
    )
    root = etree.fromstring(signed_xml.encode("utf-8"))
    inf_dps = root.find("nfse:infDPS", NS)
    signature = root.find("ds:Signature", {"ds": DS_NS})

    assert inf_dps is not None
    assert inf_dps.find("nfse:IBSCBS", NS) is not None
    assert signature is not None
    reference = signature.find(f".//{{{DS_NS}}}Reference")

    assert reference is not None
    assert reference.get("URI") == f"#{inf_dps.get('Id')}"


@pytest.mark.skipif(
    not (CRYPTOGRAPHY_AVAILABLE and SIGNXML_AVAILABLE),
    reason="cryptography or signxml not installed",
)
def test_post_sign_digest_mutates_on_ibscbs_change(sample_dps: DPS, test_certificate):
    cert_path, cert_password = test_certificate

    original_signed = _build_signed_xml(
        XMLBuilder().build_dps(sample_dps), str(cert_path), cert_password
    )
    original_digest = (
        etree.fromstring(original_signed.encode("utf-8"))
        .find(f".//{{{DS_NS}}}DigestValue")
        .text
    )

    mutated = deepcopy(sample_dps)
    mutated.ibscbs.c_ind_op = "020201"
    mutated_signed = _build_signed_xml(
        XMLBuilder().build_dps(mutated), str(cert_path), cert_password
    )
    mutated_digest = (
        etree.fromstring(mutated_signed.encode("utf-8"))
        .find(f".//{{{DS_NS}}}DigestValue")
        .text
    )

    assert original_digest != mutated_digest
