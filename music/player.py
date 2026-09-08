import asyncio
import logging
from typing import Optional

from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from music.queue import Song, queue_manager
from music.youtube import get_stream_url

logger = logging.getLogger(__name__)

bot_client: Optional[Client] = None
pytgcalls_client: Optional[PyTgCalls] = None

player_messages: dict[int, int] = {}
play_locks: dict[int, asyncio.Lock] = {}
paused_chats: set[int] = set()


def get_lock(chat_id: int) -> asyncio.Lock:
    return play_locks.setdefault(chat_id, asyncio.Lock())


def format_duration(seconds: int) -> str:
    if not seconds:
        return "00:00"

    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def get_player_markup(
    is_paused: bool = False,
) -> InlineKeyboardMarkup:
    pause_button = (
        InlineKeyboardButton(
            "▶️ Resume",
            callback_data="player:resume",
        )
        if is_paused
        else InlineKeyboardButton(
            "⏸ Pause",
            callback_data="player:pause",
        )
    )

    return InlineKeyboardMarkup(
        [
            [
                pause_button,
                InlineKeyboardButton(
                    "⏭ Next",
                    callback_data="player:next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🛑 End",
                    callback_data="player:end",
                )
            ],
        ]
    )


async def update_player_ui(
    chat_id: int,
    song: Song,
    is_paused: bool = False,
) -> None:
    if bot_client is None:
        return

    text = (
        "🎵 **Now Playing**\n\n"
        f"**{song.title}**\n"
        f"🎤 {song.channel}\n"
        f"⏱ {format_duration(song.duration)}\n"
        f"👤 Requested by: {song.requester}\n\n"
        f"[▶️ Open on YouTube]({song.url})"
    )

    markup = get_player_markup(is_paused)

    message_id = player_messages.get(chat_id)

    if message_id:
        try:
            await bot_client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=markup,
                disable_web_page_preview=True,
            )
            return
        except Exception:
            player_messages.pop(chat_id, None)

    try:
        message = await bot_client.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            disable_web_page_preview=True,
        )

        player_messages[chat_id] = message.id

    except Exception:
        logger.exception(
            "Failed to create player message for %s",
            chat_id,
        )


async def cleanup_player_ui(chat_id: int) -> None:
    if bot_client is None:
        return

    message_id = player_messages.pop(chat_id, None)

    if not message_id:
        return

    try:
        await bot_client.delete_messages(
            chat_id=chat_id,
            message_ids=message_id,
        )
    except Exception:
        logger.debug(
            "Could not delete player message in %s",
            chat_id,
        )


async def play_song(
    chat_id: int,
    song: Song,
) -> None:
    if pytgcalls
