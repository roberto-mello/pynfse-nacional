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
- Check `git status --short --branch` and confirm there are no unexpected files.
- Confirm the release tag does not already exist.

## Release Steps

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
