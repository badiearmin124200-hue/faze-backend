import os
import secrets
from html import escape
from urllib.parse import quote

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db.database import (
    create_music_room,
    create_active_music_room,
    join_active_music_room,
    get_music_room,
    set_music_ready,
    activate_music_room,
    cancel_music_room,
    leave_music_room as db_leave_music_room,
)


# =========================================================
# CONSTANTS
# =========================================================

GENRES = {
    "rap": ("رپ", "🎤"),
    "pop": ("پاپ", "🎵"),
    "metal": ("متال", "🤘"),
    "rock": ("راک", "🎸"),
    "traditional": ("سنتی", "🪕"),
}

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 6


# =========================================================
# HELPERS
# =========================================================

def genre_title(genre: str):
    return GENRES.get(
        genre,
        ("موسیقی", "🎧"),
    )[0]


def genre_icon(genre: str):
    return GENRES.get(
        genre,
        ("موسیقی", "🎧"),
    )[1]


def get_webapp_url():
    return os.getenv(
        "WEBAPP_URL",
        "",
    ).strip().rstrip("/")


def music_room_url(
    room_id: str,
    token: str,
):
    base_url = get_webapp_url()

    if not base_url:
        return None

    separator = "&" if "?" in base_url else "?"

    return (
        f"{base_url}"
        f"{separator}"
        f"room_id={quote(str(room_id))}"
        f"&token={quote(str(token))}"
    )


def get_bot_username(context):
    return context.bot_data.get(
        "bot_username"
    )


def generate_room_code():
    return "".join(
        secrets.choice(ROOM_CODE_ALPHABET)
        for _ in range(ROOM_CODE_LENGTH)
    )


def music_back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            )
        ],
    ])


def music_join_retry_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 ورود دوباره",
                callback_data="music:join",
            )
        ],
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            )
        ],
    ])


# =========================================================
# MUSIC MENU - NEW FAZE STRUCTURE
# =========================================================

def music_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📋 پلی‌لیست",
                callback_data="music:playlist",
                                style="primary",

            ),
        ],
        [
            InlineKeyboardButton(
                "🧑 با دوست",
                callback_data="music:friend",
                                style="primary",
            ),
            InlineKeyboardButton(
                "🕵️ با ناشناس",
                callback_data="music:random",
                                style="primary",

            ),
        ],
        [
            InlineKeyboardButton(
                "👥 Add to Group",
                callback_data="music:group",
                                style="primary",

            ),
        ],
        [
            InlineKeyboardButton(
                "➕ ساخت Room",
                callback_data="music:create",
                 style="success",

            ),
            InlineKeyboardButton(
                "🚪 ورود به Room",
                callback_data="music:join",
                 style="success",

            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Rooms",
                callback_data="music:rooms",
                 style="success",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 آهنگ برای یک غریبه",
                callback_data="music:stranger_song",
                                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                "🗺️ با آدم‌های نزدیک",
                callback_data="music:nearby",
                                 style="success",

            ),
        ],
        [
            InlineKeyboardButton(
                "🎼 با طرفدارهای این خواننده",
                callback_data="music:artist",
                                style="primary",

            ),
        ],
        [
            InlineKeyboardButton(
                "💿 با طرفدارهای این آلبوم",
                callback_data="music:album",
                                                 style="success",

            ),
        ],
        [
            InlineKeyboardButton(
                "🎵 آهنگ بفرسید",
                callback_data="music:send_song",
                                style="primary",
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ Together",
                callback_data="together:home",
                         style="danger",

            ),
        ],
    ])


# =========================================================
# MUSIC HOME
# =========================================================

async def music_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>FAZE MUSIC</b>\n"
        "╰────────────────────╯\n\n"
        "اینجا می‌تونی موسیقی رو با آدم‌های مختلف "
        "تجربه کنی. 🎶\n\n"
        "👥 با دوست یا آدم‌های جدید گوش بده.\n"
        "🏠 Room بساز یا وارد Room شو.\n"
        "📋 پلی‌لیست شخصی و گروهی داشته باش.\n"
        "🎁 برای یک غریبه آهنگ بفرست.\n"
        "🎼 با طرفدارهای خواننده یا آلبوم موردعلاقه‌ات باش.\n\n"
        "یک گزینه رو انتخاب کن:"
    )

    keyboard = music_menu()

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


# =========================================================
# PLAYLIST
# =========================================================

def music_playlist_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👤 پلی‌لیست من",
                callback_data="music:playlist:mine",
            ),
        ],
        [
            InlineKeyboardButton(
                "👥 پلی‌لیست دو نفره",
                callback_data="music:playlist:duo",
            ),
        ],
        [
            InlineKeyboardButton(
                "👨‍👩‍👧‍👦 پلی‌لیست گروهی",
                callback_data="music:playlist:group",
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            ),
        ],
    ])


async def music_playlist_menu_handler(
    update,
    context,
):
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          📋 <b>PLAYLIST</b>\n"
        "╰────────────────────╯\n\n"
        "پلی‌لیستت رو انتخاب کن:"
    )

    keyboard = music_playlist_menu()

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


