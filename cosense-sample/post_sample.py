import os
from pathlib import Path

from dotenv import load_dotenv

from cosense_client import CosenseClient


SAMPLE_TITLE = "Slack Cosense Test"


def main() -> None:
    load_dotenv()

    project = os.getenv("COSENSE_PROJECT")
    connect_sid = os.getenv("COSENSE_CONNECT_SID")

    if not project:
        raise RuntimeError("COSENSE_PROJECT is not set")
    if not connect_sid:
        raise RuntimeError("COSENSE_CONNECT_SID is not set")

    client = CosenseClient(project=project, connect_sid=connect_sid)
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
