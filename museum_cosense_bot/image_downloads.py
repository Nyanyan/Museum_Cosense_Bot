from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

from museum_cosense_bot.slack_client import SlackClient, SlackImage


PostKey = tuple[str, str]


class BackgroundImageDownloads:
    def __init__(
        self,
        bot_token: str,
        download_dir: str | Path,
        max_workers: int,
    ) -> None:
        self.bot_token = bot_token
        self.download_dir = Path(download_dir)
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="slack-image-download",
        )
        self.lock = Lock()
        self.futures: dict[PostKey, Future[list[SlackImage]]] = {}

    def start(
        self,
        key: PostKey,
        message: dict[str, Any],
        image_count: int,
        replace: bool = False,
    ) -> None:
        if image_count < 1:
            if replace:
                with self.lock:
                    self.futures.pop(key, None)
            return

        with self.lock:
            if key in self.futures and not replace:
                return
            self.futures[key] = self.executor.submit(self._download, key, message)

        print(
            f"[slack:image] queued background download: "
            f"channel={key[0]}, ts={key[1]}, images={image_count}",
            flush=True,
        )

    def resolve(
        self,
        key: PostKey,
        message: dict[str, Any],
        expected_count: int,
    ) -> list[SlackImage]:
        if expected_count < 1:
            return []

        future = self._get_future(key)
        if future is not None:
            try:
                images = future.result()
                if len(images) >= expected_count:
                    return images
                print(
                    f"[slack:image] background download incomplete: "
                    f"channel={key[0]}, ts={key[1]}, "
                    f"downloaded={len(images)}, expected={expected_count}. Retrying.",
                    flush=True,
                )
            except Exception as error:
                print(
                    f"[slack:image] background download failed: "
                    f"channel={key[0]}, ts={key[1]}, error={error}. Retrying.",
                    flush=True,
                )

        return self._download(key, message)

    def _get_future(self, key: PostKey) -> Future[list[SlackImage]] | None:
        with self.lock:
            return self.futures.get(key)

    def _download(self, key: PostKey, message: dict[str, Any]) -> list[SlackImage]:
        print(
            f"[slack:image] downloading: channel={key[0]}, ts={key[1]}",
            flush=True,
        )
        client = SlackClient(bot_token=self.bot_token)
        images = client.download_message_images(
            message=message,
            download_dir=self.download_dir,
        )
        print(
            f"[slack:image] downloaded: "
            f"channel={key[0]}, ts={key[1]}, images={len(images)}",
            flush=True,
        )
        return images