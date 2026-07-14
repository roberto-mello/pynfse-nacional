# Arquitetura da documentação

## Stack escolhida

O site usa `Sphinx` com `MyST`, `autodoc` e `Furo`.

Motivos:

- Markdown continua como fonte principal.
- `autodoc` puxa a referência da API direto dos docstrings.
- `MyST` mantém o conteúdo do site em Markdown com recursos Sphinx.
- `Furo` entrega um layout limpo, responsivo e fácil de navegar.
- `sphinx-copybutton` adiciona o botão de copiar nos blocos de código.
- `sphinx.ext.githubpages` prepara o artefato para GitHub Pages.

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
- Site responsivo com sidebar colapsável no mobile.
- API pages renderizadas por docstrings no código-fonte.

## Publicação

O site será publicado como conteúdo estático via GitHub Pages.

Fluxo previsto:

1. o workflow faz checkout com as tags completas disponíveis
2. `util/build_versioned_docs.py` seleciona as cinco tags anotadas
   `vMAJOR.MINOR.PATCH` mais recentes
3. cada tag é extraída para um diretório temporário e construída com seu
   próprio `uv.lock`; a configuração e o seletor de versão atuais são
   sobrepostos para manter a navegação consistente
4. a versão estável mais recente é construída também para o canal `latest` e
   copiada para a raiz; `master` é construído separadamente para
   `development`
5. o workflow verifica os índices gerados, faz upload do artefato completo e
   faz o deploy para Pages

O ponto de entrada do site fica em
`https://roberto-mello.github.io/pynfse-nacional/`. Os caminhos estáveis e o
canal de desenvolvimento estão descritos em
[Release e versionamento](appendix/release-versioning).
