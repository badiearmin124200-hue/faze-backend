import aiosqlite
import secrets


DB_PATH = "faze.db"


# =========================================================
# DATABASE INIT
# =========================================================

async def init_db():

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        await db.execute(
            "PRAGMA journal_mode=WAL"
        )

        await db.execute(
            "PRAGMA foreign_keys=ON"
        )

        # =====================================================
        # FAZE USERS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,

                first_name TEXT,
                display_name TEXT,

                avatar_file_id TEXT,
                bio TEXT,

                age INTEGER,
                gender TEXT,
                city TEXT,

                interests TEXT NOT NULL DEFAULT '[]',
                personality TEXT NOT NULL DEFAULT '[]',

                favorite_artist TEXT,
                favorite_song TEXT,
                favorite_movie TEXT,
                favorite_series TEXT,
                favorite_game TEXT,
                favorite_team TEXT,
                favorite_book TEXT,

                current_status TEXT,

                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                streak INTEGER NOT NULL DEFAULT 0,
                coins INTEGER NOT NULL DEFAULT 0,

                is_premium INTEGER NOT NULL DEFAULT 0,
                premium_until TEXT,

                discoverable INTEGER NOT NULL DEFAULT 1,

                profile_completed INTEGER NOT NULL DEFAULT 0,
                profile_completion INTEGER NOT NULL DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # PROFILE ACHIEVEMENTS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,

                emoji TEXT,
                xp_reward INTEGER NOT NULL DEFAULT 0,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL,

                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (user_id, achievement_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (achievement_id)
                    REFERENCES achievements(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # PROFILE BADGES
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,

                emoji TEXT,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                user_id INTEGER NOT NULL,
                badge_id INTEGER NOT NULL,

                showcased INTEGER NOT NULL DEFAULT 0,

                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (user_id, badge_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (badge_id)
                    REFERENCES badges(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # USER SETTINGS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,

                show_age INTEGER NOT NULL DEFAULT 1,
                show_gender INTEGER NOT NULL DEFAULT 1,
                show_city INTEGER NOT NULL DEFAULT 1,
                show_favorites INTEGER NOT NULL DEFAULT 1,
                show_activity INTEGER NOT NULL DEFAULT 1,

                notifications_enabled INTEGER NOT NULL DEFAULT 1,

                language TEXT NOT NULL DEFAULT 'fa',

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # USER STATISTICS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,

                games_played INTEGER NOT NULL DEFAULT 0,
                games_won INTEGER NOT NULL DEFAULT 0,

                quizzes_completed INTEGER NOT NULL DEFAULT 0,
                challenges_completed INTEGER NOT NULL DEFAULT 0,

                matches_count INTEGER NOT NULL DEFAULT 0,
                referrals_count INTEGER NOT NULL DEFAULT 0,

                total_activity INTEGER NOT NULL DEFAULT 0,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # =====================================================
        # COMPATIBILITY PROFILES
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS compatibility_profiles (
                user_id INTEGER PRIMARY KEY,

                username TEXT,
                first_name TEXT,
                gender TEXT,
                age INTEGER,
                city TEXT,

                answers TEXT NOT NULL DEFAULT '{}',

                completed INTEGER NOT NULL DEFAULT 0,
                discoverable INTEGER NOT NULL DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # COMPATIBILITY REQUESTS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS compatibility_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(sender_id, receiver_id)
            )
        """)

        # =====================================================
        # COMPATIBILITY MATCHES
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS compatibility_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,

                score INTEGER NOT NULL DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user1_id, user2_id)
            )
        """)

        # =====================================================
        # CREDITS / PREMIUM
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS compatibility_credits (
                user_id INTEGER PRIMARY KEY,

                credits INTEGER NOT NULL DEFAULT 0,

                premium INTEGER NOT NULL DEFAULT 0,
                premium_until TEXT
            )
        """)

        # =====================================================
        # LIVE MODES
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS live_modes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,

                emoji TEXT NOT NULL,

                active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS live_mode_members (
                mode_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (mode_id, user_id)
            )
        """)

        # =====================================================
        # MUSIC LIBRARY
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS music_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                title TEXT NOT NULL,

                artist TEXT DEFAULT 'Unknown',

                filename TEXT NOT NULL,

                file_url TEXT NOT NULL,

                duration REAL DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # MUSIC ROOMS
        # =====================================================

        await db.execute("""
            CREATE TABLE IF NOT EXISTS music_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                room_id TEXT UNIQUE NOT NULL,
                invite_token TEXT UNIQUE NOT NULL,

                creator_id INTEGER NOT NULL,
                guest_id INTEGER,

                genre TEXT NOT NULL DEFAULT 'all',

                mode TEXT NOT NULL DEFAULT 'friend',

                status TEXT NOT NULL DEFAULT 'waiting',

                creator_ready INTEGER NOT NULL DEFAULT 0,
                guest_ready INTEGER NOT NULL DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                accepted_at TEXT,
                started_at TEXT,
                closed_at TEXT,

                updated_at TEXT,

                FOREIGN KEY (creator_id)
                    REFERENCES users(telegram_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (guest_id)
                    REFERENCES users(telegram_id)
                    ON DELETE SET NULL
            )
        """)

        # =====================================================
        # MUSIC ROOMS MIGRATION
        # =====================================================

        await _migrate_music_rooms(
            db
        )

        # =====================================================
        # MUSIC ROOM INDEXES
        # =====================================================

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_music_rooms_invite_token
            ON music_rooms(invite_token)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_music_rooms_creator
            ON music_rooms(creator_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_music_rooms_guest
            ON music_rooms(guest_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_music_rooms_status
            ON music_rooms(status)
        """)

        # =====================================================
        # MUSIC LIBRARY INDEX
        # =====================================================

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_music_library_created_at
            ON music_library(created_at)
        """)

        # =====================================================
        # LIVE MODES INITIAL DATA
        # =====================================================

        modes = [
            (
                "movie",
                "امشب فیلم ببینیم",
                "آدم‌هایی که همین الان حال فیلم دیدن دارن.",
                "🎬",
            ),
            (
                "music",
                "یه موزیک‌باز پیدا کنیم",
                "برای آدم‌هایی که الان مود موسیقی دارن.",
                "🎧",
            ),
            (
                "gaming",
                "بریم بازی",
                "آدم‌هایی که الان دنبال بازی هستن.",
                "🎮",
            ),
            (
                "football",
                "پای فوتبالیم",
                "برای طرفدارهای فوتبال.",
                "⚽",
            ),
            (
                "night",
                "شب‌بیداری",
                "هنوز بیداری؟ اینجا جمع شیم.",
                "🌙",
            ),
            (
                "study",
                "باهم درس بخونیم",
                "برای وقتی که می‌خوای تنها درس نخونی.",
                "📚",
            ),
            (
                "chat",
                "یه گپ بزنیم",
                "آدم‌هایی که الان مود حرف زدن دارن.",
                "💬",
            ),
            (
                "fun",
                "یه جمع باحال",
                "برای یه دورهمی دوستانه و سرگرم‌کننده.",
                "😂",
            ),
        ]

        await db.executemany(
            """
            INSERT OR IGNORE INTO live_modes
            (slug, title, description, emoji)
            VALUES (?, ?, ?, ?)
            """,
            modes,
        )

        # =====================================================
        # ACHIEVEMENTS
        # =====================================================

        achievements = [
            (
                "first_login",
                "First Login",
                "اولین ورود به FAZE",
                "👋",
                50,
            ),
            (
                "profile_complete",
                "Profile Complete",
                "پروفایل را کامل کن",
                "👤",
                100,
            ),
            (
                "first_game",
                "First Game",
                "اولین بازی",
                "🎮",
                50,
            ),
            (
                "first_quiz",
                "Quiz Starter",
                "اولین Quiz",
                "🧠",
                50,
            ),
            (
                "first_match",
                "First Match",
                "اولین Match",
                "🤝",
                100,
            ),
            (
                "seven_day_streak",
                "7 Day Streak",
                "هفت روز پشت سر هم فعال باش",
                "🔥",
                250,
            ),
        ]

        await db.executemany(
            """
            INSERT OR IGNORE INTO achievements
            (slug, title, description, emoji, xp_reward)
            VALUES (?, ?, ?, ?, ?)
            """,
            achievements,
        )

        # =====================================================
        # BADGES
        # =====================================================

        badges = [
            (
                "early_user",
                "Early User",
                "از کاربران اولیه FAZE",
                "🌟",
            ),
            (
                "gamer",
                "Gamer",
                "فعال در بازی‌های FAZE",
                "🎮",
            ),
            (
                "quiz_master",
                "Quiz Master",
                "مهارت بالا در Quiz",
                "🧠",
            ),
            (
                "social",
                "Social",
                "تعامل اجتماعی بالا",
                "👥",
            ),
            (
                "challenge_hunter",
                "Challenge Hunter",
                "علاقه‌مند به Challengeها",
                "🔥",
            ),
        ]

        await db.executemany(
            """
            INSERT OR IGNORE INTO badges
            (slug, title, description, emoji)
            VALUES (?, ?, ?, ?)
            """,
            badges,
        )

        await db.commit()


# =========================================================
# MUSIC ROOM MIGRATION
# =========================================================

async def _migrate_music_rooms(
    db,
):
    """
    دیتابیس‌های قدیمی FAZE را برای Music Room جدید آپدیت می‌کند.
    """

    cursor = await db.execute(
        "PRAGMA table_info(music_rooms)"
    )

    rows = await cursor.fetchall()

    columns = {
        row[1]
        for row in rows
    }

    # -----------------------------------------------------
    # Migration definitions
    # -----------------------------------------------------
    #
    # نکته مهم:
    # SQLite اجازه ALTER TABLE ADD COLUMN با
    # DEFAULT CURRENT_TIMESTAMP را در بعضی شرایط نمی‌دهد.
    #
    # بنابراین created_at را بدون DEFAULT اضافه می‌کنیم
    # و بعداً مقدارهای خالی را پر می‌کنیم.
    # -----------------------------------------------------

    migrations = {

        "invite_token": """
            ALTER TABLE music_rooms
            ADD COLUMN invite_token TEXT
        """,

        "guest_id": """
            ALTER TABLE music_rooms
            ADD COLUMN guest_id INTEGER
        """,

        "genre": """
            ALTER TABLE music_rooms
            ADD COLUMN genre TEXT NOT NULL DEFAULT 'all'
        """,

        "mode": """
            ALTER TABLE music_rooms
            ADD COLUMN mode TEXT NOT NULL DEFAULT 'friend'
        """,

        "status": """
            ALTER TABLE music_rooms
            ADD COLUMN status TEXT NOT NULL DEFAULT 'waiting'
        """,

        "creator_ready": """
            ALTER TABLE music_rooms
            ADD COLUMN creator_ready INTEGER NOT NULL DEFAULT 0
        """,

        "guest_ready": """
            ALTER TABLE music_rooms
            ADD COLUMN guest_ready INTEGER NOT NULL DEFAULT 0
        """,

        "created_at": """
            ALTER TABLE music_rooms
            ADD COLUMN created_at TEXT
        """,

        "accepted_at": """
            ALTER TABLE music_rooms
            ADD COLUMN accepted_at TEXT
        """,

        "started_at": """
            ALTER TABLE music_rooms
            ADD COLUMN started_at TEXT
        """,

        "closed_at": """
            ALTER TABLE music_rooms
            ADD COLUMN closed_at TEXT
        """,

        "updated_at": """
            ALTER TABLE music_rooms
            ADD COLUMN updated_at TEXT
        """,
    }

    for column_name, sql in migrations.items():

        if column_name not in columns:

            try:

                await db.execute(
                    sql
                )

            except Exception:

                # اگر migration قبلاً در یک اجرای
                # همزمان انجام شده باشد، ادامه می‌دهیم.
                pass

    # -----------------------------------------------------
    # FIX OLD NULL INVITE TOKENS
    # -----------------------------------------------------

    cursor = await db.execute("""
        SELECT
            id,
            invite_token
        FROM music_rooms
        WHERE invite_token IS NULL
           OR invite_token = ''
    """)

    rows = await cursor.fetchall()

    for row in rows:

        # -------------------------------------------------
        # جلوگیری از collision
        # -------------------------------------------------

        while True:

            token = secrets.token_urlsafe(
                18
            )

            token_cursor = await db.execute(
                """
                SELECT 1
                FROM music_rooms
                WHERE invite_token = ?
                LIMIT 1
                """,
                (
                    token,
                ),
            )

            exists = await token_cursor.fetchone()

            if not exists:
                break

        await db.execute(
            """
            UPDATE music_rooms
            SET invite_token = ?
            WHERE id = ?
            """,
            (
                token,
                row[0],
            ),
        )

    # -----------------------------------------------------
    # FIX OLD CREATED_AT
    # -----------------------------------------------------

    try:

        await db.execute("""
            UPDATE music_rooms
            SET created_at = COALESCE(
                created_at,
                CURRENT_TIMESTAMP
            )
            WHERE created_at IS NULL
               OR created_at = ''
        """)

    except Exception:

        pass

    # -----------------------------------------------------
    # FIX OLD UPDATED_AT
    # -----------------------------------------------------

    try:

        await db.execute("""
            UPDATE music_rooms
            SET updated_at = COALESCE(
                updated_at,
                created_at,
                CURRENT_TIMESTAMP
            )
            WHERE updated_at IS NULL
               OR updated_at = ''
        """)

    except Exception:

        pass

    # -----------------------------------------------------
    # FIX OLD GENRE
    # -----------------------------------------------------

    try:

        await db.execute("""
            UPDATE music_rooms
            SET genre = 'all'
            WHERE genre IS NULL
               OR genre = ''
        """)

    except Exception:

        pass

    # -----------------------------------------------------
    # FIX OLD MODE
    # -----------------------------------------------------

    try:

        await db.execute("""
            UPDATE music_rooms
            SET mode = 'friend'
            WHERE mode IS NULL
               OR mode = ''
        """)

    except Exception:

        pass

    # -----------------------------------------------------
    # FIX OLD STATUS
    # -----------------------------------------------------

    try:

        await db.execute("""
            UPDATE music_rooms
            SET status = 'waiting'
            WHERE status IS NULL
               OR status = ''
        """)

    except Exception:

        pass

    # -----------------------------------------------------
    # Unique invite token index
    # -----------------------------------------------------

    try:

        await db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_music_rooms_invite_token_unique
            ON music_rooms(invite_token)
        """)

    except Exception:

        # اگر دیتابیس قدیمی duplicate token داشته باشد،
        # index در اجرای اول ممکن است ساخته نشود.
        # توکن‌های خالی بالا repair شده‌اند.
        pass

    await db.commit()


# =========================================================
# CREATE MUSIC ROOM - OLD FRIEND FLOW
# =========================================================

async def create_music_room(
    creator_id: int,
    genre: str,
    room_id: str,
    invite_token: str,
    mode: str = "friend",
):
    """
    مسیر قدیمی ساخت Room برای دعوت دوست.

    این مسیر waiting است تا دوست دعوت را قبول کند.
    """

    try:

        creator_id = int(
            creator_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    room_id = str(
        room_id
    ).strip()

    invite_token = str(
        invite_token
    ).strip()

    genre = str(
        genre or "all"
    ).strip()

    mode = str(
        mode or "friend"
    ).strip()

    if not room_id:
        return None

    if not invite_token:
        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        # -------------------------------------------------
        # Close creator's previous open rooms
        # -------------------------------------------------

        await db.execute(
            """
            UPDATE music_rooms
            SET
                status = 'cancelled',
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE creator_id = ?
              AND status IN (
                  'waiting',
                  'invited',
                  'accepted'
              )
            """,
            (
                creator_id,
            ),
        )

        # -------------------------------------------------
        # Create waiting room
        # -------------------------------------------------

        try:

            await db.execute(
                """
                INSERT INTO music_rooms (
                    room_id,
                    invite_token,
                    creator_id,
                    guest_id,
                    genre,
                    mode,
                    status,
                    creator_ready,
                    guest_ready,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    NULL,
                    ?,
                    ?,
                    'waiting',
                    0,
                    0,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    room_id,
                    invite_token,
                    creator_id,
                    genre,
                    mode,
                ),
            )

        except Exception:

            await db.rollback()

            return None

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# CREATE ACTIVE ROOM - NEW ROOM FLOW
# =========================================================

async def create_active_music_room(
    creator_id: int,
    room_id: str,
    invite_token: str,
    genre: str = "all",
):
    """
    ساخت Room جدید.

    این نوع Room از همان لحظه ساخت ACTIVE است.
    """

    try:

        creator_id = int(
            creator_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    room_id = str(
        room_id
    ).strip()

    invite_token = str(
        invite_token
    ).strip()

    genre = str(
        genre or "all"
    ).strip()

    if not room_id:
        return None

    if not invite_token:
        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        # -------------------------------------------------
        # Close creator's previous open rooms
        # -------------------------------------------------

        await db.execute(
            """
            UPDATE music_rooms
            SET
                status = 'cancelled',
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE creator_id = ?
              AND status IN (
                  'waiting',
                  'invited',
                  'accepted',
                  'active'
              )
            """,
            (
                creator_id,
            ),
        )

        # -------------------------------------------------
        # Create active room
        # -------------------------------------------------

        try:

            await db.execute(
                """
                INSERT INTO music_rooms (
                    room_id,
                    invite_token,
                    creator_id,
                    guest_id,
                    genre,
                    mode,
                    status,
                    creator_ready,
                    guest_ready,
                    created_at,
                    started_at,
                    updated_at
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    NULL,
                    ?,
                    'room',
                    'active',
                    1,
                    0,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    room_id,
                    invite_token,
                    creator_id,
                    genre,
                ),
            )

        except Exception:

            await db.rollback()

            return None

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# GET ROOM BY TOKEN
# =========================================================

async def get_music_room_by_token(
    invite_token: str,
):

    if not invite_token:
        return None

    return await get_music_room(
        invite_token=invite_token
    )


# =========================================================
# GET MUSIC ROOM
# =========================================================

async def get_music_room(
    room_id=None,
    invite_token=None,
):

    if (
        not room_id
        and not invite_token
    ):

        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        if invite_token:

            cursor = await db.execute(
                """
                SELECT
                    id,
                    room_id,
                    invite_token,
                    creator_id,
                    guest_id,
                    genre,
                    mode,
                    status,
                    creator_ready,
                    guest_ready,
                    created_at,
                    accepted_at,
                    started_at,
                    closed_at,
                    updated_at
                FROM music_rooms
                WHERE invite_token = ?
                LIMIT 1
                """,
                (
                    str(
                        invite_token
                    ).strip(),
                ),
            )

        else:

            cursor = await db.execute(
                """
                SELECT
                    id,
                    room_id,
                    invite_token,
                    creator_id,
                    guest_id,
                    genre,
                    mode,
                    status,
                    creator_ready,
                    guest_ready,
                    created_at,
                    accepted_at,
                    started_at,
                    closed_at,
                    updated_at
                FROM music_rooms
                WHERE room_id = ?
                LIMIT 1
                """,
                (
                    str(
                        room_id
                    ).strip(),
                ),
            )

        row = await cursor.fetchone()

        if not row:
            return None

        return dict(row)


# =========================================================
# GET MUSIC TRACK
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

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                id,
                title,
                artist,
                filename,
                file_url,
                duration,
                created_at
            FROM music_library
            WHERE id = ?
            LIMIT 1
            """,
            (
                track_id,
            ),
        )

        row = await cursor.fetchone()

    if not row:
        return None

    return dict(row)


# =========================================================
# GET MUSIC TRACKS
# =========================================================

async def get_music_tracks():

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                id,
                title,
                artist,
                filename,
                file_url,
                duration,
                created_at
            FROM music_library
            ORDER BY id DESC
            """
        )

        rows = await cursor.fetchall()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# JOIN ACTIVE ROOM - NEW ROOM FLOW
# =========================================================

async def join_active_music_room(
    room_id: str,
    guest_id: int,
):
    """
    ورود نفر دوم به Room فعال.

    ظرفیت Room دقیقاً ۲ نفر است:
        creator_id
        guest_id

    UPDATE به صورت شرطی انجام می‌شود تا دو نفر همزمان
    نتوانند یک جای خالی را بگیرند.
    """

    room_id = str(
        room_id
    ).strip()

    try:

        guest_id = int(
            guest_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    if not room_id:
        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        # -------------------------------------------------
        # Atomic join
        # -------------------------------------------------

        cursor = await db.execute(
            """
            UPDATE music_rooms
            SET
                guest_id = ?,
                guest_ready = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
              AND status = 'active'
              AND guest_id IS NULL
              AND creator_id != ?
            """,
            (
                guest_id,
                room_id,
                guest_id,
            ),
        )

        if cursor.rowcount == 0:

            await db.rollback()

            # ---------------------------------------------
            # Room may have:
            #
            # 1. disappeared
            # 2. already have this guest
            # 3. be full
            # 4. belong to this creator
            # ---------------------------------------------

            room_cursor = await db.execute(
                """
                SELECT *
                FROM music_rooms
                WHERE room_id = ?
                LIMIT 1
                """,
                (
                    room_id,
                ),
            )

            room = await room_cursor.fetchone()

            if not room:
                return None

            room = dict(
                room
            )

            if room.get(
                "status"
            ) != "active":

                return None

            if (
                room.get(
                    "creator_id"
                )
                == guest_id
            ):

                return room

            if (
                room.get(
                    "guest_id"
                )
                == guest_id
            ):

                return room

            # Room full
            return None

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# ACCEPT MUSIC INVITATION - OLD FLOW
# =========================================================

async def accept_music_room(
    room_id: str,
    guest_id: int,
):

    room_id = str(
        room_id
    ).strip()

    try:

        guest_id = int(
            guest_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        cursor = await db.execute(
            """
            UPDATE music_rooms
            SET
                guest_id = ?,
                status = 'accepted',
                accepted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
              AND guest_id IS NULL
              AND status IN (
                  'waiting',
                  'invited'
              )
              AND creator_id != ?
            """,
            (
                guest_id,
                room_id,
                guest_id,
            ),
        )

        if cursor.rowcount == 0:

            await db.rollback()

            return None

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# REJECT MUSIC INVITATION
# =========================================================

async def reject_music_room(
    room_id: str,
):

    room_id = str(
        room_id
    ).strip()

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        cursor = await db.execute(
            """
            UPDATE music_rooms
            SET
                status = 'rejected',
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
              AND status IN (
                  'waiting',
                  'invited'
              )
            """,
            (
                room_id,
            ),
        )

        await db.commit()

        return cursor.rowcount > 0


# =========================================================
# CANCEL MUSIC ROOM
# =========================================================

async def cancel_music_room(
    room_id: str,
    creator_id: int,
):

    room_id = str(
        room_id
    ).strip()

    try:

        creator_id = int(
            creator_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return False

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        cursor = await db.execute(
            """
            UPDATE music_rooms
            SET
                status = 'cancelled',
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
              AND creator_id = ?
              AND status NOT IN (
                  'cancelled',
                  'rejected',
                  'closed'
              )
            """,
            (
                room_id,
                creator_id,
            ),
        )

        await db.commit()

        return cursor.rowcount > 0


# =========================================================
# LEAVE MUSIC ROOM
# =========================================================

async def leave_music_room(
    room_id: str,
    user_id: int,
):
    """
    خروج واقعی کاربر از Music Room.

    creator:
        Room بسته می‌شود.

    guest:
        فقط guest از Room حذف می‌شود.

        اگر Room فعال باشد:
            status = active باقی می‌ماند.

        اگر Room در حالت accepted باشد:
            Room دوباره waiting می‌شود تا
            دعوت/عضویت جدید امکان‌پذیر باشد.
    """

    room_id = str(
        room_id
    ).strip()

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return False

    if not room_id:
        return False

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                creator_id,
                guest_id,
                status
            FROM music_rooms
            WHERE room_id = ?
            LIMIT 1
            """,
            (
                room_id,
            ),
        )

        room = await cursor.fetchone()

        if not room:
            return False

        creator_id = room[
            "creator_id"
        ]

        guest_id = room[
            "guest_id"
        ]

        status = str(
            room[
                "status"
            ]
            or ""
        ).lower()

        # =================================================
        # CREATOR LEAVES
        # =================================================

        if (
            creator_id is not None
            and int(creator_id)
            == user_id
        ):

            if status in {
                "cancelled",
                "rejected",
                "closed",
            }:

                return False

            cursor = await db.execute(
                """
                UPDATE music_rooms
                SET
                    status = 'cancelled',
                    closed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE room_id = ?
                  AND creator_id = ?
                  AND status NOT IN (
                      'cancelled',
                      'rejected',
                      'closed'
                  )
                """,
                (
                    room_id,
                    user_id,
                ),
            )

            await db.commit()

            return cursor.rowcount > 0

        # =================================================
        # GUEST LEAVES
        # =================================================

        if (
            guest_id is not None
            and int(guest_id)
            == user_id
        ):

            # ---------------------------------------------
            # ACTIVE
            # ---------------------------------------------

            if status == "active":

                cursor = await db.execute(
                    """
                    UPDATE music_rooms
                    SET
                        guest_id = NULL,
                        guest_ready = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE room_id = ?
                      AND guest_id = ?
                      AND status = 'active'
                    """,
                    (
                        room_id,
                        user_id,
                    ),
                )

                await db.commit()

                return cursor.rowcount > 0

            # ---------------------------------------------
            # ACCEPTED
            # ---------------------------------------------

            if status == "accepted":

                cursor = await db.execute(
                    """
                    UPDATE music_rooms
                    SET
                        guest_id = NULL,
                        guest_ready = 0,
                        status = 'waiting',
                        accepted_at = NULL,
                        started_at = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE room_id = ?
                      AND guest_id = ?
                      AND status = 'accepted'
                    """,
                    (
                        room_id,
                        user_id,
                    ),
                )

                await db.commit()

                return cursor.rowcount > 0

            return False

        # =================================================
        # NOT A MEMBER
        # =================================================

        return False


# =========================================================
# SET USER READY - OLD FLOW
# =========================================================

async def set_music_ready(
    room_id: str,
    user_id: int,
):

    room_id = str(
        room_id
    ).strip()

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                room_id,
                creator_id,
                guest_id,
                status,
                creator_ready,
                guest_ready
            FROM music_rooms
            WHERE room_id = ?
            LIMIT 1
            """,
            (
                room_id,
            ),
        )

        room = await cursor.fetchone()

        if not room:
            return None

        if room[
            "status"
        ] != "accepted":

            return None

        if (
            user_id
            == room["creator_id"]
        ):

            await db.execute(
                """
                UPDATE music_rooms
                SET
                    creator_ready = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE room_id = ?
                """,
                (
                    room_id,
                ),
            )

        elif (
            room["guest_id"] is not None
            and user_id
            == room["guest_id"]
        ):

            await db.execute(
                """
                UPDATE music_rooms
                SET
                    guest_ready = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE room_id = ?
                """,
                (
                    room_id,
                ),
            )

        else:

            return None

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# ACTIVATE MUSIC ROOM - OLD FLOW
# =========================================================

async def activate_music_room(
    room_id: str,
):

    room_id = str(
        room_id
    ).strip()

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                creator_ready,
                guest_ready,
                status
            FROM music_rooms
            WHERE room_id = ?
            LIMIT 1
            """,
            (
                room_id,
            ),
        )

        room = await cursor.fetchone()

        if not room:
            return None

        if (
            room["creator_ready"] != 1
            or room["guest_ready"] != 1
            or room["status"] != "accepted"
        ):

            return None

        await db.execute(
            """
            UPDATE music_rooms
            SET
                status = 'active',
                started_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
              AND status = 'accepted'
              AND guest_id IS NOT NULL
            """,
            (
                room_id,
            ),
        )

        await db.commit()

    return await get_music_room(
        room_id=room_id
    )


# =========================================================
# ACTIVE ROOM FOR USER
# =========================================================

async def get_active_music_room_for_user(
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

        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                id,
                room_id,
                invite_token,
                creator_id,
                guest_id,
                genre,
                mode,
                status,
                creator_ready,
                guest_ready,
                created_at,
                accepted_at,
                started_at,
                closed_at,
                updated_at
            FROM music_rooms
            WHERE status = 'active'
              AND (
                  creator_id = ?
                  OR guest_id = ?
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                user_id,
            ),
        )

        row = await cursor.fetchone()

        if not row:
            return None

        return dict(row)


# =========================================================
# USER'S MUSIC ROOM
# =========================================================

async def get_music_room_for_user(
    user_id: int,
):
    """
    آخرین اتاقی که کاربر creator یا guest آن بوده.
    """

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    async with aiosqlite.connect(
        DB_PATH,
        timeout=30,
    ) as db:

        db.row_factory = (
            aiosqlite.Row
        )

        cursor = await db.execute(
            """
            SELECT
                id,
                room_id,
                invite_token,
                creator_id,
                guest_id,
                genre,
                mode,
                status,
                creator_ready,
                guest_ready,
                created_at,
                accepted_at,
                started_at,
                closed_at,
                updated_at
            FROM music_rooms
            WHERE creator_id = ?
               OR guest_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                user_id,
            ),
        )

        row = await cursor.fetchone()

        if not row:
            return None

        return dict(row)