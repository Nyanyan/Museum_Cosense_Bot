import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from museum_cosense_bot.config import load_environment
from museum_cosense_bot.cosense_client import CosenseClient
from museum_cosense_bot.cosense_cookie import resolve_cosense_connect_sid


SAMPLE_TITLE = "Slack Cosense Test"


def main() -> None:
    load_environment()

    project = os.getenv("COSENSE_PROJECT")
    if not project:
        raise RuntimeError("COSENSE_PROJECT is not set")

    connect_sid = resolve_cosense_connect_sid()
    print(f"COSENSE_CONNECT_SID source: {connect_sid.source}")

    client = CosenseClient(project=project, connect_sid=connect_sid.value)
    sample_image_path = Path(__file__).with_name("sample.jpg")
    image_url = client.upload_image_to_gyazo(
        image_path=sample_image_path,
        title=SAMPLE_TITLE,
    )

    lines = [
        SAMPLE_TITLE,
        "",
        "これはPythonからCosense import APIを使って作成したテストページです。",
        "将来的にはSlack投稿の1行目をタイトルとして使います。",
        "",
        "sample.jpg:",
        f"[{image_url}]",
        "",
        "#from_slack",
        "#test",
    ]

    created_url = client.import_page(title=SAMPLE_TITLE, lines=lines)
    print(f"Created: {created_url}")


if __name__ == "__main__":
    main()