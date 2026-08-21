"""Instagram Graph API publishing for @tintix.lab."""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests

GRAPH_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


class InstagramClient:
    def __init__(
        self,
        account_id: str | None = None,
        access_token: str | None = None,
    ) -> None:
        self.account_id = (account_id or os.getenv("INSTAGRAM_ACCOUNT_ID", "")).strip()
        self.access_token = (
            access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        ).strip()
        if not self.account_id or not self.access_token:
            raise EnvironmentError(
                "INSTAGRAM_ACCOUNT_ID and INSTAGRAM_ACCESS_TOKEN must be set."
            )

    def _post(self, path: str, data: dict) -> dict:
        payload = {**data, "access_token": self.access_token}
        response = requests.post(f"{BASE_URL}/{path}", data=payload, timeout=120)
        if not response.ok:
            raise RuntimeError(
                f"Instagram API error ({response.status_code}): {response.text}"
            )
        return response.json()

    def _wait_for_container(self, creation_id: str, timeout: int = 90) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = requests.get(
                f"{BASE_URL}/{creation_id}",
                params={
                    "fields": "status_code",
                    "access_token": self.access_token,
                },
                timeout=30,
            )
            response.raise_for_status()
            status = response.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Media container failed: {response.json()}")
            time.sleep(2)
        raise TimeoutError("Timed out waiting for Instagram media container.")

    def publish_post(self, image_url: str, caption: str) -> str:
        container = self._post(
            f"{self.account_id}/media",
            {"image_url": image_url, "caption": caption},
        )
        creation_id = container["id"]
        self._wait_for_container(creation_id)
        published = self._post(
            f"{self.account_id}/media_publish",
            {"creation_id": creation_id},
        )
        return published["id"]

    def publish_story(self, image_url: str) -> str:
        container = self._post(
            f"{self.account_id}/media",
            {"image_url": image_url, "media_type": "STORIES"},
        )
        creation_id = container["id"]
        self._wait_for_container(creation_id)
        published = self._post(
            f"{self.account_id}/media_publish",
            {"creation_id": creation_id},
        )
        return published["id"]


def publish_to_instagram(
    post_path: Path | None,
    story_path: Path | None,
    caption: str,
    publish_post: bool = True,
    publish_story: bool = True,
) -> dict[str, str]:
    from image_host import get_public_image_url
    from instagram_setup import verify_instagram_setup

    verify_instagram_setup()
    client = InstagramClient()
    results: dict[str, str] = {}

    if publish_post and post_path:
        post_url = get_public_image_url(post_path)
        results["post"] = client.publish_post(post_url, caption)

    if publish_story and story_path:
        story_url = get_public_image_url(story_path)
        results["story"] = client.publish_story(story_url)

    return results
