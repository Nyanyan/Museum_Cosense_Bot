# Slack Samples

Slack channel reads and Socket Mode event debugging samples.

## Read Latest Messages

This checks whether `SLACK_BOT_TOKEN` can read the configured channel history and download attached images.

```bash
python samples/slack/read_slack_sample.py
```

Required Bot Token Scopes for public channels:

- `channels:history`
- `channels:read`
- `files:read`

## Debug Socket Mode Events

This checks whether Slack is actually sending events to the app over Socket Mode. It does not post to Cosense.

```bash
python samples/slack/debug_socket_mode.py
```

After the script prints `connected`, post a new message in the target Slack channel.

If `conversations.history` works but no `[socket] received` log appears after a new post, check these Slack App settings:

- Socket Mode is enabled.
- `SLACK_APP_TOKEN` is an App-Level Token that starts with `xapp-`.
- The App-Level Token has `connections:write`.
- Event Subscriptions is enabled.
- `message.channels` is added under `Subscribe to bot events`.
- The app was reinstalled to the workspace after changing scopes or events.
- The bot was invited to the target channel.