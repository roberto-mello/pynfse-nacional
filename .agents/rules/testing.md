# Testing

- Framework: pytest with pytest-asyncio (`asyncio_mode = "auto"` — no need to mark coroutines explicitly)
- Integration tests require env vars: `NFSE_TEST_CERT_PATH`, `NFSE_TEST_CERT_PASSWORD`
- Integration tests are skipped by default when env vars are absent
- Unit tests mock the HTTP client (`unittest.mock.patch`) and XML signing
- Run targeted: `uv run pytest -x -k "test_name_pattern"`
