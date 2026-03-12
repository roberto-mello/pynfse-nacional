# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/robmello/pynfse-nacional/compare/v0.4.2...HEAD
[0.4.2]: https://github.com/robmello/pynfse-nacional/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/robmello/pynfse-nacional/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/robmello/pynfse-nacional/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/robmello/pynfse-nacional/compare/v0.3.0...v0.3.2
[0.3.0]: https://github.com/robmello/pynfse-nacional/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/robmello/pynfse-nacional/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/robmello/pynfse-nacional/releases/tag/v0.1.0
