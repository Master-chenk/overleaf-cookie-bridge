# Overleaf Cookie Bridge Design Notes

Goal: provide a small local CLI that can access and update selected Overleaf project files using only a browser session cookie.

Architecture:

- Python package with a small `OverleafCookieClient` wrapping Overleaf web endpoints.
- Credentials come from environment variables, never from committed files.
- Project downloads are always backed up before extraction or replacement.
- Zip extraction rejects path traversal entries.
- Remote replacement uses CSRF-protected delete+upload and verifies the result by downloading the project zip again.

Implemented scope:

1. `overleaf-cookie verify`
   - Uses `OVERLEAF_SESSION2`.
   - GET homepage and confirms projects blob exists.
2. `overleaf-cookie list --json`
   - Lists id/name/last_updated/access_level.
3. `overleaf-cookie backup PROJECT_ID`
   - Saves zip under `~/.overleaf-cookie-bridge/backups/{project_id}/{timestamp}.zip`.
4. `overleaf-cookie pull PROJECT_ID DIR`
   - Downloads zip, saves backup, validates zip paths, extracts to DIR.
5. `overleaf-cookie push-file PROJECT_ID LOCAL_FILE --remote REMOTE_PATH --folder-id FOLDER_ID --entity-id ENTITY_ID --dry-run`
   - Downloads zip, writes backup, verifies remote path exists, prints replacement plan, does not mutate Overleaf.
6. `overleaf-cookie push-file PROJECT_ID LOCAL_FILE --remote REMOTE_PATH --folder-id FOLDER_ID --entity-id ENTITY_ID --yes`
   - Downloads zip and backup.
   - Deletes the specified entity.
   - Uploads the local file into the specified folder.
   - Downloads zip again and verifies remote bytes match local bytes.

Security rules:

- Never print cookie values.
- Redact `overleaf_session2=...` and `Cookie: ...` in exceptions/logs.
- Do not commit `.env`.
- Treat downloaded project zips as private paper data unless the user says otherwise.
- Require explicit `--yes` for remote mutation.
- Prefer `--dry-run` before `--yes`.
- Always report backup paths for recovery.
