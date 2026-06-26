from dataclasses import dataclass
from typing import Any

from museum_cosense_bot.slack_client import SlackClient


@dataclass(frozen=True)
class SlackCosensePost:
    channel_id: str
    message_ts: str
    title: str
    body_lines: list[str]
    image_count: int

    @classmethod
    def from_message(
        cls,
        channel_id: str,
        message: dict[str, Any],
    ) -> "SlackCosensePost":
        text = str(message.get("text") or "")
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if not lines or not lines[0].strip():
            raise ValueError("Slack message first line is empty; cannot create title")

        return cls(
            channel_id=channel_id,
            message_ts=str(message.get("ts") or ""),
            title=lines[0].strip(),
            body_lines=lines[1:],
            image_count=SlackClient.count_image_files(message),
        )

    def cosense_body_lines(self, image_urls: list[str]) -> list[str]:
        lines = list(self.body_lines)
        if image_urls:
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(f"[{url}]" for url in image_urls)
        return lines
