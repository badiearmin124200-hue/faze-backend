import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from .repository import repository

from .config import (
    GROUP_MUSIC_CHANNEL_1,
    GROUP_MUSIC_CHANNEL_1_TITLE,
    GROUP_MUSIC_CHANNEL_2,
    GROUP_MUSIC_CHANNEL_2_TITLE,
    GROUP_MUSIC_DURATION_DAYS,
    GROUP_MUSIC_PRICE_TOMAN,
    GROUP_MUSIC_TEST_MODE,
)
from .membership import (
    check_member_access,
    register_group_member_start,
)
from .payments import create_payment
from .rooms import (
    create_or_get_group_room,
    room_keyboard,
)
from .service import (
    build_member_keyboard,
    build_payment_keyboard,
    ensure_group,
    get_subscription,
    has_active_subscription,
)


# =========================================================
# WEBAPP
# =========================================================

def get_webapp_base_url():
    """
    URL اصلی Mini App.
    اول WEBAPP_URL را می‌خواند.
    FAZE_WEBAPP_URL برای سازگاری با تنظیمات قدیمی نگه داشته شده.
    """

    value = os.getenv(
        "WEBAPP_URL",
        "",
    ).strip()

    if not value:
        value = os.getenv(
            "FAZE_WEBAPP_URL",
            "",
        ).strip()

    if value:
        return value.rstrip("/")

    return ""


# =========================================================
# COMMON KEYBOARDS
# =========================================================

def group_music_back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ بازگشت",
                callback_data="together:music",
            )
        ],
    ])


# =========================================================
# GROUP MUSIC START
# =========================================================

async def handle_group_music_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    payload: str,
):
    if not update.effective_user:
        return

    if not payload.startswith("gm_"):
        return

    try:
        group_id = int(
            payload.removeprefix("gm_")
        )
    except ValueError:
        return

    user_id = update.effective_user.id

    await register_group_member_start(
        group_id,
        user_id,
    )

    message = update.effective_message

    if not message:
        return

    keyboard_rows = [
        [
            InlineKeyboardButton(
                "📢 بررسی دسترسی",
                callback_data=f"groupmusic:check:{group_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "‹ بازگشت",
                callback_data="together:music",
            )
        ],
    ]

    await message.reply_text(
        "✅ <b>ربات VELFA برای این گروه فعال شد.</b>\n\n"
        "حالا به دو کانال موردنیاز عضو شو و بعد "
        "«بررسی دسترسی» رو بزن.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard_rows
        ),
    )


# =========================================================
# GROUP MUSIC ENTRY
# =========================================================

