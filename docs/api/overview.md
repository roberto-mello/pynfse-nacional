# Visão Geral da API

A referência completa sai dos docstrings, mas esta página serve como mapa rápido.

## Entrada principal

- `NFSeClient`: cliente principal para enviar DPS, consultar NFSe, cancelar e recuperar emissões.

## Modelos mais usados

- `DPS`: payload de emissão.
- `Prestador`, `Tomador`, `Servico`, `Endereco`: blocos de entrada da emissão.
- `NFSeResponse`: retorno da emissão.
- `NFSeQueryResult`: retorno de consulta.
- `EventResponse`: retorno de cancelamento e outros eventos.
- `RecoveryOutcome`: retorno do fluxo de recuperação por DPS.

## Regras práticas

- Use `NFSeClient` como ponto único de integração.
- Monte os dados com os modelos, em vez de passar dicionários soltos.
- Separe homologação e produção.
- Guarde o certificado fora do repositório.

## Onde ver os detalhes

As páginas abaixo mostram a referência gerada automaticamente a partir dos docstrings do código.
