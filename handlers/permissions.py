from pyrogram import Client
from pyrogram.enums import ChatMemberStatus

from database import is_dj, is_dj_mode_enabled


ADMIN_STATUSES = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
}


async def is_admin(
    client: Client,
    chat_id: int,
    user_id: int,
) -> bool:
    """Return True if the user is the group owner/admin."""

    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ADMIN_STATUSES
    except Exception:
        return False


async def check_rights(
    client: Client,
    chat_id: int,
    user_id: int,
    is_play_action: bool = False,
) -> tuple[bool, str]:
    """
    Permission hierarchy:

    Owner/Admin:
        Always allowed.

    DJ:
        Allowed to control music.

    Normal member:
        Can use /play only when DJ Mode is OFF.
        Other music controls require DJ/Admin.
    """

    # Owner/Admin always has full control.
    if await is_admin(client, chat_id, user_id):
        return True, ""

    # Explicitly assigned DJ has full music control.
    if await is_dj(chat_id, user_id):
        return True, ""

    # Normal members can only play when DJ Mode is OFF.
    if is_play_action:
        dj_mode = await is_dj_mode_enabled(chat_id)

        if not dj_mode:
            return True, ""

    return (
        False,
        "❌ You don't have permission to control the music.",
    )