async def music_playlist_placeholder(
    update,
    context,
    playlist_type=None,
):
    query = update.callback_query

    if query:
        await query.answer()

    titles = {
        "mine": "👤 پلی‌لیست من",
        "duo": "👥 پلی‌لیست دو نفره",
        "group": "👨‍👩‍👧‍👦 پلی‌لیست گروهی",
    }

    title = titles.get(
        playlist_type,
        "📋 پلی‌لیست",
    )

    descriptions = {
        "mine": (
            "اینجا آهنگ‌هایی که خودت ذخیره کردی "
            "نمایش داده می‌شن."
        ),
        "duo": (
            "اینجا می‌تونی با یک نفر دیگه "
            "پلی‌لیست مشترک بسازی."
        ),
        "group": (
            "اینجا اعضای یک Room یا گروه می‌تونن "
            "پلی‌لیست مشترک داشته باشن."
        ),
    }

    description = descriptions.get(
        playlist_type,
        "سیستم پلی‌لیست FAZE در حال آماده‌سازی است.",
    )

    text = (
        "╭────────────────────╮\n"
        f"          {title}\n"
        "╰────────────────────╯\n\n"
        f"{description}\n\n"
        "🎵 این بخش به سیستم Music FAZE متصل خواهد شد."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📋 پلی‌لیست",
                callback_data="music:playlist",
                
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
                
            ),
        ],
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


# =========================================================
# ROOM LIST
# =========================================================

async def music_rooms_page(
    update,
    context,
):
    query = update.callback_query

    if query:
        await query.answer()

    text = (
        "╭────────────────────╮\n"
        "          🏠 <b>ROOM ها</b>\n"
        "╰────────────────────╯\n\n"
        "اینجا محل مدیریت Room های موسیقی توئه. 🎧\n\n"
        "Room فعال بساز، با کد وارد شو یا "
        "Room هایی که در آینده به آن‌ها دسترسی داری رو ببین.\n\n"
        "برای شروع می‌تونی یک Room جدید بسازی."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ ساخت Room",
                callback_data="music:create",
            ),
            InlineKeyboardButton(
                "🚪 ورود به Room",
                callback_data="music:join",
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            ),
        ],
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


# =========================================================
# GENERIC MUSIC FEATURE PLACEHOLDER
# =========================================================

async def music_feature_placeholder(
    update,
    context,
    feature: str = "",
):
    query = update.callback_query

    if query:
        await query.answer()

    feature_data = {
        "stranger_song": (
            "🎁",
            "آهنگ برای یک غریبه",
            "یک آهنگ انتخاب می‌کنی و FAZE اون رو "
            "به شکل ناشناس برای یک نفر می‌فرسته.\n\n"
            "اگر طرف مقابل بخواد، می‌تونه در جواب "
            "یک آهنگ برای تو بفرسته.",
        ),
        "nearby": (
            "🗺️",
            "با آدم‌های نزدیک",
            "آدم‌هایی که در محدوده کلی مشابه تو هستند "
            "و دنبال موسیقی می‌گردند.\n\n"
            "موقعیت دقیق نمایش داده نمی‌شه.",
        ),
        "artist": (
            "🎼",
            "با طرفدارهای این خواننده",
            "اسم خواننده رو انتخاب کن تا وارد فضای "
            "مخصوص طرفدارهای اون هنرمند بشی.",
        ),
        "album": (
            "💿",
            "با طرفدارهای این آلبوم",
            "یک آلبوم رو انتخاب کن و با طرفدارهای "
            "همون آلبوم موسیقی گوش بده.",
        ),
        "send_song": (
            "🎵",
            "آهنگ بفرسید",
            "آهنگی که دوست داری رو انتخاب کن و "
            "برای یک نفر یا یک Room بفرست.",
        ),
        "friend": (
            "🧑",
            "با دوست",
            "با یک دوست وارد Music Room شو و "
            "موسیقی رو همزمان گوش کنید.",
        ),
        "random": (
            "🕵️",
            "با ناشناس",
            "FAZE می‌تونه بر اساس سلیقه موسیقی، "
            "آدم‌های مناسب برای گوش دادن مشترک پیدا کنه.",
        ),
        "group": (
            "👥",
            "Add to Group",
            "FAZE Music رو به گروه تلگرامی اضافه کن "
            "و موسیقی رو گروهی تجربه کن.",
        ),
    }

    icon, title, description = feature_data.get(
        feature,
        (
            "🎧",
            "Music",
            "این قابلیت به‌زودی آماده می‌شه.",
        ),
    )

    text = (
        "╭────────────────────╮\n"
        f"          {icon} <b>{title}</b>\n"
        "╰────────────────────╯\n\n"
        f"{description}\n\n"
        "این بخش فعلاً در حال توسعه است. ✦"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            )
        ],
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


# =========================================================
# CREATE ACTIVE ROOM
# =========================================================

