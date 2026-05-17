# Endpoint Notes

This project uses a small subset of Overleaf's web behavior. These endpoints are unofficial and may change.

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

## Project Page / CSRF

```http
GET https://www.overleaf.com/project/{project_id}
```

The parser extracts:

```html
<meta name="ol-csrfToken" content="...">
```

The token is required for upload and delete requests.

## Source Zip Download

```http
GET https://www.overleaf.com/project/{project_id}/download/zip
```

Used by:

```bash
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID DESTINATION
overleaf-cookie push-file PROJECT_ID LOCAL_FILE --remote REMOTE_PATH --folder-id FOLDER_ID --entity-id ENTITY_ID --yes
```

`pull` writes a backup zip first, then validates member paths before extraction.

`push-file` downloads the zip before replacement for backup and after replacement for byte-for-byte verification.

## Upload File / Doc

```http
POST https://www.overleaf.com/project/{project_id}/upload?folder_id={folder_id}
```

The CLI sends multipart form data:

```text
relativePath = null
name = <file name>
type = application/octet-stream
qqfile = <file bytes>
```

Required headers include:

```text
Referer: https://www.overleaf.com/project/{project_id}
x-csrf-token: <token from project page>
```

The response contains the new entity id and type:

```json
{"success": true, "entity_id": "...", "entity_type": "doc"}
```

## Delete Entity

```http
DELETE https://www.overleaf.com/project/{project_id}/{entity_type}/{entity_id}
```

Used by `push-file` to remove the exact entity being replaced before uploading the new file. Required headers include `Referer` and `x-csrf-token`.
