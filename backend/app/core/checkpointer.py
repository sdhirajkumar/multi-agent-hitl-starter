"""Checkpointer setup for LangGraph state persistence."""
import os
from pathlib import Path
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[BaseCheckpointSaver, None]:
    """Yield an async checkpointer (AsyncSqliteSaver for zero-setup persistence,

    falling back to MemorySaver if sqlite is unavailable).
    """
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        import aiosqlite

        async with aiosqlite.connect(str(db_path)) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            # Ensure tables are setup if method exists
            if hasattr(checkpointer, "setup"):
                await checkpointer.setup()
            logger.debug(f"Connected AsyncSqliteSaver to {db_path}")
            yield checkpointer
    except Exception as e:
        logger.warning(
            f"Failed to initialize AsyncSqliteSaver ({e}). Falling back to MemorySaver."
        )
        yield MemorySaver()