async def music_create_room(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user

    if not user:
        return

    genre = context.user_data.get(
        "music_genre",
        "all",
    )

    if genre not in GENRES:
        genre = "all"

    room_id = None
    room = None

    for _ in range(5):
        candidate = generate_room_code()
        invite_token = secrets.token_urlsafe(18)

        try:
            room = await create_active_music_room(
                creator_id=user.id,
                room_id=candidate,
                invite_token=invite_token,
                genre=genre,
            )

            if room:
                room_id = candidate
                break

        except Exception:
            continue

    if not room or not room_id:
        text = (
            "❌ <b>ساخت Room انجام نشد.</b>\n\n"
            "لطفاً دوباره تلاش کن."
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 تلاش دوباره",
                    callback_data="music:create",
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="together:music",
                )
            ],
        ])

        if query:
            try:
                await query.edit_message_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception:
                pass

        elif update.message:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        return

    icon = genre_icon(genre)
    title = genre_title(genre)

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>Room ساخته شد!</b>\n"
        "╰────────────────────╯\n\n"
        "Room شما همین الان <b>فعال</b> شد. 🟢\n\n"
        f"{icon} <b>سبک:</b> {title}\n\n"
        f"🔑 <b>کد Room:</b>\n"
        f"<code>{escape(str(room['room_id']))}</code>\n\n"
        "کد بالا رو برای دوستت بفرست تا بتونه "
        "با گزینه «🚪 ورود به Room» وارد بشه.\n\n"
        "👥 ظرفیت: <b>۲ نفر</b>\n"
        "🟢 وضعیت: <b>فعال</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 ورود به Room",
                callback_data=f"musicroom:enter:{room['room_id']}",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ بستن Room",
                callback_data=f"musicroom:cancel:{room['room_id']}",
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ Music",
                callback_data="together:music",
            ),
        ],
    ])

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


# =========================================================
# JOIN ROOM - START
# =========================================================

async def music_join_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["music_joining_room"] = True

    text = (
        "╭────────────────────╮\n"
        "          🚪 <b>ورود به Room</b>\n"
        "╰────────────────────╯\n\n"
        "کد ۶ کاراکتری Room رو بفرست.\n\n"
        "مثال:\n"
        "<code>7K4P9X</code>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ لغو",
                callback_data="music:join:cancel",
            ),
        ],
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass

    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    return "MUSIC_ROOM_CODE"


# =========================================================
# JOIN ROOM - RECEIVE CODE
# =========================================================

async def music_join_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not user or not update.message:
        return "MUSIC_ROOM_CODE"

    raw_code = (
        update.message.text or ""
    ).strip()

    room_code = raw_code.upper()

    if len(room_code) != ROOM_CODE_LENGTH:
        await update.message.reply_text(
            "❌ کد Room باید دقیقاً ۶ کاراکتر باشه.\n\n"
            "مثال: <code>7K4P9X</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="music:join:cancel",
                    )
                ]
            ]),
        )

        return "MUSIC_ROOM_CODE"

    if any(
        char not in ROOM_CODE_ALPHABET
        for char in room_code
    ):
        await update.message.reply_text(
            "❌ کد Room معتبر نیست.\n\n"
            "کد رو دقیقاً مثل چیزی که سازنده فرستاده وارد کن.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="music:join:cancel",
                    )
                ]
            ]),
        )

        return "MUSIC_ROOM_CODE"

    room = await get_music_room(
        room_id=room_code
    )

    if not room:
        await update.message.reply_text(
            "❌ <b>چنین Roomی وجود نداره.</b>\n\n"
            "کد رو بررسی کن و دوباره بفرست.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ لغو",
                        callback_data="music:join:cancel",
                    )
                ]
            ]),
        )

        return "MUSIC_ROOM_CODE"

    if room["status"] != "active":
        await update.message.reply_text(
            "⚠️ <b>این Room فعال نیست.</b>\n\n"
            "ممکنه Room بسته یا لغو شده باشه.",
            parse_mode=ParseMode.HTML,
            reply_markup=music_back_keyboard(),
        )

        context.user_data.pop(
            "music_joining_room",
            None,
        )

        return None

    if room["creator_id"] == user.id:
        context.user_data.pop(
            "music_joining_room",
            None,
        )

        await update.message.reply_text(
            "🎧 <b>این Room خودته.</b>\n\n"
            f"🔑 کد: <code>{escape(str(room['room_id']))}</code>\n"
            "🟢 وضعیت: فعال",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🚀 ورود به Room",
                        callback_data=f"musicroom:enter:{room['room_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ بستن Room",
                        callback_data=f"musicroom:cancel:{room['room_id']}",
                    )
                ],
            ]),
        )

        return None

    if room["guest_id"] == user.id:
        context.user_data.pop(
            "music_joining_room",
            None,
        )

        await update.message.reply_text(
            "🎧 <b>قبلاً وارد این Room شدی.</b>\n\n"
            "می‌تونی دوباره وارد Music Room بشی.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🚀 ورود به Room",
                        callback_data=f"musicroom:enter:{room['room_id']}",
                    )
                ]
            ]),
        )

        return None

    if room["guest_id"] is not None:
        context.user_data.pop(
            "music_joining_room",
            None,
        )

        await update.message.reply_text(
            "⚠️ <b>ظرفیت Room تکمیل شده.</b>\n\n"
            "این Room الان ۲ نفر داره.",
            parse_mode=ParseMode.HTML,
            reply_markup=music_back_keyboard(),
        )

        return None

    joined_room = await join_active_music_room(
        room_id=room["room_id"],
        guest_id=user.id,
    )

    if not joined_room:
        context.user_data.pop(
            "music_joining_room",
            None,
        )

        await update.message.reply_text(
            "⚠️ <b>ورود انجام نشد.</b>\n\n"
            "احتمالاً شخص دیگری زودتر وارد Room شده.",
            parse_mode=ParseMode.HTML,
            reply_markup=music_back_keyboard(),
        )

        return None

    room = joined_room

    context.user_data.pop(
        "music_joining_room",
        None,
    )

    await update.message.reply_text(
        "╭────────────────────╮\n"
        "          🎧 <b>Room پیدا شد!</b>\n"
        "╰────────────────────╯\n\n"
        "🟢 وضعیت: <b>فعال</b>\n"
        "👥 ظرفیت: <b>۲ نفر</b>\n\n"
        "تو وارد Room شدی. 🔥\n"
        "حالا می‌تونی وارد Music Room بشی.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚀 ورود به Room",
                    callback_data=f"musicroom:enter:{room['room_id']}",
                )
            ]
        ]),
    )

    safe_first_name = escape(
        user.first_name or "یک کاربر"
    )

    try:
        await context.bot.send_message(
            chat_id=room["creator_id"],
            text=(
                "╭────────────────────╮\n"
                "          🎧 <b>یک نفر وارد Room شد!</b>\n"
                "╰────────────────────╯\n\n"
                f"👤 <b>{safe_first_name}</b> "
                "وارد Room تو شد. 🎉\n\n"
                f"🔑 کد Room: <code>{escape(str(room['room_id']))}</code>\n"
                "👥 وضعیت: <b>۲ / ۲</b>\n\n"
                "هر دوتون می‌تونید وارد Music Room بشید."
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🚀 ورود به Room",
                        callback_data=f"musicroom:enter:{room['room_id']}",
                    )
                ]
            ]),
        )

    except Exception:
        pass

    return None


