import logging
import os
import aiosqlite
import html

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode
from telegram import __version__ as PTB_VERSION

from telegram.ext import (
    Application,
    CommandHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.group_music.router import register_group_music
from src.group_music.handlers import handle_group_music_start

from src.db.database import DB_PATH
from src.bot.profile import registration_conversation

from src.bot.together import (
    together_home,
    together_watch,
    together_music,
    together_gaming,
    together_study,
    together_football,
    together_night,
    together_sing,
    together_sport,
    together_build,
    together_streak,
    together_cook,
)

from src.bot.music import (
    music_home,

    music_rap,
    music_pop,
    music_metal,
    music_rock,
    music_traditional,

    music_with_friend,
    music_in_group,
    music_with_random,

    music_inline_query,

    handle_music_invite,
    accept_music_invitation,
    reject_music_invitation,

    music_ready,
    cancel_music_room_handler,
    leave_music_room,

    music_create_room,
    music_join_start,
    music_join_code,
    music_join_cancel,
    music_enter_room,
)


logger = logging.getLogger(__name__)


# =========================================================
# TELEGRAM BUTTON STYLE COMPATIBILITY
# =========================================================

def _supports_button_style():
    try:
        parts = PTB_VERSION.split(".")

        major = int(parts[0])
        minor = int(parts[1])

        return (
            major > 22
            or (
                major == 22
                and minor >= 7
            )
        )

    except Exception:
        return False


BUTTON_STYLE_SUPPORTED = _supports_button_style()


def button(
    text,
    callback_data=None,
    style=None,
    **kwargs,
):
    params = {
        "text": text,
        **kwargs,
    }

    if callback_data is not None:
        params["callback_data"] = callback_data

    if BUTTON_STYLE_SUPPORTED and style:
        params["style"] = style

    return InlineKeyboardButton(**params)


# =========================================================
# HTML ESCAPE
# =========================================================

def escape(value):
    if value is None:
        return ""

    return html.escape(str(value))


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup([

        [
            button(
                "👥 Together",
                callback_data="together",
                style="primary",
            ),
            button(
                "🎵 Vibe",
                callback_data="vibe",
                style="primary",
            ),
        ],

        [
            button(
                "🔥 Explore",
                callback_data="explore",
                style="primary",
            ),
            button(
                "🔎 Find",
                callback_data="find",
                style="primary",
            ),
        ],

        [
            button(
                "👤 Profile",
                callback_data="profile:home",
                style="primary",
            ),
            button(
                "🛍️ Store",
                callback_data="store",
                style="primary",
            ),
        ],

        [
            button(
                "👤 Our Contacts",
                callback_data="contacts",
                style="primary",
            ),
        ],

    ])


# =========================================================
# DATABASE
# =========================================================

async def get_user(telegram_id):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        )

        return await cursor.fetchone()


