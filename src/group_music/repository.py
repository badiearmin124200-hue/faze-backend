import aiosqlite

from src.db.database import DB_PATH
from .queries import (
    ADD_ROOM_MEMBER,
    CREATE_GROUP,
    CREATE_ROOM,
    CREATE_SUBSCRIPTION,
    DEACTIVATE_GROUP,
    DEACTIVATE_ROOM,
    GET_ACTIVE_ROOM,
    GET_ACTIVE_SUBSCRIPTION,
    GET_GROUP,
    GET_MEMBER,
    UPSERT_MEMBER,
)
from .schema import init_group_music_tables


class GroupMusicRepository:

    async def _connect(self):
        db = await aiosqlite.connect(DB_PATH, timeout=30)
        db.row_factory = aiosqlite.Row
        await init_group_music_tables(db)
        return db

    async def create_or_update_group(
        self,
        group_id: int,
        title: str,
        added_by: int | None = None,
    ):
        db = await self._connect()
        try:
            await db.execute(
                CREATE_GROUP,
                (group_id, title, added_by),
            )
            await db.commit()

            cursor = await db.execute(
                GET_GROUP,
                (group_id,),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def get_group(self, group_id: int):
        db = await self._connect()
        try:
            cursor = await db.execute(
                GET_GROUP,
                (group_id,),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def deactivate_group(self, group_id: int):
        db = await self._connect()
        try:
            await db.execute(
                DEACTIVATE_GROUP,
                (group_id,),
            )
            await db.commit()
        finally:
            await db.close()

    async def upsert_member(
        self,
        group_id: int,
        user_id: int,
        bot_started: bool,
        channel_1_joined: bool,
        channel_2_joined: bool,
        access_granted: bool,
    ):
        db = await self._connect()
        try:
            await db.execute(
                UPSERT_MEMBER,
                (
                    group_id,
                    user_id,
                    int(bot_started),
                    int(channel_1_joined),
                    int(channel_2_joined),
                    int(access_granted),
                ),
            )
            await db.commit()

            cursor = await db.execute(
                GET_MEMBER,
                (group_id, user_id),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def get_member(
        self,
        group_id: int,
        user_id: int,
    ):
        db = await self._connect()
        try:
            cursor = await db.execute(
                GET_MEMBER,
                (group_id, user_id),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def create_subscription(
        self,
        group_id: int,
        purchased_by: int,
        price: int,
        started_at: str,
        expires_at: str,
        status: str = "active",
        payment_ref: str | None = None,
    ):
        db = await self._connect()
        try:
            cursor = await db.execute(
                CREATE_SUBSCRIPTION,
                (
                    group_id,
                    purchased_by,
                    price,
                    started_at,
                    expires_at,
                    status,
                    payment_ref,
                ),
            )
            await db.commit()

            subscription_id = cursor.lastrowid

            cursor = await db.execute(
                """
                SELECT *
                FROM group_music_subscriptions
                WHERE id = ?
                """,
                (subscription_id,),
            )

            return await cursor.fetchone()
        finally:
            await db.close()

    async def get_active_subscription(
        self,
        group_id: int,
    ):
        db = await self._connect()
        try:
            cursor = await db.execute(
                GET_ACTIVE_SUBSCRIPTION,
                (group_id,),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def create_room(
        self,
        group_id: int,
        room_id: str,
        created_by: int,
    ):
        db = await self._connect()
        try:
            await db.execute(
                CREATE_ROOM,
                (
                    group_id,
                    room_id,
                    created_by,
                ),
            )
            await db.commit()

            cursor = await db.execute(
                """
                SELECT *
                FROM group_music_rooms
                WHERE room_id = ?
                LIMIT 1
                """,
                (room_id,),
            )

            return await cursor.fetchone()
        finally:
            await db.close()

    async def get_active_room(
        self,
        group_id: int,
    ):
        db = await self._connect()
        try:
            cursor = await db.execute(
                GET_ACTIVE_ROOM,
                (group_id,),
            )
            return await cursor.fetchone()
        finally:
            await db.close()

    async def add_room_member(
        self,
        room_id: str,
        user_id: int,
    ):
        db = await self._connect()
        try:
            await db.execute(
                ADD_ROOM_MEMBER,
                (
                    room_id,
                    user_id,
                ),
            )
            await db.commit()
        finally:
            await db.close()

    async def deactivate_room(
        self,
        room_id: str,
    ):
        db = await self._connect()
        try:
            await db.execute(
                DEACTIVATE_ROOM,
                (room_id,),
            )
            await db.commit()
        finally:
            await db.close()


repository = GroupMusicRepository()