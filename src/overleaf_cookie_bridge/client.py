import html
import json
from dataclasses import dataclass
from typing import Literal

import requests
from bs4 import BeautifulSoup

from .auth import make_session, redact_secrets


class OverleafBridgeError(RuntimeError):
    pass


class InvalidSessionError(OverleafBridgeError):
    pass


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    last_updated: str
    access_level: str
    source: str
    archived: bool
    trashed: bool

    @classmethod
    def from_data(cls, data: dict) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            last_updated=data.get("lastUpdated", ""),
            access_level=data.get("accessLevel", ""),
            source=data.get("source", ""),
            archived=bool(data.get("archived", False)),
            trashed=bool(data.get("trashed", False)),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "last_updated": self.last_updated,
            "access_level": self.access_level,
            "source": self.source,
            "archived": self.archived,
            "trashed": self.trashed,
        }


@dataclass(frozen=True)
class UploadedEntity:
    entity_id: str
    entity_type: Literal["doc", "file", "folder"]


def parse_projects_html(content: str | bytes) -> list[Project]:
    soup = BeautifulSoup(content, "html.parser")
    meta = soup.find("meta", attrs={"name": "ol-prefetchedProjectsBlob"})
    if meta is None or not meta.get("content"):
        raise InvalidSessionError(
            "Could not find Overleaf projects blob. The session cookie may be missing, "
            "expired, or not authorized."
        )
    raw = html.unescape(meta["content"])
    data = json.loads(raw)
    return [Project.from_data(item) for item in data.get("projects", [])]


def parse_csrf_html(content: str | bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    meta = soup.find("meta", attrs={"name": "ol-csrfToken"})
    if meta is None or not meta.get("content"):
        raise InvalidSessionError("Could not find Overleaf CSRF token on project page.")
    return str(meta["content"])


class OverleafCookieClient:
    def __init__(self, session2: str, host: str = "www.overleaf.com", timeout: int = 30):
        self.host = host.strip().removeprefix("https://").removeprefix("http://").rstrip("/")
        self.timeout = timeout
        self.session = make_session(session2, host=self.host)

    def _url(self, path: str) -> str:
        return f"https://{self.host}{path}"

    def _get(self, path: str) -> requests.Response:
        try:
            response = self.session.get(self._url(path), timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise OverleafBridgeError(redact_secrets(str(exc))) from exc

    def _post(self, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.post(self._url(path), timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise OverleafBridgeError(redact_secrets(str(exc))) from exc

    def _delete(self, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.delete(self._url(path), timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise OverleafBridgeError(redact_secrets(str(exc))) from exc

    def verify(self) -> bool:
        self.list_projects(include_archived=True, include_trashed=True)
        return True

    def list_projects(
        self,
        *,
        include_archived: bool = False,
        include_trashed: bool = False,
    ) -> list[Project]:
        response = self._get("/")
        projects = parse_projects_html(response.text)
        return [
            project
            for project in projects
            if (include_archived or not project.archived)
            and (include_trashed or not project.trashed)
        ]

    def download_project_zip(self, project_id: str) -> bytes:
        response = self._get(f"/project/{project_id}/download/zip")
        return response.content

    def get_csrf_token(self, project_id: str) -> str:
        response = self._get(f"/project/{project_id}")
        return parse_csrf_html(response.text)

    def upload_file(
        self,
        project_id: str,
        folder_id: str,
        file_name: str,
        file_content: bytes,
    ) -> UploadedEntity:
        csrf_token = self.get_csrf_token(project_id)
        response = self._post(
            f"/project/{project_id}/upload?folder_id={folder_id}",
            files={
                "relativePath": (None, "null"),
                "name": (None, file_name),
                "type": (None, "application/octet-stream"),
                "qqfile": (file_name, file_content, "application/octet-stream"),
            },
            headers={
                "Referer": self._url(f"/project/{project_id}"),
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "x-csrf-token": csrf_token,
            },
        )
        data = response.json()
        return UploadedEntity(entity_id=data["entity_id"], entity_type=data["entity_type"])

    def delete_entity(
        self,
        project_id: str,
        entity_type: Literal["doc", "file", "folder"],
        entity_id: str,
    ) -> None:
        csrf_token = self.get_csrf_token(project_id)
        self._delete(
            f"/project/{project_id}/{entity_type}/{entity_id}",
            json={},
            headers={
                "Referer": self._url(f"/project/{project_id}"),
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "x-csrf-token": csrf_token,
            },
        )
