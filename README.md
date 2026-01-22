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
- Consulta de parametros municipais e servicos aderidos
- Validacao de campos com mensagens em portugues

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
from datetime import datetime
from decimal import Decimal

from pynfse_nacional import NFSeClient, DPS, Prestador, Tomador, Servico, Endereco

# Criar endereco do prestador
endereco_prestador = Endereco(
    logradouro="Rua Exemplo",
    numero="100",
    complemento="Sala 1",
    bairro="Centro",
    codigo_municipio=3550308,  # Codigo IBGE do municipio
    uf="SP",
    cep="01310100",
)

# Criar prestador (emissor da nota)
prestador = Prestador(
    cnpj="12345678000199",
    inscricao_municipal="12345",
    razao_social="Empresa Exemplo LTDA",
    nome_fantasia="Empresa Exemplo",
    endereco=endereco_prestador,
    email="contato@empresa.com",
    telefone="11999999999",
)

# Criar tomador (cliente)
tomador = Tomador(
    cpf="12345678901",
    razao_social="Joao da Silva",
    endereco=Endereco(
        logradouro="Av. Brasil",
        numero="500",
        bairro="Jardins",
        codigo_municipio=3550308,
        uf="SP",
        cep="01430001",
    ),
)

# Criar servico
servico = Servico(
    codigo_lc116="04.03.01",  # Codigo completo com subitem (XX.XX.XX)
    discriminacao="Consulta medica em consultorio",
    valor_servicos=Decimal("500.00"),
    iss_retido=False,
    aliquota_simples=Decimal("18.83"),  # Para Simples Nacional
)

# Criar DPS (nao definir id_dps - sera gerado automaticamente)
dps = DPS(
    serie="900",
    numero=1,
    competencia="2026-01",
    data_emissao=datetime.now(),
    prestador=prestador,
    tomador=tomador,
    servico=servico,
    regime_tributario="simples_nacional",
    optante_simples=True,
    incentivador_cultural=False,
)

# Inicializar cliente com certificado
client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="sua-senha",
    ambiente="homologacao",  # ou "producao"
)

# Enviar e obter NFSe
response = client.submit_dps(dps)

if response.success:
    print(f"NFSe emitida: {response.nfse_number}")
    print(f"Chave de acesso: {response.chave_acesso}")
else:
    print(f"Erro: {response.error_message}")
```

## Referencia da API

### NFSeClient

Cliente principal para a API do NFSe Nacional.

**Emissao e Consulta de NFSe:**

- `submit_dps(dps: DPS) -> NFSeResponse` - Envia DPS e recebe NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Consulta NFSe pela chave de acesso
- `download_danfse(chave_acesso: str) -> bytes` - Baixa o DANFSe em PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancela NFSe

**Consulta de Parametros Municipais:**

- `query_parametros_municipais(codigo_municipio: int) -> ParametrosMunicipais` - Consulta parametros e servicos aderidos por um municipio
- `query_servico_municipal(codigo_municipio: int, codigo_servico: str) -> ServicoMunicipal` - Verifica se um servico especifico esta aderido
- `listar_servicos_aderidos(codigo_municipio: int) -> list[ServicoMunicipal]` - Lista todos os servicos aderidos pelo municipio

### Consultando Servicos Aderidos

Antes de emitir uma NFSe, verifique se o municipio aderiu ao codigo de servico:

```python
# Verificar se um codigo de servico esta aderido
servico = client.query_servico_municipal(1302603, "040301")  # Manaus

if servico.aderido:
    print(f"Servico {servico.codigo_servico} aderido")
    print(f"Aliquota: {servico.aliquota}%")
else:
    print("Servico nao aderido pelo municipio")

# Listar todos os servicos aderidos
servicos = client.listar_servicos_aderidos(1302603)

for s in servicos:
    print(f"{s.codigo_servico}: {s.descricao}")