async def create_user(telegram_user):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO users (
                telegram_id,
                username,
                first_name,
                display_name,
                profile_completed
            )
            VALUES (?, ?, ?, ?, 0)
            """,
            (
                telegram_user.id,
                telegram_user.username,
                telegram_user.first_name,
                telegram_user.first_name,
            ),
        )

        await db.commit()


# =========================================================
# HOME
# =========================================================



async def show_home(
    update,
    context,
):

    query = update.callback_query

    if query:
        await query.answer()

    telegram_user = update.effective_user

    if not telegram_user:
        return

    user = await get_user(telegram_user.id)

    if not user:

        await create_user(telegram_user)

        user = await get_user(telegram_user.id)

    if not user:
        return

    name = (
        user["display_name"]
        or user["first_name"]
        or telegram_user.first_name
        or "کاربر"
    )

    if user["profile_completed"]:
        profile_status = "✓ پروفایل آماده‌ست"
    else:
        profile_status = "○ پروفایل هنوز کامل نشده"

    text = (
        "✦ <b>Welcome to VELFA</b>\n\n"

        f"سلام <b>{escape(name)}</b> 👋\n\n"

        "اینجا می‌تونی با دوستات، پارتنرت، آدم‌های جدید "
        "یا یه گروه، باهم وقت بگذرونید و هر کاری که دوست دارید انجام بدید.\n"
        "از موزیک و فیلم گرفته تا بازی، درس، ورزش و خیلی چیزهای دیگه.\n"
        "آدم‌های هم‌سلیقه‌ات رو در موضوعات مختلف پیدا کن، "
        "باهاشون آشنا شو و گفتگو کن.\n\n"

        "👥 <b>Together</b>\n"
        "باهم انجامش بدین.\n\n"

        "🎵 <b>Vibe</b>\n"
        "آدم‌های هم‌سلیقه‌ات رو پیدا کن.\n\n"

        "🔥 <b>Explore</b>\n"
        "چیزهای تازه و جذاب رو کشف کن.\n\n"

        "🔎 <b>Find</b>\n"
        "آهنگ، فیلم، پست، لینک و چیزهای مختلف رو پیدا کن.\n\n"

        "👤 <b>Profile</b>\n"
        "اطلاعات و علایقت رو کامل کن تا VELFA بهتر بشناسدت.\n\n"

        f"{profile_status}\n\n"

        "<i>Choose your vibe. Find your people. Do more together.</i>"
    )

    keyboard = main_menu()

    if query:

        try:

            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

            return

        except Exception:
            pass

    if update.message:

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

        return

    try:

        await context.bot.send_message(
            chat_id=telegram_user.id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception:
        pass
# =========================================================
# START
# =========================================================

async def start_handler(
    update,
    context,
):

    telegram_user = update.effective_user

    if not telegram_user:
        return

    user = await get_user(telegram_user.id)

    if not user:

        await create_user(telegram_user)

        user = await get_user(telegram_user.id)

    start_parameter = None

    if context.args:

        start_parameter = context.args[0].strip()

    # =====================================================
    # GROUP MUSIC
    # =====================================================

    if (
        start_parameter
        and start_parameter.startswith("gm_")
    ):

        await handle_group_music_start(
            update,
            context,
            start_parameter,
        )

        return

    # =====================================================
    # MUSIC INVITE
    # =====================================================

    if (
        start_parameter
        and start_parameter.startswith("music_")
    ):

        token = start_parameter[len("music_"):]

        await handle_music_invite(
            update,
            context,
            token,
        )

        return

    if not user:
        return

    # =====================================================
    # PROFILE
    # =====================================================

    if not user["profile_completed"]:

        text = (
            "╭────────────────────╮\n"
            "          ✦ <b>FAZE</b>\n"
            "╰────────────────────╯\n\n"

            "خوش اومدی 👋\n\n"

            "FAZE قراره یه جای متفاوت باشه؛\n"
            "برای آشنا شدن، پیدا کردن آدم‌های هم‌فاز، "
            "موزیک، سرگرمی و کلی تجربه دیگه.\n\n"

            "اول پروفایلت رو بساز تا بریم داخل."
        )

        keyboard = InlineKeyboardMarkup([

            [
                button(
                    "🚀 ساخت پروفایل",
                    callback_data="profile:start",
                    style="success",
                )
            ],

            [
                button(
                    "✦ ورود به FAZE",
                    callback_data="home",
                    style="primary",
                )
            ],

        ])

        if update.message:

            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        return

    await show_home(
        update,
        context,
    )


# =========================================================
# MY ID
# =========================================================

async def my_id(
    update,
    context,
):

    user = update.effective_user

    if not user or not update.message:
        return

    await update.message.reply_text(
        "🆔 <b>Telegram ID</b>\n\n"
        f"<code>{user.id}</code>",
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# RESET PROFILE
# =========================================================

async def reset_profile(
    update,
    context,
):

    user = update.effective_user

    if not user or not update.message:
        return

    admin_id = os.getenv(
        "ADMIN_TELEGRAM_ID",
        "",
    ).strip()

    if not admin_id:

        await update.message.reply_text(
            "⚠️ ADMIN_TELEGRAM_ID در فایل .env تنظیم نشده."
        )

        return

    if str(user.id) != admin_id:

        await update.message.reply_text(
            "⛔ این دستور فقط برای ادمین فعال است."
        )

        return

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (user.id,),
        )

        row = await cursor.fetchone()

        if row:

            user_id = row[0]

            await db.execute(
                """
                DELETE FROM user_achievements
                WHERE user_id = ?
                """,
                (user_id,),
            )

            await db.execute(
                """
                DELETE FROM user_badges
                WHERE user_id = ?
                """,
                (user_id,),
            )

            await db.execute(
                """
                DELETE FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,),
            )

            await db.execute(
                """
                DELETE FROM user_stats
                WHERE user_id = ?
                """,
                (user_id,),
            )

        await db.execute(
            """
            DELETE FROM music_rooms
            WHERE creator_id = ?
               OR guest_id = ?
            """,
            (
                user.id,
                user.id,
            ),
        )

        await db.execute(
            """
            DELETE FROM compatibility_profiles
            WHERE user_id = ?
            """,
            (user.id,),
        )

        await db.execute(
            """
            DELETE FROM compatibility_credits
            WHERE user_id = ?
            """,
            (user.id,),
        )

        await db.execute(
            """
            DELETE FROM live_mode_members
            WHERE user_id = ?
            """,
            (user.id,),
        )

        await db.execute(
            """
            DELETE FROM compatibility_requests
            WHERE sender_id = ?
               OR receiver_id = ?
            """,
            (
                user.id,
                user.id,
            ),
        )

        await db.execute(
            """
            DELETE FROM compatibility_matches
            WHERE user1_id = ?
               OR user2_id = ?
            """,
            (
                user.id,
                user.id,
            ),
        )

        await db.execute(
            """
            DELETE FROM users
            WHERE telegram_id = ?
            """,
            (user.id,),
        )

        await db.commit()

    context.user_data.clear()

    await update.message.reply_text(
        "♻️ <b>پروفایل FAZE ریست شد.</b>\n\n"
        "اطلاعات پروفایل قبلی پاک شد.\n\n"
        "حالا می‌تونی دوباره از صفر ثبت‌نام کنی. ✦\n\n"
        "👉 /start",
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# SIMPLE PAGE
# =========================================================

async def simple_page(
    update,
    context,
    title,
    description,
    icon,
    back_callback="home",
):

    query = update.callback_query

    text = (
        "╭────────────────────╮\n"
        f"        {icon} <b>{escape(title)}</b>\n"
        "╰────────────────────╯\n\n"

        f"{description}\n\n"

        "<i>این بخش در حال توسعه است.</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "‹ برگشت",
                callback_data=back_callback,
            )
        ]
    ])

    if query:

        await query.answer()

        try:

            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        except Exception:

            try:
                await query.message.delete()
            except Exception:
                pass

            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        return

    if update.message:

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


