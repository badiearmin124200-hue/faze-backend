
import logging

import aiosqlite

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
)

from src.db.database import DB_PATH


logger = logging.getLogger(__name__)


# =========================================================
# LIVE MODS
# =========================================================

async def get_modes():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT
                id,
                slug,
                title,
                description,
                emoji
            FROM live_modes
            WHERE active = 1
            ORDER BY id
        """)

        rows = await cursor.fetchall()

    return [
        {
            "id": row[0],
            "slug": row[1],
            "title": row[2],
            "description": row[3],
            "emoji": row[4],
        }
        for row in rows
    ]


async def get_mode(slug: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT
                id,
                slug,
                title,
                description,
                emoji
            FROM live_modes
            WHERE slug = ?
              AND active = 1
        """, (slug,))

        row = await cursor.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "slug": row[1],
        "title": row[2],
        "description": row[3],
        "emoji": row[4],
    }


# =========================================================
# JOIN / LEAVE
# =========================================================

async def join_mode(user_id: int, mode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        # هر کاربر در لحظه فقط یک مود فعال داشته باشد
        await db.execute("""
            DELETE FROM live_mode_members
            WHERE user_id = ?
        """, (user_id,))

        await db.execute("""
            INSERT OR REPLACE INTO live_mode_members
            (mode_id, user_id, joined_at, last_seen)
            VALUES (
                ?,
                ?,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
        """, (mode_id, user_id))

        await db.commit()


async def leave_mode(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM live_mode_members
            WHERE user_id = ?
        """, (user_id,))

        await db.commit()


async def refresh_presence(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE live_mode_members
            SET last_seen = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))

        await db.commit()


# =========================================================
# ACTIVE MEMBERS
# =========================================================

async def get_mode_members(mode_id: int, exclude_user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("""
            SELECT
                m.user_id,
                p.username,
                p.first_name,
                m.joined_at,
                m.last_seen
            FROM live_mode_members m
            LEFT JOIN compatibility_profiles p
                ON p.user_id = m.user_id
            WHERE m.mode_id = ?
              AND m.user_id != ?
            ORDER BY m.joined_at DESC
        """, (mode_id, exclude_user_id))

        rows = await cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2] or "کاربر",
            "joined_at": row[3],
            "last_seen": row[4],
        }
        for row in rows
    ]


async def get_mode_count(mode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM live_mode_members
            WHERE mode_id = ?
        """, (mode_id,))

        row = await cursor.fetchone()

    return row[0] if row else 0


# =========================================================
# MAIN MENU
# =========================================================

def modes_keyboard(modes):
    buttons = []

    for mode in modes:
        count = mode.get("count", 0)

        buttons.append([
            InlineKeyboardButton(
                f"{mode['emoji']} {mode['title']}  ·  👥 {count}",
                callback_data=f"mode:open:{mode['slug']}",
            )
        ])

    return InlineKeyboardMarkup(buttons)


async def show_modes(query):
    modes = await get_modes()

    if not modes:
        await query.edit_message_text(
            "فعلاً هیچ مودی فعال نیست.",
            parse_mode=ParseMode.HTML,
        )
        return

    for mode in modes:
        mode["count"] = await get_mode_count(mode["id"])

    text = (
        "🔥 <b>الان دنبال چی هستی؟</b>\n\n"
        "FAZE آدم‌هایی رو پیدا می‌کنه که همین الان "
        "مودشون شبیه توئه.\n\n"
        "یکی رو انتخاب کن 👇"
    )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=modes_keyboard(modes),
    )


# =========================================================
# MODE PAGE
# =========================================================

