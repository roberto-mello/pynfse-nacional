# Consulta

Use este fluxo para recuperar uma NFSe já emitida por chave de acesso ou pelo
identificador da DPS.

## Quando usar cada método

| Método | Quando usar |
| --- | --- |
| `query_nfse` | Você já tem a chave de acesso |
| `query_nfse_by_dps` | Você só tem o `id_dps` |
| `has_nfse_by_dps` | Você quer só saber se a DPS já gerou NFSe |
| `recover_nfse_by_dps` | Você perdeu a chave e quer tentar recuperar tudo de uma vez |

## Exemplo por DPS

```python
from pynfse_nacional import NFSeClient

client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="senha",
    ambiente="homologacao",
)

# Assuma que `dps` já foi montada no fluxo de emissão.
dps_id = dps.build_dps_id()

if client.has_nfse_by_dps(dps_id):
    result = client.query_nfse_by_dps(dps_id)
    print(result.chave_acesso)
    print(result.nfse_number)
```

## Exemplo por chave

```python
result = client.query_nfse("13026032211222333000181000000000010626030410654816")

print(result.status)
print(result.valor_servicos)
print(result.prestador_cnpj)
```

## Recuperação automática

`recover_nfse_by_dps` junta o `HEAD` de verificação com a consulta completa.
Ele é útil quando `submit_dps` falhou, mas a SEFIN pode ter processado a DPS.

```python
outcome = client.recover_nfse_by_dps(dps_id)

if outcome.status == "success":
    print(outcome.result.chave_acesso)
elif outcome.status == "processing":
    print("A DPS ainda não virou NFSe.")
else:
    print(outcome.error)
```

## O que a resposta traz

`NFSeQueryResult` inclui:

- chave de acesso
- número da NFSe
- situação
- data de emissão
- valor dos serviços
- CNPJ do prestador
- documento do tomador
- XML da NFSe quando a API devolver o corpo
- IBSCBS extraído do XML, quando existir
