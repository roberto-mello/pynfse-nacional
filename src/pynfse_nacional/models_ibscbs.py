"""IBSCBS models for NFSe Nacional."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .exceptions import NFSeValidationError
from .types import Money15V2, Percent3V2
from .utils import _redacted_repr

_REF_NFSE_PATTERN = re.compile(r"^[0-9]{50}$")
_C_IND_OP_PATTERN = re.compile(r"^[0-9]{6}$")
_FONE_PATTERN = re.compile(r"^[0-9]{6,20}$")
_CNPJ_PATTERN = re.compile(r"^[0-9]{14}$")
_CPF_PATTERN = re.compile(r"^[0-9]{11}$")
_CST_PATTERN = re.compile(r"^[0-9]{3}$")
_CLASS_TRIB_PATTERN = re.compile(r"^[0-9]{6}$")
_C_CIB_PATTERN = re.compile(r"^[0-9]{8}$")

_OP_BEM_IMOVEL = (
    "Operação com bem imóvel, bem imaterial, inclusive direito, "
    "relacionada a bem imóvel"
)
_OP_BEM_IMOVEL_EXEC = (
    "Execução de operações com bem imóvel, bem imaterial, inclusive direito, "
    "relacionado a bem imóvel"
)
_OP_SERVICO_BEM_IMOVEL_EXEC = "Execução de serviços sobre bem imóvel"
_OP_ADMIN_BEM_IMOVEL_EXEC = (
    "Execução dos serviços de administração e intermediação de bens imóveis"
)
_OP_PESSOA_FISICA = (
    "Serviço prestado fisicamente sobre a pessoa ou fruído presencialmente "
    "por pessoa física"
)
_OP_SERVICOS_PESSOA_FISICA_EXEC = (
    "Execução de serviços diversos exclusivamente prestados fisicamente "
    "sobre a pessoa ou integralmente fruídos presencialmente por pessoa "
    "física (2)"
)
_OP_FEIRAS = (
    "Serviço de planejamento, organização e administração de feiras, "
    "exposições, congressos, espetáculos, exibições e congêneres"
)
_OP_FEIRAS_EXEC = (
    "Execução de serviços de planejamento, organização e administração de "
    "feiras, exposições, congressos, espetáculos, exibições e congêneres"
)
_OP_BEM_MOVEL = "Serviço prestado fisicamente sobre bem móvel material"
_OP_BEM_MOVEL_EXEC = (
    "Execução de serviços diversos fisicamente prestados sobre bem móvel "
    "material"
)
_OP_PORTUARIO_EXEC = "Execução de serviços portuários"
_OP_TRANSP_PASSAGEIROS = "Serviço de transporte de passageiros"
_OP_TRANSP_PASSAGEIROS_EXEC = "Execução de serviços de transporte de passageiros"
_OP_TRANSP_CARGA = "Serviço de transporte de carga"
_OP_TRANSP_CARGA_EXEC = "Execução de serviços de transporte de carga"
_OP_VIA = "Serviço de exploração de via"
_OP_VIA_EXEC = "Execução de serviços de exploração de via"
_OP_PUBLICIDADE_ONEROSA = (
    "Cessão de espaço para prestação de serviços publicitários, em operações "
    "onerosas (4)"
)
_OP_PUBLICIDADE_ONEROSA_EXEC = (
    "Execução de operações de cessão de espaço para prestação de serviços "
    "publicitários"
)
_OP_PUBLICIDADE_NAO_ONEROSA = (
    "Cessão de espaço para prestação de serviços publicitários, em operações "
    "não onerosas (4)"
)
_OP_BENS_IMATERIAIS_ONEROSOS = (
    "Demais bens móveis imateriais, inclusive direitos, em operações "
    "onerosas"
)
_OP_BENS_IMATERIAIS_ONEROSOS_EXEC = (
    "Execução de demais operações não especificadas anteriormente com bens "
    "móveis imateriais, inclusive direitos"
)
_OP_BENS_IMATERIAIS_NAO_ONEROSOS = (
    "Demais bens móveis imateriais, inclusive direitos, em operações "
    "não onerosas"
)
_OP_BENS_IMATERIAIS_NAO_ONEROSOS_EXEC = (
    "Execução de demais operações não especificadas anteriormente com bens "
    "móveis imateriais, inclusive direitos"
)
_PATH_IMOVEL = "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao"
_PATH_PREST_END = "NFSe/infNFSe/DPS/infDPS/prest/end/"
_PATH_DEST = "NFSe/infNFSe/DPS/infDPS/IBSCBS/dest/"
_PATH_SERV_LOC = "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao"
_PATH_EVENTO = "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/"
_PATH_DEST_ONLY = "NFSe/infNFSe/DPS/infDPS/dest/"
_PATH_TOMA_END_OR_DEST = (
    "NFSe/infNFSe/DPS/infDPS/toma/end | "
    "NFSe/infNFSe/DPS/infDPS/IBSCBS/dest/"
)
_PATH_TOMA_END_EXT_OR_DEST_END_EXT = (
    "NFSe/infNFSe/DPS/infDPS/toma/end/endExt | "
    "NFSe/infNFSe/DPS/infDPS/IBSCBS/dest/end/endExt"
)
_PATH_TOMA_OR_DEST_FOR_BENS = (
    "NFSe/infNFSe/DPS/infDPS/toma/ | "
    "NFSe/infNFSe/DPS/infDPS/IBSCBS/dest/"
)
_PATH_TOMA_EXT_OR_DEST_END_EXT_FOR_BENS = (
    "NFSe/infNFSe/DPS/infDPS/toma/end/endExt/ | "
    "NFSe/infNFSe/DPS/infDPS/IBSCBS/dest/end/endExt/"
)


@dataclass(frozen=True)
class IBSCBSOperationVariant:
    """One official `cIndOp` row from the RTC annex."""

    sequencia: str
    c_ind_op: str
    local_fornecimento: str
    campo_layout: str


@dataclass(frozen=True)
class IBSCBSOperationCategory:
    """Grouped `cIndOp` family from the RTC annex."""

    artigo: str
    inciso: str
    tipo_operacao: str
    local_operacao: str
    caracteristica_fornecimento: str
    codigo_base: str
    variantes: tuple[IBSCBSOperationVariant, ...]

IBSCBS_OPERATION_CATEGORIES = (
    IBSCBSOperationCategory(
        "Art. 11",
        "II",
        _OP_BEM_IMOVEL,
        "o local onde o imóvel estiver situado",
        _OP_BEM_IMOVEL_EXEC,
        "0201",
        (
            IBSCBSOperationVariant(
                "01",
                "020101",
                "Localidade do imóvel (1)",
                _PATH_IMOVEL,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "II",
        _OP_BEM_IMOVEL,
        "o local onde o imóvel estiver situado",
        _OP_SERVICO_BEM_IMOVEL_EXEC,
        "0202",
        (
            IBSCBSOperationVariant(
                "01",
                "020201",
                "Localidade do imóvel (1)",
                _PATH_IMOVEL,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "II",
        _OP_BEM_IMOVEL,
        "o local onde o imóvel estiver situado",
        _OP_ADMIN_BEM_IMOVEL_EXEC,
        "0203",
        (
            IBSCBSOperationVariant(
                "01",
                "020301",
                "Localidade do imóvel (1)",
                _PATH_IMOVEL,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "III",
        _OP_PESSOA_FISICA,
        "o local da prestação do serviço",
        _OP_SERVICOS_PESSOA_FISICA_EXEC,
        "0301",
        (
            IBSCBSOperationVariant(
                "01",
                "030101",
                "Estabelecimento do fornecedor",
                _PATH_PREST_END,
            ),
            IBSCBSOperationVariant(
                "02",
                "030102",
                "Endereço do adquirente",
                _PATH_TOMA_END_OR_DEST,
            ),
            IBSCBSOperationVariant(
                "03",
                "030103",
                "Endereço do destinatário",
                _PATH_DEST,
            ),
            IBSCBSOperationVariant(
                "04",
                "030104",
                "Endereço diverso do fornecedor, adquirente ou destinatário",
                _PATH_SERV_LOC,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "IV",
        _OP_FEIRAS,
        "o local do evento a que se refere o serviço",
        _OP_FEIRAS_EXEC,
        "0401",
        (
            IBSCBSOperationVariant(
                "01",
                "040101",
                "Local do Evento",
                _PATH_EVENTO,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "V",
        _OP_BEM_MOVEL,
        "o local da prestação do serviço",
        _OP_BEM_MOVEL_EXEC,
        "0501",
        (
            IBSCBSOperationVariant(
                "01",
                "050101",
                "Estabelecimento do fornecedor",
                _PATH_PREST_END,
            ),
            IBSCBSOperationVariant(
                "02",
                "050102",
                "Endereço do adquirente",
                _PATH_TOMA_END_OR_DEST,
            ),
            IBSCBSOperationVariant(
                "03",
                "050103",
                "Endereço do destinatário",
                _PATH_DEST,
            ),
            IBSCBSOperationVariant(
                "04",
                "050104",
                "Endereço diverso do fornecedor, adquirente ou destinatário",
                _PATH_SERV_LOC,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "V",
        _OP_BEM_MOVEL,
        "o local da prestação do serviço",
        _OP_PORTUARIO_EXEC,
        "0502",
        (
            IBSCBSOperationVariant(
                "01",
                "050201",
                "Local da prestação",
                _PATH_SERV_LOC,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "VI",
        _OP_TRANSP_PASSAGEIROS,
        "o local da prestação do serviço",
        _OP_TRANSP_PASSAGEIROS_EXEC,
        "0601",
        (
            IBSCBSOperationVariant(
                "01",
                "060101",
                "Local de início do transporte",
                _PATH_SERV_LOC,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "VII",
        _OP_TRANSP_CARGA,
        "o local da prestação do serviço",
        _OP_TRANSP_CARGA_EXEC,
        "0701",
        (
            IBSCBSOperationVariant(
                "01",
                "070101",
                "Endereço fornecido para entrega",
                _PATH_SERV_LOC,
            ),
            IBSCBSOperationVariant(
                "02",
                "070102",
                "Local da retirada",
                _PATH_SERV_LOC,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "VIII",
        _OP_VIA,
        (
            "o território de cada Município e Estado, ou do Distrito Federal, "
            "proporcionalmente à correspondente extensão da via explorada"
        ),
        _OP_VIA_EXEC,
        "0801",
        (
            IBSCBSOperationVariant(
                "01",
                "080101",
                (
                    "Local da prestação, correspondente à extensão da via "
                    "explorada e proporcional ao território dos entes "
                    "tributantes"
                ),
                "EXCLUSIVO PARA NFS-e Via.",
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_PUBLICIDADE_ONEROSA,
        (
            "o local do domicílio principal do adquirente, nas operações "
            "onerosas"
        ),
        _OP_PUBLICIDADE_ONEROSA_EXEC,
        "1005",
        (
            IBSCBSOperationVariant(
                "01",
                "100101",
                "Local do domicílio principal do adquirente (3)",
                _PATH_TOMA_END_OR_DEST,
            ),
            IBSCBSOperationVariant(
                "02",
                "100102",
                (
                    "Local do domicílio do destinatário, nos casos de "
                    "adquirente residente ou domiciliado no exterior (5)(6)"
                ),
                _PATH_TOMA_END_EXT_OR_DEST_END_EXT,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_PUBLICIDADE_NAO_ONEROSA,
        (
            "o local do domicílio principal do destinatário, nas operações "
            "não onerosas"
        ),
        _OP_PUBLICIDADE_ONEROSA_EXEC,
        "1006",
        (
            IBSCBSOperationVariant(
                "01",
                "100201",
                "Local do domicílio principal do destinatário (6)",
                _PATH_DEST_ONLY,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_BENS_IMATERIAIS_ONEROSOS,
        (
            "o local do domicílio principal do adquirente, nas operações "
            "onerosas"
        ),
        _OP_BENS_IMATERIAIS_ONEROSOS_EXEC,
        "1001",
        (
            IBSCBSOperationVariant(
                "01",
                "100301",
                "Local do domicílio principal do adquirente (3)",
                _PATH_TOMA_END_OR_DEST,
            ),
            IBSCBSOperationVariant(
                "02",
                "100302",
                (
                    "Local do domicílio do destinatário, nos casos de "
                    "adquirente residente ou domiciliado no exterior (5)(6)"
                ),
                _PATH_TOMA_END_EXT_OR_DEST_END_EXT,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_BENS_IMATERIAIS_NAO_ONEROSOS,
        (
            "o local do domicílio principal do destinatário, nas operações "
            "não onerosas"
        ),
        _OP_BENS_IMATERIAIS_NAO_ONEROSOS_EXEC,
        "1002",
        (
            IBSCBSOperationVariant(
                "01",
                "100401",
                "Local do domicílio principal do destinatário (6)",
                _PATH_DEST_ONLY,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_BENS_IMATERIAIS_ONEROSOS,
        (
            "o local do domicílio principal do adquirente, nas operações "
            "onerosas"
        ),
        _OP_BENS_IMATERIAIS_ONEROSOS_EXEC,
        "1003",
        (
            IBSCBSOperationVariant(
                "01",
                "100501",
                "Local do domicílio principal do adquirente (3)",
                _PATH_TOMA_OR_DEST_FOR_BENS,
            ),
            IBSCBSOperationVariant(
                "02",
                "100502",
                (
                    "Local do domicílio do destinatário, nos casos de "
                    "adquirente residente ou domiciliado no exterior (5)(6)"
                ),
                _PATH_TOMA_EXT_OR_DEST_END_EXT_FOR_BENS,
            ),
        ),
    ),
    IBSCBSOperationCategory(
        "Art. 11",
        "X",
        _OP_BENS_IMATERIAIS_NAO_ONEROSOS,
        (
            "o local do domicílio principal do destinatário, nas operações "
            "não onerosas"
        ),
        _OP_BENS_IMATERIAIS_NAO_ONEROSOS_EXEC,
        "1004",
        (
            IBSCBSOperationVariant(
                "01",
                "100601",
                "Local do domicílio principal do destinatário (6)",
                _PATH_DEST_ONLY,
            ),
        ),
    ),
)
IBSCBS_OPERATION_VARIANTS = tuple(
    variant
    for category in IBSCBS_OPERATION_CATEGORIES
    for variant in category.variantes
)
IBSCBS_OPERATION_CATEGORIES_BY_CODE = {
    category.codigo_base: category for category in IBSCBS_OPERATION_CATEGORIES
}
IBSCBS_OPERATION_VARIANTS_BY_CODE = {
    variant.c_ind_op: variant for variant in IBSCBS_OPERATION_VARIANTS
}

# Official ANEXO_C-INDOP_IBSCBS-SNNFSe-v1.01-20260209 workbook.
# Source table contains 26 codes; 080101 is Via-only and is excluded below.
IBSCBS_C_IND_OP_CODES = tuple(variant.c_ind_op for variant in IBSCBS_OPERATION_VARIANTS)
IBSCBS_C_IND_OP_ALLOWLIST = frozenset(
    code for code in IBSCBS_C_IND_OP_CODES if code != "080101"
)

IBSCBSOperationCode = Literal[
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
    "100101",
    "100102",
    "100201",
    "100301",
    "100302",
    "100401",
    "100501",
    "100502",
    "100601",
]


def get_ibscbs_operation_category(c_ind_op: str) -> Optional[IBSCBSOperationCategory]:
    """Return the grouped operation family for a six-digit `cIndOp`."""

    if len(c_ind_op) < 4:
        return None

    return IBSCBS_OPERATION_CATEGORIES_BY_CODE.get(c_ind_op[:4])


def get_ibscbs_operation_variant(c_ind_op: str) -> Optional[IBSCBSOperationVariant]:
    """Return the official annex row for a six-digit `cIndOp`."""

    return IBSCBS_OPERATION_VARIANTS_BY_CODE.get(c_ind_op)


def _validate_choice(model_name: str, selected: list[tuple[str, Any]]) -> None:
    count = sum(value is not None for _, value in selected)
    if count != 1:
        names = ", ".join(name for name, _ in selected)
        raise ValueError(f"{model_name} deve informar exatamente um de: {names}.")


class EnderecoIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    logradouro: str = Field(..., min_length=1, max_length=255)
    numero: str = Field(..., min_length=1, max_length=60)
    complemento: Optional[str] = Field(None, max_length=156)
    bairro: str = Field(..., min_length=1, max_length=60)
    codigo_municipio: int = Field(..., ge=1000000, le=9999999)
    uf: Optional[str] = Field(None, min_length=2, max_length=2)
    cep: str = Field(..., pattern=r"^[0-9]{8}$")

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        from .models import VALID_UFS

        value_upper = value.upper()
        if value_upper not in VALID_UFS:
            raise ValueError(
                f"UF inválida. Use uma sigla válida: {', '.join(sorted(VALID_UFS))}"
            )
        return value_upper


class RefNFSe(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    ref_nfse: list[str] = Field(default_factory=list, min_length=1, max_length=99)

    @field_validator("ref_nfse")
    @classmethod
    def validate_ref_nfse(cls, values: list[str]) -> list[str]:
        for value in values:
            if not _REF_NFSE_PATTERN.fullmatch(value):
                raise ValueError("refNFSe deve conter 50 dígitos numéricos.")
        return values

    @model_validator(mode="after")
    def validate_non_empty(self) -> "RefNFSe":
        if not self.ref_nfse:
            raise ValueError("refNFSe deve conter ao menos uma referência.")
        return self


class DestIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    cnpj: Optional[str] = Field(None, pattern=_CNPJ_PATTERN.pattern)
    cpf: Optional[str] = Field(None, pattern=_CPF_PATTERN.pattern)
    nif: Optional[str] = Field(None, min_length=1, max_length=40)
    c_nao_nif: Optional[Literal["0", "1", "2"]] = None
    x_nome: str = Field(..., min_length=1, max_length=150)
    end: Optional[EnderecoIBSCBS] = None
    fone: Optional[str] = Field(None, pattern=_FONE_PATTERN.pattern)
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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

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
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    cst_reg: str = Field(..., pattern=_CST_PATTERN.pattern)
    c_class_trib_reg: str = Field(..., pattern=_CLASS_TRIB_PATTERN.pattern)


class GDifIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    p_dif_uf: Percent3V2
    p_dif_mun: Percent3V2
    p_dif_cbs: Percent3V2


class GIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    cst: str = Field(..., pattern=_CST_PATTERN.pattern)
    c_class_trib: str = Field(..., pattern=_CLASS_TRIB_PATTERN.pattern)
    c_cred_pres: Optional[str] = Field(None, pattern=r"^[0-9]{2}$")
    g_trib_regular: Optional[GTribRegularIBSCBS] = None
    g_dif: Optional[GDifIBSCBS] = None


class ListaDocFornecIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    cnpj: Optional[str] = Field(None, pattern=_CNPJ_PATTERN.pattern)
    cpf: Optional[str] = Field(None, pattern=_CPF_PATTERN.pattern)
    nif: Optional[str] = Field(None, min_length=1, max_length=40)
    c_nao_nif: Optional[Literal["0", "1", "2"]] = None
    x_nome: str = Field(..., min_length=1, max_length=150)

    @model_validator(mode="after")
    def validate_choice(self) -> "ListaDocFornecIBSCBS":
        _validate_choice(
            "ListaDocFornecIBSCBS",
            [
                ("cnpj", self.cnpj),
                ("cpf", self.cpf),
                ("nif", self.nif),
                ("c_nao_nif", self.c_nao_nif),
            ],
        )
        return self


class ListaDocDFeIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    tipo_chave_dfe: Literal["1", "2", "3", "9"]
    x_tipo_chave_dfe: Optional[str] = Field(None, max_length=255)
    chave_dfe: str = Field(..., min_length=1, max_length=50)


class ListaDocFiscalOutroIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    c_mun_doc_fiscal: str = Field(..., pattern=r"^[0-9]{1,7}$")
    n_doc_fiscal: str = Field(..., min_length=1, max_length=255)
    x_doc_fiscal: str = Field(..., min_length=1, max_length=255)


class ListaDocOutroIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    n_doc: str = Field(..., min_length=1, max_length=255)
    x_doc: str = Field(..., min_length=1, max_length=255)


class ListaDocIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    d_fe_nacional: Optional[ListaDocDFeIBSCBS] = None
    doc_fiscal_outro: Optional[ListaDocFiscalOutroIBSCBS] = None
    doc_outro: Optional[ListaDocOutroIBSCBS] = None
    fornec: Optional[ListaDocFornecIBSCBS] = None
    dt_emi_doc: date
    dt_comp_doc: date
    tp_ree_rep_res: Literal["01", "02", "03", "04", "99"]
    x_tp_ree_rep_res: Optional[str] = Field(None, max_length=150)
    vlr_ree_rep_res: Money15V2

    @model_validator(mode="after")
    def validate_choice(self) -> "ListaDocIBSCBS":
        _validate_choice(
            "ListaDocIBSCBS",
            [
                ("d_fe_nacional", self.d_fe_nacional),
                ("doc_fiscal_outro", self.doc_fiscal_outro),
                ("doc_outro", self.doc_outro),
            ],
        )
        return self


class TribIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    g_ibscbs: GIBSCBS


class ValoresIBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    g_ree_rep_res: Optional[list[ListaDocIBSCBS]] = Field(default=None, max_length=1000)
    trib: TribIBSCBS


class IBSCBS(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    fin_nfse: Literal["0", "1", "2"]
    tp_nfse_credito: Optional[Literal["01", "05"]] = None
    tp_nfse_debito: Optional[Literal["01", "02", "03", "04", "05", "06"]] = None
    ind_final: Optional[Literal["0", "1"]] = None
    c_ind_op: IBSCBSOperationCode
    tp_oper: Optional[Literal["1", "2", "3", "4", "5"]] = None
    g_ref_nfse: Optional[RefNFSe] = None
    tp_ente_gov: Optional[Literal["1", "2", "3", "4"]] = None
    ind_dest: Literal["0", "1"]
    dest: Optional[DestIBSCBS] = None
    imovel: Optional[ImovelIBSCBS] = None
    valores: ValoresIBSCBS

    @field_validator("c_ind_op", mode="before")
    @classmethod
    def validate_c_ind_op(cls, value: object) -> str:
        if not isinstance(value, str):
            raise NFSeValidationError("cIndOp inválido (valor redigido).")

        if not _C_IND_OP_PATTERN.fullmatch(value):
            raise NFSeValidationError(
                f"cIndOp inválido ({_redacted_repr('valor', value)})."
            )

        if value == "080101":
            raise NFSeValidationError("cIndOp exclusivo de NFS-e Via.")

        if value not in IBSCBS_C_IND_OP_ALLOWLIST:
            raise NFSeValidationError(
                f"cIndOp inválido ({_redacted_repr('valor', value)})."
            )

        return value

    @field_validator("g_ref_nfse")
    @classmethod
    def validate_ref_nfse(cls, value: Optional[RefNFSe]) -> Optional[RefNFSe]:
        if value is not None and len(value.ref_nfse) > 99:
            raise ValueError("gRefNFSe suporta no máximo 99 referências.")
        return value

    @model_validator(mode="after")
    def validate_fin_nfse_rules(self) -> "IBSCBS":
        if self.fin_nfse == "0":
            if self.tp_nfse_credito is not None or self.tp_nfse_debito is not None:
                raise ValueError(
                    "tpNFSeCredito e tpNFSeDebito são proibidos para finNFSe 0."
                )

        if self.fin_nfse == "1":
            if self.tp_nfse_credito is None:
                raise ValueError("tpNFSeCredito é obrigatório para finNFSe 1.")
            if self.tp_nfse_debito is not None:
                raise ValueError("tpNFSeDebito é proibido para finNFSe 1.")

        if self.fin_nfse == "2":
            if self.tp_nfse_debito is None:
                raise ValueError("tpNFSeDebito é obrigatório para finNFSe 2.")
            if self.tp_nfse_credito is not None:
                raise ValueError("tpNFSeCredito é proibido para finNFSe 2.")

        if self.tp_oper in {"2", "3"} and self.g_ref_nfse is None:
            raise ValueError("gRefNFSe é obrigatório para tpOper 2/3.")

        if self.tp_oper in {"1", "4", "5"} and self.g_ref_nfse is not None:
            raise ValueError("gRefNFSe é proibido para tpOper 1/4/5.")

        if self.fin_nfse == "1":
            if self.tp_nfse_credito == "01":
                if self.g_ref_nfse is None:
                    raise ValueError("gRefNFSe é obrigatório para tpNFSeCredito 01.")
                if len(self.g_ref_nfse.ref_nfse) != 1:
                    raise ValueError("tpNFSeCredito 01 permite apenas uma refNFSe.")
            elif self.tp_nfse_credito == "05" and self.g_ref_nfse is not None:
                raise ValueError("gRefNFSe é proibido para tpNFSeCredito 05.")

        if self.fin_nfse == "2":
            if self.tp_nfse_debito in {"03", "04"}:
                if self.g_ref_nfse is None:
                    raise ValueError("gRefNFSe é obrigatório para tpNFSeDebito 03/04.")
                if self.tp_nfse_debito == "04" and len(self.g_ref_nfse.ref_nfse) != 1:
                    raise ValueError("tpNFSeDebito 04 permite apenas uma refNFSe.")
            elif (
                self.tp_nfse_debito in {"01", "02", "05", "06"}
                and self.g_ref_nfse is not None
            ):
                raise ValueError("gRefNFSe é proibido para tpNFSeDebito 01/02/05/06.")

        return self


IBSCBS.model_rebuild()
ListaDocFornecIBSCBS.model_rebuild()
ListaDocDFeIBSCBS.model_rebuild()
ListaDocFiscalOutroIBSCBS.model_rebuild()
ListaDocOutroIBSCBS.model_rebuild()
ListaDocIBSCBS.model_rebuild()
DestIBSCBS.model_rebuild()
ImovelIBSCBS.model_rebuild()
RefNFSe.model_rebuild()
ValoresIBSCBS.model_rebuild()
TribIBSCBS.model_rebuild()
GIBSCBS.model_rebuild()
GTribRegularIBSCBS.model_rebuild()
GDifIBSCBS.model_rebuild()
