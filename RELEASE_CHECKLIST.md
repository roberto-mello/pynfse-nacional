# Release Checklist

Use this checklist before cutting and pushing a release for `pynfse-nacional`.
For this repo, the release artifact is the annotated git tag plus the published
package metadata in the repository.

## Pre-release Checks

- Confirm the release bead or follow-up beads are closed, deferred, or filed.
- Verify `pyproject.toml` and `src/pynfse_nacional/__init__.py` report the same
  version.
- Confirm `CHANGELOG.md` contains the release entry for the target version.
- Run the test suite, or at minimum the affected tests for the release scope.
- Run the linter on the touched files, or the repo-wide lint command when the
  change is broad.
- Run the manual homologacao issuance test with a valid certificate. This test
  is intentionally not part of CI/CD because it requires mTLS credentials and
  calls the external SEFIN service:

  ```bash
  uv run pytest \\
    tests/test_client_integration.py::TestNFSeClientSubmitDPS::test_submit_dps_homologacao \\
    -v -s
  ```

  Set `NFSE_TEST_CERT_PATH` in the git-ignored repository `.env` file before
  running the command.
  Resolve `NFSE_TEST_CERT_PASSWORD` through the configured secret manager or
  Keychain; never commit or inline the password. Release gate passes only when
  the test reports `NFSe issued successfully`, with an access key and NFSe
  number. A business-rule rejection such as `E0116` is not a passing result.
- Check `git status --short --branch` and confirm there are no unexpected files.
- Confirm the release tag does not already exist.

## Release Steps

For a normal release, the one-command path is:

```bash
uv run release
```

The command reads the upload token from `UV_PUBLISH_TOKEN` or from
`~/.pypirc` if you have a `[pypi]` or `[testpypi]` section with
`username = __token__` and `password = <token>`.
If you keep a named repository section instead, such as `[pynfse-nacional]`
with `repository = https://upload.pypi.org/legacy/`, the release helper will
use that token too.

Use `--repository testpypi --dry-run` first if you want to validate the build
and upload flow against TestPyPI.

1. Update version metadata and changelog if they are not already aligned.
2. Run the required quality gates.
3. Close the release bead and file any remaining follow-up beads.
4. Commit the release-ready changes.
5. Run `git pull --rebase`.
6. Create an annotated tag, for example `v0.4.7`.
7. Push the branch and the tag.
8. Run `git status --short --branch` and confirm the branch is up to date with
   `origin`.

## Post-release Checks

- Confirm the tag exists locally and remotely.
- Confirm downstream consumers can reference the new tag or package version.
- If a package index release is part of the workflow, publish the artifact after
  the tag is pushed.

## Notes

- If a release introduces follow-up work, file a bead before closing the release.
- If the release scope changes after the checklist is complete, rerun the
  pre-release checks before tagging.
