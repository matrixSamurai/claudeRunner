"""
Manages a Cloudflare Tunnel (cloudflared) process to expose the dev server.
Parses the tunnel URL from cloudflared's output automatically.
"""

import asyncio
import logging
import re

from config import Config

logger = logging.getLogger(__name__)


class TunnelManager:
    def __init__(self):
        self._process: asyncio.subprocess.Process | None = None
        self.current_url: str | None = None

    async def start(self) -> str | None:
        """Start cloudflared tunnel and return the public URL."""
        if self._process and self._process.returncode is None:
            logger.info("Tunnel already running.")
            return self.current_url

        logger.info(f"Starting Cloudflare tunnel on port {Config.TUNNEL_PORT}...")
        try:
            self._process = await asyncio.create_subprocess_exec(
                Config.CLOUDFLARED_BIN,
                "tunnel",
                "--url",
                f"http://localhost:{Config.TUNNEL_PORT}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Read stderr to find the tunnel URL (cloudflared logs to stderr)
            url = await asyncio.wait_for(self._parse_url(), timeout=30)
            if url:
                self.current_url = url
                logger.info(f"Tunnel URL: {url}")
                return url

            logger.error("Could not parse tunnel URL from cloudflared output.")
            return None

        except asyncio.TimeoutError:
            logger.error("Timed out waiting for cloudflared URL.")
            return None
        except FileNotFoundError:
            raise RuntimeError(
                f"cloudflared not found at '{Config.CLOUDFLARED_BIN}'. "
                "Install it: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
            )

    async def _parse_url(self) -> str | None:
        """Read cloudflared stderr until we find the tunnel URL."""
        url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")

        async for line in self._process.stderr:
            text = line.decode("utf-8", errors="replace")
            logger.debug(f"cloudflared: {text.strip()}")
            match = url_pattern.search(text)
            if match:
                return match.group(0)

        return None

    async def stop(self):
        """Stop the cloudflared tunnel."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            self.current_url = None
            logger.info("Tunnel stopped.")
