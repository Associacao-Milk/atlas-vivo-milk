# FTPS secret authorization gate

This file documents only the authorization boundary. No credential value belongs in this repository.

Required GitHub Actions secret name: `PTSERVIDOR_FTPS_PASSWORD`.

The Mistral migration agent and repository workflow must never receive the secret value in prompts, responses, logs, artefacts, issues, commits, or corpus. The value is consumed only by the GitHub Actions runtime as an environment secret for the FTPS client.

Human gate: the repository owner enters the secret directly in GitHub Actions Secrets. After that gate, the migration workflow may be triggered to perform a canary upload, download-back and SHA-256 verification before any batch transfer.
