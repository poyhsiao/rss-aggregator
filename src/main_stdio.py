"""Entry point for stdio mode (desktop application)."""

import asyncio
import signal
import sys
from typing import Any

from src.config import get_settings
get_settings.cache_clear()

from src.stdio.server import StdioServer


async def main() -> None:
    """Main entry point for stdio mode."""
    server = StdioServer()

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        asyncio.create_task(server.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