async def show_group_music_entry(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    genre: str = "all",
):
    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    # =====================================================
    # PRIVATE CHAT
    # =====================================================

    if message.chat.type == ChatType.PRIVATE:

        bot_username = context.bot.username or ""

        if not bot_username:
            try:
                bot = await context.bot.get_me()
                bot_username = bot.username or ""
            except Exception:
                bot_username = ""

        if not bot_username:

            text = (
                "⚠️ <b>خطا</b>\n\n"
                "نام کاربری بات پیدا نشد."
            )

            keyboard = group_music_back_keyboard()

            if query:
                try:
                    await query.edit_message_text(
                        text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                except Exception:
                    pass

            elif message:
                await message.reply_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )

            return

        # -------------------------------------------------
        # Telegram Add-to-Group link
        # -------------------------------------------------

        add_to_group_url = (
            f"https://t.me/{bot_username}"
            f"?startgroup=groupmusic"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "➕ افزودن VELFA به گروه",
                    url=add_to_group_url,
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ بازگشت",
                    callback_data="together:music",
                )
            ],
        ])

        text = (
            "╭────────────────────╮\n"
            "       👥 <b>VELFA GROUP MUSIC</b>\n"
            "╰────────────────────╯\n\n"
            "برای استفاده از Music Room گروهی، "
            "VELFA رو به گروه تلگرامت اضافه کن. 🎧\n\n"
            "بعد از اضافه شدن، داخل همون گروه "
            "دستور <code>/faze</code> رو بفرست.\n\n"
            "👥 ظرفیت: <b>۲۰ نفر همزمان</b>"
        )

        if query:
            try:
                await query.edit_message_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                return
            except Exception:
                pass

        await message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        return

    # =====================================================
    # GROUP CHECK
    # =====================================================

    if message.chat.type not in {
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    }:
        await message.reply_text(
            "👥 این بخش فقط در چت خصوصی یا گروه قابل استفاده است.",
            reply_markup=group_music_back_keyboard(),
        )
        return

    group_id = message.chat.id

    # =====================================================
    # REGISTER GROUP
    # =====================================================

    await ensure_group(
        group_id,
        message.chat.title or "VELFA Group",
        user.id,
    )

    # =====================================================
    # ADMIN CHECK
    # =====================================================

    is_admin = await is_group_admin(
        context,
        group_id,
        user.id,
    )

    # =====================================================
    # SUBSCRIPTION
    # =====================================================

    active_subscription = (
        await has_active_subscription(
            group_id
        )
    )

    # =====================================================
    # TEST MODE
    # =====================================================

    if GROUP_MUSIC_TEST_MODE and is_admin:
        active_subscription = True

    # =====================================================
    # ADMIN
    # =====================================================

    if is_admin:

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 اشتراک ۳۰ روزه",
                    callback_data=(
                        f"groupmusic:subscribe:{group_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🎵 ورود به Music Room",
                    callback_data=(
                        f"groupmusic:room:{group_id}"
                    ),
                )
            ],
        ])

        if GROUP_MUSIC_TEST_MODE:
            status = "🟢 اشتراک فعال است (حالت تست)."
        else:
            status = (
                "🟢 اشتراک فعال است."
                if active_subscription
                else "🔴 اشتراک فعالی وجود ندارد."
            )

        await message.reply_text(
            "👥 <b>VELFA Group Music</b>\n\n"
            f"{status}\n\n"
            f"💳 اشتراک: "
            f"{GROUP_MUSIC_PRICE_TOMAN:,} تومان\n"
            f"⏱ مدت: {GROUP_MUSIC_DURATION_DAYS} روز",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        return

    # =====================================================
    # MEMBER
    # =====================================================

    access = await check_member_access(
        context.bot,
        group_id,
        user.id,
    )

    if not active_subscription:

        await message.reply_text(
            "⛔ <b>اشتراک این گروه فعال نیست.</b>\n\n"
            "ادمین گروه باید اشتراک ۳۰ روزه تهیه کند.",
            parse_mode="HTML",
            reply_markup=group_music_back_keyboard(),
        )

        return

    if not access["access_granted"]:

        missing = []

        if not access["bot_started"]:
            missing.append("🤖 استارت ربات")

        if not access["channel_1_joined"]:
            missing.append(
                f"📢 {GROUP_MUSIC_CHANNEL_1_TITLE}"
            )

        if not access["channel_2_joined"]:
            missing.append(
                f"📢 {GROUP_MUSIC_CHANNEL_2_TITLE}"
            )

        keyboard = build_member_keyboard(
            bot_username=context.bot.username or "",
            group_id=group_id,
            channel_1=GROUP_MUSIC_CHANNEL_1,
            channel_2=GROUP_MUSIC_CHANNEL_2,
        )

        await message.reply_text(
            "🔒 برای ورود به Music Room باید "
            "موارد زیر کامل شود:\n\n"
            + "\n".join(
                f"• {item}"
                for item in missing
            ),
            reply_markup=keyboard,
        )

        return

    # =====================================================
    # MEMBER HAS ACCESS
    # =====================================================

    await send_group_room(
        update,
        context,
        group_id,
        user.id,
    )


# =========================================================
# SEND GROUP ROOM
# =========================================================

async def send_group_room(
    update,
    context,
    group_id,
    user_id,
):
    await repository.upsert_member(
        group_id=group_id,
        user_id=user_id,
        bot_started=True,
        channel_1_joined=True,
        channel_2_joined=True,
        access_granted=True,
    )

    room = await create_or_get_group_room(
        group_id,
        user_id,
    )

    message = update.effective_message

    if not message:
        return

    if not room:
        await message.reply_text(
            "❌ ساخت Music Room انجام نشد.",
            reply_markup=group_music_back_keyboard(),
        )
        return

    bot_username = context.bot.username or ""

    if not bot_username:
        try:
            bot = await context.bot.get_me()
            bot_username = bot.username or ""
        except Exception:
            bot_username = ""

    if not bot_username:
        await message.reply_text(
            "❌ username بات پیدا نشد.",
            reply_markup=group_music_back_keyboard(),
        )
        return

    # =====================================================
    # ROOM MESSAGE
    # =====================================================

    await message.reply_text(
        "🎵 <b>VELFA Music Room</b>\n\n"
        "اتاق موسیقی گروه آماده است. 🔥\n\n"
        "👥 ظرفیت: <b>۲۰ نفر همزمان</b>",
        parse_mode="HTML",
        reply_markup=room_keyboard(
            bot_username,
            room["room_id"],
        ),
    )


# =========================================================
# CHECK GROUP ADMIN
# =========================================================

async def is_group_admin(
    context: ContextTypes.DEFAULT_TYPE,
    group_id: int,
    user_id: int,
):
    try:

        member = await context.bot.get_chat_member(
            group_id,
            user_id,
        )

        return member.status in {
            "creator",
            "administrator",
        }

    except Exception:
        return False


# =========================================================
# SUBSCRIBE
# =========================================================

async def group_music_subscribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    try:
        group_id = int(
            query.data.split(":")[-1]
        )
    except (
        ValueError,
        AttributeError,
    ):
        await query.answer(
            "❌ اطلاعات گروه نامعتبر است.",
            show_alert=True,
        )
        return

    user_id = query.from_user.id

    # =====================================================
    # ADMIN CHECK
    # =====================================================

    if not await is_group_admin(
        context,
        group_id,
        user_id,
    ):
        await query.answer(
            "فقط ادمین گروه می‌تواند اشتراک بخرد.",
            show_alert=True,
        )
        return

    await query.answer()

    # =====================================================
    # CREATE PAYMENT
    # =====================================================

    payment = await create_payment(
        group_id,
        user_id,
    )

    url = payment.get(
        "payment_url",
        "",
    )

    keyboard = build_payment_keyboard(
        group_id,
        url,
    )

    if url:

        text = (
            "💳 <b>اشتراک VELFA Group Music</b>\n\n"
            f"💰 مبلغ: {GROUP_MUSIC_PRICE_TOMAN:,} تومان\n"
            f"⏱ مدت: {GROUP_MUSIC_DURATION_DAYS} روز\n\n"
            "بعد از پرداخت، اشتراک توسط سیستم پرداخت "
            "تأیید می‌شود."
        )

    else:

        text = (
            "💳 <b>اشتراک VELFA Group Music</b>\n\n"
            f"💰 مبلغ: {GROUP_MUSIC_PRICE_TOMAN:,} تومان\n"
            f"⏱ مدت: {GROUP_MUSIC_DURATION_DAYS} روز\n\n"
            "سیستم پرداخت هنوز تنظیم نشده است."
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# CHECK ACCESS / SUBSCRIPTION
# =========================================================

async def group_music_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:
        parts = query.data.split(":")
        group_id = int(
            parts[-1]
        )
    except (
        ValueError,
        AttributeError,
    ):
        return

    user_id = query.from_user.id

    # =====================================================
    # TEST MODE FOR ADMIN
    # =====================================================

    if (
        GROUP_MUSIC_TEST_MODE
        and await is_group_admin(
            context,
            group_id,
            user_id,
        )
    ):
        await query.message.reply_text(
            "🟢 اشتراک تستی فعال است."
        )

        await send_group_room(
            update,
            context,
            group_id,
            user_id,
        )

        return

    # =====================================================
    # REAL SUBSCRIPTION
    # =====================================================

    subscription = await get_subscription(
        group_id
    )

    if not subscription:

        await query.message.reply_text(
            "🔴 اشتراک فعال نیست."
        )

        return

    # =====================================================
    # ADMIN
    # =====================================================

    if await is_group_admin(
        context,
        group_id,
        user_id,
    ):

        await query.message.reply_text(
            "🟢 اشتراک گروه فعال است."
        )

        return

    # =====================================================
    # MEMBER
    # =====================================================

    access = await check_member_access(
        context.bot,
        group_id,
        user_id,
    )

    if access["access_granted"]:

        await send_group_room(
            update,
            context,
            group_id,
            user_id,
        )

        return

    await query.message.reply_text(
        "🔒 هنوز شرایط دسترسی کامل نشده.",
        reply_markup=build_member_keyboard(
            context.bot.username or "",
            group_id,
            GROUP_MUSIC_CHANNEL_1,
            GROUP_MUSIC_CHANNEL_2,
        ),
    )


# =========================================================
# ACCESS BUTTON
# =========================================================

async def group_music_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await group_music_check(
        update,
        context,
    )


# =========================================================
# ROOM BUTTON
# =========================================================

async def group_music_room(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:
        group_id = int(
            query.data.split(":")[-1]
        )
    except (
        ValueError,
        AttributeError,
    ):
        return

    user_id = query.from_user.id

    # =====================================================
    # ADMIN TEST MODE
    # =====================================================

    is_admin = await is_group_admin(
        context,
        group_id,
        user_id,
    )

    if GROUP_MUSIC_TEST_MODE and is_admin:

        await send_group_room(
            update,
            context,
            group_id,
            user_id,
        )

        return

    # =====================================================
    # REAL SUBSCRIPTION
    # =====================================================

    if not await has_active_subscription(
        group_id
    ):

        await query.message.reply_text(
            "🔴 اشتراک این گروه فعال نیست."
        )

        return

    # =====================================================
    # ADMIN
    # =====================================================

    if is_admin:

        await send_group_room(
            update,
            context,
            group_id,
            user_id,
        )

        return

    # =====================================================
    # MEMBER
    # =====================================================

    access = await check_member_access(
        context.bot,
        group_id,
        user_id,
    )

    if not access["access_granted"]:

        await query.message.reply_text(
            "🔒 دسترسی شما کامل نیست.",
            reply_markup=build_member_keyboard(
                context.bot.username or "",
                group_id,
                GROUP_MUSIC_CHANNEL_1,
                GROUP_MUSIC_CHANNEL_2,
            ),
        )

        return

    await send_group_room(
        update,
        context,
        group_id,
        user_id,
    )