# Release e versionamento

## Regra de versão

O número da versão vive em dois lugares:

- `pyproject.toml`
- `src/pynfse_nacional/__init__.py`

Os dois precisam bater antes de um release. Se não baterem, a publicação fica
confusa e o usuário final percebe na primeira instalação.

## Forma de release

O fluxo normal é este:

1. atualizar versão e changelog
2. rodar os testes e o lint do que mudou
3. checar `git status --short --branch`
4. confirmar que o tag ainda não existe
5. rodar `uv run release` ou `uv run release --repository testpypi --dry-run`
6. criar um tag anotado, como `v0.5.1`
7. fazer push da branch e do tag
8. conferir se o pacote e a documentação apareceram no lugar certo

O checklist oficial continua em
[RELEASE_CHECKLIST.md](https://github.com/robmello/pynfse-nacional/blob/master/RELEASE_CHECKLIST.md).
Use ele antes de cortar tag. Ele cobre o que normalmente escapa quando a pressa
aperta.

## Regras para documentação

- Mudança que afeta comportamento público precisa de ajuste no guia e, se
  houver API nova, na referência da API.
- Página de apêndice serve para regras operacionais, não para tutorial longo.
- Se a alteração mexe em certificado, mTLS, PDF ou release, deixe isso escrito
  na documentação do mesmo PR.
- Texto de docs deve ser direto. Se parecer texto de marketing, está longo
  demais.

## CI e publicação

Sim, a CI de documentação já está conectada.

O workflow em
[`.github/workflows/docs.yml`](https://github.com/robmello/pynfse-nacional/blob/master/.github/workflows/docs.yml):

- roda em `push` e `pull_request` quando mexe em `docs/**`, `src/**`, `README.md`,
  `pyproject.toml` ou `uv.lock`
- instala as dependências de docs com `uv sync --group docs --frozen`
- gera o site com `uv run sphinx-build -b html -W --keep-going docs site`
- publica no GitHub Pages quando o push cai na branch `master`

O que ainda não existe é um workflow separado para publicar pacote no PyPI. Isso
continua no comando `release` e no processo manual descrito acima.
