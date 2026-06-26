from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

import requests


@dataclass(frozen=True)
class SlackImage:
    file_id: str
    name: str
    mimetype: str
    saved_path: Path


@dataclass(frozen=True)
class SlackMessage:
    ts: str
    datetime_utc: str
    user: str
    text: str
    images: list[SlackImage]


class SlackClient:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token.strip()
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.bot_token}"})

    def fetch_channel_messages(
        self,
        channel_id: str,
        limit: int,
        download_dir: str | Path,
    ) -> list[SlackMessage]:
        data = self._slack_get(
            "conversations.history",
            params={
                "channel": channel_id,
                "limit": limit,
            },
        )
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            raise RuntimeError("Slack API response did not include messages")

        return [
            self._parse_message(message, download_dir)
            for message in reversed(messages)
            if isinstance(message, dict)
        ]

    def _parse_message(
        self,
        message: dict[str, Any],
        download_dir: str | Path,
    ) -> SlackMessage:
        ts = str(message.get("ts", ""))
        return SlackMessage(
            ts=ts,
            datetime_utc=self._format_slack_ts(ts),
            user=str(message.get("user") or message.get("bot_id") or "unknown"),
            text=str(message.get("text") or ""),
            images=self._download_message_images(message, Path(download_dir)),
        )

    def _download_message_images(
        self,
        message: dict[str, Any],
        download_dir: Path,
    ) -> list[SlackImage]:
        download_dir.mkdir(parents=True, exist_ok=True)
        images: list[SlackImage] = []

        for file_data in message.get("files", []):
            if not isinstance(file_data, dict) or not self._is_image_file(file_data):
                continue

            file_id = str(file_data.get("id") or "file")
            name = str(file_data.get("name") or f"{file_id}.image")
            mimetype = str(file_data.get("mimetype") or "application/octet-stream")
            download_url = file_data.get("url_private_download") or file_data.get("url_private")
            if not isinstance(download_url, str) or not download_url:
                continue

            saved_path = download_dir / f"{file_id}_{self._safe_filename(name)}"
            response = self.session.get(download_url, stream=True, timeout=60)
            self._raise_http_error(response)

            with saved_path.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)

            images.append(
                SlackImage(
                    file_id=file_id,
                    name=name,
                    mimetype=mimetype,
                    saved_path=saved_path,
                )
            )

        return images

    def _slack_get(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(
            f"https://slack.com/api/{method}",
            params=params,
            timeout=30,
        )
        self._raise_http_error(response)

        data = response.json()
        if data.get("ok") is not True:
            raise RuntimeError(f"Slack API error in {method}: {data.get('error')}")

        return data

    @staticmethod
    def _is_image_file(file_data: dict[str, Any]) -> bool:
        mimetype = str(file_data.get("mimetype") or "")
        return mimetype.startswith("image/")

    @staticmethod
    def _safe_filename(filename: str) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
        return safe_name or "image"

    @staticmethod
    def _format_slack_ts(ts: str) -> str:
        try:
            timestamp = float(ts)
        except ValueError:
            return "unknown"
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()

    @staticmethod
    def _raise_http_error(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise RuntimeError(
                f"HTTP error {response.status_code}: {response.text}"
            ) from error
