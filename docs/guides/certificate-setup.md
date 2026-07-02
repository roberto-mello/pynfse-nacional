# Configuração de certificado

Para assinar e transmitir XMLs para o NFSe Nacional, você precisa informar um
certificado em formato PKCS#12.

## O que a biblioteca espera

- `cert_path`: caminho para o arquivo `.pfx` ou `.p12`
- `cert_password`: senha do certificado
- `ambiente`: `homologacao` ou `producao`

O certificado só é carregado quando a biblioteca precisa assinar um XML ou
abrir a conexão mTLS. Se o arquivo estiver ausente, a senha estiver errada ou
o pacote não tiver a chave privada, o erro aparece como
`NFSeCertificateError`.

## Exemplo mínimo

```python
import os

from pynfse_nacional import NFSeClient

client = NFSeClient(
    cert_path=os.environ["NFSE_CERT_PATH"],
    cert_password=os.environ["NFSE_CERT_PASSWORD"],
    ambiente="homologacao",
)
```

## Boas práticas

- Guarde o certificado fora do repositório.
- Prefira variáveis de ambiente para o caminho e a senha.
- Use um certificado específico para homologação e outro para produção.
- Valide o arquivo antes do primeiro envio, para não descobrir o erro só no
  `submit_dps`.

## Erros comuns

| Sintoma | Causa provável | O que verificar |
| --- | --- | --- |
| `Arquivo de certificado nao encontrado` | Caminho incorreto | Confirme `cert_path` |
| `Private key not found in certificate` | Arquivo sem chave privada | Verifique se o `.pfx`/`.p12` exportou a chave |
| `Erro ao carregar certificado` | Senha errada ou arquivo corrompido | Reexporte o certificado e teste a senha |

