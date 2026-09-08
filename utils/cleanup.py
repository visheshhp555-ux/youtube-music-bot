import asyncio
import logging

from pyrogram import Client

logger = logging.getLogger(__name__)


async def auto_delete(
    client: Client,
    chat_id: int,
    message_id: int,
    delay: int = 120,
):
    """Delete a temporary Telegram message after a delay."""

    try:
        await asyncio.sleep(delay)

        await client.delete_messages(
            chat_id=chat_id,
            message_ids=message_id,
        )

    except asyncio.CancelledError:
        logger.debug(
            "Cleanup task cancelled for message %s in chat %s",
            message_id,
            chat_id,
        )
        raise

    except Exception as exc:
        # Message may already be deleted or inaccessible.
        logger.debug(
            "Could not delete message %s in chat %s: %s",
            message_id,
            chat_id,
            exc,
        )
