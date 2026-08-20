"""Pre-flight checks for Instagram Graph API credentials."""

from __future__ import annotations

import os

import requests

GRAPH_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

REQUIRED_SCOPES = frozenset(
    {
        "instagram_basic",
        "instagram_content_publish",
        "pages_read_engagement",
        "pages_show_list",
    }
)


def _debug_token(access_token: str) -> dict:
    response = requests.get(
        f"{BASE_URL}/debug_token",
        params={"input_token": access_token, "access_token": access_token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", {})


def verify_instagram_setup(
    account_id: str | None = None,
    access_token: str | None = None,
) -> None:
    """
    Validate token scopes and Instagram account access before publishing.
    Raises RuntimeError with actionable steps when misconfigured.
    """
    token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    if not token or not ig_id:
        raise RuntimeError(
            "Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID in .env"
        )

    info = _debug_token(token)
    if not info.get("is_valid"):
        raise RuntimeError("Instagram access token is invalid or expired.")

    granted = set(info.get("scopes") or [])
    missing = REQUIRED_SCOPES - granted
    if missing:
        raise RuntimeError(
            "Instagram token is missing required permissions: "
            f"{', '.join(sorted(missing))}.\n"
            "Fix in Meta for Developers → Graph API Explorer:\n"
            "  1. Select your App and Facebook Page\n"
            "  2. Add permissions: instagram_basic, instagram_content_publish, "
            "pages_read_engagement, pages_show_list\n"
            "  3. Generate a Page Access Token and update .env"
        )

    response = requests.get(
        f"{BASE_URL}/{ig_id}",
        params={"fields": "username,name", "access_token": token},
        timeout=30,
    )
    if not response.ok:
        page_id = info.get("profile_id") or info.get("user_id")
        hint = (
            f"\nToken is linked to page/user ID {page_id}. "
            "Fetch the correct Instagram ID with:\n"
            f"  GET /{page_id}?fields=instagram_business_account"
        )
        raise RuntimeError(
            f"Cannot access Instagram account ID '{ig_id}'. "
            f"API response: {response.text}{hint}"
        )

    username = response.json().get("username", "?")
    print(f"Instagram ready: @{username} (id {ig_id})")
