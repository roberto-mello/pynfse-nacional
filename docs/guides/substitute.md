# Substituição

Substituir uma NFSe significa cancelar a nota original e emitir uma nova DPS
com os dados corrigidos.

## Exemplo

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

new_dps = DPS(
    serie="900",
    numero=2,
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
        discriminacao="Descrição corrigida do serviço prestado",
        valor_servicos=Decimal("500.00"),
    ),
)

response = client.substitute_nfse(
    chave_acesso_original="12345678901234567890123456789012345678901234567890",
    new_dps=new_dps,
    motivo="Correção da descrição do serviço prestado",
    codigo_motivo=99,
)
```

## Regras

- O motivo precisa ter entre 15 e 255 caracteres.
- A substituição precisa acontecer dentro do prazo aceito pelo município.
- Não dá para substituir NFSe sem tomador identificado.
- Não dá para trocar o tomador por outra pessoa.
- `new_dps` não deve carregar o campo `substituicao`; a biblioteca adiciona isso.

## Quando usar

Use substituição quando o problema for de conteúdo e a regra municipal permitir
corrigir a nota por nova emissão em vez de cancelar manualmente.

