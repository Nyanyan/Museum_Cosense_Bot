# Museum Cosense Bot Samples

PythonからCosense（旧Scrapbox）にページを作成するサンプルと、Slackの `museum-memo` チャンネルを読み取るテストコードです。
現時点ではSlackから取得した内容をCosenseへアップロードする処理はまだ実装しません。

## セットアップ

```bash
cd cosense-sample
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` を `.env` にコピーします。

```bash
copy .env.example .env
```

`.env` の値を設定します。

```env
COSENSE_PROJECT=your-project-name
COSENSE_CONNECT_SID=s%3Axxxxxxxxxxxxxxxxxxxxxxxx

SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_NAME=museum-memo
SLACK_CHANNEL_ID=C0BDC3P774J
SLACK_HISTORY_LIMIT=5
SLACK_IMAGE_DOWNLOAD_DIR=slack-downloads
```

## Cosense設定

`COSENSE_PROJECT` は投稿先のCosenseプロジェクト名です。

`COSENSE_CONNECT_SID` はCosenseにログイン済みのブラウザCookie `connect.sid` の値です。
`connect.sid=s%3A...` の形式でも、`s%3A...` の値だけでも使えます。

`COSENSE_CONNECT_SID` はログイン済みセッションCookieなので、パスワードと同じように機密情報として扱ってください。

## Gyazo連携

Cosense投稿サンプルは `sample.jpg` をGyazoへアップロードし、そのGyazo URLをCosenseページ本文に入れます。
事前にCosenseの設定画面でGyazo OAuth Uploadを接続しておいてください。

Gyazoのアクセストークンは `.env` には書きません。
Pythonコードは `connect.sid` を使ってCosenseからGyazo OAuth用のトークンを取得します。

## Slack設定

`SLACK_BOT_TOKEN` はSlackアプリのBot User OAuth Tokenです。`xoxb-...` で始まる値を設定してください。

`SLACK_CHANNEL_NAME` は読み取り対象のチャンネル名です。このサンプルでは `museum-memo` です。

`SLACK_CHANNEL_ID` は読み取り対象のチャンネルIDです。このサンプルでは `C0BDC3P774J` です。

Slackアプリには少なくとも以下のBot Token Scopesを付けてください。

- `channels:history`
- `channels:read`
- `files:read`

Botを `museum-memo` チャンネルに招待してから実行してください。

## Cosense投稿サンプル

```bash
python post_sample.py
```

成功すると作成したページURLが表示されます。

```txt
Created: https://scrapbox.io/your-project/Slack%20Cosense%20Test
```

## Slack読み取りテスト

```bash
python read_slack_sample.py
```

`SLACK_HISTORY_LIMIT` 件分の投稿を読み取り、本文と画像の取得結果を標準出力に表示します。
画像ファイルは `SLACK_IMAGE_DOWNLOAD_DIR` に保存され、その保存パスが表示されます。

このテストでは、Slackから取得した内容をCosenseへアップロードしません。
