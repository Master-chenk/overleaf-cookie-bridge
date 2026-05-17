---
name: overleaf-cookie-bridge
description: Use Overleaf Cookie Bridge to access and update Overleaf projects with only the browser session cookie. Use when a human or agent asks to verify cookie-only access, list projects, download a backup, pull a project locally, or replace one known remote file through backup, delete, upload, and zip verification. Treat the cookie as a live login credential and never print, commit, or store it in project files.
---

# Overleaf Cookie Bridge Agent Runbook

## Setup

Run commands from the repository root:

```bash
cd /Users/chenk/code/overleaf-cookie-bridge
source .venv/bin/activate
```

If the virtualenv is missing, recreate it with Python 3.11+:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

The cookie is a login credential. Never print it, commit it, or place it in examples. Prefer setting it only for the current shell:

```bash
export OVERLEAF_SESSION2='<redacted>'
```

The CLI is installed as:

```bash
overleaf-cookie --help
```

## Decision Matrix

| User intent | Command / workflow |
| --- | --- |
| Check whether cookie-only access works | `overleaf-cookie verify` |
| List visible projects and IDs | `overleaf-cookie list --json` |
| Create a timestamped backup only | `overleaf-cookie backup <PROJECT_ID>` |
| Pull a project to local disk | `overleaf-cookie pull <PROJECT_ID> <DEST_DIR>` |
| Inspect project source files after pull | `find <DEST_DIR> -maxdepth 2 -type f` or Hermes `search_files(target='files')` |
| Replace one known remote file | `overleaf-cookie push-file <PROJECT_ID> <LOCAL_FILE> --remote <PATH> --folder-id <FOLDER_ID> --entity-id <ENTITY_ID> --dry-run`, then repeat with `--yes` |
| Edit a paper | pull to local disk, edit local files, compile locally, then push one file at a time after dry-run review |

## Implemented Commands

```bash
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID DESTINATION
overleaf-cookie push-file PROJECT_ID LOCAL_FILE --remote REMOTE_PATH --folder-id FOLDER_ID --entity-id ENTITY_ID --dry-run
overleaf-cookie push-file PROJECT_ID LOCAL_FILE --remote REMOTE_PATH --folder-id FOLDER_ID --entity-id ENTITY_ID --yes
```

Implemented modules:

```text
src/overleaf_cookie_bridge/auth.py       # cookie handling and redaction
src/overleaf_cookie_bridge/client.py     # project list, zip download, CSRF, upload/delete
src/overleaf_cookie_bridge/remote_zip.py # zip member verification helpers
src/overleaf_cookie_bridge/sync.py       # backup zip and safe extraction
src/overleaf_cookie_bridge/tree.py       # entity tree helpers
src/overleaf_cookie_bridge/cli.py        # click CLI
```

Tests:

```bash
pytest -q
```

## Authentication Policy

Use the `overleaf_session2` cookie only through environment variables or a local secret store. The cookie is equivalent to a live login session.

Allowed:

```bash
OVERLEAF_SESSION2='<redacted>' overleaf-cookie verify
```

Avoid:

```bash
# Do not write real cookies to files committed to git
printf 'OVERLEAF_SESSION2=...' > .env
```

Never include real cookie values in:

- git commits
- `README.md`
- `SKILL.md`
- issue comments
- terminal summaries
- exception messages

If a cookie is exposed in chat or logs, tell the user it should be rotated or invalidated after the session.

## Core Endpoints Used

These are unofficial Overleaf web endpoints and may change.

| Purpose | Endpoint | Notes |
| --- | --- | --- |
| Project list | `GET https://www.overleaf.com/` | Parse `meta[name=ol-prefetchedProjectsBlob]` |
| Project page / CSRF | `GET /project/{project_id}` | Parse `meta[name=ol-csrfToken]` |
| Download source zip | `GET /project/{project_id}/download/zip` | Used for backup, pull, and post-upload verification |
| Upload file/doc | `POST /project/{project_id}/upload?folder_id={folder_id}` | Multipart upload, needs CSRF |
| Delete entity | `DELETE /project/{project_id}/{entity_type}/{entity_id}` | Needs CSRF; entity type is usually `doc` or `file` |

## Command Pipelines

### `verify`

```text
OVERLEAF_SESSION2
  -> requests.Session cookie jar
  -> GET https://www.overleaf.com/
  -> parse ol-prefetchedProjectsBlob
  -> report visible project count
```

### `list`

```text
OVERLEAF_SESSION2
  -> GET https://www.overleaf.com/
  -> parse ol-prefetchedProjectsBlob
  -> Project dataclasses
  -> table or JSON output
```

### `backup`

