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
from datetime import datetime
from decimal import Decimal

from pynfse_nacional import DPS, Endereco, NFSeClient, Prestador, Servico, Tomador

client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="senha",
    ambiente="homologacao",
)

endereco = Endereco(
    logradouro="Rua Exemplo",
    numero="100",
    bairro="Centro",
    codigo_municipio=3550308,
    uf="SP",
    cep="01310100",
)

dps = DPS(
    serie="900",
    numero=1,
    competencia="2026-01",
    data_emissao=datetime.now(),
    prestador=Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Empresa Exemplo LTDA",
        endereco=endereco,
    ),
    tomador=Tomador(
        cpf="52998224725",
        razao_social="Joao da Silva",
        endereco=endereco,
    ),
    servico=Servico(
        codigo_lc116="04.03.01",
        discriminacao="Consulta médica em consultório",
        valor_servicos=Decimal("500.00"),
    ),
)

response = client.submit_dps(dps)
```

## Próximos passos

- [Configuração de certificado](guides/certificate-setup)
- [Primeira emissão](guides/first-emission)
- [Consulta](guides/query)
- [Cancelamento](guides/cancel)
- [Substituição](guides/substitute)
- [DANFSe PDF](guides/danfse-pdf)
- [IBSCBS](guides/ibscbs)
- Se você precisar do mapeamento `REGIME_TO_SIMPLES_NACIONAL`, veja o exemplo
  em [Primeira emissão](guides/first-emission).
