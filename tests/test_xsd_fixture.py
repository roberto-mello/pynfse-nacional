"""Smoke tests for vendored NFSe XSD fixtures."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from lxml import etree

from pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador
from pynfse_nacional.xml_builder import XMLBuilder

from ._helpers.xsd import load_dps_schema, load_nfse_schema, sample_path


def test_nfse_schema_loads():
    schema = load_nfse_schema()

    assert isinstance(schema, etree.XMLSchema)


def test_dps_schema_loads():
    schema = load_dps_schema()

    assert isinstance(schema, etree.XMLSchema)


@pytest.mark.parametrize(
    "filename",
    [
        "ibscbs_minimal.xml",
        "ibscbs_with_retention.xml",
    ],
)
def test_golden_ibscbs_samples_validate_against_official_xsd(filename: str):
    schema = load_dps_schema()
    tree = etree.parse(str(sample_path(filename)))

    schema.assertValid(tree)


def test_tserie_dps_accepts_plain_serie():
    endereco = Endereco(
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        codigo_municipio=3509502,
        uf="SP",
        cep="13000000",
    )
    prestador = Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Empresa Teste LTDA",
        endereco=endereco,
    )
    tomador = Tomador(
        cpf="52998224725",
        razao_social="Joao Silva",
    )
    servico = Servico(
        codigo_lc116="04.03.01",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("10.00"),
    )
    dps = DPS(
        serie="3",
        numero=1,
        competencia="2026-01",
        data_emissao=datetime(2026, 1, 15, 10, 30, 0),
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        regime_tributario="normal",
        op_simp_nac="1",
    )

    xml_str = XMLBuilder().build_dps(dps)
    schema = load_dps_schema()

    schema.assertValid(etree.fromstring(xml_str.encode("utf-8")))
