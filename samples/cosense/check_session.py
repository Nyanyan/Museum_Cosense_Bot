import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from museum_cosense_bot.config import load_environment
from museum_cosense_bot.cosense_client import CosenseClient


def main() -> None:
    load_environment()

    project = _required_env("COSENSE_PROJECT")
    connect_sid = _required_env("COSENSE_CONNECT_SID")

    client = CosenseClient(project=project, connect_sid=connect_sid)
    print(f"Cosense project: {project}")
    print(f"COSENSE_CONNECT_SID: {_mask_secret(connect_sid)}")
    print("Checking Cosense login session...")
    client.validate_session()
    print("Cosense login session: OK")

    lines = client.get_page_lines("__cosense_session_check__")
    if lines is None:
        print("Cosense project access: OK (test page does not exist, which is fine)")
    else:
        print(f"Cosense project access: OK (test page lines={len(lines)})")


def _mask_secret(value: str) -> str:
    value = value.strip()
    if len(value) <= 12:
        return "***"
    return f"{value[:8]}...{value[-4:]}"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


if __name__ == "__main__":
    main()