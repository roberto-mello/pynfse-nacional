# pynfse-nacional

Biblioteca Python para integração com a API do NFSe Nacional.

## Comece aqui

::::{grid} 1 2 2 2
:gutter: 2

:::{grid-item-card} Guia de início
:link: getting-started
:link-type: doc
:shadow: md

Instale, configure certificado mTLS e envie a primeira DPS.
:::

:::{grid-item-card} Referência da API
:link: api/index
:link-type: doc
:shadow: md

Cliente, modelos, XML, PDF e utilitários gerados dos docstrings.
:::

:::{grid-item-card} Guias
:link: guides/index
:link-type: doc
:shadow: md

Fluxos práticos para emissão, consulta, cancelamento e substituição.
:::

:::{grid-item-card} Arquitetura
:link: architecture
:link-type: doc
:shadow: md

Stack, navegação, regras de renderização e publicação.
:::

::::

## Instalação

```bash
uv add pynfse-nacional
```

Para DANFSe em PDF:

```bash
uv add "pynfse-nacional[pdf]"
```

## Quickstart

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

## O que este site cobre

- [Guias](guides/index) para certificado, emissão, consulta, cancelamento, substituição, PDF e IBSCBS.
- [Referência da API](api/index) gerada dos docstrings do código.
- [Apêndice](appendix/index) para troubleshooting, ambiente e release.

## Documentação oficial

- [Site da documentação](https://robmello.github.io/pynfse-nacional/) - guias, referência da API e apêndice
- [Portal NFSe Nacional](https://www.gov.br/nfse)
- [Documentação Técnica](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/)
- [Documentação Atual](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual)

## Licença

GNU Affero General Public License v3 (AGPL-3.0)

```{toctree}
:maxdepth: 2
:caption: Conteúdo

getting-started
guides/index
api/index
appendix/index
architecture
```