# =========================================================
# JOIN ROOM - CANCEL
# =========================================================

async def music_join_cancel(
    update,
    context,
):
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data.pop(
        "music_joining_room",
        None,
    )

    text = (
        "🎧 <b>Music Room</b>\n\n"
        "ورود به Room لغو شد."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ برگشت",
                callback_data="together:music",
            )
        ]
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass

    return None


# =========================================================
# ENTER ROOM
# =========================================================

async def music_enter_room(
    update,
    context,
    room_id: str,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    room = await get_music_room(
        room_id=room_id
    )

    if not room:
        await query.answer(
            "❌ Room پیدا نشد.",
            show_alert=True,
        )
        return

    if room["status"] != "active":
        await query.answer(
            "⚠️ این Room فعال نیست.",
            show_alert=True,
        )
        return

    if user.id not in (
        room["creator_id"],
        room["guest_id"],
    ):
        await query.answer(
            "❌ شما عضو این Room نیستید.",
            show_alert=True,
        )
        return

    url = music_room_url(
        room["room_id"],
        room["invite_token"],
    )

    if not url:
        await query.answer(
            "⚠️ Mini App تنظیم نشده.",
            show_alert=True,
        )
        return

    await query.answer(
        "🚀 ورود به Music Room"
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🎧 <b>FAZE MUSIC</b>\n\n"
                "Room آماده‌ست. 🔥\n\n"
                f"🔑 کد: <code>{escape(str(room['room_id']))}</code>\n"
                "👥 ظرفیت: <b>۲ نفر</b>"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=music_webapp_keyboard(room),
        )

    except Exception:
        try:
            if query.message:
                await query.message.reply_text(
                    "🎧 Room آماده‌ست.",
                    reply_markup=music_webapp_keyboard(room),
                )
        except Exception:
            pass


# =========================================================
# MUSIC MODE MENU - LEGACY FLOW
# =========================================================

def music_mode_menu(genre: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎧 با دوست",
                callback_data=f"musicmode:friend:{genre}",
            )
        ],
        [
            InlineKeyboardButton(
                "👥 اد تو گروه",
                callback_data=f"musicmode:group:{genre}",
            )
        ],
        [
            InlineKeyboardButton(
                "👤 با ناشناس",
                callback_data=f"musicmode:random:{genre}",
            )
        ],
        [
            InlineKeyboardButton(
                "➕ ساخت Room",
                callback_data="music:create",
            ),
            InlineKeyboardButton(
                "🚪 ورود به Room",
                callback_data="music:join",
            ),
        ],
        [
            InlineKeyboardButton(
                "‹ انتخاب سبک",
                callback_data="together:music",
            ),
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            ),
        ],
    ])


# =========================================================
# SELECT MUSIC MODE
# =========================================================

