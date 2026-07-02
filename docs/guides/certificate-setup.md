# Configuração de certificado

Para assinar XML e abrir a conexão mTLS com o NFSe Nacional, a biblioteca
precisa de um certificado PKCS#12.

## O que a biblioteca espera

- `cert_path`: caminho para o arquivo `.pfx` ou `.p12`
- `cert_password`: senha do certificado
- `ambiente`: `homologacao` ou `producao`

O arquivo só é lido quando a biblioteca precisa assinar XML ou abrir a
conexão mTLS. Se o caminho estiver errado, a senha não bater ou o arquivo não
tiver a chave privada, o erro aparece como `NFSeCertificateError`.

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

## O que costuma dar errado

- Guarde o certificado fora do repositório.
- Use variáveis de ambiente para o caminho e a senha.
- Separe um certificado de homologação e outro de produção.
- Teste o arquivo antes do primeiro `submit_dps`.

## Padrão recomendado

Se a sua aplicação já tem uma camada própria de certificados, uma recomendação
é usar um serviço único para localizar o arquivo, ler a senha de um 
cofre/secret manager e devolver o cliente NFSe já configurado.

Isso costuma funcionar bem porque:

- evita espalhar `cert_path` e `cert_password` pela aplicação
- deixa a rotação do certificado concentrada em um só ponto
- facilita separar homologação e produção
- reduz o risco de log acidental de senha
- simplifica troca de certificado sem mexer no restante do código

O formato mais simples é:

- guardar o `.pfx`/`.p12` fora do repositório
- manter a senha em variável de ambiente, secret do CI ou cofre da plataforma
- carregar o certificado uma vez por processo, não a cada requisição
- criar um adapter central que entregue `NFSeClient` pronto para uso

## Segurança

Certificado de cliente não é só "um arquivo para passar no construtor". Ele
vale como identidade da empresa perante a SEFIN.

No `pynfse_nacional`, o certificado fica no seu ambiente local. A biblioteca:

- lê o `.pfx` ou `.p12` da máquina onde está rodando;
- usa a chave para assinar o XML;
- cria arquivos PEM temporários só para montar a conexão mTLS;
- apaga esses arquivos temporários no fim da chamada.

Na prática, isso quer dizer:

- não coloque o certificado nem a senha no seu repositório de código
- não imprima `cert_path` nem `cert_password` em log
- use permissões de arquivo restritas
- troque o certificado se ele vazar ou se alguém da equipe sair com acesso a ele
- mantenha homologação e produção separados

Se você usa segredo de ambiente, prefira o que sua infraestrutura já protege
bem, como secret manager, cofre da plataforma ou variáveis injetadas no CI.
O código não precisa ver a senha mais vezes do que o necessário.

## Erros comuns

| Sintoma | Causa provável | O que verificar |
| --- | --- | --- |
| `Arquivo de certificado nao encontrado` | Caminho incorreto | Confirme `cert_path` |
| `Private key not found in certificate` | Arquivo sem chave privada | Veja se o `.pfx` ou `.p12` saiu com a chave |
| `Erro ao carregar certificado` | Senha errada ou arquivo corrompido | Reexporte o certificado e teste a senha |
