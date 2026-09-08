import logging

from pyrogram import Client
from pyrogram.types import CallbackQuery

from handlers.permissions import check_rights
from music.player import (
    end_player,
    pause_song,
    play_next,
    resume_song,
)
from music.queue import queue_manager

logger = logging.getLogger(__name__)


def register_callbacks(app: Client):

    @app.on_callback_query()
    async def callback_dispatcher(
        client: Client,
        query: CallbackQuery,
    ):
        # Ignore callbacks that do not belong to a message.
        if not query.message:
            await query.answer(
                "❌ This button is no longer active.",
                show_alert=True,
            )
            return

        chat_id = query.message.chat.id
        user_id = query.from_user.id
        data = query.data or ""

        # Only handle our player callbacks.
        if not data.startswith("player:"):
            return

        # Check permissions.
        allowed, reason = await check_rights(
            client,
            chat_id,
            user_id,
        )

        if not allowed:
            await query.answer(
                reason,
                show_alert=True,
            )
            return

        try:

            # -------------------------------------------------
            # PAUSE
            # -------------------------------------------------

            if data == "player:pause":

                success = await pause_song(
                    chat_id
                )

                if success:
                    await query.answer(
                        "⏸ Paused"
                    )
                else:
                    await query.answer(
                        "❌ Nothing is playing.",
                        show_alert=True,
                    )

            # -------------------------------------------------
            # RESUME
            # -------------------------------------------------

            elif data == "player:resume":

                success = await resume_song(
                    chat_id
                )

                if success:
                    await query.answer(
                        "▶️ Resumed"
                    )
                else:
                    await query.answer(
                        "❌ Nothing is paused.",
                        show_alert=True,
                    )

            # -------------------------------------------------
            # NEXT
            # -------------------------------------------------

            elif data == "player:next":

                current = queue_manager.get_current(
                    chat_id
                )

                if not current:
                    await query.answer(
                        "❌ Nothing is playing.",
                        show_alert=True,
                    )
                    return

                await query.answer(
                    "⏭ Skipping..."
                )

                await play_next(
                    chat_id
                )

            # -------------------------------------------------
            # END
            # -------------------------------------------------

            elif data == "player:end":

                await query.answer(
                    "🛑 Stopping..."
                )

                await end_player(
                    chat_id
                )

            # -------------------------------------------------
            # UNKNOWN CALLBACK
            # -------------------------------------------------

            else:
                await query.answer(
                    "❌ Unknown player action.",
                    show_alert=True,
                )

        except Exception as exc:

            logger.exception(
                "Player callback failed in chat %s",
                chat_id,
            )

            try:
                await query.answer(
                    f"❌ Action failed: {exc}",
                    show_alert=True,
                )
            except Exception:
                pass
