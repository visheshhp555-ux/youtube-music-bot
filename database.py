import logging

import aiosqlite

from config import DATABASE_PATH

logger = logging.getLogger(__name__)


async def init_db():
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    chat_id INTEGER PRIMARY KEY,
                    dj_mode INTEGER NOT NULL DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS djs (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    PRIMARY KEY (chat_id, user_id)
                )
            """)

            await db.commit()

        logger.info("Database initialized successfully.")

    except Exception:
        logger.exception("Failed to initialize database.")
        raise


async def is_dj_mode_enabled(chat_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT dj_mode FROM groups WHERE chat_id = ?",
            (chat_id,)
        ) as cursor:
            row = await cursor.fetchone()

    return bool(row[0]) if row else False


async def set_dj_mode(chat_id: int, status: bool):
    dj_mode = 1 if status else 0

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO groups (chat_id, dj_mode)
            VALUES (?, ?)
            ON CONFLICT(chat_id)
            DO UPDATE SET dj_mode = excluded.dj_mode
            """,
            (chat_id, dj_mode)
        )
        await db.commit()


async def add_dj(chat_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO djs (chat_id, user_id)
            VALUES (?, ?)
            """,
            (chat_id, user_id)
        )
        await db.commit()


async def remove_dj(chat_id: int, user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            DELETE FROM djs
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        )
        await db.commit()


async def is_dj(chat_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """
            SELECT 1
            FROM djs
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()

    return row is not None


async def get_djs(chat_id: int) -> list[int]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            """
            SELECT user_id
            FROM djs
            WHERE chat_id = ?
            ORDER BY user_id
            """,
            (chat_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    return [row[0] for row in rows]
