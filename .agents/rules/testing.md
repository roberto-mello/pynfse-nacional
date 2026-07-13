# Testing

- Framework: pytest with pytest-asyncio (`asyncio_mode = "auto"` — no need to mark coroutines explicitly)
- Integration tests require env vars: `NFSE_TEST_CERT_PATH`, `NFSE_TEST_CERT_PASSWORD`
- Integration tests are skipped by default when env vars are absent
- Live homologacao tests are skipped unless `--run-homologacao` is passed
- Unit tests mock the HTTP client (`unittest.mock.patch`) and XML signing
- Run targeted: `uv run pytest -x -k "test_name_pattern"`

## Test certificate credentials

- Cert path: `NFSE_TEST_CERT_PATH` in `.env` (gitignored; see `.env.example`).
- Cert password: macOS Keychain service `pynfse-nacional-tests`, account `cert-password`.
- `tests/conftest.py` loads `.env` and resolves the password from Keychain when the env var is absent.
- Do not bypass Keychain in ad hoc shell repros by exporting the password directly; use the test helper so live runs stay secret-free.
- Integration tests self-skip when either credential is empty.
