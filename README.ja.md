# Museum Cosense Bot

[English](README.md) | [日本語](README.ja.md)

設定した公開 Slack チャンネルの新規投稿を受け取り、Slack スレッド上で人間の承認を待ってから、承認済みの内容を Cosense に投稿する Python ボットです。

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

`.env`、`SLACK_BOT_TOKEN`、`SLACK_APP_TOKEN`、ブラウザ Cookie の情報はコミットしないでください。
実際の Slack チャンネル名やチャンネル ID は、ローカルの `.env` にだけ保存してください。

## .env

Cosense 認証には、実行時に現在の Firefox ログイン Cookie を読む方法を推奨します。これにより、`COSENSE_CONNECT_SID` を手動で更新し続ける必要がありません。

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

Cosense 認証オプション:

- `COSENSE_COOKIE_SOURCE=firefox`: Firefox の Cookie から最新の `connect.sid` を読み取ります。
- `COSENSE_FIREFOX_COOKIE_FILE`: Firefox プロファイルが複数ある場合に、特定の `cookies.sqlite` ファイルを指定する任意のパスです。
- `COSENSE_CONNECT_SID`: 手動指定のフォールバックです。`COSENSE_COOKIE_SOURCE` が空、`env`、または `connect_sid` の場合に使われます。

`.env` ファイルは次の順序で読み込まれます。同じキーが複数のファイルにある場合は、先に読み込まれた値が優先されます。

1. ルートの `.env`
2. `museum_cosense_bot/.env`
3. `cosense-sample/.env`

通常の運用では、ルートの `.env` を使ってください。

## Slack App の設定

このプロジェクトは公開チャンネルを対象にしているため、プライベートチャンネル用の `groups:*` スコープは不要です。

Bot Token Scopes:

- `channels:history`
- `channels:read`
- `chat:write`
- `files:read`

App-Level Token Scope:

- `connections:write`

Event Subscriptions の Bot Event:

- `message.channels`

追加で必要な設定:

- Socket Mode を有効にする。
- Interactivity & Shortcuts を有効にする。
- スコープやイベントを変更した後は Slack App を再インストールする。
- 対象チャンネルで `/invite @your-bot-name` を実行し、ボットを招待する。

## 本番ボットの実行

```bash
python run_bot.py
```

処理の流れ:

1. `SLACK_CHANNEL_ID` から新規投稿を受け取ります。
2. 1 行目を Cosense ページのタイトルとして使います。
3. 2 行目以降を本文として使います。
4. 元の Slack スレッドに、確認用メッセージ、`Post to Cosense` ボタン、`Reload` ボタンを返信します。
5. 添付画像は、確認用メッセージを投稿した後にバックグラウンドで Slack からダウンロードされます。
6. どちらかのボタンがクリックされると、確認用メッセージは残したまま両方のボタンを削除し、ステータス行を表示します。
7. `Reload` がクリックされた場合は、Slack 投稿の最新内容を取得し直して、新しい確認用メッセージを返信します。
8. `Post to Cosense` がクリックされた場合は、ダウンロード済みの画像を Gyazo にアップロードします。
9. 内容を Cosense に投稿します。
10. 同じタイトルの Cosense ページがすでに存在する場合は、既存の行を残し、`----------` を追加してから新しい内容を追記します。

ボットは、自分自身の投稿、スレッド返信、1 行目が空の投稿を無視します。各確認用メッセージでは、ボタンのクリックを 1 回だけ受け付けます。`Post to Cosense` のクリックは、ボットプロセスの実行中、Slack 投稿ごとに 1 回だけ受け付けられます。

## デバッグ

Slack チャンネル履歴にアクセスできるか確認します。

```bash
python samples/slack/read_slack_sample.py
```

Slack Socket Mode のイベントが届くか確認します。

```bash
python samples/slack/debug_socket_mode.py
```

Cosense 認証が動作するか確認します。

```bash
python samples/cosense/check_session.py
```

`COSENSE_COOKIE_SOURCE=firefox` で Cookie が見つからない場合は、Firefox で `https://scrapbox.io/` にログインしていることを確認してください。Firefox プロファイルが複数ある場合は、対象プロファイルの `cookies.sqlite` を `COSENSE_FIREFOX_COOKIE_FILE` に設定してください。

## サンプル

Cosense 投稿サンプル:

```bash
python samples/cosense/post_sample.py
```

Slack 読み取りサンプル:

```bash
python samples/slack/read_slack_sample.py
```