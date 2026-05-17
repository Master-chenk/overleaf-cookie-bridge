# Maintainer Notes

## Release Checklist

1. Update `CHANGELOG.md`.
2. Update version in `pyproject.toml` and `src/overleaf_cookie_bridge/__init__.py`.
3. Run:

```bash
pytest -q
ruff check .
python -m build
python -m twine check dist/*
```

4. Tag:

```bash
git tag v0.1.0
git push origin main --tags
```

5. Publish when ready:

```bash
python -m twine upload dist/*
```

## Manual Integration Test

Use only a throwaway Overleaf project or a project the user explicitly allows reading.

```bash
export OVERLEAF_SESSION2='<redacted>'
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID /tmp/overleaf-cookie-test
```

Confirm:

- the cookie is never printed
- the backup zip exists
- expected project files appear under the destination
- no remote Overleaf state is changed
