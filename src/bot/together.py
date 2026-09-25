from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    __version__ as PTB_VERSION,
)

from telegram.constants import ParseMode
from telegram.ext import ContextTypes


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
    """
    ساخت دکمه با پشتیبانی امن از style.
    اگر نسخه PTB قدیمی باشد style حذف می‌شود.
    """

    params = {
        "text": text,
        **kwargs,
    }

    if callback_data is not None:
        params["callback_data"] = callback_data

    if (
        BUTTON_STYLE_SUPPORTED
        and style
    ):
        params["style"] = style

    return InlineKeyboardButton(
        **params
    )


# =========================================================
# TOGETHER MENU
# =========================================================
#
# ساختار:
#
# 👥 Together
#
# ├── 🎧 موزیک گوش بدیم
# ├── 🎬 فیلم ببینیم
# ├── 📚 باهم درس بخونیم
# ├── 🎤 باهم بخونیم
# ├── 🎮 باهم بازی کنیم
# ├── 🌙 شب‌بیداری
# ├── ⚽ فوتبال ببینیم
# ├── 🏃 باهم ورزش کنیم
# ├── 🧑‍💻 باهم Build کنیم
# ├── 🔥 باهم Streak کنیم
# └── 🍳 باهم Cook کنیم
#
# =========================================================

def together_menu():

    return InlineKeyboardMarkup([

        # -------------------------------------------------
        # ROW 1
        # -------------------------------------------------

        [
            button(
                "🎧 موزیک گوش بدیم",
                callback_data="together:music",
                style="success",
            ),

            button(
                "🎬 فیلم ببینیم",
                callback_data="together:watch",
                style="primary",
            ),
        ],

        # -------------------------------------------------
        # ROW 2
        # -------------------------------------------------

        [
            button(
                "📚 باهم درس بخونیم",
                callback_data="together:study",
                                style="success",

            ),

            button(
                "🎤 باهم بخونیم",
                callback_data="together:sing",
                                style="primary",

            ),
        ],

        # -------------------------------------------------
        # ROW 3
        # -------------------------------------------------

        [
            button(
                "🎮 باهم بازی کنیم",
                callback_data="together:gaming",
                                style="success",

            ),

            button(
                "🌙 شب‌بیداری",
                callback_data="together:night",
                                style="primary",

            ),
        ],

        # -------------------------------------------------
        # ROW 4
        # -------------------------------------------------

        [
            button(
                "⚽ فوتبال ببینیم",
                callback_data="together:football",
                                style="success",

            ),

            button(
                "🏃 باهم ورزش کنیم",
                callback_data="together:sport",
                                style="primary",

            ),
        ],

        # -------------------------------------------------
        # ROW 5
        # -------------------------------------------------

        [
            button(
                "🧑‍💻 باهم Build کنیم",
                callback_data="together:build",
                                style="success",

            ),

            button(
                "🔥 باهم Streak کنیم",
                callback_data="together:streak",
                                style="primary",

            ),
        ],

        # -------------------------------------------------
        # ROW 6
        # -------------------------------------------------

        [
            button(
                "🍳 باهم Cook کنیم",
                callback_data="together:cook",
                                style="primary",

            )
        ],

        # -------------------------------------------------
        # BACK
        # -------------------------------------------------

        [
            button(
                "‹ صفحه اصلی",
                callback_data="home",
                        style="danger",

            )
        ],
    ])


# =========================================================
# TOGETHER HOME
# =========================================================

async def together_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query:

        await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>TOGETHER</b>\n"
        "╰────────────────────╯\n\n"

        "<b>الان تو چه فازی‌ای؟</b>\n\n"

        "با آدم‌هایی که همین الان دنبال\n"
        "همین کارن همراه شو.\n\n"

        "🎧 <b>موزیک گوش بدیم</b>\n"
        "🎬 <b>فیلم ببینیم</b>\n"
        "📚 <b>باهم درس بخونیم</b>\n"
        "🎤 <b>باهم بخونیم</b>\n"
        "🎮 <b>باهم بازی کنیم</b>\n"
        "🌙 <b>شب‌بیداری</b>\n"
        "⚽ <b>فوتبال ببینیم</b>\n"
        "🏃 <b>باهم ورزش کنیم</b>\n"
        "🧑‍💻 <b>باهم Build کنیم</b>\n"
        "🔥 <b>باهم Streak کنیم</b>\n"
        "🍳 <b>باهم Cook کنیم</b>"
    )

    keyboard = together_menu()

    # =====================================================
    # CALLBACK
    # =====================================================

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

    # =====================================================
    # MESSAGE
    # =====================================================

    if update.message:

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

        return