async def music_mode(
    update,
    context,
    genre: str,
    title: str,
    icon: str,
):
    query = update.callback_query

    if query:
        await query.answer()

    context.user_data["music_genre"] = genre

    text = (
        "╭────────────────────╮\n"
        f"          {icon} <b>{title}</b>\n"
        "╰────────────────────╯\n\n"
        "حالا انتخاب کن چطور می‌خوای گوش بدی:\n\n"
        "🎧 <b>با دوست</b>\n"
        "با یک دوست وارد اتاق موسیقی شو.\n\n"
        "👥 <b>اد تو گروه</b>\n"
        "اتاق موسیقی رو داخل گروه باز کن.\n\n"
        "👤 <b>با ناشناس</b>\n"
        "با یک نفر تصادفی که سلیقه مشابهی داره گوش بده.\n\n"
        "➕ <b>ساخت Room</b>\n"
        "یک Room فعال بساز و کدش رو برای دوستت بفرست.\n\n"
        "🚪 <b>ورود به Room</b>\n"
        "با کد وارد یک Room فعال شو."
    )

    keyboard = music_mode_menu(genre)

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


# =========================================================
# GENRE HANDLERS
# =========================================================

async def music_rap(update, context):
    await music_mode(
        update,
        context,
        "rap",
        "رپ",
        "🎤",
    )


async def music_pop(update, context):
    await music_mode(
        update,
        context,
        "pop",
        "پاپ",
        "🎵",
    )


async def music_metal(update, context):
    await music_mode(
        update,
        context,
        "metal",
        "متال",
        "🤘",
    )


async def music_rock(update, context):
    await music_mode(
        update,
        context,
        "rock",
        "راک",
        "🎸",
    )


async def music_traditional(update, context):
    await music_mode(
        update,
        context,
        "traditional",
        "سنتی",
        "🪕",
    )


# =========================================================
# FRIEND ROOM - OLD FLOW
# =========================================================

async def music_with_friend(update, context):
    query = update.callback_query

    if query:
        await query.answer()

    user = update.effective_user

    if not user:
        return

    genre = context.user_data.get(
        "music_genre",
        "rap",
    )

    if genre not in GENRES:
        genre = "rap"

    room_id = secrets.token_urlsafe(9)
    invite_token = secrets.token_urlsafe(18)

    await create_music_room(
        creator_id=user.id,
        genre=genre,
        room_id=room_id,
        invite_token=invite_token,
        mode="friend",
    )

    bot_username = get_bot_username(context)

    if not bot_username:
        me = await context.bot.get_me()
        bot_username = me.username

        if bot_username:
            context.bot_data["bot_username"] = bot_username

    if not bot_username:
        if query:
            await query.answer(
                "⚠️ نام کاربری Bot پیدا نشد.",
                show_alert=True,
            )
        return

    invite_link = (
        f"https://t.me/{bot_username}"
        f"?start=music_{invite_token}"
    )

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>FAZE MUSIC</b>\n"
        "╰────────────────────╯\n\n"
        "اتاق موسیقی ساخته شد. ✦\n\n"
        f"🎵 <b>سبک:</b> {genre_title(genre)}\n"
        "👥 <b>حالت:</b> با دوست\n\n"
        "حالا دوستت رو انتخاب کن و دعوت رو داخل "
        "همون چت براش بفرست.\n\n"
        "بعد از ارسال، دوستت می‌تونه مستقیماً "
        "از داخل همون پیام قبول یا رد کنه."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📨 انتخاب دوست و ارسال دعوت",
                switch_inline_query=f"music_{invite_token}",
            )
        ],
        [
            InlineKeyboardButton(
                "✕ لغو اتاق",
                callback_data=f"musicroom:cancel:{room_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "‹  بازگشت ",
                callback_data="together:music",
            ),
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            ),
        ],
    ])

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


# =========================================================
# INLINE MODE
# =========================================================

