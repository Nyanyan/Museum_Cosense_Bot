from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from museum_cosense_bot.config import load_environment, project_root
from museum_cosense_bot.cosense_client import CosenseClient
from museum_cosense_bot.slack_client import POST_TO_COSENSE_ACTION_ID, SlackClient
from museum_cosense_bot.slack_post import SlackCosensePost


ALLOWED_TOP_LEVEL_SUBTYPES = {None, "file_share"}


@dataclass(frozen=True)
class BotConfig:
    cosense_project: str
    cosense_connect_sid: str
    slack_bot_token: str
    slack_app_token: str
    slack_channel_id: str
    slack_channel_name: str
    image_download_dir: Path

    @classmethod
    def from_env(cls) -> "BotConfig":
        load_environment()
        root = project_root()
        image_download_dir = Path(
            os.getenv("SLACK_IMAGE_DOWNLOAD_DIR", "data/slack-downloads")
        )
        if not image_download_dir.is_absolute():
            image_download_dir = root / image_download_dir

        return cls(
            cosense_project=_required_env("COSENSE_PROJECT"),
            cosense_connect_sid=_required_env("COSENSE_CONNECT_SID"),
            slack_bot_token=_required_env("SLACK_BOT_TOKEN"),
            slack_app_token=_required_env("SLACK_APP_TOKEN"),
            slack_channel_id=_required_env("SLACK_CHANNEL_ID"),
            slack_channel_name=_required_env("SLACK_CHANNEL_NAME"),
            image_download_dir=image_download_dir,
        )


def create_app(config: BotConfig) -> App:
    app = App(token=config.slack_bot_token)
    slack = SlackClient(bot_token=config.slack_bot_token)
    cosense = CosenseClient(
        project=config.cosense_project,
        connect_sid=config.cosense_connect_sid,
    )
    seen_event_ids: set[str] = set()

    @app.event("message")
    def handle_message_event(
        event: dict[str, Any],
        body: dict[str, Any],
        logger: Any,
    ) -> None:
        event_id = str(body.get("event_id") or "")
        if event_id:
            if event_id in seen_event_ids:
                return
            seen_event_ids.add(event_id)

        if not _should_handle_message(event, config.slack_channel_id):
            return

        try:
            post = SlackCosensePost.from_message(
                channel_id=config.slack_channel_id,
                message=event,
            )
        except ValueError as error:
            logger.info("Skipped Slack message: %s", error)
            return

        slack.post_review_request(
            channel_id=config.slack_channel_id,
            thread_ts=post.message_ts,
            title=post.title,
            body_lines=post.body_lines,
            image_count=post.image_count,
        )

    @app.action(POST_TO_COSENSE_ACTION_ID)
    def handle_post_to_cosense(
        ack: Any,
        body: dict[str, Any],
        logger: Any,
    ) -> None:
        ack()
        action = body["actions"][0]
        value = json.loads(action["value"])
        channel_id = value["channel_id"]
        message_ts = value["message_ts"]
        review_message_ts = body["message"]["ts"]

        try:
            message = slack.fetch_message(
                channel_id=channel_id,
                message_ts=message_ts,
            )
            post = SlackCosensePost.from_message(
                channel_id=channel_id,
                message=message,
            )
            downloaded_images = slack.download_message_images(
                message=message,
                download_dir=config.image_download_dir,
            )
            image_urls = [
                cosense.upload_image_to_gyazo(
                    image_path=image.saved_path,
                    title=post.title,
                )
                for image in downloaded_images
            ]
            page_url = cosense.append_or_create_page(
                title=post.title,
                body_lines=post.cosense_body_lines(image_urls),
            )
        except Exception as error:
            logger.exception("Failed to post Slack message to Cosense")
            slack.post_message(
                channel_id=channel_id,
                thread_ts=message_ts,
                text=f"Failed to post to Cosense: {error}",
            )
            return

        slack.update_message(
            channel_id=channel_id,
            message_ts=review_message_ts,
            text=f"Posted to Cosense: {page_url}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Posted to Cosense*\n{page_url}",
                    },
                }
            ],
        )
        slack.post_message(
            channel_id=channel_id,
            thread_ts=message_ts,
            text=f"Posted to Cosense: {page_url}",
        )

    return app


def main() -> None:
    config = BotConfig.from_env()
    app = create_app(config)
    print(
        f"Listening for Slack messages in "
        f"#{config.slack_channel_name} ({config.slack_channel_id})"
    )
    SocketModeHandler(app, config.slack_app_token).start()


def _should_handle_message(event: dict[str, Any], target_channel_id: str) -> bool:
    if event.get("channel") != target_channel_id:
        return False
    if event.get("bot_id"):
        return False
    if event.get("subtype") not in ALLOWED_TOP_LEVEL_SUBTYPES:
        return False

    ts = event.get("ts")
    thread_ts = event.get("thread_ts")
    if thread_ts and thread_ts != ts:
        return False

    return True


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


if __name__ == "__main__":
    main()