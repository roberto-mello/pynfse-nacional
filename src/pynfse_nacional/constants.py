from enum import Enum


class Ambiente(str, Enum):
    HOMOLOGACAO = "homologacao"
    PRODUCAO = "producao"


# Convenience constants
AMBIENTE_HOMOLOGACAO = Ambiente.HOMOLOGACAO
AMBIENTE_PRODUCAO = Ambiente.PRODUCAO

API_URLS = {
    Ambiente.HOMOLOGACAO: "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
    Ambiente.PRODUCAO: "https://sefin.nfse.gov.br/SefinNacional",
}

ENDPOINTS = {
    "submit_dps": "/nfse",
    "query_nfse": "/nfse/{chave}",
    "download_danfse": "/danfse/{chave}",
    "events": "/eventos",
}

# Regime tributario codes
REGIME_SIMPLES_NACIONAL = "1"
REGIME_SIMPLES_EXCESSO = "2"
REGIME_NORMAL = "3"
REGIME_MEI = "4"

# NFSe status codes
STATUS_EMITIDA = "emitida"
STATUS_CANCELADA = "cancelada"
STATUS_SUBSTITUIDA = "substituida"
