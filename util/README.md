# NFSe Nacional - Scripts Utilitarios

Utilitarios de linha de comando para emissao de NFSe (Nota Fiscal de Servicos Eletronica) atraves do sistema nacional de NFSe do Brasil.

## Indice

- [Configuracao](#configuracao)
- [Uso](#uso)
- [Opcoes de Linha de Comando](#opcoes-de-linha-de-comando)
- [Codigos de Servico LC 116](#codigos-de-servico-lc-116)
- [Codigos de Municipio IBGE](#codigos-de-municipio-ibge)
- [Solucao de Problemas](#solucao-de-problemas)
- [Arquivos](#arquivos)
- [English Version](#english-version)

## Configuracao

### 1. Instalar a biblioteca

```bash
# Instalacao basica
pip install pynfse-nacional

# Com suporte a geracao de PDF
pip install "pynfse-nacional[pdf]"
```

### 2. Configurar seu emissor (prestador)

Copie o arquivo de configuracao de exemplo e preencha os dados da sua empresa:

```bash
cp issuer.example.ini issuer.ini
```

Edite o `issuer.ini` com:
- Caminho do certificado e senha
- Informacoes da empresa (CNPJ, razao social, etc.)
- Endereco
- Configuracoes do regime tributario

### 3. Certificado

Voce precisa de um certificado digital ICP-Brasil A1 (arquivo `.pfx` ou `.p12`) para emitir NFSe. Este e o mesmo certificado usado para assinar outros documentos eletronicos brasileiros (NF-e, CT-e, etc.).

## Uso

### Exemplo Basico

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cpf 12345678901 \
    --tomador-nome "Joao da Silva" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Consultoria em tecnologia da informacao" \
    --servico-valor 1500.00
```

### Exemplo Completo com Endereco do Tomador

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cnpj 99888777000166 \
    --tomador-nome "Empresa Cliente LTDA" \
    --tomador-email "financeiro@cliente.com.br" \
    --tomador-logradouro "Av. Paulista" \
    --tomador-numero "1000" \
    --tomador-complemento "10 andar" \
    --tomador-bairro "Bela Vista" \
    --tomador-municipio 3550308 \
    --tomador-uf SP \
    --tomador-cep 01310100 \
    --servico-codigo "4.03.03" \
    --servico-descricao "Desenvolvimento de software sob encomenda" \
    --servico-valor 5000.00
```

### Ambiente de Producao

Por padrao, o script usa o ambiente de **homologacao** (teste). Para emitir NFSe real em producao:

```bash
python issue_nfse.py --config issuer.ini --producao \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente Real" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico prestado" \
    --servico-valor 1000.00
```

### Gerar PDF

Para gerar o PDF do DANFSE apos a emissao:

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico" \
    --servico-valor 100.00 \
    --gerar-pdf --pdf-output ./notas/
```

### Saida em JSON

Para integracao com outras ferramentas:

```bash
python issue_nfse.py --config issuer.ini --json \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico" \
    --servico-valor 100.00
```

Saida:
```json
{
  "success": true,
  "chave_acesso": "13026032427139240001850000000000034260108333...",
  "nfse_number": "342601",
  "ambiente": "homologacao",
  "dps_numero": 1,
  "dps_serie": "900"
}
```

## Opcoes de Linha de Comando

### Ambiente

| Opcao | Descricao |
|-------|-----------|
| `--config`, `-c` | Caminho para o arquivo de configuracao do emissor (obrigatorio) |
| `--producao` | Usar ambiente de producao (padrao: homologacao) |

### Certificado (sobrescreve arquivo de config)

| Opcao | Descricao |
|-------|-----------|
| `--cert-path` | Caminho para o arquivo do certificado |
| `--cert-password` | Senha do certificado |

Voce tambem pode usar variaveis de ambiente:
```bash
export NFSE_CERT_PATH=/caminho/para/cert.pfx
export NFSE_CERT_PASSWORD=senha123
```

### Tomador (Destinatario do Servico)

| Opcao | Descricao |
|-------|-----------|
| `--tomador-cpf` | CPF (11 digitos) |
| `--tomador-cnpj` | CNPJ (14 digitos) |
| `--tomador-nome` | Nome/razao social (obrigatorio) |
| `--tomador-email` | Email |
| `--tomador-telefone` | Telefone |

### Endereco do Tomador (opcional)

| Opcao | Descricao |
|-------|-----------|
| `--tomador-logradouro` | Nome da rua |
| `--tomador-numero` | Numero |
| `--tomador-complemento` | Complemento |
| `--tomador-bairro` | Bairro |
| `--tomador-municipio` | Codigo do municipio IBGE |
| `--tomador-uf` | Estado (2 letras) |
| `--tomador-cep` | CEP (8 digitos) |

### Detalhes do Servico

| Opcao | Descricao |
|-------|-----------|
| `--servico-codigo` | Codigo LC 116 (obrigatorio, ex: "4.03.03") |
| `--servico-descricao` | Descricao (obrigatorio) |
| `--servico-valor` | Valor em BRL (obrigatorio) |
| `--servico-cnae` | Codigo CNAE |
| `--servico-codigo-municipal` | Codigo de tributacao municipal |
| `--servico-nbs` | Codigo NBS |

### Opcoes de Tributos

| Opcao | Descricao |
|-------|-----------|
| `--iss-retido` | ISS retido pelo tomador |
| `--aliquota-iss` | Aliquota do ISS (percentual) |
| `--aliquota-simples` | Aliquota total do Simples Nacional |

### Opcoes da DPS

| Opcao | Descricao |
|-------|-----------|
| `--numero` | Numero da DPS (auto-incremento por padrao) |
| `--serie` | Serie da DPS (do arquivo de config por padrao) |
| `--competencia` | Competencia YYYY-MM (mes atual por padrao) |

### Opcoes de Saida

| Opcao | Descricao |
|-------|-----------|
| `--gerar-pdf` | Gerar PDF do DANFSE |
| `--pdf-output` | Diretorio de saida do PDF |
| `--json` | Saida em formato JSON |
| `--quiet`, `-q` | Saida minima |

## Codigos de Servico LC 116

Codigos de servico comuns (Lista de Servicos - LC 116/2003):

| Codigo | Descricao |
|--------|-----------|
| 1.01 | Analise e desenvolvimento de sistemas |
| 1.02 | Programacao |
| 1.03 | Processamento de dados |
| 1.04 | Elaboracao de programas |
| 1.05 | Licenciamento de software |
| 4.03 | Processamento de dados e congeneres |
| 7.01 | Engenharia, agronomia, etc. |
| 17.01 | Assessoria ou consultoria |

Lista completa: [Portal Nacional da NFS-e](https://www.gov.br/nfse/pt-br)

## Codigos de Municipio IBGE

Encontre o codigo do seu municipio em: https://www.ibge.gov.br/explica/codigos-dos-municipios.php

Codigos comuns:
- Sao Paulo/SP: 3550308
- Rio de Janeiro/RJ: 3304557
- Belo Horizonte/MG: 3106200
- Curitiba/PR: 4106902
- Porto Alegre/RS: 4314902

## Solucao de Problemas

### Erros de certificado

```
Certificate Error: Certificate file not found
```
Verifique se o caminho do certificado no `issuer.ini` esta correto.

```
Certificate Error: Error loading certificate
```
Verifique se a senha do certificado esta correta.

### Erros da API

```
API Error: TIMEOUT
```
A API do SEFIN pode estar temporariamente indisponivel. Tente novamente mais tarde.

```
API Error: 422 - Validation error
```
Verifique se todos os campos obrigatorios estao preenchidos corretamente, especialmente:
- Formato do CNPJ/CPF
- Codigos de municipio
- Formato do codigo de servico

### Conflito de numero da DPS

Se voce receber um erro sobre numero de DPS duplicado, atualize o `proximo_numero` no seu `issuer.ini` para um valor maior.

## Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `issuer.example.ini` | Configuracao de exemplo (copie para `issuer.ini`) |
| `issuer.ini` | Sua configuracao (nao rastreado pelo git) |
| `issue_nfse.py` | Script CLI principal para emitir NFSe |
| `query_convenio.py` | Script para consultar se um municipio aderiu ao sistema nacional |
| `debug_api.py` | Script de debug para explorar endpoints da API |
| `README.md` | Esta documentacao |

## Consultar Convenio Municipal

Para verificar se um municipio aderiu ao sistema NFSe Nacional:

```bash
# Consultar Manaus:
python query_convenio.py --config issuer.ini --municipio 1302603

# Consultar Sao Paulo:
python query_convenio.py --config issuer.ini --municipio 3550308

# Saida em JSON:
python query_convenio.py --config issuer.ini --municipio 1302603 --json

# Ambiente de producao:
python query_convenio.py --config issuer.ini --municipio 1302603 --producao
```

## Debug da API

Para explorar endpoints da API e debug de conectividade:

```bash
# Explorar endpoints para um municipio:
python debug_api.py --config issuer.ini --municipio 1302603

# Ambiente de producao:
python debug_api.py --config issuer.ini --municipio 1302603 --producao
```

Este script faz chamadas HTTP diretas para explorar respostas da API e testar conectividade.

---

## English Version

Command-line utilities for issuing NFSe (Nota Fiscal de Servicos Eletronica) through Brazil's national NFSe system.

### Setup

#### 1. Install the library

```bash
# Basic installation
pip install pynfse-nacional

# With PDF generation support
pip install "pynfse-nacional[pdf]"
```

#### 2. Configure your issuer (prestador)

Copy the example configuration file and fill in your company details:

```bash
cp issuer.example.ini issuer.ini
```

Edit `issuer.ini` with your:
- Certificate path and password
- Company information (CNPJ, razao social, etc.)
- Address
- Tax regime settings

#### 3. Certificate

You need an ICP-Brasil A1 digital certificate (`.pfx` or `.p12` file) to issue NFSe. This is the same certificate used for signing other Brazilian electronic documents (NF-e, CT-e, etc.).

### Usage

#### Basic Example

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cpf 12345678901 \
    --tomador-nome "Joao da Silva" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Consultoria em tecnologia da informacao" \
    --servico-valor 1500.00
```

#### Production Environment

By default, the script uses the **homologacao** (staging) environment. To issue real NFSe in production:

```bash
python issue_nfse.py --config issuer.ini --producao \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente Real" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico prestado" \
    --servico-valor 1000.00
```

#### Generate PDF

To generate the DANFSE PDF after issuing:

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico" \
    --servico-valor 100.00 \
    --gerar-pdf --pdf-output ./notas/
```

### Command Line Options

See the Portuguese section above for the complete options table. The options use Portuguese names (e.g., `--tomador-cpf`, `--servico-valor`) as they map directly to Brazilian tax concepts.

### Troubleshooting

#### Certificate errors

```
Certificate Error: Certificate file not found
```
Check if the certificate path in `issuer.ini` is correct.

```
Certificate Error: Error loading certificate
```
Check if the certificate password is correct.

#### API errors

```
API Error: TIMEOUT
```
The SEFIN API may be temporarily unavailable. Try again later.

```
API Error: 422 - Validation error
```
Check if all required fields are filled correctly, especially:
- CNPJ/CPF format
- Municipality codes
- Service code format

### Files

| File | Description |
|------|-------------|
| `issuer.example.ini` | Example configuration (copy to `issuer.ini`) |
| `issuer.ini` | Your configuration (not tracked by git) |
| `issue_nfse.py` | Main CLI script for issuing NFSe |
| `query_convenio.py` | Script to check if a municipality has joined the national system |
| `debug_api.py` | Debug script to explore API endpoints |
| `README.md` | This documentation |

### Query Municipal Agreement

To check if a municipality has joined the NFSe Nacional system:

```bash
# Query Manaus:
python query_convenio.py --config issuer.ini --municipio 1302603

# Query Sao Paulo:
python query_convenio.py --config issuer.ini --municipio 3550308

# JSON output:
python query_convenio.py --config issuer.ini --municipio 1302603 --json

# Production environment:
python query_convenio.py --config issuer.ini --municipio 1302603 --producao
```

### API Debug

To explore API endpoints and debug connectivity:

```bash
# Explore endpoints for a municipality:
python debug_api.py --config issuer.ini --municipio 1302603

# Production environment:
python debug_api.py --config issuer.ini --municipio 1302603 --producao
```

This script makes raw HTTP calls to explore API responses and test connectivity.
