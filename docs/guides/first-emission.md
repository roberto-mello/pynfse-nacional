# Primeira emissão

Aqui está o fluxo que normalmente funciona: montar a DPS, enviar e guardar a
resposta que vier da SEFIN.

## Passos

1. Monte endereço, prestador, tomador e serviço.
2. Crie a DPS.
3. Envie com `submit_dps`.
4. Leia `success`, `chave_acesso`, `nfse_number` e o XML retornado.

## Exemplo completo

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
        email="contato@empresa.com",
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

if response.success:
    print(response.chave_acesso)
    print(response.nfse_number)
else:
    print(response.error_code, response.error_message)
```

### Inscrição municipal

`Prestador.inscricao_municipal` aceita o valor da inscrição municipal sem
preenchimento visual. Valores numéricos são normalizados para 15 dígitos no XML
enviado, de acordo com a chave do CNC usada pela SEFIN. Isso é necessário para
alguns cadastros municipais e evita `E0116` quando o valor no CNC possui zeros à
esquerda.

## Por baixo dos panos

- A DPS vira XML.
- O XML é assinado com o certificado.
- O conteúdo vai compactado em GZip e codificado em Base64.
- A API devolve a chave de acesso e, quando disponível, o número da NFSe.

## Se houver IBSCBS

Se o prestador for optante pelo Simples Nacional e o caso pedir IBSCBS,
preencha `dps.ibscbs` e use `op_simp_nac="3"` com `reg_ap_trib_sn`.

- `op_simp_nac` aceita apenas `"1"`, `"2"` e `"3"` (TSOpSimpNac oficial).
- `op_simp_nac="1"` e `"2"` não aceitam `reg_ap_trib_sn`.
- `op_simp_nac="3"` exige `reg_ap_trib_sn`.

## Quando você precisa do mapeamento

Se outra aplicação precisar do mesmo mapeamento que a biblioteca usa para os
regimes do Simples Nacional, importe `REGIME_TO_SIMPLES_NACIONAL` do pacote
principal:

```python
from pynfse_nacional import REGIME_TO_SIMPLES_NACIONAL

mapeamento = REGIME_TO_SIMPLES_NACIONAL["simples_nacional"]
print(mapeamento["opSimpNac"])
```

Esse contrato fica exposto no pacote para evitar cópias locais e manter o valor
usado na emissão sincronizado entre integrações.
