# Tests

## Homologacao

Run the live homologacao suite with:

```bash
uv run pytest -m homologacao -v -s
```

Requirements:

- `NFSE_TEST_CERT_PATH` in `.env`
- `NFSE_TEST_CERT_PASSWORD` in macOS Keychain
- A valid ICP-Brasil A1 test certificate (`.pfx`)

Store the password in macOS Keychain or another secret manager. Do not pass it
inline on the shell.

The `homologacao` marker selects `tests/test_client_integration.py`.

Known issue:

- `E0116` requires the issuer IM in the CNC canonical representation. Numeric
  IM values are now zero-padded to 15 characters before DPS submission; the
  live issuer fixture now succeeds in homologacao.
- SEFIN homologacao may return `E999 / Erro não catalogado` for a valid DPS.
- The live integration test skips that response as server-side instability.
- During live repro, SEFIN returned a JSON body with top-level `erros` and
  capitalized `Codigo` / `Descricao` fields, not the lowercase keys the parser
  originally expected.
- The parser now normalizes that payload and surfaces `E999 / Erro não catalogado`.

## Notes

- The suite targets `ambiente="homologacao"`.
- If credentials are missing, the tests skip.
