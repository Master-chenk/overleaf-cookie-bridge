# Overleaf Cookie Bridge Examples

## Minimal read-only workflow

```bash
export OVERLEAF_SESSION2='<redacted>'
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie pull PROJECT_ID ./paper
```

## Backup only

```bash
export OVERLEAF_COOKIE_BACKUP_ROOT=./backups
overleaf-cookie backup PROJECT_ID
```

## Agent-assisted paper workflow

```bash
overleaf-cookie pull PROJECT_ID ./paper
cd ./paper
latexmk -pdf -interaction=nonstopmode main.tex
```

Edit local `.tex` files and keep the backup zip printed by `pull` for recovery.
