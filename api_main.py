"""
API-only entrypoint for DouK-Downloader.

Starts FastAPI server directly without any interactive menu, disclaimer,
or language selection prompts.

This module is designed for container deployments (e.g., Zeabur) where
non-interactive behavior is mandatory.
"""

import os
from asyncio import run

from src.application import TikTokDownloader
from src.application.main_server import APIServer
from src.custom import SERVER_HOST, SERVER_PORT


async def start_api_only() -> None:
    """Boot the application in Web API mode only.

    Steps:
    - Initialize `TikTokDownloader` context to setup database and settings.
    - Prepare parameters without triggering interactive flows.
    - Launch FastAPI server with optional `PORT` env override.

    Parameters:
    - None

    Returns:
    - None
    """
    async with TikTokDownloader() as app:
        # Initialize logging/recording and parameters without disclaimer/menu
        app.check_config()
        await app.check_settings(False)

        # Allow platforms to provide `PORT`; default to project constant
        port = int(os.getenv("PORT", SERVER_PORT))
        server = APIServer(app.parameter, app.database)
        await server.run_server(SERVER_HOST, port)


def main() -> None:
    """Synchronous entrypoint wrapper.

    Returns:
    - None: Runs the async API startup routine.
    """
    run(start_api_only())


if __name__ == "__main__":
    main()