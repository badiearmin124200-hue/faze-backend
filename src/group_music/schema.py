CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS group_music_groups (
    group_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    added_by INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS group_music_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    purchased_by INTEGER NOT NULL,
    price INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    payment_ref TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    FOREIGN KEY (group_id)
        REFERENCES group_music_groups(group_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_group_music_subscriptions_group
ON group_music_subscriptions(group_id);

CREATE TABLE IF NOT EXISTS group_music_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    bot_started INTEGER NOT NULL DEFAULT 0,
    channel_1_joined INTEGER NOT NULL DEFAULT 0,
    channel_2_joined INTEGER NOT NULL DEFAULT 0,
    access_granted INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id)
        REFERENCES group_music_groups(group_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_music_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    room_id TEXT UNIQUE NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (group_id)
        REFERENCES group_music_groups(group_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_group_music_rooms_group
ON group_music_rooms(group_id);

CREATE TABLE IF NOT EXISTS group_music_room_members (
    room_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id)
        REFERENCES group_music_rooms(room_id)
        ON DELETE CASCADE
);
"""


async def init_group_music_tables(db):
    await db.executescript(CREATE_TABLES_SQL)
    await db.commit()