import os


GROUP_MUSIC_PRICE_TOMAN = int(
    os.getenv("GROUP_MUSIC_PRICE_TOMAN", "100000")
)

GROUP_MUSIC_DURATION_DAYS = int(
    os.getenv("GROUP_MUSIC_DURATION_DAYS", "30")
)

GROUP_MUSIC_CHANNEL_1 = os.getenv(
    "GROUP_MUSIC_CHANNEL_1",
    ""
).strip()

GROUP_MUSIC_CHANNEL_2 = os.getenv(
    "GROUP_MUSIC_CHANNEL_2",
    ""
).strip()

GROUP_MUSIC_CHANNEL_1_TITLE = os.getenv(
    "GROUP_MUSIC_CHANNEL_1_TITLE",
    "کانال اول"
).strip()

GROUP_MUSIC_CHANNEL_2_TITLE = os.getenv(
    "GROUP_MUSIC_CHANNEL_2_TITLE",
    "کانال دوم"
).strip()

GROUP_MUSIC_PAYMENT_URL = os.getenv(
    "GROUP_MUSIC_PAYMENT_URL",
    ""
).strip()

GROUP_MUSIC_ROOM_PREFIX = "gmusic"
GROUP_MUSIC_TEST_MODE = True