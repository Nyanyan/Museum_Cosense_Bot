from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

import requests


POST_TO_COSENSE_ACTION_ID = "post_to_cosense"
RELOAD_REVIEW_ACTION_ID = "reload_review"


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

    def fetch_message(self, channel_id: str, message_ts: str) -> dict[str, Any]:
        data = self._slack_get(
            "conversations.replies",
            params={
                "channel": channel_id,
                "ts": message_ts,
                "limit": 1,
                "inclusive": True,
            },
        )
        messages = data.get("messages", [])
        if not isinstance(messages, list) or not messages:
            raise RuntimeError("Slack message was not found")
        message = messages[0]
        if not isinstance(message, dict):
            raise RuntimeError("Slack message response was invalid")
        return message

    def post_review_request(
        self,
        channel_id: str,
        thread_ts: str,
        title: str,
        body_lines: list[str],
        image_count: int,
    ) -> dict[str, Any]:
        return self.post_message(
            channel_id=channel_id,
            thread_ts=thread_ts,
            text=f"Cosense draft: {title}",
            blocks=self._review_blocks(
                channel_id=channel_id,
                message_ts=thread_ts,
                title=title,
                body_lines=body_lines,
                image_count=image_count,
                status_text=None,
                buttons_enabled=True,
            ),
        )

    def update_review_request_status(
        self,
        channel_id: str,
        review_message_ts: str,
        original_message_ts: str,
        title: str,
        body_lines: list[str],
        image_count: int,
        status_text: str,
    ) -> dict[str, Any]:
        return self.update_message(
            channel_id=channel_id,
            message_ts=review_message_ts,
            text=f"Cosense draft: {title} - {status_text}",
            blocks=self._review_blocks(
                channel_id=channel_id,
                message_ts=original_message_ts,
                title=title,
                body_lines=body_lines,
                image_count=image_count,
                status_text=status_text,
                buttons_enabled=False,
            ),
        )

    def post_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": channel_id,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks
        return self._slack_post("chat.postMessage", payload)

    def update_message(
        self,
        channel_id: str,
        message_ts: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": channel_id,
            "ts": message_ts,
            "text": text,
        }
        if blocks is not None:
            payload["blocks"] = blocks
        return self._slack_post("chat.update", payload)

    def download_message_images(
        self,
        message: dict[str, Any],
        download_dir: str | Path,
    ) -> list[SlackImage]:
        return self._download_message_images(message, Path(download_dir))

    @staticmethod
    def count_image_files(message: dict[str, Any]) -> int:
        return sum(
            1
            for file_data in message.get("files", [])
            if isinstance(file_data, dict) and SlackClient._is_image_file(file_data)
        )

    def _review_blocks(
        self,
        channel_id: str,
        message_ts: str,
        title: str,
        body_lines: list[str],
        image_count: int,
        status_text: str | None,
        buttons_enabled: bool,
    ) -> list[dict[str, Any]]:
        body_preview = "\n".join(body_lines).strip() or "(no body)"
        if len(body_preview) > 1800:
            body_preview = body_preview[:1800] + "..."

        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Cosense draft*\n"
                        f"*Title:* {title}\n"
                        f"*Body:*\n```{body_preview}```\n"
                        f"*Attached images:* {image_count}"
                    ),
                },
            }
        ]
        if status_text:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {status_text}",
                        }
                    ],
                }
            )
        if buttons_enabled:
            button_value = json.dumps(
                {
                    "channel_id": channel_id,
                    "message_ts": message_ts,
                },
                ensure_ascii=False,
            )
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Post to Cosense",
                            },
                            "style": "primary",
                            "action_id": POST_TO_COSENSE_ACTION_ID,
                            "value": button_value,
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reload",
                            },
                            "action_id": RELOAD_REVIEW_ACTION_ID,
                            "value": button_value,
                        },
                    ],
                }
            )
        return blocks

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
            download_url = file_data.get("url_private_download") or file_data.get(
                "url_private"
            )
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
        return self._parse_slack_response(method, response)

    def _slack_post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"https://slack.com/api/{method}",
            json=payload,
            timeout=30,
        )
        self._raise_http_error(response)
        return self._parse_slack_response(method, response)

    @staticmethod
    def _parse_slack_response(method: str, response: requests.Response) -> dict[str, Any]:
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