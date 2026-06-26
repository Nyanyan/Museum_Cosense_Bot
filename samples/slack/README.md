# Slack Read Sample

Slackの `museum-memo` チャンネルから投稿本文と添付画像を読み取り、標準出力に表示します。
画像は `SLACK_IMAGE_DOWNLOAD_DIR` に保存されます。

## 実行

リポジトリ直下で実行します。

```bash
python samples/slack/read_slack_sample.py
```

Slackアプリには少なくとも以下のBot Token Scopesを付け、Botを対象チャンネルに招待してください。

- `channels:history`
- `channels:read`
- `files:read`

プライベートチャンネルを読む場合は、必要に応じて `groups:history` と `groups:read` も追加してください。