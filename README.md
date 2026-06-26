# Museum Cosense Bot

A Python bot that reviews new Slack posts in a configured channel and posts approved content to Cosense.

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
Do not put real Slack channel names or channel IDs in `.env.example`; keep them only in your local `.env`.

## Environment Variables

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

The code still reads the old `cosense-sample/.env` as a temporary fallback, but using a root `.env` is recommended.

## Slack App Settings

Bot Token Scopes:

- `channels:history`
- `channels:read`
- `chat:write`
- `files:read`

For private channels, also add these if needed:

- `groups:history`
- `groups:read`

Enable Socket Mode and create an App-Level Token with this scope:

- `connections:write`

Enable Event Subscriptions and add this Bot Event:

- `message.channels`

For private channels, also add:

- `message.groups`

Enable Interactivity & Shortcuts. With Socket Mode, a public Request URL is not required.

Invite the bot to the target channel:

```txt
/invite @your-bot-name
```

After changing scopes or event settings, reinstall the Slack app to the workspace.

## Run Production Bot

```bash
python run_bot.py
```

Flow:

1. Receive new posts from `SLACK_CHANNEL_ID`.
2. Use the first line as the Cosense page title.
3. Use the second and later lines as the body.
4. If images are attached, download them from Slack and upload them to Gyazo after approval.
5. Reply in the original Slack thread with a review message and a `Post to Cosense` button.
6. When the button is clicked, post the content to Cosense.
7. If a Cosense page with the same title already exists, append `----------` and then append the new content.

The bot ignores its own posts, thread replies, and posts with an empty first line.

## Samples

Cosense post sample:

```bash
python samples/cosense/post_sample.py
```

Slack read sample:

```bash
python samples/slack/read_slack_sample.py
```