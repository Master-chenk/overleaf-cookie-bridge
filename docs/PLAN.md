# Overleaf Cookie Bridge Design Notes

Goal: provide a small local CLI that can access Overleaf projects using only a browser session cookie.

Architecture:

- Python package with a small `OverleafCookieClient` wrapping the read-oriented Overleaf web endpoints.
- Credentials come from environment variables, never from committed files.
- Project downloads are always backed up before extraction.
- Zip extraction rejects path traversal entries.

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

Security rules:

- Never print cookie values.
- Redact `overleaf_session2=...` and `Cookie: ...` in exceptions/logs.
- Do not commit `.env`.
- Treat downloaded project zips as private paper data unless the user says otherwise.
