import re
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    codigo_municipio: int = Field(..., description="IBGE city code")
    uf: str
    cep: str


class Prestador(BaseModel):
    cnpj: str
    inscricao_municipal: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    endereco: Endereco
    email: Optional[str] = None
    telefone: Optional[str] = None


class Tomador(BaseModel):
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    razao_social: str
    endereco: Optional[Endereco] = None
    email: Optional[str] = None
    telefone: Optional[str] = None


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
    codigo_cnae: Optional[str] = None
    codigo_lc116: str = Field(..., description="Item da lista de servicos LC 116 (ex: 4.03.03)")
    codigo_tributacao_municipal: Optional[str] = Field(None, description="Codigo tributacao municipal")
    codigo_nbs: Optional[str] = Field(None, description="Codigo NBS do servico")
    discriminacao: str
    valor_servicos: Decimal
    iss_retido: bool = False
    aliquota_iss: Optional[Decimal] = None
    aliquota_simples: Optional[Decimal] = Field(None, description="Aliquota Simples Nacional (ex: 18.83)")
    valor_deducoes: Decimal = Decimal("0.00")
    valor_pis: Decimal = Decimal("0.00")
    valor_cofins: Decimal = Decimal("0.00")
    valor_inss: Decimal = Decimal("0.00")
    valor_ir: Decimal = Decimal("0.00")
    valor_csll: Decimal = Decimal("0.00")


class DPS(BaseModel):
    """Declaracao de Prestacao de Servicos."""

    id_dps: Optional[str] = Field(None, description="DPS ID (auto-generated if not provided)")
    serie: str = Field(default="900", description="Serie must be numeric (1-5 digits)")
    numero: int
    competencia: str = Field(..., description="YYYY-MM format")
    data_emissao: datetime
    prestador: Prestador
    tomador: Tomador
    servico: Servico
    regime_tributario: str = Field(
        ..., description="simples_nacional|simples_excesso|normal|mei"
    )
    optante_simples: bool = False
    incentivador_cultural: bool = False

    @field_validator("serie")
    @classmethod
    def validate_serie(cls, v: str) -> str:
        """Validate serie is numeric (XSD pattern: ^0{0,4}\\d{1,5}$)."""

        if not re.match(r"^0{0,4}\d{1,5}$", v):
            raise ValueError(
                f"serie must be numeric (1-5 digits), got '{v}'. "
                "Use values like '1', '900', '00001'. Alphabetic series like 'NF' are not allowed."
            )

        return v

    @field_validator("id_dps")
    @classmethod
    def validate_id_dps(cls, v: Optional[str]) -> Optional[str]:
        """Validate id_dps format if provided (XSD pattern: DPS[0-9]{42})."""

        if v is None:
            return v

        if not re.match(r"^DPS[0-9]{42}$", v):
            raise ValueError(
                f"id_dps must match pattern 'DPS' + 42 digits (45 chars total), got '{v}' ({len(v)} chars). "
                "Format: DPS + cLocEmi(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15). "
                "Leave id_dps unset to auto-generate."
            )

        return v


class NFSeResponse(BaseModel):
    """Response from NFSe Nacional API after DPS submission."""

    success: bool
    chave_acesso: Optional[str] = None
    nfse_number: Optional[str] = None
    nfse_xml_gzip_b64: Optional[str] = Field(None, description="Base64-encoded gzipped NFSe XML from API")
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
    xml_original: Optional[str] = Field(None, description="Original signed XML (Base64)")
    data_cancelamento: Optional[datetime] = None
    motivo_cancelamento: Optional[str] = None
