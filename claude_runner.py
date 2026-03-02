"""
Handles running Claude Code CLI commands and managing the dev server.
"""

import asyncio
import logging
import subprocess
import socket
from config import Config

logger = logging.getLogger(__name__)

_dev_process: asyncio.subprocess.Process | None = None


class ClaudeRunner:
    async def run(self, instruction: str, repo_path: str) -> dict:
        """Run a Claude Code instruction in a repo directory."""
        cmd = [
            Config.CLAUDE_BIN,
            "--print",
            "--allowedTools", Config.CLAUDE_ALLOWED_TOOLS,
            instruction,
        ]

        logger.info(f"Running Claude in {repo_path}: {instruction[:80]}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=Config.CLAUDE_TIMEOUT
            )

            output = stdout.decode("utf-8", errors="replace").strip()
            error = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                logger.warning(f"Claude exited {proc.returncode}: {error[:200]}")
                return {"output": error or output, "success": False}

            return {"output": output, "success": True}

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Claude took longer than {Config.CLAUDE_TIMEOUT}s. Try a smaller task."
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude binary not found at '{Config.CLAUDE_BIN}'. "
                "Run `which claude` on your server and update CLAUDE_BIN in config.py."
            )

    async def start_dev_server(self) -> bool:
        """Start the Next.js dev server in the frontend repo."""
        global _dev_process

        if await self.is_dev_server_running():
            logger.info("Dev server already running.")
            return True

        logger.info(f"Starting dev server: {Config.FRONTEND_DEV_COMMAND}")
        try:
            _dev_process = await asyncio.create_subprocess_shell(
                Config.FRONTEND_DEV_COMMAND,
                cwd=Config.FRONTEND_REPO_PATH,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait up to 20s for the port to open
            for _ in range(20):
                await asyncio.sleep(1)
                if await self.is_dev_server_running():
                    logger.info(f"Dev server up on port {Config.FRONTEND_DEV_PORT}")
                    return True

            logger.warning("Dev server didn't open port in time.")
            return False

        except Exception as e:
            logger.exception(f"Failed to start dev server: {e}")
            return False

    async def restart_dev_server(self) -> bool:
        """Kill and restart the dev server."""
        global _dev_process
        if _dev_process:
            try:
                _dev_process.terminate()
                await asyncio.wait_for(_dev_process.wait(), timeout=10)
            except Exception:
                pass
            _dev_process = None

        return await self.start_dev_server()

    async def is_dev_server_running(self) -> bool:
        """Check if something is listening on the frontend dev port."""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None, self._check_port, "127.0.0.1", Config.FRONTEND_DEV_PORT
            )
            return True
        except (ConnectionRefusedError, OSError):
            return False

    def _check_port(self, host: str, port: int):
        with socket.create_connection((host, port), timeout=1):
            pass
