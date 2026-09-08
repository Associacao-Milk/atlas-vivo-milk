# Nextcloud cloud integration for Atlas Vivo MILK

Status: architecture approved for implementation; production credentials and storage capacity are not yet validated.

## Evidence and source boundary

A Drive file named `index.rst` (ID `1XFxu6vReyX2ohpdEGWTHOw2Nh6YxMx_Y`) was inspected on 2026-08-13. It is a 686-byte table of contents for the Nextcloud developer documentation and links to the upstream documentation repository. It is not an installer and does not contain the referenced documentation tree.

Treat the current official Nextcloud developer and administration manuals as canonical. Do not copy an isolated documentation index into the application as if it were a complete SDK.

## Deployment boundary

- Application code may be served by the Atlas subdomain.
- Personal data, Drive exports, credentials, audit records, indexes and migration checkpoints must remain outside every webroot.
- Do not write Atlas data into `public_html`, the Atlas document root, a Git repository or a GitHub Actions artifact.
- Preserve the main Associação MILK site and its document root.
- Configure the Nextcloud data directory outside the webroot during installation. Moving it later is a separate maintenance operation and must not be folded into the Drive migration.
- Use HTTPS only.

## Runtime configuration

Provide secrets through the hosting control plane or a private `0600` environment file outside the repository:

```text
NEXTCLOUD_BASE_URL=
NEXTCLOUD_USER=
NEXTCLOUD_APP_PASSWORD=
NEXTCLOUD_REMOTE_ROOT=/Atlas-Vivo-MILK
ATLAS_PRIVATE_ROOT=
```

Never use the account password. Create a dedicated Nextcloud app password and a dedicated restricted user. Rotate it independently of human login credentials.

## WebDAV contract

Use the supported WebDAV endpoint exposed by the installed Nextcloud version. The integration must:

1. validate TLS;
2. use bounded connect/read timeouts;
3. retry only idempotent reads and resumable uploads;
4. reject paths containing traversal components;
5. record status, byte count and checksum without logging credentials or personal content;
6. use a checkpoint per object;
7. treat an object as already present only after size and checksum verification;
8. preserve the Drive source unchanged.

## Agent permissions

Mistral and other agents receive tools, not unrestricted shell access:

- `inventory.read`: metadata and migration status only;
- `object.read`: explicitly selected objects;
- `object.write-staging`: writes only inside a staging prefix;
- `checkpoint.append`: append-only migration events;
- `publish.request`: prepares a release but cannot promote it;
- `audit.read`: sanitized technical audit events.

Deterministic pre-tool guards must deny deletion, permission changes, DNS changes, writes to the main domain, writes inside a webroot, and secret retrieval. Post-tool guards must verify expected node counts, byte counts, hashes and failure totals before fan-in.

## Capacity gate

The known Drive inventory is 4,870 files, 397 folders and 16,011,662,239 bytes. The migration must not begin until available private storage is measured and is sufficient for source objects, native Google exports, checkpoints and operational reserve. A documented 10 GB account is insufficient.

Recommended minimum:

- 25 GB for a migration without a second complete copy;
- 40 GB when staging and a recoverable backup must coexist.

## Rollout

1. Confirm private destination path, quota, filesystem ownership and backup.
2. Install or validate Nextcloud with data and configuration outside the webroot.
3. Create the dedicated restricted user and app password.
4. Run WebDAV health and capability probes without uploading personal data.
5. Upload a generated non-sensitive fixture to staging and verify checksum.
6. Run one bounded migration batch with checkpointing.
7. Reconcile discovered, transferred, verified, already-existing, failed and bytes.
8. Continue resumably only after the bounded batch has zero unexplained failures.
9. Keep public web deployment separate from the private-data migration.

## Non-goals

This specification does not authorize GitHub Actions to receive Drive credentials or personal files, does not declare the Drive migration complete, and does not create a production cPanel or Nextcloud token.
