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

# Parametrizacao API URLs (for municipal parameters)
PARAMETRIZACAO_URLS = {
    Ambiente.HOMOLOGACAO: "https://adn.producaorestrita.nfse.gov.br/parametrizacao",
    Ambiente.PRODUCAO: "https://adn.nfse.gov.br/parametrizacao",
}

ENDPOINTS = {
    "submit_dps": "/nfse",
    "query_nfse": "/nfse/{chave}",
    "download_danfse": "/danfse/{chave}",
    "events": "/eventos",
    "parametros_municipais": "/parametros_municipais/{codigo_municipio}",
    "servico_municipal": "/parametros_municipais/{codigo_municipio}/{codigo_servico}",
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
