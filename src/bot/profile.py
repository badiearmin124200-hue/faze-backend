import html
import json
import aiosqlite

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.db.database import DB_PATH


# =========================================================
# STATES
# =========================================================

NAME = 0
PHOTO = 1
AGE = 2
GENDER = 3
CITY = 4
INTERESTS_STATE = 5
BIO = 6

PERSONALITY = 7
SOCIAL_LEVEL = 8
GROUP_TYPE = 9

EDIT_MENU = 10
EDIT_NAME = 11
EDIT_PHOTO = 12
EDIT_GENDER = 13
EDIT_AGE = 14
EDIT_CITY = 15
EDIT_INTERESTS = 16
EDIT_BIO = 17

EDIT_PERSONALITY = 18
EDIT_SOCIAL_LEVEL = 19
EDIT_GROUP_TYPE = 20


AGE_PER_PAGE = 18
PROVINCES_PER_PAGE = 10


# =========================================================
# DATA
# =========================================================

PROVINCES = [
    "آذربایجان شرقی",
    "آذربایجان غربی",
    "اردبیل",
    "اصفهان",
    "البرز",
    "ایلام",
    "بوشهر",
    "تهران",
    "چهارمحال و بختیاری",
    "خراسان جنوبی",
    "خراسان رضوی",
    "خراسان شمالی",
    "خوزستان",
    "زنجان",
    "سمنان",
    "سیستان و بلوچستان",
    "فارس",
    "قزوین",
    "قم",
    "کردستان",
    "کرمان",
    "کرمانشاه",
    "کهگیلویه و بویراحمد",
    "گلستان",
    "گیلان",
    "لرستان",
    "مازندران",
    "مرکزی",
    "هرمزگان",
    "همدان",
    "یزد",
]


INTERESTS = [
    ("🎬 فیلم", "فیلم"),
    ("🎧 موسیقی", "موسیقی"),
    ("🎮 گیم", "گیم"),
    ("⚽ فوتبال", "فوتبال"),
    ("💻 کدنویسی", "کدنویسی"),
    ("🏋️ ورزش", "ورزش"),
    ("📚 درس", "درس"),
    ("📺 سریال", "سریال"),
    ("✈️ سفر", "سفر"),
    ("📖 کتاب", "کتاب"),
    ("🎨 هنر", "هنر"),
    ("🌙 شب‌بیداری", "شب‌بیداری"),
]


PERSONALITY_TYPES = {
    "introvert": "درونگرا",
    "ambivert": "بینابین",
    "extrovert": "برونگرا",
}


GROUP_TYPES = {
    "two": "دو نفره",
    "small": "جمع کوچک",
    "large": "جمع شلوغ",
    "any": "فرقی نداره",
}


# =========================================================
# HELPERS
# =========================================================

def safe_text(value, default=""):
    if value is None:
        return default

    return html.escape(str(value))


def progress_bar(current, total=10):
    current = max(0, min(current, total))
    return "●" * current + "○" * (total - current)


def profile_header(step, title, subtitle=None):
    text = (
        "✦ <b>FAZE</b>\n"
        f"<code>{progress_bar(step)}</code>\n\n"
        f"✨ <b>{safe_text(title)}</b>\n"
    )

    if subtitle:
        text += f"\n{subtitle}\n"

    return text


def nav_buttons(
    back_callback=None,
    home_callback="home",
):
    buttons = []
    row = []

    if back_callback:
        row.append(
            InlineKeyboardButton(
                "‹ برگشت",
                callback_data=back_callback,
            )
        )

    if home_callback:
        row.append(
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data=home_callback,
            )
        )

    if row:
        buttons.append(row)

    return buttons


async def answer(query):
    if not query:
        return

    try:
        await query.answer()
    except Exception:
        pass


async def render_text(
    query,
    text,
    keyboard=None,
):
    markup = (
        InlineKeyboardMarkup(keyboard)
        if keyboard
        else None
    )

    try:
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        return
    except Exception:
        pass

    try:
        await query.message.delete()
    except Exception:
        pass

    await query.message.chat.send_message(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=markup,
    )


# =========================================================
# HOME
# =========================================================

async def go_home(update, context):
    query = update.callback_query

    if query:
        await answer(query)

    try:
        from src.bot.handlers import show_home

        await show_home(
            update,
            context,
        )

    except Exception:
        if query:
            await render_text(
                query,
                (
                    "✦ <b>FAZE</b>\n\n"
                    "به صفحه اصلی برگشتی."
                ),
                [
                    [
                        InlineKeyboardButton(
                            "👤 پروفایل",
                            callback_data="profile:home",
                        )
                    ]
                ],
            )


# =========================================================
# DATABASE
# =========================================================

async def get_user(telegram_id: int):
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


