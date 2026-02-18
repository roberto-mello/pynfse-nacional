# pynfse-nacional

Biblioteca Python para integração com a API do NFSe Nacional (Padrão Nacional).

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Início Rápido](#início-rápido)
- [Referência da API](#referência-da-api)
- [Ambientes](#ambientes)
- [Documentação](#documentação)
- [Licença](#licença)
- [English Version](#english-version)

## Visão Geral

Esta biblioteca fornece um cliente para interagir com a API do NFSe Nacional (SEFIN Nacional), que se tornou obrigatória para todos os municípios brasileiros a partir de janeiro de 2026.

## Funcionalidades

- Autenticação mTLS com certificados ICP-Brasil A1/A3
- Geração de XML da DPS (Declaração de Prestação de Serviços)
- Assinatura digital de XML (XMLDSIG)
- Compressão GZip e codificação Base64
- Emissão, consulta, cancelamento e substituição de NFSe
- Download e geração local do DANFSe em PDF
- Consulta de convênio municipal
- Validação de campos com mensagens em português

## Instalação

```bash
uv add pynfse-nacional
```

Ou com pip:

```bash
pip install pynfse-nacional
```

Para geração local de PDF (DANFSe):

```bash
uv add "pynfse-nacional[pdf]"
```

## Início Rápido

```python
from datetime import datetime
from decimal import Decimal

from pynfse_nacional import NFSeClient, DPS, Prestador, Tomador, Servico, Endereco

# Criar endereço do prestador
endereco_prestador = Endereco(
    logradouro="Rua Exemplo",
    numero="100",
    complemento="Sala 1",
    bairro="Centro",
    codigo_municipio=3550308,  # Código IBGE do município
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

# Criar serviço
servico = Servico(
    codigo_lc116="04.03.01",  # Código completo com subitem (XX.XX.XX)
    discriminacao="Consulta médica em consultório",
    valor_servicos=Decimal("500.00"),
    iss_retido=False,
    aliquota_simples=Decimal("18.83"),  # Para Simples Nacional
)

# Criar DPS (não definir id_dps - será gerado automaticamente)
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

## Referência da API

### NFSeClient

Cliente principal para a API do NFSe Nacional.

**Emissão e Consulta de NFSe:**

- `submit_dps(dps: DPS) -> NFSeResponse` - Envia DPS e recebe NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Consulta NFSe pela chave de acesso
- `download_danfse(chave_acesso: str) -> bytes` - Baixa o DANFSe em PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancela NFSe
- `substitute_nfse(chave_acesso_original, new_dps, motivo, codigo_motivo) -> NFSeResponse` - Substitui NFSe existente

**Consulta de Convênio Municipal:**

- `query_convenio_municipal(codigo_municipio) -> ConvenioMunicipal` - Consulta se município tem convênio com o sistema nacional

### Verificando Convênio Municipal

Antes de emitir uma NFSe, verifique se o município tem convênio com o sistema nacional:

```python
# Verificar se o município tem convênio
convenio = client.query_convenio_municipal(1302603)

if convenio.aderido:
    print("Município tem convênio com o sistema nacional")
    print(f"Dados: {convenio.raw_data}")
else:
    print("Município NÃO tem convênio")
```

**Nota:** A API de parametrização (alíquotas por serviço) está com problemas no ambiente de homologação. Apenas a consulta de convênio municipal está disponível.

### Substituindo NFSe

Para corrigir informações em uma NFSe já emitida, você pode substituí-la por uma nova:

```python
from datetime import datetime
from decimal import Decimal

# Criar novo DPS com as informações corrigidas
new_dps = DPS(
    serie="900",
    numero=2,  # Novo número sequencial
    competencia="2026-01",
    data_emissao=datetime.now(),
    prestador=prestador,
    tomador=tomador,
    servico=Servico(
        codigo_lc116="04.03.01",
        discriminacao="Descrição corrigida do serviço prestado",  # Corrigido
        valor_servicos=Decimal("500.00"),
    ),
    regime_tributario="simples_nacional",
)

# Substituir a NFSe original
response = client.substitute_nfse(
    chave_acesso_original="12345678901234567890123456789012345678901234567890",
    new_dps=new_dps,
    motivo="Correção da descrição do serviço prestado",
    codigo_motivo=99,  # 99 = outros
)

if response.success:
    print(f"NFSe substituta emitida: {response.nfse_number}")
    print(f"Nova chave de acesso: {response.chave_acesso}")
else:
    print(f"Erro: {response.error_message}")
```

**Regras de substituição:**
- A substituição deve ser feita em até 35 dias após a emissão original
- Não é permitido substituir NFSe onde o tomador não foi identificado
- Não é permitido alterar o tomador para outra pessoa/empresa
- O motivo deve ter entre 15 e 255 caracteres

### Gerando DANFSe (PDF)

A biblioteca permite gerar o DANFSe localmente a partir do XML da NFSe:

```python
from pynfse_nacional.pdf_generator import (
    generate_danfse_from_base64,
    generate_danfse_from_xml,
    HeaderConfig,
)

# Apos emitir a NFSe, gerar PDF a partir da resposta
response = client.submit_dps(dps)

if response.success:
    # Gerar PDF a partir do XML comprimido retornado pela API
    pdf_bytes = generate_danfse_from_base64(
        nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
        output_path="/caminho/para/danfse.pdf",  # Opcional - salva em arquivo
    )

    # Ou gerar a partir de XML string
    pdf_bytes = generate_danfse_from_xml(
        xml_content=response.xml_nfse,
        output_path="/caminho/para/danfse.pdf",
    )
```

**Com cabeçalho personalizado (logo da empresa):**

```python
header = HeaderConfig(
    image_path="/caminho/para/logo.png",
    title="Nome da Empresa",
    subtitle="Serviços Médicos",
    phone="(11) 99999-9999",
    email="contato@empresa.com",
)

pdf_bytes = generate_danfse_from_base64(
    nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
    output_path="/caminho/para/danfse.pdf",
    header_config=header,
)
```

### Modelos

- `DPS` - Declaração de prestação de serviços
- `Prestador` - Prestador de serviços (emissor)
- `Tomador` - Tomador de serviços
- `Servico` - Detalhes do serviço
- `ConvenioMunicipal` - Informações de convênio municipal
- `SubstituicaoNFSe` - Informações de substituição de NFSe

## Ambientes

- **Homologação**: `sefin.producaorestrita.nfse.gov.br`
- **Produção**: `sefin.nfse.gov.br`

## Documentação

### Documentação Oficial

- [Portal NFSe Nacional](https://www.gov.br/nfse) - Portal principal do sistema nacional
- [Documentação Técnica](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/) - Biblioteca de documentos técnicos
- [Documentação Atual](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual) - Versão mais recente dos documentos
- [Schemas XSD](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260122.zip) - Esquemas XML para validação
- [APIs - Produção e Homologação](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao) - Endpoints das APIs

### Manuais da API

- [Manual de Contribuintes](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/manual-contribuintes-emissor-publico-api-sistema-nacional-nfs-e-v1-2-out2025.pdf) - Guia para integração via API
- [Manual de Municípios - ADN](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual) - Compartilhamento de dados
- [Manual de Municípios - CNC](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual) - Cadastro Nacional de Contribuintes

### Swagger / OpenAPI

- **Homologação**: `https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/docs/index`
- **Produção**: `https://sefin.nfse.gov.br/API/SefinNacional/docs/index`

### Recursos da Comunidade

- [Implementação de Referência (PoC)](https://github.com/nfe/poc-nfse-nacional) - Projeto oficial de prova de conceito
- [Biblioteca PHP](https://github.com/nfse-nacional/nfse-php) - Implementação em PHP
- [Códigos IBGE dos Municípios](https://github.com/kelvins/municipios-brasileiros) - Lista de municípios em CSV

## Licença

GNU Affero General Public License v3 (AGPL-3.0)

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
- DANFSe PDF download and local generation
- Municipal agreement (convenio) query
- Field validation with Portuguese error messages

### Installation

```bash
uv add pynfse-nacional
```

Or with pip:

```bash
pip install pynfse-nacional
```

For local PDF generation (DANFSe):

```bash
uv add "pynfse-nacional[pdf]"
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
- `substitute_nfse(chave_acesso_original, new_dps, motivo, codigo_motivo) -> NFSeResponse` - Substitute existing NFSe

**Municipal Agreement Query:**

- `query_convenio_municipal(codigo_municipio) -> ConvenioMunicipal` - Query if municipality has agreement with the national system

#### Checking Municipal Agreement

Before issuing an NFSe, check if the municipality has an agreement with the national system:

```python
# Check if the municipality has an agreement
convenio = client.query_convenio_municipal(1302603)

if convenio.aderido:
    print("Municipality has agreement with the national system")
    print(f"Data: {convenio.raw_data}")
else:
    print("Municipality does NOT have agreement")
```

**Note:** The parametrization API (service tax rates) has issues in the homologation environment. Only the municipal agreement query is available.

#### Generating DANFSe (PDF)

The library allows generating DANFSe locally from the NFSe XML:

```python
from pynfse_nacional.pdf_generator import (
    generate_danfse_from_base64,
    generate_danfse_from_xml,
    HeaderConfig,
)

# After issuing the NFSe, generate PDF from the response
response = client.submit_dps(dps)

if response.success:
    # Generate PDF from compressed XML returned by the API
    pdf_bytes = generate_danfse_from_base64(
        nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
        output_path="/path/to/danfse.pdf",  # Optional - saves to file
    )

    # Or generate from XML string
    pdf_bytes = generate_danfse_from_xml(
        xml_content=response.xml_nfse,
        output_path="/path/to/danfse.pdf",
    )
```

**With custom header (company logo):**

```python
header = HeaderConfig(
    image_path="/path/to/logo.png",
    title="Company Name",
    subtitle="Medical Services",
    phone="(11) 99999-9999",
    email="contact@company.com",
)

pdf_bytes = generate_danfse_from_base64(
    nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
    output_path="/path/to/danfse.pdf",
    header_config=header,
)
```

#### Models

- `DPS` - Service declaration
- `Prestador` - Service provider (issuer)
- `Tomador` - Service recipient
- `Servico` - Service details
- `ConvenioMunicipal` - Municipal agreement information
- `SubstituicaoNFSe` - NFSe substitution information

### Environments

- **Homologacao** (staging): `sefin.producaorestrita.nfse.gov.br`
- **Producao** (production): `sefin.nfse.gov.br`

### Documentation

- [NFSe Nacional Portal](https://www.gov.br/nfse)
- [Technical Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)
- [All Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual)
- [XSD Schemas](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260122.zip)
- [API Docs](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao)

### Community Resources

- Reference Implementation: https://github.com/nfe/poc-nfse-nacional
- PHP Library: https://github.com/nfse-nacional/nfse-php
- IBGE Municipality Codes (CSV): https://github.com/kelvins/municipios-brasileiros

### License

GNU Affero General Public License v3 (AGPL-3.0)
