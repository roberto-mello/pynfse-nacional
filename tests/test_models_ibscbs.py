"""Tests for IBSCBS Pydantic models."""

from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from pynfse_nacional.models_ibscbs import (
    GIBSCBS,
    IBSCBS,
    DestIBSCBS,
    EnderecoIBSCBS,
    GDifIBSCBS,
    GTribRegularIBSCBS,
    ImovelIBSCBS,
    RefNFSe,
    TribIBSCBS,
    ValoresIBSCBS,
)
from pynfse_nacional.types import Percent2V2, Percent3V2


def build_minimal_ibscbs() -> IBSCBS:
    return IBSCBS(
        fin_nfse="0",
        c_ind_op="020101",
        ind_dest="0",
        valores=ValoresIBSCBS(
            trib=TribIBSCBS(
                g_ibscbs=GIBSCBS(
                    cst="001",
                    c_class_trib="123456",
                )
            )
        ),
    )


class TestIBSCBSMinimal:
    def test_accepts_minimal_mandatory_payload(self):
        ibscbs = build_minimal_ibscbs()

        assert ibscbs.fin_nfse == "0"
        assert ibscbs.c_ind_op == "020101"
        assert ibscbs.ind_dest == "0"
        assert ibscbs.valores.trib.g_ibscbs.cst == "001"
        assert ibscbs.valores.trib.g_ibscbs.c_class_trib == "123456"


class TestIBSCBSOptionalModels:
    def test_accepts_ref_nfse(self):
        ref = RefNFSe(
            ref_nfse=[
                "12345678901234567890123456789012345678901234567890",
            ]
        )

        assert ref.ref_nfse == [
            "12345678901234567890123456789012345678901234567890",
        ]

    def test_accepts_dest_with_cnpj(self):
        dest = DestIBSCBS(
            cnpj="11222333000181",
            x_nome="Cliente Teste LTDA",
        )

        assert dest.cnpj == "11222333000181"

    def test_accepts_imovel_with_cib(self):
        imovel = ImovelIBSCBS(c_cib="12345678")

        assert imovel.c_cib == "12345678"

    def test_accepts_g_trib_regular_and_g_dif(self):
        g_trib_regular = GTribRegularIBSCBS(
            cst_reg="123",
            c_class_trib_reg="123456",
        )
        g_dif = GDifIBSCBS(
            p_dif_uf=Decimal("12.34"),
            p_dif_mun=Decimal("45.67"),
            p_dif_cbs=Decimal("89.01"),
        )

        assert g_trib_regular.cst_reg == "123"
        assert g_dif.p_dif_cbs == Decimal("89.01")


class TestIBSCBSChoices:
    def test_dest_requires_exactly_one_identifier(self):
        with pytest.raises(ValidationError):
            DestIBSCBS(
                cnpj="11222333000181",
                cpf="52998224725",
                x_nome="Cliente Teste LTDA",
            )

        with pytest.raises(ValidationError):
            DestIBSCBS(x_nome="Cliente Teste LTDA")

    def test_imovel_requires_exactly_one_identifier(self):
        with pytest.raises(ValidationError):
            ImovelIBSCBS(
                c_cib="12345678",
                end=EnderecoIBSCBS(
                    logradouro="Rua Teste",
                    numero="100",
                    bairro="Centro",
                    codigo_municipio=3550308,
                    uf="SP",
                    cep="01310100",
                ),
            )

        with pytest.raises(ValidationError):
            ImovelIBSCBS()


class TestIBSCBSDecimals:
    def test_percent2v2_boundaries(self):
        adapter = TypeAdapter(Percent2V2)

        assert adapter.validate_python(Decimal("0.00")) == Decimal("0.00")
        assert adapter.validate_python(Decimal("99.99")) == Decimal("99.99")

        with pytest.raises(ValidationError):
            adapter.validate_python(Decimal("-0.01"))

        with pytest.raises(ValidationError):
            adapter.validate_python(Decimal("100.00"))

        with pytest.raises(ValidationError):
            adapter.validate_python(Decimal("NaN"))

        with pytest.raises(ValidationError):
            adapter.validate_python(Decimal("Infinity"))

    def test_percent3v2_boundaries(self):
        adapter = TypeAdapter(Percent3V2)

        assert adapter.validate_python(Decimal("999.99")) == Decimal("999.99")

        with pytest.raises(ValidationError):
            adapter.validate_python(Decimal("1000.00"))


class TestIBSCBSCodes:
    def test_fin_nfse_literal(self):
        ibscbs = build_minimal_ibscbs()
        assert ibscbs.fin_nfse == "0"

        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="3",
                c_ind_op="020101",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_c_ind_op_accepts_official_code(self):
        ibscbs = build_minimal_ibscbs()

        assert ibscbs.c_ind_op == "020101"

    def test_c_ind_op_rejects_unknown_code(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="0",
                c_ind_op="999999",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_c_ind_op_rejects_via_only_code(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="0",
                c_ind_op="080101",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )


class TestIBSCBSValidation:
    def test_ref_nfse_enforces_max_length(self):
        with pytest.raises(ValidationError):
            RefNFSe(
                ref_nfse=[
                    "12345678901234567890123456789012345678901234567890",
                ]
                * 100,
            )

    def test_extra_fields_are_forbidden(self):
        with pytest.raises(ValidationError):
            GIBSCBS(
                cst="001",
                c_class_trib="123456",
                v_ibs="10.00",
            )

