# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-07-01

### Fixed
- Hardened gzipped NFSe decoding against oversized payloads, switched XML parsing
  in the signer and response-number extraction paths to a safer parser config,
  and removed raw sensitive values from validation errors.

### Added
- IBSCBS support for DPS payloads and XML emission, including the widened `opSimpNac`
  model and `regApIBSCBSSN` handling for Simples Nacional providers.
- Response-side IBSCBS parsing now populates `NFSe`, `NFSeQueryResult`, and the
  PDF parser data model from the response XML with a single XML parse.
- DANFSe PDF rendering now shows an optional IBSCBS totals lane when `totCIBS`
  is present, and leaves the layout unchanged when it is absent.
- `NFSeClient` now supports recovering an NFSe by DPS identifier with
  `query_nfse_by_dps(id_dps)` and checking availability with
  `has_nfse_by_dps(id_dps)`, using the official `GET /dps/{id}` and
  `HEAD /dps/{id}` endpoints.
- Vendored NFSe XSD v1.01-20260209 fixtures plus IBSCBS golden XML samples for
  schema validation coverage.

### Changed
- `DPS.optante_simples` (`bool`) was removed and replaced by
  `DPS.op_simp_nac` (`Literal['1', '2', '3', '4']`) to match the official
  NFSe schema. Old `optante_simples` inputs now fail fast because `DPS`
  forbids extra fields. Migration: `optante_simples=True` maps to
  `op_simp_nac='3'` and `False` maps to `op_simp_nac='1'`. For
  `op_simp_nac='3'` or `'4'`, also provide `reg_ap_trib_sn` and
  `reg_ap_ibs_cbs_sn`; for `'1'` or `'2'`, leave those fields unset.
- `verAplic` is now derived from the installed package version instead of using a
  hardcoded release string.
- Bumped the supported floors for `lxml` and `signxml` to match the current
  secure/runtime baseline.
- Updated project documentation and official schema references to the current
  2026-02-09 NFSe XSD package.

## [0.4.7] - 2026-06-15

### Fixed
- `_get_client()` context manager no longer swallows httpx network errors
  (`RemoteProtocolError`, `ConnectError`, etc.) from the yield body and
  misclassifies them as `NFSeCertificateError`. Only `httpx.Client()`
  construction errors are wrapped as `NFSeCertificateError`; errors during
  request execution now propagate to the correct `except httpx.TimeoutException`
  / `except httpx.RequestError` handlers in `submit_dps()`, `cancel_nfse()`,
  `query_nfse()`, `download_danfse()`, and `query_convenio_municipal()`.
- `Prestador.inscricao_municipal` is now optional and the DPS XML builder
  omits `<IM>` when the field is not provided, matching the official NFSe
  layout.

### Changed
- All E501 line-length violations in `client.py` resolved for ruff compliance.
- Imports sorted for isort/ruff compliance.
- Added a dedicated release checklist in `RELEASE_CHECKLIST.md` and linked it
  from `AGENTS.md` and `CLAUDE.md` so release steps stay centralized.
- Cleaned lint debt in the touched release files without changing NFSe
  transport behavior.

## [0.4.6] - 2026-03-11

### Fixed
- `cancel_nfse()`, `query_nfse()`, and `download_danfse()` now validate that
  `chave_acesso` is exactly 50 numeric digits before URL interpolation, raising
  `ValueError` on invalid input.
- `_parse_event_response()` correctly distinguishes a confirmed `retEvento.cStat=144`
  success from a legacy `{protocolo: "..."}` response — previously both fell through
  the same code path, producing `success=True` with `protocolo=None` when `retEvento`
  was absent.
- `_parse_event_response()` now aggregates all entries in the SEFIN `erro` array into
  a single joined error message, rather than silently discarding all but the first.
- `descricao` and `complemento` fields from SEFIN error responses are capped at 255
  characters to prevent unbounded log entries.
- `_get_client()` initialises temp file paths to `None` before writing, preventing a
  potential `NameError` in the `finally` cleanup block if a write fails mid-way.

### Changed
- Removed unused internal constants `REGIME_SIMPLES_NACIONAL`, `REGIME_SIMPLES_EXCESSO`,
  `REGIME_NORMAL`, `REGIME_MEI`, `STATUS_EMITIDA`, `STATUS_CANCELADA`, `STATUS_SUBSTITUIDA`
  from `constants.py` — these were never exported and not referenced anywhere in the library.

## [0.4.5] - 2026-03-12

### Fixed
- `cancel_nfse()` now posts to the correct endpoint `/nfse/{chave}/eventos` instead
  of `/eventos`, which returned HTTP 404 (resource not found).