async def music_inline_query(update, context):
    inline_query = update.inline_query

    if not inline_query:
        return

    raw_query = (
        inline_query.query or ""
    ).strip()

    prefix = "music_"

    if not raw_query.startswith(prefix):
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    token = raw_query[
        len(prefix):
    ].strip()

    if not token:
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    room = await get_music_room(
        invite_token=token
    )

    if not room:
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    if room["creator_id"] != inline_query.from_user.id:
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    if room["status"] != "waiting":
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    bot_username = get_bot_username(context)

    if not bot_username:
        me = await context.bot.get_me()
        bot_username = me.username

        if bot_username:
            context.bot_data["bot_username"] = bot_username

    if not bot_username:
        await inline_query.answer(
            [],
            cache_time=0,
            is_personal=True,
        )
        return

    creator_name = (
        inline_query.from_user.first_name
        or inline_query.from_user.username
        or "دوستت"
    )

    creator_name = escape(
        creator_name
    )

    invite_link = (
        f"https://t.me/{bot_username}"
        f"?start=music_{room['invite_token']}"
    )

    genre_name = genre_title(
        room["genre"]
    )

    genre_emoji = genre_icon(
        room["genre"]
    )

    message_text = (
        "╭────────────────────╮\n"
        "          🎧 <b>دعوت به Music Room</b>\n"
        "╰────────────────────╯\n\n"
        f"👤 <b>{creator_name}</b> تو رو به یه اتاق موسیقی دعوت کرده.\n\n"
        f"{genre_emoji} <b>سبک:</b> {genre_name}\n"
        "🎶 <b>حالت:</b> با دوست\n\n"
        "اگه می‌خوای باهاش آهنگ گوش بدی، دعوت رو قبول کن.\n\n"
        f"🔗 <a href=\"{invite_link}\">لینک دعوت</a>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول دعوت",
                callback_data=f"musicinvite:accept:{room['room_id']}",
            ),
            InlineKeyboardButton(
                "❌ رد دعوت",
                callback_data=f"musicinvite:reject:{room['room_id']}",
            ),
        ],
    ])

    result = InlineQueryResultArticle(
        id=f"musicinvite_{room['room_id']}",
        title="🎧 دعوت به Music Room",
        description=f"{genre_emoji} {genre_name} • دعوت دوست",
        input_message_content=InputTextMessageContent(
            message_text=message_text,
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=keyboard,
    )

    await inline_query.answer(
        [result],
        cache_time=0,
        is_personal=True,
    )


# =========================================================
# GROUP MUSIC
# =========================================================

async def music_in_group(update, context):
    query = update.callback_query

    if query:
        await query.answer()

    genre = context.user_data.get(
        "music_genre",
        "rap",
    )

    if genre not in GENRES:
        genre = "rap"

    from src.group_music.handlers import (
        show_group_music_entry,
    )

    await show_group_music_entry(
        update,
        context,
        genre,
    )


# =========================================================
# RANDOM
# =========================================================

async def music_with_random(update, context):
    query = update.callback_query

    if query:
        await query.answer()

    genre = context.user_data.get(
        "music_genre",
        "rap",
    )

    if genre not in GENRES:
        genre = "rap"

    text = (
        "╭────────────────────╮\n"
        "          👤 <b>با ناشناس</b>\n"
        "╰────────────────────╯\n\n"
        f"🎵 سبک انتخابی: <b>{genre_title(genre)}</b>\n\n"
        "سیستم Match موسیقی ناشناس مرحله بعدی FAZE Music هست. ✦"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "‹ انتخاب روش",
                callback_data=f"music:{genre}",
            )
        ],
        [
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            )
        ],
    ])

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


# =========================================================
# INVITATION KEYBOARD
# =========================================================

def music_invitation_keyboard(room_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول دعوت",
                callback_data=f"musicinvite:accept:{room_id}",
            ),
            InlineKeyboardButton(
                "❌ رد دعوت",
                callback_data=f"musicinvite:reject:{room_id}",
            ),
        ],
    ])


# =========================================================
# SHOW INVITATION
# =========================================================

async def show_music_invitation(
    update,
    context,
    room,
):
    creator_id = room["creator_id"]

    try:
        creator = await context.bot.get_chat(
            creator_id
        )

        creator_name = (
            creator.first_name
            or creator.username
            or "یک کاربر"
        )

    except Exception:
        creator_name = "یک کاربر"

    creator_name = escape(
        creator_name
    )

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>FAZE MUSIC</b>\n"
        "╰────────────────────╯\n\n"
        f"👤 <b>{creator_name}</b> ازت دعوت کرده\n"
        "باهاش وارد یه اتاق موسیقی بشی.\n\n"
        f"🎵 <b>سبک:</b> {genre_title(room['genre'])}\n\n"
        "اگه قبول کنی، بعد از آماده شدن هر دوتون\n"
        "وارد Music Room می‌شید."
    )

    keyboard = music_invitation_keyboard(
        room["room_id"]
    )

    query = update.callback_query

    if query:
        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass

        return

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


# =========================================================
# HANDLE MUSIC INVITE
# =========================================================

