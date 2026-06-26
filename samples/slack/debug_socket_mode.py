import json
import os
import sys
from pathlib import Path
from threading import Event
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web import WebClient

from museum_cosense_bot.config import (
    LEGACY_ENV_PATH,
    PACKAGE_ENV_PATH,
    PROJECT_ROOT as CONFIG_PROJECT_ROOT,
    load_environment,
)


TARGET_CHANNEL_ID = "SLACK_CHANNEL_ID"


def main() -> None:
    load_environment()

    bot_token = _required_env("SLACK_BOT_TOKEN")
    app_token = _required_env("SLACK_APP_TOKEN")
    channel_id = _required_env("SLACK_CHANNEL_ID")
    channel_name = os.getenv("SLACK_CHANNEL_NAME", "")

    print("=" * 72, flush=True)
    print("Slack Socket Mode debug receiver", flush=True)
    print("This script only prints Slack payloads. It does not post to Cosense.", flush=True)
    print("=" * 72, flush=True)
    _print_env_diagnostics(bot_token, app_token, channel_id, channel_name)

    web_client = WebClient(token=bot_token)
    _probe_slack_web_api(web_client, channel_id)

    socket_client = SocketModeClient(
        app_token=app_token,
        web_client=web_client,
    )

    def process_socket_mode_request(
        client: SocketModeClient,
        request: SocketModeRequest,
    ) -> None:
        print("\n" + "=" * 72, flush=True)
        print(
            f"[socket] received: type={request.type!r}, "
            f"envelope_id={request.envelope_id!r}",
            flush=True,
        )

        client.send_socket_mode_response(
            SocketModeResponse(envelope_id=request.envelope_id)
        )
        print("[socket] acknowledged envelope", flush=True)

        payload = request.payload or {}
        print("[socket] payload:", flush=True)
        print(_pretty_json(payload), flush=True)

        if request.type == "events_api":
            _print_event_diagnostics(payload, channel_id)
        else:
            print(
                "[socket] non-events_api payload. "
                "This is usually an action, shortcut, or other interactive payload.",
                flush=True,
            )

    socket_client.socket_mode_request_listeners.append(process_socket_mode_request)

    print("\n[socket] connecting...", flush=True)
    socket_client.connect()
    print("[socket] connected. Now post a new message in the target Slack channel.", flush=True)
    print("[socket] press Ctrl+C to stop.", flush=True)

    try:
        Event().wait()
    except KeyboardInterrupt:
        print("\n[socket] stopped by user", flush=True)


def _print_env_diagnostics(
    bot_token: str,
    app_token: str,
    channel_id: str,
    channel_name: str,
) -> None:
    print("[env] search order. Earlier files win when the same key exists:", flush=True)
    for path in [CONFIG_PROJECT_ROOT / ".env", PACKAGE_ENV_PATH, LEGACY_ENV_PATH]:
        print(f"[env] - {path} exists={path.exists()}", flush=True)

    print(f"[env] SLACK_BOT_TOKEN={_mask_secret(bot_token)}", flush=True)
    print(f"[env] SLACK_APP_TOKEN={_mask_secret(app_token)}", flush=True)
    print(f"[env] SLACK_CHANNEL_NAME={channel_name!r}", flush=True)
    print(f"[env] SLACK_CHANNEL_ID={channel_id!r}", flush=True)

    if not bot_token.startswith("xoxb-"):
        print("[warn] SLACK_BOT_TOKEN should usually start with xoxb-", flush=True)
    if not app_token.startswith("xapp-"):
        print("[warn] SLACK_APP_TOKEN should start with xapp-", flush=True)


def _probe_slack_web_api(web_client: WebClient, channel_id: str) -> None:
    print("\n[probe] calling auth.test with SLACK_BOT_TOKEN", flush=True)
    try:
        auth = web_client.auth_test()
        print(
            "[probe] auth.test ok: "
            f"team={auth.get('team')!r}, user={auth.get('user')!r}, "
            f"bot_id={auth.get('bot_id')!r}",
            flush=True,
        )
    except Exception as error:
        print(f"[probe] auth.test failed: {error}", flush=True)
        return

    print("\n[probe] calling conversations.info for target channel", flush=True)
    try:
        info = web_client.conversations_info(channel=channel_id)
        channel = info.get("channel", {})
        print(
            "[probe] conversations.info ok: "
            f"id={channel.get('id')!r}, name={channel.get('name')!r}, "
            f"is_channel={channel.get('is_channel')!r}, "
            f"is_private={channel.get('is_private')!r}, "
            f"is_member={channel.get('is_member')!r}",
            flush=True,
        )
        if channel.get("is_member") is not True:
            print(
                "[warn] bot is not a member of this channel. "
                "Run /invite @your-bot-name in Slack.",
                flush=True,
            )
    except Exception as error:
        print(f"[probe] conversations.info failed: {error}", flush=True)

    print("\n[probe] calling conversations.history limit=1", flush=True)
    try:
        history = web_client.conversations_history(channel=channel_id, limit=1)
        messages = history.get("messages", [])
        print(f"[probe] conversations.history ok: messages={len(messages)}", flush=True)
        if messages:
            message = messages[0]
            text = str(message.get("text") or "").replace("\n", " ")[:120]
            print(
                "[probe] latest message: "
                f"ts={message.get('ts')!r}, user={message.get('user')!r}, "
                f"subtype={message.get('subtype')!r}, text={text!r}",
                flush=True,
            )
    except Exception as error:
        print(f"[probe] conversations.history failed: {error}", flush=True)


def _print_event_diagnostics(payload: dict[str, Any], target_channel_id: str) -> None:
    event = payload.get("event", {})
    if not isinstance(event, dict):
        print("[event] payload.event is not an object", flush=True)
        return

    files = event.get("files")
    file_count = len(files) if isinstance(files, list) else 0
    text_preview = str(event.get("text") or "").replace("\n", " ")[:120]
    channel = event.get("channel")

    print("[event] summary:", flush=True)
    print(f"[event] - event_id={payload.get('event_id')!r}", flush=True)
    print(f"[event] - type={event.get('type')!r}", flush=True)
    print(f"[event] - subtype={event.get('subtype')!r}", flush=True)
    print(f"[event] - channel={channel!r}", flush=True)
    print(f"[event] - target_channel={target_channel_id!r}", flush=True)
    print(f"[event] - channel_matches={channel == target_channel_id}", flush=True)
    print(f"[event] - user={event.get('user')!r}", flush=True)
    print(f"[event] - bot_id={event.get('bot_id')!r}", flush=True)
    print(f"[event] - ts={event.get('ts')!r}", flush=True)
    print(f"[event] - thread_ts={event.get('thread_ts')!r}", flush=True)
    print(f"[event] - files={file_count}", flush=True)
    print(f"[event] - text={text_preview!r}", flush=True)

    if event.get("type") != "message":
        print("[hint] This is not a message event.", flush=True)
    elif channel != target_channel_id:
        print("[hint] Event arrived, but it is for a different channel.", flush=True)
    elif event.get("bot_id"):
        print("[hint] Event arrived, but it is a bot message.", flush=True)
    else:
        print("[hint] Message event arrived for the target channel.", flush=True)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


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