async def update_user(
    telegram_id: int,
    **fields,
):
    allowed = {
        "display_name",
        "avatar_file_id",
        "age",
        "gender",
        "city",
        "interests",
        "bio",
        "personality",
        "profile_completed",
        "profile_completion",
        "current_status",
    }

    fields = {
        key: value
        for key, value in fields.items()
        if key in allowed
    }

    if not fields:
        return

    parts = []
    values = []

    for key, value in fields.items():
        parts.append(
            f"{key} = ?"
        )
        values.append(value)

    parts.append(
        "updated_at = CURRENT_TIMESTAMP"
    )

    values.append(telegram_id)

    query = f"""
        UPDATE users
        SET {", ".join(parts)}
        WHERE telegram_id = ?
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            query,
            values,
        )

        await db.commit()


# =========================================================
# PERSONALITY HELPERS
# =========================================================

def get_personality(user):
    if not user:
        return {}

    raw = user["personality"]

    if not raw:
        return {}

    try:
        data = json.loads(raw)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def personality_text(value):
    return PERSONALITY_TYPES.get(
        value,
        "مشخص نشده",
    )


def group_text(value):
    return GROUP_TYPES.get(
        value,
        "مشخص نشده",
    )


def social_text(value):
    if value is None:
        return "مشخص نشده"

    return f"{value} از ۵"


def save_personality_data(
    context,
    key,
    value,
):
    registration = context.user_data.setdefault(
        "registration",
        {},
    )

    personality = registration.setdefault(
        "personality",
        {},
    )

    personality[key] = value


# =========================================================
# PROFILE HOME
# =========================================================

async def profile_home(update, context):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    telegram_user = update.effective_user

    if not telegram_user:
        return ConversationHandler.END

    user = await get_user(
        telegram_user.id
    )

    if not user:
        await create_user(
            telegram_user
        )

        user = await get_user(
            telegram_user.id
        )

    if not user:
        await answer(query)
        return ConversationHandler.END

    # پروفایل ناقص → ورود مستقیم به ثبت‌نام
    if not user["profile_completed"]:
        return await start_registration(
            update,
            context,
        )

    await show_profile(
        update,
        context,
        user,
    )

    return ConversationHandler.END


# =========================================================
# SHOW PROFILE
# =========================================================

async def show_profile(
    update,
    context,
    user=None,
):
    query = update.callback_query

    if not query:
        return

    await answer(query)

    telegram_user = update.effective_user

    if not telegram_user:
        return

    if user is None:
        user = await get_user(
            telegram_user.id
        )

    if not user:
        await create_user(
            telegram_user
        )

        user = await get_user(
            telegram_user.id
        )

    if not user:
        return

    try:
        interests = json.loads(
            user["interests"] or "[]"
        )

        if not isinstance(
            interests,
            list,
        ):
            interests = []

    except Exception:
        interests = []

    personality = get_personality(user)

    display_name = safe_text(
        user["display_name"]
        or user["first_name"]
        or "کاربر"
    )

    gender_map = {
        "male": "پسر",
        "female": "دختر",
        "پسر": "پسر",
        "دختر": "دختر",
    }

    gender = gender_map.get(
        user["gender"],
        "مشخص نشده",
    )

    age = (
        str(user["age"])
        if user["age"]
        else "—"
    )

    province = safe_text(
        user["city"]
        or "مشخص نشده"
    )

    bio = safe_text(
        user["bio"]
        or "هنوز چیزی درباره خودش ننوشته."
    )

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>PROFILE</b>\n"
        "╰────────────────────╯\n\n"
        f"👤 <b>اسم:</b> {display_name}\n"
        f"🎂 <b>سن:</b> {age}\n"
        f"🚻 <b>جنسیت:</b> {gender}\n"
        f"📍 <b>استان:</b> {province}\n\n"
        "💫 <b>علایق من</b>\n"
    )

    if interests:
        text += "\n"

        for item in interests:
            text += (
                f"    ▫️ {safe_text(item)}\n"
            )

    else:
        text += (
            "\n"
            "<i>هنوز چیزی انتخاب نشده.</i>\n"
        )

    text += (
        "\n"
        "🧠 <b>شخصیت من</b>\n\n"
        f"   🧠 تیپ شخصیتی: "
        f"<b>{personality_text(personality.get('type'))}</b>\n"
        f"   👥 اجتماعی بودن: "
        f"<b>{social_text(personality.get('social_level'))}</b>\n"
        f"   👥 مدل جمع: "
        f"<b>{group_text(personality.get('group_type'))}</b>\n\n"
        "📝 <b>Bio</b>\n"
        f"{bio}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Level {user['level']}"
        f"   ·   ⚡ {user['xp']} XP\n"
        f"🔥 {user['streak']} روز"
        f"   ·   🪙 {user['coins']} سکه"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ ویرایش پروفایل",
                callback_data="profile:edit",
                style="primary"

            )
        ],
        [
            InlineKeyboardButton(
                "🏆 دستاوردها",
                callback_data="profile:achievements",
                                style="primary"

            ),
            InlineKeyboardButton(
                "📊 آمار",
                callback_data="profile:stats",
                                style="primary"

            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="profile:settings",
                                style="primary"

                
            )
        ],
        [
            InlineKeyboardButton(
                "‹ برگشت",
                callback_data="home",
                style="danger"

            )
        ],
    ]

    if user["avatar_file_id"]:
        try:
            try:
                await query.message.delete()
            except Exception:
                pass

            await context.bot.send_photo(
                chat_id=telegram_user.id,
                photo=user["avatar_file_id"],
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
            )

            return

        except Exception:
            pass

    await render_text(
        query,
        text,
        keyboard,
    )


# =========================================================
# REGISTRATION START
# =========================================================

async def start_registration(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await answer(query)

    context.user_data["registration"] = {}

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>FAZE</b>\n"
        "╰────────────────────╯\n\n"
        "🚀 <b>بزن بریم</b>\n\n"
        "قراره یه پروفایل بسازیم که واقعاً خودت باشه.\n\n"
        "<i>چند مرحله بیشتر نیست.</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 شروع",
                callback_data="reg:name",
            )
        ],
        [
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            )
        ],
    ]

    await render_text(
        query,
        text,
        keyboard,
    )

    return NAME


# =========================================================
# EDIT PROFILE ENTRY
# =========================================================

async def edit_profile(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await answer(query)

    return await show_edit_menu(
        query
    )


# =========================================================
# NAME
# =========================================================

async def ask_name(
    update,
    context,
):
    query = update.callback_query

    if query:
        await answer(query)

        text = profile_header(
            1,
            "اسم تو چیه؟",
            "اسم نمایشی‌ای که دوست داری بقیه توی FAZE ببینن رو بفرست.",
        )

        keyboard = nav_buttons(
            back_callback="reg:welcome",
        )

        await render_text(
            query,
            text,
            keyboard,
        )

        return NAME

    if update.message:
        name = update.message.text.strip()

        if not name:
            await update.message.reply_text(
                "اسم نمی‌تونه خالی باشه."
            )
            return NAME

        if len(name) > 40:
            await update.message.reply_text(
                "اسم خیلی طولانیه. حداکثر ۴۰ کاراکتر."
            )
            return NAME

        context.user_data.setdefault(
            "registration",
            {},
        )["name"] = name

        await update.message.reply_text(
            profile_header(
                2,
                "یه عکس هم اضافه کنیم؟",
                "عکست می‌تونه پروفایلت رو کامل‌تر و جذاب‌تر کنه.",
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📸 ارسال عکس",
                        callback_data="reg:photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "رد کردن",
                        callback_data="reg:skip_photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "‹ برگشت",
                        callback_data="reg:back_name",
                    ),
                    InlineKeyboardButton(
                        "⌂ صفحه اصلی",
                        callback_data="home",
                    ),
                ],
            ]),
        )

        return PHOTO

    return NAME


# =========================================================
# PHOTO
# =========================================================

async def photo_choice(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return PHOTO

    await answer(query)

    data = query.data

    if data == "reg:skip_photo":

        context.user_data.setdefault(
            "registration",
            {},
        )["photo"] = None

        await show_age_picker(
            query,
            page=0,
            back_callback="reg:back_photo",
        )

        return AGE

    if data == "reg:photo":

        await render_text(
            query,
            profile_header(
                2,
                "عکست رو بفرست 📸",
                "یک عکس از خودت ارسال کن.",
            ),
            nav_buttons(
                back_callback="reg:back_photo",
            ),
        )

        return PHOTO

    if data == "reg:back_photo":

        context.user_data.setdefault(
            "registration",
            {},
        ).pop(
            "name",
            None,
        )

        await render_text(
            query,
            profile_header(
                1,
                "اسم تو چیه؟",
                "اسم نمایشی‌ای که دوست داری بقیه ببینن رو بفرست.",
            ),
            nav_buttons(
                back_callback="reg:welcome",
            ),
        )

        return NAME

    return PHOTO


async def receive_photo(
    update,
    context,
):
    if not update.message:
        return PHOTO

    if not update.message.photo:
        return PHOTO

    photo = update.message.photo[-1]

    context.user_data.setdefault(
        "registration",
        {},
    )["photo"] = photo.file_id

    await update.message.reply_text(
        profile_header(
            2,
            "عکس ثبت شد ✓",
            "حالا بریم سراغ سن.",
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "ادامه →",
                    callback_data="reg:continue_age",
                )
            ],
            [
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                )
            ],
        ]),
    )

    return AGE


# =========================================================
# AGE
# =========================================================

async def show_age_picker(
    query,
    page=0,
    back_callback="reg:back_photo",
    edit_mode=False,
):
    start = 13 + (
        page * AGE_PER_PAGE
    )

    end = min(
        start + AGE_PER_PAGE,
        91,
    )

    keyboard = []
    row = []

    for age in range(
        start,
        end,
    ):
        callback = (
            f"edit:age:{age}"
            if edit_mode
            else f"reg:age:{age}"
        )

        row.append(
            InlineKeyboardButton(
                str(age),
                callback_data=callback,
            )
        )

        if len(row) == 6:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "‹",
                callback_data=(
                    f"edit:age_page:{page - 1}"
                    if edit_mode
                    else f"reg:age_page:{page - 1}"
                ),
            )
        )

    if end < 91:
        navigation.append(
            InlineKeyboardButton(
                "›",
                callback_data=(
                    f"edit:age_page:{page + 1}"
                    if edit_mode
                    else f"reg:age_page:{page + 1}"
                ),
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append(
        nav_buttons(
            back_callback=back_callback,
        )[0]
    )

    text = profile_header(
        3,
        "چند سالته؟",
        "سن واقعی خودت رو انتخاب کن.",
    )

    if edit_mode:
        text = (
            "✦ <b>تغییر سن</b>\n\n"
            "سن جدیدت رو انتخاب کن."
        )

    await render_text(
        query,
        text,
        keyboard,
    )


async def age_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return AGE

    await answer(query)

    data = query.data

    if data == "reg:continue_age":

        await show_age_picker(
            query,
            page=0,
            back_callback="reg:back_photo",
        )

        return AGE

    if data.startswith(
        "reg:age_page:"
    ):
        page = int(
            data.split(":")[-1]
        )

        await show_age_picker(
            query,
            page=page,
            back_callback="reg:back_photo",
        )

        return AGE

    if data.startswith("reg:age:"):

        age = int(
            data.split(":")[-1]
        )

        context.user_data.setdefault(
            "registration",
            {},
        )["age"] = age

        await show_gender_picker(
            query,
            registration=True,
        )

        return GENDER

    if data == "reg:back_photo":

        await render_text(
            query,
            profile_header(
                2,
                "یه عکس هم اضافه کنیم؟",
                "عکست می‌تونه پروفایلت رو کامل‌تر کنه.",
            ),
            [
                [
                    InlineKeyboardButton(
                        "📸 ارسال عکس",
                        callback_data="reg:photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "رد کردن",
                        callback_data="reg:skip_photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "‹ برگشت",
                        callback_data="reg:back_name",
                    ),
                    InlineKeyboardButton(
                        "⌂ صفحه اصلی",
                        callback_data="home",
                    ),
                ],
            ],
        )

        return PHOTO

    return AGE


# =========================================================
# GENDER
# =========================================================

async def show_gender_picker(
    query,
    registration=True,
):
    if registration:
        title = "جنسیتت چیه؟"
        subtitle = "یکی از گزینه‌ها رو انتخاب کن."
    else:
        title = "جنسیت"
        subtitle = "جنسیت جدیدت رو انتخاب کن."

    text = profile_header(
        4,
        title,
        subtitle,
    )

    if not registration:
        text = (
            "✦ <b>تغییر جنسیت</b>\n\n"
            "جنسیت جدیدت رو انتخاب کن."
        )

    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👦 پسر",
                callback_data=(
                    f"{prefix}:gender:male"
                ),
            ),
            InlineKeyboardButton(
                "👧 دختر",
                callback_data=(
                    f"{prefix}:gender:female"
                ),
            ),
        ]
    ]

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_age",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

    await render_text(
        query,
        text,
        keyboard,
    )


async def gender_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return GENDER

    await answer(query)

    data = query.data

    if data == "reg:back_age":

        await show_age_picker(
            query,
            page=0,
            back_callback="reg:back_photo",
        )

        return AGE

    if data == "reg:gender:male":
        gender = "male"

    elif data == "reg:gender:female":
        gender = "female"

    else:
        return GENDER

    context.user_data.setdefault(
        "registration",
        {},
    )["gender"] = gender

    await show_province_picker(
        query,
        page=0,
        registration=True,
    )

    return CITY


# =========================================================
# PROVINCE
# =========================================================

async def show_province_picker(
    query,
    page=0,
    registration=True,
):
    start = page * PROVINCES_PER_PAGE

    end = min(
        start + PROVINCES_PER_PAGE,
        len(PROVINCES),
    )

    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = []

    for index in range(
        start,
        end,
        2,
    ):
        row = []

        for province_index in range(
            index,
            min(index + 2, end),
        ):
            province = PROVINCES[
                province_index
            ]

            row.append(
                InlineKeyboardButton(
                    province,
                    callback_data=(
                        f"{prefix}:city:{province_index}"
                    ),
                )
            )

        keyboard.append(row)

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "‹",
                callback_data=(
                    f"{prefix}:city_page:{page - 1}"
                ),
            )
        )

    if end < len(PROVINCES):
        navigation.append(
            InlineKeyboardButton(
                "›",
                callback_data=(
                    f"{prefix}:city_page:{page + 1}"
                ),
            )
        )

    if navigation:
        keyboard.append(navigation)

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_gender",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

        text = profile_header(
            5,
            "استانت کجاست؟",
            "استان محل زندگی‌ات رو انتخاب کن.",
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

        text = (
            "✦ <b>تغییر استان</b>\n\n"
            "استان جدیدت رو انتخاب کن."
        )

    await render_text(
        query,
        text,
        keyboard,
    )


async def city_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return CITY

    await answer(query)

    data = query.data

    if data == "reg:back_gender":

        await show_gender_picker(
            query,
            registration=True,
        )

        return GENDER

    if data.startswith(
        "reg:city_page:"
    ):
        page = int(
            data.split(":")[-1]
        )

        await show_province_picker(
            query,
            page=page,
            registration=True,
        )

        return CITY

    if data.startswith(
        "reg:city:"
    ):
        index = int(
            data.split(":")[-1]
        )

        if (
            index < 0
            or index >= len(PROVINCES)
        ):
            return CITY

        province = PROVINCES[
            index
        ]

        registration = (
            context.user_data.setdefault(
                "registration",
                {},
            )
        )

        registration["city"] = province
        registration["interests"] = []

        await show_interest_picker(
            query,
            selected=[],
            registration=True,
        )

        return INTERESTS_STATE

    return CITY


# =========================================================
# INTERESTS
# =========================================================

def interests_keyboard(
    selected,
    registration=True,
):
    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = []

    for index in range(
        0,
        len(INTERESTS),
        2,
    ):
        row = []

        for i in range(
            index,
            min(index + 2, len(INTERESTS)),
        ):
            label, value = INTERESTS[i]

            if value in selected:
                label = f"✓ {label}"

            row.append(
                InlineKeyboardButton(
                    label,
                    callback_data=(
                        f"{prefix}:interest:{i}"
                    ),
                )
            )

        keyboard.append(row)

    keyboard.append(
        [
            InlineKeyboardButton(
                f"✓ ادامه ({len(selected)}/8)",
                callback_data=(
                    f"{prefix}:interests_done"
                ),
            )
        ]
    )

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_city",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

    return keyboard


async def show_interest_picker(
    query,
    selected=None,
    registration=True,
):
    selected = selected or []

    if registration:
        text = profile_header(
            6,
            "چه چیزایی دوست داری؟",
            "حداقل ۳ مورد و حداکثر ۸ مورد انتخاب کن.",
        )

    else:
        text = (
            "✦ <b>ویرایش علایق</b>\n\n"
            "علایقت رو انتخاب کن.\n"
            f"انتخاب شده: <b>{len(selected)}</b> مورد"
        )

    await render_text(
        query,
        text,
        interests_keyboard(
            selected,
            registration,
        ),
    )


async def interests_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return INTERESTS_STATE

    await answer(query)

    data = query.data

    registration = data.startswith(
        "reg:"
    )

    if registration:
        storage = (
            context.user_data
            .setdefault(
                "registration",
                {},
            )
            .setdefault(
                "interests",
                [],
            )
        )

    else:
        storage = (
            context.user_data
            .setdefault(
                "edit",
                {},
            )
            .setdefault(
                "interests",
                [],
            )
        )

    if data == "reg:back_city":

        await show_province_picker(
            query,
            page=0,
            registration=True,
        )

        return CITY

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if ":interest:" in data:

        index = int(
            data.split(":")[-1]
        )

        if (
            index < 0
            or index >= len(INTERESTS)
        ):
            return (
                INTERESTS_STATE
                if registration
                else EDIT_INTERESTS
            )

        value = INTERESTS[
            index
        ][1]

        if value in storage:
            storage.remove(value)

        else:
            if len(storage) >= 8:

                await query.answer(
                    "حداکثر ۸ علاقه می‌تونی انتخاب کنی.",
                    show_alert=True,
                )

                return (
                    INTERESTS_STATE
                    if registration
                    else EDIT_INTERESTS
                )

            storage.append(value)

        await show_interest_picker(
            query,
            selected=storage,
            registration=registration,
        )

        return (
            INTERESTS_STATE
            if registration
            else EDIT_INTERESTS
        )

    if data == "reg:interests_done":

        if len(storage) < 3:

            await query.answer(
                "حداقل ۳ مورد انتخاب کن.",
                show_alert=True,
            )

            return INTERESTS_STATE

        await ask_bio(
            query,
            registration=True,
        )

        return BIO

    if data == "edit:interests_done":

        if len(storage) < 3:

            await query.answer(
                "حداقل ۳ مورد انتخاب کن.",
                show_alert=True,
            )

            return EDIT_INTERESTS

        await save_edited_interests(
            query,
            context,
        )

        return EDIT_MENU

    return (
        INTERESTS_STATE
        if registration
        else EDIT_INTERESTS
    )


# =========================================================
# BIO
# =========================================================

async def ask_bio(
    query,
    registration=True,
):
    if registration:

        text = profile_header(
            7,
            "یه Bio کوتاه بنویس",
            "اختیاریه؛ می‌تونی درباره خودت، علایقت یا حال و هوات بنویسی.",
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "رد کردن",
                    callback_data="reg:skip_bio",
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_interests",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ],
        ]

    else:
        text = (
            "✦ <b>ویرایش Bio</b>\n\n"
            "Bio جدیدت رو بفرست."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "پاک کردن Bio",
                    callback_data="edit:bio_clear",
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ],
        ]

    await render_text(
        query,
        text,
        keyboard,
    )


async def bio_handler(
    update,
    context,
):
    query = update.callback_query

    if query:

        await answer(query)

        data = query.data

        if data == "reg:skip_bio":

            context.user_data.setdefault(
                "registration",
                {},
            )["bio"] = ""

            await ask_personality(
                query,
                context,
            )

            return PERSONALITY

        if data == "reg:back_interests":

            selected = (
                context.user_data
                .get(
                    "registration",
                    {},
                )
                .get(
                    "interests",
                    [],
                )
            )

            await show_interest_picker(
                query,
                selected=selected,
                registration=True,
            )

            return INTERESTS_STATE

        if data == "edit:bio_clear":

            await update_user(
                update.effective_user.id,
                bio="",
            )

            await query.answer(
                "Bio پاک شد ✓",
                show_alert=False,
            )

            await show_edit_menu(
                query
            )

            return EDIT_MENU

        return BIO

    if update.message:

        bio = (
            update.message.text.strip()
        )

        if len(bio) > 500:

            await update.message.reply_text(
                "Bio خیلی طولانیه. حداکثر ۵۰۰ کاراکتر."
            )

            return BIO

        context.user_data.setdefault(
            "registration",
            {},
        )["bio"] = bio

        await update.message.reply_text(
            "✓ Bio ثبت شد.\n\n"
            "حالا بریم سراغ چند سؤال کوتاه درباره خودت..."
        )

        await update.message.reply_text(
            profile_header(
                8,
                "خودت رو بیشتر کدوم می‌دونی؟ 🧠",
                "این جواب کمک می‌کنه آدم‌های مناسب‌تری رو توی FAZE پیدا کنی.",
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                personality_keyboard(
                    registration=True,
                )
            ),
        )

        return PERSONALITY

    return BIO


# =========================================================
# PERSONALITY
# =========================================================

def personality_keyboard(
    registration=True,
):
    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🧘 درونگرا",
                callback_data=(
                    f"{prefix}:personality:introvert"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                "⚖️ بین این دوتا",
                callback_data=(
                    f"{prefix}:personality:ambivert"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ برونگرا",
                callback_data=(
                    f"{prefix}:personality:extrovert"
                ),
            ),
        ],
    ]

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_bio",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

    return keyboard


async def ask_personality(
    query,
    context,
):
    text = profile_header(
        8,
        "خودت رو بیشتر کدوم می‌دونی؟ 🧠",
        "این جواب کمک می‌کنه FAZE بهتر سلیقه و شخصیتت رو بشناسه.",
    )

    await render_text(
        query,
        text,
        personality_keyboard(
            registration=True,
        ),
    )


async def personality_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return PERSONALITY

    await answer(query)

    data = query.data

    if data == "reg:back_bio":

        await ask_bio(
            query,
            registration=True,
        )

        return BIO

    value = data.split(":")[-1]

    if value not in PERSONALITY_TYPES:
        return PERSONALITY

    save_personality_data(
        context,
        "type",
        value,
    )

    await show_social_level(
        query,
        registration=True,
    )

    return SOCIAL_LEVEL


# =========================================================
# SOCIAL LEVEL
# =========================================================

def social_level_keyboard(
    registration=True,
):
    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "1",
                callback_data=(
                    f"{prefix}:social:1"
                ),
            ),
            InlineKeyboardButton(
                "2",
                callback_data=(
                    f"{prefix}:social:2"
                ),
            ),
            InlineKeyboardButton(
                "3",
                callback_data=(
                    f"{prefix}:social:3"
                ),
            ),
            InlineKeyboardButton(
                "4",
                callback_data=(
                    f"{prefix}:social:4"
                ),
            ),
            InlineKeyboardButton(
                "5",
                callback_data=(
                    f"{prefix}:social:5"
                ),
            ),
        ],
    ]

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_personality",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

    return keyboard


async def show_social_level(
    query,
    registration=True,
):
    if registration:

        text = profile_header(
            9,
            "به اجتماعی بودنت چند میدی؟ 👥",
            "از ۱ تا ۵ انتخاب کن.\n\n"
            "۱ یعنی بیشتر ترجیح میدی خلوت خودت باشی.\n"
            "۵ یعنی از بودن بین آدم‌ها انرژی می‌گیری.",
        )

    else:

        text = (
            "✦ <b>میزان اجتماعی بودن</b>\n\n"
            "از ۱ تا ۵ انتخاب کن.\n\n"
            "۱ = بیشتر خلوت\n"
            "۵ = خیلی اجتماعی"
        )

    await render_text(
        query,
        text,
        social_level_keyboard(
            registration=registration,
        ),
    )


async def social_level_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return SOCIAL_LEVEL

    await answer(query)

    data = query.data

    if data == "reg:back_personality":

        await ask_personality(
            query,
            context,
        )

        return PERSONALITY

    if not data.startswith(
        "reg:social:"
    ):
        return SOCIAL_LEVEL

    value = int(
        data.split(":")[-1]
    )

    if value < 1 or value > 5:
        return SOCIAL_LEVEL

    save_personality_data(
        context,
        "social_level",
        value,
    )

    await show_group_type(
        query,
        registration=True,
    )

    return GROUP_TYPE


# =========================================================
# GROUP TYPE
# =========================================================

def group_type_keyboard(
    registration=True,
):
    prefix = (
        "reg"
        if registration
        else "edit"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 دو نفره",
                callback_data=(
                    f"{prefix}:group:two"
                ),
            ),
            InlineKeyboardButton(
                "👥 جمع کوچک",
                callback_data=(
                    f"{prefix}:group:small"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                "🔥 جمع شلوغ",
                callback_data=(
                    f"{prefix}:group:large"
                ),
            ),
            InlineKeyboardButton(
                "🎲 فرقی نداره",
                callback_data=(
                    f"{prefix}:group:any"
                ),
            ),
        ],
    ]

    if registration:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="reg:back_social",
                ),
                InlineKeyboardButton(
                    "⌂ صفحه اصلی",
                    callback_data="home",
                ),
            ]
        )

    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        )

    return keyboard


async def show_group_type(
    query,
    registration=True,
):
    if registration:
        text = profile_header(
            10,
            "چه مدل جمعی رو بیشتر دوست داری؟ 👥",
            "معمولاً توی چه فضایی راحت‌تری؟",
        )

    else:
        text = (
            "✦ <b>مدل جمع</b>\n\n"
            "کدوم حالت بیشتر بهت می‌خوره؟"
        )

    await render_text(
        query,
        text,
        group_type_keyboard(
            registration=registration,
        ),
    )


async def group_type_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return GROUP_TYPE

    await answer(query)

    data = query.data

    if data == "reg:back_social":

        await show_social_level(
            query,
            registration=True,
        )

        return SOCIAL_LEVEL

    if not data.startswith(
        "reg:group:"
    ):
        return GROUP_TYPE

    value = data.split(":")[-1]

    if value not in GROUP_TYPES:
        return GROUP_TYPE

    save_personality_data(
        context,
        "group_type",
        value,
    )

    await finish_registration(
        update,
        context,
    )

    return ConversationHandler.END


# =========================================================
# FINISH REGISTRATION
# =========================================================

async def finish_registration(
    update,
    context,
):
    registration = context.user_data.get(
        "registration",
        {},
    )

    telegram_user = update.effective_user

    if not telegram_user:
        return

    interests = registration.get(
        "interests",
        [],
    )

    personality = registration.get(
        "personality",
        {},
    )

    await update_user(
        telegram_user.id,
        display_name=registration.get(
            "name",
            telegram_user.first_name or "کاربر",
        ),
        avatar_file_id=registration.get(
            "photo"
        ),
        age=registration.get(
            "age"
        ),
        gender=registration.get(
            "gender"
        ),
        city=registration.get(
            "city"
        ),
        interests=json.dumps(
            interests,
            ensure_ascii=False,
        ),
        bio=registration.get(
            "bio",
            "",
        ),
        personality=json.dumps(
            personality,
            ensure_ascii=False,
        ),
        profile_completed=1,
        profile_completion=100,
    )

    context.user_data.pop(
        "registration",
        None,
    )

    query = update.callback_query

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>FAZE</b>\n"
        "╰────────────────────╯\n\n"
        "🎉 <b>پروفایلت ساخته شد!</b>\n\n"
        "حالا می‌تونی وارد FAZE بشی و آدم‌های مناسب خودت رو پیدا کنی."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 مشاهده پروفایل",
                callback_data="profile:home",
            )
        ],
        [
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            )
        ],
    ]

    if query:
        await render_text(
            query,
            text,
            keyboard,
        )

    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )


# =========================================================
# EDIT MENU
# =========================================================

async def show_edit_menu(
    query,
):
    text = (
        "╭────────────────────╮\n"
        "       ✦ <b>ویرایش پروفایل</b>\n"
        "╰────────────────────╯\n\n"
        "کدوم بخش رو می‌خوای تغییر بدی؟\n\n"
        "<i>هر تغییری ذخیره میشه و فوراً روی پروفایلت اعمال میشه.</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 اسم",
                callback_data="profile:edit:name",
            ),
            InlineKeyboardButton(
                "📸 عکس",
                callback_data="profile:edit:photo",
            ),
        ],
        [
            InlineKeyboardButton(
                "🚻 جنسیت",
                callback_data="profile:edit:gender",
            ),
            InlineKeyboardButton(
                "🎂 سن",
                callback_data="profile:edit:age",
            ),
        ],
        [
            InlineKeyboardButton(
                "📍 استان",
                callback_data="profile:edit:city",
            ),
            InlineKeyboardButton(
                "💫 علایق",
                callback_data="profile:edit:interests",
            ),
        ],
        [
            InlineKeyboardButton(
                "📝 Bio",
                callback_data="profile:edit:bio",
            )
        ],
        [
            InlineKeyboardButton(
                "🧠 شخصیت",
                callback_data="profile:edit:personality",
            ),
            InlineKeyboardButton(
                "👥 اجتماعی بودن",
                callback_data="profile:edit:social",
            ),
        ],
        [
            InlineKeyboardButton(
                "👥 مدل جمع",
                callback_data="profile:edit:group",
            )
        ],
        [
            InlineKeyboardButton(
                "‹ پروفایل",
                callback_data="profile:home",
            ),
            InlineKeyboardButton(
                "⌂ صفحه اصلی",
                callback_data="home",
            ),
        ],
    ]

    await render_text(
        query,
        text,
        keyboard,
    )

    return EDIT_MENU


# =========================================================
# EDIT NAME
# =========================================================

async def edit_name_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await render_text(
        query,
        (
            "✦ <b>تغییر اسم</b>\n\n"
            "اسم جدیدت رو بفرست."
        ),
        [
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ]
        ],
    )

    return EDIT_NAME


async def edit_name_save(
    update,
    context,
):
    if not update.message:
        return EDIT_NAME

    name = update.message.text.strip()

    if not name:
        await update.message.reply_text(
            "اسم نمی‌تونه خالی باشه."
        )
        return EDIT_NAME

    if len(name) > 40:
        await update.message.reply_text(
            "اسم خیلی طولانیه. حداکثر ۴۰ کاراکتر."
        )
        return EDIT_NAME

    await update_user(
        update.effective_user.id,
        display_name=name,
    )

    await update.message.reply_text(
        "✓ اسم با موفقیت تغییر کرد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ]),
    )

    return EDIT_MENU


# =========================================================
# EDIT PHOTO
# =========================================================

async def edit_photo_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await render_text(
        query,
        (
            "✦ <b>تغییر عکس</b>\n\n"
            "عکس جدیدت رو بفرست."
        ),
        [
            [
                InlineKeyboardButton(
                    "🗑 حذف عکس",
                    callback_data="edit:photo_clear",
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="edit:menu",
                ),
                InlineKeyboardButton(
                    "⌂ پروفایل",
                    callback_data="profile:home",
                ),
            ],
        ],
    )

    return EDIT_PHOTO


async def edit_photo_handler(
    update,
    context,
):
    query = update.callback_query

    if query:

        await answer(query)

        if query.data == "edit:photo_clear":

            await update_user(
                query.from_user.id,
                avatar_file_id=None,
            )

            await render_text(
                query,
                (
                    "✓ <b>عکس حذف شد.</b>\n\n"
                    "می‌تونی یک عکس جدید هم ارسال کنی."
                ),
                [
                    [
                        InlineKeyboardButton(
                            "📸 انتخاب عکس جدید",
                            callback_data="profile:edit:photo",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "‹ ویرایش",
                            callback_data="edit:menu",
                        ),
                        InlineKeyboardButton(
                            "👤 پروفایل",
                            callback_data="profile:home",
                        ),
                    ],
                ],
            )

            return EDIT_MENU

        if query.data == "edit:menu":

            await show_edit_menu(
                query
            )

            return EDIT_MENU

        return EDIT_PHOTO

    if (
        update.message
        and update.message.photo
    ):
        photo = update.message.photo[-1]

        await update_user(
            update.effective_user.id,
            avatar_file_id=photo.file_id,
        )

        await update.message.reply_text(
            "✓ عکس پروفایل با موفقیت تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✏️ ادامه ویرایش",
                        callback_data="profile:edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👤 مشاهده پروفایل",
                        callback_data="profile:home",
                    )
                ],
            ]),
        )

        return EDIT_MENU

    return EDIT_PHOTO


# =========================================================
# EDIT GENDER
# =========================================================

async def edit_gender_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await show_gender_picker(
        query,
        registration=False,
    )

    return EDIT_GENDER


async def edit_gender_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_GENDER

    await answer(query)

    if query.data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if query.data == "edit:gender:male":
        gender = "male"

    elif query.data == "edit:gender:female":
        gender = "female"

    else:
        return EDIT_GENDER

    await update_user(
        query.from_user.id,
        gender=gender,
    )

    await render_text(
        query,
        "✓ <b>جنسیت با موفقیت تغییر کرد.</b>",
        [
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ],
    )

    return EDIT_MENU


# =========================================================
# EDIT AGE
# =========================================================

async def edit_age_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await show_age_picker(
        query,
        page=0,
        back_callback="edit:menu",
        edit_mode=True,
    )

    return EDIT_AGE


async def edit_age_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_AGE

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if data.startswith(
        "edit:age_page:"
    ):

        page = int(
            data.split(":")[-1]
        )

        await show_age_picker(
            query,
            page=page,
            back_callback="edit:menu",
            edit_mode=True,
        )

        return EDIT_AGE

    if data.startswith(
        "edit:age:"
    ):

        age = int(
            data.split(":")[-1]
        )

        await update_user(
            query.from_user.id,
            age=age,
        )

        await render_text(
            query,
            f"✓ <b>سن به {age} تغییر کرد.</b>",
            [
                [
                    InlineKeyboardButton(
                        "✏️ ادامه ویرایش",
                        callback_data="profile:edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👤 مشاهده پروفایل",
                        callback_data="profile:home",
                    )
                ],
            ],
        )

        return EDIT_MENU

    return EDIT_AGE


# =========================================================
# EDIT CITY
# =========================================================

async def edit_city_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await show_province_picker(
        query,
        page=0,
        registration=False,
    )

    return EDIT_CITY


async def edit_city_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_CITY

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if data.startswith(
        "edit:city_page:"
    ):

        page = int(
            data.split(":")[-1]
        )

        await show_province_picker(
            query,
            page=page,
            registration=False,
        )

        return EDIT_CITY

    if data.startswith(
        "edit:city:"
    ):

        index = int(
            data.split(":")[-1]
        )

        if (
            index < 0
            or index >= len(PROVINCES)
        ):
            return EDIT_CITY

        province = PROVINCES[
            index
        ]

        await update_user(
            query.from_user.id,
            city=province,
        )

        await render_text(
            query,
            (
                "✓ <b>استان تغییر کرد.</b>\n\n"
                f"📍 استان جدید: "
                f"<b>{safe_text(province)}</b>"
            ),
            [
                [
                    InlineKeyboardButton(
                        "✏️ ادامه ویرایش",
                        callback_data="profile:edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👤 مشاهده پروفایل",
                        callback_data="profile:home",
                    )
                ],
            ],
        )

        return EDIT_MENU

    return EDIT_CITY


# =========================================================
# EDIT INTERESTS
# =========================================================

async def edit_interests_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    user = await get_user(
        query.from_user.id
    )

    if not user:
        return EDIT_INTERESTS

    try:
        interests = json.loads(
            user["interests"] or "[]"
        )

        if not isinstance(
            interests,
            list,
        ):
            interests = []

    except Exception:
        interests = []

    context.user_data.setdefault(
        "edit",
        {},
    )["interests"] = list(
        interests
    )

    await show_interest_picker(
        query,
        selected=interests,
        registration=False,
    )

    return EDIT_INTERESTS


async def save_edited_interests(
    query,
    context,
):
    interests = (
        context.user_data
        .get(
            "edit",
            {},
        )
        .get(
            "interests",
            [],
        )
    )

    await update_user(
        query.from_user.id,
        interests=json.dumps(
            interests,
            ensure_ascii=False,
        ),
    )

    context.user_data.pop(
        "edit",
        None,
    )

    await render_text(
        query,
        "✓ <b>علایقت با موفقیت ذخیره شد.</b>",
        [
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ],
    )


# =========================================================
# EDIT BIO
# =========================================================

async def edit_bio_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await ask_bio(
        query,
        registration=False,
    )

    return EDIT_BIO


async def edit_bio_handler(
    update,
    context,
):
    query = update.callback_query

    if query:

        await answer(query)

        if query.data == "edit:menu":

            await show_edit_menu(
                query
            )

            return EDIT_MENU

        if query.data == "edit:bio_clear":

            await update_user(
                query.from_user.id,
                bio="",
            )

            await render_text(
                query,
                "✓ <b>Bio پاک شد.</b>",
                [
                    [
                        InlineKeyboardButton(
                            "✏️ ادامه ویرایش",
                            callback_data="profile:edit",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "👤 مشاهده پروفایل",
                            callback_data="profile:home",
                        )
                    ],
                ],
            )

            return EDIT_MENU

        return EDIT_BIO

    if update.message:

        bio = update.message.text.strip()

        if len(bio) > 500:

            await update.message.reply_text(
                "Bio خیلی طولانیه. حداکثر ۵۰۰ کاراکتر."
            )

            return EDIT_BIO

        await update_user(
            update.effective_user.id,
            bio=bio,
        )

        await update.message.reply_text(
            "✓ Bio با موفقیت تغییر کرد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✏️ ادامه ویرایش",
                        callback_data="profile:edit",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👤 مشاهده پروفایل",
                        callback_data="profile:home",
                    )
                ],
            ]),
        )

        return EDIT_MENU

    return EDIT_BIO


# =========================================================
# EDIT PERSONALITY
# =========================================================

async def edit_personality_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    text = (
        "✦ <b>تغییر تیپ شخصیتی</b>\n\n"
        "خودت رو بیشتر کدوم می‌دونی؟ 🧠"
    )

    await render_text(
        query,
        text,
        personality_keyboard(
            registration=False,
        ),
    )

    return EDIT_PERSONALITY


async def edit_personality_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_PERSONALITY

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    value = data.split(":")[-1]

    if value not in PERSONALITY_TYPES:
        return EDIT_PERSONALITY

    user = await get_user(
        query.from_user.id
    )

    if not user:
        return EDIT_PERSONALITY

    personality = get_personality(
        user
    )

    personality["type"] = value

    await update_user(
        query.from_user.id,
        personality=json.dumps(
            personality,
            ensure_ascii=False,
        ),
    )

    await render_text(
        query,
        (
            "✓ <b>تیپ شخصیتی تغییر کرد.</b>\n\n"
            f"🧠 تیپ جدید: "
            f"<b>{personality_text(value)}</b>"
        ),
        [
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ],
    )

    return EDIT_MENU


# =========================================================
# EDIT SOCIAL LEVEL
# =========================================================

async def edit_social_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await show_social_level(
        query,
        registration=False,
    )

    return EDIT_SOCIAL_LEVEL


async def edit_social_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_SOCIAL_LEVEL

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if not data.startswith(
        "edit:social:"
    ):
        return EDIT_SOCIAL_LEVEL

    value = int(
        data.split(":")[-1]
    )

    if value < 1 or value > 5:
        return EDIT_SOCIAL_LEVEL

    user = await get_user(
        query.from_user.id
    )

    if not user:
        return EDIT_SOCIAL_LEVEL

    personality = get_personality(
        user
    )

    personality[
        "social_level"
    ] = value

    await update_user(
        query.from_user.id,
        personality=json.dumps(
            personality,
            ensure_ascii=False,
        ),
    )

    await render_text(
        query,
        (
            "✓ <b>میزان اجتماعی بودنت تغییر کرد.</b>\n\n"
            f"👥 امتیاز جدید: "
            f"<b>{value} از ۵</b>"
        ),
        [
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ],
    )

    return EDIT_MENU


# =========================================================
# EDIT GROUP TYPE
# =========================================================

async def edit_group_start(
    update,
    context,
):
    query = update.callback_query

    await answer(query)

    await show_group_type(
        query,
        registration=False,
    )

    return EDIT_GROUP_TYPE


async def edit_group_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_GROUP_TYPE

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if not data.startswith(
        "edit:group:"
    ):
        return EDIT_GROUP_TYPE

    value = data.split(":")[-1]

    if value not in GROUP_TYPES:
        return EDIT_GROUP_TYPE

    user = await get_user(
        query.from_user.id
    )

    if not user:
        return EDIT_GROUP_TYPE

    personality = get_personality(
        user
    )

    personality[
        "group_type"
    ] = value

    await update_user(
        query.from_user.id,
        personality=json.dumps(
            personality,
            ensure_ascii=False,
        ),
    )

    await render_text(
        query,
        (
            "✓ <b>مدل جمع موردعلاقه تغییر کرد.</b>\n\n"
            f"👥 انتخاب جدید: "
            f"<b>{group_text(value)}</b>"
        ),
        [
            [
                InlineKeyboardButton(
                    "✏️ ادامه ویرایش",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 مشاهده پروفایل",
                    callback_data="profile:home",
                )
            ],
        ],
    )

    return EDIT_MENU


# =========================================================
# EDIT MENU HANDLER
# =========================================================

async def edit_menu_handler(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return EDIT_MENU

    await answer(query)

    data = query.data

    if data == "edit:menu":

        await show_edit_menu(
            query
        )

        return EDIT_MENU

    if data == "profile:edit:name":
        return await edit_name_start(
            update,
            context,
        )

    if data == "profile:edit:photo":
        return await edit_photo_start(
            update,
            context,
        )

    if data == "profile:edit:gender":
        return await edit_gender_start(
            update,
            context,
        )

    if data == "profile:edit:age":
        return await edit_age_start(
            update,
            context,
        )

    if data == "profile:edit:city":
        return await edit_city_start(
            update,
            context,
        )

    if data == "profile:edit:interests":
        return await edit_interests_start(
            update,
            context,
        )

    if data == "profile:edit:bio":
        return await edit_bio_start(
            update,
            context,
        )

    if data == "profile:edit:personality":
        return await edit_personality_start(
            update,
            context,
        )

    if data == "profile:edit:social":
        return await edit_social_start(
            update,
            context,
        )

    if data == "profile:edit:group":
        return await edit_group_start(
            update,
            context,
        )

    if data == "profile:home":

        await profile_home(
            update,
            context,
        )

        return ConversationHandler.END

    if data == "home":

        await go_home(
            update,
            context,
        )

        return ConversationHandler.END

    return EDIT_MENU


# =========================================================
# REGISTRATION NAVIGATION
# =========================================================

async def registration_navigation(
    update,
    context,
):
    query = update.callback_query

    if not query:
        return ConversationHandler.END

    await answer(query)

    data = query.data

    if data == "reg:welcome":

        context.user_data[
            "registration"
        ] = {}

        await render_text(
            query,
            (
                "✦ <b>FAZE</b>\n\n"
                "🚀 <b>بزن بریم</b>\n\n"
                "چند مرحله کوتاه تا ساخت پروفایلت."
            ),
            [
                [
                    InlineKeyboardButton(
                        "🚀 شروع",
                        callback_data="reg:name",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⌂ صفحه اصلی",
                        callback_data="home",
                    )
                ],
            ],
        )

        return NAME

    if data in (
        "reg:back_name",
        "reg:name",
    ):

        await render_text(
            query,
            profile_header(
                1,
                "اسم تو چیه؟",
                "اسم نمایشی‌ای که دوست داری بقیه ببینن رو بفرست.",
            ),
            nav_buttons(
                back_callback="reg:welcome",
            ),
        )

        return NAME

    if data == "reg:back_photo":

        await render_text(
            query,
            profile_header(
                2,
                "یه عکس هم اضافه کنیم؟",
                "عکست می‌تونه پروفایلت رو کامل‌تر کنه.",
            ),
            [
                [
                    InlineKeyboardButton(
                        "📸 ارسال عکس",
                        callback_data="reg:photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "رد کردن",
                        callback_data="reg:skip_photo",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "‹ برگشت",
                        callback_data="reg:back_name",
                    ),
                    InlineKeyboardButton(
                        "⌂ صفحه اصلی",
                        callback_data="home",
                    ),
                ],
            ],
        )

        return PHOTO

    if data == "reg:back_bio":

        await ask_bio(
            query,
            registration=True,
        )

        return BIO

    if data == "home":

        await go_home(
            update,
            context,
        )

        return ConversationHandler.END

    return ConversationHandler.END


# =========================================================
# PROFILE CONVERSATION
# =========================================================

def registration_conversation():

    return ConversationHandler(
        entry_points=[
            # ساخت پروفایل
            CallbackQueryHandler(
                start_registration,
                pattern=r"^profile:start$",
            ),

            # باز کردن پروفایل
            CallbackQueryHandler(
                profile_home,
                pattern=r"^profile:home$",
            ),

            # ویرایش پروفایل
            CallbackQueryHandler(
                edit_profile,
                pattern=r"^profile:edit$",
            ),
        ],

        states={

            # =================================================
            # REGISTRATION
            # =================================================

            NAME: [
                CallbackQueryHandler(
                    registration_navigation,
                    pattern=(
                        r"^(reg:welcome|"
                        r"reg:name|"
                        r"reg:back_name|"
                        r"home)$"
                    ),
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    ask_name,
                ),
            ],

            PHOTO: [
                CallbackQueryHandler(
                    photo_choice,
                    pattern=(
                        r"^reg:"
                        r"(photo|skip_photo|back_photo)$"
                    ),
                ),

                MessageHandler(
                    filters.PHOTO,
                    receive_photo,
                ),
            ],

            AGE: [
                CallbackQueryHandler(
                    age_handler,
                    pattern=(
                        r"^reg:"
                        r"(continue_age|"
                        r"age_page:\d+|"
                        r"age:\d+|"
                        r"back_photo)$"
                    ),
                ),
            ],

            GENDER: [
                CallbackQueryHandler(
                    gender_handler,
                    pattern=(
                        r"^reg:"
                        r"(gender:(male|female)|"
                        r"back_age)$"
                    ),
                ),
            ],

            CITY: [
                CallbackQueryHandler(
                    city_handler,
                    pattern=(
                        r"^reg:"
                        r"(city:\d+|"
                        r"city_page:\d+|"
                        r"back_gender)$"
                    ),
                ),
            ],

            INTERESTS_STATE: [
                CallbackQueryHandler(
                    interests_handler,
                    pattern=(
                        r"^reg:"
                        r"(interest:\d+|"
                        r"interests_done|"
                        r"back_city)$"
                    ),
                ),
            ],

            BIO: [
                CallbackQueryHandler(
                    bio_handler,
                    pattern=(
                        r"^reg:"
                        r"(skip_bio|"
                        r"back_interests)$"
                    ),
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bio_handler,
                ),
            ],

            # =================================================
            # PERSONALITY
            # =================================================

            PERSONALITY: [
                CallbackQueryHandler(
                    personality_handler,
                    pattern=(
                        r"^reg:"
                        r"(personality:"
                        r"(introvert|"
                        r"ambivert|"
                        r"extrovert)|"
                        r"back_bio)$"
                    ),
                ),
            ],

            SOCIAL_LEVEL: [
                CallbackQueryHandler(
                    social_level_handler,
                    pattern=(
                        r"^reg:"
                        r"(social:[1-5]|"
                        r"back_personality)$"
                    ),
                ),
            ],

            GROUP_TYPE: [
                CallbackQueryHandler(
                    group_type_handler,
                    pattern=(
                        r"^reg:"
                        r"(group:"
                        r"(two|small|large|any)|"
                        r"back_social)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT MENU
            # =================================================

            EDIT_MENU: [
                CallbackQueryHandler(
                    edit_menu_handler,
                    pattern=(
                        r"^(profile:edit:"
                        r"(name|photo|gender|age|city|"
                        r"interests|bio|personality|social|group)"
                        r"|profile:home|"
                        r"home|"
                        r"edit:menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT NAME
            # =================================================

            EDIT_NAME: [
                CallbackQueryHandler(
                    edit_menu_handler,
                    pattern=(
                        r"^(edit:menu|"
                        r"profile:home|"
                        r"home)$"
                    ),
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_name_save,
                ),
            ],

            # =================================================
            # EDIT PHOTO
            # =================================================

            EDIT_PHOTO: [
                CallbackQueryHandler(
                    edit_photo_handler,
                    pattern=(
                        r"^(edit:photo_clear|"
                        r"edit:menu)$"
                    ),
                ),

                MessageHandler(
                    filters.PHOTO,
                    edit_photo_handler,
                ),
            ],

            # =================================================
            # EDIT GENDER
            # =================================================

            EDIT_GENDER: [
                CallbackQueryHandler(
                    edit_gender_handler,
                    pattern=(
                        r"^edit:"
                        r"(gender:"
                        r"(male|female)|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT AGE
            # =================================================

            EDIT_AGE: [
                CallbackQueryHandler(
                    edit_age_handler,
                    pattern=(
                        r"^edit:"
                        r"(age:\d+|"
                        r"age_page:\d+|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT CITY
            # =================================================

            EDIT_CITY: [
                CallbackQueryHandler(
                    edit_city_handler,
                    pattern=(
                        r"^edit:"
                        r"(city:\d+|"
                        r"city_page:\d+|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT INTERESTS
            # =================================================

            EDIT_INTERESTS: [
                CallbackQueryHandler(
                    interests_handler,
                    pattern=(
                        r"^edit:"
                        r"(interest:\d+|"
                        r"interests_done|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT BIO
            # =================================================

            EDIT_BIO: [
                CallbackQueryHandler(
                    edit_bio_handler,
                    pattern=(
                        r"^edit:"
                        r"(bio_clear|"
                        r"menu)$"
                    ),
                ),

                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    edit_bio_handler,
                ),
            ],

            # =================================================
            # EDIT PERSONALITY
            # =================================================

            EDIT_PERSONALITY: [
                CallbackQueryHandler(
                    edit_personality_handler,
                    pattern=(
                        r"^edit:"
                        r"(personality:"
                        r"(introvert|"
                        r"ambivert|"
                        r"extrovert)|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT SOCIAL
            # =================================================

            EDIT_SOCIAL_LEVEL: [
                CallbackQueryHandler(
                    edit_social_handler,
                    pattern=(
                        r"^edit:"
                        r"(social:[1-5]|"
                        r"menu)$"
                    ),
                ),
            ],

            # =================================================
            # EDIT GROUP
            # =================================================

            EDIT_GROUP_TYPE: [
                CallbackQueryHandler(
                    edit_group_handler,
                    pattern=(
                        r"^edit:"
                        r"(group:"
                        r"(two|small|large|any)|"
                        r"menu)$"
                    ),
                ),
            ],
        },

        fallbacks=[
            CallbackQueryHandler(
                go_home,
                pattern=r"^home$",
            ),
        ],

        allow_reentry=True,
    )


# =========================================================
# OPTIONAL DIRECT COMMAND
# =========================================================

async def profile_command(
    update,
    context,
):
    telegram_user = update.effective_user

    if not telegram_user:
        return

    user = await get_user(
        telegram_user.id
    )

    if not user:
        await create_user(
            telegram_user
        )

        user = await get_user(
            telegram_user.id
        )

    if not user:
        return

    if not user["profile_completed"]:

        await update.message.reply_text(
            "هنوز پروفایلت رو نساختی.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✦ ساخت پروفایل",
                        callback_data="profile:start",
                    )
                ]
            ]),
        )

        return

    try:
        interests = json.loads(
            user["interests"] or "[]"
        )

        if not isinstance(
            interests,
            list,
        ):
            interests = []

    except Exception:
        interests = []

    personality = get_personality(
        user
    )

    gender_map = {
        "male": "پسر",
        "female": "دختر",
    }

    display_name = safe_text(
        user["display_name"]
        or user["first_name"]
        or "کاربر"
    )

    gender = gender_map.get(
        user["gender"],
        "مشخص نشده",
    )

    province = safe_text(
        user["city"]
        or "مشخص نشده"
    )

    interest_text = (
        "\n".join(
            f"▫️ {safe_text(x)}"
            for x in interests
        )
        if interests
        else "هنوز چیزی انتخاب نشده."
    )

    text = (
        "╭────────────────────╮\n"
        "          ✦ <b>PROFILE</b>\n"
        "╰────────────────────╯\n\n"
        f"👤 <b>اسم:</b> {display_name}\n"
        f"🎂 <b>سن:</b> {user['age'] or '—'}\n"
        f"🚻 <b>جنسیت:</b> {gender}\n"
        f"📍 <b>استان:</b> {province}\n\n"
        "💫 <b>علایق من</b>\n"
        f"{interest_text}\n\n"
        "🧠 <b>شخصیت من</b>\n\n"
        f"   🧠 تیپ شخصیتی: "
        f"<b>{personality_text(personality.get('type'))}</b>\n"
        f"   👥 اجتماعی بودن: "
        f"<b>{social_text(personality.get('social_level'))}</b>\n"
        f"   👥 مدل جمع: "
        f"<b>{group_text(personality.get('group_type'))}</b>\n\n"
        "📝 <b>Bio</b>\n"
        f"{safe_text(user['bio'] or '—')}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Level {user['level']}"
        f" · ⚡ {user['xp']} XP"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✏️ ویرایش پروفایل",
                    callback_data="profile:edit",
                )
            ],
            [
                InlineKeyboardButton(
                    "‹ برگشت",
                    callback_data="home",
                )
            ],
        ]),
    )