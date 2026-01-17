# pynfse-nacional

Python library for Brazilian NFSe Nacional (Padrao Nacional) API integration.

## Overview

This library provides a client for interacting with the NFSe Nacional (SEFIN Nacional) API, which became mandatory for all Brazilian municipalities starting January 2026.

## Features

- mTLS authentication with ICP-Brasil A1/A3 certificates
- DPS (Declaracao de Prestacao de Servicos) XML generation
- XML digital signing (XMLDSIG)
- GZip compression and Base64 encoding
- NFSe issuance, query, and cancellation
- DANFSe PDF download

## Installation

```bash
pip install pynfse-nacional
```

Or install from source:

```bash
pip install git+https://github.com/robmello/pynfse-nacional.git
```

## Quick Start

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
print(f"NFSe emitida: {response.nfse_number}")
print(f"Chave de acesso: {response.chave_acesso}")
```

## API Reference

### NFSeClient

Main client for NFSe Nacional API.

- `submit_dps(dps: DPS) -> NFSeResponse` - Submit DPS and receive NFSe
- `query_nfse(chave_acesso: str) -> NFSeQueryResult` - Query NFSe by access key
- `download_danfse(chave_acesso: str) -> bytes` - Download DANFSe PDF
- `cancel_nfse(chave_acesso: str, reason: str) -> EventResponse` - Cancel NFSe

### Models

- `DPS` - Service declaration
- `Prestador` - Service provider (issuer)
- `Tomador` - Service recipient
- `Servico` - Service details

## Environments

- **Homologacao**: `sefin.producaorestrita.nfse.gov.br`
- **Producao**: `sefin.nfse.gov.br`

## Documentation

- [NFSe Nacional Portal](https://www.gov.br/nfse)
- [Technical Documentation](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)

## License

MIT License
