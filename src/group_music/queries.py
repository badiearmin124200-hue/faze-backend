CREATE_GROUP = """
INSERT INTO group_music_groups
    (group_id, title, added_by, active)
VALUES
    (?, ?, ?, 1)
ON CONFLICT(group_id)
DO UPDATE SET
    title = excluded.title,
    active = 1,
    updated_at = CURRENT_TIMESTAMP
"""

GET_GROUP = """
SELECT *
FROM group_music_groups
WHERE group_id = ?
LIMIT 1
"""

DEACTIVATE_GROUP = """
UPDATE group_music_groups
SET active = 0,
    updated_at = CURRENT_TIMESTAMP
WHERE group_id = ?
"""

UPSERT_MEMBER = """
INSERT INTO group_music_members
    (
        group_id,
        user_id,
        bot_started,
        channel_1_joined,
        channel_2_joined,
        access_granted
    )
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(group_id, user_id)
DO UPDATE SET
    bot_started = excluded.bot_started,
    channel_1_joined = excluded.channel_1_joined,
    channel_2_joined = excluded.channel_2_joined,
    access_granted = excluded.access_granted,
    updated_at = CURRENT_TIMESTAMP
"""

GET_MEMBER = """
SELECT *
FROM group_music_members
WHERE group_id = ?
  AND user_id = ?
LIMIT 1
"""

CREATE_SUBSCRIPTION = """
INSERT INTO group_music_subscriptions
    (
        group_id,
        purchased_by,
        price,
        started_at,
        expires_at,
        status,
        payment_ref
    )
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

GET_ACTIVE_SUBSCRIPTION = """
SELECT *
FROM group_music_subscriptions
WHERE group_id = ?
  AND status = 'active'
  AND expires_at > CURRENT_TIMESTAMP
ORDER BY expires_at DESC
LIMIT 1
"""

CREATE_ROOM = """
INSERT INTO group_music_rooms
    (
        group_id,
        room_id,
        created_by,
        active
    )
VALUES (?, ?, ?, 1)
"""

GET_ACTIVE_ROOM = """
SELECT *
FROM group_music_rooms
WHERE group_id = ?
  AND active = 1
ORDER BY id DESC
LIMIT 1
"""

ADD_ROOM_MEMBER = """
INSERT OR IGNORE INTO group_music_room_members
    (room_id, user_id)
VALUES (?, ?)
"""

DEACTIVATE_ROOM = """
UPDATE group_music_rooms
SET active = 0
WHERE room_id = ?
"""