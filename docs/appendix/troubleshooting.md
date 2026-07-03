# Troubleshooting

## Certificado não carrega

Sintoma comum:

- `NFSeCertificateError: Certificate file not found`
- `NFSeCertificateError: Error loading certificate`
- `Private key not found in certificate`

O que conferir:

- caminho do arquivo em `cert_path`
- senha do certificado
- extensão real do arquivo, `.pfx` ou `.p12`
- se o arquivo tem chave privada embutida
- permissões de leitura no ambiente onde a aplicação roda

## PDF opcional não funciona

Se a geração local do DANFSe falhar, quase sempre falta o extra de PDF.

Instale com:

```bash
uv add "pynfse-nacional[pdf]"
```

O extra traz `reportlab` e `qrcode`. Sem ele, a biblioteca continua útil, só
sem a geração local do PDF.

## A documentação não compila

Se `sphinx-build` reclamar, rode a partir do ambiente de docs:

```bash
uv sync --group docs
uv run sphinx-build -b html -W --keep-going docs site
```

Erros úteis para caçar:

- links quebrados
- docstrings com indentação ruim
- páginas novas fora do `toctree`

## A API responde com erro estranho

Quando a SEFIN devolve algo diferente do esperado, confira primeiro:

- ambiente usado no cliente
- número da DPS
- validade do certificado
- se a nota já foi emitida e a aplicação perdeu a `chave_acesso`

Quando o erro vier da própria biblioteca, use o par `error.code` + `error.message`
para diagnosticar:

- `error.code` identifica a categoria do problema de forma estável
- `error.message` já vem em PT-BR com acentuação correta
- os códigos e as mensagens estão catalogados em [Códigos de erro](error-codes)

Se o problema acontecer só em homologação, vale testar o mesmo fluxo em outro
certificado de homologação. Às vezes o arquivo está bom, mas o cadastro no
ambiente não está.
