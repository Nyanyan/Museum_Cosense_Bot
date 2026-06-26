# Cosense Sample

PythonからCosense（旧Scrapbox）にサンプルページを1つ作成し、`sample.jpg` もGyazo経由で本文に添付する最小サンプルです。
Slack連携はまだ実装しません。

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
```

`COSENSE_PROJECT` は投稿先のCosenseプロジェクト名です。

`COSENSE_CONNECT_SID` はCosenseにログイン済みのブラウザCookie `connect.sid` の値です。
`connect.sid=s%3A...` の形式でも、`s%3A...` の値だけでも使えます。

`COSENSE_CONNECT_SID` はログイン済みセッションCookieなので、パスワードと同じように機密情報として扱ってください。

## Gyazo連携

このサンプルは `sample.jpg` をGyazoへアップロードし、そのGyazo URLをCosenseページ本文に入れます。
事前にCosenseの設定画面でGyazo OAuth Uploadを接続しておいてください。

Gyazoのアクセストークンは `.env` には書きません。
Pythonコードは `connect.sid` を使ってCosenseからGyazo OAuth用のトークンを取得します。

## 実行

```bash
python post_sample.py
```

成功すると作成したページURLが表示されます。

```txt
Created: https://scrapbox.io/your-project/Slack%20Cosense%20Test
```

このサンプルは、まずCosenseへの1ページ投稿と画像添付だけを確認するためのものです。
Slack APIやSlack Boltの処理は含めていません。
