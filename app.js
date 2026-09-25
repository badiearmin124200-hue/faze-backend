/* =========================================================
   FAZE MUSIC
   ========================================================= */


/* =========================================================
   TELEGRAM
========================================================= */
console.log("VELFA MUSIC APP VERSION: 20260925-2");
const telegramWebApp =
    window.Telegram?.WebApp || null;
const BACKEND_URL = "https://lapping-sizzling-humongous.ngrok-free.dev";
if (telegramWebApp) {
    telegramWebApp.ready();
    telegramWebApp.expand();
}


/* =========================================================
   URL / ROOM
========================================================= */

const params = new URLSearchParams(
    window.location.search
);

const telegramStartParam =
    telegramWebApp?.initDataUnsafe?.start_param ||
    params.get("tgWebAppStartParam") ||
    "";

const roomId =
    params.get("room_id") ||
    telegramStartParam ||
    "";
const isGroupMusicRoom =
    roomId.startsWith("gmusic_") ||
    roomId.startsWith("gm_");

const token = params.get("token");


/* =========================================================
   DEV MODE
========================================================= */

const requestedDevUser =
    params.get("dev_user");

const telegramInitData =
    telegramWebApp?.initData || "";

const isLocalhost =
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "localhost" ||
    window.location.hostname === "0.0.0.0";

const isDevMode =
    isLocalhost &&
    (
        requestedDevUser === "1" ||
        requestedDevUser === "2"
    );

const devUser =
    isDevMode
        ? requestedDevUser
        : null;

const isSyntheticDevRoom =
    isDevMode &&
    roomId === "__FAZE_DEV_ROOM__";


if (devUser) {

    console.log(
        "FAZE DEV MODE | User:",
        devUser
    );

    console.log(
        "FAZE DEV ROOM:",
        roomId
    );

    console.log(
        "FAZE SYNTHETIC DEV ROOM:",
        isSyntheticDevRoom
    );
}


/* =========================================================
   DOM
========================================================= */

const roomStatus =
    document.getElementById(
        "roomStatus"
    );

const connectionDot =
    document.getElementById(
        "connectionDot"
    );

const connectionText =
    document.getElementById(
        "connectionText"
    );

const playButton =
    document.getElementById(
        "playButton"
    );

const previousButton =
    document.getElementById(
        "previousButton"
    );

const nextButton =
    document.getElementById(
        "nextButton"
    );

const progressBar =
    document.getElementById(
        "progressBar"
    );

const volumeBar =
    document.getElementById(
        "volumeBar"
    );

const currentTimeElement =
    document.getElementById(
        "currentTime"
    );

const durationElement =
    document.getElementById(
        "duration"
    );

const albumCover =
    document.getElementById(
        "albumCover"
    );

const syncButton =
    document.getElementById(
        "syncButton"
    );

const leaveButton =
    document.getElementById(
        "leaveButton"
    );

const toast =
    document.getElementById(
        "toast"
    );

const musicFileInput =
    document.getElementById(
        "musicFileInput"
    );

const selectMusicButton =
    document.getElementById(
        "selectMusicButton"
    );

const uploadStatus =
    document.getElementById(
        "uploadStatus"
    );

const sharedVolumeToggle =
    document.getElementById(
        "sharedVolumeToggle"
    );

const librarySearch =
    document.getElementById(
        "librarySearch"
    );

const libraryTracks =
    document.getElementById(
        "libraryTracks"
    );

const userCountElement =
    document.getElementById(
        "userCount"
    );

const creatorNameElement =
    document.getElementById(
        "creatorName"
    );

const creatorStatusElement =
    document.getElementById(
        "creatorStatus"
    );

const guestNameElement =
    document.getElementById(
        "guestName"
    );

const guestStatusElement =
    document.getElementById(
        "guestStatus"
    );

const trackTitleElement =
    document.getElementById(
        "trackTitle"
    );

const trackArtistElement =
    document.getElementById(
        "trackArtist"
    );

const audioPlayer =
    document.getElementById(
        "audioPlayer"
    );


if (!audioPlayer) {

    console.error(
        "FAZE Music: #audioPlayer پیدا نشد."
    );
}


/* =========================================================
   STATE
========================================================= */

let socket = null;

let reconnectTimer = null;

let reconnectAttempts = 0;

let serverClockOffset = 0;

let isPlaying = false;

let currentPosition = 0;

let duration = 0;

let lastServerVersion = -1;

let lastServerState = null;

let currentTrackUrl = "";

let currentTrackId = null;

let isApplyingRemoteState = false;

let isSeekingLocally = false;

let clockSyncTimer = null;

let driftTimer = null;

let toastTimer = null;

let isLeavingRoom = false;

let isLoadingTrack = false;

let lastLocalVolume = 1;

let musicLibrary = [];

let currentLibraryIndex = -1;

let currentRoomUsers = [];

let currentUserRole = null;

let pendingLeaveTimer = null;

let lastSentTrackId = null;

let lastLocalActionAt = 0;

let endedTrackGuard = false;

let remotePlaybackRequestId = 0;

let connectionGeneration = 0;

let lastHardSeekAt = 0;

let lastTrackStateVersion = -1;

let reconnectSyncTimer = null;


/* =========================================================
   CONSTANTS
========================================================= */

const MAX_RECONNECT_DELAY = 10000;

const CLOCK_SYNC_INTERVAL = 3000;

const DRIFT_CHECK_INTERVAL = 1000;

const HARD_DRIFT = 0.8;

const REMOTE_APPLY_TIMEOUT = 500;

const LEAVE_CLOSE_DELAY = 250;

const RECONNECT_SYNC_DELAY = 250;

const HARD_SEEK_COOLDOWN = 1500;


/* =========================================================
   HELPERS
========================================================= */

function showToast(message) {

    if (!toast) {
        return;
    }

    toast.textContent =
        message;

    toast.classList.add(
        "show"
    );

    clearTimeout(
        toastTimer
    );

    toastTimer =
        setTimeout(
            () => {

                toast.classList.remove(
                    "show"
                );

            },
            2500
        );
}


function formatTime(seconds) {

    seconds =
        Number(seconds);

    if (
        !Number.isFinite(seconds) ||
        seconds < 0
    ) {

        seconds = 0;
    }

    seconds =
        Math.floor(seconds);

    const hours =
        Math.floor(
            seconds / 3600
        );

    const minutes =
        Math.floor(
            (
                seconds % 3600
            ) / 60
        );

    const remainingSeconds =
        seconds % 60;

    if (hours > 0) {

        return (
            hours +
            ":" +
            String(minutes).padStart(
                2,
                "0"
            ) +
            ":" +
            String(
                remainingSeconds
            ).padStart(
                2,
                "0"
            )
        );
    }

    return (
        minutes +
        ":" +
        String(
            remainingSeconds
        ).padStart(
            2,
            "0"
        )
    );
}


function clamp(
    value,
    min,
    max
) {

    return Math.max(
        min,
        Math.min(
            max,
            value
        )
    );
}


function getServerNow() {

    return (
        Date.now() / 1000
    ) + serverClockOffset;
}


function getAbsoluteUrl(
    url
) {

    if (!url) {
        return "";
    }

    try {

        return new URL(
            url,
            window.location.href
        ).href;

    } catch (error) {

        console.error(
            "Invalid URL:",
            url,
            error
        );

        return "";
    }
}


function safeNumber(
    value,
    fallback = 0
) {

    const number =
        Number(value);

    return Number.isFinite(number)
        ? number
        : fallback;
}


function getTrackId(
    track
) {

    if (!track) {
        return null;
    }

    const value =
        track.track_id ??
        track.trackId ??
        track.id ??
        null;

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return null;
    }

    return value;
}


function getTrackUrl(
    track
) {

    if (!track) {
        return "";
    }

    const url =
        track.file_url ||
        track.url ||
        "";

    if (!url) {
        return "";
    }

    if (url.startsWith("/")) {
        return (
            BACKEND_URL.replace(/\/+$/, "") +
            url
        );
    }

    return url;
}
function normalizeTrack(
    track
) {

    if (!track) {
        return null;
    }

    const id =
        getTrackId(
            track
        );

    const url =
        getTrackUrl(
            track
        );

    if (!url) {
        return null;
    }

    return {
        ...track,

        id:
            id,

        track_id:
            id,

        file_url:
            url,

        url:
            url,

        title:
            track.title ||
            "آهنگ جدید",

        artist:
            track.artist ||
            "FAZE Music",

        duration:
            safeNumber(
                track.duration,
                0
            )
    };
}


function parseTimestamp(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return NaN;
    }

    const numeric =
        Number(value);

    if (
        Number.isFinite(
            numeric
        )
    ) {

        return numeric;
    }

    const parsed =
        Date.parse(
            String(value)
        );

    if (
        Number.isFinite(
            parsed
        )
    ) {

        return parsed / 1000;
    }

    return NaN;
}


function isCurrentSocket(
    candidate
) {

    return (
        socket === candidate
    );
}


function getCurrentUserId() {

    if (devUser === "1") {
        return 1;
    }

    if (devUser === "2") {
        return 2;
    }

    try {

        const tgUser =
            window.Telegram
                ?.WebApp
                ?.initDataUnsafe
                ?.user;

        return tgUser?.id || null;

    } catch (_) {

        return null;
    }
}


function normalizeUserId(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return null;
    }

    return String(value);
}


function isUserOnline(
    user
) {

    if (!user) {
        return false;
    }

    return (
        user.online === true ||
        user.online === 1 ||
        user.online === "1" ||
        user.online === "true" ||
        String(
            user.status || ""
        ).toLowerCase() === "online"
    );
}


function getUserDisplayName(
    user
) {

    if (!user) {
        return "";
    }

    return (
        user.name ||
        user.first_name ||
        user.firstName ||
        user.username ||
        (
            user.id
                ? "کاربر " +
                String(
                    user.id
                ).slice(-4)
                : "کاربر"
        )
    );
}


