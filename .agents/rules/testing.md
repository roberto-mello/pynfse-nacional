# Testing

- Framework: pytest with pytest-asyncio (`asyncio_mode = "auto"` — no need to mark coroutines explicitly)
- Integration tests require env vars: `NFSE_TEST_CERT_PATH`, `NFSE_TEST_CERT_PASSWORD`
- Integration tests are skipped by default when env vars are absent
- Unit tests mock the HTTP client (`unittest.mock.patch`) and XML signing
- Run targeted: `uv run pytest -x -k "test_name_pattern"`

## Test certificate credentials

- Cert path: `NFSE_TEST_CERT_PATH` in `.env` (gitignored; see `.env.example`).
- Cert password: macOS Keychain service `pynfse-nacional-tests`, account `cert-password`.
- Set it with: `security add-generic-password -a "cert-password" -s "pynfse-nacional-tests" -w`
- `tests/conftest.py` loads `.env` and resolves the password from Keychain when the env var is absent.
- Integration tests self-skip when either credential is empty.
