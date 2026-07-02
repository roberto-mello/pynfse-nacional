# Matriz de ambiente

Esta biblioteca roda em Python 3.10 ou mais novo. O projeto declara suporte a
3.10, 3.11 e 3.12.

## Ambientes

| Ambiente | Uso | Observações |
| --- | --- | --- |
| Homologação | Testes de integração e validação | Use um certificado separado do de produção. |
| Produção | Emissão real | Trate o certificado como segredo sensível. |

## Instalação

| Perfil | Comando | O que traz |
| --- | --- | --- |
| Núcleo | `uv add pynfse-nacional` | Cliente, modelos, XML e integrações básicas. |
| PDF | `uv add "pynfse-nacional[pdf]"` | Geração local do DANFSe com `reportlab` e `qrcode`. |

## Suporte prático

- Certificado: PKCS#12 `.pfx` ou `.p12`
- Autenticação: mTLS
- Formatos comuns de ambiente: local, CI e produção com secrets injetados

## Quando olhar esta matriz

Use esta página antes de mexer em deploy, suporte a PDF ou automação de release.
Ela evita aquele tipo de surpresa chata que aparece só depois do merge.
