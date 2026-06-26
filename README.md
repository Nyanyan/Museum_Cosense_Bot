# Museum Cosense Bot

[English](README.md) | [日本語](README.ja.md)

A Python bot that receives new posts from a configured public Slack channel, asks for human approval in the Slack thread, and then posts the approved content to Cosense.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set real values.

```bash
copy .env.example .env
```

Do not commit `.env`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, or browser cookie data.
Keep real Slack channel names and channel IDs only in your local `.env`.

## .env

Recommended Cosense auth uses the current Firefox login cookie at runtime, so you do not need to keep updating `COSENSE_CONNECT_SID` by hand.

```env
COSENSE_PROJECT=your-project-name
COSENSE_COOKIE_SOURCE=firefox
COSENSE_FIREFOX_COOKIE_FILE=
COSENSE_CONNECT_SID=

SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_CHANNEL_NAME=
SLACK_CHANNEL_ID=
SLACK_HISTORY_LIMIT=5
SLACK_IMAGE_DOWNLOAD_DIR=data/slack-downloads
SLACK_IMAGE_DOWNLOAD_WORKERS=4
```

Cosense auth options:

- `COSENSE_COOKIE_SOURCE=firefox`: read the latest `connect.sid` from Firefox cookies.
- `COSENSE_FIREFOX_COOKIE_FILE`: optional path to a specific Firefox `cookies.sqlite` file when multiple profiles are present.
- `COSENSE_CONNECT_SID`: optional manual fallback. Used when `COSENSE_COOKIE_SOURCE` is blank, `env`, or `connect_sid`.

`.env` files are loaded in this order. Earlier values win when the same key exists in multiple files.

1. Root `.env`
2. `museum_cosense_bot/.env`
3. `cosense-sample/.env`

Use the root `.env` for normal operation.

## Slack App Settings

This project targets a public channel, so private-channel `groups:*` scopes are not required.

Bot Token Scopes:

- `channels:history`
- `channels:read`
- `chat:write`
- `files:read`

App-Level Token Scope:

- `connections:write`

Event Subscriptions Bot Event:

- `message.channels`

Also required:

- Enable Socket Mode.
- Enable Interactivity & Shortcuts.
- Reinstall the Slack App after changing scopes or events.
- Invite the bot to the target channel with `/invite @your-bot-name`.

## Run Production Bot

```bash
python run_bot.py
```

Flow:

1. Receive new posts from `SLACK_CHANNEL_ID`.
2. Use the first line as the Cosense page title.
3. Use the second and later lines as the body.
4. Reply in the original Slack thread with a review message and a `Post to Cosense` button.
5. Attached images are downloaded from Slack in the background after the review message is posted.
6. When the button is clicked, the review message is kept but the button is removed and a status line is shown.
7. Upload downloaded images to Gyazo.
8. Post the content to Cosense.
9. If a Cosense page with the same title already exists, keep the existing lines, append `----------`, and then append the new content.

The bot ignores its own posts, thread replies, and posts with an empty first line. Button clicks are accepted only once per Slack post while the bot process is running.

## Debugging

Check Slack channel history access:

```bash
python samples/slack/read_slack_sample.py
```

Check whether Slack Socket Mode events arrive:

```bash
python samples/slack/debug_socket_mode.py
```

Check whether Cosense auth works:

```bash
python samples/cosense/check_session.py
```

If `COSENSE_COOKIE_SOURCE=firefox` cannot find the cookie, make sure Firefox is logged in to `https://scrapbox.io/`. If Firefox has multiple profiles, set `COSENSE_FIREFOX_COOKIE_FILE` to that profile's `cookies.sqlite`.

## Samples

Cosense post sample:

```bash
python samples/cosense/post_sample.py
```

Slack read sample:

```bash
python samples/slack/read_slack_sample.py
```