# =========================================================
# VIBE
# =========================================================

async def vibe_home(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🎵 <b>VIBE</b>\n"
        "╰────────────────────╯\n\n"

        "<b>هم‌فاز خودتو پیدا کن.</b>\n\n"

        "Vibe جاییه برای پیدا کردن آدم‌هایی "
        "که سلیقه و حال‌وهوای نزدیک به تو دارن."
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "🧠 هم‌سلیقه",
                callback_data="vibe:similar",
                style="primary",
            )
        ],

        [
            button(
                "🎵 سلیقه موسیقی",
                callback_data="vibe:music",
            ),
            button(
                "🎬 سلیقه فیلم",
                callback_data="vibe:movies",
            ),
        ],

        [
            button(
                "‹ صفحه اصلی",
                callback_data="home",
            )
        ],

    ])

    try:

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception:
        pass


# =========================================================
# EXPLORE
# =========================================================

async def explore_home(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🔥 <b>EXPLORE</b>\n"
        "╰────────────────────╯\n\n"

        "چیزهای جالبی که همین الان تو FAZE جریان دارن.\n\n"

        "آدم‌ها، محتوا، فعالیت‌ها و اتفاق‌های تازه."
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "🔥 الان داغه",
                callback_data="explore:hot",
            ),
            button(
                "✨ تازه‌ها",
                callback_data="explore:new",
            ),
        ],

        [
            button(
                "👥 آدم‌های فعال",
                callback_data="explore:people",
            )
        ],

        [
            button(
                "‹ صفحه اصلی",
                callback_data="home",
            )
        ],

    ])

    try:

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception:
        pass


# =========================================================
# FIND
# =========================================================

async def find_home(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🔎 <b>FIND</b>\n"
        "╰────────────────────╯\n\n"

        "<b>چیو می‌خوای پیدا کنی؟</b>\n\n"

        "اسم، لینک، عکس یا ویدیو بده؛ "
        "FAZE از همون‌جا شروع می‌کنه."
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "🎵 اسم آهنگ بده",
                callback_data="find:song",
            ),
            button(
                "🎬 اسم فیلم بده",
                callback_data="find:movie",
            ),
        ],

        [
            button(
                "📱 لینک Instagram بده",
                callback_data="find:instagram",
            )
        ],

        [
            button(
                "▶️ لینک YouTube بده",
                callback_data="find:youtube",
            )
        ],

        [
            button(
                "📌 لینک Pinterest بده",
                callback_data="find:pinterest",
            )
        ],

        [
            button(
                "🎞️ ویدیو بده",
                callback_data="find:video",
            ),
            button(
                "🖼️ عکس بده",
                callback_data="find:image",
            ),
        ],

        [
            button(
                "🔗 لینک بده",
                callback_data="find:link",
            )
        ],

        [
            button(
                "‹ صفحه اصلی",
                callback_data="home",
            )
        ],

    ])

    try:

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception:
        pass


# =========================================================
# STORE
# =========================================================

async def store_home(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🛍️ <b>STORE</b>\n"
        "╰────────────────────╯\n\n"

        "چیزهایی که می‌تونی داخل FAZE تهیه یا فعال کنی.\n\n"

        "⭐ Premium\n"
        "🪙 Coins\n"
        "🎁 امکانات ویژه"
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "⭐ Premium",
                callback_data="store:premium",
                style="success",
            )
        ],

        [
            button(
                "🪙 Coins",
                callback_data="store:coins",
            ),
            button(
                "🎁 امکانات",
                callback_data="store:extras",
            ),
        ],

        [
            button(
                "‹ صفحه اصلی",
                callback_data="home",
            )
        ],

    ])

    try:

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception:
        pass


# =========================================================
# PROFILE
# =========================================================

async def open_profile(
    update,
    context,
):

    from src.bot.profile import profile_home

    await profile_home(
        update,
        context,
    )


# =========================================================
# PROFILE STATS
# =========================================================

