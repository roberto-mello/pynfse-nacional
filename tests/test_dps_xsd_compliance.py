"""DPS XML compliance against the unpatched official SEFIN XSD.

This harness validates DPS XML produced by ``XMLBuilder.build_dps`` against
the official NFSe schema vendored under ``tests/fixtures/xsd_official``.
There is no patched fixture anymore. The old xsd/nfse_v1.01 copy was the lie:
it blessed invented elements and hid the E1235 production rejection.
This harness is the gate that catches that drift.

Runs on every CI push, needs no certificate and no network.

Expected state on ``main`` before the ``pynfse-a90`` fix lands
-------------------------------------------------------------

Scenarios that emit ``regApIBSCBSSN`` (``simples_nacional`` and
``simples_nacional_with_ibscbs``) are marked ``xfail(strict=True)`` because
the current ``xml_builder`` emits that element inside ``regTrib`` for
``opSimpNac`` 3/4 even though the official ``TCRegTrib`` complex type does
not declare it. The official schema therefore rejects the emitted XML at
that element -- which is exactly the E1235 failure SEFIN returned from
production.

``strict=True`` makes the harness a forcing function, not a silent pass:

- Pre-a90 on ``main``: the scenarios ``xfail`` and CI stays green. The xfail
  reason names ``regApIBSCBSSN`` so the bug is documented in the test output.
- Post-a90 (the ``pynfse-a90`` fix PR): the scenarios ``xpass`` and
  ``strict=True`` turns that into a HARD failure, so CI goes red until the
  ``pynfse-a90`` PR removes the ``xfail`` marker. That forces the a90 author
  to own the cleanup and proves the harness now passes.

Running the scenarios by hand without the ``xfail`` marker (or inspecting
``schema.error_log``) prints the exact rejection, e.g. ``Element
regApIBSCBSSN: This element is not expected. Expected is regEspTrib``. That
is the E1235 signature and the proof the harness catches the bug.

The ``non_simples`` and ``mei`` scenarios are sanity gates: they never emit
``regApIBSCBSSN`` so they validate cleanly today. If they ever fail, the
harness is catching a different schema violation than E1235 and the failure
must be investigated.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

import pytest
from lxml import etree

from pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador
from pynfse_nacional.models_ibscbs import (
    GIBSCBS,
    IBSCBS,
    TribIBSCBS,
    ValoresIBSCBS,
)
from pynfse_nacional.xml_builder import XMLBuilder

from ._helpers.xsd import load_dps_schema

ENV_PREST_COD_MUN = 3509502
ENV_PREST_CNPJ = "11222333000181"
ENV_TOMA_CPF = "52998224725"

_A90_REGAP_XFAIL_REASON = (
    "pynfse-a90: xml_builder emits regApIBSCBSSN inside regTrib for "
    "opSimpNac 3/4, which the official TCRegTrib does not declare. "
    "E1235 in production. Remove this xfail once a90 drops the element."
)

_SIMPLES_DEFAULTS = {
    "reg_ap_trib_sn": "1",
    "reg_ap_ibs_cbs_sn": "1",
    "aliquota_simples": Decimal("15.50"),
}


def _endereco() -> Endereco:
    return Endereco(
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        codigo_municipio=ENV_PREST_COD_MUN,
        uf="SP",
        cep="13000000",
    )


def _prestador() -> Prestador:
    return Prestador(
        cnpj=ENV_PREST_CNPJ,
        inscricao_municipal="12345",
        razao_social="Empresa Teste LTDA",
        endereco=_endereco(),
    )


def _tomador() -> Tomador:
    return Tomador(
        cpf=ENV_TOMA_CPF,
        razao_social="Joao Silva",
    )


def _servico(aliquota_simples: Decimal | None = None) -> Servico:
    return Servico(
        codigo_lc116="04.03.01",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("10.00"),
        aliquota_simples=aliquota_simples,
    )


def _regular_ibscbs() -> IBSCBS:
    return IBSCBS(
        fin_nfse="0",
        c_ind_op="020101",
        ind_dest="0",
        ind_final="0",
        valores=ValoresIBSCBS(
            trib=TribIBSCBS(
                g_ibscbs=GIBSCBS(
                    cst="001",
                    c_class_trib="000001",
                )
            )
        ),
    )


def _build_dps(
    *,
    op_simp_nac: Literal["1", "2", "3", "4"],
    regime_tributario: str,
    ibscbs: IBSCBS | None = None,
    reg_ap_trib_sn: str | None = None,
    reg_ap_ibs_cbs_sn: str | None = None,
    aliquota_simples: Decimal | None = None,
) -> DPS:
    return DPS(
        serie="3",
        numero=1,
        competencia="2026-01",
        data_emissao=datetime(2026, 1, 15, 10, 30, 0),
        prestador=_prestador(),
        tomador=_tomador(),
        servico=_servico(aliquota_simples=aliquota_simples),
        regime_tributario=regime_tributario,
        op_simp_nac=op_simp_nac,
        reg_ap_trib_sn=reg_ap_trib_sn,
        reg_ap_ibs_cbs_sn=reg_ap_ibs_cbs_sn,
        ibscbs=ibscbs,
    )


def _assert_validates_official(dps: DPS) -> None:
    schema = load_dps_schema()
    xml_str = XMLBuilder().build_dps(dps)
    tree = etree.fromstring(xml_str.encode("utf-8"))

    if schema.validate(tree):
        return

    errors = "\n".join(
        f"line {error.line}: {error.message}" for error in schema.error_log
    )
    raise AssertionError(
        f"DPS XML rejected by unpatched official XSD:\n{errors}\n\n"
        f"Emitted XML:\n{xml_str}"
    )


def test_non_simples_validates_against_official_xsd() -> None:
    """opSimpNac=1 never emits regApIBSCBSSN; sanity gate."""

    dps = _build_dps(op_simp_nac="1", regime_tributario="normal")
    _assert_validates_official(dps)


def test_mei_validates_against_official_xsd() -> None:
    """opSimpNac=2 (MEI) never emits regApIBSCBSSN; sanity gate."""

    dps = _build_dps(op_simp_nac="2", regime_tributario="mei")
    _assert_validates_official(dps)


@pytest.mark.xfail(reason=_A90_REGAP_XFAIL_REASON, strict=True)
def test_simples_nacional_validates_against_official_xsd() -> None:
    """opSimpNac=3 currently emits regApIBSCBSSN; official schema rejects it.

    Pre-a90 this xfails (E1235-class). Post-a90 it xpasses and the xfail
    marker must be removed.
    """

    dps = _build_dps(
        op_simp_nac="3",
        regime_tributario="simples_nacional",
        **_SIMPLES_DEFAULTS,
    )
    _assert_validates_official(dps)


@pytest.mark.xfail(reason=_A90_REGAP_XFAIL_REASON, strict=True)
def test_simples_nacional_with_ibscbs_validates_against_official_xsd() -> None:
    """opSimpNac=3 with IBSCBS group; pre-a90 fails on regApIBSCBSSN.

    The IBSCBS group itself (infDPS/IBSCBS, finNFSe=0) IS valid in the
    official schema; only regApIBSCBSSN in regTrib is rejected. Post-a90
    this xpasses and the xfail marker must be removed.
    """

    dps = _build_dps(
        op_simp_nac="3",
        regime_tributario="simples_nacional",
        ibscbs=_regular_ibscbs(),
        **_SIMPLES_DEFAULTS,
    )
    _assert_validates_official(dps)
