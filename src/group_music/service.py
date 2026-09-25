import secrets
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import (
    GROUP_MUSIC_DURATION_DAYS,
    GROUP_MUSIC_PAYMENT_URL,
    GROUP_MUSIC_PRICE_TOMAN,
)
from .repository import repository


def now_utc():
    return datetime.now(timezone.utc)


def telegram_time(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def make_room_id(group_id: int) -> str:
    return (
        f"gmusic_{abs(group_id)}_"
        f"{secrets.token_urlsafe(8)}"
    )


async def ensure_group(
    group_id: int,
    title: str,
    added_by: int | None = None,
):
    return await repository.create_or_update_group(
        group_id,
        title,
        added_by,
    )


async def get_subscription(group_id: int):
    return await repository.get_active_subscription(group_id)


async def has_active_subscription(group_id: int) -> bool:
    return bool(
        await repository.get_active_subscription(group_id)
    )


async def create_pending_subscription(
    group_id: int,
    purchased_by: int,
):
    start = now_utc()
    expires = start + timedelta(
        days=GROUP_MUSIC_DURATION_DAYS
    )

    payment_ref = (
        f"GM-{group_id}-"
        f"{purchased_by}-"
        f"{secrets.token_hex(6)}"
    )

    return await repository.create_subscription(
        group_id=group_id,
        purchased_by=purchased_by,
        price=GROUP_MUSIC_PRICE_TOMAN,
        started_at=telegram_time(start),
        expires_at=telegram_time(expires),
        status="pending",
        payment_ref=payment_ref,
    )


async def activate_subscription(
    group_id: int,
    purchased_by: int,
    payment_ref: str | None = None,
):
    start = now_utc()
    expires = start + timedelta(
        days=GROUP_MUSIC_DURATION_DAYS
    )

    return await repository.create_subscription(
        group_id=group_id,
        purchased_by=purchased_by,
        price=GROUP_MUSIC_PRICE_TOMAN,
        started_at=telegram_time(start),
        expires_at=telegram_time(expires),
        status="active",
        payment_ref=payment_ref,
    )


async def get_or_create_room(
    group_id: int,
    created_by: int,
):
    existing = await repository.get_active_room(
        group_id
    )

    if existing:
        await repository.add_room_member(
            existing["room_id"],
            created_by,
        )
        return existing

    room_id = make_room_id(group_id)

    room = await repository.create_room(
        group_id,
        room_id,
        created_by,
    )

    await repository.add_room_member(
        room_id,
        created_by,
    )

    return room


def build_start_url(
    bot_username: str,
    group_id: int,
) -> str:
    return (
        f"https://t.me/{bot_username}"
        f"?start=gm_{group_id}"
    )


def build_payment_keyboard(
    group_id: int,
    payment_url: str | None = None,
):
    buttons = []

    if payment_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    "💳 پرداخت اشتراک ۳۰ روزه",
                    url=payment_url,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔄 بررسی اشتراک",
                callback_data=f"groupmusic:check:{group_id}",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "🏠 بازگشت",
                callback_data="home",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def build_member_keyboard(
    bot_username: str,
    group_id: int,
    channel_1: str,
    channel_2: str,
):
    buttons = []

    if channel_1:
        url = (
            channel_1
            if channel_1.startswith("http")
            else f"https://t.me/{channel_1.lstrip('@')}"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "📢 عضویت در کانال اول",
                    url=url,
                )
            ]
        )

    if channel_2:
        url = (
            channel_2
            if channel_2.startswith("http")
            else f"https://t.me/{channel_2.lstrip('@')}"
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "📢 عضویت در کانال دوم",
                    url=url,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "🔄 بررسی دسترسی",
                callback_data=f"groupmusic:access:{group_id}",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def payment_url_for(
    group_id: int,
    user_id: int,
):
    if not GROUP_MUSIC_PAYMENT_URL:
        return ""

    try:
        return GROUP_MUSIC_PAYMENT_URL.format(
            group_id=group_id,
            user_id=user_id,
            price=GROUP_MUSIC_PRICE_TOMAN,
        )
    except Exception:
        return GROUP_MUSIC_PAYMENT_URL