async def profile_stats(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    telegram_user = update.effective_user

    if not telegram_user:
        return

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_user.id,),
        )

        user = await cursor.fetchone()

        if not user:

            await query.answer(
                "پروفایل پیدا نشد.",
                show_alert=True,
            )

            return

        cursor = await db.execute(
            """
            SELECT *
            FROM user_stats
            WHERE user_id = ?
            """,
            (user["id"],),
        )

        stats = await cursor.fetchone()

    if not stats:

        games_played = 0
        games_won = 0
        quizzes = 0
        challenges = 0
        matches = 0
        referrals = 0

    else:

        games_played = stats["games_played"]
        games_won = stats["games_won"]
        quizzes = stats["quizzes_completed"]
        challenges = stats["challenges_completed"]
        matches = stats["matches_count"]
        referrals = stats["referrals_count"]

    text = (
        "╭────────────────────╮\n"
        "          📊 <b>آمار من</b>\n"
        "╰────────────────────╯\n\n"

        f"⭐ <b>Level:</b> {user['level']}\n"
        f"⚡ <b>XP:</b> {user['xp']}\n"
        f"🔥 <b>Streak:</b> {user['streak']} روز\n"
        f"🪙 <b>Coins:</b> {user['coins']}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🎮 بازی‌ها: {games_played}\n"
        f"🏆 بردها: {games_won}\n"
        f"🧠 Quizها: {quizzes}\n"
        f"🔥 Challengeها: {challenges}\n"
        f"🤝 Matchها: {matches}\n"
        f"👥 دعوت‌ها: {referrals}"
    )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                button(
                    "‹ پروفایل",
                    callback_data="profile:home",
                )
            ]
        ]),
    )


# =========================================================
# SETTINGS
# =========================================================

async def profile_settings(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    telegram_user = update.effective_user

    if not telegram_user:
        return

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM user_settings
            WHERE user_id = (
                SELECT id
                FROM users
                WHERE telegram_id = ?
            )
            """,
            (telegram_user.id,),
        )

        settings = await cursor.fetchone()

    if not settings:

        async with aiosqlite.connect(DB_PATH) as db:

            cursor = await db.execute(
                """
                SELECT id
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_user.id,),
            )

            row = await cursor.fetchone()

            if row:

                await db.execute(
                    """
                    INSERT OR IGNORE INTO user_settings (
                        user_id
                    )
                    VALUES (?)
                    """,
                    (row[0],),
                )

                await db.commit()

        show_age = 1
        show_gender = 1
        show_city = 1
        show_favorites = 1
        show_activity = 1
        notifications = 1

    else:

        show_age = settings["show_age"]
        show_gender = settings["show_gender"]
        show_city = settings["show_city"]
        show_favorites = settings["show_favorites"]
        show_activity = settings["show_activity"]
        notifications = settings["notifications_enabled"]

    def mark(value):
        return "✓" if value else "○"

    text = (
        "╭────────────────────╮\n"
        "          ⚙️ <b>تنظیمات</b>\n"
        "╰────────────────────╯\n\n"

        "تنظیمات پروفایل و حریم خصوصی از اینجا کنترل میشه."
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                f"{mark(show_age)} نمایش سن",
                callback_data="settings:age",
            ),
            button(
                f"{mark(show_gender)} نمایش جنسیت",
                callback_data="settings:gender",
            ),
        ],

        [
            button(
                f"{mark(show_city)} نمایش استان",
                callback_data="settings:city",
            ),
            button(
                f"{mark(show_favorites)} نمایش علایق",
                callback_data="settings:favorites",
            ),
        ],

        [
            button(
                f"{mark(show_activity)} نمایش فعالیت",
                callback_data="settings:activity",
            )
        ],

        [
            button(
                f"{mark(notifications)} اعلان‌ها",
                callback_data="settings:notifications",
            )
        ],

        [
            button(
                "‹ پروفایل",
                callback_data="profile:home",
            )
        ],

    ])

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# =========================================================
# SETTINGS TOGGLE
# =========================================================

async def toggle_setting(
    update,
    context,
    field,
):

    query = update.callback_query

    if not query:
        return

    telegram_user = update.effective_user

    if not telegram_user:
        return

    allowed_fields = {
        "age": "show_age",
        "gender": "show_gender",
        "city": "show_city",
        "favorites": "show_favorites",
        "activity": "show_activity",
        "notifications": "notifications_enabled",
    }

    column = allowed_fields.get(field)

    if not column:

        await query.answer(
            "تنظیم نامعتبر است.",
            show_alert=True,
        )

        return

    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            """
            SELECT id
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_user.id,),
        )

        user_row = await cursor.fetchone()

        if not user_row:

            await query.answer(
                "پروفایل پیدا نشد.",
                show_alert=True,
            )

            return

        user_id = user_row[0]

        cursor = await db.execute(
            f"""
            SELECT {column}
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,),
        )

        row = await cursor.fetchone()

        if not row:

            await db.execute(
                """
                INSERT OR IGNORE INTO user_settings (
                    user_id
                )
                VALUES (?)
                """,
                (user_id,),
            )

            current = 1

        else:

            current = row[0]

        new_value = 0 if current else 1

        await db.execute(
            f"""
            UPDATE user_settings
            SET {column} = ?
            WHERE user_id = ?
            """,
            (
                new_value,
                user_id,
            ),
        )

        await db.commit()

    await query.answer(
        "فعال شد." if new_value else "غیرفعال شد."
    )

    await profile_settings(
        update,
        context,
    )


