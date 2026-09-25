from telegram import InlineKeyboardMarkup

from .config import (
    GROUP_MUSIC_CHANNEL_1,
    GROUP_MUSIC_CHANNEL_2,
)
from .repository import repository


async def check_channel_membership(
    bot,
    user_id: int,
    channel: str,
) -> bool:
    if not channel:
        return True

    chat = channel

    if not (
        chat.startswith("@")
        or chat.startswith("-100")
        or chat.startswith("https://t.me/")
    ):
        chat = f"@{chat}"

    if chat.startswith("https://t.me/"):
        chat = "@" + chat.rstrip("/").split("/")[-1]

    try:
        member = await bot.get_chat_member(
            chat_id=chat,
            user_id=user_id,
        )

        return member.status in {
            "creator",
            "administrator",
            "member",
            "restricted",
        }

    except Exception:
        return False


async def user_has_started_bot(
    group_id: int,
    user_id: int,
) -> bool:
    member = await repository.get_member(
        group_id,
        user_id,
    )

    return bool(
        member and member["bot_started"]
    )


async def check_member_access(
    bot,
    group_id: int,
    user_id: int,
):
    bot_started = await user_has_started_bot(
        group_id,
        user_id,
    )

    channel_1_joined = await check_channel_membership(
        bot,
        user_id,
        GROUP_MUSIC_CHANNEL_1,
    )

    channel_2_joined = await check_channel_membership(
        bot,
        user_id,
        GROUP_MUSIC_CHANNEL_2,
    )

    access = (
        bot_started
        and channel_1_joined
        and channel_2_joined
    )

    await repository.upsert_member(
        group_id=group_id,
        user_id=user_id,
        bot_started=bot_started,
        channel_1_joined=channel_1_joined,
        channel_2_joined=channel_2_joined,
        access_granted=access,
    )

    return {
        "bot_started": bot_started,
        "channel_1_joined": channel_1_joined,
        "channel_2_joined": channel_2_joined,
        "access_granted": access,
    }


async def register_group_member_start(
    group_id: int,
    user_id: int,
):
    current = await repository.get_member(
        group_id,
        user_id,
    )

    await repository.upsert_member(
        group_id=group_id,
        user_id=user_id,
        bot_started=True,
        channel_1_joined=bool(
            current and current["channel_1_joined"]
        ),
        channel_2_joined=bool(
            current and current["channel_2_joined"]
        ),
        access_granted=bool(
            current and current["access_granted"]
        ),
    )


def access_keyboard(
    bot_username: str,
    group_id: int,
):
    from .service import build_member_keyboard

    return build_member_keyboard(
        bot_username=bot_username,
        group_id=group_id,
        channel_1=GROUP_MUSIC_CHANNEL_1,
        channel_2=GROUP_MUSIC_CHANNEL_2,
    )