# =========================================================
# TOGETHER PLACEHOLDER
# =========================================================

async def together_placeholder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    title: str,
    description: str,
    icon: str,
):

    query = update.callback_query

    if query:

        await query.answer()

    text = (
        "╭────────────────────╮\n"
        f"          {icon} <b>{title}</b>\n"
        "╰────────────────────╯\n\n"

        f"{description}\n\n"

        "✦ <i>این بخش رو قدم‌به‌قدم می‌سازیم.</i>"
    )

    keyboard = InlineKeyboardMarkup([

        [
            button(
                "‹ Together",
                callback_data="together:home",
            )
        ],

        [
            button(
                "⌂ صفحه اصلی",
                callback_data="home",
            )
        ],

    ])

    # =====================================================
    # CALLBACK
    # =====================================================

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

    # =====================================================
    # MESSAGE
    # =====================================================

    if update.message:

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


# =========================================================
# 🎬 WATCH MOVIE
# =========================================================

async def together_watch(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "فیلم ببینیم",

        "با آدم‌هایی که همین الان حال فیلم دیدن دارن همراه شو.",

        "🎬",
    )


# =========================================================
# 🎧 MUSIC
# =========================================================
#
# این بخش دیگر Placeholder نیست.
#
# مستقیم سیستم Music فعلی FAZE را باز می‌کند.
#
# =========================================================

async def together_music(
    update,
    context,
):

    from src.bot.music import music_home

    await music_home(
        update,
        context,
    )


# =========================================================
# 🎮 GAMING
# =========================================================

async def together_gaming(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم بازی کنیم",

        "یه بازی پیدا کن و با آدم‌هایی که همین الان دنبال بازی هستن شروع کن.",

        "🎮",
    )


# =========================================================
# 📚 STUDY
# =========================================================

async def together_study(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم درس بخونیم",

        "با آدم‌هایی که الان مشغول درس خوندنن همراه شو.",

        "📚",
    )


# =========================================================
# 🎤 SING
# =========================================================

async def together_sing(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم بخونیم",

        "میکروفون، آهنگ و چند نفر که پایه‌ان؛ اینجا برای باهم خوندنه.",

        "🎤",
    )


# =========================================================
# 🌙 NIGHT
# =========================================================

async def together_night(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "شب‌بیداری",

        "هنوز بیداری؟ با آدم‌هایی که این ساعت آنلاینن همراه شو.",

        "🌙",
    )


# =========================================================
# ⚽ FOOTBALL
# =========================================================

async def together_football(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "فوتبال ببینیم",

        "با بقیه پای فوتبال باش و همزمان باهاشون همراه شو.",

        "⚽",
    )


# =========================================================
# 🏃 SPORT
# =========================================================

async def together_sport(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم ورزش کنیم",

        "یه فعالیت ورزشی انتخاب کن و با آدم‌هایی که دنبال همین فازن همراه شو.",

        "🏃",
    )


# =========================================================
# 🧑‍💻 BUILD
# =========================================================

async def together_build(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم Build کنیم",

        "یه پروژه، کد یا ایده انتخاب کن و با بقیه باهم بسازین.",

        "🧑‍💻",
    )


# =========================================================
# 🔥 STREAK
# =========================================================

async def together_streak(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم Streak کنیم",

        "یه هدف انتخاب کن و با چند نفر هر روز ادامه‌ش بدین.",

        "🔥",
    )


# =========================================================
# 🍳 COOK
# =========================================================

async def together_cook(
    update,
    context,
):

    await together_placeholder(
        update,
        context,

        "باهم Cook کنیم",

        "یه غذا انتخاب کن و همزمان با بقیه شروع به درست کردنش کن.",

        "🍳",
    )