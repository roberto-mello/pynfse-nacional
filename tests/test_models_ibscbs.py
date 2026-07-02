"""Tests for IBSCBS Pydantic models."""

from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from pynfse_nacional.models_ibscbs import (
    GIBSCBS,
    IBSCBS,
    IBSCBS_C_IND_OP_ALLOWLIST,
    IBSCBS_C_IND_OP_CODES,
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
    def test_c_ind_op_codes_match_official_annex(self):
        assert IBSCBS_C_IND_OP_CODES == (
            "020101",
            "020201",
            "020301",
            "030101",
            "030102",
            "030103",
            "030104",
            "040101",
            "050101",
            "050102",
            "050103",
            "050104",
            "050201",
            "060101",
            "070101",
            "070102",
            "080101",
            "100101",
            "100102",
            "100201",
            "100301",
            "100302",
            "100401",
            "100501",
            "100502",
            "100601",
        )
        assert IBSCBS_C_IND_OP_ALLOWLIST == frozenset(
            code for code in IBSCBS_C_IND_OP_CODES if code != "080101"
        )

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


class TestIBSCBSRules:
    def test_accepts_fin_nfse_one_with_credit_and_reference(self):
        ibscbs = IBSCBS(
            fin_nfse="1",
            tp_nfse_credito="01",
            c_ind_op="020101",
            ind_dest="0",
            g_ref_nfse=RefNFSe(
                ref_nfse=[
                    "12345678901234567890123456789012345678901234567890",
                ]
            ),
            valores=ValoresIBSCBS(
                trib=TribIBSCBS(
                    g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                )
            ),
        )

        assert ibscbs.fin_nfse == "1"
        assert ibscbs.tp_nfse_credito == "01"

    def test_accepts_fin_nfse_two_with_debit_and_reference(self):
        ibscbs = IBSCBS(
            fin_nfse="2",
            tp_nfse_debito="04",
            c_ind_op="020101",
            ind_dest="0",
            g_ref_nfse=RefNFSe(
                ref_nfse=[
                    "12345678901234567890123456789012345678901234567890",
                ]
            ),
            valores=ValoresIBSCBS(
                trib=TribIBSCBS(
                    g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                )
            ),
        )

        assert ibscbs.fin_nfse == "2"
        assert ibscbs.tp_nfse_debito == "04"

    def test_rejects_fin_nfse_zero_with_credit(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="0",
                tp_nfse_credito="01",
                c_ind_op="020101",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_rejects_fin_nfse_one_without_credit(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="1",
                c_ind_op="020101",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_rejects_fin_nfse_two_without_debit(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="2",
                c_ind_op="020101",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_rejects_tp_oper_without_reference(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="0",
                c_ind_op="020101",
                tp_oper="2",
                ind_dest="0",
                valores=ValoresIBSCBS(
                    trib=TribIBSCBS(
                        g_ibscbs=GIBSCBS(cst="001", c_class_trib="123456")
                    )
                ),
            )

    def test_rejects_empty_reference_group(self):
        with pytest.raises(ValidationError):
            IBSCBS(
                fin_nfse="0",
                c_ind_op="020101",
                ind_dest="0",
                g_ref_nfse=RefNFSe(),
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
