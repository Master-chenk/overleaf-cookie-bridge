# Security Policy

## Supported Versions

This project is experimental. Security fixes are made on the default branch until a stable release policy exists.

## Sensitive Data

Do not include any of the following in public issues, pull requests, logs, screenshots, or examples:

- `overleaf_session2` cookies
- full `Cookie:` headers
- Overleaf project zips containing private papers
- private Overleaf project IDs or names
- unpublished paper text, reviewer comments, or bibliography dumps

An Overleaf session cookie is equivalent to a live login session. If it is exposed, invalidate it by logging out of Overleaf sessions or rotating the account session.

## Reporting a Vulnerability

If this repository is hosted on GitHub, use GitHub private vulnerability reporting if enabled. Otherwise contact the maintainer privately.

Please include:

- affected version or commit
- reproduction steps without real credentials
- expected impact
- suggested fix, if known

## Scope

This project uses unofficial Overleaf web endpoints. Breakage due to Overleaf changing private APIs is expected and is not necessarily a security issue unless it causes credential disclosure, unintended remote mutation, or data loss.
