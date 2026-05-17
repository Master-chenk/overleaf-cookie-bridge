---
name: overleaf-cookie-bridge
description: Use Overleaf Cookie Bridge to access Overleaf projects with only the browser session cookie. Use when a human or agent asks to verify cookie-only access, list Overleaf projects, download a full project backup, or pull an Overleaf paper into a local workspace without Git. Treat the cookie as a live login credential and never print, commit, or store it in project files.
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
| Edit a paper | pull to local disk, edit local files, compile locally, and keep the backup zip for recovery |

## Implemented Commands

```bash
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID DESTINATION
```

Implemented modules:

```text
src/overleaf_cookie_bridge/auth.py    # cookie handling and redaction
src/overleaf_cookie_bridge/client.py  # project list, zip download, CSRF parse
src/overleaf_cookie_bridge/sync.py    # backup zip and safe extraction
src/overleaf_cookie_bridge/tree.py    # entity tree helpers
src/overleaf_cookie_bridge/cli.py     # click CLI
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
| Project page / CSRF parser | `GET /project/{project_id}` | Parse `meta[name=ol-csrfToken]`; parser is present for endpoint compatibility checks |
| Download source zip | `GET /project/{project_id}/download/zip` | Used for backup and pull |

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

## Output Discipline

- Prefer `--json` for machine-readable project lists.
- Do not print full zip contents unless requested; summarize file counts and key paths.
- Do not paste large LaTeX files into chat; use file paths and diffs.
- Always report backup paths after `backup` or `pull`.
- Never echo the cookie or raw `Cookie:` header.

## Paper Editing Workflow

For a paper change with the current tool surface:

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

6. Keep the backup zip path from the pull output for recovery.

## Common Pitfalls

1. Using a cookie after it has been pasted into a transcript. It may still work, but the user should rotate it after the work is done.

2. Treating this tool as an official Overleaf API client. It uses web endpoints and HTML metadata, so breakage is possible.

3. Assuming a pull modifies Overleaf. `pull` only downloads and extracts locally.

4. Depending on local edits without a backup. `pull` already creates one; report the path to the user.

5. Printing cookies in shell history or logs. Use environment variables carefully and redact summaries.

## Verification Checklist

Before saying cookie-only Overleaf access is working:

- [ ] `overleaf-cookie verify` succeeds.
- [ ] `overleaf-cookie list --json` returns expected project IDs.
- [ ] `overleaf-cookie backup PROJECT_ID` writes a zip under `~/.overleaf-cookie-bridge/backups/`.
- [ ] `overleaf-cookie pull PROJECT_ID DEST` extracts expected `.tex` and `.bib` files.
- [ ] Tests pass with `pytest -q`.

## References

- `docs/ENDPOINTS.md` — endpoint notes for the implemented read/backup workflow.
- `https://github.com/jkulhanek/pyoverleaf` — reference implementation for Overleaf cookie/session behavior.
- `https://github.com/ZhongKuang/TAAC2026-CLI` — style reference for a repo-level `SKILL.md` runbook.
