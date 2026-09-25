import hashlib
import hmac
import json
import logging
import math
import os

from src.group_music.config import GROUP_MUSIC_TEST_MODE

import time
from urllib.parse import parse_qsl

import aiosqlite
from fastapi import WebSocket, WebSocketDisconnect

from src.db.database import (
    DB_PATH,
    get_music_room,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

GROUP_MUSIC_MAX_USERS = 20


# =========================================================
# TELEGRAM INIT DATA
# =========================================================

def verify_telegram_init_data(
    init_data: str,
    bot_token: str,
):
    if not init_data or not bot_token:
        return None

    try:
        data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True,
            )
        )

        received_hash = data.pop(
            "hash",
            None,
        )

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={data[key]}"
            for key in sorted(data)
        )

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash,
        ):
            return None

        try:
            auth_date = int(
                data.get(
                    "auth_date",
                    "0",
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        now = int(
            time.time()
        )

        if auth_date <= 0:
            return None

        if auth_date > now + 60:
            return None

        if now - auth_date > 24 * 60 * 60:
            return None

        user_raw = data.get(
            "user",
            "{}",
        )

        try:
            user_data = json.loads(
                user_raw
            )
        except (
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return None

        if not isinstance(
            user_data,
            dict,
        ):
            return None

        if not user_data.get(
            "id"
        ):
            return None

        try:
            user_data["id"] = int(
                user_data["id"]
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return user_data

    except Exception:
        logger.exception(
            "Telegram init data verification failed"
        )

        return None


# =========================================================
# DATABASE USER
# =========================================================

async def get_user_by_telegram_id(
    telegram_id: int,
):
    try:
        telegram_id = int(
            telegram_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    try:
        async with aiosqlite.connect(
            DB_PATH
        ) as db:

            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    display_name,
                    avatar_file_id
                FROM users
                WHERE telegram_id = ?
                LIMIT 1
                """,
                (
                    telegram_id,
                ),
            )

            row = await cursor.fetchone()

        return (
            dict(row)
            if row
            else None
        )

    except Exception:
        logger.exception(
            "Failed to load user | telegram_id=%s",
            telegram_id,
        )

        return None


# =========================================================
# MUSIC TRACK
# =========================================================

async def get_music_track(
    track_id: int,
):
    try:
        track_id = int(
            track_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if track_id <= 0:
        return None

    try:
        async with aiosqlite.connect(
            DB_PATH
        ) as db:

            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    id,
                    title,
                    artist,
                    file_url,
                    duration
                FROM music_library
                WHERE id = ?
                LIMIT 1
                """,
                (
                    track_id,
                ),
            )

            row = await cursor.fetchone()

        return (
            dict(row)
            if row
            else None
        )

    except Exception:
        logger.exception(
            "Failed to load music track | track_id=%s",
            track_id,
        )

        return None


# =========================================================
# DEV USERS
# =========================================================

DEV_USERS = {
    "1": {
        "id": 100001,
        "name": "کاربر تست ۱",
        "username": "dev_creator",
        "avatar": None,
    },

    "2": {
        "id": 100002,
        "name": "کاربر تست ۲",
        "username": "dev_guest",
        "avatar": None,
    },
}


# =========================================================
# DEV ROOM
# =========================================================

DEV_ROOM_ID = "__FAZE_DEV_ROOM__"


def get_dev_user(
    dev_user: str,
):
    return DEV_USERS.get(
        str(dev_user)
    )


def get_dev_room():
    return {
        "room_id": DEV_ROOM_ID,
        "invite_token": "dev-token",

        "creator_id": DEV_USERS[
            "1"
        ][
            "id"
        ],

        "guest_id": DEV_USERS[
            "2"
        ][
            "id"
        ],

        "genre": "all",
        "mode": "friend",
        "status": "active",
    }


def is_local_dev_connection(
    websocket: WebSocket,
):
    client = websocket.client

    if not client:
        return False

    host = client.host

    return host in {
        "127.0.0.1",
        "::1",
        "localhost",
    }


# =========================================================
# GROUP MUSIC ROOM
# =========================================================

def is_group_music_room(
    room_id: str,
) -> bool:
    """
    Group Music rooms created by service.py use:

        gmusic_<group_id>_<random>

    Keep support for older gm_ prefix too.
    """

    value = str(
        room_id or ""
    )

    return (
        value.startswith("gmusic_")
        or value.startswith("gm_")
    )


async def get_group_music_room(
    room_id: str,
):
    """
    Load an Add-to-Group Music Room.
    """

    try:
        async with aiosqlite.connect(
            DB_PATH
        ) as db:

            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    r.id,
                    r.group_id,
                    r.room_id,
                    r.created_by,
                    r.created_at,
                    r.active,

                    g.title AS group_title,
                    g.added_by AS group_added_by,
                    g.active AS group_active

                FROM group_music_rooms r

                LEFT JOIN group_music_groups g
                    ON g.group_id = r.group_id

                WHERE r.room_id = ?

                LIMIT 1
                """,
                (
                    room_id,
                ),
            )

            row = await cursor.fetchone()

        if not row:
            return None

        room = dict(
            row
        )

        room_active = (
            int(
                room.get(
                    "active",
                    0,
                )
                or 0
            )
            == 1
        )

        group_active = (
            int(
                room.get(
                    "group_active",
                    0,
                )
                or 0
            )
            == 1
        )

        if not room_active:
            room["status"] = "closed"

        elif not group_active:
            room["status"] = "closed"

        else:
            room["status"] = "active"

        room["creator_id"] = room.get(
            "created_by"
        )

        room["guest_id"] = None

        room["mode"] = "group"

        room["genre"] = "all"

        # Group rooms do not use invite tokens.
        room["invite_token"] = ""

        return room

    except Exception:
        logger.exception(
            "Failed to load Group Music Room | room=%s",
            room_id,
        )

        return None


# =========================================================
# GROUP MUSIC ACCESS
# =========================================================

async def get_group_music_access(
    room,
    user_id: int,
):
    """
    Verify Group Music access.

    Production:
        - Group must be active.
        - Room must be active.
        - Member must be registered.
        - Bot must have been started.
        - Required channels must be joined.
        - access_granted must be 1.
        - Active subscription is required.

    Test mode:
        - New users are automatically registered.
        - Membership flags are automatically granted.
        - Subscription is not required.
    """

    if not room:
        return None

    try:
        group_id = int(
            room.get("group_id")
        )

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    try:
        async with aiosqlite.connect(
            DB_PATH
        ) as db:

            db.row_factory = aiosqlite.Row

            # =================================================
            # GROUP
            # =================================================

            cursor = await db.execute(
                """
                SELECT
                    group_id,
                    title,
                    added_by,
                    active
                FROM group_music_groups
                WHERE group_id = ?
                LIMIT 1
                """,
                (
                    group_id,
                ),
            )

            group = await cursor.fetchone()

            if not group:

                logger.warning(
                    "Group Music access denied: "
                    "group not found | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            if int(
                group["active"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "group inactive | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # ROOM
            # =================================================

            cursor = await db.execute(
                """
                SELECT
                    room_id,
                    group_id,
                    created_by,
                    active
                FROM group_music_rooms
                WHERE room_id = ?
                  AND group_id = ?
                LIMIT 1
                """,
                (
                    room.get("room_id"),
                    group_id,
                ),
            )

            room_row = await cursor.fetchone()

            if not room_row:

                logger.warning(
                    "Group Music access denied: "
                    "room not found | room=%s | group=%s | user=%s",
                    room.get("room_id"),
                    group_id,
                    user_id,
                )

                return None

            if int(
                room_row["active"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "room inactive | room=%s | user=%s",
                    room.get("room_id"),
                    user_id,
                )

                return None

            # =================================================
            # MEMBER
            # =================================================

            cursor = await db.execute(
                """
                SELECT
                    group_id,
                    user_id,
                    bot_started,
                    channel_1_joined,
                    channel_2_joined,
                    access_granted
                FROM group_music_members
                WHERE group_id = ?
                  AND user_id = ?
                LIMIT 1
                """,
                (
                    group_id,
                    user_id,
                ),
            )

            member = await cursor.fetchone()

            # =================================================
            # TEST MODE
            # =================================================
            # اگر کاربر برای اولین بار وارد Room شده
            # و هنوز member ندارد، در حالت تست ثبتش می‌کنیم.
            # =================================================

            if (
                not member
                and GROUP_MUSIC_TEST_MODE
            ):

                logger.info(
                    "Group Music TEST MODE: "
                    "registering new member | "
                    "group=%s | user=%s",
                    group_id,
                    user_id,
                )

                await db.execute(
                    """
                    INSERT INTO group_music_members
                    (
                        group_id,
                        user_id,
                        bot_started,
                        channel_1_joined,
                        channel_2_joined,
                        access_granted
                    )
                    VALUES (?, ?, 1, 1, 1, 1)
                    ON CONFLICT(group_id, user_id)
                    DO UPDATE SET
                        bot_started = 1,
                        channel_1_joined = 1,
                        channel_2_joined = 1,
                        access_granted = 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        group_id,
                        user_id,
                    ),
                )

                await db.commit()

                # دوباره member را می‌خوانیم
                cursor = await db.execute(
                    """
                    SELECT
                        group_id,
                        user_id,
                        bot_started,
                        channel_1_joined,
                        channel_2_joined,
                        access_granted
                    FROM group_music_members
                    WHERE group_id = ?
                      AND user_id = ?
                    LIMIT 1
                    """,
                    (
                        group_id,
                        user_id,
                    ),
                )

                member = await cursor.fetchone()

            # =================================================
            # MEMBER NOT FOUND
            # =================================================

            if not member:

                logger.warning(
                    "Group Music access denied: "
                    "member not found | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # BOT START
            # =================================================

            if int(
                member["bot_started"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "bot not started | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # CHANNEL 1
            # =================================================

            if int(
                member["channel_1_joined"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "channel 1 not joined | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # CHANNEL 2
            # =================================================

            if int(
                member["channel_2_joined"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "channel 2 not joined | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # ACCESS GRANTED
            # =================================================

            if int(
                member["access_granted"] or 0
            ) != 1:

                logger.warning(
                    "Group Music access denied: "
                    "access_granted=0 | group=%s | user=%s",
                    group_id,
                    user_id,
                )

                return None

            # =================================================
            # SUBSCRIPTION
            # =================================================

            now_text = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.gmtime(),
            )

            cursor = await db.execute(
                """
                SELECT
                    id,
                    group_id,
                    purchased_by,
                    price,
                    started_at,
                    expires_at,
                    status,
                    payment_ref
                FROM group_music_subscriptions
                WHERE group_id = ?
                  AND status = 'active'
                  AND expires_at > ?
                ORDER BY expires_at DESC
                LIMIT 1
                """,
                (
                    group_id,
                    now_text,
                ),
            )

            subscription = await cursor.fetchone()

        # =====================================================
        # SUBSCRIPTION CHECK
        # =====================================================

        if GROUP_MUSIC_TEST_MODE:

            logger.info(
                "Group Music TEST MODE access granted | "
                "room=%s | group=%s | user=%s",
                room.get("room_id"),
                group_id,
                user_id,
            )

        elif not subscription:

            logger.warning(
                "Group Music access denied: "
                "no active subscription | "
                "group=%s | user=%s",
                group_id,
                user_id,
            )

            return None

        # =====================================================
        # ACCESS GRANTED
        # =====================================================

        return {
            "group": dict(group),

            "member": dict(member),

            "subscription": (
                dict(subscription)
                if subscription
                else None
            ),
        }

    except Exception:

        logger.exception(
            "Failed to verify Group Music access | "
            "group=%s | user=%s",
            group_id,
            user_id,
        )

        return None
# =========================================================
# GROUP MUSIC ROOM MEMBERS
# =========================================================

async def get_group_music_room_member_count(
    room_id: str,
) -> int:
    try:
        async with aiosqlite.connect(
            DB_PATH
        ) as db:

            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM group_music_room_members
                WHERE room_id = ?
                """,
                (
                    room_id,
                ),
            )

            row = await cursor.fetchone()

        if not row:
            return 0

        try:
            return int(
                row[0]
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    except Exception:
        logger.exception(
            "Failed to count Group Music Room members | room=%s",
            room_id,
        )

        return 0


async def add_group_music_room_member(
    room_id: str,
    user_id: int,
):
    """
    Add a user to the persistent Group Music Room.

    Returns:

        True
        False
        "full"
    """

    room = await get_group_music_room(
        room_id
    )

    if not room:
        return False

    try:
        user_id = int(
            user_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    try:
        async with aiosqlite.connect(
            DB_PATH,
            timeout=30,
        ) as db:

            # -------------------------------------------------
            # Check existing member
            # -------------------------------------------------

            cursor = await db.execute(
                """
                SELECT 1
                FROM group_music_room_members
                WHERE room_id = ?
                AND user_id = ?
                LIMIT 1
                """,
                (
                    room_id,
                    user_id,
                ),
            )

            existing = await cursor.fetchone()

            if existing:
                return True

            # -------------------------------------------------
            # Capacity check
            # -------------------------------------------------

            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM group_music_room_members
                WHERE room_id = ?
                """,
                (
                    room_id,
                ),
            )

            row = await cursor.fetchone()

            try:
                count = (
                    int(
                        row[0]
                    )
                    if row
                    else 0
                )
            except (
                TypeError,
                ValueError,
            ):
                count = 0

            if count >= GROUP_MUSIC_MAX_USERS:
                return "full"

            # -------------------------------------------------
            # Insert
            # -------------------------------------------------

            await db.execute(
                """
                INSERT OR IGNORE INTO
                group_music_room_members
                (
                    room_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    room_id,
                    user_id,
                ),
            )

            await db.commit()

        return True

    except Exception:
        logger.exception(
            "Failed to add Group Music Room member | "
            "room=%s | user=%s",
            room_id,
            user_id,
        )

        return False


async def remove_group_music_room_member(
    room_id: str,
    user_id: int,
):
    try:
        user_id = int(
            user_id
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    try:
        async with aiosqlite.connect(
            DB_PATH,
            timeout=30,
        ) as db:

            cursor = await db.execute(
                """
                DELETE FROM
                group_music_room_members
                WHERE room_id = ?
                AND user_id = ?
                """,
                (
                    room_id,
                    user_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

    except Exception:
        logger.exception(
            "Failed to remove Group Music Room member | "
            "room=%s | user=%s",
            room_id,
            user_id,
        )

        return False


async def leave_group_music_room_from_websocket(
    room_id,
    user_id,
):
    if not is_group_music_room(
        room_id
    ):
        return False

    return await remove_group_music_room_member(
        room_id,
        user_id,
    )


# =========================================================
# WEBSOCKET MANAGER
# =========================================================

class MusicWebSocketManager:

    def __init__(self):
        self.connections = {}
        self.room_states = {}
        self.room_users = {}

    # =====================================================
    # INITIAL STATE
    # =====================================================

    def initial_state(self):

        return {
            "version": 0,

            "track_id": None,

            "url": None,

            "title": "",

            "artist": "",

            "duration": 0,

            "is_playing": False,

            "position": 0,

            "changed_at": time.time(),

            "volume": 0.8,
        }

    # =====================================================
    # ENSURE ROOM STATE
    # =====================================================

    def ensure_room_state(
        self,
        room_id,
    ):

        if room_id not in self.room_states:

            self.room_states[
                room_id
            ] = self.initial_state()

        return self.room_states[
            room_id
        ]

    # =====================================================
    # CONNECT
    # =====================================================

    async def connect(
        self,
        websocket,
        room_id,
        user,
    ):

        # -------------------------------------------------
        # Validate user ID
        # -------------------------------------------------

        try:
            user_id = int(
                user.get(
                    "id"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            await websocket.close(
                code=4003
            )
            return False

        user["id"] = user_id

        # -------------------------------------------------
        # GROUP CAPACITY
        # -------------------------------------------------

        if is_group_music_room(
            room_id
        ):

            current_connections = len(
                self.connections.get(
                    room_id,
                    [],
                )
            )

            same_user_connected = any(
                int(
                    item.get(
                        "user",
                        {},
                    ).get(
                        "id",
                        -1,
                    )
                )
                == user_id
                for item in self.connections.get(
                    room_id,
                    [],
                )
            )

            if (
                current_connections
                >= GROUP_MUSIC_MAX_USERS
                and not same_user_connected
            ):

                try:
                    await websocket.close(
                        code=4029
                    )
                except Exception:
                    pass

                return False

        # -------------------------------------------------
        # Accept
        # -------------------------------------------------

        await websocket.accept()

        self.connections.setdefault(
            room_id,
            [],
        )

        self.room_users.setdefault(
            room_id,
            [],
        )

        state = self.ensure_room_state(
            room_id
        )

        # -------------------------------------------------
        # Remove previous connection of same user
        # -------------------------------------------------

        old_connections = []

        for item in list(
            self.connections[
                room_id
            ]
        ):

            old_user = item.get(
                "user",
                {},
            )

            try:
                old_user_id = int(
                    old_user.get(
                        "id"
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                old_user_id = None

            if old_user_id == user_id:

                old_connections.append(
                    item
                )

        for item in old_connections:

            old_websocket = item.get(
                "websocket"
            )

            if old_websocket is not None:

                try:
                    if (
                        old_websocket
                        is not websocket
                    ):
                        await old_websocket.close(
                            code=4001
                        )
                except Exception:
                    pass

            if item in self.connections.get(
                room_id,
                [],
            ):
                self.connections[
                    room_id
                ].remove(
                    item
                )

        # -------------------------------------------------
        # Add connection
        # -------------------------------------------------

        self.connections[
            room_id
        ].append(
            {
                "websocket": websocket,
                "user": dict(user),
            }
        )

        # -------------------------------------------------
        # Update users
        # -------------------------------------------------

        existing_users = []

        for existing_user in self.room_users.get(
            room_id,
            [],
        ):

            try:
                existing_id = int(
                    existing_user.get(
                        "id"
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                existing_id = None

            if existing_id != user_id:
                existing_users.append(
                    existing_user
                )

        existing_users.append(
            dict(user)
        )

        self.room_users[
            room_id
        ] = existing_users

        logger.info(
            "Music WS connected | "
            "room=%s | user=%s | role=%s | connections=%s",
            room_id,
            user_id,
            user.get(
                "role",
                "guest",
            ),
            len(
                self.connections.get(
                    room_id,
                    [],
                )
            ),
        )

        # -------------------------------------------------
        # Current state
        # -------------------------------------------------

        try:

            await websocket.send_json(
                {
                    "type": "state",

                    "data": dict(
                        state
                    ),

                    "state": dict(
                        state
                    ),
                }
            )

        except Exception:

            self._remove_connection(
                websocket,
                room_id,
            )

            raise

        await self.broadcast_users(
            room_id
        )

        return True

    # =====================================================
    # INTERNAL REMOVE CONNECTION
    # =====================================================

    def _remove_connection(
        self,
        websocket,
        room_id,
    ):

        items = self.connections.get(
            room_id,
            [],
        )

        removed_user_ids = set()

        remaining = []

        for item in items:

            if (
                item.get("websocket")
                is websocket
            ):

                user = item.get(
                    "user",
                    {},
                )

                user_id = user.get(
                    "id"
                )

                if user_id is not None:
                    removed_user_ids.add(
                        user_id
                    )

            else:
                remaining.append(
                    item
                )

        if remaining:

            self.connections[
                room_id
            ] = remaining

        else:

            self.connections.pop(
                room_id,
                None,
            )

        if room_id in self.room_users:

            current_users = []

            active_user_ids = {
                item.get(
                    "user",
                    {},
                ).get(
                    "id"
                )

                for item in self.connections.get(
                    room_id,
                    [],
                )
            }

            for user in self.room_users[
                room_id
            ]:

                user_id = user.get(
                    "id"
                )

                if (
                    user_id in removed_user_ids
                    and user_id not in active_user_ids
                ):
                    continue

                current_users.append(
                    user
                )

            if current_users:

                self.room_users[
                    room_id
                ] = current_users

            else:

                self.room_users.pop(
                    room_id,
                    None,
                )

        return bool(
            removed_user_ids
        )

    # =====================================================
    # DISCONNECT
    # =====================================================

    async def disconnect(
        self,
        websocket,
        room_id,
    ):

        removed = self._remove_connection(
            websocket,
            room_id,
        )

        if not removed:
            return

        logger.info(
            "Music WS disconnected | "
            "room=%s | remaining=%s",
            room_id,
            len(
                self.connections.get(
                    room_id,
                    [],
                )
            ),
        )

        if (
            room_id in self.connections
            and self.connections[
                room_id
            ]
        ):

            await self.broadcast_users(
                room_id
            )

        else:

            self.room_users.pop(
                room_id,
                None,
            )

    # =====================================================
    # BUILD USERS
    # =====================================================

    def build_users_payload(
        self,
        room_id,
    ):

        users = list(
            self.room_users.get(
                room_id,
                [],
            )
        )

        active_user_ids = {
            item.get(
                "user",
                {},
            ).get(
                "id"
            )

            for item in self.connections.get(
                room_id,
                [],
            )
        }

        result = []

        for user in users:

            user_id = user.get(
                "id"
            )

            online = (
                user_id
                in active_user_ids
            )

            result.append(
                {
                    "id": user_id,

                    "name": user.get(
                        "name",
                        "کاربر",
                    ),

                    "username": user.get(
                        "username"
                    ),

                    "avatar": user.get(
                        "avatar"
                    ),

                    "role": user.get(
                        "role",
                        "guest",
                    ),

                    "online": online,
                }
            )

        return {
            "type": "room_users",

            "data": result,

            "users": result,

            "count": len(
                result
            ),

            "max_users": (
                GROUP_MUSIC_MAX_USERS
                if is_group_music_room(
                    room_id
                )
                else None
            ),
        }

    # =====================================================
    # BROADCAST USERS
    # =====================================================

    async def broadcast_users(
        self,
        room_id,
    ):

        payload = self.build_users_payload(
            room_id
        )

        await self.broadcast(
            room_id,
            payload,
        )

    # =====================================================
    # BROADCAST
    # =====================================================

    async def broadcast(
        self,
        room_id,
        payload,
    ):

        items = list(
            self.connections.get(
                room_id,
                [],
            )
        )

        if not items:
            return

        dead = []

        for item in items:

            websocket = item.get(
                "websocket"
            )

            if websocket is None:
                continue

            try:

                await websocket.send_json(
                    payload
                )

            except Exception:

                dead.append(
                    websocket
                )

        removed_any = False

        for websocket in dead:

            removed = self._remove_connection(
                websocket,
                room_id,
            )

            if removed:
                removed_any = True

        if (
            removed_any
            and room_id in self.connections
            and self.connections[
                room_id
            ]
        ):

            users_payload = (
                self.build_users_payload(
                    room_id
                )
            )

            for item in list(
                self.connections.get(
                    room_id,
                    [],
                )
            ):

                websocket = item.get(
                    "websocket"
                )

                if websocket is None:
                    continue

                try:

                    await websocket.send_json(
                        users_payload
                    )

                except Exception:

                    self._remove_connection(
                        websocket,
                        room_id,
                    )

    # =====================================================
    # UPDATE STATE
    # =====================================================

    async def update_state(
        self,
        room_id,
        changes,
    ):

        state = self.ensure_room_state(
            room_id
        )

        if isinstance(
            changes,
            dict,
        ):

            state.update(
                changes
            )

        try:

            current_version = int(
                state.get(
                    "version",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            current_version = 0

        state[
            "version"
        ] = (
            current_version + 1
        )

        state[
            "changed_at"
        ] = time.time()

        state_copy = dict(
            state
        )

        await self.broadcast(
            room_id,
            {
                "type": "state",

                "data": state_copy,

                "state": state_copy,
            },
        )

        return state_copy

    # =====================================================
    # CLOSE ROOM
    # =====================================================

    async def close_room_connections(
        self,
        room_id,
        reason="room_closed",
    ):

        items = list(
            self.connections.get(
                room_id,
                [],
            )
        )

        for item in items:

            websocket = item.get(
                "websocket"
            )

            if websocket is None:
                continue

            try:

                await websocket.send_json(
                    {
                        "type": "room_closed",

                        "reason": reason,
                    }
                )

            except Exception:
                pass

        for item in items:

            websocket = item.get(
                "websocket"
            )

            if websocket is None:
                continue

            try:

                await websocket.close(
                    code=4002
                )

            except Exception:
                pass

        self.connections.pop(
            room_id,
            None,
        )

        self.room_users.pop(
            room_id,
            None,
        )

    # =====================================================
    # REMOVE ONE USER
    # =====================================================

    async def remove_user(
        self,
        room_id,
        user_id,
    ):

        try:
            user_id = int(
                user_id
            )
        except (
            TypeError,
            ValueError,
        ):
            return

        items = list(
            self.connections.get(
                room_id,
                [],
            )
        )

        removed = False

        for item in items:

            item_user = item.get(
                "user",
                {},
            )

            if (
                item_user.get("id")
                != user_id
            ):
                continue

            websocket = item.get(
                "websocket"
            )

            if websocket is not None:

                try:

                    await websocket.send_json(
                        {
                            "type": "room_left",
                        }
                    )

                except Exception:
                    pass

                try:

                    await websocket.close(
                        code=4000
                    )

                except Exception:
                    pass

                self._remove_connection(
                    websocket,
                    room_id,
                )

                removed = True

        if room_id in self.room_users:

            self.room_users[
                room_id
            ] = [
                user

                for user in self.room_users[
                    room_id
                ]

                if user.get(
                    "id"
                ) != user_id
            ]

            if not self.room_users[
                room_id
            ]:

                self.room_users.pop(
                    room_id,
                    None,
                )

        if (
            removed
            and room_id in self.connections
            and self.connections[
                room_id
            ]
        ):

            await self.broadcast_users(
                room_id
            )

    # =====================================================
    # GET USER CONNECTION
    # =====================================================

    def get_user_connection(
        self,
        room_id,
        user_id,
    ):

        for item in self.connections.get(
            room_id,
            [],
        ):

            user = item.get(
                "user",
                {},
            )

            if (
                user.get("id")
                == user_id
            ):

                return item

        return None


manager = MusicWebSocketManager()


# =========================================================
# SAFE VALUES
# =========================================================

def safe_position(
    value,
):

    try:

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):
            return 0

        return max(
            0,
            value,
        )

    except Exception:

        return 0


def safe_volume(
    value,
):

    try:

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):
            return 0.8

        return min(
            1,
            max(
                0,
                value,
            ),
        )

    except Exception:

        return 0.8


def safe_track_id(
    value,
):

    try:

        track_id = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if track_id <= 0:
        return None

    return track_id


# =========================================================
# SAFE ROOM ID
# =========================================================

def safe_room_id(
    room_id,
):

    if room_id is None:
        return ""

    room_id = str(
        room_id
    ).strip()

    if not room_id:
        return ""

    if len(room_id) > 128:
        return ""

    return room_id


# =========================================================
# MESSAGE DATA NORMALIZER
# =========================================================

def get_message_data(
    message,
):

    if not isinstance(
        message,
        dict,
    ):
        return {}

    nested = message.get(
        "data"
    )

    if isinstance(
        nested,
        dict,
    ):

        data = dict(
            nested
        )

    else:

        data = {}

    supported_fields = {
        "track_id",
        "trackId",

        "url",

        "title",

        "artist",

        "duration",

        "position",

        "volume",

        "client_time",
    }

    for key in supported_fields:

        if key in message:

            data[key] = message.get(
                key
            )

    if (
        "track_id" not in data
        and "trackId" in data
    ):

        data["track_id"] = data.get(
            "trackId"
        )

    return data


# =========================================================
# DATABASE ROOM LEAVE
# =========================================================

async def leave_music_room_from_websocket(
    room_id,
    user_id,
):

    # -----------------------------------------------------
    # GROUP MUSIC ROOM
    # -----------------------------------------------------

    if is_group_music_room(
        room_id
    ):

        return await leave_group_music_room_from_websocket(
            room_id,
            user_id,
        )

    # -----------------------------------------------------
    # DEV
    # -----------------------------------------------------

    if room_id == DEV_ROOM_ID:

        try:

            user_id = int(
                user_id
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

        if user_id == DEV_USERS[
            "1"
        ][
            "id"
        ]:

            return "creator"

        if user_id == DEV_USERS[
            "2"
        ][
            "id"
        ]:

            return "guest"

        return None

    # -----------------------------------------------------
    # NORMAL MUSIC ROOM
    # -----------------------------------------------------

    room = await get_music_room(
        room_id=room_id
    )

    if not room:
        return None

    try:

        normalized_user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    now = int(
        time.time()
    )

    try:

        creator_id = int(
            room[
                "creator_id"
            ]
        )

    except (
        TypeError,
        ValueError,
        KeyError,
    ):

        creator_id = None

    if (
        creator_id is not None
        and creator_id
        == normalized_user_id
    ):

        async with aiosqlite.connect(
            DB_PATH,
            timeout=30,
        ) as db:

            await db.execute(
                """
                UPDATE music_rooms
                SET
                    status = 'cancelled',
                    closed_at = ?,
                    updated_at = ?
                WHERE room_id = ?
                AND status NOT IN (
                    'cancelled',
                    'rejected',
                    'closed'
                )
                """,
                (
                    now,
                    now,
                    room_id,
                ),
            )

            await db.commit()

        return "creator"

    guest_id = room.get(
        "guest_id"
    )

    if guest_id is not None:

        try:

            guest_id = int(
                guest_id
            )

        except (
            TypeError,
            ValueError,
        ):

            guest_id = None

    if (
        guest_id is not None
        and guest_id
        == normalized_user_id
    ):

        current_status = str(
            room.get(
                "status",
                "",
            )
        ).lower()

        if current_status == "active":

            async with aiosqlite.connect(
                DB_PATH,
                timeout=30,
            ) as db:

                await db.execute(
                    """
                    UPDATE music_rooms
                    SET
                        guest_id = NULL,
                        guest_ready = 0,
                        updated_at = ?
                    WHERE room_id = ?
                    AND guest_id = ?
                    AND status = 'active'
                    """,
                    (
                        now,
                        room_id,
                        normalized_user_id,
                    ),
                )

                await db.commit()

            return "guest"

        if current_status == "accepted":

            async with aiosqlite.connect(
                DB_PATH,
                timeout=30,
            ) as db:

                await db.execute(
                    """
                    UPDATE music_rooms
                    SET
                        guest_id = NULL,
                        guest_ready = 0,
                        status = 'waiting',
                        accepted_at = NULL,
                        updated_at = ?
                    WHERE room_id = ?
                    AND guest_id = ?
                    AND status = 'accepted'
                    """,
                    (
                        now,
                        room_id,
                        normalized_user_id,
                    ),
                )

                await db.commit()

            return "guest"

    return None


# =========================================================
# BUILD DEV USER
# =========================================================

def build_dev_user(
    dev_user,
    role,
):

    user = get_dev_user(
        dev_user
    )

    if not user:
        return None

    return {
        "id": user[
            "id"
        ],

        "name": user.get(
            "name",
            "کاربر تست",
        ),

        "username": user.get(
            "username"
        ),

        "avatar": user.get(
            "avatar"
        ),

        "role": role,
    }


# =========================================================
# BUILD TELEGRAM USER
# =========================================================

def build_telegram_user(
    telegram_user,
    db_user,
    telegram_id,
    role,
):

    display_name = None

    if db_user:

        display_name = db_user.get(
            "display_name"
        )

    if not display_name:

        display_name = (
            telegram_user.get(
                "first_name"
            )

            or telegram_user.get(
                "username"
            )

            or "کاربر"
        )

    username = None

    if db_user:

        username = db_user.get(
            "username"
        )

    if not username:

        username = telegram_user.get(
            "username"
        )

    avatar = None

    if db_user:

        avatar = db_user.get(
            "avatar_file_id"
        )

    return {
        "id": telegram_id,

        "name": display_name,

        "username": username,

        "avatar": avatar,

        "role": role,
    }


# =========================================================
# ROOM ROLE
# =========================================================

def get_room_role(
    room,
    user_id,
):

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    try:

        creator_id = int(
            room[
                "creator_id"
            ]
        )

    except (
        TypeError,
        ValueError,
        KeyError,
    ):

        creator_id = None

    if (
        creator_id is not None
        and user_id == creator_id
    ):

        return "creator"

    guest_id = room.get(
        "guest_id"
    )

    if guest_id is not None:

        try:

            guest_id = int(
                guest_id
            )

        except (
            TypeError,
            ValueError,
        ):

            guest_id = None

    if (
        guest_id is not None
        and user_id == guest_id
    ):

        return "guest"

    if is_group_music_room(
        room.get(
            "room_id",
            "",
        )
    ):

        return "member"

    return None


# =========================================================
# MUSIC WEBSOCKET
# =========================================================

async def music_websocket(
    websocket: WebSocket,
    room_id: str,
    token: str,
    init_data: str,
    dev_user: str = "",
    dev_mode: bool = False,
):

    room_id = safe_room_id(
        room_id
    )

    if not room_id:

        await websocket.close(
            code=4004
        )

        return

    real_user = None

    is_group_room = is_group_music_room(
        room_id
    )

    # =====================================================
    # LOAD ROOM
    # =====================================================

    room = None

    # -----------------------------------------------------
    # DEV synthetic room
    # -----------------------------------------------------

    if (
        dev_mode
        and room_id == DEV_ROOM_ID
    ):

        room = get_dev_room()

    # -----------------------------------------------------
    # GROUP MUSIC ROOM
    # -----------------------------------------------------

    elif is_group_room:

        room = await get_group_music_room(
            room_id
        )

    # -----------------------------------------------------
    # NORMAL DB ROOM
    # -----------------------------------------------------

    else:

        try:

            room = await get_music_room(
                room_id=room_id
            )

        except Exception:

            logger.exception(
                "Failed to load music room | room=%s",
                room_id,
            )

            await websocket.close(
                code=1011
            )

            return

    # -----------------------------------------------------
    # ROOM NOT FOUND
    # -----------------------------------------------------

    if not room:

        await websocket.close(
            code=4004
        )

        return

    # =====================================================
    # ROOM STATUS
    # =====================================================

    status = str(
        room.get(
            "status",
            "",
        )
    ).lower()

    if status not in {
        "active",
        "accepted",
    }:

        logger.warning(
            "Music WS rejected because room is not active | "
            "room=%s | status=%s",
            room_id,
            status,
        )

        await websocket.close(
            code=4003
        )

        return

    # =====================================================
    # DEV
    # =====================================================

    if (
        dev_mode
        and dev_user
    ):

        if not is_local_dev_connection(
            websocket
        ):

            await websocket.close(
                code=4003
            )

            return

        user = get_dev_user(
            dev_user
        )

        if not user:

            await websocket.close(
                code=4003
            )

            return

        role = get_room_role(
            room,
            user[
                "id"
            ],
        )

        if room_id == DEV_ROOM_ID:

            if str(
                dev_user
            ) == "1":

                role = "creator"

            elif str(
                dev_user
            ) == "2":

                role = "guest"

            else:

                await websocket.close(
                    code=4003
                )

                return

        elif role is None:

            if str(
                dev_user
            ) == "1":

                role = "creator"

            elif str(
                dev_user
            ) == "2":

                role = "guest"

            else:

                await websocket.close(
                    code=4003
                )

                return

        if role not in {
            "creator",
            "guest",
            "member",
        }:

            await websocket.close(
                code=4003
            )

            return

        real_user = build_dev_user(
            dev_user,
            role,
        )

        if not real_user:

            await websocket.close(
                code=4003
            )

            return

        real_user[
            "db_id"
        ] = real_user[
            "id"
        ]

    # =====================================================
    # PRODUCTION
    # =====================================================

    else:

        bot_token = os.getenv(
            "BOT_TOKEN",
            "",
        ).strip()

        if not bot_token:

            logger.error(
                "BOT_TOKEN is missing while production "
                "Music WebSocket was requested."
            )

            await websocket.close(
                code=1011
            )

            return

        # -------------------------------------------------
        # Telegram initData
        # -------------------------------------------------

        telegram_user = (
            verify_telegram_init_data(
                init_data,
                bot_token,
            )
        )

        if not telegram_user:

            logger.warning(
                "Music WS invalid Telegram initData | room=%s",
                room_id,
            )

            await websocket.close(
                code=4003
            )

            return

        try:

            telegram_id = int(
                telegram_user[
                    "id"
                ]
            )

        except (
            TypeError,
            ValueError,
            KeyError,
        ):

            await websocket.close(
                code=4003
            )

            return

        # =================================================
        # GROUP MUSIC ACCESS
        # =================================================

        if is_group_room:

            access = await get_group_music_access(
                room,
                telegram_id,
            )

            if not access:

                logger.warning(
                    "Group Music access denied | "
                    "room=%s | group=%s | user=%s",
                    room_id,
                    room.get(
                        "group_id"
                    ),
                    telegram_id,
                )

                await websocket.close(
                    code=4003
                )

                return

            # -------------------------------------------------
            # Persistent membership / capacity
            # -------------------------------------------------

            joined = await add_group_music_room_member(
                room_id,
                telegram_id,
            )

            if joined == "full":

                logger.info(
                    "Group Music Room full | "
                    "room=%s | user=%s | limit=%s",
                    room_id,
                    telegram_id,
                    GROUP_MUSIC_MAX_USERS,
                )

                try:

                    await websocket.close(
                        code=4029
                    )

                except Exception:
                    pass

                return

            if not joined:

                logger.error(
                    "Failed to register Group Music member | "
                    "room=%s | user=%s",
                    room_id,
                    telegram_id,
                )

                await websocket.close(
                    code=4003
                )

                return

            # -------------------------------------------------
            # Role
            # -------------------------------------------------

            role = "member"

            try:

                creator_id = int(
                    room.get(
                        "creator_id"
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                creator_id = None

            if (
                creator_id is not None
                and telegram_id == creator_id
            ):

                role = "creator"

            # -------------------------------------------------
            # Database user
            # -------------------------------------------------

            try:

                db_user = (
                    await get_user_by_telegram_id(
                        telegram_id
                    )
                )

            except Exception:

                logger.exception(
                    "Failed to load Telegram user | telegram_id=%s",
                    telegram_id,
                )

                await remove_group_music_room_member(
                    room_id,
                    telegram_id,
                )

                await websocket.close(
                    code=1011
                )

                return

            real_user = build_telegram_user(
                telegram_user,
                db_user,
                telegram_id,
                role,
            )

            real_user[
                "db_id"
            ] = telegram_id

            real_user[
                "group_id"
            ] = room.get(
                "group_id"
            )

            real_user[
                "group_title"
            ] = room.get(
                "group_title"
            )

        # =================================================
        # NORMAL MUSIC ROOM ACCESS
        # =================================================

        else:

            # -------------------------------------------------
            # Normal rooms still require invite token.
            # -------------------------------------------------

            if not token:

                await websocket.close(
                    code=4003
                )

                return

            room_token = str(
                room.get(
                    "invite_token",
                    "",
                )
            )

            if not room_token:

                await websocket.close(
                    code=4003
                )

                return

            try:

                token_matches = hmac.compare_digest(
                    str(token),
                    room_token,
                )

            except Exception:

                token_matches = False

            if not token_matches:

                logger.warning(
                    "Music WS invalid room token | room=%s",
                    room_id,
                )

                await websocket.close(
                    code=4003
                )

                return

            role = get_room_role(
                room,
                telegram_id,
            )

            if role is None:

                logger.warning(
                    "Music WS user is not a room member | "
                    "room=%s | user=%s",
                    room_id,
                    telegram_id,
                )

                await websocket.close(
                    code=4003
                )

                return

            try:

                db_user = (
                    await get_user_by_telegram_id(
                        telegram_id
                    )
                )

            except Exception:

                logger.exception(
                    "Failed to load Telegram user | telegram_id=%s",
                    telegram_id,
                )

                await websocket.close(
                    code=1011
                )

                return

            real_user = build_telegram_user(
                telegram_user,
                db_user,
                telegram_id,
                role,
            )

            real_user[
                "db_id"
            ] = telegram_id

    # =====================================================
    # CONNECT TO MANAGER
    # =====================================================

    try:

        connected = await manager.connect(
            websocket,
            room_id,
            real_user,
        )

        if connected is False:

            if is_group_room:

                try:

                    await remove_group_music_room_member(
                        room_id,
                        real_user.get(
                            "db_id",
                            real_user.get(
                                "id"
                            ),
                        ),
                    )

                except Exception:
                    pass

            return

    except Exception as e:

        logger.exception(
            "Music WebSocket connect error | "
            "room=%s | user=%s | error=%s",
            room_id,
            real_user.get(
                "id",
                "?",
            )
            if real_user
            else "?",
            e,
        )

        if is_group_room and real_user:

            try:

                await remove_group_music_room_member(
                    room_id,
                    real_user.get(
                        "db_id",
                        real_user.get(
                            "id"
                        ),
                    ),
                )

            except Exception:
                pass

        try:

            await websocket.close(
                code=1011
            )

        except Exception:
            pass

        return

    # =====================================================
    # MESSAGE LOOP
    # =====================================================

    try:

        while True:

            message = (
                await websocket.receive_json()
            )

            if not isinstance(
                message,
                dict,
            ):
                continue

            event_type = message.get(
                "type"
            )

            if not isinstance(
                event_type,
                str,
            ):
                continue

            event_type = (
                event_type
                .strip()
                .lower()
            )

            data = get_message_data(
                message
            )

            # =================================================
            # PING
            # =================================================

            if event_type == "ping":

                await websocket.send_json(
                    {
                        "type": "pong",

                        "server_time": time.time(),

                        "client_time": data.get(
                            "client_time"
                        ),
                    }
                )

                continue

            # =================================================
            # SYNC REQUEST
            # =================================================

            if event_type == "sync_request":

                state = (
                    manager.room_states.get(
                        room_id
                    )
                )

                if state is None:

                    state = (
                        manager.initial_state()
                    )

                state_copy = dict(
                    state
                )

                await websocket.send_json(
                    {
                        "type": "state",

                        "data": state_copy,

                        "state": state_copy,
                    }
                )

                continue

            # =================================================
            # PLAY
            # =================================================

            if event_type == "play":

                state = (
                    manager.room_states.get(
                        room_id
                    )
                )

                if state is None:
                    state = manager.initial_state()

                track_id = safe_track_id(
                    state.get(
                        "track_id"
                    )
                )

                if track_id is None:
                    continue

                position = safe_position(
                    data.get(
                        "position",
                        state.get(
                            "position",
                            0,
                        ),
                    )
                )

                track = await get_music_track(
                    track_id
                )

                if not track:

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "آهنگ فعلی پیدا نشد."
                            ),
                        }
                    )

                    continue

                try:

                    duration = float(
                        track.get(
                            "duration"
                        )
                        or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    duration = 0

                if (
                    duration > 0
                    and position > duration
                ):

                    position = duration

                await manager.update_state(
                    room_id,
                    {
                        "track_id": track_id,

                        "is_playing": True,

                        "position": position,
                    },
                )

                continue

            # =================================================
            # PAUSE
            # =================================================

            if event_type == "pause":

                state = (
                    manager.room_states.get(
                        room_id
                    )
                )

                if state is None:
                    state = manager.initial_state()

                track_id = safe_track_id(
                    state.get(
                        "track_id"
                    )
                )

                if track_id is None:
                    continue

                position = safe_position(
                    data.get(
                        "position",
                        state.get(
                            "position",
                            0,
                        ),
                    )
                )

                track = await get_music_track(
                    track_id
                )

                if not track:

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "آهنگ فعلی پیدا نشد."
                            ),
                        }
                    )

                    continue

                try:

                    duration = float(
                        track.get(
                            "duration"
                        )
                        or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    duration = 0

                if (
                    duration > 0
                    and position > duration
                ):

                    position = duration

                await manager.update_state(
                    room_id,
                    {
                        "track_id": track_id,

                        "is_playing": False,

                        "position": position,
                    },
                )

                continue

            # =================================================
            # SEEK
            # =================================================

            if event_type == "seek":

                state = (
                    manager.room_states.get(
                        room_id
                    )
                )

                if state is None:
                    state = manager.initial_state()

                track_id = safe_track_id(
                    state.get(
                        "track_id"
                    )
                )

                if track_id is None:
                    continue

                position = safe_position(
                    data.get(
                        "position",
                        0,
                    )
                )

                track = await get_music_track(
                    track_id
                )

                if not track:

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "آهنگ فعلی پیدا نشد."
                            ),
                        }
                    )

                    continue

                try:

                    duration = float(
                        track.get(
                            "duration"
                        )
                        or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    duration = 0

                if (
                    duration > 0
                    and position > duration
                ):

                    position = duration

                await manager.update_state(
                    room_id,
                    {
                        "position": position,
                    },
                )

                continue

            # =================================================
            # TRACK
            # =================================================

            if event_type == "track":

                track_id = safe_track_id(
                    data.get(
                        "track_id"
                    )
                )

                if track_id is None:

                    logger.warning(
                        "Invalid track_id received | "
                        "room=%s | user=%s | message=%s",
                        room_id,
                        real_user.get(
                            "id",
                            "?",
                        )
                        if real_user
                        else "?",
                        message,
                    )

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "شناسه آهنگ نامعتبر است."
                            ),
                        }
                    )

                    continue

                track = (
                    await get_music_track(
                        track_id
                    )
                )

                if not track:

                    logger.warning(
                        "Music track not found | "
                        "room=%s | track_id=%s | user=%s",
                        room_id,
                        track_id,
                        real_user.get(
                            "id",
                            "?",
                        )
                        if real_user
                        else "?",
                    )

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "این آهنگ پیدا نشد."
                            ),
                        }
                    )

                    continue

                file_url = str(
                    track.get(
                        "file_url"
                    )
                    or ""
                ).strip()

                if not file_url:

                    await websocket.send_json(
                        {
                            "type": "error",

                            "message": (
                                "فایل این آهنگ در دسترس نیست."
                            ),
                        }
                    )

                    continue

                try:

                    duration = float(
                        track.get(
                            "duration"
                        )
                        or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    duration = 0

                if not math.isfinite(
                    duration
                ):

                    duration = 0

                await manager.update_state(
                    room_id,
                    {
                        "track_id": int(
                            track[
                                "id"
                            ]
                        ),

                        "url": file_url,

                        "title": str(
                            track.get(
                                "title"
                            )
                            or ""
                        ),

                        "artist": str(
                            track.get(
                                "artist"
                            )
                            or ""
                        ),

                        "duration": duration,

                        "position": 0,

                        "is_playing": False,
                    },
                )

                logger.info(
                    "Music track changed | "
                    "room=%s | track_id=%s | title=%s | user=%s",
                    room_id,
                    track[
                        "id"
                    ],
                    track.get(
                        "title",
                        "",
                    ),
                    real_user.get(
                        "id",
                        "?",
                    )
                    if real_user
                    else "?",
                )

                continue

            # =================================================
            # VOLUME
            # =================================================

            if event_type == "volume":

                volume = safe_volume(
                    data.get(
                        "volume"
                    )
                )

                await manager.update_state(
                    room_id,
                    {
                        "volume": volume,
                    },
                )

                continue

            # =================================================
            # LEAVE
            # =================================================

            if event_type == "leave":

                leave_user_id = real_user.get(
                    "db_id",
                    real_user.get(
                        "id"
                    ),
                )

                # =================================================
                # GROUP MUSIC ROOM
                # =================================================

                if is_group_room:

                    removed_from_db = (
                        await leave_group_music_room_from_websocket(
                            room_id,
                            leave_user_id,
                        )
                    )

                    logger.info(
                        "Group Music user left | "
                        "room=%s | user=%s | removed=%s",
                        room_id,
                        leave_user_id,
                        removed_from_db,
                    )

                    try:

                        await websocket.send_json(
                            {
                                "type": "room_left",
                            }
                        )

                    except Exception:
                        pass

                    manager._remove_connection(
                        websocket,
                        room_id,
                    )

                    if (
                        room_id in manager.connections
                        and manager.connections[
                            room_id
                        ]
                    ):

                        await manager.broadcast_users(
                            room_id
                        )

                    break

                # =================================================
                # NORMAL MUSIC ROOM
                # =================================================

                leaving_role = (
                    await leave_music_room_from_websocket(
                        room_id,
                        leave_user_id,
                    )
                )

                if leaving_role == "creator":

                    await manager.close_room_connections(
                        room_id,
                        reason="creator_left",
                    )

                    break

                if leaving_role == "guest":

                    try:

                        await websocket.send_json(
                            {
                                "type": "room_left",
                            }
                        )

                    except Exception:
                        pass

                    manager._remove_connection(
                        websocket,
                        room_id,
                    )

                    if (
                        room_id in manager.connections
                        and manager.connections[
                            room_id
                        ]
                    ):

                        await manager.broadcast_users(
                            room_id
                        )

                    break

                try:

                    await websocket.send_json(
                        {
                            "type": "room_left",
                        }
                    )

                except Exception:
                    pass

                break

            # =================================================
            # UNKNOWN EVENT
            # =================================================

            logger.debug(
                "Unknown Music WS event | "
                "room=%s | user=%s | type=%s",
                room_id,
                real_user.get(
                    "id",
                    "?",
                )
                if real_user
                else "?",
                event_type,
            )

            continue

    # =====================================================
    # NORMAL DISCONNECT
    # =====================================================

    except WebSocketDisconnect:

        pass

    # =====================================================
    # OTHER ERROR
    # =====================================================

    except Exception as e:

        logger.exception(
            "Music WebSocket error | "
            "room=%s | user=%s | error=%s",
            room_id,
            real_user.get(
                "id",
                "?",
            )
            if real_user
            else "?",
            e,
        )

        try:

            await websocket.send_json(
                {
                    "type": "error",

                    "message": (
                        "ارتباط با Room دچار مشکل شد."
                    ),
                }
            )

        except Exception:
            pass

    # =====================================================
    # FINALLY
    # =====================================================

    finally:

        try:

            # -------------------------------------------------
            # Remove persistent Group Music membership
            # when the websocket connection disappears.
            #
            # This is important because the 20-user limit
            # represents currently active room participants.
            # -------------------------------------------------

            if (
                is_group_room
                and real_user
            ):

                leave_user_id = real_user.get(
                    "db_id",
                    real_user.get(
                        "id"
                    ),
                )

                try:

                    await remove_group_music_room_member(
                        room_id,
                        leave_user_id,
                    )

                except Exception:

                    logger.exception(
                        "Group Music persistent member cleanup failed | "
                        "room=%s | user=%s",
                        room_id,
                        leave_user_id,
                    )

            await manager.disconnect(
                websocket,
                room_id,
            )

        except Exception:

            logger.exception(
                "Music WebSocket cleanup error | room=%s",
                room_id,
            )