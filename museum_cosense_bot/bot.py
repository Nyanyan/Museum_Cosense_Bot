from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from museum_cosense_bot.config import (
    LEGACY_ENV_PATH,
    PACKAGE_ENV_PATH,
    PROJECT_ROOT,
    load_environment,
    project_root,
)
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
        print(_event_summary("received message event", event, body), flush=True)
        event_id = str(body.get("event_id") or "")
        if event_id:
            if event_id in seen_event_ids:
                print(f"[slack:event] skipped duplicate event_id={event_id}", flush=True)
                return
            seen_event_ids.add(event_id)

        skip_reason = _message_skip_reason(event, config.slack_channel_id)
        if skip_reason:
            print(f"[slack:event] skipped: {skip_reason}", flush=True)
            return

        try:
            post = SlackCosensePost.from_message(
                channel_id=config.slack_channel_id,
                message=event,
            )
        except ValueError as error:
            logger.info("Skipped Slack message: %s", error)
            print(f"[slack:event] skipped: {error}", flush=True)
            return

        print(
            "[slack:event] accepted: "
            f"title={post.title!r}, body_lines={len(post.body_lines)}, "
            f"images={post.image_count}",
            flush=True,
        )
        slack.post_review_request(
            channel_id=config.slack_channel_id,
            thread_ts=post.message_ts,
            title=post.title,
            body_lines=post.body_lines,
            image_count=post.image_count,
        )
        print(
            f"[slack:event] posted review button in thread_ts={post.message_ts}",
            flush=True,
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
        user_id = body.get("user", {}).get("id", "unknown")
        print(
            "[slack:action] Post to Cosense clicked: "
            f"user={user_id}, channel={channel_id}, "
            f"message_ts={message_ts}, review_message_ts={review_message_ts}",
            flush=True,
        )

        try:
            print("[cosense] fetching original Slack message", flush=True)
            message = slack.fetch_message(
                channel_id=channel_id,
                message_ts=message_ts,
            )
            post = SlackCosensePost.from_message(
                channel_id=channel_id,
                message=message,
            )
            print(
                "[cosense] parsed Slack post: "
                f"title={post.title!r}, body_lines={len(post.body_lines)}, "
                f"images={post.image_count}",
                flush=True,
            )
            downloaded_images = slack.download_message_images(
                message=message,
                download_dir=config.image_download_dir,
            )
            print(f"[cosense] downloaded images: {len(downloaded_images)}", flush=True)
            image_urls = [
                cosense.upload_image_to_gyazo(
                    image_path=image.saved_path,
                    title=post.title,
                )
                for image in downloaded_images
            ]
            print(f"[cosense] uploaded images to Gyazo: {len(image_urls)}", flush=True)
            page_url = cosense.append_or_create_page(
                title=post.title,
                body_lines=post.cosense_body_lines(image_urls),
            )
            print(f"[cosense] posted page: {page_url}", flush=True)
        except Exception as error:
            logger.exception("Failed to post Slack message to Cosense")
            print(f"[cosense] failed: {error}", flush=True)
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
    _print_startup_diagnostics(config)
    app = create_app(config)
    print(
        f"Listening for Slack messages in "
        f"#{config.slack_channel_name} ({config.slack_channel_id})",
        flush=True,
    )
    print("[socket-mode] starting SocketModeHandler", flush=True)
    SocketModeHandler(app, config.slack_app_token).start()


def _message_skip_reason(event: dict[str, Any], target_channel_id: str) -> str | None:
    event_channel = event.get("channel")
    if event_channel != target_channel_id:
        return f"channel mismatch: event.channel={event_channel!r}, target={target_channel_id!r}"
    if event.get("bot_id"):
        return f"bot message: bot_id={event.get('bot_id')!r}"

    subtype = event.get("subtype")
    if subtype not in ALLOWED_TOP_LEVEL_SUBTYPES:
        return f"unsupported subtype: {subtype!r}"

    ts = event.get("ts")
    thread_ts = event.get("thread_ts")
    if thread_ts and thread_ts != ts:
        return f"thread reply: ts={ts!r}, thread_ts={thread_ts!r}"

    return None


def _should_handle_message(event: dict[str, Any], target_channel_id: str) -> bool:
    return _message_skip_reason(event, target_channel_id) is None


def _event_summary(label: str, event: dict[str, Any], body: dict[str, Any]) -> str:
    text = str(event.get("text") or "")
    text_preview = text.replace("\n", " ")[:120]
    files = event.get("files")
    file_count = len(files) if isinstance(files, list) else 0
    return (
        f"[slack:event] {label}: "
        f"event_id={body.get('event_id')!r}, "
        f"type={event.get('type')!r}, subtype={event.get('subtype')!r}, "
        f"channel={event.get('channel')!r}, user={event.get('user')!r}, "
        f"bot_id={event.get('bot_id')!r}, ts={event.get('ts')!r}, "
        f"thread_ts={event.get('thread_ts')!r}, files={file_count}, "
        f"text={text_preview!r}"
    )


def _print_startup_diagnostics(config: BotConfig) -> None:
    print("[config] .env search order:", flush=True)
    for path in [PROJECT_ROOT / ".env", PACKAGE_ENV_PATH, LEGACY_ENV_PATH]:
        print(f"[config] - {path} exists={path.exists()}", flush=True)
    print(f"[config] COSENSE_PROJECT={config.cosense_project}", flush=True)
    print(f"[config] SLACK_CHANNEL_NAME={config.slack_channel_name}", flush=True)
    print(f"[config] SLACK_CHANNEL_ID={config.slack_channel_id}", flush=True)
    print(f"[config] SLACK_IMAGE_DOWNLOAD_DIR={config.image_download_dir}", flush=True)
    print(f"[config] SLACK_BOT_TOKEN={_mask_secret(config.slack_bot_token)}", flush=True)
    print(f"[config] SLACK_APP_TOKEN={_mask_secret(config.slack_app_token)}", flush=True)


def _mask_secret(value: str) -> str:
    if len(value) <= 12:
        return "***"
    return f"{value[:8]}...{value[-4:]}"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


if __name__ == "__main__":
    main()