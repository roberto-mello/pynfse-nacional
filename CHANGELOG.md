# Registro de alterações

Todas as mudanças relevantes deste projeto serão registradas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
e este projeto segue o [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## 0.9.5 - 2026-07-14

Versão com algumas adições de qualidade de vida para auxiliar desenvolvedores quando
precisarem inspecionar o que é enviado à SEFIN.

### Adicionado

- Operações públicas de diagnóstico em `NFSeClient` que retornam dados
  `RawNFSeResponse` desacoplados e imutáveis para envio, tais como consulta de NFSe por
  chave, consulta de DPS e sondagens de recuperação em duas etapas. Não expõem
  o cliente mTLS ativo nem a resposta de transporte.
- `RawNFSeResponse.redacted_preview()` fornece uma prévia limitada, com melhor
  esforço para ocultar dados sensíveis, para diagnóstico; os
  consumidores devem revisá-la antes de enviá-la a um serviço externo de logs.

## 0.9.4 - 2026-07-12

### Adicionado

- Fixtures oficiais do XSD NFSe v1.01, fixtures de anexos e testes de
  fidelidade de schema que detectam alterações no schema upstream e limitam o
  tamanho dos arquivos baixados.
- Mecanismos de verificação na integração que fazem os testes de homologação falharem diante
  de rejeições de schema E1xxx, em vez de tratá-las como erros aceitáveis.
- Validação que exige `x_tipo_chave_dfe` quando `tipo_chave_dfe="9"`.

### Alterado

- `DPS.op_simp_nac` agora aceita apenas os valores oficiais de `TSOpSimpNac`,
  `"1"`, `"2"` e `"3"`; os campos do Simples Nacional agora seguem a
  estrutura oficial de `TCRegTrib`.
- Os valores numéricos de `Prestador.inscricao_municipal` são normalizados
  para 15 dígitos no XML da DPS enviada, em conformidade com os identificadores
  do CNC e evitando rejeições `E0116` aplicáveis.
- `verAplic` continua sendo derivado da versão instalada do pacote e agora
  informa `pynfse-0.9.4`.

### Corrigido

- O XML da DPS não emite mais `regApIBSCBSSN` inventado dentro de `regTrib`
  (rejeição de schema E1235 da SEFIN).
- O parsing do envio de DPS agora trata arrays `erro`/`erros` da SEFIN, listas
  JSON no nível superior e chaves de resposta com letras maiúsculas,
  preservando os detalhes do erro informado pelo provedor.
- O parsing de NFSe e DANFSe agora compartilha a regra de validação da chave de
  acesso com 50 dígitos.
- O parsing de respostas XML e PDFs agora usa `defusedxml`.
- As referências de documentos IBSCBS agora emitem os nomes oficiais dos
  elementos e exigem o campo complementar `tipo_chave_dfe`.
- Os rótulos do Simples Nacional na saída do DANFSe agora correspondem ao enum
  oficial: `1`=Não Optante, `2`=MEI, `3`=ME/EPP.

### Segurança

- Adicionadas proteções do `defusedxml` contra ataques de expansão de entidades.
- Downloads de arquivos de fidelidade de schema agora têm o tamanho limitado
  antes da extração dos arquivos compactados.
- Referências do GitHub Actions são fixadas em SHAs de commits imutáveis.

### Removido

- `DPS.reg_ap_ibs_cbs_sn` e
  `REGIME_TO_SIMPLES_NACIONAL["regApIbsCbsSn"]`, que não estavam presentes no
  schema oficial.

### Migração

- Remova `reg_ap_ibs_cbs_sn=...`; o campo agora é rejeitado como extra.
- Substitua `op_simp_nac="4"` por `"1"`, `"2"` ou `"3"`.
- Para ME/EPP (`op_simp_nac="3"`), informe apenas `reg_ap_trib_sn`.
- Use a etapa manual de emissão em homologação descrita em
  `RELEASE_CHECKLIST.md`; a emissão real na SEFIN faz parte do nosso processo
  de pré-lançamento. Ela intencionalmente não faz parte do CI/CD automatizado,
  pois exigiria certificados no GitHub.

## 0.9.3 - 2026-07-07

### Corrigido

- `submit_dps()` agora normaliza payloads de erro da SEFIN que chegam como
  arrays `erro` ou listas JSON no nível superior, preservando a mensagem do
  provedor em vez de falhar por causa do formato da resposta.

## 0.9.2 - 2026-07-04

A versão "star-spangled banner". Ficou claro que não queríamos duplicar o
mapeamento de regimes nos clientes, então fizemos esta pequena adição.

### Adicionado

- Exportado `REGIME_TO_SIMPLES_NACIONAL` no pacote de nível superior para que os
  consumidores possam reutilizar o mapeamento canônico do Simples Nacional sem
  duplicá-lo.

## 0.9.1 - 2026-07-03

### Adicionado

- Códigos numéricos de erro estáveis centralizados em `error_codes.py` e
  mensagens de erro em PT-BR em `error_messages.py`.
- Mensagens de erro geradas pela biblioteca padronizadas em português
  brasileiro, com acentuação, preservando os valores numéricos de `ErrorCode`
  para tratamento programático.

## [0.9.0] - 2026-07-02

### Corrigido

- O decoding de NFSe compactadas com gzip foi endurecido contra payloads
  grandes demais; o parsing XML nos caminhos do assinador e da extração do
  número da resposta passou a usar uma configuração de parser mais segura; e
  valores sensíveis brutos foram removidos dos erros de validação.

### Adicionado

- Suporte a IBSCBS para payloads de DPS e emissão de XML, incluindo o modelo
  `opSimpNac` ampliado e o tratamento de `regApIBSCBSSN` para prestadores do
  Simples Nacional.
- O parsing de IBSCBS no lado da resposta agora preenche `NFSe`,
  `NFSeQueryResult` e o modelo de dados do parser de PDF a partir do XML da
  resposta com um único parsing XML.
- A renderização do PDF DANFSe agora exibe uma faixa opcional com os totais de
  IBSCBS quando `totCIBS` está presente, mantendo o layout inalterado quando
  ele está ausente.
- `NFSeClient` agora permite recuperar uma NFSe pelo identificador da DPS com
  `query_nfse_by_dps(id_dps)` e verificar sua disponibilidade com
  `has_nfse_by_dps(id_dps)`, usando os endpoints oficiais `GET /dps/{id}` e
  `HEAD /dps/{id}`.
- O helper de alto nível `NFSeClient.recover_nfse_by_dps(id_dps)` combina
  `has_nfse_by_dps` e `query_nfse_by_dps` para o fluxo de recuperação de
  `chave_acesso` duplicada ou perdida. Ele retorna um dataclass imutável
  `RecoveryOutcome` (`status="success" | "processing" | "error"`), para que
  os consumidores não precisem rederivar a semântica dos status `202 / 404 /
  409` da SEFIN. `RecoveryOutcome` é exportado no pacote de nível superior.
- Fixtures versionadas do XSD NFSe v1.01-20260209 e amostras XML golden de
  IBSCBS para cobertura de validação de schema.

### Alterado

- `DPS.optante_simples` (`bool`) foi removido e substituído por
  `DPS.op_simp_nac` (`Literal['1', '2', '3', '4']`) para corresponder ao schema
  oficial da NFSe. Entradas antigas com `optante_simples` agora falham
  rapidamente porque `DPS` rejeita campos extras. Migração:
  `optante_simples=True` corresponde a `op_simp_nac='3'` e `False` corresponde
  a `op_simp_nac='1'`. Para `op_simp_nac='3'` ou `'4'`, informe também
  `reg_ap_trib_sn` e `reg_ap_ibs_cbs_sn`; para `'1'` ou `'2'`, deixe esses
  campos sem valor.
- `verAplic` agora é derivado da versão instalada do pacote, em vez de usar
  uma string de lançamento fixa.
- Os limites mínimos suportados de `lxml` e `signxml` foram atualizados para
  corresponder à base segura e ao runtime atuais.
- A documentação do projeto e as referências ao schema oficial foram
  atualizadas para o pacote de XSD NFSe de 2026-02-09.

## [0.4.7] - 2026-06-15

### Corrigido

- O gerenciador de contexto `_get_client()` não engole mais erros de rede do
  httpx (`RemoteProtocolError`, `ConnectError` etc.) ocorridos no corpo do
  `yield`, classificando-os incorretamente como `NFSeCertificateError`. Apenas
  erros na construção de `httpx.Client()` são encapsulados como
  `NFSeCertificateError`; erros durante a execução da requisição agora seguem
  para os handlers corretos `except httpx.TimeoutException` /
  `except httpx.RequestError` em `submit_dps()`, `cancel_nfse()`,
  `query_nfse()`, `download_danfse()` e `query_convenio_municipal()`.
- `Prestador.inscricao_municipal` agora é opcional e o builder de XML da DPS
  omite `<IM>` quando o campo não é informado, em conformidade com o layout
  oficial da NFSe.

### Alterado

- Todas as violações E501 de limite de linha em `client.py` foram corrigidas
  para conformidade com o Ruff.
- Imports organizados para conformidade com isort/Ruff.
- Adicionado um checklist de lançamento dedicado em `RELEASE_CHECKLIST.md`,
  vinculado a `AGENTS.md` e `CLAUDE.md`, para manter os passos de lançamento
  centralizados.
- Reduzido o débito de lint nos arquivos de lançamento alterados sem modificar
  o comportamento de transporte da NFSe.

## [0.4.6] - 2026-03-11

### Corrigido

- `cancel_nfse()`, `query_nfse()` e `download_danfse()` agora validam que
  `chave_acesso` contém exatamente 50 dígitos numéricos antes de interpolá-la
  na URL, lançando `ValueError` para entradas inválidas.
- `_parse_event_response()` agora distingue corretamente um sucesso confirmado
  por `retEvento.cStat=144` de uma resposta legada `{protocolo: "..."}` — antes,
  ambos seguiam pelo mesmo caminho e produziam `success=True` com
  `protocolo=None` quando `retEvento` estava ausente.
- `_parse_event_response()` agora agrega todas as entradas do array `erro` da
  SEFIN em uma única mensagem de erro, em vez de descartar silenciosamente
  todas menos a primeira.
- Os campos `descricao` e `complemento` das respostas de erro da SEFIN são
  limitados a 255 caracteres para evitar entradas de log sem limite.
- `_get_client()` agora inicializa os caminhos dos arquivos temporários como
  `None` antes da escrita, evitando um `NameError` no cleanup de `finally` se a
  escrita falhar no meio do processo.

### Alterado

- Removidas as constantes internas não utilizadas `REGIME_SIMPLES_NACIONAL`,
  `REGIME_SIMPLES_EXCESSO`, `REGIME_NORMAL`, `REGIME_MEI`, `STATUS_EMITIDA`,
  `STATUS_CANCELADA` e `STATUS_SUBSTITUIDA` de `constants.py`; elas nunca foram
  exportadas nem referenciadas pela biblioteca.

## [0.4.5] - 2026-03-12

### Corrigido

- `cancel_nfse()` agora publica no endpoint correto `/nfse/{chave}/eventos`, em
  vez de `/eventos`, que retornava HTTP 404 (recurso não encontrado).
- O atributo `Id` de `infPedReg` agora segue o tipo XSD `TSIdPedRegEvt` com o
  padrão `PRE[0-9]{56}`: `PRE` + chave de 50 dígitos + código de evento de 6
  dígitos `101101`. Antes, era usado `PRE{chave}1` (54 caracteres), o que
  falhava na validação do schema com RNG6110.
- Removido o elemento `nPedRegEvento` de `infPedReg`; ele não faz parte do
  schema e causava o erro RNG6110 "invalid child element".
- `_parse_event_response()` agora interpreta o formato do array `erro` da SEFIN
  (`[{codigo, descricao, complemento}]`) para produzir mensagens de erro
  corretas em respostas 4xx.

## [0.4.4] - 2026-03-11

### Corrigido

- `cancel_nfse()` agora aceita e encaminha `cnpj_prestador` para
  `build_cancel_event()`, preenchendo o campo `CNPJAutor` no XML
  `pedRegEvento`. A SEFIN exige esse campo para identificar o autor do
  cancelamento; sua ausência causava HTTP 404 no endpoint `/eventos`, mesmo
  quando a NFS-e existia.

## [0.4.2] - 2026-03-11

### Corrigido

- `cancel_nfse()` não envia mais JSON simples para `/eventos`, o que causava
  HTTP 404 em produção. Agora ele constrói um documento XML `pedRegEvento`
  assinado (tipo de evento `e101101`), compacta-o com gzip, codifica-o em
  base64 e o envia como `{"pedidoRegistroEventoXmlGZipB64": ...}` — o mesmo
  padrão usado por `submit_dps()`.
- `_parse_event_response()` foi atualizado para tratar o formato de resposta
  `retEvento` da SEFIN (`cStat: 144` = sucesso, `idEvento` como protocolo).
- Testes obsoletos referenciavam o elemento XML `subst1`, renomeado para
  `subst` na versão 0.4.1.

### Adicionado

- `XMLBuilder.build_cancel_event()` — produz o XML `pedRegEvento/infPedReg`
  exigido pelo endpoint de cancelamento da SEFIN.
- `cancel_nfse()` agora aceita o parâmetro opcional `codigo_motivo: int = 1`
  (1 = erro na emissão, 2 = serviço não prestado, 4 = duplicidade).
- `XMLSignerService.sign()` agora trata tanto documentos DPS (`infDPS`) quanto
  documentos de evento (`infPedReg`) sem métodos separados.

## [0.4.1] - 2026-02-03

### Corrigido

- O elemento XML de substituição da NFSe foi renomeado de `subst1` para
  `subst`, em conformidade com o schema oficial.

## [0.4.0] - 2026-01-28

### Adicionado

- Suporte à substituição de NFSe por meio de `substitute_nfse()` e do modelo
  `SubstituicaoNFSe`.

### Alterado

- A licença foi alterada de MIT para AGPL-3.0.

## [0.3.2] - 2026-01-20

### Corrigido

- O gerador de PDF agora extrai e renderiza o endereço do tomador no DANFSe.
- A extração de `nfse_number` agora lê o número do XML da NFSe, em vez de
  derivá-lo de `chave_acesso`.

## [0.3.0] - 2026-01-10

### Adicionado

- Gerador local de PDF DANFSe (`pdf_generator.py`) como alternativa à API
  oficial do DANFSe, que é pouco confiável em produção.
- Cobertura abrangente de testes unitários para o cliente e o gerador de PDF.

## [0.2.0] - 2025-12-20

### Adicionado

- `query_convenio_municipal()` — verifica se um município aderiu ao sistema
  nacional de NFSe.
- Validação abrangente de campos com mensagens de erro em português para CNPJ,
  CPF, CEP, UF e códigos de serviço.
- Utilitário de linha de comando para emitir NFSe.

## [0.1.0] - 2025-12-01

### Adicionado

- Lançamento inicial.
- `NFSeClient` com suporte a mTLS para certificados PKCS12.
- `submit_dps()` — cria, assina e envia uma DPS para receber uma NFSe.
- `query_nfse()` — consulta uma NFSe pela chave de acesso.
- `download_danfse()` — baixa o PDF DANFSe da API oficial.
- `cancel_nfse()` — registra um evento de cancelamento.
- Modelos Pydantic: `DPS`, `Prestador`, `Tomador`, `Servico`, `NFSeResponse`,
  `EventResponse`.
- Builder de XML e assinador de XML usando `lxml` e `signxml`.
- Suporte aos ambientes de homologação e produção.

[0.9.1]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.5.0...v0.9.0
[0.5.0]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.4.7...v0.5.0
[0.4.7]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.4.4...v0.4.5
[0.4.1]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.3.0...v0.3.2
[0.3.0]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/roberto-mello/pynfse-nacional/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/roberto-mello/pynfse-nacional/releases/tag/v0.1.0
