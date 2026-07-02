# Consulta

Use este fluxo quando a NFSe já saiu, mas você ainda precisa puxar o registro
para o seu sistema.

## Quando usar cada método

| Método | Quando usar |
| --- | --- |
| `query_nfse` | Você já tem a chave de acesso |
| `query_nfse_by_dps` | Você só tem o `id_dps` |
| `has_nfse_by_dps` | Você quer só saber se a DPS já gerou NFSe |
| `recover_nfse_by_dps` | Você perdeu a chave e quer tentar recuperar tudo de uma vez |

## Exemplo por DPS

Aqui, `nota` é o registro que já guarda o `id_dps` depois da emissão.

```python
from pynfse_nacional import NFSeClient

client = NFSeClient(
    cert_path="/caminho/para/certificado.pfx",
    cert_password="senha",
    ambiente="homologacao",
)

def consultar_nfse_pendente(client: NFSeClient, nota) -> None:
    dps_id = nota.id_dps

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

## Exemplo em uma aplicação real

Num sistema de faturamento, a consulta costuma servir para fechar uma emissão
que ficou sem resposta. O fluxo abaixo pega o resultado e grava no banco.

Neste exemplo, `nota` é o objeto persistido pela sua aplicação.

```python
from pynfse_nacional import NFSeClient


def sincronizar_nfse_por_dps(client: NFSeClient, nota) -> str:
    outcome = client.recover_nfse_by_dps(nota.id_dps)

    if outcome.status == "processing":
        return "A DPS ainda está em processamento."

    if outcome.status == "error":
        raise outcome.error

    nfse = outcome.result
    registro = {
        "dps_id": nota.id_dps,
        "chave_acesso": nfse.chave_acesso,
        "numero_nfse": nfse.nfse_number,
        "status": nfse.status,
        "xml_nfse": nfse.xml_nfse,
        "ibscbs": nfse.ibscbs,
    }
    salvar_registro_no_banco(registro)
    return f"NFSe {nfse.nfse_number} salva com sucesso."
```

`recover_nfse_by_dps` junta a checagem por `HEAD` com a consulta completa. Ele
é útil quando `submit_dps` falhou, mas a SEFIN talvez tenha processado a DPS.

```python
outcome = client.recover_nfse_by_dps(nota.id_dps)

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
