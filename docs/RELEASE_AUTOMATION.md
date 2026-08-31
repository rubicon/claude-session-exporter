# Release automation

Releases are cut by [release-please](https://github.com/googleapis/release-please). On every push to
`main`, the `release-please` workflow reads the Conventional Commits since the last release, opens (or
updates) a release pull request that bumps the version and the changelog, and on merge tags the version
and publishes a GitHub release.

The workflow is committed, but it stays dormant until the credential secret below exists. Until then it
runs as a green no-op. This is intentional, so the automation can be reviewed and merged before the
one-time manual setup is done.

## Why a GitHub App is required

`main` requires signed, verified commits and a passing `test` check. The default `GITHUB_TOKEN` cannot
satisfy both: commits it makes do not trigger the CI workflow, so the release PR would never get its
required check. A GitHub App token does trigger CI and produces verified commits, so release-please uses
one. Credentials are pulled at run time from 1Password, so no App key is stored as a per-repo secret.

## One-time setup (maintainer)

1. **Create or reuse a GitHub App** with repository permissions `Contents: read and write` and
   `Pull requests: read and write`. Install it on `rubicon/claude-session-exporter`. Note its **App ID**
   and generate a **private key** (`.pem`).

2. **Store the App credentials in 1Password**, in a shared `Automation` vault, as an item named
   `rubicon_release_please_private_key` with two fields:
   - `app id` — the numeric App ID.
   - `private key` — the full `.pem`. Store it somewhere that preserves newlines, such as an SSH Key
     item's key field, a notes field, or a file attachment. A single-line text field flattens the
     newlines and the key will not parse. Verify with:
     `op read "op://Automation/rubicon_release_please_private_key/private key" | openssl rsa -noout -check`
     (never print the key itself).

   The item and field names above are the literal strings the workflow resolves, so they have to match
   the vault exactly, separators included.

3. **Create a 1Password service account** scoped **read-only** to the `Automation` vault, with an
   expiry. Add its token as the repo secret `OP_SERVICE_ACCOUNT_TOKEN`:
   `gh secret set OP_SERVICE_ACCOUNT_TOKEN -R rubicon/claude-session-exporter`

4. **Confirm Actions can run the workflow.** No repo-wide Actions write permission is needed: the App
   token carries the permissions, and the workflow requests `contents: write` / `pull-requests: write`
   at the job level.

Once the secret exists, the next push to `main` activates release-please. It reads the current version
from `.release-please-manifest.json` and proposes the next one from the Conventional Commits since that
release.

## Rotating credentials

Replace the key in the one 1Password item and every repo using this App picks it up. Rotate the service
account token before its expiry. If a private key is ever printed, generate a new App key, update the
vault, and delete the old one.
