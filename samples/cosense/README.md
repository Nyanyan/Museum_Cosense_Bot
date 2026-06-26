# Cosense Samples

Samples for posting to Cosense from Python.

## Auth

Recommended `.env` settings:

```env
COSENSE_PROJECT=your-project-name
COSENSE_COOKIE_SOURCE=firefox
COSENSE_FIREFOX_COOKIE_FILE=
COSENSE_CONNECT_SID=
```

With `COSENSE_COOKIE_SOURCE=firefox`, the code reads the current `connect.sid` from Firefox cookies at runtime. This avoids manually updating `COSENSE_CONNECT_SID` whenever the browser session changes.

If Firefox has multiple profiles, set `COSENSE_FIREFOX_COOKIE_FILE` to the target profile's `cookies.sqlite`.

## Check Session

Use this first when Cosense returns `HTTP 401` or `NotLoggedInError`.

```bash
python samples/cosense/check_session.py
```

If this fails, open Firefox and make sure you are logged in to `https://scrapbox.io/`.

## Post Sample Page

This posts a sample page and uploads `sample.jpg` through Gyazo.

```bash
python samples/cosense/post_sample.py
```

Gyazo OAuth Upload must be connected in Cosense settings. The Gyazo access token is not stored in `.env`; it is fetched from Cosense using the current logged-in session.