# =========================================================
# OUR CONTACTS
# =========================================================

async def contacts_page(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "       👤 <b>Our Contacts</b>\n"
        "╰────────────────────╯\n\n"

        "راه‌های ارتباطی رسمی FAZE\n\n"

        "🛟 <b>Support</b>\n"
        "@YOUR_SUPPORT_ID\n\n"

        "📢 <b>Advertising</b>\n"
        "@YOUR_ADS_ID\n\n"

        "🤝 <b>Partnership</b>\n"
        "@YOUR_PARTNERSHIP_ID\n\n"

        "<i>برای پشتیبانی، تبلیغات یا همکاری\n"
        "از آیدی مربوطه استفاده کن.</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            button(
                "‹ Back",
                callback_data="home",
                style="danger",
            )
        ]
    ])

    try:

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception as error:

        logger.exception(
            "Failed to open contacts page: %s",
            error,
        )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def callback_handler(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        await show_home(
            update,
            context,
        )

        return

    # =====================================================
    # OUR CONTACTS
    # =====================================================

    if data == "contacts":

        await contacts_page(
            update,
            context,
        )

        return

    # =====================================================
    # VIBE
    # =====================================================

    if data == "vibe":

        await vibe_home(
            update,
            context,
        )

        return

    if data == "vibe:similar":

        await simple_page(
            update,
            context,
            "هم‌سلیقه",
            "آدم‌هایی که سلیقه و علایق نزدیک به تو دارن.",
            "🧠",
            "vibe",
        )

        return

    if data == "vibe:music":

        await simple_page(
            update,
            context,
            "سلیقه موسیقی",
            "آدم‌ها رو بر اساس سلیقه موسیقی پیدا کن.",
            "🎵",
            "vibe",
        )

        return

    if data == "vibe:movies":

        await simple_page(
            update,
            context,
            "سلیقه فیلم",
            "آدم‌هایی با سلیقه فیلم مشابه خودت پیدا کن.",
            "🎬",
            "vibe",
        )

        return

    # =====================================================
    # EXPLORE
    # =====================================================

    if data == "explore":

        await explore_home(
            update,
            context,
        )

        return

    if data == "explore:hot":

        await simple_page(
            update,
            context,
            "الان داغه",
            "چیزهایی که همین الان بیشتر تو FAZE جریان دارن.",
            "🔥",
            "explore",
        )

        return

    if data == "explore:new":

        await simple_page(
            update,
            context,
            "تازه‌ها",
            "جدیدترین اتفاق‌ها و فعالیت‌های FAZE.",
            "✨",
            "explore",
        )

        return

    if data == "explore:people":

        await simple_page(
            update,
            context,
            "آدم‌های فعال",
            "آدم‌هایی که همین الان تو FAZE فعال هستن.",
            "👥",
            "explore",
        )

        return

    # =====================================================
    # FIND
    # =====================================================

    if data == "find":

        await find_home(
            update,
            context,
        )

        return

    find_pages = {

        "find:song": (
            "اسم آهنگ",
            "🎵",
            "اسم آهنگ رو بفرست تا FAZE پیداش کنه."
        ),

        "find:movie": (
            "اسم فیلم",
            "🎬",
            "اسم فیلم رو بفرست تا FAZE دنبالش بگرده."
        ),

        "find:instagram": (
            "Instagram",
            "📱",
            "لینک Instagram رو بفرست."
        ),

        "find:youtube": (
            "YouTube",
            "▶️",
            "لینک YouTube رو بفرست."
        ),

        "find:pinterest": (
            "Pinterest",
            "📌",
            "لینک Pinterest رو بفرست."
        ),

        "find:video": (
            "ویدیو",
            "🎞️",
            "ویدیو رو بفرست تا FAZE بررسیش کنه."
        ),

        "find:image": (
            "عکس",
            "🖼️",
            "عکس رو بفرست تا FAZE بررسیش کنه."
        ),

        "find:link": (
            "لینک",
            "🔗",
            "لینک رو بفرست تا FAZE بررسیش کنه."
        ),

    }

    if data in find_pages:

        title, icon, description = find_pages[data]

        await simple_page(
            update,
            context,
            title,
            description,
            icon,
            "find",
        )

        return

    # =====================================================
    # STORE
    # =====================================================

    if data == "store":

        await store_home(
            update,
            context,
        )

        return

    if data == "store:premium":

        await simple_page(
            update,
            context,
            "Premium",
            "امکانات Premium برای FAZE.",
            "⭐",
            "store",
        )

        return

    if data == "store:coins":

        await simple_page(
            update,
            context,
            "Coins",
            "خرید و استفاده از Coinهای FAZE.",
            "🪙",
            "store",
        )

        return

    if data == "store:extras":

        await simple_page(
            update,
            context,
            "امکانات ویژه",
            "امکانات اضافه و آیتم‌های ویژه FAZE.",
            "🎁",
            "store",
        )

        return

    # =====================================================
    # PROFILE
    # =====================================================

    if data == "profile:home":

        await open_profile(
            update,
            context,
        )

        return

    if data == "profile:start":

        from src.bot.profile import profile_home

        await profile_home(
            update,
            context,
        )

        return

    if data == "profile:achievements":

        await simple_page(
            update,
            context,
            "دستاوردها",
            "دستاوردهایی که در FAZE باز می‌کنی اینجا نمایش داده می‌شن.",
            "🏆",
            "profile:home",
        )

        return

    if data == "profile:stats":

        await profile_stats(
            update,
            context,
        )

        return

    if data == "profile:settings":

        await profile_settings(
            update,
            context,
        )

        return

    if data == "profile:noop":

        await query.answer()

        return

    # =====================================================
    # SETTINGS
    # =====================================================

    if data.startswith("settings:"):

        setting = data.split(":", 1)[1]

        await toggle_setting(
            update,
            context,
            setting,
        )

        return

    # =====================================================
    # TOGETHER
    # =====================================================

    if data == "together":

        await together_home(
            update,
            context,
        )

        return

    if data == "together:home":

        await together_home(
            update,
            context,
        )

        return

    if data == "together:watch":

        await together_watch(
            update,
            context,
        )

        return

    if data == "together:music":

        await music_home(
            update,
            context,
        )

        return

    if data == "together:gaming":

        await together_gaming(
            update,
            context,
        )

        return

    if data == "together:study":

        await together_study(
            update,
            context,
        )

        return

    if data == "together:football":

        await together_football(
            update,
            context,
        )

        return

    if data == "together:night":

        await together_night(
            update,
            context,
        )

        return

    if data == "together:sing":

        await together_sing(
            update,
            context,
        )

        return

    if data == "together:sport":

        await together_sport(
            update,
            context,
        )

        return

    if data == "together:build":

        await together_build(
            update,
            context,
        )

        return

    if data == "together:streak":

        await together_streak(
            update,
            context,
        )

        return

    if data == "together:cook":

        await together_cook(
            update,
            context,
        )

        return

    # =====================================================
    # MUSIC PLAYLIST
    # =====================================================

    if data == "music:playlist":

        from src.bot.music import music_playlist_menu

        await music_playlist_menu(
            update,
            context,
        )

        return

    if data == "music:playlist:mine":

        from src.bot.music import music_playlist_placeholder

        await music_playlist_placeholder(
            update,
            context,
            "پلی‌لیست من",
            "پلی‌لیست شخصی خودت رو بساز و مدیریت کن.",
            "👤",
        )

        return

    if data == "music:playlist:duo":

        from src.bot.music import music_playlist_placeholder

        await music_playlist_placeholder(
            update,
            context,
            "پلی‌لیست دو نفره",
            "یه پلی‌لیست مشترک برای دو نفر.",
            "👥",
        )

        return

    if data == "music:playlist:group":

        from src.bot.music import music_playlist_placeholder

        await music_playlist_placeholder(
            update,
            context,
            "پلی‌لیست گروهی",
            "یه پلی‌لیست مشترک برای کل Room.",
            "👨‍👩‍👧‍👦",
        )

        return

    # =====================================================
    # MUSIC
    # =====================================================

    if data == "music:friend":

        await music_with_friend(
            update,
            context,
        )

        return

    if data == "music:random":

        await music_with_random(
            update,
            context,
        )

        return

    if data == "music:group":

        await music_in_group(
            update,
            context,
        )

        return

    if data == "music:create":

        await music_create_room(
            update,
            context,
        )

        return

    if data == "music:rooms":

        from src.bot.music import music_rooms_page

        await music_rooms_page(
            update,
            context,
        )

        return

    if data == "music:stranger_song":

        from src.bot.music import music_feature_placeholder

        await music_feature_placeholder(
            update,
            context,
            "آهنگ برای یک غریبه",
            "یه آهنگ انتخاب کن تا به صورت ناشناس برای یک نفر فرستاده بشه.",
            "🎁",
        )

        return

    if data == "music:nearby":

        from src.bot.music import music_feature_placeholder

        await music_feature_placeholder(
            update,
            context,
            "با آدم‌های نزدیک",
            "با آدم‌هایی از محدوده کلی مشابه خودت موزیک گوش کن.",
            "🗺️",
        )

        return

    if data in (
        "music:artist",
        "music:artist_fans",
    ):

        from src.bot.music import music_feature_placeholder

        await music_feature_placeholder(
            update,
            context,
            "طرفدارهای این خواننده",
            "اسم خواننده رو بده و با طرفدارهای همون خواننده همراه شو.",
            "🎼",
        )

        return

    if data in (
        "music:album",
        "music:album_fans",
    ):

        from src.bot.music import music_feature_placeholder

        await music_feature_placeholder(
            update,
            context,
            "طرفدارهای این آلبوم",
            "با طرفدارهای یک آلبوم مشترک موزیک گوش کن.",
            "💿",
        )

        return

    if data == "music:send_song":

        from src.bot.music import music_feature_placeholder

        await music_feature_placeholder(
            update,
            context,
            "آهنگ بفرستید",
            "یه آهنگ رو برای دوست یا آدم دیگه‌ای بفرست.",
            "🎵",
        )

        return

    # =====================================================
    # MUSIC GENRES
    # =====================================================

    if data == "music:rap":

        await music_rap(
            update,
            context,
        )

        return

    if data == "music:pop":

        await music_pop(
            update,
            context,
        )

        return

    if data == "music:metal":

        await music_metal(
            update,
            context,
        )

        return

    if data == "music:rock":

        await music_rock(
            update,
            context,
        )

        return

    if data == "music:traditional":

        await music_traditional(
            update,
            context,
        )

        return

    # =====================================================
    # LEGACY MUSIC MODES
    # =====================================================

    if data.startswith("musicmode:group:"):

        from src.group_music.handlers import show_group_music_entry

        genre = data.split(":", 2)[2]

        context.user_data["music_genre"] = genre

        await show_group_music_entry(
            update,
            context,
            genre,
        )

        return

    if data.startswith("musicmode:friend:"):

        genre = data.split(":", 2)[2]

        context.user_data["music_genre"] = genre

        await music_with_friend(
            update,
            context,
        )

        return

    if data.startswith("musicmode:random:"):

        genre = data.split(":", 2)[2]

        context.user_data["music_genre"] = genre

        await music_with_random(
            update,
            context,
        )

        return

    # =====================================================
    # MUSIC ROOM ENTER
    # =====================================================

    if data.startswith("musicroom:enter:"):

        room_id = data.split(":", 2)[2]

        await music_enter_room(
            update,
            context,
            room_id,
        )

        return

    # =====================================================
    # MUSIC INVITES
    # =====================================================

    if data.startswith("musicinvite:accept:"):

        room_id = data.split(":", 2)[2]

        await accept_music_invitation(
            update,
            context,
            room_id,
        )

        return

    if data.startswith("musicinvite:reject:"):

        room_id = data.split(":", 2)[2]

        await reject_music_invitation(
            update,
            context,
            room_id,
        )

        return

    # =====================================================
    # READY
    # =====================================================

    if data.startswith("musicready:"):

        room_id = data.split(":", 1)[1]

        await music_ready(
            update,
            context,
            room_id,
        )

        return

    # =====================================================
    # ROOM CANCEL
    # =====================================================

    if data.startswith("musicroom:cancel:"):

        room_id = data.split(":", 2)[2]

        await cancel_music_room_handler(
            update,
            context,
            room_id,
        )

        return

    # =====================================================
    # ROOM LEAVE
    # =====================================================

    if data.startswith("musicroom:leave:"):

        room_id = data.split(":", 2)[2]

        await leave_music_room(
            update,
            context,
            room_id,
        )

        return

    # =====================================================
    # NO WEBAPP
    # =====================================================

    if data == "musicroom:no_webapp":

        await query.answer(
            "WEBAPP_URL هنوز در .env تنظیم نشده.",
            show_alert=True,
        )

        return

    # =====================================================
    # OLD CALLBACKS
    # =====================================================

    old_pages = {

        "discover": (
            "کشف",
            "🔎",
            "آدم‌های جدید و چیزهای جدید رو کشف کن.",
        ),

        "games": (
            "بازی‌ها",
            "🎮",
            "بازی‌های FAZE اینجا قرار می‌گیرن.",
        ),

        "quiz": (
            "Quiz",
            "🧠",
            "Quizهای مختلف برای رقابت و سرگرمی.",
        ),

        "rooms": (
            "Rooms",
            "🏠",
            "اتاق‌های FAZE برای دورهمی و تعامل.",
        ),

        "challenges": (
            "Challenges",
            "🔥",
            "چالش‌های روزانه و رقابت‌های FAZE.",
        ),

        "ranking": (
            "Ranking",
            "🏆",
            "جدول رتبه‌بندی کاربران FAZE.",
        ),

        "rewards": (
            "Rewards",
            "🎁",
            "اینجا بخش جایزه‌ها و پاداش‌های FAZE قرار می‌گیره.",
        ),

    }

    if data in old_pages:

        title, icon, description = old_pages[data]

        await simple_page(
            update,
            context,
            title,
            description,
            icon,
            "home",
        )

        return

    if data == "more":

        await show_more(
            update,
            context,
        )

        return

    # =====================================================
    # UNKNOWN
    # =====================================================

    await query.answer(
        "این بخش هنوز فعال نشده.",
        show_alert=False,
    )


# =========================================================
# MORE
# =========================================================

async def show_more(
    update,
    context,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>بیشتر</b>\n"
        "╰────────────────────╯\n\n"

        "بخش‌های بیشتر FAZE از اینجا در دسترس خواهند بود."
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "⚙️ تنظیمات",
                callback_data="profile:settings",
            )
        ],

        [
            button(
                "🎁 Rewards",
                callback_data="rewards",
            ),
            button(
                "🏆 Ranking",
                callback_data="ranking",
            ),
        ],

        [
            button(
                "‹ برگشت",
                callback_data="home",
            )
        ],

    ])

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# =========================================================
# REGISTER
# =========================================================