function extractRoomUsers(
    message
) {

    if (!message) {
        return [];
    }

    if (
        Array.isArray(
            message.users
        )
    ) {

        return message.users;
    }

    if (
        Array.isArray(
            message.data
        )
    ) {

        return message.data;
    }

    if (
        message.data &&
        Array.isArray(
            message.data.users
        )
    ) {

        return message.data.users;
    }

    return [];
}


function extractMusicState(
    message
) {

    if (!message) {
        return null;
    }

    if (
        message.data &&
        typeof message.data === "object" &&
        !Array.isArray(message.data)
    ) {

        return message.data;
    }

    if (
        message.state &&
        typeof message.state === "object" &&
        !Array.isArray(message.state)
    ) {

        return message.state;
    }

    return message;
}


/* =========================================================
   UI UPDATE
========================================================= */

function updateUI() {

    const safeDuration =
        Number.isFinite(
            duration
        )
            ? Math.max(
                0,
                duration
            )
            : 0;

    const safePosition =
        Number.isFinite(
            currentPosition
        )
            ? clamp(
                currentPosition,
                0,
                safeDuration > 0
                    ? safeDuration
                    : Number.MAX_SAFE_INTEGER
            )
            : 0;


    if (progressBar) {

        progressBar.value =
            safeDuration > 0
                ? clamp(
                    (
                        safePosition /
                        safeDuration
                    ) * 100,
                    0,
                    100
                )
                : 0;
    }


    if (currentTimeElement) {

        currentTimeElement.textContent =
            formatTime(
                safePosition
            );
    }


    if (durationElement) {

        durationElement.textContent =
            formatTime(
                safeDuration
            );
    }


    if (playButton) {

        playButton.textContent =
            isPlaying
                ? "⏸"
                : "▶";
    }


    if (albumCover) {

        albumCover.classList.toggle(
            "playing",
            isPlaying
        );
    }


    if (previousButton) {

        previousButton.disabled =
            musicLibrary.length === 0;
    }


    if (nextButton) {

        nextButton.disabled =
            musicLibrary.length === 0;
    }
}


/* =========================================================
   CONNECTION UI
========================================================= */

function setConnectionState(
    state
) {

    if (
        !connectionDot ||
        !connectionText ||
        !roomStatus
    ) {

        return;
    }


    connectionDot.classList.remove(
        "connected",
        "error"
    );


    if (state === "connected") {

        connectionDot.classList.add(
            "connected"
        );

        connectionText.textContent =
            "متصل";

        roomStatus.textContent =
            "اتصال به اتاق برقرار شد";

        return;
    }


    if (state === "connecting") {

        connectionText.textContent =
            "در حال اتصال...";

        roomStatus.textContent =
            "در حال اتصال به اتاق";

        return;
    }


    if (state === "error") {

        connectionDot.classList.add(
            "error"
        );

        connectionText.textContent =
            "خطا";

        roomStatus.textContent =
            "خطا در اتصال";

        return;
    }


    if (state === "closed") {

        connectionDot.classList.add(
            "error"
        );

        connectionText.textContent =
            "قطع شده";

        roomStatus.textContent =
            "اتصال قطع شد";

        return;
    }


    connectionText.textContent =
        "نامشخص";
}


/* =========================================================
   WEBSOCKET URL
========================================================= */

