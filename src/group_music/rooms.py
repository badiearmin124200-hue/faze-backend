from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .service import get_or_create_room


# =========================================================
# MINI APP URL
# =========================================================

def room_webapp_url(
    bot_username: str,
    room_id: str,
):
    """
    Opens the Telegram Mini App with the room ID.
    """

    username = (
        bot_username
        .lstrip("@")
        .strip()
    )

    room_id = str(room_id).strip()

    if not username:
        return ""

    if not room_id:
        return ""

    start_param = quote(
        room_id,
        safe="",
    )

    return (
        f"https://t.me/{username}"
        f"?startapp={start_param}"
    )


# =========================================================
# GROUP ROOM
# =========================================================

async def create_or_get_group_room(
    group_id: int,
    user_id: int,
):
    return await get_or_create_room(
        group_id,
        user_id,
    )


# =========================================================
# ROOM KEYBOARD
# =========================================================

def room_keyboard(
    bot_username: str,
    room_id: str,
):
    webapp_url = room_webapp_url(
        bot_username,
        room_id,
    )

    if not webapp_url:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Mini App در دسترس نیست",
                    callback_data="home",
                )
            ]
        ])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎵 ورود به Music Room",
                url=webapp_url,
            )
        ]
    ])