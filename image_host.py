"""Upload local images to a public URL for Instagram Graph API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import requests

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {"User-Agent": BROWSER_USER_AGENT}


def _verify_public_image_url(url: str) -> bool:
    """Return True when URL serves a direct image Instagram can fetch."""
    try:
        response = requests.head(url, headers=REQUEST_HEADERS, timeout=30, allow_redirects=True)
        if response.status_code >= 400:
            response = requests.get(
                url,
                headers={**REQUEST_HEADERS, "Range": "bytes=0-511"},
                timeout=30,
                allow_redirects=True,
            )
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type.startswith("image/"):
            return True
        if "text/html" in content_type:
            return False
    except requests.RequestException as exc:
        if url.startswith(("https://files.catbox.moe/", "https://litter.catbox.moe/")):
            print(f"Could not probe {url} locally ({exc}) — trusting Catbox CDN URL")
            return True
        return False
    return False


def _upload_to_catbox(file_path: Path) -> str:
    print("Uploading image to Catbox...")
    with file_path.open("rb") as handle:
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (file_path.name, handle, "image/png")},
            headers=REQUEST_HEADERS,
            timeout=60,
        )
    response.raise_for_status()
    url = response.text.strip()
    if not url.startswith("https://"):
        raise ValueError(f"Unexpected Catbox response: {url[:200]}")
    print(f"Hosted at Catbox — {url}")
    return url


def _upload_to_litterbox(file_path: Path) -> str:
    print("Uploading image to Litterbox...")
    with file_path.open("rb") as handle:
        response = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "24h"},
            files={"fileToUpload": (file_path.name, handle, "image/png")},
            headers=REQUEST_HEADERS,
            timeout=60,
        )
    response.raise_for_status()
    url = response.text.strip()
    if not url.startswith("https://"):
        raise ValueError(f"Unexpected Litterbox response: {url[:200]}")
    print(f"Hosted at Litterbox — {url}")
    return url


def get_public_image_url(file_path: Path) -> str:
    """
    Upload and return an Instagram-compatible direct image URL.

    Uses IMAGE_PUBLIC_BASE_URL when set, otherwise Catbox → Litterbox fallbacks.
    """
    base_url = os.getenv("IMAGE_PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}/{file_path.name}"

    uploaders: list[tuple[str, Callable[[Path], str]]] = [
        ("Catbox", _upload_to_catbox),
        ("Litterbox", _upload_to_litterbox),
    ]
    errors: list[str] = []

    for name, upload in uploaders:
        try:
            url = upload(file_path)
            if _verify_public_image_url(url):
                return url
            print(f"{name} URL is not a direct image — trying next host...")
            errors.append(f"{name}: URL does not serve image/* content-type")
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            print(f"{name} failed — trying next host...")

    raise RuntimeError("All image hosts failed — " + "; ".join(errors))
