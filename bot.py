import asyncio
import logging

from pyrogram import Client, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import StreamAudioEnded

import config
import database
import music.player as player

from handlers.commands import register_commands
from handlers.callbacks import register_callbacks


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
)

logger = logging.getLogger("MusicBot")


# ---------------------------------------------------------
# Telegram Bot
# ---------------------------------------------------------

bot = Client(
    "MusicBotTelegram",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)


# ---------------------------------------------------------
# Assistant User Account
# ---------------------------------------------------------

if not config.SESSION_STRING:
    raise RuntimeError(
        "SESSION_STRING is required for voice-chat playback."
    )

assistant = Client(
    "MusicBotAssistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
)


# ---------------------------------------------------------
# PyTgCalls
# ---------------------------------------------------------

call_py = PyTgCalls(
    assistant
)


# Give player.py access to the clients.
player.bot_client = bot
player.pytgcalls_client = call_py


# ---------------------------------------------------------
# Stream End Event
# ---------------------------------------------------------

@call_py.on_stream_end()
async def stream_end_handler(
    client: PyTgCalls,
    event,
):
    if isinstance(event, StreamAudioEnded):
        chat_id = event.chat_id

        logger.info(
            "Audio ended in chat %s. Playing next track.",
            chat_id,
        )

        try:
            await player.play_next(
                chat_id
            )
        except Exception:
            logger.exception(
                "Failed to play next track in %s",
                chat_id,
            )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

async def main():

    logger.info(
        "Initializing database..."
    )

    await database.init_db()


    logger.info(
        "Registering command handlers..."
    )

    register_commands(
        bot
    )


    logger.info(
        "Registering callback handlers..."
    )

    register_callbacks(
        bot
    )


    logger.info(
        "Starting Telegram bot..."
    )

    await bot.start()


    logger.info(
        "Starting assistant account..."
    )

    await assistant.start()


    logger.info(
        "Starting PyTgCalls..."
    )

    await call_py.start()


    # -----------------------------------------------------
    # Connection Information
    # -----------------------------------------------------

    bot_info = await bot.get_me()

    assistant_info = await assistant.get_me()

    logger.info(
        "Bot online: @%s (%s)",
        bot_info.username,
        bot_info.id,
    )

    logger.info(
        "Assistant online: %s (%s)",
        assistant_info.first_name,
        assistant_info.id,
    )


    logger.info(
        "Music bot is ready."
    )


    # Keep application alive.
    await idle()


    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------

    logger.info(
        "Stopping PyTgCalls..."
    )

    await call_py.stop()


    logger.info(
        "Stopping assistant..."
    )

    await assistant.stop()


    logger.info(
        "Stopping bot..."
    )

    await bot.stop()


    logger.info(
        "Shutdown complete."
    )


# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":

    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        logger.info(
            "Process interrupted."
        )

    except Exception:
        logger.exception(
            "Fatal application error."
        )
