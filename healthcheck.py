"""
Container health check script for DouK-Downloader.

Periodically invoked by Docker `HEALTHCHECK` to verify the FastAPI
server is up by querying `http://localhost:<PORT>/health`.

This script uses only Python standard library to avoid adding curl/wget
and keeps the final image minimal.
"""

import os
import sys
import urllib.request
from typing import Optional


def check(url: str, timeout: float = 2.0) -> int:
    """Probe health endpoint and return appropriate exit code.

    Parameters:
    - url (str): Full URL to the health endpoint (e.g., `http://localhost:5555/health`).
    - timeout (float): Request timeout in seconds.

    Returns:
    - int: `0` when the endpoint responds with HTTP 200; otherwise `1`.

    Usage:
    - Called by Docker HEALTHCHECK. A non-zero exit code marks container as unhealthy.
    """
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # Consider healthy only on HTTP 200
            return 0 if resp.status == 200 else 1
    except Exception:
        return 1


def main() -> None:
    """Entrypoint for health check.

    Reads `PORT` from environment (default `5555`), builds the local URL,
    and exits with proper status code for Docker to interpret.

    Returns:
    - None
    """
    port = os.getenv("PORT", "5555")
    url = f"http://localhost:{port}/health"
    timeout_env: Optional[str] = os.getenv("HEALTHCHECK_TIMEOUT", "2")
    try:
        timeout = float(timeout_env)
    except Exception:
        timeout = 2.0
    sys.exit(check(url, timeout))


if __name__ == "__main__":
    main()