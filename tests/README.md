# Tests

## Homologacao

Run the live homologacao suite with:

```bash
uv run pytest --run-homologacao -m homologacao -v -s
```

Requirements:

- `NFSE_TEST_CERT_PATH` in `.env`
- `NFSE_TEST_CERT_PASSWORD` in macOS Keychain
- A valid ICP-Brasil A1 test certificate (`.pfx`)
- Optional `NFSE_TEST_PRESTADOR_CNPJ` and `NFSE_TEST_PRESTADOR_IM` in `.env`

Store the password in macOS Keychain or another secret manager. Do not pass it
inline on the shell.

The `homologacao` marker selects `tests/test_client_integration.py`.
The `--run-homologacao` flag is required because these tests call the external
SEFIN service and may issue a test NFSe.
The checked-in defaults are synthetic. Set the optional prestador variables to
the homologacao identity authorized by the test certificate when the release
gate must issue successfully; keep those values only in the git-ignored `.env`.

Known issue:

- `E0116` requires the issuer IM in the CNC canonical representation. Numeric
  IM values are now zero-padded to 15 characters before DPS submission; the
  synthetic fixture validates against the official XSD; a successful live
  issuance requires a registered homologacao prestador identity.
- SEFIN homologacao may return `E999 / Erro não catalogado` for a valid DPS.
- The live integration test skips that response as server-side instability.
- During live repro, SEFIN returned a JSON body with top-level `erros` and
  capitalized `Codigo` / `Descricao` fields, not the lowercase keys the parser
  originally expected.
- The parser now normalizes that payload and surfaces `E999 / Erro não catalogado`.

## Notes

- The suite targets `ambiente="homologacao"`.
- If credentials are missing, the tests skip.
