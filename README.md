# overleaf-cookie-bridge

[中文说明](README.zh-CN.md)

A small, cookie-only CLI for safely reading, backing up, pulling, and replacing selected Overleaf project files through the web session used by your browser.

It is designed for agent-assisted paper workflows where Git access is unavailable or inconvenient:

- verify an `overleaf_session2` cookie
- list visible Overleaf projects
- download a full project zip backup
- pull a project into a local workspace
- replace one known remote file through backup, delete, upload, and zip verification

Important: Overleaf does not provide a public stable API for this workflow. This project uses unofficial web endpoints and should be treated as a best-effort bridge.

## Status

Current release: `0.1.0`

Implemented commands:

```bash
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID ./paper
overleaf-cookie push-file PROJECT_ID ./main.tex --remote main.tex --folder-id FOLDER_ID --entity-id ENTITY_ID --dry-run
overleaf-cookie push-file PROJECT_ID ./main.tex --remote main.tex --folder-id FOLDER_ID --entity-id ENTITY_ID --yes
```

## Installation

For local development:

```bash
git clone https://github.com/Master-chenk/overleaf-cookie-bridge.git
cd overleaf-cookie-bridge
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

For minimal runtime install from a local checkout:

```bash
pip install -e .
```

## Authentication

Set the Overleaf browser session cookie in your current shell:

```bash
export OVERLEAF_SESSION2='<your overleaf_session2 cookie>'
```

The cookie is equivalent to a live login session. Do not commit it, paste it into issues, or store it in shell scripts.

After work is complete, consider logging out of Overleaf or rotating/invalidating the session if the cookie was exposed.

## Quick Start

```bash
source .venv/bin/activate
export OVERLEAF_SESSION2='<redacted>'

overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie pull PROJECT_ID ./paper
```

Backups are saved under:

```text
~/.overleaf-cookie-bridge/backups/PROJECT_ID/TIMESTAMP.zip
```

You can override the backup root:

```bash
export OVERLEAF_COOKIE_BACKUP_ROOT=/path/to/backups
```

## Commands

### Verify cookie

```bash
overleaf-cookie verify
```

Expected output:

```text
OK: cookie is valid; visible projects: N
```

### List projects

```bash
overleaf-cookie list
overleaf-cookie list --json
overleaf-cookie list --all --json
```

### Backup project

```bash
overleaf-cookie backup PROJECT_ID
```

### Pull project

```bash
overleaf-cookie pull PROJECT_ID ./paper
```

This downloads a backup zip and safely extracts the project. Zip path traversal entries are rejected.

### Replace one remote file

Preview the write plan without changing Overleaf:

```bash
overleaf-cookie push-file PROJECT_ID ./main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --dry-run
```

Execute after reviewing the plan:

```bash
overleaf-cookie push-file PROJECT_ID ./main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --yes
```

`push-file` downloads a full backup zip first, deletes the specified existing entity, uploads the local file to the specified folder, then downloads the zip again and verifies the remote bytes match the local file.

You must provide the current Overleaf `folder_id` and `entity_id`. Use a throwaway file first when validating a project. Replacing a `doc` may change its internal Overleaf entity id and can affect comments/history attached to that file.

## Safety Model

The CLI is conservative:

- full zip backup before local extraction or remote replacement
- remote replacement requires `--yes`
- `push-file --dry-run` previews the plan without remote mutation
- `push-file --yes` verifies by downloading the project zip after upload
- secret redaction in common error paths
- path traversal protection during extraction

See `SKILL.md` for the agent runbook.

## Development

```bash
source .venv/bin/activate
pytest -q
ruff check .
python -m build
```

If `build` or `ruff` is missing:

```bash
pip install -e '.[dev]'
```

## Project Layout

```text
src/overleaf_cookie_bridge/auth.py       # cookie handling and redaction
src/overleaf_cookie_bridge/client.py     # project listing, zip download, CSRF, upload/delete
src/overleaf_cookie_bridge/remote_zip.py # zip member verification helpers
src/overleaf_cookie_bridge/sync.py       # backup zip and safe extraction
src/overleaf_cookie_bridge/tree.py       # entity tree helpers
src/overleaf_cookie_bridge/cli.py        # click CLI
tests/                                   # pytest suite
docs/                                    # endpoint notes and maintainer docs
SKILL.md                                 # agent runbook
```

## Security

Please do not file public issues containing cookies, project source zips, private paper text, or Overleaf project IDs that should remain private.

Report sensitive issues privately according to `SECURITY.md`.

## Related Work

- https://github.com/jkulhanek/pyoverleaf — reference implementation for Overleaf cookie/session behavior.
- Overleaf Git integration — preferred when available because it is official and versioned.

## License

MIT. See `LICENSE`.
