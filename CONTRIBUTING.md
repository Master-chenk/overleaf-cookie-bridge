# Contributing

Thanks for helping improve overleaf-cookie-bridge.

## Development Setup

```bash
git clone https://github.com/Master-chenk/overleaf-cookie-bridge.git
cd overleaf-cookie-bridge
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

## Quality Checks

Run before opening a pull request:

```bash
pytest -q
ruff check .
python -m build
```

## Test Policy

- Add tests for new behavior.
- Mock Overleaf HTTP responses in unit tests.
- Do not add tests that require real Overleaf cookies in CI.
- Manual integration tests must use Overleaf projects the tester is authorized to access.
- Manual tests must not commit downloaded project files, zips, cookies, or private paper text.

## Scope

This project exposes read-oriented commands:

- verify session cookie access
- list projects
- download project backups
- pull projects to a local workspace
- replace one known remote file with backup, explicit confirmation, and zip verification

Keep changes aligned with that scope.

## Secrets

Never commit cookies or private paper sources. If a secret is accidentally committed, rotate it and purge it from git history before publishing.