```text
OVERLEAF_SESSION2
  -> GET /project/{project_id}/download/zip
  -> write ~/.overleaf-cookie-bridge/backups/{project_id}/{timestamp}.zip
```

### `pull`

```text
OVERLEAF_SESSION2
  -> GET /project/{project_id}/download/zip
  -> write timestamped backup zip
  -> validate zip member paths
  -> extract to destination
```

### `push-file`

```text
OVERLEAF_SESSION2
  -> read local file bytes
  -> GET /project/{project_id}/download/zip
  -> write timestamped backup zip
  -> verify remote path exists in zip
  -> show replacement plan
  -> if --dry-run: stop without mutation
  -> if --yes:
       GET /project/{project_id} and parse CSRF
       DELETE /project/{project_id}/{entity_type}/{entity_id}
       GET /project/{project_id} and parse CSRF
       POST /project/{project_id}/upload?folder_id={folder_id}
       GET /project/{project_id}/download/zip
       compare remote bytes with local bytes
```

## Remote Replacement Safety Rules

`push-file` mutates Overleaf. Use it only when the user explicitly asks to update the remote project.

Required practice:

1. Run `push-file ... --dry-run` first.
2. Review project ID, remote path, local file, entity type, entity ID, folder ID, backup path, old size, and new size.
3. Execute only with `--yes` after the dry-run plan looks correct.
4. Report the backup path.
5. Report delete/upload entity IDs.
6. Report that post-upload zip verification succeeded.

Important limitations:

- The user must provide the current `folder_id` and `entity_id`; the CLI does not discover them yet.
- Replacing an Overleaf `doc` uses delete+upload and may change the internal entity ID.
- Replacing a `doc` may affect comments/history attached to that file.
- If verification fails, use the backup zip path printed by the command for recovery.

## Output Discipline

- Prefer `--json` for machine-readable project lists.
- Do not print full zip contents unless requested; summarize file counts and key paths.
- Do not paste large LaTeX files into chat; use file paths and diffs.
- Always report backup paths after `backup`, `pull`, or `push-file`.
- Never echo the cookie or raw `Cookie:` header.

## Paper Editing Workflow

For a paper change:

1. Verify cookie:

```bash
overleaf-cookie verify
```

2. Pull and back up:

```bash
overleaf-cookie pull PROJECT_ID /path/to/local-paper
```

3. Inspect structure:

```bash
find /path/to/local-paper -maxdepth 2 -type f
```

4. Edit local `.tex` or `.bib` files.
5. Compile locally when possible:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

6. Preview one remote file replacement:

```bash
overleaf-cookie push-file PROJECT_ID /path/to/local-paper/main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --dry-run
```

7. Execute after reviewing the plan:

```bash
overleaf-cookie push-file PROJECT_ID /path/to/local-paper/main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --yes
```

## Common Pitfalls

1. Using a cookie after it has been pasted into a transcript. It may still work, but the user should rotate it after the work is done.

2. Treating this tool as an official Overleaf API client. It uses web endpoints and HTML metadata, so breakage is possible.

3. Assuming a pull modifies Overleaf. `pull` only downloads and extracts locally.

4. Running `push-file` with stale entity IDs. If the remote file was replaced already, entity IDs may have changed.

5. Replacing a `doc` without understanding the delete+upload model. Comments/history tied to the old entity may be affected.

6. Depending on local edits without a backup. `pull` and `push-file` create backups; report the path to the user.

7. Printing cookies in shell history or logs. Use environment variables carefully and redact summaries.

## Verification Checklist

Before saying cookie-only Overleaf access is working:

- [ ] `overleaf-cookie verify` succeeds.
- [ ] `overleaf-cookie list --json` returns expected project IDs.
- [ ] `overleaf-cookie backup PROJECT_ID` writes a zip under `~/.overleaf-cookie-bridge/backups/`.
- [ ] `overleaf-cookie pull PROJECT_ID DEST` extracts expected `.tex` and `.bib` files.
- [ ] Tests pass with `pytest -q`.

Before saying remote replacement is complete:

- [ ] `push-file --dry-run` was reviewed.
- [ ] `push-file --yes` completed without HTTP errors.
- [ ] The command printed a backup zip path.
- [ ] The command printed deleted and uploaded entity IDs.
- [ ] The command printed `Verified remote content matches local file.`

## References

- `docs/ENDPOINTS.md` — endpoint notes for the implemented workflow.
- `https://github.com/jkulhanek/pyoverleaf` — reference implementation for Overleaf cookie/session behavior.
- `https://github.com/ZhongKuang/TAAC2026-CLI` — style reference for a repo-level `SKILL.md` runbook.
