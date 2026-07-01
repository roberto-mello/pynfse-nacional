"""IBSCBS models for NFSe Nacional."""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .types import Percent3V2

_REF_NFSE_PATTERN = re.compile(r"^[0-9]{50}$")
_C_IND_OP_PATTERN = re.compile(r"^[0-9]{6}$")
_FONE_PATTERN = re.compile(r"^[0-9]{6,20}$")
_CNPJ_PATTERN = re.compile(r"^[0-9]{14}$")
_CPF_PATTERN = re.compile(r"^[0-9]{11}$")
_CST_PATTERN = re.compile(r"^[0-9]{3}$")
_CLASS_TRIB_PATTERN = re.compile(r"^[0-9]{6}$")
_C_CIB_PATTERN = re.compile(r"^[0-9]{8}$")

# Official ANEXO_C-INDOP_IBSCBS-SNNFSe-v1.01-20260122 workbook.
# Source table contains 26 codes; 080101 is Via-only and is excluded below.
IBSCBS_C_IND_OP_CODES = (
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
IBSCBS_C_IND_OP_ALLOWLIST = frozenset(
    code for code in IBSCBS_C_IND_OP_CODES if code != "080101"
)


def _validate_choice(model_name: str, selected: list[tuple[str, Any]]) -> None:
    count = sum(value is not None for _, value in selected)
    if count != 1:
        names = ", ".join(name for name, _ in selected)
        raise ValueError(f"{model_name} deve informar exatamente um de: {names}.")


class EnderecoIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logradouro: str = Field(..., min_length=1, max_length=255)
    numero: str = Field(..., min_length=1, max_length=60)
    complemento: Optional[str] = Field(None, max_length=156)
    bairro: str = Field(..., min_length=1, max_length=60)
    codigo_municipio: int = Field(..., ge=1000000, le=9999999)
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., pattern=r"^[0-9]{8}$")


class RefNFSe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_nfse: list[str] = Field(default_factory=list, max_length=99)

    @field_validator("ref_nfse")
    @classmethod
    def validate_ref_nfse(cls, values: list[str]) -> list[str]:
        for value in values:
            if not _REF_NFSE_PATTERN.fullmatch(value):
                raise ValueError("refNFSe deve conter 50 digitos numericos.")
        return values


class DestIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cnpj: Optional[str] = Field(None, pattern=r"^[0-9]{14}$")
    cpf: Optional[str] = Field(None, pattern=r"^[0-9]{11}$")
    nif: Optional[str] = Field(None, min_length=1, max_length=40)
    c_nao_nif: Optional[Literal["0", "1", "2"]] = None
    x_nome: str = Field(..., min_length=1, max_length=150)
    end: Optional[EnderecoIBSCBS] = None
    fone: Optional[str] = Field(None, pattern=r"^[0-9]{6,20}$")
    email: Optional[str] = Field(None, max_length=80)

    @model_validator(mode="after")
    def validate_choice(self) -> "DestIBSCBS":
        _validate_choice(
            "DestIBSCBS",
            [
                ("cnpj", self.cnpj),
                ("cpf", self.cpf),
                ("nif", self.nif),
                ("c_nao_nif", self.c_nao_nif),
            ],
        )
        return self


class ImovelIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insc_imob_fisc: Optional[str] = Field(None, min_length=1, max_length=30)
    c_cib: Optional[str] = Field(None, pattern=_C_CIB_PATTERN.pattern)
    end: Optional[EnderecoIBSCBS] = None

    @model_validator(mode="after")
    def validate_choice(self) -> "ImovelIBSCBS":
        _validate_choice(
            "ImovelIBSCBS",
            [
                ("c_cib", self.c_cib),
                ("end", self.end),
            ],
        )
        return self


class GTribRegularIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cst_reg: str = Field(..., pattern=_CST_PATTERN.pattern)
    c_class_trib_reg: str = Field(..., pattern=_CLASS_TRIB_PATTERN.pattern)


class GDifIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    p_dif_uf: Percent3V2
    p_dif_mun: Percent3V2
    p_dif_cbs: Percent3V2


class GIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cst: str = Field(..., pattern=_CST_PATTERN.pattern)
    c_class_trib: str = Field(..., pattern=_CLASS_TRIB_PATTERN.pattern)
    c_cred_pres: Optional[str] = Field(None, pattern=r"^[0-9]{2}$")
    g_trib_regular: Optional[GTribRegularIBSCBS] = None
    g_dif: Optional[GDifIBSCBS] = None


class TribIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    g_ibscbs: GIBSCBS


class ValoresIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    g_ree_rep_res: Optional[list[Any]] = Field(default=None, max_length=1000)
    trib: TribIBSCBS


class IBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fin_nfse: Literal["0", "1", "2"]
    ind_final: Optional[Literal["0", "1"]] = None
    c_ind_op: str = Field(..., pattern=_C_IND_OP_PATTERN.pattern)
    tp_oper: Optional[Literal["1", "2", "3", "4", "5"]] = None
    g_ref_nfse: Optional[RefNFSe] = None
    tp_ente_gov: Optional[Literal["1", "2", "3", "4"]] = None
    ind_dest: Literal["0", "1"]
    dest: Optional[DestIBSCBS] = None
    imovel: Optional[ImovelIBSCBS] = None
    valores: ValoresIBSCBS

    @field_validator("c_ind_op")
    @classmethod
    def validate_c_ind_op(cls, value: str) -> str:
        if not _C_IND_OP_PATTERN.fullmatch(value):
            raise ValueError("cIndOp deve conter 6 digitos numericos.")
        if value not in IBSCBS_C_IND_OP_ALLOWLIST:
            if value == "080101":
                raise ValueError("cIndOp '080101' e exclusivo de NFS-e Via.")
            raise ValueError("cIndOp invalido para IBSCBS.")
        return value

    @field_validator("g_ref_nfse")
    @classmethod
    def validate_ref_nfse(cls, value: Optional[RefNFSe]) -> Optional[RefNFSe]:
        if value is not None and len(value.ref_nfse) > 99:
            raise ValueError("gRefNFSe suporta no maximo 99 referencias.")
        return value


IBSCBS.model_rebuild()
DestIBSCBS.model_rebuild()
ImovelIBSCBS.model_rebuild()
RefNFSe.model_rebuild()
ValoresIBSCBS.model_rebuild()
TribIBSCBS.model_rebuild()
GIBSCBS.model_rebuild()
GTribRegularIBSCBS.model_rebuild()
GDifIBSCBS.model_rebuild()
