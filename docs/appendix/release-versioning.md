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

## Canais da documentação

O site público mantém canais separados para que exemplos em desenvolvimento
não substituam a documentação de uma versão publicada:

| URL | Conteúdo |
| --- | --- |
| `/` | alias da versão estável mais recente |
| `/latest/` | versão estável mais recente, explicitamente nomeada |
| `/MAJOR.MINOR.PATCH/` | documentação de uma versão estável específica |
| `/development/` | documentação atual de `master`, podendo conter mudanças não lançadas |

Os canais estáveis vêm apenas de tags anotadas no formato
`vMAJOR.MINOR.PATCH`. O workflow seleciona as cinco versões semânticas mais
recentes; quando uma nova versão é publicada, ela entra automaticamente como
`latest` e a mais antiga deixa de ser publicada quando a janela ultrapassa
cinco versões.

Cada página tem um seletor de versão. A documentação em `/development/` é a
referência para testar mudanças ainda não lançadas; para suporte a uma versão
instalada, use o caminho correspondente ao release.

O checklist oficial continua em
[RELEASE_CHECKLIST.md](https://github.com/roberto-mello/pynfse-nacional/blob/master/RELEASE_CHECKLIST.md).
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
[`.github/workflows/docs.yml`](https://github.com/roberto-mello/pynfse-nacional/blob/master/.github/workflows/docs.yml):

- valida pull requests que alteram documentação, código, configuração ou o
  builder de versões
- roda em pushes para `master`, em tags `v*` e por `workflow_dispatch`
- busca as tags disponíveis e constrói cada uma das cinco versões estáveis em
  um arquivo temporário usando o `uv.lock` daquele release
- constrói `master` separadamente para `/development/`
- monta um único artefato com todas as versões, `/latest/` e a raiz antes do
  deploy no GitHub Pages
- trata warnings do Sphinx como erros e verifica a existência dos índices de
  todos os canais antes de publicar

O que ainda não existe é um workflow separado para publicar pacote no PyPI. Isso
continua no comando `release` e no processo manual descrito acima.

Pull requests fazem apenas a validação do build. Pushes para `master`, tags de
release e uma execução manual autorizada publicam o artefato completo. Como o
deploy substitui o conteúdo anterior do Pages, cada execução precisa montar
novamente todos os cinco releases, os aliases e `development`.