async def handle_music_invite(
    update,
    context,
    token,
):
    user = update.effective_user

    if not user or not update.message:
        return

    room = await get_music_room(
        invite_token=token
    )

    if not room:
        await update.message.reply_text(
            "❌ این دعوت معتبر نیست یا اتاق دیگر وجود ندارد."
        )
        return

    if room["status"] != "waiting":
        await update.message.reply_text(
            "⚠️ این دعوت دیگر فعال نیست."
        )
        return

    if room["creator_id"] == user.id:
        await update.message.reply_text(
            "😄 این دعوت متعلق به خودته!"
        )
        return

    try:
        creator = await context.bot.get_chat(
            room["creator_id"]
        )

        creator_name = (
            creator.first_name
            or creator.username
            or "دوستت"
        )

    except Exception:
        creator_name = "دوستت"

    creator_name = escape(
        creator_name
    )

    genre = genre_title(
        room["genre"]
    )

    text = (
        "🎧 <b>دعوت به اتاق موسیقی</b>\n\n"
        f"👤 <b>{creator_name}</b> تو رو به یک اتاق موسیقی دعوت کرده.\n\n"
        f"🎵 سبک: <b>{genre}</b>\n"
        "🎶 حالت: <b>با دوست</b>\n\n"
        "می‌خوای وارد این اتاق بشی؟"
    )

    keyboard = music_invitation_keyboard(
        room["room_id"]
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


# =========================================================
# ACCEPT INVITATION
# =========================================================

async def accept_music_invitation(
    update,
    context,
    room_id: str,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    room = await get_music_room(
        room_id
    )

    if not room:
        await query.answer(
            "این دعوت پیدا نشد.",
            show_alert=True,
        )
        return

    if room["status"] != "waiting":
        await query.answer(
            "این دعوت دیگه فعال نیست.",
            show_alert=True,
        )
        return

    if room["creator_id"] == user.id:
        await query.answer(
            "نمی‌تونی دعوت خودت رو قبول کنی.",
            show_alert=True,
        )
        return

    if room["guest_id"] is not None:
        await query.answer(
            "این اتاق قبلاً پذیرفته شده.",
            show_alert=True,
        )
        return

    from src.db.database import accept_music_room

    room = await accept_music_room(
        room_id=room_id,
        guest_id=user.id,
    )

    if not room:
        await query.answer(
            "این دعوت دیگه قابل قبول نیست.",
            show_alert=True,
        )
        return

    await query.answer(
        "دعوت قبول شد ✅"
    )

    safe_first_name = escape(
        user.first_name or "دوستت"
    )

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>دعوت پذیرفته شد</b>\n"
        "╰────────────────────╯\n\n"
        f"👤 <b>{safe_first_name}</b>\n\n"
        f"🎵 <b>سبک:</b> {genre_title(room['genre'])}\n\n"
        "وارد اتاق شدی. ✦\n"
        "حالا هر دوتون باید آماده بشید."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 من آماده‌ام",
                callback_data=f"musicready:{room_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ خروج از اتاق",
                callback_data=f"musicroom:leave:{room_id}",
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

    try:
        await context.bot.send_message(
            chat_id=room["creator_id"],
            text=(
                "╭────────────────────╮\n"
                "          🎧 <b>دعوت قبول شد!</b>\n"
                "╰────────────────────╯\n\n"
                f"👤 <b>{safe_first_name}</b> دعوتت رو قبول کرد. 🎉\n\n"
                f"🎵 <b>سبک:</b> {genre_title(room['genre'])}\n\n"
                "حالا هر دوتون روی «من آماده‌ام» بزنید."
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🚀 من آماده‌ام",
                        callback_data=f"musicready:{room_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ لغو اتاق",
                        callback_data=f"musicroom:cancel:{room_id}",
                    )
                ],
            ]),
        )
    except Exception:
        pass


# =========================================================
# REJECT INVITATION
# =========================================================

async def reject_music_invitation(
    update,
    context,
    room_id: str,
):
    query = update.callback_query

    if not query:
        return

    room = await get_music_room(
        room_id
    )

    if not room:
        await query.answer(
            "این دعوت پیدا نشد.",
            show_alert=True,
        )
        return

    user = update.effective_user

    if not user:
        return

    if room["creator_id"] == user.id:
        await query.answer(
            "این دعوت متعلق به خودته.",
            show_alert=True,
        )
        return

    if room["status"] != "waiting":
        await query.answer(
            "این دعوت دیگه فعال نیست.",
            show_alert=True,
        )
        return

    from src.db.database import reject_music_room

    success = await reject_music_room(
        room_id
    )

    if not success:
        await query.answer(
            "این دعوت دیگه قابل رد کردن نیست.",
            show_alert=True,
        )
        return

    await query.answer(
        "دعوت رد شد."
    )

    try:
        await query.edit_message_text(
            "╭────────────────────╮\n"
            "          ❌ <b>دعوت رد شد</b>\n"
            "╰────────────────────╯\n\n"
            "این دعوت Music Room رد شد.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    try:
        await context.bot.send_message(
            chat_id=room["creator_id"],
            text=(
                "🎧 دعوت Music Room رد شد.\n\n"
                "دوستت دعوت رو قبول نکرد."
            ),
        )
    except Exception:
        pass


# =========================================================
# READY
# =========================================================

async def music_ready(
    update,
    context,
    room_id: str,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    room = await get_music_room(
        room_id
    )

    if not room:
        await query.answer(
            "اتاق پیدا نشد.",
            show_alert=True,
        )
        return

    if user.id not in (
        room["creator_id"],
        room["guest_id"],
    ):
        await query.answer(
            "این اتاق برای شما نیست.",
            show_alert=True,
        )
        return

    if room["status"] != "accepted":
        await query.answer(
            "اتاق هنوز آماده نیست.",
            show_alert=True,
        )
        return

    room = await set_music_ready(
        room_id,
        user.id,
    )

    if not room:
        await query.answer(
            "وضعیت آماده‌بودن ثبت نشد.",
            show_alert=True,
        )
        return

    await query.answer(
        "آماده شدی 🚀"
    )

    creator_ready = bool(
        room["creator_ready"]
    )

    guest_ready = bool(
        room["guest_ready"]
    )

    if creator_ready and guest_ready:

        room = await activate_music_room(
            room_id
        )

        if not room:
            return

        await send_music_room_access(
            context,
            room,
        )

        try:
            await query.edit_message_text(
                "╭────────────────────╮\n"
                "          🚀 <b>Music Room آماده‌ست</b>\n"
                "╰────────────────────╯\n\n"
                "هر دوتون آماده‌اید! 🔥\n\n"
                "پیام ورود به Music Room برات ارسال شد.",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass

        return

    text = (
        "╭────────────────────╮\n"
        "          🎧 <b>آماده شدی</b>\n"
        "╰────────────────────╯\n\n"
        "تو آماده‌ای ✅\n\n"
        "⏳ منتظریم نفر دوم هم آماده بشه.\n\n"
        "به محض اینکه هر دوتون آماده باشید، "
        "Music Room فعال میشه."
    )

    try:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ خروج از اتاق",
                        callback_data=f"musicroom:leave:{room_id}",
                    )
                ]
            ]),
        )
    except Exception:
        pass

    other_user = (
        room["guest_id"]
        if user.id == room["creator_id"]
        else room["creator_id"]
    )

    if other_user:
        try:
            await context.bot.send_message(
                chat_id=other_user,
                text=(
                    "🎧 دوستت آماده شد!\n\n"
                    "حالا تو هم روی «🚀 من آماده‌ام» بزن "
                    "تا Music Room باز بشه."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🚀 من آماده‌ام",
                            callback_data=f"musicready:{room_id}",
                        )
                    ]
                ]),
            )
        except Exception:
            pass


