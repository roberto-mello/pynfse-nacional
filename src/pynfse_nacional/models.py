from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


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
    codigo_cnae: str
    codigo_lc116: str
    discriminacao: str
    valor_servicos: Decimal
    iss_retido: bool = False
    aliquota_iss: Optional[Decimal] = None
    valor_deducoes: Decimal = Decimal("0.00")
    valor_pis: Decimal = Decimal("0.00")
    valor_cofins: Decimal = Decimal("0.00")
    valor_inss: Decimal = Decimal("0.00")
    valor_ir: Decimal = Decimal("0.00")
    valor_csll: Decimal = Decimal("0.00")


class DPS(BaseModel):
    """Declaracao de Prestacao de Servicos."""

    id_dps: str = Field(..., description="Unique DPS identifier: CNPJ + serie + numero")
    serie: str = Field(default="NF")
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


class NFSeResponse(BaseModel):
    """Response from NFSe Nacional API after DPS submission."""

    success: bool
    chave_acesso: Optional[str] = None
    nfse_number: Optional[str] = None
    xml_nfse: Optional[str] = None
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
