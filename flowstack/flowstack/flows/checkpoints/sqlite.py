"""
Credit to LangGraph -
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/sqlite.py
https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/aiosqlite.py
"""

import asyncio
import sqlite3
import threading
from typing import Any, AsyncIterator, Iterator, Optional, Self

import aiosqlite

from flowstack.flows import Checkpoint, CheckpointMetadata, CheckpointTuple, Checkpointer
from flowstack.flows.serde import Serializer

SETUP_SCRIPT = """
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS checkpoints (
        thread_id TEXT NOT NULL,
        thread_ts TEXT NOT NULL,
        parent_ts TEXT,
        checkpoint BLOB,
        metadata BLOB,
        PRIMARY KEY (thread_id, thread_ts)
    );
"""

class SqliteCheckpointer(Checkpointer):
    conn: sqlite3.Connection
    async_conn: aiosqlite.Connection
    lock: threading.Lock
    async_lock: asyncio.Lock
    is_setup: bool

    def __init__(
        self,
        conn: sqlite3.Connection,
        async_conn: aiosqlite.Connection,
        *,
        serde: Optional[Serializer] = None
    ):
        super().__init__(serde=serde)
        self.conn = conn
        self.async_conn = async_conn
        self.lock = threading.Lock()
        self.async_lock = asyncio.Lock()
        self.is_setup = False

    @classmethod
    def from_conn_string(cls, conn_string: str) -> Self:
        return cls(
            sqlite3.Connection(conn_string, check_same_thread=False),
            aiosqlite.connect(conn_string)
        )

    def get(self, **kwargs) -> Optional[CheckpointTuple]:
        pass

    async def aget(self, **kwargs) -> Optional[CheckpointTuple]:
        pass

    def search(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> Iterator[CheckpointTuple]:
        pass

    async def asearch(
        self,
        filters: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[CheckpointTuple]:
        pass

    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    def put_writes(
        self,
        writes: list[tuple[str, Any]],
        task_id: str,
        **kwargs
    ) -> None:
        pass

    async def aput_writes(
        self,
        writes: list[tuple[str, Any]],
        task_id: str,
        **kwargs
    ) -> None:
        pass