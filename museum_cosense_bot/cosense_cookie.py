from dataclasses import dataclass
from pathlib import Path
from http.cookiejar import Cookie
import os
import time


COSENSE_COOKIE_NAME = "connect.sid"
COSENSE_COOKIE_DOMAIN = "scrapbox.io"


@dataclass(frozen=True)
class CosenseConnectSid:
    value: str
    source: str


def resolve_cosense_connect_sid() -> CosenseConnectSid:
    cookie_source = os.getenv("COSENSE_COOKIE_SOURCE", "").strip().lower()
    env_connect_sid = os.getenv("COSENSE_CONNECT_SID", "").strip()

    if cookie_source == "firefox":
        return _resolve_from_firefox()

    if cookie_source in ("", "env", "connect_sid") and env_connect_sid:
        return CosenseConnectSid(
            value=env_connect_sid,
            source="COSENSE_CONNECT_SID",
        )

    if cookie_source in ("", "env", "connect_sid"):
        raise RuntimeError(
            "COSENSE_CONNECT_SID is not set. "
            "Set COSENSE_COOKIE_SOURCE=firefox to read connect.sid from Firefox, "
            "or set COSENSE_CONNECT_SID manually."
        )

    raise RuntimeError(
        f"Unsupported COSENSE_COOKIE_SOURCE: {cookie_source!r}. "
        "Supported values are firefox, env, or blank."
    )


def _resolve_from_firefox() -> CosenseConnectSid:
    cookie_file = os.getenv("COSENSE_FIREFOX_COOKIE_FILE", "").strip()
    cookies = _load_firefox_cookies(cookie_file)
    candidates = [
        cookie
        for cookie in cookies
        if _is_cosense_connect_sid(cookie)
    ]
    if not candidates:
        hint = (
            " Make sure Firefox is logged in to https://scrapbox.io/."
        )
        if cookie_file:
            hint += f" Checked cookie file: {cookie_file}"
        raise RuntimeError(
            "Firefox connect.sid cookie for scrapbox.io was not found." + hint
        )

    candidates.sort(key=lambda cookie: cookie.expires or 0, reverse=True)
    selected = candidates[0]
    source = "Firefox cookies"
    if cookie_file:
        source = f"Firefox cookie file: {cookie_file}"
    return CosenseConnectSid(value=selected.value, source=source)


def _load_firefox_cookies(cookie_file: str):
    try:
        import browser_cookie3
    except ImportError as error:
        raise RuntimeError(
            "browser-cookie3 is required for COSENSE_COOKIE_SOURCE=firefox. "
            "Run: pip install -r requirements.txt"
        ) from error

    kwargs = {"domain_name": COSENSE_COOKIE_DOMAIN}
    if cookie_file:
        kwargs["cookie_file"] = str(Path(cookie_file).expanduser())
    return browser_cookie3.firefox(**kwargs)


def _is_cosense_connect_sid(cookie: Cookie) -> bool:
    if cookie.name != COSENSE_COOKIE_NAME:
        return False
    if COSENSE_COOKIE_DOMAIN not in cookie.domain:
        return False
    if cookie.expires is not None and cookie.expires < time.time():
        return False
    return bool(cookie.value)