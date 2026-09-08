import asyncio

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

from database import (
    add_dj,
    get_djs,
    is_dj_mode_enabled,
    remove_dj,
    set_dj_mode,
)
from handlers.permissions import check_rights
from music.player import (
    cleanup_player_ui,
    end_player,
    format_duration,
    pause_song,
    play_next,
    resume_song,
    start_stream,
)
from music.queue import Song, queue_manager
from music.youtube import search_youtube
from utils.cleanup import auto_delete


ADMIN_STATUSES = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
}


async def delete_later(client: Client, message: Message) -> None:
    asyncio.create_task(
        auto_delete(
            client,
            message.chat.id,
            message.id,
        )
    )


async def send_temp(
    client: Client,
    message: Message,
    text: str,
) -> Message:
    response = await message.reply_text(text)
    await delete_later(client, response)
    return response


async def is_admin(
    client: Client,
    chat_id: int,
    user_id: int,
) -> bool:
    try:
        member = await client.get_chat_member(
            chat_id,
            user_id,
        )
        return member.status in ADMIN_STATUSES
    except Exception:
        return False


def register_commands(app: Client):

    # ---------------------------------------------------------
    # /play
    # ---------------------------------------------------------

    @app.on_message(filters.command("play") & filters.group)
    async def play_handler(
        client: Client,
        message: Message,
    ):
        chat_id = message.chat.id
        user = message.from_user

        if not user:
            return

        allowed, reason = await check_rights(
            client,
            chat_id,
            user.id,
            is_play_action=True,
        )

        if not allowed:
            await send_temp(
                client,
                message,
                reason,
            )
            return

        query = " ".join(
            message.command[1:]
        ).strip()

        if not query:
            await send_temp(
                client,
                message,
                "❌ Usage: `/play <song name or YouTube link>`",
            )
            return

        status_msg = await message.reply_text(
            "🔍 Searching YouTube..."
        )

        try:
            song_info = await search_youtube(query)

            if not song_info:
                await status_msg.edit_text(
                    "❌ No playable result found on YouTube."
                )
                await delete_later(
                    client,
                    status_msg,
                )
                return

            song = Song(
                title=song_info["title"],
                channel=song_info["channel"],
                duration=song_info["duration"],
                url=song_info["url"],
               
