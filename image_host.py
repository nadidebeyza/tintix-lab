"""Upload local images to a temporary public URL for Instagram Graph API."""

from __future__ import annotations

import os
from pathlib import Path

import requests

HOSTS = (
    "https://0x0.st",
    "https://catbox.moe/user/api.php",
)


def _upload_to_0x0(file_path: Path) -> str:
    with file_path.open("rb") as handle:
        response = requests.post(
            HOSTS[0],
            files={"file": (file_path.name, handle, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    url = response.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Unexpected host response: {url[:120]}")
    return url


def _upload_to_catbox(file_path: Path) -> str:
    with file_path.open("rb") as handle:
        response = requests.post(
            HOSTS[1],
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (file_path.name, handle, "image/png")},
            timeout=120,
        )
    response.raise_for_status()
    url = response.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Unexpected host response: {url[:120]}")
    return url


def get_public_image_url(file_path: Path) -> str:
    """
    Return a publicly reachable URL for an image file.

    Uses IMAGE_PUBLIC_BASE_URL if set (e.g. self-hosted output folder),
    otherwise uploads to a temporary file host.
    """
    base_url = os.getenv("IMAGE_PUBLIC_BASE_URL", "").rstrip("/")
    if base_url:
        return f"{base_url}/{file_path.name}"

    errors: list[str] = []
    for uploader in (_upload_to_0x0, _upload_to_catbox):
        try:
            return uploader(file_path)
        except requests.RequestException as exc:
            errors.append(str(exc))

    raise RuntimeError(
        "Could not obtain a public image URL. "
        f"Tried temporary hosts. Errors: {' | '.join(errors)}"
    )
