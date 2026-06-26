# Museum Cosense Bot

Slackのpublicチャンネルに投稿された内容を、人間の確認ボタンを挟んでCosenseへ投稿するPython Botです。

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

`COSENSE_CONNECT_SID`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` は機密情報です。Gitにコミットしないでください。
Slackチャンネル名やチャンネルIDも `.env.example` には入れず、ローカルの `.env` にだけ入れてください。

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

`.env` は以下の順に読み込まれます。同じキーが複数にある場合は、先に読まれた値が使われます。

1. ルートの `.env`
2. `museum_cosense_bot/.env`
3. `cosense-sample/.env`

基本的にはルートの `.env` を使ってください。

## Slack App設定

今回はpublicチャンネル用なので、privateチャンネル向けの `groups:*` 権限は不要です。

Bot Token Scopes:

- `channels:history`
- `channels:read`
- `chat:write`
- `files:read`

App-Level Token Scope:

- `connections:write`

Event SubscriptionsのBot Event:

- `message.channels`

その他に必要な設定:

- Socket ModeをOnにする
- Interactivity & ShortcutsをOnにする
- 権限やイベントを変えた後にSlack AppをReinstallする
- 対象チャンネルで `/invite @your-bot-name` してBotを招待する

## 本番Botの実行

```bash
python run_bot.py
```

処理の流れ:

1. `SLACK_CHANNEL_ID` の新規投稿を受信する
2. 1行目をCosenseページタイトルにする
3. 2行目以降を本文にする
4. 元投稿のスレッドに確認メッセージと `Post to Cosense` ボタンを投稿する
5. ボタンが押されたら、添付画像をSlackから取得してGyazoへアップロードする
6. Cosenseへ投稿する
7. 同じタイトルのCosenseページが既にあれば、末尾に `----------` を入れて追記する

Bot自身の投稿、スレッド返信、1行目が空の投稿は無視します。

## デバッグ

最新投稿の取得だけを確認する場合:

```bash
python samples/slack/read_slack_sample.py
```

Socket ModeでSlackイベントが届いているか確認する場合:

```bash
python samples/slack/debug_socket_mode.py
```

`debug_socket_mode.py` が `connected` と表示した後、対象Slackチャンネルに新規投稿してください。

`conversations.history` は成功するのに `[socket] received` が出ない場合、Bot TokenではなくSlack App側のSocket Mode/Event Subscriptions設定が原因の可能性が高いです。

## サンプル

Cosense投稿サンプル:

```bash
python samples/cosense/post_sample.py
```

Slack読み取りサンプル:

```bash
python samples/slack/read_slack_sample.py
```