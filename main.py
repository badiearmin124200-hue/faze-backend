import logging
import aiosqlite
import os
import uuid
from fastapi import Form
from fastapi import Response


from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from pathlib import Path

from src.db.database import DB_PATH

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    WebSocket,
    UploadFile,
    File,
    HTTPException,
)

from telegram.ext import Application
from fastapi.staticfiles import StaticFiles

from src.bot.handlers import register
from src.music.websocket import music_websocket


# =========================================================
# ENV
# =========================================================

load_dotenv()


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
).strip()


DEV_MODE = (
    os.getenv(
        "DEV_MODE",
        "false"
    ).strip().lower()
    == "true"
)


_bot_app: Application | None = None
_bot_username: str | None = None


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(
    __file__
).resolve().parent


# ---------------------------------------------------------
# IMPORTANT:
# Always use the same absolute SQLite database path.
# This prevents the API and WebSocket from accidentally
# opening different faze.db files because of cwd changes.
# ---------------------------------------------------------

_raw_db_path = Path(DB_PATH)

if _raw_db_path.is_absolute():

    DB_FILE = _raw_db_path

else:

    DB_FILE = (
        BASE_DIR
        / _raw_db_path
    )


DB_FILE = DB_FILE.resolve()


MUSIC_WEB_DIR = (
    BASE_DIR
    / "webapp"
    / "music"
)


MUSIC_UPLOAD_DIR = (
    BASE_DIR
    / "uploads"
    / "music"
)


# =========================================================
# STARTUP PATH LOG
# =========================================================

logger.info(
    "FAZE BASE_DIR: %s",
    BASE_DIR,
)

logger.info(
    "FAZE DATABASE: %s",
    DB_FILE,
)

logger.info(
    "FAZE MUSIC WEB: %s",
    MUSIC_WEB_DIR,
)

logger.info(
    "FAZE MUSIC FILES: %s",
    MUSIC_UPLOAD_DIR,
)


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global _bot_app
    global _bot_username

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    from src.db.database import init_db

    try:

        await init_db()

        logger.info(
            "Database initialized successfully."
        )

    except Exception:

        logger.exception(
            "Database initialization failed."
        )

        raise


    # =====================================================
    # DEV MODE
    # =====================================================

    if DEV_MODE:

        logger.warning(
            "=========================================="
        )

        logger.warning(
            "FAZE DEV MODE IS ENABLED"
        )

        logger.warning(
            "Telegram bot initialization is DISABLED."
        )

        logger.warning(
            "Telegram authentication is bypassed "
            "ONLY for local development users."
        )

        logger.warning(
            "DEV MUSIC ROOM is enabled."
        )

        logger.warning(
            "=========================================="
        )

        try:

            yield

        finally:

            logger.info(
                "FAZE DEV MODE stopped."
            )

        return


    # =====================================================
    # PRODUCTION TELEGRAM MODE
    # =====================================================

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN در فایل .env تنظیم نشده است."
        )


    # -----------------------------------------------------
    # Telegram Application
    # -----------------------------------------------------

    _bot_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    register(
        _bot_app
    )


    # -----------------------------------------------------
    # Telegram Initialize
    # -----------------------------------------------------

    await _bot_app.initialize()


    # -----------------------------------------------------
    # Get Bot Info
    # -----------------------------------------------------

    me = await _bot_app.bot.get_me()

    _bot_username = me.username

    _bot_app.bot_data[
        "bot_username"
    ] = _bot_username


    logger.info(
        "Logged in as @%s (id=%s)",
        _bot_username,
        me.id,
    )


    # -----------------------------------------------------
    # Remove old webhook
    # -----------------------------------------------------

    await _bot_app.bot.delete_webhook(
        drop_pending_updates=True
    )


    # -----------------------------------------------------
    # Start Telegram Application
    # -----------------------------------------------------

    await _bot_app.start()


    # -----------------------------------------------------
    # Start Polling
    # -----------------------------------------------------

    await _bot_app.updater.start_polling(
        drop_pending_updates=True
    )


    logger.info(
        "FAZE bot started (polling)."
    )

    logger.info(
        "FAZE running in production Telegram mode."
    )


    # =====================================================
    # APPLICATION RUNNING
    # =====================================================

    try:

        yield

    finally:

        logger.info(
            "FAZE shutdown started."
        )

        try:

            # ---------------------------------------------
            # Stop Telegram Polling
            # ---------------------------------------------

            if (
                _bot_app
                and _bot_app.updater
                and _bot_app.updater.running
            ):

                await _bot_app.updater.stop()


            # ---------------------------------------------
            # Stop Telegram Application
            # ---------------------------------------------

            if (
                _bot_app
                and _bot_app.running
            ):

                await _bot_app.stop()


            # ---------------------------------------------
            # Shutdown Telegram Application
            # ---------------------------------------------

            if _bot_app:

                await _bot_app.shutdown()


            logger.info(
                "FAZE bot stopped."
            )


        except Exception as e:

            logger.exception(
                "Shutdown error: %s",
                e,
            )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="FAZE",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://badiearmin124200-hue.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# =========================================================