def register(app: Application):

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start_handler,
        )
    )

    # -----------------------------------------------------
    # RESET
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "resetprofile",
            reset_profile,
        )
    )

    # -----------------------------------------------------
    # MY ID
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "myid",
            my_id,
        )
    )

    # -----------------------------------------------------
    # PROFILE REGISTRATION
    # -----------------------------------------------------

    app.add_handler(
        registration_conversation()
    )

    # -----------------------------------------------------
    # MUSIC INLINE
    # -----------------------------------------------------

    app.add_handler(
        InlineQueryHandler(
            music_inline_query
        )
    )

    # -----------------------------------------------------
    # MUSIC JOIN CONVERSATION
    # -----------------------------------------------------

    music_join_conversation = ConversationHandler(

        entry_points=[

            CallbackQueryHandler(
                music_join_start,
                pattern=r"^music:join$",
            )

        ],

        states={

            "MUSIC_ROOM_CODE": [

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    music_join_code,
                ),

                CallbackQueryHandler(
                    music_join_cancel,
                    pattern=r"^music:join:cancel$",
                ),

            ]

        },

        fallbacks=[

            CallbackQueryHandler(
                music_join_cancel,
                pattern=r"^music:join:cancel$",
            )

        ],

        per_user=True,
        per_chat=True,
        allow_reentry=True,
    )

    app.add_handler(
        music_join_conversation
    )

    # -----------------------------------------------------
    # GENERAL CALLBACKS
    # -----------------------------------------------------

    app.add_handler(

        CallbackQueryHandler(

            callback_handler,

            pattern=(
                r"^(?:"

                # HOME
                r"home|"

                # CONTACTS
                r"contacts|"

                # TOP LEVEL
                r"vibe|"
                r"explore|"
                r"find|"
                r"store|"

                # VIBE
                r"vibe:similar|"
                r"vibe:music|"
                r"vibe:movies|"

                # EXPLORE
                r"explore:hot|"
                r"explore:new|"
                r"explore:people|"

                # FIND
                r"find:song|"
                r"find:movie|"
                r"find:instagram|"
                r"find:youtube|"
                r"find:pinterest|"
                r"find:video|"
                r"find:image|"
                r"find:link|"

                # STORE
                r"store:premium|"
                r"store:coins|"
                r"store:extras|"

                # PROFILE
                r"profile:home|"
                r"profile:start|"
                r"profile:achievements|"
                r"profile:stats|"
                r"profile:settings|"
                r"profile:noop|"

                # SETTINGS
                r"settings:age|"
                r"settings:gender|"
                r"settings:city|"
                r"settings:favorites|"
                r"settings:activity|"
                r"settings:notifications|"

                # TOGETHER
                r"together|"
                r"together:home|"
                r"together:watch|"
                r"together:music|"
                r"together:gaming|"
                r"together:study|"
                r"together:football|"
                r"together:night|"
                r"together:sing|"
                r"together:sport|"
                r"together:build|"
                r"together:streak|"
                r"together:cook|"

                # MUSIC PLAYLIST
                r"music:playlist|"
                r"music:playlist:mine|"
                r"music:playlist:duo|"
                r"music:playlist:group|"

                # MUSIC
                r"music:friend|"
                r"music:random|"
                r"music:group|"
                r"music:create|"
                r"music:join|"
                r"music:rooms|"

                r"music:stranger_song|"
                r"music:nearby|"
                r"music:artist|"
                r"music:artist_fans|"
                r"music:album|"
                r"music:album_fans|"
                r"music:send_song|"

                # MUSIC GENRES
                r"music:rap|"
                r"music:pop|"
                r"music:metal|"
                r"music:rock|"
                r"music:traditional|"

                # LEGACY MUSIC MODES
                r"musicmode:friend:[A-Za-z0-9_-]+|"
                r"musicmode:group:[A-Za-z0-9_-]+|"
                r"musicmode:random:[A-Za-z0-9_-]+|"

                # MUSIC INVITES
                r"musicinvite:accept:[A-Za-z0-9_-]+|"
                r"musicinvite:reject:[A-Za-z0-9_-]+|"

                # READY
                r"musicready:[A-Za-z0-9_-]+|"

                # MUSIC ROOM
                r"musicroom:enter:[A-Za-z0-9_-]+|"
                r"musicroom:cancel:[A-Za-z0-9_-]+|"
                r"musicroom:leave:[A-Za-z0-9_-]+|"
                r"musicroom:no_webapp|"

                # OLD CALLBACKS
                r"discover|"
                r"games|"
                r"quiz|"
                r"rooms|"
                r"challenges|"
                r"ranking|"
                r"rewards|"
                r"more"

                r")$"
            ),
        )
    )

    # -----------------------------------------------------
    # GROUP MUSIC
    # -----------------------------------------------------

    register_group_music(app)

    # -----------------------------------------------------
    # LOG
    # -----------------------------------------------------

    logger.info(
        "FAZE handlers registered successfully."
    )