def mode_members_keyboard(
    mode_slug: str,
    members: list,
):
    buttons = []

    for member in members:
        name = member["first_name"]

        buttons.append([
            InlineKeyboardButton(
                f"👤 {name}",
                callback_data=f"mode:person:{member['user_id']}:{mode_slug}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔥 پیوستن به این مود",
            callback_data=f"mode:join:{mode_slug}",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🔄 بروزرسانی",
            callback_data=f"mode:open:{mode_slug}",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ همه مودها",
            callback_data="mode:list",
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def show_mode(query, slug: str):
    mode = await get_mode(slug)

    if not mode:
        await query.answer(
            "این مود پیدا نشد.",
            show_alert=True,
        )
        return

    await refresh_presence(
        query.from_user.id
    )

    members = await get_mode_members(
        mode["id"],
        query.from_user.id,
    )

    count = await get_mode_count(
        mode["id"]
    )

    if members:
        people_text = "\n".join(
            [
                f"👤 <b>{member['first_name']}</b>"
                for member in members[:20]
            ]
        )
    else:
        people_text = (
            "هنوز کسی اینجا نیست.\n"
            "اولین نفر باش 😎"
        )

    text = (
        f"{mode['emoji']} <b>{mode['title']}</b>\n\n"
        f"{mode['description']}\n\n"
        f"👥 <b>{count}</b> نفر الان اینجان.\n\n"
        f"{people_text}\n\n"
        "اگر همین حال‌وهوارو داری، وارد شو 👇"
    )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=mode_members_keyboard(
            mode["slug"],
            members,
        ),
    )


# =========================================================
# JOIN MODE
# =========================================================

async def join_current_mode(
    query,
    slug: str,
):
    mode = await get_mode(slug)

    if not mode:
        await query.answer(
            "مود پیدا نشد.",
            show_alert=True,
        )
        return

    await join_mode(
        query.from_user.id,
        mode["id"],
    )

    await query.answer(
        "🔥 وارد مود شدی!",
        show_alert=True,
    )

    await show_mode(
        query,
        slug,
    )


# =========================================================
# PERSON
# =========================================================

async def show_person(
    query,
    user_id: int,
    mode_slug: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT
                user_id,
                username,
                first_name,
                gender,
                age,
                city
            FROM compatibility_profiles
            WHERE user_id = ?
        """, (user_id,))

        row = await cursor.fetchone()

    if not row:
        await query.answer(
            "پروفایل این کاربر پیدا نشد.",
            show_alert=True,
        )
        return

    name = row[2] or "کاربر"
    username = row[1]
    age = row[4]
    city = row[5]

    text = (
        f"👤 <b>{name}</b>\n\n"
        f"🔥 مود فعلی: <b>{mode_slug}</b>\n"
    )

    if age:
        text += f"🎂 سن: {age}\n"

    if city:
        text += f"📍 شهر: {city}\n"

    if username:
        text += f"\n🔗 @{username}"

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 برگشت به مود",
                    callback_data=f"mode:open:{mode_slug}",
                )
            ]
        ]),
    )


# =========================================================
# OPEN FROM /START
# =========================================================

async def open_modes(
    query,
    context,
):
    await query.answer()
    await show_modes(query)


# =========================================================
# CALLBACK
# =========================================================

async def mode_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query or not query.data:
        return

    parts = query.data.split(":")

    if len(parts) < 2:
        return

    action = parts[1]

    try:

        # -----------------------------
        # LIST
        # -----------------------------

        if action == "list":
            await query.answer()
            await show_modes(query)
            return

        # -----------------------------
        # OPEN
        # -----------------------------

        if action == "open":

            if len(parts) != 3:
                return

            slug = parts[2]

            await query.answer()
            await show_mode(
                query,
                slug,
            )

            return

        # -----------------------------
        # JOIN
        # -----------------------------

        if action == "join":

            if len(parts) != 3:
                return

            slug = parts[2]

            await join_current_mode(
                query,
                slug,
            )

            return

        # -----------------------------
        # PERSON
        # -----------------------------

        if action == "person":

            if len(parts) != 4:
                return

            user_id = int(parts[2])
            mode_slug = parts[3]

            await query.answer()

            await show_person(
                query,
                user_id,
                mode_slug,
            )

            return

    except Exception:
        logger.exception(
            "Live mode callback failed"
        )

        try:
            await query.answer(
                "یه خطایی پیش اومد. دوباره امتحان کن.",
                show_alert=True,
            )
        except Exception:
            pass


# =========================================================
# REGISTER
# =========================================================

def register(app: Application):

    app.add_handler(
        CallbackQueryHandler(
            mode_callback,
            pattern=r"^mode:",
        )
    )

    logger.info(
        "FAZE live modes registered."
    )
