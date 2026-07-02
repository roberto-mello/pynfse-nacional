# Cancelamento

O cancelamento usa a chave de acesso da NFSe, o motivo livre e o CNPJ do
prestador.

## Exemplo

```python
result = client.cancel_nfse(
    chave_acesso="13026032211222333000181000000000010626030410654816",
    reason="Erro na emissão do serviço prestado",
    codigo_motivo=1,
    cnpj_prestador="11222333000181",
)

if result.success:
    print(result.protocolo)
else:
    print(result.error_code, result.error_message)
```

## Códigos de motivo

| Código | Significado |
| --- | --- |
| `1` | Erro na emissão |
| `2` | Serviço não prestado |
| `4` | Duplicidade |

## Regras práticas

- `cnpj_prestador` é obrigatório para a SEFIN identificar quem cancelou.
- O motivo deve ser claro e curto.
- O prazo de cancelamento pode variar por município.
- Alguns municípios impõem limite de valor para cancelamento via API.

## Quando falha

Se a resposta vier com erro, revise:

- chave de acesso com 50 dígitos
- CNPJ do prestador com 14 dígitos
- motivo aceito pelo município
- janela de cancelamento ainda aberta

