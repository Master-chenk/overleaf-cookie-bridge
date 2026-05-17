# Endpoint Notes

This project uses a small read-oriented subset of Overleaf's web behavior. These endpoints are unofficial and may change.

## Authentication

The CLI authenticates by setting the `overleaf_session2` cookie on a `requests.Session` for the Overleaf host.

The cookie must come from the user environment:

```bash
export OVERLEAF_SESSION2='<redacted>'
```

Do not commit real cookies.

## Project List

```http
GET https://www.overleaf.com/
```

The response HTML includes a prefetched projects blob:

```html
<meta name="ol-prefetchedProjectsBlob" content="...">
```

The CLI parses this JSON blob and returns visible projects.

## Project Page / CSRF Parser

```http
GET https://www.overleaf.com/project/{project_id}
```

The parser can extract:

```html
<meta name="ol-csrfToken" content="...">
```

The current public CLI does not mutate Overleaf remotely, but keeping this parser tested helps detect page-shape changes.

## Source Zip Download

```http
GET https://www.overleaf.com/project/{project_id}/download/zip
```

Used by:

```bash
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID DESTINATION
```

`pull` writes a backup zip first, then validates member paths before extraction.
