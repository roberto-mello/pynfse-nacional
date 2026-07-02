# pynfse-nacional

Biblioteca Python para integração com a API do NFSe Nacional.

## Instalação

```bash
uv add pynfse-nacional
```

Para geração local de DANFSe em PDF:

```bash
uv add "pynfse-nacional[pdf]"
```

## Início rápido

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

- Leia [Começando](getting-started.md) para ver o fluxo base.
- Veja os [Guias](guides/index.md) para tarefas comuns.
- Consulte a [Referência da API](api/index.md) para módulos e classes.
- Use [Arquitetura](architecture.md) para entender a forma do site.

