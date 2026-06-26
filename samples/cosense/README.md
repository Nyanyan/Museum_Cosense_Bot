# Cosense Samples

Samples for posting to Cosense from Python.

## Check Session

Use this first when Cosense returns `HTTP 401` or `NotLoggedInError`.

```bash
python samples/cosense/check_session.py
```

If this fails, refresh `COSENSE_CONNECT_SID` from a logged-in browser session on `scrapbox.io`, update `.env`, and restart the bot.

## Post Sample Page

This posts a sample page and uploads `sample.jpg` through Gyazo.

```bash
python samples/cosense/post_sample.py
```

Gyazo OAuth Upload must be connected in Cosense settings. The Gyazo access token is not stored in `.env`; it is fetched from Cosense using `connect.sid`.