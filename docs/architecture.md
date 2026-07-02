# Arquitetura da documentação

## Stack escolhida

O site usa `MkDocs Material` com `mkdocstrings`.

Motivos:

- Markdown continua como fonte principal.
- A navegação lateral, a busca e os botões de copiar já vêm no tema.
- A referência da API sai dos docstrings, sem copiar conteúdo para páginas soltas.
- O layout cai para drawer no mobile sem precisar de uma camada extra de UI.
- `navigation.indexes` faz cada seção abrir sua página de visão geral.

## Mapa do site

- Início
- Arquitetura
- Começando
- Guias
  - Configuração de certificado
  - Primeira emissão
  - Consulta
  - Cancelamento
  - Substituição
  - DANFSe PDF
  - IBSCBS
- Referência da API
  - Cliente
  - Modelos
  - XML Builder
  - XML Signer
  - PDF Generator
  - Exceções
  - Utilitários
- Apêndice
  - Troubleshooting
  - Matriz de ambiente
  - Release e versionamento

## Layout da home

A home do site deve manter:

- hero curto;
- snippet de instalação;
- quickstart funcional e enxuto;
- CTA visível para guias e referência da API;
- link explícito para o README do repositório.

## O que fica no README

O README continua sendo a face do pacote no PyPI e no GitHub.

Fica no README:

- instalação;
- quickstart mínimo;
- exemplos principais;
- link para a documentação completa.

Os metadados do pacote apontam para o site da documentação como `Homepage`
e mantêm o repositório separado como `Repository`.

Sai do README:

- referência exaustiva de API;
- guias longos;
- detalhes de publicação;
- material de apêndice.

## Regras de renderização

- Blocos de código com syntax highlight e botão de copiar.
- Páginas legíveis sem depender de JavaScript para conteúdo principal.
- Navegação lateral em seções aninhadas.
- Busca global habilitada.
- Site responsivo com drawer no mobile.
- API pages renderizadas por docstrings no código-fonte.

## Publicação

O site será publicado como conteúdo estático via GitHub Pages.

Fluxo previsto:

1. `uv sync --group docs`
2. `uv run mkdocs build --strict`
3. upload do artefato do site no GitHub Actions
4. deploy para Pages a partir do artefato gerado

O ponto de entrada do site fica em `https://robmello.github.io/pynfse-nacional/`.