function buildWebSocketUrl() {
    if (!roomId) {
        return "";
    }

    const backendUrl = BACKEND_URL.replace(/\/+$/, "");

    const protocol = backendUrl.startsWith("https://")
        ? "wss:"
        : "ws:";

    let path;

    if (isSyntheticDevRoom) {
        path = "/ws/music-dev";
    } else {
        path =
            "/ws/music/" +
            encodeURIComponent(roomId);
    }

    let url =
        protocol +
        "//" +
        backendUrl.replace(/^https?:\/\//, "") +
        path;

    const query = new URLSearchParams();

    if (token) {
        query.set("token", token);
    }

    if (telegramInitData) {
        query.set("init_data", telegramInitData);
    }

    if (devUser === "1" || devUser === "2") {
        query.set("dev_user", devUser);
    }

    const queryString = query.toString();

    if (queryString) {
        url += "?" + queryString;
    }

    return url;
}
/* =========================================================
   WEBSOCKET CONNECT
========================================================= */

function connectWebSocket() {

    console.log("🔥 WS STEP 1: connectWebSocket CALLED", {
        roomId,
        isLeavingRoom,
        isGroupMusicRoom,
        telegramInitData: !!telegramInitData,
    });


    if (isLeavingRoom) {
        console.warn("🔥 WS STOP: isLeavingRoom = true");
        return;
    }


    if (!roomId) {

        console.error("🔥 WS STOP: roomId is EMPTY");

        setConnectionState("error");

        if (roomStatus) {
            roomStatus.textContent =
                "شناسه اتاق پیدا نشد";
        }

        return;
    }


    if (
        socket &&
        (
            socket.readyState === WebSocket.OPEN ||
            socket.readyState === WebSocket.CONNECTING
        )
    ) {

        console.log(
            "🔥 WS STOP: existing socket is already OPEN/CONNECTING",
            socket.readyState
        );

        return;
    }


    socket = null;

    connectionGeneration += 1;

    const thisGeneration =
        connectionGeneration;


    if (reconnectSyncTimer) {

        clearTimeout(
            reconnectSyncTimer
        );

        reconnectSyncTimer = null;
    }


    console.log("🔥 WS STEP 2: preparing connection", {
        roomId,
        telegramInitData: !!telegramInitData,
        devUser,
    });


    if (
        !devUser &&
        telegramWebApp &&
        !telegramInitData
    ) {

        console.warn(
            "🔥 WS WARNING: Telegram initData is EMPTY"
        );
    }


    if (devUser) {

        if (
            devUser !== "1" &&
            devUser !== "2"
        ) {

            console.error(
                "🔥 WS STOP: invalid dev_user",
                devUser
            );

            setConnectionState("error");

            return;
        }
    }


    setConnectionState("connecting");


    const wsUrl =
        buildWebSocketUrl();


    console.log("🔥 WS STEP 3: URL BUILT", wsUrl);


    if (!wsUrl) {

        console.error(
            "🔥 WS STOP: buildWebSocketUrl() returned EMPTY"
        );

        setConnectionState("error");

        return;
    }


    let newSocket;


    try {

        console.log(
            "🔥 WS STEP 4: CREATING WebSocket"
        );

        newSocket =
            new WebSocket(wsUrl);

    } catch (error) {

        console.error(
            "🔥 WS CONSTRUCTOR ERROR:",
            error
        );

        setConnectionState("error");

        scheduleReconnect();

        return;
    }


    socket =
        newSocket;


    console.log(
        "🔥 WS STEP 5: WebSocket object CREATED"
    );


    newSocket.addEventListener(
        "open",
        () => {

            console.log(
                "🔥 WS STEP 6: OPENED",
                {
                    roomId,
                    readyState:
                        newSocket.readyState,
                }
            );


            if (
                !isCurrentSocket(newSocket) ||
                thisGeneration !==
                connectionGeneration
            ) {

                console.warn(
                    "🔥 WS OPEN ignored: socket is not current"
                );

                try {
                    newSocket.close();
                } catch (_) { }

                return;
            }


            reconnectAttempts = 0;


            if (reconnectTimer) {

                clearTimeout(
                    reconnectTimer
                );

                reconnectTimer = null;
            }


            setConnectionState(
                "connected"
            );


            showToast(
                "به Music Room متصل شدی 🎧"
            );


            startClockSync();

            startDriftCorrection();


            if (reconnectSyncTimer) {

                clearTimeout(
                    reconnectSyncTimer
                );
            }


            reconnectSyncTimer =
                setTimeout(
                    () => {

                        reconnectSyncTimer = null;


                        if (
                            isCurrentSocket(
                                newSocket
                            ) &&
                            newSocket.readyState ===
                            WebSocket.OPEN &&
                            !isLeavingRoom
                        ) {

                            console.log(
                                "🔥 WS STEP 7: REQUEST SYNC"
                            );

                            requestSync();
                        }

                    },
                    RECONNECT_SYNC_DELAY
                );
        }
    );


    newSocket.addEventListener(
        "message",
        event => {

            if (
                !isCurrentSocket(
                    newSocket
                )
            ) {
                return;
            }


            try {

                const data =
                    JSON.parse(
                        event.data
                    );


                console.log(
                    "🔥 WS MESSAGE:",
                    data.type
                );


                handleSocketMessage(
                    data
                );

            } catch (error) {

                console.error(
                    "🔥 WS MESSAGE PARSE ERROR:",
                    error
                );
            }
        }
    );


    newSocket.addEventListener(
        "close",
        event => {

            console.warn(
                "🔥 WS CLOSED:",
                {
                    code: event.code,
                    reason: event.reason,
                    roomId,
                }
            );


            if (
                !isCurrentSocket(
                    newSocket
                )
            ) {
                return;
            }


            socket = null;


            stopClockSync();

            stopDriftCorrection();


            if (reconnectSyncTimer) {

                clearTimeout(
                    reconnectSyncTimer
                );

                reconnectSyncTimer = null;
            }


            if (isLeavingRoom) {

                setConnectionState("closed");

                return;
            }


            if (
                event.code === 1000 &&
                (
                    event.reason ===
                    "Room closed" ||
                    event.reason ===
                    "User left room"
                )
            ) {

                setConnectionState("closed");

                return;
            }


            setConnectionState("closed");

            scheduleReconnect();
        }
    );


    newSocket.addEventListener(
        "error",
        error => {

            console.error(
                "🔥 WS ERROR:",
                error
            );


            if (
                isCurrentSocket(
                    newSocket
                )
            ) {

                setConnectionState(
                    "error"
                );
            }
        }
    );
}


/* =========================================================
   RECONNECT
========================================================= */

function scheduleReconnect() {

    if (
        isLeavingRoom ||
        reconnectTimer
    ) {

        return;
    }


    const delay =
        Math.min(
            1000 *
            Math.pow(
                2,
                reconnectAttempts
            ),
            MAX_RECONNECT_DELAY
        );


    reconnectAttempts =
        Math.min(
            reconnectAttempts + 1,
            10
        );


    console.log(
        "Music reconnect scheduled:",
        delay,
        "ms"
    );


    reconnectTimer =
        setTimeout(
            () => {

                reconnectTimer =
                    null;


                if (
                    !isLeavingRoom &&
                    (
                        !socket ||
                        (
                            socket.readyState !==
                            WebSocket.OPEN &&
                            socket.readyState !==
                            WebSocket.CONNECTING
                        )
                    )
                ) {

                    connectWebSocket();
                }

            },
            delay
        );
}


/* =========================================================
   CLOCK SYNC
========================================================= */

function startClockSync() {

    stopClockSync();


    if (isLeavingRoom) {
        return;
    }


    sendClockPing();


    clockSyncTimer =
        setInterval(
            () => {

                if (
                    !isLeavingRoom
                ) {

                    sendClockPing();
                }

            },
            CLOCK_SYNC_INTERVAL
        );
}


function stopClockSync() {

    if (clockSyncTimer) {

        clearInterval(
            clockSyncTimer
        );

        clockSyncTimer =
            null;
    }
}


function sendClockPing() {

    if (
        !socket ||
        socket.readyState !==
        WebSocket.OPEN ||
        isLeavingRoom
    ) {

        return;
    }


    const clientTime =
        Date.now() / 1000;


    sendMessage(
        {
            type:
                "ping",

            client_time:
                clientTime
        },
        false
    );
}


/* =========================================================
   SOCKET MESSAGE ROUTER
========================================================= */

function handleSocketMessage(
    message
) {

    if (
        !message ||
        typeof message !== "object"
    ) {

        return;
    }


    if (
        message.type ===
        "pong"
    ) {

        handlePong(
            message
        );

        return;
    }


    if (
        message.type ===
        "room_users"
    ) {

        renderRoomUsers(
            extractRoomUsers(
                message
            )
        );

        return;
    }


    if (
        message.type ===
        "state"
    ) {

        const state =
            extractMusicState(
                message
            );


        if (state) {

            handleMusicState(
                state
            );
        }

        return;
    }


    if (
        message.type ===
        "room_left"
    ) {

        isLeavingRoom =
            true;


        stopClockSync();

        stopDriftCorrection();


        if (audioPlayer) {

            audioPlayer.pause();
        }


        isPlaying =
            false;


        updateUI();


        showToast(
            "از Music Room خارج شدی 👋"
        );


        setConnectionState(
            "closed"
        );


        return;
    }


    if (
        message.type ===
        "room_closed"
    ) {

        isLeavingRoom =
            true;


        stopClockSync();

        stopDriftCorrection();


        if (audioPlayer) {

            audioPlayer.pause();
        }


        isPlaying =
            false;


        updateUI();


        showToast(
            "این Room بسته شد."
        );


        setConnectionState(
            "closed"
        );


        setTimeout(
            () => {

                if (
                    telegramWebApp &&
                    typeof telegramWebApp.close ===
                    "function"
                ) {

                    telegramWebApp.close();

                } else if (
                    window.history.length > 1
                ) {

                    window.history.back();

                } else {

                    window.location.href =
                        "/music/";
                }

            },
            500
        );


        return;
    }


    if (
        message.type ===
        "error"
    ) {

        console.warn(
            "Music server error:",
            message
        );


        if (message.message) {

            showToast(
                "❌ " +
                message.message
            );
        }


        return;
    }
}


/* =========================================================
   PONG
========================================================= */

function handlePong(
    data
) {

    const receivedAt =
        Date.now() / 1000;


    const sentAt =
        Number(
            data.client_time
        );


    const serverTime =
        Number(
            data.server_time
        );


    if (
        !Number.isFinite(
            sentAt
        ) ||
        !Number.isFinite(
            serverTime
        )
    ) {

        return;
    }


    const roundTripTime =
        Math.max(
            0,
            receivedAt -
            sentAt
        );


    const estimatedOffset =
        serverTime -
        (
            sentAt +
            roundTripTime / 2
        );


    if (
        !Number.isFinite(
            estimatedOffset
        )
    ) {

        return;
    }


    const smoothing =
        roundTripTime < 0.25
            ? 0.25
            : 0.10;


    serverClockOffset =
        (
            serverClockOffset *
            (1 - smoothing)
        ) +
        (
            estimatedOffset *
            smoothing
        );
}


/* =========================================================
   MUSIC STATE
========================================================= */

function handleMusicState(
    data
) {

    if (
        !data ||
        typeof data !== "object"
    ) {

        return;
    }


    const serverVersion =
        Number(
            data.version
        );

    const hasVersion =
        Number.isFinite(
            serverVersion
        );


    /*
     * State قدیمی را اصلاً اعمال نکن.
     */

    if (
        hasVersion &&
        serverVersion <
        lastServerVersion
    ) {

        return;
    }


    /*
     * State را ذخیره کن.
     */

    lastServerState = {
        ...data
    };


    if (hasVersion) {

        lastServerVersion =
            serverVersion;
    }


    /* =====================================================
       TRACK
    ===================================================== */

    const stateTrackUrl =
        data.url ||
        data.file_url ||
        "";


    if (stateTrackUrl) {

        const absoluteUrl =
            getAbsoluteUrl(
                stateTrackUrl
            );


        /*
         * فقط اگر واقعاً آهنگ عوض شده،
         * src را عوض کن.
         */

        if (
            absoluteUrl &&
            currentTrackUrl !==
            absoluteUrl
        ) {

            applyRemoteTrack({
                ...data,
                url:
                    stateTrackUrl
            });

            return;
        }
    }


    /* =====================================================
       TRACK ID
    ===================================================== */

    const incomingTrackId =
        data.track_id ??
        data.trackId ??
        null;


    if (
        incomingTrackId !== null &&
        incomingTrackId !== undefined
    ) {

        currentTrackId =
            incomingTrackId;
    }


    /* =====================================================
       TITLE / ARTIST
    ===================================================== */

    if (
        data.title !== undefined &&
        trackTitleElement
    ) {

        trackTitleElement.textContent =
            data.title ||
            "آهنگ جدید";
    }


    if (
        data.artist !== undefined &&
        trackArtistElement
    ) {

        trackArtistElement.textContent =
            data.artist ||
            "FAZE Music";
    }


    /* =====================================================
       SERVER POSITION
    ===================================================== */

    let serverPosition =
        Math.max(
            0,
            safeNumber(
                data.position,
                0
            )
        );


    let targetPosition =
        serverPosition;


    const changedAt =
        parseTimestamp(
            data.changed_at
        );


    if (
        Boolean(data.is_playing) &&
        Number.isFinite(
            changedAt
        )
    ) {

        const elapsed =
            Math.max(
                0,
                getServerNow() -
                changedAt
            );


        targetPosition =
            serverPosition +
            elapsed;
    }


    if (
        duration > 0
    ) {

        targetPosition =
            clamp(
                targetPosition,
                0,
                duration
            );
    }


    /*
     * موقع پخش محلی، position سرور را
     * هر بار روی audioPlayer تحمیل نکن.
     *
     * این کار دلیل اصلی بسیاری از
     * قطع‌وصل‌های قبلی بود.
     */

    if (
        !isSeekingLocally
    ) {

        currentPosition =
            targetPosition;
    }


    /* =====================================================
       DURATION
    ===================================================== */

    if (
        data.duration !== undefined &&
        data.duration !== null
    ) {

        const serverDuration =
            safeNumber(
                data.duration,
                0
            );


        if (
            serverDuration > 0
        ) {

            duration =
                serverDuration;
        }
    }


    /* =====================================================
       VOLUME
    ===================================================== */

    if (
        data.volume !== undefined &&
        data.volume !== null &&
        sharedVolumeToggle?.checked
    ) {

        const safeVolume =
            clamp(
                safeNumber(
                    data.volume,
                    lastLocalVolume
                ),
                0,
                1
            );


        if (audioPlayer) {

            audioPlayer.volume =
                safeVolume;
        }


        lastLocalVolume =
            safeVolume;


        if (volumeBar) {

            volumeBar.value =
                Math.round(
                    safeVolume * 100
                );
        }
    }


    /* =====================================================
       PLAY / PAUSE
    ===================================================== */

    const shouldPlay =
        Boolean(
            data.is_playing
        );


    if (shouldPlay) {

        /*
         * اگر در حال پخش است:
         * اصلاً play() دوباره نزن.
         */

        if (
            audioPlayer &&
            audioPlayer.paused &&
            !isLoadingTrack
        ) {

            startRemotePlayback();
        }

    } else {

        if (
            audioPlayer &&
            !audioPlayer.paused
        ) {

            stopRemotePlayback();
        }
    }


    updateUI();
}


/* =========================================================
   APPLY REMOTE TRACK
========================================================= */

function applyRemoteTrack(
    data
) {

    if (!audioPlayer) {
        return;
    }


    const trackUrl =
        data.url ||
        data.file_url ||
        "";


    const absoluteUrl =
        getAbsoluteUrl(
            trackUrl
        );


    if (!absoluteUrl) {
        return;
    }


    /*
     * اگر همان آهنگ است، دوباره load نکن.
     */

    if (
        currentTrackUrl ===
        absoluteUrl &&
        audioPlayer.src ===
        absoluteUrl
    ) {

        return;
    }


    currentTrackUrl =
        absoluteUrl;


    const incomingTrackId =
        data.track_id ??
        data.trackId ??
        null;


    if (
        incomingTrackId !==
        null &&
        incomingTrackId !==
        undefined
    ) {

        currentTrackId =
            incomingTrackId;
    }


    isApplyingRemoteState =
        true;


    isLoadingTrack =
        true;


    endedTrackGuard =
        false;


    remotePlaybackRequestId += 1;


    audioPlayer.pause();


    isPlaying =
        false;


    /*
     * آهنگ جدید را load کن.
     */

    audioPlayer.src =
        trackUrl;

    audioPlayer.load();


    currentPosition =
        Math.max(
            0,
            safeNumber(
                data.position,
                0
            )
        );


    duration =
        safeNumber(
            data.duration,
            0
        );


    if (trackTitleElement) {

        trackTitleElement.textContent =
            data.title ||
            "آهنگ جدید";
    }


    if (trackArtistElement) {

        trackArtistElement.textContent =
            data.artist ||
            "FAZE Music";
    }


    currentLibraryIndex =
        findLibraryTrackIndex(
            incomingTrackId,
            trackUrl
        );


    updateUI();


    /*
     * loading فقط بعد از آماده‌شدن فایل
     * یا timeout آزاد می‌شود.
     */

    let released =
        false;


    const releaseLoading =
        () => {

            if (released) {
                return;
            }


            released =
                true;


            audioPlayer.removeEventListener(
                "loadeddata",
                releaseLoading
            );


            audioPlayer.removeEventListener(
                "canplay",
                releaseLoading
            );


            isLoadingTrack =
                false;

            isApplyingRemoteState =
                false;


            /*
             * اگر server گفته بود در حال پخش است،
             * حالا یک بار پخش را شروع کن.
             */

            if (
                lastServerState &&
                Boolean(
                    lastServerState.is_playing
                ) &&
                !isLeavingRoom &&
                audioPlayer.paused
            ) {

                startRemotePlayback();
            }
        };


    audioPlayer.addEventListener(
        "loadeddata",
        releaseLoading
    );


    audioPlayer.addEventListener(
        "canplay",
        releaseLoading
    );


    setTimeout(
        releaseLoading,
        5000
    );
}


/* =========================================================
   REMOTE PLAYBACK
========================================================= */

async function startRemotePlayback() {

    if (
        !audioPlayer ||
        !audioPlayer.src ||
        isLeavingRoom
    ) {
        return;
    }

    /*
     * اگر همین الان در حال پخش است،
     * play() جدید نزن.
     */
    if (!audioPlayer.paused) {
        return;
    }

    /*
     * هنگام load شدن آهنگ صبر کن.
     */
    if (isLoadingTrack) {
        return;
    }

    const requestId =
        ++remotePlaybackRequestId;

    try {

        isApplyingRemoteState = true;

        /*
         * قبل از شروع پخش position را تنظیم کن.
         */
        if (
            Number.isFinite(currentPosition) &&
            audioPlayer.readyState >= 2
        ) {

            const actualPosition =
                safeNumber(
                    audioPlayer.currentTime,
                    0
                );

            const difference =
                Math.abs(
                    actualPosition -
                    currentPosition
                );

            if (difference > 0.25) {

                try {

                    audioPlayer.currentTime =
                        currentPosition;

                } catch (error) {

                    console.warn(
                        "Remote position apply failed:",
                        error
                    );
                }
            }
        }

        /*
         * اگر فایل هنوز آماده نیست،
         * منتظر canplay / loadeddata بمان.
         */
        if (audioPlayer.readyState < 3) {

            await new Promise(
                resolve => {

                    let finished = false;

                    const finish = () => {

                        if (finished) {
                            return;
                        }

                        finished = true;

                        audioPlayer.removeEventListener(
                            "canplay",
                            finish
                        );

                        audioPlayer.removeEventListener(
                            "loadeddata",
                            finish
                        );

                        audioPlayer.removeEventListener(
                            "error",
                            finish
                        );

                        resolve();
                    };

                    audioPlayer.addEventListener(
                        "canplay",
                        finish,
                        { once: true }
                    );

                    audioPlayer.addEventListener(
                        "loadeddata",
                        finish,
                        { once: true }
                    );

                    audioPlayer.addEventListener(
                        "error",
                        finish,
                        { once: true }
                    );

                    setTimeout(
                        finish,
                        5000
                    );
                }
            );
        }

        if (
            requestId !==
            remotePlaybackRequestId ||
            isLeavingRoom
        ) {
            return;
        }

        /*
         * ممکن است کاربر در همین فاصله خودش play کرده باشد.
         */
        if (!audioPlayer.paused) {
            return;
        }

        await audioPlayer.play();

        if (
            requestId !==
            remotePlaybackRequestId
        ) {
            return;
        }

        isPlaying = true;

        audioPlayer.playbackRate = 1;

        updateUI();

    } catch (error) {

        console.warn(
            "Remote playback blocked:",
            error
        );

        isPlaying = false;

        updateUI();

        /*
         * خطای autoplay را قطع WebSocket حساب نکن.
         */
        if (
            !isLeavingRoom &&
            error?.name !== "AbortError"
        ) {

            showToast(
                "▶️ برای شروع پخش، یک‌بار دکمه پخش را بزن"
            );
        }

    } finally {

        setTimeout(
            () => {

                if (
                    requestId ===
                    remotePlaybackRequestId
                ) {

                    isApplyingRemoteState =
                        false;
                }

            },
            REMOTE_APPLY_TIMEOUT
        );
    }
}


/* =========================================================
   REMOTE PAUSE
========================================================= */

function stopRemotePlayback() {

    if (!audioPlayer) {
        return;
    }

    remotePlaybackRequestId += 1;

    isApplyingRemoteState = true;

    audioPlayer.pause();

    isPlaying = false;

    audioPlayer.playbackRate = 1;

    currentPosition =
        safeNumber(
            audioPlayer.currentTime,
            currentPosition
        );

    updateUI();

    setTimeout(
        () => {

            isApplyingRemoteState =
                false;

        },
        REMOTE_APPLY_TIMEOUT
    );
}


/* =========================================================
   ROOM USERS
========================================================= */

function renderRoomUsers(users) {

    currentRoomUsers =
        Array.isArray(users)
            ? users.filter(Boolean)
            : [];


    /* =====================================================
       GROUP MUSIC ROOM
    ===================================================== */

    if (isGroupMusicRoom) {

        const friendUsersCard =
            document.getElementById(
                "friendUsersCard"
            );

        const groupUsersCard =
            document.getElementById(
                "groupMusicUsersCard"
            );

        const groupUsersList =
            document.getElementById(
                "groupMusicUsersList"
            );

        const groupUsersCount =
            document.getElementById(
                "groupUserCount"
            );

        const groupRoomTitle =
            document.getElementById(
                "groupMusicTitle"
            );

        const groupRoomCapacity =
            document.getElementById(
                "groupMusicCapacity"
            );

        const groupMusicHeader =
            document.getElementById(
                "groupMusicHeader"
            );


        /*
         * نمایش Group UI
         */

        if (friendUsersCard) {

            friendUsersCard.hidden = true;
            friendUsersCard.style.display = "none";
        }

        if (groupUsersCard) {

            groupUsersCard.hidden = false;
            groupUsersCard.style.display = "";
        }

        if (groupMusicHeader) {

            groupMusicHeader.hidden = false;
            groupMusicHeader.style.display = "";
        }


        /*
         * پیدا کردن Creator
         */

        const creator =
            currentRoomUsers.find(
                user => {

                    const role =
                        String(
                            user.role ||
                            user.user_role ||
                            ""
                        ).toLowerCase();

                    return (
                        role === "creator" ||
                        role === "owner"
                    );
                }
            );


        /*
         * نقش کاربر فعلی
         */

        const currentUserId =
            normalizeUserId(
                getCurrentUserId()
            );

        if (isDevMode) {

            currentUserRole =
                String(devUser) === "1"
                    ? "creator"
                    : "guest";

        } else if (
            currentUserId &&
            creator &&
            normalizeUserId(
                creator.id
            ) === currentUserId
        ) {

            currentUserRole =
                "creator";

        } else {

            currentUserRole =
                "guest";
        }


        /*
         * نام گروه
         */

        const groupTitle =
            currentRoomUsers
                .map(
                    user =>
                        user?.group_title
                )
                .find(
                    title =>
                        title &&
                        String(title).trim()
                );

        if (groupRoomTitle) {

            groupRoomTitle.textContent =
                `🎶 روم مخصوص گروه «${groupTitle || "FAZE"
                }»`;
        }


        /*
         * تعداد کاربران
         */

        const totalCount =
            currentRoomUsers.length;

        const onlineCount =
            currentRoomUsers.length;


        if (groupUsersCount) {

            groupUsersCount.textContent =
                `${totalCount} / 20`;
        }

        if (groupRoomCapacity) {

            groupRoomCapacity.textContent =
                `👥 ظرفیت: ${totalCount} / 20`;
        }


        /*
         * وضعیت کلی روم
         */

        if (roomStatus) {

            roomStatus.textContent =
                onlineCount > 0
                    ? `🟢 ${onlineCount} نفر آنلاین هستند`
                    : "⚪ هنوز کسی آنلاین نیست";
        }


        /*
         * لیست کاربران
         */

        if (groupUsersList) {

            groupUsersList.innerHTML = "";

            if (
                currentRoomUsers.length === 0
            ) {

                const empty =
                    document.createElement(
                        "div"
                    );

                empty.className =
                    "group-users-empty";

                empty.textContent =
                    "هنوز کسی وارد روم نشده.";

                groupUsersList.appendChild(
                    empty
                );

            } else {

                for (
                    const user
                    of currentRoomUsers
                ) {

                    if (!user) {
                        continue;
                    }


                    /*
                     * Row
                     */

                    const row =
                        document.createElement(
                            "div"
                        );

                    row.className =
                        "group-user";


                    /*
                     * Avatar
                     */

                    const avatar =
                        document.createElement(
                            "div"
                        );

                    avatar.className =
                        "group-user-avatar";


                    const avatarUrl =
                        user.avatar ||
                        user.photo_url ||
                        user.photoUrl ||
                        "";


                    if (
                        avatarUrl &&
                        (
                            String(
                                avatarUrl
                            ).startsWith("http") ||
                            String(
                                avatarUrl
                            ).startsWith("/")
                        )
                    ) {

                        const img =
                            document.createElement(
                                "img"
                            );

                        img.src =
                            avatarUrl;

                        img.alt = "";

                        img.loading =
                            "lazy";

                        avatar.appendChild(
                            img
                        );

                    } else {

                        avatar.textContent =
                            "👤";
                    }


                    /*
                     * Info
                     */

                    const info =
                        document.createElement(
                            "div"
                        );

                    info.className =
                        "group-user-info";


                    /*
                     * Name
                     */

                    const name =
                        document.createElement(
                            "strong"
                        );

                    name.textContent =
                        getUserDisplayName(
                            user
                        );

                    info.appendChild(
                        name
                    );


                    /*
                     * Online status
                     */

                    const status =
                        document.createElement(
                            "span"
                        );

                    status.className =
                        "group-user-status online";

                    status.textContent =
                        "● آنلاین";

                    info.appendChild(
                        status
                    );


                    /*
                     * Username
                     */

                    const username =
                        user.username ||
                        user.user_name ||
                        "";

                    if (username) {

                        const usernameEl =
                            document.createElement(
                                "small"
                            );

                        usernameEl.textContent =
                            String(
                                username
                            ).startsWith("@")
                                ? username
                                : `@${username}`;

                        info.appendChild(
                            usernameEl
                        );
                    }


                    /*
                     * Role
                     */

                    const role =
                        String(
                            user.role ||
                            user.user_role ||
                            ""
                        ).toLowerCase();

                    if (
                        role === "creator" ||
                        role === "owner"
                    ) {

                        const roleLabel =
                            document.createElement(
                                "small"
                            );

                        roleLabel.className =
                            "group-user-role";

                        roleLabel.textContent =
                            "👑 سازنده روم";

                        info.appendChild(
                            roleLabel
                        );
                    }


                    /*
                     * Current user
                     */

                    const thisUserId =
                        normalizeUserId(
                            user.id
                        );

                    if (
                        currentUserId &&
                        thisUserId ===
                        currentUserId
                    ) {

                        const meLabel =
                            document.createElement(
                                "small"
                            );

                        meLabel.className =
                            "group-user-me";

                        meLabel.textContent =
                            "شما";

                        info.appendChild(
                            meLabel
                        );
                    }


                    /*
                     * Online dot
                     */

                    const onlineDot =
                        document.createElement(
                            "div"
                        );

                    onlineDot.className =
                        "group-user-online-dot";


                    /*
                     * Build row
                     */

                    row.appendChild(
                        avatar
                    );

                    row.appendChild(
                        info
                    );

                    row.appendChild(
                        onlineDot
                    );

                    groupUsersList.appendChild(
                        row
                    );
                }
            }
        }

        return;
    }


    /* =====================================================
       NORMAL FRIEND ROOM
    ===================================================== */

    const friendUsersCard =
        document.getElementById(
            "friendUsersCard"
        );

    const groupUsersCard =
        document.getElementById(
            "groupMusicUsersCard"
        );

    const groupMusicHeader =
        document.getElementById(
            "groupMusicHeader"
        );


    /*
     * Friend نمایش
     */

    if (friendUsersCard) {

        friendUsersCard.hidden = false;
        friendUsersCard.style.display = "";
    }


    /*
     * Group مخفی
     */

    if (groupUsersCard) {

        groupUsersCard.hidden = true;
        groupUsersCard.style.display = "none";
    }

    if (groupMusicHeader) {

        groupMusicHeader.hidden = true;
        groupMusicHeader.style.display = "none";
    }


    /*
     * Creator / Guest
     */

    let creator = null;
    let guest = null;


    for (
        const user
        of currentRoomUsers
    ) {

        if (!user) {
            continue;
        }

        const role =
            String(
                user.role ||
                user.user_role ||
                ""
            ).toLowerCase();


        if (
            role === "creator" ||
            role === "owner"
        ) {

            creator = user;

        } else if (
            role === "guest"
        ) {

            guest = user;
        }
    }


    /*
     * Dev role
     */

    if (isDevMode) {

        currentUserRole =
            String(devUser) === "1"
                ? "creator"
                : "guest";
    }


    const currentUserId =
        normalizeUserId(
            getCurrentUserId()
        );


    /*
     * Creator fallback
     */

    if (!creator) {

        const currentUser =
            currentRoomUsers.find(
                user =>
                    normalizeUserId(
                        user?.id
                    ) === currentUserId
            );

        if (
            currentUser &&
            currentUserRole === "creator"
        ) {

            creator =
                currentUser;
        }
    }


    /*
     * Guest fallback
     */

    if (!guest) {

        const currentUser =
            currentRoomUsers.find(
                user =>
                    normalizeUserId(
                        user?.id
                    ) === currentUserId
            );

        if (
            currentUser &&
            currentUserRole === "guest"
        ) {

            guest =
                currentUser;
        }
    }


    /*
     * اولین نفر = Creator
     */

    if (
        !creator &&
        currentRoomUsers.length > 0
    ) {

        creator =
            currentRoomUsers[0];
    }


    /*
     * نفر دوم = Guest
     */

    if (!guest) {

        guest =
            currentRoomUsers.find(
                user =>
                    normalizeUserId(
                        user?.id
                    ) !==
                    normalizeUserId(
                        creator?.id
                    )
            ) || null;
    }


    /*
     * تعیین نقش فعلی
     */

    if (
        currentUserId &&
        creator &&
        normalizeUserId(
            creator.id
        ) === currentUserId
    ) {

        currentUserRole =
            "creator";

    } else if (
        currentUserId &&
        guest &&
        normalizeUserId(
            guest.id
        ) === currentUserId
    ) {

        currentUserRole =
            "guest";
    }


    /*
     * Friend elements
     */

    const creatorEl =
        document.getElementById(
            "creatorUser"
        );

    const guestEl =
        document.getElementById(
            "guestUser"
        );

    const creatorName =
        document.getElementById(
            "creatorName"
        );

    const guestName =
        document.getElementById(
            "guestName"
        );

    const creatorStatus =
        document.getElementById(
            "creatorStatus"
        );

    const guestStatus =
        document.getElementById(
            "guestStatus"
        );

    const userCountElement =
        document.getElementById(
            "userCount"
        );


    /*
     * Legacy helper
     */

    function setUserElement(
        element,
        user,
        emptyText
    ) {

        if (!element) {
            return;
        }

        element.classList.remove(
            "online",
            "offline"
        );

        if (!user) {

            element.textContent =
                emptyText;

            element.classList.add(
                "offline"
            );

            return;
        }

        const online =
            isUserOnline(user);

        const name =
            getUserDisplayName(user);

        element.textContent =
            `${name} — ${online
                ? "آنلاین"
                : "آفلاین"
            }`;

        element.classList.toggle(
            "online",
            online
        );

        element.classList.toggle(
            "offline",
            !online
        );
    }


    /*
     * جداگانه نام و وضعیت را آپدیت کن.
     */

    function updateSeparatedUserUI(
        nameElement,
        statusElement,
        user,
        emptyName
    ) {

        if (nameElement) {

            nameElement.textContent =
                user
                    ? getUserDisplayName(user)
                    : emptyName;
        }

        if (statusElement) {

            const online =
                Boolean(
                    user &&
                    isUserOnline(user)
                );

            statusElement.textContent =
                user
                    ? (
                        online
                            ? "آنلاین"
                            : "آفلاین"
                    )
                    : "در انتظار...";

            statusElement.classList.toggle(
                "online",
                online
            );

            statusElement.classList.toggle(
                "offline",
                !online
            );
        }
    }


    /*
     * Creator / Guest UI
     */

    setUserElement(
        creatorEl,
        creator,
        "سازنده — در انتظار..."
    );

    setUserElement(
        guestEl,
        guest,
        "مهمان — در انتظار..."
    );


    updateSeparatedUserUI(
        creatorName,
        creatorStatus,
        creator,
        "سازنده"
    );

    updateSeparatedUserUI(
        guestName,
        guestStatus,
        guest,
        "مهمان"
    );


    /*
     * تعداد آنلاین
     */

    const onlineCount =
        currentRoomUsers.filter(
            user =>
                isUserOnline(user)
        ).length;


    if (userCountElement) {

        userCountElement.textContent =
            `${Math.min(
                onlineCount,
                2
            )} / 2`;
    }


    /*
     * وضعیت Friend Room
     */

    if (roomStatus) {

        if (onlineCount >= 2) {

            roomStatus.textContent =
                "🟢 هر دو نفر آنلاین هستند";

        } else if (onlineCount === 1) {

            roomStatus.textContent =
                "🟡 منتظر نفر دوم...";

        } else {

            roomStatus.textContent =
                "⚪ منتظر کاربران...";
        }
    }
}


/* =========================================================
   SEND MESSAGE
========================================================= */

function sendMessage(
    data,
    showError = true
) {

    if (
        !socket ||
        socket.readyState !==
        WebSocket.OPEN
    ) {

        if (showError) {

            showToast(
                "اتصال برقرار نیست"
            );
        }

        return false;
    }


    try {

        socket.send(
            JSON.stringify(data)
        );

        lastLocalActionAt =
            Date.now();

        return true;

    } catch (error) {

        console.error(
            "WebSocket send error:",
            error
        );

        if (showError) {

            showToast(
                "❌ ارسال اطلاعات ناموفق بود"
            );
        }

        return false;
    }
}


/* =========================================================
   SYNC REQUEST
========================================================= */

function requestSync() {

    if (
        !socket ||
        socket.readyState !==
        WebSocket.OPEN ||
        isLeavingRoom
    ) {

        return false;
    }

    return sendMessage(
        {
            type:
                "sync_request"
        },
        false
    );
}


/* =========================================================
   MUSIC UPLOAD
========================================================= */

if (selectMusicButton) {

    selectMusicButton.addEventListener(
        "click",
        () => {

            if (musicFileInput) {

                musicFileInput.click();
            }
        }
    );
}


if (musicFileInput) {

    musicFileInput.addEventListener(
        "change",
        async () => {

            const file =
                musicFileInput.files?.[0];

            if (!file) {
                return;
            }

            if (uploadStatus) {

                uploadStatus.textContent =
                    "در حال آپلود آهنگ...";
            }

            try {

                const formData =
                    new FormData();

                formData.append(
                    "file",
                    file
                );

                const response = await fetch(
                    `${BACKEND_URL}/api/music/upload`,
                    {
                        method: "POST",
                        body: formData
                    }
                );

                if (!response.ok) {

                    let message =
                        "Upload failed";

                    try {

                        const errorData =
                            await response.json();

                        message =
                            errorData.detail ||
                            message;

                    } catch (_) { }

                    throw new Error(
                        message
                    );
                }

                const data =
                    await response.json();

                const uploadedTrackId =
                    data.track_id ??
                    data.trackId ??
                    data.id ??
                    null;

                const uploadedUrl =
                    data.file_url ||
                    data.url ||
                    "";

                if (!uploadedUrl) {

                    throw new Error(
                        "سرور آدرس آهنگ را برنگرداند."
                    );
                }

                if (
                    uploadedTrackId === null
                ) {

                    throw new Error(
                        "سرور شناسه آهنگ را برنگرداند."
                    );
                }

                const uploadedTitle =
                    data.title ||
                    file.name.replace(
                        /\.[^/.]+$/,
                        ""
                    );

                const uploadedArtist =
                    data.artist ||
                    "FAZE Music";

                currentTrackUrl =
                    getAbsoluteUrl(
                        uploadedUrl
                    );

                currentTrackId =
                    uploadedTrackId;

                if (audioPlayer) {

                    isApplyingRemoteState =
                        true;

                    isLoadingTrack =
                        true;

                    remotePlaybackRequestId +=
                        1;

                    audioPlayer.pause();

                    audioPlayer.src =
                        uploadedUrl;

                    audioPlayer.load();
                }

                if (trackTitleElement) {

                    trackTitleElement.textContent =
                        uploadedTitle;
                }

                if (trackArtistElement) {

                    trackArtistElement.textContent =
                        uploadedArtist;
                }

                currentPosition = 0;

                isPlaying = false;

                duration = 0;

                const sent =
                    sendMessage(
                        {
                            type:
                                "track",

                            track_id:
                                uploadedTrackId,

                            url:
                                uploadedUrl,

                            title:
                                uploadedTitle,

                            artist:
                                uploadedArtist
                        }
                    );

                if (!sent) {

                    showToast(
                        "⚠️ آهنگ آپلود شد ولی اتصال Room برقرار نیست"
                    );
                }

                updateUI();

                await loadMusicLibrary();

                currentLibraryIndex =
                    findLibraryTrackIndex(
                        uploadedTrackId,
                        uploadedUrl
                    );

                renderMusicLibrary(
                    musicLibrary
                );

                if (uploadStatus) {

                    uploadStatus.textContent =
                        "آهنگ با موفقیت آپلود شد.";
                }

                showToast(
                    "🎵 آهنگ آماده پخش شد"
                );

                setTimeout(
                    () => {

                        isApplyingRemoteState =
                            false;

                        isLoadingTrack =
                            false;

                    },
                    500
                );

            } catch (error) {

                console.error(
                    "Music upload error:",
                    error
                );

                if (uploadStatus) {

                    uploadStatus.textContent =
                        error?.message ||
                        "آپلود آهنگ ناموفق بود.";
                }

                showToast(
                    "❌ آپلود آهنگ انجام نشد"
                );

            } finally {

                musicFileInput.value =
                    "";
            }
        }
    );
}


/* =========================================================
   PLAY / PAUSE
========================================================= */

if (playButton) {

    playButton.addEventListener(
        "click",
        async () => {

            if (!audioPlayer) {
                return;
            }

            if (!audioPlayer.src) {

                showToast(
                    "🎵 اول یک آهنگ انتخاب کن"
                );

                return;
            }

            if (audioPlayer.paused) {

                try {

                    await audioPlayer.play();

                    isPlaying = true;

                    audioPlayer.playbackRate =
                        1;

                    const position =
                        safeNumber(
                            audioPlayer.currentTime,
                            currentPosition
                        );

                    currentPosition =
                        position;

                    sendMessage(
                        {
                            type:
                                "play",

                            position:
                                position
                        }
                    );

                    updateUI();

                } catch (error) {

                    console.error(
                        "Audio play error:",
                        error
                    );

                    showToast(
                        "❌ پخش آهنگ انجام نشد"
                    );
                }

            } else {

                const position =
                    safeNumber(
                        audioPlayer.currentTime,
                        currentPosition
                    );

                audioPlayer.pause();

                isPlaying = false;

                audioPlayer.playbackRate =
                    1;

                currentPosition =
                    position;

                sendMessage(
                    {
                        type:
                            "pause",

                        position:
                            position
                    }
                );

                updateUI();
            }
        }
    );
}


/* =========================================================
   PREVIOUS TRACK
========================================================= */

if (previousButton) {

    previousButton.addEventListener(
        "click",
        () => {

            playPreviousTrack();
        }
    );
}


function playPreviousTrack() {

    if (musicLibrary.length === 0) {

        showToast(
            "🎵 آرشیو آهنگ خالی است"
        );

        return;
    }

    let index =
        currentLibraryIndex;

    if (index < 0) {

        index =
            musicLibrary.length - 1;

    } else {

        index =
            index - 1;

        if (index < 0) {

            index =
                musicLibrary.length - 1;
        }
    }

    selectLibraryTrack(
        musicLibrary[index],
        true
    );
}


/* =========================================================
   NEXT TRACK
========================================================= */

if (nextButton) {

    nextButton.addEventListener(
        "click",
        () => {

            playNextTrack();
        }
    );
}


function playNextTrack() {

    if (musicLibrary.length === 0) {

        showToast(
            "🎵 آرشیو آهنگ خالی است"
        );

        return;
    }

    let index =
        currentLibraryIndex;

    if (index < 0) {

        index = 0;

    } else {

        index =
            index + 1;

        if (
            index >=
            musicLibrary.length
        ) {

            index = 0;
        }
    }

    selectLibraryTrack(
        musicLibrary[index],
        true
    );
}


/* =========================================================
   PROGRESS INPUT
========================================================= */

if (progressBar) {

    progressBar.addEventListener(
        "input",
        () => {

            if (
                duration <= 0 ||
                !audioPlayer
            ) {
                return;
            }

            isSeekingLocally =
                true;

            currentPosition =
                (
                    Number(
                        progressBar.value
                    ) / 100
                ) *
                duration;

            try {

                audioPlayer.currentTime =
                    currentPosition;

            } catch (error) {

                console.error(
                    "Local seek error:",
                    error
                );
            }

            updateUI();
        }
    );


    progressBar.addEventListener(
        "change",
        () => {

            if (
                duration <= 0 ||
                !audioPlayer
            ) {

                isSeekingLocally =
                    false;

                return;
            }

            const position =
                safeNumber(
                    audioPlayer.currentTime,
                    currentPosition
                );

            currentPosition =
                position;

            sendMessage(
                {
                    type:
                        "seek",

                    position:
                        position
                }
            );

            isSeekingLocally =
                false;

            lastHardSeekAt =
                Date.now();

            updateUI();
        }
    );


    progressBar.addEventListener(
        "pointerup",
        () => {

            setTimeout(
                () => {

                    isSeekingLocally =
                        false;

                },
                100
            );
        }
    );
}


/* =========================================================
   VOLUME
========================================================= */

if (volumeBar) {

    volumeBar.addEventListener(
        "input",
        () => {

            if (!audioPlayer) {
                return;
            }

            const volume =
                clamp(
                    Number(
                        volumeBar.value
                    ) / 100,
                    0,
                    1
                );

            audioPlayer.volume =
                volume;

            lastLocalVolume =
                volume;

            if (
                sharedVolumeToggle &&
                sharedVolumeToggle.checked
            ) {

                sendMessage(
                    {
                        type:
                            "volume",

                        volume:
                            volume
                    },
                    false
                );
            }
        }
    );
}


/* =========================================================
   SHARED VOLUME
========================================================= */

if (sharedVolumeToggle) {

    sharedVolumeToggle.addEventListener(
        "change",
        () => {

            if (
                sharedVolumeToggle.checked
            ) {

                const volume =
                    audioPlayer
                        ? clamp(
                            safeNumber(
                                audioPlayer.volume,
                                lastLocalVolume
                            ),
                            0,
                            1
                        )
                        : lastLocalVolume;

                lastLocalVolume =
                    volume;

                sendMessage(
                    {
                        type:
                            "volume",

                        volume:
                            volume
                    }
                );

                showToast(
                    "🔊 صدای مشترک فعال شد"
                );

            } else {

                showToast(
                    "🔈 صدای مشترک خاموش شد"
                );
            }
        }
    );
}


/* =========================================================
   SYNC BUTTON
========================================================= */

if (syncButton) {

    syncButton.addEventListener(
        "click",
        () => {

            if (requestSync()) {

                showToast(
                    "درخواست همگام‌سازی ارسال شد 🔄"
                );

            } else {

                showToast(
                    "⚠️ اتصال برقرار نیست"
                );
            }
        }
    );
}


/* =========================================================
   LEAVE BUTTON
========================================================= */

if (leaveButton) {

    leaveButton.addEventListener(
        "click",
        () => {

            const confirmed =
                window.confirm(
                    "مطمئنی می‌خواهی از اتاق خارج شوی؟"
                );

            if (!confirmed) {
                return;
            }

            leaveRoom();
        }
    );
}


/* =========================================================
   LEAVE ROOM
========================================================= */

function leaveRoom() {

    if (isLeavingRoom) {
        return;
    }

    isLeavingRoom = true;

    if (reconnectTimer) {

        clearTimeout(
            reconnectTimer
        );

        reconnectTimer = null;
    }

    if (reconnectSyncTimer) {

        clearTimeout(
            reconnectSyncTimer
        );

        reconnectSyncTimer = null;
    }

    reconnectAttempts = 0;

    if (pendingLeaveTimer) {

        clearTimeout(
            pendingLeaveTimer
        );

        pendingLeaveTimer = null;
    }

    stopClockSync();

    stopDriftCorrection();

    if (audioPlayer) {

        audioPlayer.pause();

        audioPlayer.playbackRate =
            1;
    }

    isPlaying = false;

    updateUI();

    const socketToClose =
        socket;

    if (
        socketToClose &&
        socketToClose.readyState ===
        WebSocket.OPEN
    ) {

        try {

            socketToClose.send(
                JSON.stringify(
                    {
                        type:
                            "leave"
                    }
                )
            );

        } catch (error) {

            console.warn(
                "Leave message send error:",
                error
            );
        }

        pendingLeaveTimer =
            setTimeout(
                () => {

                    try {

                        if (
                            socketToClose.readyState ===
                            WebSocket.OPEN ||
                            socketToClose.readyState ===
                            WebSocket.CLOSING
                        ) {

                            socketToClose.close(
                                1000,
                                "User left room"
                            );
                        }

                    } catch (error) {

                        console.warn(
                            "Socket close error:",
                            error
                        );
                    }

                    pendingLeaveTimer =
                        null;

                },
                LEAVE_CLOSE_DELAY
            );

    } else if (socketToClose) {

        try {

            socketToClose.close(
                1000,
                "User left room"
            );

        } catch (error) {

            console.warn(
                "Socket close error:",
                error
            );
        }
    }

    socket = null;

    showToast(
        "از Music Room خارج شدی 👋"
    );

    if (
        telegramWebApp &&
        typeof telegramWebApp.close ===
        "function"
    ) {

        setTimeout(
            () => {

                telegramWebApp.close();

            },
            300
        );

        return;
    }

    setTimeout(
        () => {

            if (
                window.history.length > 1
            ) {

                window.history.back();

            } else {

                window.location.href =
                    "/music/";
            }

        },
        300
    );
}


/* =========================================================
   AUDIO EVENTS
========================================================= */

if (audioPlayer) {

    audioPlayer.addEventListener(
        "loadedmetadata",
        () => {

            const browserDuration =
                safeNumber(
                    audioPlayer.duration,
                    0
                );

            if (browserDuration > 0) {

                duration =
                    browserDuration;
            }

            if (
                Number.isFinite(
                    currentPosition
                ) &&
                currentPosition > 0 &&
                duration > 0
            ) {

                try {

                    audioPlayer.currentTime =
                        Math.min(
                            currentPosition,
                            duration
                        );

                } catch (error) {

                    console.warn(
                        "Metadata seek error:",
                        error
                    );
                }
            }

            updateUI();
        }
    );


    audioPlayer.addEventListener(
        "timeupdate",
        () => {

            if (
                !audioPlayer.seeking &&
                !isSeekingLocally
            ) {

                currentPosition =
                    safeNumber(
                        audioPlayer.currentTime,
                        0
                    );

                if (
                    Number.isFinite(
                        audioPlayer.duration
                    ) &&
                    audioPlayer.duration > 0
                ) {

                    duration =
                        audioPlayer.duration;
                }

                updateUI();
            }
        }
    );


    audioPlayer.addEventListener(
        "play",
        () => {

            if (
                !isApplyingRemoteState
            ) {

                isPlaying = true;

                updateUI();
            }
        }
    );


    audioPlayer.addEventListener(
        "pause",
        () => {

            if (
                !isApplyingRemoteState
            ) {

                isPlaying = false;

                updateUI();
            }
        }
    );


    audioPlayer.addEventListener(
        "waiting",
        () => {

            console.log(
                "Audio buffering..."
            );
        }
    );


    audioPlayer.addEventListener(
        "playing",
        () => {

            if (!isLeavingRoom) {

                isPlaying = true;

                updateUI();
            }
        }
    );


    audioPlayer.addEventListener(
        "ended",
        () => {

            if (
                endedTrackGuard ||
                isLeavingRoom
            ) {
                return;
            }

            endedTrackGuard = true;

            isPlaying = false;

            currentPosition = 0;

            try {

                audioPlayer.currentTime =
                    0;

            } catch (_) { }

            audioPlayer.playbackRate =
                1;

            updateUI();

            /*
             * فقط creator آهنگ بعدی را انتخاب کند.
             */

            if (
                currentUserRole ===
                "guest"
            ) {

                requestSync();

                setTimeout(
                    () => {

                        endedTrackGuard =
                            false;

                    },
                    1000
                );

                return;
            }

            if (
                musicLibrary.length > 0
            ) {

                playNextTrack();

            } else {

                setTimeout(
                    () => {

                        endedTrackGuard =
                            false;

                    },
                    1000
                );
            }
        }
    );


    audioPlayer.addEventListener(
        "error",
        () => {

            console.error(
                "Audio element error:",
                audioPlayer.error
            );

            isPlaying = false;

            updateUI();

            if (!isLeavingRoom) {

                showToast(
                    "❌ پخش این فایل ممکن نیست"
                );
            }
        }
    );
}


/* =========================================================
   LOAD MUSIC LIBRARY
========================================================= */

function loadMusicLibraryJsonp() {
    return new Promise((resolve, reject) => {
        const callbackName =
            "musicLibraryCallback_" + Date.now();

        const script = document.createElement("script");

        const timeout = setTimeout(() => {
            cleanup();
            reject(
                new Error("سرور آرشیو پاسخ نداد.")
            );
        }, 10000);

        function cleanup() {
            clearTimeout(timeout);
            delete window[callbackName];
            script.remove();
        }

        window[callbackName] = (data) => {
            cleanup();
            resolve(data);
        };

        script.onerror = () => {
            cleanup();
            reject(
                new Error(
                    "اتصال به آرشیو موسیقی برقرار نشد."
                )
            );
        };

        script.src =
            `${BACKEND_URL}/api/music/library/jsonp?callback=${callbackName}&v=20260925`;

        document.head.appendChild(script);
    });
}


async function loadMusicLibrary() {
    if (!libraryTracks) {
        return;
    }

    libraryTracks.innerHTML =
        "<p>⏳ در حال دریافت آرشیو...</p>";

    try {
        const callbackName =
            "musicLibraryCallback_" + Date.now();

        const data = await new Promise((resolve, reject) => {
            const script = document.createElement("script");

            const timeout = setTimeout(() => {
                script.remove();
                reject(
                    new Error("سرور آرشیو پاسخ نداد.")
                );
            }, 10000);

            window[callbackName] = (result) => {
                clearTimeout(timeout);
                delete window[callbackName];
                script.remove();
                resolve(result);
            };

            script.onerror = () => {
                clearTimeout(timeout);
                delete window[callbackName];
                script.remove();
                reject(
                    new Error(
                        "اتصال به آرشیو موسیقی برقرار نشد."
                    )
                );
            };

            script.src =
                `${BACKEND_URL}/api/music/library/jsonp?callback=${callbackName}&v=20260925`;

            document.head.appendChild(script);
        });

        if (!data || data.status !== "ok") {
            throw new Error(
                "سرور آرشیو پاسخ معتبر نداد."
            );
        }

        const tracks = Array.isArray(data.tracks)
            ? data.tracks
            : [];

        musicLibrary = tracks
            .map(normalizeTrack)
            .filter(Boolean);

        currentLibraryIndex =
            findLibraryTrackIndex(
                currentTrackId,
                currentTrackUrl
            );

        if (musicLibrary.length === 0) {
            libraryTracks.innerHTML =
                "<p>🎵 هنوز آهنگی در آرشیو نیست.</p>";

            updateUI();
            return;
        }

        renderMusicLibrary(musicLibrary);
        updateUI();

    } catch (error) {
        console.error(
            "❌ Music library error:",
            error
        );

        libraryTracks.innerHTML =
            `<p>❌ دریافت آرشیو ناموفق بود.</p>
             <small>${error.message || "خطای نامشخص"}</small>`;
    }
}
/* =========================================================
   FIND LIBRARY TRACK
========================================================= */

function findLibraryTrackIndex(
    trackId,
    url
) {
ر
    if (
        !Array.isArray(
            musicLibrary
        )
    ) {

        return -1;
    }

    if (
        trackId !== null &&
        trackId !== undefined
    ) {

        const id =
            String(
                trackId
            );

        const indexById =
            musicLibrary.findIndex(
                track =>
                    String(
                        getTrackId(
                            track
                        )
                    ) === id
            );

        if (indexById >= 0) {
            return indexById;
        }
    }

    if (url) {

        const absoluteUrl =
            getAbsoluteUrl(
                url
            );

        if (absoluteUrl) {

            const indexByUrl =
                musicLibrary.findIndex(
                    track =>
                        getAbsoluteUrl(
                            getTrackUrl(
                                track
                            )
                        ) ===
                        absoluteUrl
                );

            if (indexByUrl >= 0) {
                return indexByUrl;
            }
        }
    }

    return -1;
}


/* =========================================================
   RENDER LIBRARY
========================================================= */

function renderMusicLibrary(
    tracks
) {

    if (!libraryTracks) {
        return;
    }

    libraryTracks.innerHTML = "";

    if (
        !Array.isArray(
            tracks
        ) ||
        tracks.length === 0
    ) {

        libraryTracks.innerHTML =
            "<p>🎵 هنوز آهنگی در آرشیو نیست.</p>";

        return;
    }

    tracks.forEach(
        track => {

            const item =
                document.createElement(
                    "button"
                );

            item.type = "button";

            item.className =
                "library-track";

            const trackIndex =
                findLibraryTrackIndex(
                    getTrackId(track),
                    getTrackUrl(track)
                );

            if (
                trackIndex ===
                currentLibraryIndex
            ) {

                item.classList.add(
                    "active"
                );
            }

            const title =
                document.createElement(
                    "span"
                );

            title.textContent =
                `🎵 ${track.title ||
                "بدون نام"
                }`;

            const artist =
                document.createElement(
                    "small"
                );

            artist.textContent =
                track.artist ||
                "Unknown";

            item.appendChild(
                title
            );

            item.appendChild(
                artist
            );

            item.addEventListener(
                "click",
                () => {

                    selectLibraryTrack(
                        track
                    );
                }
            );

            libraryTracks.appendChild(
                item
            );
        }
    );
}


/* =========================================================
   LIBRARY SEARCH
========================================================= */

if (librarySearch) {

    librarySearch.addEventListener(
        "input",
        () => {

            const query =
                librarySearch.value
                    .trim()
                    .toLowerCase();

            if (!query) {

                renderMusicLibrary(
                    musicLibrary
                );

                return;
            }

            const filtered =
                musicLibrary.filter(
                    track => {

                        const title =
                            String(
                                track.title ||
                                ""
                            ).toLowerCase();

                        const artist =
                            String(
                                track.artist ||
                                ""
                            ).toLowerCase();

                        return (
                            title.includes(query) ||
                            artist.includes(query)
                        );
                    }
                );

            if (
                filtered.length === 0
            ) {

                libraryTracks.innerHTML =
                    "<p>🔎 آهنگی پیدا نشد.</p>";

                return;
            }

            renderMusicLibrary(
                filtered
            );
        }
    );
}


/* =========================================================
   SELECT LIBRARY TRACK
========================================================= */

function selectLibraryTrack(
    track,
    autoPlay = false
) {

    const normalizedTrack =
        normalizeTrack(track);

    if (!normalizedTrack) {

        showToast(
            "❌ فایل آهنگ پیدا نشد"
        );

        return;
    }

    if (!audioPlayer) {
        return;
    }

    const trackId =
        getTrackId(
            normalizedTrack
        );

    const trackUrl =
        getTrackUrl(
            normalizedTrack
        );

    const absoluteUrl =
        getAbsoluteUrl(
            trackUrl
        );

    if (!absoluteUrl) {

        showToast(
            "❌ آدرس آهنگ نامعتبر است"
        );

        return;
    }

    if (
        trackId === null ||
        trackId === undefined
    ) {

        showToast(
            "❌ شناسه آهنگ پیدا نشد"
        );

        return;
    }

    currentTrackUrl =
        absoluteUrl;

    currentTrackId =
        trackId;

    currentLibraryIndex =
        findLibraryTrackIndex(
            trackId,
            trackUrl
        );

    isApplyingRemoteState =
        true;

    isLoadingTrack =
        true;

    endedTrackGuard =
        false;

    remotePlaybackRequestId += 1;

    audioPlayer.pause();

    audioPlayer.src =
        trackUrl;

    audioPlayer.load();

    currentPosition = 0;

    isPlaying = false;

    duration =
        safeNumber(
            normalizedTrack.duration,
            0
        );

    if (trackTitleElement) {

        trackTitleElement.textContent =
            normalizedTrack.title;
    }

    if (trackArtistElement) {

        trackArtistElement.textContent =
            normalizedTrack.artist;
    }

    updateUI();

    lastSentTrackId =
        trackId;

    const sent =
        sendMessage(
            {
                type:
                    "track",

                track_id:
                    trackId,

                url:
                    trackUrl,

                title:
                    normalizedTrack.title,

                artist:
                    normalizedTrack.artist,

                duration:
                    safeNumber(
                        normalizedTrack.duration,
                        0
                    )
            }
        );

    if (!sent) {

        isApplyingRemoteState =
            false;

        isLoadingTrack =
            false;

        showToast(
            "⚠️ اتصال Room برقرار نیست"
        );

        return;
    }

    if (autoPlay) {

        const playAfterLoad =
            async () => {

                if (isLeavingRoom) {
                    return;
                }

                if (
                    !isCurrentTrack(
                        absoluteUrl,
                        trackId
                    )
                ) {
                    return;
                }

                try {

                    await audioPlayer.play();

                    if (!isLeavingRoom) {

                        isPlaying = true;

                        currentPosition =
                            safeNumber(
                                audioPlayer.currentTime,
                                0
                            );

                        sendMessage(
                            {
                                type:
                                    "play",

                                position:
                                    currentPosition
                            }
                        );

                        updateUI();
                    }

                } catch (error) {

                    console.warn(
                        "Auto play blocked:",
                        error
                    );

                    isPlaying = false;

                    updateUI();

                    showToast(
                        "▶️ برای پخش، دکمه پخش را بزن"
                    );
                }
            };


        if (
            audioPlayer.readyState >= 3
        ) {

            setTimeout(
                playAfterLoad,
                50
            );

        } else {

            audioPlayer.addEventListener(
                "canplay",
                playAfterLoad,
                {
                    once: true
                }
            );
        }
    }


    const releaseLocalTrack =
        () => {

            isApplyingRemoteState =
                false;

            isLoadingTrack =
                false;
        };


    audioPlayer.addEventListener(
        "loadeddata",
        releaseLocalTrack,
        {
            once: true
        }
    );


    setTimeout(
        releaseLocalTrack,
        5000
    );


    renderMusicLibrary(
        musicLibrary
    );

    showToast(
        "🎵 آهنگ انتخاب شد"
    );
}


/* =========================================================
   CURRENT TRACK CHECK
========================================================= */

function isCurrentTrack(
    expectedUrl,
    expectedId
) {

    return (
        currentTrackUrl ===
        expectedUrl &&
        String(currentTrackId) ===
        String(expectedId)
    );
}


/* =========================================================
   DRIFT CORRECTION
========================================================= */

function startDriftCorrection() {

    stopDriftCorrection();

    if (isLeavingRoom) {
        return;
    }

    driftTimer =
        setInterval(
            correctPlaybackDrift,
            DRIFT_CHECK_INTERVAL
        );
}


function stopDriftCorrection() {

    if (driftTimer) {

        clearInterval(
            driftTimer
        );

        driftTimer = null;
    }
}


function correctPlaybackDrift() {

    if (
        !audioPlayer ||
        audioPlayer.paused ||
        !isPlaying ||
        !lastServerState ||
        isSeekingLocally ||
        isLoadingTrack ||
        isLeavingRoom
    ) {
        return;
    }

    const state =
        lastServerState;

    if (!state.is_playing) {
        return;
    }

    const changedAt =
        parseTimestamp(
            state.changed_at
        );

    if (
        !Number.isFinite(
            changedAt
        )
    ) {
        return;
    }

    const basePosition =
        Math.max(
            0,
            safeNumber(
                state.position,
                0
            )
        );

    const expectedPosition =
        basePosition +
        Math.max(
            0,
            getServerNow() -
            changedAt
        );

    const actualPosition =
        safeNumber(
            audioPlayer.currentTime,
            0
        );

    const drift =
        expectedPosition -
        actualPosition;

    if (
        Math.abs(drift) <=
        HARD_DRIFT
    ) {

        if (
            audioPlayer.playbackRate !==
            1
        ) {

            audioPlayer.playbackRate =
                1;
        }

        return;
    }

    if (
        audioPlayer.readyState < 3
    ) {
        return;
    }

    const now =
        Date.now();

    if (
        now -
        lastHardSeekAt <
        HARD_SEEK_COOLDOWN
    ) {
        return;
    }

    const target =
        duration > 0
            ? clamp(
                expectedPosition,
                0,
                duration
            )
            : Math.max(
                0,
                expectedPosition
            );

    try {

        lastHardSeekAt =
            now;

        audioPlayer.currentTime =
            target;

        currentPosition =
            target;

        updateUI();

    } catch (error) {

        console.warn(
            "Drift correction error:",
            error
        );
    }
}


/* =========================================================
   KEYBOARD SHORTCUTS
========================================================= */

document.addEventListener(
    "keydown",
    event => {

        const tag =
            event.target?.tagName
                ?.toLowerCase();

        if (
            tag === "input" ||
            tag === "textarea" ||
            tag === "select"
        ) {
            return;
        }

        if (
            event.code ===
            "Space"
        ) {

            event.preventDefault();

            if (playButton) {
                playButton.click();
            }

            return;
        }

        if (
            event.code ===
            "ArrowRight"
        ) {

            playNextTrack();

            return;
        }

        if (
            event.code ===
            "ArrowLeft"
        ) {

            playPreviousTrack();
        }
    }
);


/* =========================================================
   PAGE VISIBILITY
========================================================= */

document.addEventListener(
    "visibilitychange",
    () => {

        if (
            document.visibilityState ===
            "visible"
        ) {

            if (
                socket &&
                socket.readyState ===
                WebSocket.OPEN
            ) {

                requestSync();

                startClockSync();

                startDriftCorrection();

            } else if (
                !isLeavingRoom
            ) {

                connectWebSocket();
            }
        }
    }
);


/* =========================================================
   PAGE UNLOAD
========================================================= */

window.addEventListener(
    "pagehide",
    () => {

        stopClockSync();

        stopDriftCorrection();
    }
);


/* =========================================================
   INITIALIZE
========================================================= */

if (audioPlayer) {

    const initialVolume =
        clamp(
            safeNumber(
                audioPlayer.volume,
                1
            ),
            0,
            1
        );

    audioPlayer.volume =
        initialVolume;

    lastLocalVolume =
        initialVolume;
}


if (volumeBar) {

    volumeBar.value =
        Math.round(
            lastLocalVolume *
            100
        );
}


/*
 * ترتیب مهم است:
 * اول UI
 * بعد WebSocket
 * بعد Library
 */

console.log(
    "🔥 INIT STEP 1: app.js reached initialization"
);


updateUI();

console.log(
    "🔥 INIT STEP 2: updateUI done"
);


startDriftCorrection();

console.log(
    "🔥 INIT STEP 3: drift correction started"
);


connectWebSocket();

console.log(
    "🔥 INIT STEP 4: connectWebSocket called"
);


loadMusicLibrary();

console.log(
    "🔥🔥🔥 FAZE APP.JS LOADED - END OF FILE"
);