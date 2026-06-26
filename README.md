# Museum Cosense Bot

Slackの `museum-memo` チャンネルとCosense（旧Scrapbox）をつなぐためのPythonコードです。

現時点では、以下のサンプルがあります。

- `samples/cosense/`: PythonからCosenseへページと画像を投稿するサンプル
- `samples/slack/`: Slackチャンネルの投稿本文と画像を読み取るサンプル

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` を `.env` にコピーして、実際の値を設定します。

```bash
copy .env.example .env
```

`COSENSE_CONNECT_SID` と `SLACK_BOT_TOKEN` は機密情報です。Gitにコミットしないでください。

## 環境変数

```env
COSENSE_PROJECT=your-project-name
COSENSE_CONNECT_SID=s%3Axxxxxxxxxxxxxxxxxxxxxxxx

SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_NAME=museum-memo
SLACK_CHANNEL_ID=C0BDC3P774J
SLACK_HISTORY_LIMIT=5
SLACK_IMAGE_DOWNLOAD_DIR=data/slack-downloads
```

## サンプル実行

Cosense投稿サンプル:

```bash
python samples/cosense/post_sample.py
```

Slack読み取りサンプル:

```bash
python samples/slack/read_slack_sample.py
```