# pynfse-nacional

Biblioteca Python para integracao com a API do NFSe Nacional (Padrao Nacional).

## Indice

- [Visao Geral](#visao-geral)
- [Funcionalidades](#funcionalidades)
- [Instalacao](#instalacao)
- [Inicio Rapido](#inicio-rapido)
- [Referencia da API](#referencia-da-api)
- [Ambientes](#ambientes)
- [Documentacao](#documentacao)
- [Licenca](#licenca)
- [English Version](#english-version)

## Visao Geral

Esta biblioteca fornece um cliente para interagir com a API do NFSe Nacional (SEFIN Nacional), que se tornou obrigatoria para todos os municipios brasileiros a partir de janeiro de 2026.

## Funcionalidades

- Autenticacao mTLS com certificados ICP-Brasil A1/A3
- Geracao de XML da DPS (Declaracao de Prestacao de Servicos)
- Assinatura digital de XML (XMLDSIG)
- Compressao GZip e codificacao Base64
- Emissao, consulta e cancelamento de NFSe
- Download do DANFSe em PDF

## Instalacao

```bash
pip install pynfse-nacional
```

Ou instale a partir do codigo fonte:

```bash
pip install git+https://github.com/robmello/pynfse-nacional.git
```

## Inicio Rapido

```python
from pynfse_nacional import NFSeClient, DPS, Prestador, Tomador, Servico

# Inicializar cliente com certificado
client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="sua-senha",
    ambiente="homologacao"  # ou "producao"
)

# Criar DPS
dps = DPS(
    prestador=Prestador(
        cnpj="12345678000199",
        inscricao_municipal="12345",
        # ...
    ),
    tomador=Tomador(
        cpf_cnpj="98765432100",
        # ...
    ),
    servico=Servico(
        valor_servicos=1000.00,
        item_lista_servico="4.01",
        # ...
    ),
)

# Enviar e obter NFSe
response = client.submit_dps(dps)
print(f"NFSe emitida: {response.nfse_number}")
print(f"Chave de acesso: {response.chave_acesso}")
```

## Referencia da API

### NFSeClient

Cliente principal para a API do NFSe Nacional.

- `submit_dps(dps: DPS) -> NFSeResponse` - Envia DPS e recebe NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Consulta NFSe pela chave de acesso
- `download_danfse(chave_acesso: str) -> bytes` - Baixa o DANFSe em PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancela NFSe

### Modelos

- `DPS` - Declaracao de prestacao de servicos
- `Prestador` - Prestador de servicos (emissor)
- `Tomador` - Tomador de servicos
- `Servico` - Detalhes do servico

## Ambientes

- **Homologacao**: `sefin.producaorestrita.nfse.gov.br`
- **Producao**: `sefin.nfse.gov.br`

## Documentacao

- [Portal NFSe Nacional](https://www.gov.br/nfse)
- [Documentacao Tecnica](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)
- [Toda Documentacao](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual)
- [Schemas XSD](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260101.zip)
- [Documentacao das APIs](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao)

### Recursos da Comunidade

- Implementacao de Referencia: https://github.com/nfe/poc-nfse-nacional
- Biblioteca PHP: https://github.com/nfse-nacional/nfse-php

## Licenca

Licenca MIT

---

## English Version

Python library for Brazilian NFSe Nacional (Padrao Nacional) API integration.

### Overview

This library provides a client for interacting with the NFSe Nacional (SEFIN Nacional) API, which became mandatory for all Brazilian municipalities starting January 2026.

### Features

- mTLS authentication with ICP-Brasil A1/A3 certificates
- DPS (Declaracao de Prestacao de Servicos) XML generation
- XML digital signing (XMLDSIG)
- GZip compression and Base64 encoding
- NFSe issuance, query, and cancellation
- DANFSe PDF download

### Installation

```bash
pip install pynfse-nacional
```

Or install from source:

```bash
pip install git+https://github.com/robmello/pynfse-nacional.git
```

### Quick Start

```python
from pynfse_nacional import NFSeClient, DPS, Prestador, Tomador, Servico

# Initialize client with certificate
client = NFSeClient(
    cert_path="/path/to/certificate.pfx",
    cert_password="your-password",
    ambiente="homologacao"  # or "producao"
)

# Create DPS
dps = DPS(
    prestador=Prestador(
        cnpj="12345678000199",
        inscricao_municipal="12345",
        # ...
    ),
    tomador=Tomador(
        cpf_cnpj="98765432100",
        # ...
    ),
    servico=Servico(
        valor_servicos=1000.00,
        item_lista_servico="4.01",
        # ...
    ),
)

# Submit and get NFSe
response = client.submit_dps(dps)
print(f"NFSe issued: {response.nfse_number}")
print(f"Access key: {response.chave_acesso}")
```

### API Reference

#### NFSeClient

Main client for NFSe Nacional API.

- `submit_dps(dps: DPS) -> NFSeResponse` - Submit DPS and receive NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Query NFSe by access key
- `download_danfse(chave_acesso: str) -> bytes` - Download DANFSe PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancel NFSe

#### Models

- `DPS` - Service declaration
- `Prestador` - Service provider (issuer)
- `Tomador` - Service recipient
- `Servico` - Service details

### Environments

- **Homologacao** (staging): `sefin.producaorestrita.nfse.gov.br`
- **Producao** (production): `sefin.nfse.gov.br`

### Documentation

- [NFSe Nacional Portal](https://www.gov.br/nfse)
- [Technical Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)
- [All Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual)
- [XSD Schemas](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260101.zip)
- [API Docs](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao)

### Community Resources

- Reference Implementation: https://github.com/nfe/poc-nfse-nacional
- PHP Library: https://github.com/nfse-nacional/nfse-php

### License

MIT License
