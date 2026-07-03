# Códigos de Erro

A biblioteca exporta `ErrorCode` no pacote principal para facilitar o tratamento
programático dos erros.

```python
from pynfse_nacional import ErrorCode, NFSeAPIError

try:
    client.query_nfse("123")
except NFSeAPIError as error:
    if error.code == ErrorCode.COMMUNICATION_TIMEOUT:
        ...
    print(error.message)
```

## Contrato

- `error.code` é o identificador estável para automação
- `error.message` é a mensagem em Português Brasileiro para exibição
- mensagens da biblioteca ficam centralizadas no catálogo interno
- `error_messages.py` existe para uso interno e para lookup auxiliar, não como
  dependência obrigatória para o chamador

## Faixas

- `100-199`: validação
- `200-299`: certificado e assinatura
- `300-399`: comunicação e transporte
- `400-499`: resposta e parsing
- `500-599`: compressão e decodificação

## Uso recomendado

Use o código para decisões de fluxo e a mensagem para mostrar ao usuário.
Se precisar de tratamento mais fino, compare a classe da exceção e depois o
`code` numérico.
