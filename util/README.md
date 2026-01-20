# NFSe Nacional - Utility Scripts

Command-line utilities for issuing NFSe (Nota Fiscal de Servicos Eletronica) through Brazil's national NFSe system.

## Setup

### 1. Install the library

```bash
# Basic installation
pip install pynfse-nacional

# With PDF generation support
pip install "pynfse-nacional[pdf]"
```

### 2. Configure your issuer (prestador)

Copy the example configuration file and fill in your company details:

```bash
cp issuer.example.ini issuer.ini
```

Edit `issuer.ini` with your:
- Certificate path and password
- Company information (CNPJ, razao social, etc.)
- Address
- Tax regime settings

### 3. Certificate

You need an ICP-Brasil A1 digital certificate (`.pfx` or `.p12` file) to issue NFSe. This is the same certificate used for signing other Brazilian electronic documents (NF-e, CT-e, etc.).

## Usage

### Basic Example

```bash
python issue_nfse.py --config issuer.ini \
    --tomador-cpf 12345678901 \
    --tomador-nome "Joao da Silva" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Consultoria em tecnologia da informacao" \
    --servico-valor 1500.00
```

### Full Example with Tomador Address

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

### Production Environment

By default, the script uses the **homologacao** (staging) environment. To issue real NFSe in production:

```bash
python issue_nfse.py --config issuer.ini --producao \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente Real" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico prestado" \
    --servico-valor 1000.00
```

### Generate PDF

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

### JSON Output

For integration with other tools:

```bash
python issue_nfse.py --config issuer.ini --json \
    --tomador-cpf 12345678901 \
    --tomador-nome "Cliente" \
    --servico-codigo "4.03.03" \
    --servico-descricao "Servico" \
    --servico-valor 100.00
```

Output:
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

## Command Line Options

### Environment

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to issuer configuration file (required) |
| `--producao` | Use production environment (default: homologacao) |

### Certificate (override config file)

| Option | Description |
|--------|-------------|
| `--cert-path` | Path to certificate file |
| `--cert-password` | Certificate password |

You can also use environment variables:
```bash
export NFSE_CERT_PATH=/path/to/cert.pfx
export NFSE_CERT_PASSWORD=senha123
```

### Tomador (Service Recipient)

| Option | Description |
|--------|-------------|
| `--tomador-cpf` | CPF (11 digits) |
| `--tomador-cnpj` | CNPJ (14 digits) |
| `--tomador-nome` | Name/razao social (required) |
| `--tomador-email` | Email |
| `--tomador-telefone` | Phone |

### Tomador Address (optional)

| Option | Description |
|--------|-------------|
| `--tomador-logradouro` | Street name |
| `--tomador-numero` | Street number |
| `--tomador-complemento` | Complement |
| `--tomador-bairro` | Neighborhood |
| `--tomador-municipio` | IBGE municipality code |
| `--tomador-uf` | State (2 letters) |
| `--tomador-cep` | ZIP code (8 digits) |

### Service Details

| Option | Description |
|--------|-------------|
| `--servico-codigo` | LC 116 code (required, e.g., "4.03.03") |
| `--servico-descricao` | Description (required) |
| `--servico-valor` | Value in BRL (required) |
| `--servico-cnae` | CNAE code |
| `--servico-codigo-municipal` | Municipal tax code |
| `--servico-nbs` | NBS code |

### Tax Options

| Option | Description |
|--------|-------------|
| `--iss-retido` | ISS retained by tomador |
| `--aliquota-iss` | ISS rate (percentage) |
| `--aliquota-simples` | Simples Nacional total tax rate |

### DPS Options

| Option | Description |
|--------|-------------|
| `--numero` | DPS number (auto-increment by default) |
| `--serie` | DPS series (from config by default) |
| `--competencia` | Competencia YYYY-MM (current month by default) |

### Output Options

| Option | Description |
|--------|-------------|
| `--gerar-pdf` | Generate DANFSE PDF |
| `--pdf-output` | PDF output directory |
| `--json` | Output as JSON |
| `--quiet`, `-q` | Minimal output |

## LC 116 Service Codes

Common service codes (Lista de Servicos - LC 116/2003):

| Code | Description |
|------|-------------|
| 1.01 | Analise e desenvolvimento de sistemas |
| 1.02 | Programacao |
| 1.03 | Processamento de dados |
| 1.04 | Elaboracao de programas |
| 1.05 | Licenciamento de software |
| 4.03 | Processamento de dados e congeneres |
| 7.01 | Engenharia, agronomia, etc. |
| 17.01 | Assessoria ou consultoria |

Full list: [Portal Nacional da NFS-e](https://www.gov.br/nfse/pt-br)

## IBGE Municipality Codes

Find your municipality code at: https://www.ibge.gov.br/explica/codigos-dos-municipios.php

Common codes:
- Sao Paulo/SP: 3550308
- Rio de Janeiro/RJ: 3304557
- Belo Horizonte/MG: 3106200
- Curitiba/PR: 4106902
- Porto Alegre/RS: 4314902

## Troubleshooting

### Certificate errors

```
Certificate Error: Certificate file not found
```
Check if the certificate path in `issuer.ini` is correct.

```
Certificate Error: Error loading certificate
```
Check if the certificate password is correct.

### API errors

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

### DPS number conflict

If you get an error about duplicate DPS number, update the `proximo_numero` in your `issuer.ini` to a higher value.

## Files

| File | Description |
|------|-------------|
| `issuer.example.ini` | Example configuration (copy to `issuer.ini`) |
| `issuer.ini` | Your configuration (not tracked by git) |
| `issue_nfse.py` | Main CLI script |
| `README.md` | This documentation |
