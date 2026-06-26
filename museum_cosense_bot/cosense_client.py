import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


class CosenseClient:
    def __init__(self, project: str, connect_sid: str) -> None:
        self.project = project
        self.connect_sid = self._normalize_connect_sid(connect_sid)
        self.session = requests.Session()
        self.session.cookies.set(
            "connect.sid",
            self.connect_sid,
            domain="scrapbox.io",
            path="/",
        )

    def get_csrf_token(self) -> str:
        response = self.session.get("https://scrapbox.io/api/users/me", timeout=30)
        self._raise_for_status(response)

        data = response.json()
        if data.get("isGuest") is True:
            raise RuntimeError(
                "Cosense login session is not valid. "
                "Please set a fresh logged-in connect.sid cookie."
            )

        csrf_token = data.get("csrfToken")
        if not isinstance(csrf_token, str):
            return ""

        return csrf_token

    def import_page(self, title: str, lines: list[str]) -> str:
        csrf_token = self.get_csrf_token()
        page_lines = self._ensure_title_line(title, lines)
        payload = {
            "pages": [
                {
                    "title": title,
                    "lines": page_lines,
                }
            ]
        }
        json_body = json.dumps(payload, ensure_ascii=False)
        url = f"https://scrapbox.io/api/page-data/import/{self.project}.json"
        headers = self._same_origin_headers()
        if csrf_token:
            headers["X-CSRF-TOKEN"] = csrf_token

        response = self.session.post(
            url,
            headers=headers,
            data={"name": "undefined"},
            files={
                "import-file": (
                    "import.json",
                    json_body.encode("utf-8"),
                    "application/json",
                )
            },
            timeout=30,
        )
        self._raise_for_status(response)

        return self.page_url(title)

    def upload_image_to_gyazo(self, image_path: str | Path, title: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise RuntimeError(f"Image file was not found: {path}")

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if not content_type.startswith("image/"):
            raise RuntimeError(f"{path} is not an image file")

        gyazo_token = self._get_gyazo_oauth_token()
        with path.open("rb") as image_file:
            response = requests.post(
                "https://upload.gyazo.com/api/upload",
                data={
                    "access_token": gyazo_token,
                    "title": title,
                    "referer_url": self.page_url(title),
                },
                files={
                    "imagedata": (
                        path.name,
                        image_file,
                        content_type,
                    )
                },
                timeout=60,
            )
        self._raise_for_status(response)

        data = response.json()
        permalink_url = data.get("permalink_url")
        if not isinstance(permalink_url, str) or not permalink_url:
            raise RuntimeError("permalink_url was not found in Gyazo upload response")

        return permalink_url

    def page_url(self, title: str) -> str:
        return f"https://scrapbox.io/{self.project}/{quote(title, safe='')}"

    def _get_project(self) -> dict[str, Any]:
        response = self.session.get(
            f"https://scrapbox.io/api/projects/{self.project}",
            headers=self._same_origin_headers(),
            timeout=30,
        )
        self._raise_for_status(response)
        return response.json()

    def _get_gyazo_oauth_token(self) -> str:
        project = self._get_project()
        gyazo_teams_name = project.get("gyazoTeamsName") or ""
        response = self.session.get(
            "https://scrapbox.io/api/login/gyazo/oauth-upload/token",
            params={"gyazoTeamsName": gyazo_teams_name},
            headers=self._same_origin_headers(),
            timeout=30,
        )
        self._raise_for_status(response)

        data = response.json()
        token = data.get("token")
        if not isinstance(token, str) or not token:
            raise RuntimeError(
                "Gyazo OAuth token was not found. "
                "Please connect Gyazo from Cosense settings."
            )

        return token

    @staticmethod
    def _normalize_connect_sid(connect_sid: str) -> str:
        value = connect_sid.strip()

        if value.lower().startswith("cookie:"):
            value = value[len("cookie:") :].strip()

        if "connect.sid=" in value:
            for cookie_part in value.split(";"):
                name, separator, cookie_value = cookie_part.strip().partition("=")
                if separator and name == "connect.sid":
                    return cookie_value.strip()

        return value

    @staticmethod
    def _ensure_title_line(title: str, lines: list[str]) -> list[str]:
        if not lines or lines[0] != title:
            return [title, *lines]
        return lines

    def _same_origin_headers(self) -> dict[str, str]:
        return {
            "Origin": "https://scrapbox.io",
            "Referer": f"https://scrapbox.io/{self.project}",
        }

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            body = response.text
            raise RuntimeError(
                f"HTTP error {response.status_code}: {body}"
            ) from error
