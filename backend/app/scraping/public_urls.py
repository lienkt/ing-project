"""Public HTTP(S) targets for user-requested browser captures."""

import ipaddress
import socket
from urllib.parse import urlsplit


def validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Use a public HTTP(S) URL without credentials")
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except (OSError, ValueError) as exc:
        raise ValueError("The website address could not be resolved") from exc
    if not addresses or any(
        not ipaddress.ip_address(item[4][0]).is_global for item in addresses
    ):
        raise ValueError(
            "Capture requires a public website; local/private addresses are not allowed"
        )
