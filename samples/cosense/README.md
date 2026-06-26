# Cosense Sample

PythonからCosenseにサンプルページを1つ作成し、`sample.jpg` もGyazo経由で本文に添付します。

## 実行

リポジトリ直下で実行します。

```bash
python samples/cosense/post_sample.py
```

Cosenseの設定画面でGyazo OAuth Uploadを接続しておいてください。
Gyazoのアクセストークンは `.env` には書かず、`connect.sid` を使ってCosenseから取得します。