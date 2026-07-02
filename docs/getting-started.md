# Começando

Fluxo mínimo:

1. Instale a biblioteca.
2. Configure certificado mTLS.
3. Monte uma DPS.
4. Envie a DPS.
5. Consulte, cancele ou substitua a NFSe gerada.

## Instalação

```bash
uv add pynfse-nacional
```

Para DANFSe em PDF:

```bash
uv add "pynfse-nacional[pdf]"
```

## Primeiro envio

```python
from decimal import Decimal

from pynfse_nacional import DPS, NFSeClient, Prestador, Servico, Tomador

client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="senha",
    ambiente="homologacao",
)

dps = DPS(
    serie="900",
    numero=1,
    competencia="2026-01",
    prestador=Prestador(...),
    tomador=Tomador(...),
    servico=Servico(
        codigo_lc116="04.03.01",
        discriminacao="Consulta médica em consultório",
        valor_servicos=Decimal("500.00"),
    ),
)

response = client.submit_dps(dps)
```

## Próximos passos

- [Configuração de certificado](guides/certificate-setup.md)
- [Primeira emissão](guides/first-emission.md)
- [Consulta](guides/query.md)
- [Cancelamento](guides/cancel.md)
- [Substituição](guides/substitute.md)
- [DANFSe PDF](guides/danfse-pdf.md)
- [IBSCBS](guides/ibscbs.md)
