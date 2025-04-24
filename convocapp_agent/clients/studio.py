import logging
import datetime
import asyncio
import os

from typing import Any
from anyio import ClosedResourceError
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client

from models.match_models import CreateMatch


MAX_RETRIES = 20
RETRY_DELAY_BASE = 1
RETRY_DELAY_MAX = 30

load_dotenv()


class StudioClient:
    def __init__(self):
        self.url = os.getenv("STUDIO_URL")
        self.session: ClientSession | None = None
        self.retry_count = 0
        self._reconnecting = asyncio.Lock()
        self._connected = asyncio.Event()
        self._connection_task: asyncio.Task | None = None
        self._keep_alive: asyncio.Event | None = None
        self.timeout = 50

    async def connect(self):
        """Starts and waits for the connection to be ready."""
        # If already running, check if it's stuck
        if self._connection_task:
            if self._connection_task.done():
                self._connection_task = None  # allow retry
            else:
                if self._connected.is_set():
                    return
                else:
                    # Wait, but with timeout to detect stuck connections
                    try:
                        await asyncio.wait_for(self._connected.wait(), timeout=self.timeout)
                        return
                    except asyncio.TimeoutError:
                        logging.warning("[Studio] Connection task appears stuck. Restarting...")
                        self._connection_task.cancel()
                        try:
                            await self._connection_task
                        except asyncio.CancelledError:
                            pass
                        self._connection_task = None

        # Clear and restart connection
        self._connected.clear()
        self._connection_task = asyncio.create_task(self._run_connection())
        await self._connected.wait()

    async def _run_connection(self):
        logging.info("[Studio] Connecting to SSE...")

        self._keep_alive = asyncio.Event()

        try:
            async with sse_client(f"{self.url}/sse") as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    self.retry_count = 0
                    self._connected.set()
                    logging.info("[Studio] Connected and initialized ✅")

                    # Wait forever unless .cleanup() triggers .set()
                    await self._keep_alive.wait()

        except asyncio.CancelledError:
            logging.info("[Studio] Connection task cancelled 🧹")
            self.session = None
            self._connected.clear()

        except Exception as e:
            logging.error(f"[Studio] Connection error: {e}")
            self.session = None
            self._connected.clear()

    async def cleanup(self):
        if self._keep_alive:
            self._keep_alive.set()
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
            self._connection_task = None
        self.session = None
        self._connected.clear()
        logging.info("[Studio] Cleaned up connection")

    async def ensure_connection(self):
        logging.info("[Studio] Ensuring connection...")
        if self.session:
            return

        async with self._reconnecting:
            if self.session:
                return
            await self.connect()

    async def call_tool(self, name: str, args: dict) -> Any:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await self.ensure_connection()

                result = await asyncio.wait_for(self.session.call_tool(name, args), timeout=self.timeout)

                return result

            except (asyncio.TimeoutError, ClosedResourceError) as e:
                logging.warning(f"[Studio] Attempt {attempt} failed: {type(e).__name__} - {e}")
                self.session = None
                self._connected.clear()

                if attempt < MAX_RETRIES:
                    backoff = min(RETRY_DELAY_BASE * (2 ** (attempt - 1)), RETRY_DELAY_MAX)
                    logging.info(f"[Studio] Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    logging.error(f"[Studio] Max retries reached ({MAX_RETRIES}). Giving up.")
                    raise

            except Exception as e:
                logging.error(f"[Studio] Tool call failed with non-retryable error: {e}")
                raise

    async def create_match(self, args: CreateMatch) -> Any:
        return await self.call_tool("create_match", {"when": args.when, "where": args.where})

    async def edit_match(self, match_id: str, new_time: datetime.datetime) -> Any:
        return await self.call_tool("edit_match", {"id": match_id, "when": new_time.isoformat()})


studio = StudioClient()
