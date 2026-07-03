# pynfse-nacional

Biblioteca Python para integração com a API do NFSe Nacional (Padrão Nacional).

Documentação completa: [roberto-mello.github.io/pynfse-nacional](https://roberto-mello.github.io/pynfse-nacional/)

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
- Suporte a IBSCBS na DPS, na resposta da API e no DANFSe
- Download e geração local do DANFSe em PDF
- Consulta de convênio municipal
- Validação de campos com mensagens em português
- Códigos numéricos estáveis por categoria para erros da biblioteca

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
    cnpj="11222333000181",
    inscricao_municipal="12345",
    razao_social="Empresa Exemplo LTDA",
    nome_fantasia="Empresa Exemplo",
    endereco=endereco_prestador,
    email="contato@empresa.com",
    telefone="11999999999",
)

# Criar tomador (cliente)
tomador = Tomador(
    cpf="52998224725",
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
    op_simp_nac="3",
    reg_ap_trib_sn="1",
    reg_ap_ibs_cbs_sn="1",
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

Para contribuintes optantes pelo Simples Nacional com IBSCBS, informe o grupo
`ibscbs` e mantenha os campos de apuração compatíveis com `op_simp_nac`:
`"3"` e `"4"` exigem `reg_ap_trib_sn` e `reg_ap_ibs_cbs_sn`; `"1"` e `"2"`
não devem preenchê-los. Os valores `cst` e `c_class_trib` abaixo são apenas
exemplos válidos no schema:

```python
from pynfse_nacional import GIBSCBS, IBSCBS, TribIBSCBS, ValoresIBSCBS

dps.ibscbs = IBSCBS(
    fin_nfse="0",
    c_ind_op="020101",
    ind_dest="0",
    valores=ValoresIBSCBS(
        trib=TribIBSCBS(
            g_ibscbs=GIBSCBS(
                cst="001",
                c_class_trib="123456",
            )
        )
    ),
)
```

## Erros e Códigos

A biblioteca exporta `ErrorCode` no pacote principal para facilitar o tratamento
programático dos erros:

```python
from pynfse_nacional import ErrorCode, NFSeAPIError

try:
    client.query_nfse("123")
except NFSeAPIError as error:
    if error.code == ErrorCode.COMMUNICATION_TIMEOUT:
        ...
    print(error.message)
```

- `error.code` é o identificador estável para automação
- `error.message` é a mensagem em Português do Brasil
- as mensagens geradas pela biblioteca ficam centralizadas internamente

Veja o apêndice de documentação para a lista completa dos códigos por faixa e
categoria.

## Referência da API

### NFSeClient

Cliente principal para a API do NFSe Nacional.

**Emissão e Consulta de NFSe:**

- `submit_dps(dps: DPS) -> NFSeResponse` - Envia DPS e recebe NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Consulta NFSe pela chave de acesso
- `query_nfse_by_dps(id_dps: str) -> NFSeQueryResult` - Recupera a NFSe pelo identificador da DPS
- `has_nfse_by_dps(id_dps: str) -> bool` - Verifica se a DPS já gerou uma NFSe
- `recover_nfse_by_dps(id_dps: str) -> RecoveryOutcome` - Recuperação simplificada combinando `has_nfse_by_dps` e `query_nfse_by_dps` (ver abaixo)
- `download_danfse(chave_acesso: str) -> bytes` - Baixa o DANFSe em PDF
- `cancel_nfse(chave_acesso, reason, codigo_motivo=1, cnpj_prestador="") -> EventResponse` - Cancela NFSe
- `substitute_nfse(chave_acesso_original, new_dps, motivo, codigo_motivo) -> NFSeResponse` - Substitui NFSe existente

**Consulta por DPS:**

Se você só tiver o identificador da DPS, use a consulta por DPS para recuperar
a chave de acesso e depois obter os dados completos da NFSe:

```python
dps_id = dps.build_dps_id()

result = client.query_nfse_by_dps(dps_id)

print(result.chave_acesso)
print(result.nfse_number)
```

Se você só quiser verificar se a NFSe já foi gerada:

```python
if client.has_nfse_by_dps(dps_id):
    print("NFSe já gerada")
```

`build_dps()` usa o mesmo identificador para montar o XML, mas não grava o
valor de volta em `dps.id_dps`. Guarde o `dps_id` se quiser consultar depois.

**Recuperação Simplificada de NFSe por DPS:**

Quando o `submit_dps` falha ou a SEFIN já processou a DPS mas a aplicação
perdeu a `chave_acesso` (ex.: resposta duplicada `e0014`, ou falha de
transporte após a SEFIN aceitar a DPS), use `recover_nfse_by_dps` para tentar
recuperar o estado da NFSe em uma única chamada. O retorno é um
`RecoveryOutcome` (dataclass imutável) com `status` com três valores possíveis:

- `"success"`: a NFSe existe remotamente; `result` (um `NFSeQueryResult`)
  contém os dados completos para persistir.
- `"processing"`: a DPS foi recebida mas a NFSe ainda não foi emitida (a SEFIN
  retornou `202 / 404 / 409` na consulta). A aplicação deve manter o
  registro como retryable em vez de marcar como falha permanente.
- `"error"`: a própria consulta falhou (transporte ou erro de API); `error`
  contém o `NFSeAPIError`. A aplicação deve apresentar o erro original do
  submit.

Exemplo:

```python
from pynfse_nacional import RecoveryOutcome

outcome = client.recover_nfse_by_dps(dps_id)

if outcome.status == "success":
    result = outcome.result  # NFSeQueryResult
    print(result.chave_acesso, result.nfse_number)
elif outcome.status == "processing":
    # DPS aceita, NFSe ainda não emitida — tentar novamente depois
    ...
else:  # "error"
    # recovery falhou — apresentar o erro original do submit
    print(outcome.error.code, outcome.error.message)
```

`recover_nfse_by_dps()` é mais eficiente que `query_nfse_by_dps()` no caminho de
"ainda não está pronto" pois faz primeiro um `HEAD /dps/{id}` (que só retorna
o status, sem corpo) via `has_nfse_by_dps()`. Só quando o HEAD confirma que a
NFSe existe é que ele parte para o `GET` completo e decodifica o XML. Assim,
quando a DPS ainda não gerou NFSe, isso evita tentar baixar e processar um XML
que não existe.

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

### Cancelando NFSe

Para cancelar uma NFSe emitida, utilize a chave de acesso e o CNPJ do prestador (obrigatório para identificação junto à SEFIN):

```python
result = client.cancel_nfse(
    chave_acesso="13026032211222333000181000000000010626030410654816",
    reason="Erro na emissão do serviço prestado",
    codigo_motivo=1,          # 1=erro na emissão, 2=serviço não prestado, 4=duplicidade
    cnpj_prestador="11222333000181",  # CNPJ do prestador, somente dígitos
)

if result.success:
    print(f"NFS-e cancelada. Protocolo: {result.protocolo}")
else:
    print(f"Erro ao cancelar: [{result.error_code}] {result.error_message}")
```

**Códigos de motivo (`codigo_motivo`):**

| Código | Descrição |
|--------|-----------|
| 1 | Erro na emissão |
| 2 | Serviço não prestado |
| 4 | Duplicidade |

**Observações:**
- O `cnpj_prestador` é obrigatório — sem ele, a SEFIN retorna HTTP 404.
- Alguns municípios configuram um valor máximo para cancelamento via API. Se o valor da NFS-e exceder esse limite, o cancelamento deve ser feito pelo portal municipal.
- O prazo para cancelamento varia por município.

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
- `IBSCBS` - Dados do leiaute IBSCBS da DPS

## Ambientes

- **Homologação**: `sefin.producaorestrita.nfse.gov.br`
- **Produção**: `sefin.nfse.gov.br`

## Documentação

### Documentação Online

- [Site da documentação](https://roberto-mello.github.io/pynfse-nacional/) - Guias, referência da API e apêndice

### Documentação Oficial

- [Portal NFSe Nacional](https://www.gov.br/nfse) - Portal principal do sistema nacional
- [Documentação Técnica](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/) - Biblioteca de documentos técnicos
- [Documentação Atual](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual) - Versão mais recente dos documentos
- [Schemas XSD](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip) - Esquemas XML para validação
- [Anexo C - IBSCBS / INDOP](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/anexo_c-indop_ibscbs-snnfse-v1-01-20260122.xlsx) - Tabela oficial de `cIndOp` para IBSCBS
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
- Stable numeric error codes grouped by category

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
    cnpj="11222333000181",
    inscricao_municipal="12345",
    razao_social="Example Company LTDA",
    nome_fantasia="Example Company",
    endereco=provider_address,
    email="contact@company.com",
    telefone="11999999999",
)

# Create recipient (client)
tomador = Tomador(
    cpf="52998224725",
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
    op_simp_nac="3",
    reg_ap_trib_sn="1",
    reg_ap_ibs_cbs_sn="1",
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

For Simples Nacional providers using IBSCBS, include the `ibscbs` group and
keep the apportionment fields aligned with `op_simp_nac`: `"3"` and `"4"`
require `reg_ap_trib_sn` and `reg_ap_ibs_cbs_sn`; `"1"` and `"2"` must leave
them unset. The `cst` and `c_class_trib` values below are just schema-valid
examples:

```python
from pynfse_nacional import GIBSCBS, IBSCBS, TribIBSCBS, ValoresIBSCBS

dps.ibscbs = IBSCBS(
    fin_nfse="0",
    c_ind_op="020101",
    ind_dest="0",
    valores=ValoresIBSCBS(
        trib=TribIBSCBS(
            g_ibscbs=GIBSCBS(
                cst="001",
                c_class_trib="123456",
            )
        )
    ),
)
```

### Errors and Codes

The library exports `ErrorCode` from the top-level package so callers can
branch on stable numeric identifiers:

```python
from pynfse_nacional import ErrorCode, NFSeAPIError

try:
    client.query_nfse("123")
except NFSeAPIError as error:
    if error.code == ErrorCode.COMMUNICATION_TIMEOUT:
        ...
    print(error.message)
```

- `error.code` is the stable value for programmatic handling
- `error.message` is the human-readable message in Brazilian Portuguese
- library-generated messages are centralized internally

### API Reference

#### NFSeClient

Main client for NFSe Nacional API.

**NFSe Issuance and Query:**

- `submit_dps(dps: DPS) -> NFSeResponse` - Submit DPS and receive NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Query NFSe by access key
- `query_nfse_by_dps(id_dps: str) -> NFSeQueryResult` - Recover NFSe by DPS identifier
- `has_nfse_by_dps(id_dps: str) -> bool` - Check whether a DPS already generated an NFSe
- `recover_nfse_by_dps(id_dps: str) -> RecoveryOutcome` - High-level recovery combining `has_nfse_by_dps` + `query_nfse_by_dps` for the duplicate / lost-`chave_acesso` path; returns a frozen `RecoveryOutcome` with `status="success" | "processing" | "error"` (see Portuguese section for a full example)
- `download_danfse(chave_acesso: str) -> bytes` - Download DANFSe PDF
- `cancel_nfse(chave_acesso, reason, codigo_motivo=1, cnpj_prestador="") -> EventResponse` - Cancel NFSe
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

#### Cancelling NFSe

To cancel an issued NFSe, provide the access key and the provider's CNPJ (required by SEFIN to identify the requester):

```python
result = client.cancel_nfse(
    chave_acesso="13026032211222333000181000000000010626030410654816",
    reason="Erro na emissão do serviço prestado",
    codigo_motivo=1,           # 1=issuance error, 2=service not rendered, 4=duplicate
    cnpj_prestador="11222333000181",   # Provider CNPJ, digits only
)

if result.success:
    print(f"NFSe cancelled. Protocol: {result.protocolo}")
else:
    print(f"Cancellation failed: [{result.error_code}] {result.error_message}")
```

**Cancellation reason codes (`codigo_motivo`):**

| Code | Description |
|------|-------------|
| 1 | Issuance error |
| 2 | Service not rendered |
| 4 | Duplicate |

**Notes:**
- `cnpj_prestador` is required — without it SEFIN returns HTTP 404.
- Some municipalities configure a maximum cancellation value via API. If the NFSe value exceeds that limit, cancellation must be done through the municipal portal.

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
- `IBSCBS` - IBSCBS layout data for DPS

### Environments

- **Homologacao** (staging): `sefin.producaorestrita.nfse.gov.br`
- **Producao** (production): `sefin.nfse.gov.br`

### Documentation

- [Documentation site](https://roberto-mello.github.io/pynfse-nacional/) - Guides, API reference, and appendix

- [NFSe Nacional Portal](https://www.gov.br/nfse)
- [Technical Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)
- [All Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual)
- [XSD Schemas](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260209.zip)
- [IBSCBS Annex / INDOP](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/anexo_c-indop_ibscbs-snnfse-v1-01-20260122.xlsx) - Official `cIndOp` table for IBSCBS
- [API Docs](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao)

### Community Resources

- Reference Implementation: https://github.com/nfe/poc-nfse-nacional
- PHP Library: https://github.com/nfse-nacional/nfse-php
- IBGE Municipality Codes (CSV): https://github.com/kelvins/municipios-brasileiros

### License

GNU Affero General Public License v3 (AGPL-3.0)
