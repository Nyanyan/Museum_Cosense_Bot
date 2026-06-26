# Museum Cosense Bot

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

Do not commit `COSENSE_CONNECT_SID`, `SLACK_BOT_TOKEN`, or `SLACK_APP_TOKEN`.
Keep real Slack channel names and channel IDs only in your local `.env`.

## .env

```env
COSENSE_PROJECT=your-project-name
COSENSE_CONNECT_SID=s%3Axxxxxxxxxxxxxxxxxxxxxxxx

SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_CHANNEL_NAME=
SLACK_CHANNEL_ID=
SLACK_HISTORY_LIMIT=5
SLACK_IMAGE_DOWNLOAD_DIR=data/slack-downloads
```

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
5. When the button is clicked, download attached images from Slack and upload them to Gyazo.
6. Post the content to Cosense.
7. If a Cosense page with the same title already exists, append `----------` and then append the new content.

The bot ignores its own posts, thread replies, and posts with an empty first line.

## Debugging

Check Slack channel history access:

```bash
python samples/slack/read_slack_sample.py
```

Check whether Slack Socket Mode events arrive:

```bash
python samples/slack/debug_socket_mode.py
```

Check whether `COSENSE_CONNECT_SID` is still a valid logged-in Cosense session:

```bash
python samples/cosense/check_session.py
```

If Slack works but Cosense returns `HTTP 401` or `NotLoggedInError`, refresh `COSENSE_CONNECT_SID` from a logged-in browser session on `scrapbox.io`, update `.env`, and restart the bot. The cookie can expire or become invalid after logout.

## Samples

Cosense post sample:

```bash
python samples/cosense/post_sample.py
```

Slack read sample:

```bash
python samples/slack/read_slack_sample.py
```