# ENSURE MUSIC DIRECTORIES
# =========================================================

MUSIC_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# STATIC FILES
# =========================================================

app.mount(
    "/music",
    StaticFiles(
        directory=MUSIC_WEB_DIR,
        html=True,
    ),
    name="music",
)


app.mount(
    "/music-files",
    StaticFiles(
        directory=MUSIC_UPLOAD_DIR,
    ),
    name="music-files",
)


# =========================================================
# MUSIC WEBSOCKET
# =========================================================

@app.websocket(
    "/ws/music/{room_id}"
)
async def music_room_websocket(
    websocket: WebSocket,
    room_id: str,
):

    # -----------------------------------------------------
    # Read query parameters
    # -----------------------------------------------------

    token = (
        websocket
        .query_params
        .get(
            "token",
            ""
        )
        .strip()
    )


    init_data = (
        websocket
        .query_params
        .get(
            "init_data",
            ""
        )
        .strip()
    )


    dev_user = (
        websocket
        .query_params
        .get(
            "dev_user",
            ""
        )
        .strip()
    )


    # -----------------------------------------------------
    # Connection log
    # -----------------------------------------------------

    logger.info(
        "Music WS connection attempt | "
        "room=%s | "
        "has_token=%s | "
        "has_init_data=%s | "
        "dev_mode=%s | "
        "dev_user=%s",
        room_id,
        bool(token),
        bool(init_data),
        DEV_MODE,
        dev_user or "-",
    )


    # -----------------------------------------------------
    # Delegate authentication / room handling
    # -----------------------------------------------------

    try:

        await music_websocket(
            websocket,
            room_id,
            token,
            init_data,
            dev_user=dev_user,
            dev_mode=DEV_MODE,
        )

    except Exception:

        logger.exception(
            "Music WebSocket crashed | room=%s",
            room_id,
        )

        # -------------------------------------------------
        # If connection is still open, try to close it
        # cleanly. Never let an exception escape into the
        # ASGI WebSocket stack unnecessarily.
        # -------------------------------------------------

        try:

            await websocket.close(
                code=1011
            )

        except Exception:

            pass


# =========================================================
# DEV MUSIC ROOM SHORTCUT
# =========================================================

@app.websocket(
    "/ws/music-dev"
)
async def music_dev_websocket(
    websocket: WebSocket,
):

    dev_user = (
        websocket
        .query_params
        .get(
            "dev_user",
            ""
        )
        .strip()
    )


    logger.info(
        "DEV Music WS connection | "
        "dev_user=%s",
        dev_user or "-",
    )


    try:

        await music_websocket(
            websocket,
            "__FAZE_DEV_ROOM__",
            "",
            "",
            dev_user=dev_user,
            dev_mode=DEV_MODE,
        )

    except Exception:

        logger.exception(
            "DEV Music WebSocket crashed | "
            "dev_user=%s",
            dev_user or "-",
        )

        try:

            await websocket.close(
                code=1011
            )

        except Exception:

            pass


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get(
    "/health"
)
async def health_check():

    return {
        "status": "ok",

        "bot": _bot_username,

        "polling": bool(
            _bot_app
            and _bot_app.updater
            and _bot_app.updater.running
        ),

        "dev_mode": DEV_MODE,

        "database": str(
            DB_FILE
        ),
    }


# =========================================================
# MUSIC UPLOAD
# =========================================================

@app.post(
    "/api/music/upload"
)
async def upload_music(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="فایل انتخاب نشده است."
        )


    # -----------------------------------------------------
    # Allowed formats
    # -----------------------------------------------------

    allowed_extensions = {
        ".mp3",
        ".m4a",
        ".wav",
        ".ogg",
    }


    original_name = Path(
        file.filename
    ).name


    extension = Path(
        original_name
    ).suffix.lower()


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="فرمت فایل پشتیبانی نمی‌شود."
        )


    # -----------------------------------------------------
    # Music directory
    # -----------------------------------------------------

    MUSIC_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # Unique filename
    # -----------------------------------------------------

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    file_path = (
        MUSIC_UPLOAD_DIR
        / unique_name
    )


    try:

        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )


                if not chunk:

                    break


                buffer.write(
                    chunk
                )


        # -------------------------------------------------
        # Track title
        # -------------------------------------------------

        title = Path(
            original_name
        ).stem.strip()


        if not title:

            title = "آهنگ جدید"


        # -------------------------------------------------
        # Public URL
        # -------------------------------------------------

        file_url = (
            f"/music-files/"
            f"{unique_name}"
        )


        # -------------------------------------------------
        # Database
        # -------------------------------------------------

        async with aiosqlite.connect(
            DB_FILE
        ) as db:

            cursor = await db.execute(
                """
                INSERT INTO music_library
                (
                    title,
                    artist,
                    filename,
                    file_url,
                    duration
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    title,
                    "FAZE Music",
                    unique_name,
                    file_url,
                    0,
                ),
            )


            await db.commit()


            track_id = cursor.lastrowid


        logger.info(
            "Music uploaded | "
            "track_id=%s | "
            "title=%s | "
            "file=%s",
            track_id,
            title,
            unique_name,
        )


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "status": "ok",
            "track_id": track_id,
            "filename": unique_name,
            "title": title,
            "artist": "FAZE Music",
            "url": file_url,
        }


    except HTTPException:

        raise


    except Exception as e:

        logger.exception(
            "Music upload failed: %s",
            e,
        )


        # -----------------------------------------------
        # Remove uploaded file if DB failed
        # -----------------------------------------------

        try:

            file_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass


        raise HTTPException(
            status_code=500,
            detail="آپلود آهنگ انجام نشد."
        )


    finally:

        try:

            await file.close()

        except Exception:

            pass


# =========================================================
# MUSIC LIBRARY
# =========================================================


@app.get("/api/music/library")
async def get_music_library(response: Response):
    response.headers["Access-Control-Allow-Origin"] = (
        "https://badiearmin124200-hue.github.io"
    )
    response.headers["Access-Control-Expose-Headers"] = "*"

    try:
        async with aiosqlite.connect(DB_FILE) as db:
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
                ORDER BY id DESC
                """
            )

            rows = await cursor.fetchall()

        tracks = [dict(row) for row in rows]

        logger.info(
            "Music library loaded | tracks=%s | db=%s",
            len(tracks),
            DB_FILE,
        )

        return {
            "status": "ok",
            "tracks": tracks,
        }

    except Exception as e:
        logger.exception(
            "Music library failed: %s",
            e,
        )

        raise HTTPException(
            status_code=500,
            detail="دریافت کتابخانه آهنگ انجام نشد.",
        )