- `infPedReg` `Id` attribute now follows XSD type `TSIdPedRegEvt` pattern
  `PRE[0-9]{56}`: `PRE` + 50-digit chave + 6-digit event code `101101`. Previously
  used `PRE{chave}1` (54 chars) which failed SEFIN schema validation with RNG6110.
- Removed `nPedRegEvento` element from `infPedReg` — it is not part of the schema
  and caused RNG6110 "invalid child element" errors.
- `_parse_event_response()` now parses SEFIN's `erro` array format
  (`[{codigo, descricao, complemento}]`) for proper error messages on 4xx responses.

## [0.4.4] - 2026-03-11

### Fixed
- `cancel_nfse()` now accepts and forwards `cnpj_prestador` to `build_cancel_event()`,
  populating the `CNPJAutor` field in the `pedRegEvento` XML. SEFIN requires this field
  to identify the cancellation author; omitting it caused HTTP 404 on the `/eventos`
  endpoint even when the NFS-e existed.

## [0.4.2] - 2026-03-11

### Fixed
- `cancel_nfse()` was sending plain JSON to `/eventos`, causing HTTP 404 in
  production. It now builds a signed `pedRegEvento` XML document (event type
  `e101101`), compresses it with gzip, base64-encodes it, and POSTs it as
  `{"pedidoRegistroEventoXmlGZipB64": ...}` — the same pattern used by
  `submit_dps()`.
- `_parse_event_response()` updated to handle the SEFIN `retEvento` response
  shape (`cStat: 144` = success, `idEvento` as protocolo).
- Stale tests referenced `subst1` XML element name that was renamed to `subst`
  in 0.4.1 to match the NFSe schema.

### Added
- `XMLBuilder.build_cancel_event()` — produces the `pedRegEvento/infPedReg`
  XML required by the SEFIN cancellation endpoint.
- `cancel_nfse()` now accepts an optional `codigo_motivo: int = 1` parameter
  (1 = erro na emissão, 2 = serviço não prestado, 4 = duplicidade).
- `XMLSignerService.sign()` now handles both DPS documents (`infDPS`) and
  event documents (`infPedReg`) without separate methods.

## [0.4.1] - 2026-02-03

### Fixed
- NFSe substitution XML element renamed from `subst1` to `subst` to match
  the official schema.

## [0.4.0] - 2026-01-28

### Added
- NFSe substitution support via `substitute_nfse()` and `SubstituicaoNFSe`
  model.

### Changed
- License changed from MIT to AGPL-3.0.

## [0.3.2] - 2026-01-20

### Fixed
- PDF generator now extracts and renders tomador address in DANFSe.
- `nfse_number` extraction now reads from the NFSe XML rather than
  deriving it from the `chave_acesso`.

## [0.3.0] - 2026-01-10

### Added
- Local DANFSe PDF generator (`pdf_generator.py`) as an alternative to the
  official DANFSE API (which is unreliable in production).
- Comprehensive unit tests for client and PDF generator.

## [0.2.0] - 2025-12-20

### Added
- `query_convenio_municipal()` — check whether a municipality has joined the
  national NFSe system.
- Comprehensive field validation with Portuguese error messages for CNPJ, CPF,
  CEP, UF, and service codes.
- CLI utility for issuing NFSe.

## [0.1.0] - 2025-12-01

### Added
- Initial release.
- `NFSeClient` with mTLS support for PKCS12 certificates.
- `submit_dps()` — build, sign, and submit a DPS to receive an NFSe.
- `query_nfse()` — query NFSe by access key.
- `download_danfse()` — download DANFSe PDF from the official API.
- `cancel_nfse()` — register a cancellation event.
- Pydantic models: `DPS`, `Prestador`, `Tomador`, `Servico`, `NFSeResponse`,
  `EventResponse`.
- XML builder and XML signer using `lxml` and `signxml`.
- Support for homologação and produção environments.

[0.5.0]: https://github.com/robmello/pynfse-nacional/compare/v0.4.7...v0.5.0
[0.4.7]: https://github.com/robmello/pynfse-nacional/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/robmello/pynfse-nacional/compare/v0.4.5...v0.4.6
[0.4.5]: https://github.com/robmello/pynfse-nacional/compare/v0.4.4...v0.4.5
[0.4.1]: https://github.com/robmello/pynfse-nacional/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/robmello/pynfse-nacional/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/robmello/pynfse-nacional/compare/v0.3.0...v0.3.2
[0.3.0]: https://github.com/robmello/pynfse-nacional/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/robmello/pynfse-nacional/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/robmello/pynfse-nacional/releases/tag/v0.1.0