```

### Modelos

- `DPS` - Declaracao de prestacao de servicos
- `Prestador` - Prestador de servicos (emissor)
- `Tomador` - Tomador de servicos
- `Servico` - Detalhes do servico
- `ParametrosMunicipais` - Parametros de um municipio (adesao, servicos)
- `ServicoMunicipal` - Informacoes de um servico aderido

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
- Codigos IBGE dos Municipios (CSV): https://github.com/kelvins/municipios-brasileiros

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
- Municipal parameters and adhered services query
- Field validation with Portuguese error messages

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
from datetime import datetime
from decimal import Decimal

from pynfse_nacional import NFSeClient, DPS, Prestador, Tomador, Servico, Endereco

# Create provider address
provider_address = Endereco(
    logradouro="Rua Exemplo",
    numero="100",
    complemento="Sala 1",
    bairro="Centro",
    codigo_municipio=3550308,  # IBGE municipality code
    uf="SP",
    cep="01310100",
)

# Create provider (invoice issuer)
prestador = Prestador(
    cnpj="12345678000199",
    inscricao_municipal="12345",
    razao_social="Example Company LTDA",
    nome_fantasia="Example Company",
    endereco=provider_address,
    email="contact@company.com",
    telefone="11999999999",
)

# Create recipient (client)
tomador = Tomador(
    cpf="12345678901",
    razao_social="John Smith",
    endereco=Endereco(
        logradouro="Av. Brasil",
        numero="500",
        bairro="Jardins",
        codigo_municipio=3550308,
        uf="SP",
        cep="01430001",
    ),
)

# Create service
servico = Servico(
    codigo_lc116="04.03.01",  # Full code with subitem (XX.XX.XX)
    discriminacao="Medical consultation",
    valor_servicos=Decimal("500.00"),
    iss_retido=False,
    aliquota_simples=Decimal("18.83"),  # For Simples Nacional
)

# Create DPS (do NOT set id_dps - it will be auto-generated)
dps = DPS(
    serie="900",
    numero=1,
    competencia="2026-01",
    data_emissao=datetime.now(),
    prestador=prestador,
    tomador=tomador,
    servico=servico,
    regime_tributario="simples_nacional",
    optante_simples=True,
    incentivador_cultural=False,
)

# Initialize client with certificate
client = NFSeClient(
    cert_path="/path/to/certificate.pfx",
    cert_password="your-password",
    ambiente="homologacao",  # or "producao"
)

# Submit and get NFSe
response = client.submit_dps(dps)

if response.success:
    print(f"NFSe issued: {response.nfse_number}")
    print(f"Access key: {response.chave_acesso}")
else:
    print(f"Error: {response.error_message}")
```

### API Reference

#### NFSeClient

Main client for NFSe Nacional API.

**NFSe Issuance and Query:**

- `submit_dps(dps: DPS) -> NFSeResponse` - Submit DPS and receive NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Query NFSe by access key
- `download_danfse(chave_acesso: str) -> bytes` - Download DANFSe PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancel NFSe

**Municipal Parameters Query:**

- `query_parametros_municipais(codigo_municipio: int) -> ParametrosMunicipais` - Query parameters and adhered services for a municipality
- `query_servico_municipal(codigo_municipio: int, codigo_servico: str) -> ServicoMunicipal` - Check if a specific service is adhered
- `listar_servicos_aderidos(codigo_municipio: int) -> list[ServicoMunicipal]` - List all adhered services for a municipality

#### Querying Adhered Services

Before issuing an NFSe, check if the municipality has adhered to the service code:

```python
# Check if a service code is adhered
servico = client.query_servico_municipal(1302603, "040301")  # Manaus

if servico.aderido:
    print(f"Service {servico.codigo_servico} is adhered")
    print(f"Tax rate: {servico.aliquota}%")
else:
    print("Service not adhered by the municipality")

# List all adhered services
servicos = client.listar_servicos_aderidos(1302603)

for s in servicos:
    print(f"{s.codigo_servico}: {s.descricao}")
```

#### Models

- `DPS` - Service declaration
- `Prestador` - Service provider (issuer)
- `Tomador` - Service recipient
- `Servico` - Service details
- `ParametrosMunicipais` - Municipality parameters (adherence, services)
- `ServicoMunicipal` - Adhered service information

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
- IBGE Municipality Codes (CSV): https://github.com/kelvins/municipios-brasileiros

### License

MIT License
