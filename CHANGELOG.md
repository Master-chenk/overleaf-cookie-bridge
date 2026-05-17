# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows Keep a Changelog, and this project uses semantic versioning once releases begin.

## [0.1.0] - 2026-05-17

### Added

- Cookie-based Overleaf session handling through `OVERLEAF_SESSION2`.
- `overleaf-cookie verify` command.
- `overleaf-cookie list` and `overleaf-cookie list --json` commands.
- `overleaf-cookie backup PROJECT_ID` command.
- `overleaf-cookie pull PROJECT_ID DESTINATION` command.
- Safe zip extraction with path traversal protection.
- Timestamped project zip backups.
- Secret redaction helpers.
- Endpoint notes for the implemented read/backup workflow.
- Repo-level `SKILL.md` agent runbook.
