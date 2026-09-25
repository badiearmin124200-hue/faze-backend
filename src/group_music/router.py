from telegram.ext import (
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    filters,
)

from .groups import handle_bot_added
from .handlers import (
    group_music_access,
    group_music_check,
    group_music_room,
    group_music_subscribe,
)


def register_group_music(app):

    # =====================================================
    # BOT ADDED / REMOVED
    # =====================================================

    app.add_handler(
        ChatMemberHandler(
            handle_bot_added,
            ChatMemberHandler.MY_CHAT_MEMBER,
        )
    )

    # =====================================================
    # /faze
    # =====================================================

    app.add_handler(
        CommandHandler(
            "faze",
            group_music_room_command,
            filters=filters.ChatType.GROUPS,
        )
    )

    # =====================================================
    # SUBSCRIBE
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            group_music_subscribe,
            pattern=r"^groupmusic:subscribe:-?\d+$",
        )
    )

    # =====================================================
    # CHECK SUBSCRIPTION / ACCESS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            group_music_check,
            pattern=r"^groupmusic:check:-?\d+$",
        )
    )

    # =====================================================
    # MEMBER ACCESS
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            group_music_access,
            pattern=r"^groupmusic:access:-?\d+$",
        )
    )

    # =====================================================
    # OPEN ROOM
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            group_music_room,
            pattern=r"^groupmusic:room:-?\d+$",
        )
    )


async def group_music_room_command(
    update,
    context,
):
    from .handlers import show_group_music_entry

    await show_group_music_entry(
        update,
        context,
        "all",
    )