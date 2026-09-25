from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from .repository import repository
from .service import ensure_group


async def handle_bot_added(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat_member = update.my_chat_member

    if not chat_member:
        return

    chat = chat_member.chat
    new_status = chat_member.new_chat_member.status

    if chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        return

    group_id = chat.id

    if new_status in {
        "member",
        "administrator",
    }:
        added_by = None

        if chat_member.from_user:
            added_by = chat_member.from_user.id

        await ensure_group(
            group_id=group_id,
            title=chat.title or "FAZE Group",
            added_by=added_by,
        )

        return

    if new_status in {
        "left",
        "kicked",
    }:
        await repository.deactivate_group(
            group_id
        )


async def get_group_info(
    group_id: int,
):
    return await repository.get_group(
        group_id
    )


async def is_group_active(
    group_id: int,
) -> bool:
    group = await repository.get_group(
        group_id
    )

    if not group:
        return False

    return bool(group["active"])