# =========================================================
# WEB APP BUTTON
# =========================================================

def music_webapp_keyboard(room):
    url = music_room_url(
        room["room_id"],
        room["invite_token"],
    )

    if not url:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚠️ Mini App تنظیم نشده",
                    callback_data="musicroom:no_webapp",
                )
            ]
        ])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 ورود به Music Room",
                web_app=WebAppInfo(url=url),
            )
        ]
    ])


# =========================================================
# SEND ROOM ACCESS
# =========================================================

async def send_music_room_access(
    context,
    room,
):
    keyboard = music_webapp_keyboard(
        room
    )

    text = (
        "🎧 <b>FAZE MUSIC</b>\n\n"
        "اتاق موسیقی شما آماده‌ست. 🔥\n\n"
        "هر دو نفر می‌تونید وارد Music Room بشید."
    )

    sent_users = set()

    for user_id in (
        room["creator_id"],
        room["guest_id"],
    ):
        if not user_id:
            continue

        if user_id in sent_users:
            continue

        sent_users.add(user_id)

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            pass


# =========================================================
# CANCEL ROOM
# =========================================================

async def cancel_music_room_handler(
    update,
    context,
    room_id: str,
):
    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    room = await get_music_room(
        room_id
    )

    if not room:
        await query.answer(
            "اتاق پیدا نشد.",
            show_alert=True,
        )
        return

    if room["creator_id"] != user.id:
        await query.answer(
            "فقط سازنده اتاق می‌تونه لغوش کنه.",
            show_alert=True,
        )
        return

    success = await cancel_music_room(
        room_id,
        user.id,
    )

    if not success:
        await query.answer(
            "این Room دیگه قابل لغو نیست.",
            show_alert=True,
        )
        return

    await query.answer(
        "اتاق لغو شد."
    )

    try:
        await query.edit_message_text(
            "╭────────────────────╮\n"
            "          ✕ <b>اتاق لغو شد</b>\n"
            "╰────────────────────╯\n\n"
            "Music Room لغو شد.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    guest_id = room["guest_id"]

    if guest_id:
        try:
            await context.bot.send_message(
                chat_id=guest_id,
                text="🎧 Music Room توسط سازنده لغو شد.",
            )
        except Exception:
            pass


# =========================================================
# LEAVE ROOM
# =========================================================

async def leave_music_room(
    update,
    context,
    room_id: str,
):
    """
    Creator -> Room لغو می‌شود.
    Guest   -> فقط Guest خارج می‌شود و Room فعال می‌ماند.
    """

    query = update.callback_query

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    room = await get_music_room(
        room_id
    )

    if not room:
        await query.answer(
            "اتاق پیدا نشد.",
            show_alert=True,
        )
        return

    if user.id not in (
        room["creator_id"],
        room["guest_id"],
    ):
        await query.answer(
            "این اتاق برای شما نیست.",
            show_alert=True,
        )
        return

    is_creator = (
        user.id == room["creator_id"]
    )

    other_user = (
        room["guest_id"]
        if is_creator
        else room["creator_id"]
    )

    success = await db_leave_music_room(
        room_id=room_id,
        user_id=user.id,
    )

    if not success:
        await query.answer(
            "خروج از اتاق انجام نشد.",
            show_alert=True,
        )
        return

    await query.answer(
        "از اتاق خارج شدی."
    )

    try:
        await query.edit_message_text(
            "🎧 از Music Room خارج شدی.",
            parse_mode=ParseMode.HTML,
            reply_markup=music_back_keyboard(),
        )
    except Exception:
        pass

    if other_user:
        try:
            if is_creator:
                await context.bot.send_message(
                    chat_id=other_user,
                    text=(
                        "🎧 <b>سازنده از Music Room خارج شد.</b>\n\n"
                        "این Room بسته شد."
                    ),
                    parse_mode=ParseMode.HTML,
                )

            else:
                await context.bot.send_message(
                    chat_id=other_user,
                    text=(
                        "🎧 <b>نفر دوم از Music Room خارج شد.</b>\n\n"
                        "Room همچنان فعاله و می‌تونی "
                        "یک نفر دیگه رو وارد کنی."
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "🚀 ورود به Room",
                                callback_data=f"musicroom:enter:{room_id}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "❌ بستن Room",
                                callback_data=f"musicroom:cancel:{room_id}",
                            )
                        ],
                    ]),
                )

        except Exception:
            pass