from fastapi.responses import Response
import re
import json


@app.get("/api/music/library/jsonp")
async def get_music_library_jsonp(callback: str = "musicLibraryCallback"):

    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", callback):
        raise HTTPException(status_code=400, detail="Invalid callback")

    try:
        async with aiosqlite.connect(DB_FILE) as db:
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
                ORDER BY id DESC
                """
            )

            rows = await cursor.fetchall()

        tracks = [dict(row) for row in rows]

        payload = {
            "status": "ok",
            "tracks": tracks,
        }

        javascript = (
            f"{callback}({json.dumps(payload, ensure_ascii=False)});"
        )

        return Response(
            content=javascript,
            media_type="application/javascript",
        )

    except Exception as e:
        logger.exception("Music library JSONP failed: %s", e)

        javascript = (
            f"{callback}("
            '{"status":"error","tracks":[]}'
            ");"
        )

        return Response(
            content=javascript,
            media_type="application/javascript",
            status_code=500,
        )

# =========================================================
# ADMIN ADD MUSIC
# =========================================================

@app.post(
    "/api/music/admin/add"
)
async def admin_add_music(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: str = Form("Unknown"),
):

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="فایل انتخاب نشده است."
        )


    # -----------------------------------------------------
    # Clean metadata
    # -----------------------------------------------------

    clean_title = (
        title.strip()
        or "بدون عنوان"
    )


    clean_artist = (
        artist.strip()
        or "Unknown"
    )


    # -----------------------------------------------------
    # Allowed formats
    # -----------------------------------------------------

    allowed_extensions = {
        ".mp3",
        ".m4a",
        ".wav",
        ".ogg",
    }


    original_name = Path(
        file.filename
    ).name


    extension = Path(
        original_name
    ).suffix.lower()


    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="فرمت فایل پشتیبانی نمی‌شود."
        )


    # -----------------------------------------------------
    # Music directory
    # -----------------------------------------------------

    MUSIC_UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # Unique filename
    # -----------------------------------------------------

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    file_path = (
        MUSIC_UPLOAD_DIR
        / unique_name
    )


    try:

        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )


                if not chunk:

                    break


                buffer.write(
                    chunk
                )


        # -------------------------------------------------
        # Public URL
        # -------------------------------------------------

        file_url = (
            f"/music-files/"
            f"{unique_name}"
        )


        # -------------------------------------------------
        # Database
        # -------------------------------------------------

        async with aiosqlite.connect(
            DB_FILE
        ) as db:

            cursor = await db.execute(
                """
                INSERT INTO music_library
                (
                    title,
                    artist,
                    filename,
                    file_url,
                    duration
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    clean_title,
                    clean_artist,
                    unique_name,
                    file_url,
                    0,
                ),
            )


            await db.commit()


            track_id = cursor.lastrowid


        logger.info(
            "Admin music added | "
            "track_id=%s | "
            "title=%s | "
            "artist=%s",
            track_id,
            clean_title,
            clean_artist,
        )


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "status": "ok",
            "track_id": track_id,
            "filename": unique_name,
            "title": clean_title,
            "artist": clean_artist,
            "url": file_url,
        }


    except HTTPException:

        raise


    except Exception as e:

        logger.exception(
            "Admin music upload failed: %s",
            e,
        )


        # -----------------------------------------------
        # Remove uploaded file if DB failed
        # -----------------------------------------------

        try:

            file_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass


        raise HTTPException(
            status_code=500,
            detail="افزودن آهنگ انجام نشد."
        )


    finally:

        try:

            await file.close()

        except Exception:

            pass