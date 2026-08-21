"""Instagram Graph API publishing for @tintix.lab."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

from instagram_setup import instagram_api_base, resolve_instagram_account_id


class InstagramClient:
    def __init__(
        self,
        account_id: str | None = None,
        access_token: str | None = None,
    ) -> None:
        self.access_token = (
            access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        ).strip()
        if not self.access_token:
            raise EnvironmentError("INSTAGRAM_ACCESS_TOKEN must be set.")

        self.base_url = instagram_api_base(self.access_token)
        self.account_id = resolve_instagram_account_id(account_id, self.access_token)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        query = {**(params or {}), "access_token": self.access_token}
        response = requests.request(
            method,
            url,
            params=query,
            data=data,
            timeout=120,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if not response.ok or "error" in payload:
            error = payload.get("error", {})
            message = error.get("message", response.text)
            raise RuntimeError(
                f"Instagram API error ({response.status_code}): {message}"
            )
        return payload

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, data=data)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def _wait_for_container(self, creation_id: str, timeout: int = 90) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            payload = self._get(
                creation_id,
                {"fields": "status_code,status"},
            )
            status = payload.get("status_code")
            if status == "FINISHED":
                return
            if status == "PUBLISHED":
                return
            if status in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Media container failed: {payload}")
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
