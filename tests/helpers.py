import io
import json
import zipfile


def project_html(projects):
    blob = json.dumps({"projects": projects})
    escaped = blob.replace(chr(34), "&quot;")
    return (
        '<html><head><meta name="ol-prefetchedProjectsBlob" '
        f'content="{escaped}"></head></html>'
    )


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()
