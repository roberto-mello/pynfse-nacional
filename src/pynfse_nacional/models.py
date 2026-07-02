import re
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models_ibscbs import IBSCBS

# Valid Brazilian UF codes
VALID_UFS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}


def _validate_cpf_digits(cpf: str) -> bool:
    """Validate CPF check digits."""

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc_digit(cpf_partial: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(cpf_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    d1 = calc_digit(cpf[:9], [10, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc_digit(cpf[:10], [11, 10, 9, 8, 7, 6, 5, 4, 3, 2])

    return cpf[-2:] == f"{d1}{d2}"


def _validate_cnpj_digits(cnpj: str) -> bool:
    """Validate CNPJ check digits."""

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_digit(cnpj_partial: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(cnpj_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    d1 = calc_digit(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc_digit(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])

    return cnpj[-2:] == f"{d1}{d2}"


class Endereco(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    logradouro: str = Field(..., min_length=1, max_length=255)
    numero: str = Field(..., min_length=1, max_length=60)
    complemento: Optional[str] = Field(None, max_length=156)
    bairro: str = Field(..., min_length=1, max_length=60)
    codigo_municipio: int = Field(
        ..., description="Codigo IBGE do municipio (7 digitos)"
    )
    uf: str = Field(..., description="Sigla da UF (ex: SP, RJ, MG)")
    cep: str = Field(..., description="CEP com 8 digitos, sem formatacao")

    @field_validator("codigo_municipio")
    @classmethod
    def validate_codigo_municipio(cls, v: int) -> int:
        """Valida codigo IBGE do municipio (7 digitos)."""

        if not 1000000 <= v <= 9999999:
            raise ValueError("codigo_municipio deve ter 7 dígitos (código IBGE).")

        return v

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        """Valida sigla da UF."""

        v_upper = v.upper()

        if v_upper not in VALID_UFS:
            raise ValueError(
                f"UF inválida. Use uma sigla válida: {', '.join(sorted(VALID_UFS))}"
            )

        return v_upper

    @field_validator("cep")
    @classmethod
    def validate_cep(cls, v: str) -> str:
        """Valida CEP (8 digitos)."""

        cep_clean = re.sub(r"[.\-]", "", v)

        if not re.match(r"^[0-9]{8}$", cep_clean):
            raise ValueError("CEP deve conter 8 dígitos numéricos.")

        return cep_clean


class Prestador(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    cnpj: str = Field(..., description="CNPJ com 14 digitos, sem formatacao")
    inscricao_municipal: Optional[str] = Field(None, min_length=1, max_length=15)
    razao_social: str = Field(..., min_length=1, max_length=300)
    nome_fantasia: Optional[str] = Field(None, max_length=150)
    endereco: Endereco
    email: Optional[str] = Field(None, max_length=80)
    telefone: Optional[str] = Field(None, description="Telefone com 6-20 digitos")

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        """Valida CNPJ (14 digitos com digitos verificadores)."""

        cnpj_clean = re.sub(r"[.\-/]", "", v)

        if not re.match(r"^[0-9]{14}$", cnpj_clean):
            raise ValueError("CNPJ deve conter 14 dígitos numéricos.")

        if not _validate_cnpj_digits(cnpj_clean):
            raise ValueError("CNPJ inválido (dígitos verificadores incorretos).")

        return cnpj_clean

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: Optional[str]) -> Optional[str]:
        """Valida telefone (6-20 digitos)."""

        if v is None:
            return v

        tel_clean = re.sub(r"[+\-() ]", "", v)

        if not re.match(r"^[0-9]{6,20}$", tel_clean):
            raise ValueError("Telefone deve conter entre 6 e 20 dígitos.")

        return tel_clean


class Tomador(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    cpf: Optional[str] = Field(None, description="CPF com 11 digitos, sem formatacao")
    cnpj: Optional[str] = Field(None, description="CNPJ com 14 digitos, sem formatacao")
    razao_social: str = Field(..., min_length=1, max_length=300)
    endereco: Optional[Endereco] = None
    email: Optional[str] = Field(None, max_length=80)
    telefone: Optional[str] = Field(None, description="Telefone com 6-20 digitos")

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Valida CPF (11 digitos com digitos verificadores)."""

        if v is None:
            return v

        cpf_clean = re.sub(r"[.\-]", "", v)

        if not re.match(r"^[0-9]{11}$", cpf_clean):
            raise ValueError("CPF deve conter 11 dígitos numéricos.")

        if not _validate_cpf_digits(cpf_clean):
            raise ValueError("CPF inválido (dígitos verificadores incorretos).")

        return cpf_clean

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: Optional[str]) -> Optional[str]:
        """Valida CNPJ (14 digitos com digitos verificadores)."""

        if v is None:
            return v

        cnpj_clean = re.sub(r"[.\-/]", "", v)

        if not re.match(r"^[0-9]{14}$", cnpj_clean):
            raise ValueError("CNPJ deve conter 14 dígitos numéricos.")

        if not _validate_cnpj_digits(cnpj_clean):
            raise ValueError("CNPJ inválido (dígitos verificadores incorretos).")

        return cnpj_clean

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: Optional[str]) -> Optional[str]:
        """Valida telefone (6-20 digitos)."""

        if v is None:
            return v

        tel_clean = re.sub(r"[+\-() ]", "", v)

        if not re.match(r"^[0-9]{6,20}$", tel_clean):
            raise ValueError("Telefone deve conter entre 6 e 20 dígitos.")

        return tel_clean

    @model_validator(mode="after")
    def validate_cpf_or_cnpj(self) -> "Tomador":
        """Valida que pelo menos CPF ou CNPJ foi informado."""

        if self.cpf is None and self.cnpj is None:
            raise ValueError(
                "Tomador deve ter CPF ou CNPJ informado. "
                "Informe pelo menos um documento de identificacao."
            )

        return self


class ValoresServico(BaseModel):
    """Service values breakdown for NFSe."""

    valor_servicos: Decimal
    valor_deducoes: Decimal = Decimal("0.00")
    valor_pis: Decimal = Decimal("0.00")
    valor_cofins: Decimal = Decimal("0.00")
    valor_inss: Decimal = Decimal("0.00")
    valor_ir: Decimal = Decimal("0.00")
    valor_csll: Decimal = Decimal("0.00")
    valor_iss: Optional[Decimal] = None
    valor_iss_retido: Optional[Decimal] = None
    valor_liquido: Optional[Decimal] = None
    base_calculo: Optional[Decimal] = None
    aliquota: Optional[Decimal] = None


class Servico(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    codigo_cnae: Optional[str] = None
    codigo_lc116: str = Field(
        ...,
        description=(
            "Item da lista de servicos LC 116 com subitem "
            "(ex: '04.03.01', '01.01.01')"
        ),
    )
    codigo_tributacao_municipal: Optional[str] = Field(
        None, description="Codigo tributacao municipal"
    )
    codigo_nbs: Optional[str] = Field(
        None, description="Codigo NBS do servico (9 digitos)"
    )
    discriminacao: str = Field(..., min_length=1, max_length=2000)
    valor_servicos: Decimal
    iss_retido: bool = False
    aliquota_iss: Optional[Decimal] = None
    aliquota_simples: Optional[Decimal] = Field(
        None, description="Aliquota Simples Nacional (ex: 18.83)"
    )
    valor_deducoes: Decimal = Decimal("0.00")
    valor_pis: Decimal = Decimal("0.00")
    valor_cofins: Decimal = Decimal("0.00")
    valor_inss: Decimal = Decimal("0.00")
    valor_ir: Decimal = Decimal("0.00")
    valor_csll: Decimal = Decimal("0.00")

    @field_validator("codigo_lc116")
    @classmethod
    def validate_codigo_lc116(cls, v: str) -> str:
        """Valida codigo LC 116 (deve ter formato XX.XX.XX com subitem)."""

        code_clean = v.replace(".", "")

        if re.match(r"^\d{1,2}\.\d{2}$", v) or re.match(r"^\d{3,4}$", code_clean):
            raise ValueError(
                "codigo_lc116 deve incluir o subitem completo "
                f"(ex: '04.03.01'), recebido: '{v}'. "
                "O formato correto é XX.XX.XX (item.subitem.detalhe). "
                "Consulte a lista de serviços em: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/"
            )

        if not re.match(r"^\d{1,2}\.\d{2}\.\d{2}$", v):
            if re.match(r"^\d{6}$", code_clean):
                return v

            raise ValueError(
                "codigo_lc116 deve estar no formato XX.XX.XX "
                "(ex: '04.03.01')."
            )

        return v

    @field_validator("codigo_nbs")
    @classmethod
    def validate_codigo_nbs(cls, v: Optional[str]) -> Optional[str]:
        """Valida codigo NBS (9 digitos)."""

        if v is None:
            return v

        nbs_clean = v.replace(".", "")

        if not re.match(r"^[0-9]{9}$", nbs_clean):
            raise ValueError("codigo_nbs deve conter 9 dígitos.")

        return v

    @field_validator("valor_servicos")
    @classmethod
    def validate_valor_servicos(cls, v: Decimal) -> Decimal:
        """Valida valor dos servicos (deve ser positivo)."""

        if v <= 0:
            raise ValueError("valor_servicos deve ser maior que zero.")

        return v


class SubstituicaoNFSe(BaseModel):
    """Informacoes de substituicao de NFSe."""

    model_config = ConfigDict(hide_input_in_errors=True)

    chave_nfse_substituida: str = Field(
        ...,
        min_length=50,
        max_length=50,
        description="Chave de acesso da NFSe que sera substituida (50 caracteres)",
    )
    codigo_motivo: int = Field(
        default=99,
        ge=1,
        le=99,
        description="Codigo do motivo da substituicao (1-99, 99=outros)",
    )
    motivo: str = Field(
        ...,
        min_length=15,
        max_length=255,
        description="Descricao do motivo da substituicao (15-255 caracteres)",
    )

    @field_validator("chave_nfse_substituida")
    @classmethod
    def validate_chave_nfse(cls, v: str) -> str:
        """Valida chave de acesso da NFSe (50 digitos)."""

        if not re.match(r"^[0-9]{50}$", v):
            raise ValueError("chave_nfse_substituida deve conter 50 dígitos numéricos.")

        return v


class DPS(BaseModel):
    """Declaracao de Prestacao de Servicos.

    The regApTribSN/regApIBSCBSSN rules follow the IBSCBS regulations:
    E0162, R294, R295, E0710, E0712, and E0713.
    """

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    id_dps: Optional[str] = Field(
        None, description="DPS ID (gerado automaticamente se não informado)"
    )
    serie: str = Field(default="900", description="Série numérica (1-5 dígitos)")
    numero: int = Field(
        ..., gt=0, description="Número do DPS (deve ser maior que zero)"
    )
    competencia: str = Field(..., description="Competência no formato YYYY-MM")
    data_emissao: datetime
    prestador: Prestador
    tomador: Tomador
    servico: Servico
    regime_tributario: str = Field(
        ..., description="simples_nacional|simples_excesso|normal|mei"
    )
    op_simp_nac: Literal["1", "2", "3", "4"] = "1"
    reg_ap_trib_sn: Optional[Literal["1", "2", "3"]] = None
    reg_ap_ibs_cbs_sn: Optional[Literal["1", "2", "3"]] = None
    incentivador_cultural: bool = False
    ibscbs: Optional[IBSCBS] = Field(
        None,
        description="Grupo IBSCBS da DPS (sinaliza o uso do layout RTC)",
    )
    substituicao: Optional[SubstituicaoNFSe] = Field(
        None,
        description=(
            "Informações de substituição "
            "(preencher apenas para substituir NFSe existente)"
        ),
    )

    @field_validator("serie")
    @classmethod
    def validate_serie(cls, v: str) -> str:
        """Valida serie (1-5 digitos numericos)."""

        if not re.match(r"^0{0,4}\d{1,5}$", v):
            raise ValueError("serie deve ser numérica (1-5 dígitos).")

        return v

    @field_validator("id_dps")
    @classmethod
    def validate_id_dps(cls, v: Optional[str]) -> Optional[str]:
        """Valida id_dps se informado (padrao: DPS + 42 digitos)."""

        if v is None:
            return v

        if not re.match(r"^DPS[0-9]{42}$", v):
            raise ValueError("id_dps deve seguir o padrão 'DPS' + 42 dígitos.")

        return v

    def build_dps_id(self) -> str:
        """Build the official DPS identifier from model data."""

        c_loc_emi = str(self.prestador.endereco.codigo_municipio).zfill(7)
        tp_insc = "2"  # CNPJ
        cnpj = self.prestador.cnpj.zfill(14)
        serie = self.serie.zfill(5)
        n_dps = str(self.numero).zfill(15)

        return f"DPS{c_loc_emi}{tp_insc}{cnpj}{serie}{n_dps}"

    @field_validator("competencia")
    @classmethod
    def validate_competencia(cls, v: str) -> str:
        """Valida competencia (formato YYYY-MM)."""

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError(
                "competência deve estar no formato YYYY-MM "
                f"(ex: '2026-01'), recebido: '{v}'."
            )

        return v

    @field_validator("regime_tributario")
    @classmethod
    def validate_regime_tributario(cls, v: str) -> str:
        """Valida regime tributario."""

        valid_regimes = {"simples_nacional", "simples_excesso", "normal", "mei"}

        if v not in valid_regimes:
            raise ValueError(
                f"regime_tributário inválido: '{v}'. "
                f"Use um dos valores: {', '.join(sorted(valid_regimes))}"
            )

        return v

    @model_validator(mode="after")
    def validate_regime_tributario_rules(self) -> "DPS":
        """Validate opSimpNac-dependent regTrib flags."""

        if self.op_simp_nac in {"1", "2"} and self.reg_ap_trib_sn is not None:
            raise ValueError("regApTribSN é proibido para opSimpNac 1/2.")

        if self.op_simp_nac in {"1", "2"} and self.reg_ap_ibs_cbs_sn is not None:
            raise ValueError("regApIBSCBSSN é proibido para opSimpNac 1/2.")

        if self.op_simp_nac in {"3", "4"} and self.reg_ap_trib_sn is None:
            raise ValueError("regApTribSN é obrigatório para opSimpNac 3/4.")

        if self.op_simp_nac in {"3", "4"} and self.reg_ap_ibs_cbs_sn is None:
            raise ValueError("regApIBSCBSSN é obrigatório para opSimpNac 3/4.")

        return self


class NFSeResponse(BaseModel):
    """Response from NFSe Nacional API after DPS submission."""

    success: bool
    chave_acesso: Optional[str] = None
    nfse_number: Optional[str] = None
    nfse_xml_gzip_b64: Optional[str] = Field(
        None, description="Base64-encoded gzipped NFSe XML from API"
    )
    xml_nfse: Optional[str] = Field(None, description="Decoded NFSe XML")
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class EventResponse(BaseModel):
    """Response from event registration (e.g., cancellation)."""

    success: bool
    protocolo: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class NFSeQueryResult(BaseModel):
    """Result of querying an NFSe by access key."""

    chave_acesso: str
    nfse_number: str
    status: str
    data_emissao: datetime
    valor_servicos: Decimal
    prestador_cnpj: str
    tomador_documento: Optional[str] = None
    xml_nfse: Optional[str] = None
    ibscbs: Optional[IBSCBS] = None


class NFSe(BaseModel):
    """Nota Fiscal de Servicos Eletronica - returned by SEFIN after DPS processing."""

    chave_acesso: str = Field(..., description="50-char access key from SEFIN")
    numero: str = Field(..., description="NFSe number assigned by SEFIN")
    codigo_verificacao: Optional[str] = None
    data_emissao: datetime
    competencia: str
    prestador: Prestador
    tomador: Tomador
    servico: Servico
    valores: ValoresServico
    status: str = Field(default="emitida", description="emitida|cancelada|substituida")
    xml_original: Optional[str] = Field(
        None, description="Original signed XML (Base64)"
    )
    ibscbs: Optional[IBSCBS] = None
    data_cancelamento: Optional[datetime] = None
    motivo_cancelamento: Optional[str] = None


class ConvenioMunicipal(BaseModel):
    """Informacoes de convenio de um municipio."""

    codigo_municipio: int = Field(..., description="Codigo IBGE do municipio")
    aderido: bool = Field(default=False, description="Se o municipio tem convenio")
    raw_data: Optional[dict] = Field(None, description="Dados brutos da API")
