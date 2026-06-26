import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from museum_cosense_bot.config import load_environment
from museum_cosense_bot.slack_client import SlackClient, SlackMessage


DEFAULT_HISTORY_LIMIT = 5


def main() -> None:
    load_environment()

    bot_token = os.getenv("SLACK_BOT_TOKEN")
    channel_name = os.getenv("SLACK_CHANNEL_NAME")
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    history_limit = _get_history_limit()
    download_dir = _resolve_download_dir(
        os.getenv("SLACK_IMAGE_DOWNLOAD_DIR", "data/slack-downloads")
    )

    if not bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is not set")
    if not channel_name:
        raise RuntimeError("SLACK_CHANNEL_NAME is not set")
    if not channel_id:
        raise RuntimeError("SLACK_CHANNEL_ID is not set")

    client = SlackClient(bot_token=bot_token)
    messages = client.fetch_channel_messages(
        channel_id=channel_id,
        limit=history_limit,
        download_dir=download_dir,
    )

    print(f"Channel: {channel_name} ({channel_id})")
    print(f"Fetched messages: {len(messages)}")
    for message in messages:
        _print_message(message)


def _get_history_limit() -> int:
    raw_value = os.getenv("SLACK_HISTORY_LIMIT", str(DEFAULT_HISTORY_LIMIT))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError("SLACK_HISTORY_LIMIT must be an integer") from error

    if value < 1:
        raise RuntimeError("SLACK_HISTORY_LIMIT must be 1 or greater")

    return value


def _resolve_download_dir(raw_path: str) -> Path:
    download_dir = Path(raw_path)
    if download_dir.is_absolute():
        return download_dir
    return PROJECT_ROOT / download_dir


def _print_message(message: SlackMessage) -> None:
    print("-" * 60)
    print(f"ts: {message.ts}")
    print(f"datetime_utc: {message.datetime_utc}")
    print(f"user: {message.user}")
    print("text:")
    print(message.text or "(no text)")

    if not message.images:
        print("images: none")
        return

    print("images:")
    for image in message.images:
        print(f"- id: {image.file_id}")
        print(f"  name: {image.name}")
        print(f"  mimetype: {image.mimetype}")
        print(f"  saved_path: {image.saved_path}")


if __name__ == "__main__":
    main()