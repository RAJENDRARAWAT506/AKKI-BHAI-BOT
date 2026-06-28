"""
██████╗  ██████╗ ████████╗
██╔══██╗██╔═══██╗╚══██╔══╝
██████╔╝██║   ██║   ██║
██╔══██╗██║   ██║   ██║
██████╔╝╚██████╔╝   ██║
╚═════╝  ╚═════╝    ╚═╝
➤ BOT STARTED SUCCESSFULLY
➤ DATABASE LOADED 
➤ TELEGRAM API CONNECTED
"""
import asyncio
import sqlite3
import json
import requests
import time
from contextlib import contextmanager
from datetime import date
from functools import partial, wraps
import os

from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.error import TelegramError, Forbidden, NetworkError, RetryAfter, TimedOut
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    filters,
    ContextTypes,
)
from html import escape as html_escape

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

load_dotenv()

BOT_TOKEN:          str = os.getenv("BOT_TOKEN", "")
SOURCE_CHAT_ID:     int = int(os.getenv("SOURCE_CHAT_ID", "0"))
ADMIN_ID:           int = int(os.getenv("ADMIN_ID", "0"))

BROADCAST_CONCURRENCY: int = 100   # max parallel broadcast workers
APPROVAL_CONCURRENCY:  int = 50
SEQUENCE_CONCURRENCY:  int = 10
MAX_RETRIES_DB:        int = 3
MAX_RETRIES_API:       int = 3
DB_PATH:               str = "bot.db"
API_URL:               str = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ═══════════════════════════════════════════════════════════════════
# PREMIUM EMOJI IDs
# ═══════════════════════════════════════════════════════════════════
# --- Original panel emojis ---
EMOJI_BROADCAST    = "5325524851631334621"
EMOJI_STATS        = "6165982511882047164"
EMOJI_ADMINS       = "6170133383025267499"
EMOJI_SUBADMINS    = "6163314886219665690"
EMOJI_SEQUENCE     = "6204216787492409275"
EMOJI_APPROVE      = "6169969289504756963"
EMOJI_AUTO_APPROVE = "6163177640539721557"
EMOJI_PERMISSIONS  = "6163403572999361145"
EMOJI_BOT_PROFILE  = "6165628911519535262"
EMOJI_TEST_SEQ     = "6235394337346165182"
EMOJI_PREMIUM      = "6291764155313558218"
EMOJI_INTRO        = "6311999627440691097"
EMOJI_ADD_MSG      = "5397916757333654639"
EMOJI_REMOVE_MSG   = "6120511091823874486"
EMOJI_REORDER      = "5359441070201513074"
EMOJI_LIST_MSG     = "6168060795016976899"
EMOJI_REPLY_SET    = "6242498410822244114"
EMOJI_REPLY_REMOVE = "6266787717896476444"
EMOJI_BACK         = "6264961759795221684"
EMOJI_CANCEL       = "6276025694333966034"
EMOJI_BLUE         = "6321140649286442286"
EMOJI_RED          = "6163177640539721557"
EMOJI_GREEN        = "5260640681906419699"
EMOJI_DEFAULT      = "4956273117191213833"
EMOJI_YES          = "5260640681906419699"
EMOJI_NO           = "6120660741369369103"
EMOJI_SAME_ROW     = "4956591954088428445"
EMOJI_NEXT_ROW     = "4958845510543737828"
EMOJI_DONE         = "5260640681906419699"
EMOJI_ADD_ANOTHER  = "6269130601081608904"
EMOJI_CHANGE_NAME  = "6282641460093260838"
EMOJI_CHANGE_BIO   = "6269425390456935341"
EMOJI_CHANGE_DESC  = "6120953460570460166"

# --- Extra premium emojis from user ---
EMOJI_UP           = "5462995330163289902"   # ⏫
EMOJI_SWORD1       = "5454014806950429357"   # ⚔️
EMOJI_STAR1        = "6165853967805845075"   # 🌟
EMOJI_STAR2        = "6163685425933193643"   # 🌟
EMOJI_SPARKLE      = "6165894413512871182"   # 💫
EMOJI_TOAST        = "4956619819836244992"   # 🥂
EMOJI_BOOM         = "6163233930381103380"   # 💥
EMOJI_BUTTERFLY    = "6163205317308977224"   # 🦋
EMOJI_LIGHTNING1   = "6163348228050784800"   # ⚡️
EMOJI_NEW          = "6165621962262450849"   # 🆕
EMOJI_CHART        = "6203743692549788189"   # 📊
EMOJI_SMILE        = "6163208362440790474"   # 😊
EMOJI_CHICKEN      = "6163322703060144015"   # 🐔
EMOJI_SWORD2       = "6244638666040284878"   # ⚔️
EMOJI_CARD         = "6170133383025267499"   # 🃏
EMOJI_STAR3        = "6163712312428468196"   # ⭐️
EMOJI_TROPHY       = "6165711370596650697"   # 🏆
EMOJI_LIGHTNING2   = "6163534904509338440"   # ⚡️
EMOJI_STAR4        = "6163236082159718244"   # 🌟
EMOJI_BUILD        = "6163665505874874605"   # 🏗
EMOJI_SNAKE        = "6237571928714910827"   # 🐍
EMOJI_SKULL        = "6224482822606819520"   # 💀
EMOJI_ROSE         = "6118641900581818936"   # 🌹
EMOJI_COOL         = "6224149653403734022"   # 😎
EMOJI_DEVIL        = "6336780965968353744"   # 😈
EMOJI_BAT          = "6339164578328352187"   # 🦇
EMOJI_CHECK1       = "6276282773896434467"   # ✔️
EMOJI_ROCKET       = "6276311855119994929"   # 🚀
EMOJI_GIFT1        = "6276192588173154244"   # 🎁
EMOJI_GIFT2        = "6276134137963222688"   # 🎁
EMOJI_BRAIN        = "5373180412883378717"   # 🧠
EMOJI_ICE          = "5370862723976405092"   # ❄️
EMOJI_THINK        = "5370919202796348364"   # 🤔
EMOJI_DROP         = "5373135805353041178"   # 💧
EMOJI_GEAR         = "5370935802844946281"   # ⚙️
EMOJI_REPEAT       = "5415588516237157133"   # 🔂
EMOJI_OK           = "5260640681906419699"   # ✅
EMOJI_DEVIL2       = "5260553279321944543"   # 😈
EMOJI_OK2          = "5262880537416054812"   # ✅
EMOJI_GIFT3        = "5427315847129478207"   # 🎁
EMOJI_SIREN        = "5260750418320836046"   # 🚨
EMOJI_FIREWORK     = "6199293238847740460"   # 🎇
EMOJI_GLOW         = "6276044051024189481"   # 🌟
EMOJI_SKULL2       = "6264911817915505675"   # ☠️
EMOJI_DINO         = "6235524376070984680"   # 🦖
EMOJI_YIN          = "6163667490149765932"   # ☯️
EMOJI_CARD2        = "6321283959460208089"   # 💳
EMOJI_BLUEDOT      = "6321140649286442286"   # 🔵
EMOJI_PIRATE       = "6300703159077570304"   # 🏴‍☠️
EMOJI_LIGHTNING3   = "5366382111014010097"   # ⚡️
EMOJI_VAMPIRE      = "5366576600018072985"   # 🧛
EMOJI_DOG          = "5363976955098053119"   # 🐶
EMOJI_LION         = "5415974569372565930"   # 🦁
EMOJI_LIGHTNING4   = "5416028557111474714"   # ⚡️
EMOJI_ZEBRA        = "5416049108529987626"   # 🦓

def btn(text, style=None, emoji_id=None):
    """Build a raw reply keyboard button dict."""
    b = {"text": text}
    if style:
        b["style"] = style
    if emoji_id:
        b["icon_custom_emoji_id"] = emoji_id
    return b

# ═══════════════════════════════════════════════════════════════════
# SEMAPHORE
# ═══════════════════════════════════════════════════════════════════
sequence_semaphore = asyncio.Semaphore(SEQUENCE_CONCURRENCY)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID not set in .env")

print(r"""
██████╗  ██████╗ ████████╗
██╔══██╗██╔═══██╗╚══██╔══╝
██████╔╝██║   ██║   ██║
██╔══██╗██║   ██║   ██║
██████╔╝╚██████╔╝   ██║
╚═════╝  ╚═════╝    ╚═╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
◆ BOT STARTED SUCCESSFULLY
◆ DATABASE LOADED 
◆ TELEGRAM API CONNECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# ═══════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════
class BotInternalError(Exception): pass
class DBError(BotInternalError): pass
class APIError(BotInternalError): pass

# ═══════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════
def retry_db(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(MAX_RETRIES_DB):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                last_exc = e
                if attempt < MAX_RETRIES_DB - 1:
                    time.sleep(0.1 * (attempt + 1))
                else:
                    raise DBError(f"DB op failed: {e}")
            except Exception as e:
                raise DBError(f"DB unexpected: {e}")
        raise DBError("Unexpected retry exit")
    return wrapper

@contextmanager
def get_conn():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            try: conn.rollback()
            except: pass
        raise DBError(f"Commit failed: {e}")
    except Exception as e:
        if conn:
            try: conn.rollback()
            except: pass
        raise DBError(f"Connection error: {e}")
    finally:
        if conn:
            try: conn.close()
            except: pass

@retry_db
def init_db() -> None:
    with get_conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                first_seen DATE NOT NULL DEFAULT (DATE('now')),
                username   TEXT,
                first_name TEXT,
                last_name  TEXT
            );
            CREATE TABLE IF NOT EXISTS subadmins (
                user_id  INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT (DATETIME('now')),
                role TEXT DEFAULT 'subadmin'
            );
            CREATE TABLE IF NOT EXISTS messages (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id    INTEGER NOT NULL,
                position      INTEGER NOT NULL UNIQUE,
                content_json  TEXT,
                buttons_json  TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS state (
                user_id INTEGER PRIMARY KEY,
                action  TEXT NOT NULL,
                data    TEXT
            );
            CREATE TABLE IF NOT EXISTS pending_requests (
                user_id    INTEGER,
                chat_id    INTEGER,
                created_at TIMESTAMP DEFAULT (DATETIME('now')),
                PRIMARY KEY (user_id, chat_id)
            );
            CREATE TABLE IF NOT EXISTS subadmin_perms (
                user_id INTEGER PRIMARY KEY,
                can_broadcast INTEGER DEFAULT 1,
                can_stats INTEGER DEFAULT 1,
                can_manage_seq INTEGER DEFAULT 0,
                can_manage_subadmins INTEGER DEFAULT 0,
                can_change_source INTEGER DEFAULT 0,
                can_set_post_button INTEGER DEFAULT 0,
                can_manage_bot_profile INTEGER DEFAULT 0,
                can_test_sequence INTEGER DEFAULT 0,
                can_approve_requests INTEGER DEFAULT 0,
                can_toggle_auto_approve INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES subadmins(user_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS post_sequence (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                message_text TEXT,
                buttons_json TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS intro (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                message_text TEXT
            );
            CREATE TABLE IF NOT EXISTS direct_reply (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                message_id INTEGER,
                content_json TEXT,
                buttons_json TEXT DEFAULT '[]'
            );
        """)
        for col in ["content_json", "buttons_json"]:
            try: c.execute(f"ALTER TABLE messages ADD COLUMN {col} TEXT DEFAULT '[]'")
            except: pass
        for perm in ["can_manage_bot_profile","can_test_sequence","can_approve_requests","can_toggle_auto_approve"]:
            try: c.execute(f"ALTER TABLE subadmin_perms ADD COLUMN {perm} INTEGER DEFAULT 0")
            except: pass
        try:
            c.execute("ALTER TABLE users ADD COLUMN username TEXT")
            c.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
            c.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
        except: pass
        try: c.execute("ALTER TABLE post_sequence ADD COLUMN buttons_json TEXT DEFAULT '[]'")
        except: pass
        try: c.execute("CREATE TABLE IF NOT EXISTS intro (id INTEGER PRIMARY KEY CHECK (id = 1), message_text TEXT)")
        except: pass
        try: c.execute("CREATE TABLE IF NOT EXISTS direct_reply (id INTEGER PRIMARY KEY CHECK (id=1), message_id INTEGER, content_json TEXT, buttons_json TEXT DEFAULT '[]')")
        except: pass

        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('source_chat_id', ?)", (str(SOURCE_CHAT_ID),))
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('auto_approve', '0')")
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('start_enabled', '1')")
        c.execute("INSERT OR IGNORE INTO post_sequence (id) VALUES (1)")
        c.execute("INSERT OR IGNORE INTO intro (id) VALUES (1)")
        c.execute("INSERT OR IGNORE INTO direct_reply (id) VALUES (1)")

# ── Users ──
@retry_db
def db_upsert_user(user_id: int, username=None, first_name=None, last_name=None) -> bool:
    with get_conn() as c:
        return c.execute(
            "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name, last_name=excluded.last_name",
            (user_id, username, first_name, last_name)
        ).rowcount > 0

@retry_db
def db_total_users() -> int:
    with get_conn() as c:
        r = c.execute("SELECT COUNT(*) FROM users").fetchone()
        return r[0] if r else 0

@retry_db
def db_daily_users() -> int:
    with get_conn() as c:
        r = c.execute("SELECT COUNT(*) FROM users WHERE first_seen = ?", (date.today().isoformat(),)).fetchone()
        return r[0] if r else 0

@retry_db
def db_all_user_ids() -> list:
    with get_conn() as c:
        rows = c.execute("SELECT user_id FROM users").fetchall()
        return [r["user_id"] for r in rows] if rows else []

# ── Roles & Admins ──
def is_main_admin(uid): return uid == ADMIN_ID

@retry_db
def db_get_admin_role(uid):
    with get_conn() as c:
        row = c.execute("SELECT role FROM subadmins WHERE user_id = ?", (uid,)).fetchone()
        return row["role"] if row else None

def db_is_subadmin(uid): return db_get_admin_role(uid) is not None
def db_is_admin(uid): return is_main_admin(uid) or db_get_admin_role(uid) == "admin"
def is_any_admin(uid): return is_main_admin(uid) or db_is_subadmin(uid)

@retry_db
def db_add_admin(uid, role="subadmin"):
    with get_conn() as c:
        try:
            c.execute("INSERT INTO subadmins (user_id, role) VALUES (?,?)", (uid, role))
            c.execute("INSERT INTO subadmin_perms (user_id) VALUES (?)", (uid,))
            if role == "admin":
                c.execute("UPDATE subadmin_perms SET can_approve_requests=1, can_toggle_auto_approve=1 WHERE user_id=?", (uid,))
            return True
        except sqlite3.IntegrityError:
            return False

@retry_db
def db_remove_subadmin(uid):
    with get_conn() as c:
        return c.execute("DELETE FROM subadmins WHERE user_id=?", (uid,)).rowcount > 0

@retry_db
def db_list_admins(role_filter=None):
    with get_conn() as c:
        if role_filter:
            rows = c.execute("SELECT user_id, role FROM subadmins WHERE role=?", (role_filter,)).fetchall()
        else:
            rows = c.execute("SELECT user_id, role FROM subadmins").fetchall()
        return rows if rows else []

def db_get_all_admin_ids():
    ids = [ADMIN_ID]
    ids.extend(r["user_id"] for r in db_list_admins())
    return ids

# ── Permissions ──
PERMISSIONS = [
    "can_broadcast","can_stats","can_manage_seq","can_change_source",
    "can_set_post_button","can_manage_subadmins","can_manage_bot_profile",
    "can_test_sequence","can_approve_requests","can_toggle_auto_approve"
]
PERM_DISPLAY = {
    "can_broadcast":"Broadcast","can_stats":"Stats",
    "can_manage_seq":"Manage Sequence","can_change_source":"Change Source",
    "can_set_post_button":"Set Post Button","can_manage_subadmins":"Manage Subadmins",
    "can_manage_bot_profile":"Bot Profile","can_test_sequence":"Test Sequence",
    "can_approve_requests":"Approve All Requests","can_toggle_auto_approve":"Auto‑Approve Toggle"
}

@retry_db
def db_get_subadmin_perms(uid):
    with get_conn() as c:
        row = c.execute("SELECT * FROM subadmin_perms WHERE user_id=?", (uid,)).fetchone()
        return {k:bool(row[k]) for k in row.keys() if k!="user_id"} if row else {}

@retry_db
def db_set_subadmin_perm(uid, perm, value):
    with get_conn() as c:
        c.execute(f"UPDATE subadmin_perms SET {perm}=? WHERE user_id=?", (int(value), uid))

def db_has_perm(uid, perm):
    if is_main_admin(uid): return True
    return db_get_subadmin_perms(uid).get(perm, False)

# ── Auto‑approve ──
@retry_db
def db_get_auto_approve():
    with get_conn() as c:
        row = c.execute("SELECT value FROM config WHERE key='auto_approve'").fetchone()
        return row and row["value"]=="1"
@retry_db
def db_set_auto_approve(value):
    with get_conn() as c:
        c.execute("UPDATE config SET value=? WHERE key='auto_approve'", ("1" if value else "0",))

# ── Pending requests ──
@retry_db
def db_add_pending_request(uid, chat_id):
    with get_conn() as c:
        c.execute("INSERT OR IGNORE INTO pending_requests (user_id,chat_id) VALUES (?,?)", (uid,chat_id))
@retry_db
def db_get_pending_requests():
    with get_conn() as c:
        rows = c.execute("SELECT user_id, chat_id FROM pending_requests").fetchall()
        return rows if rows else []
@retry_db
def db_clear_pending_requests():
    with get_conn() as c:
        c.execute("DELETE FROM pending_requests")

# ── Intro / Direct reply ──
@retry_db
def db_get_intro():
    with get_conn() as c:
        row = c.execute("SELECT message_text FROM intro WHERE id=1").fetchone()
        return row["message_text"] if row and row["message_text"] else None
@retry_db
def db_set_intro(text):
    with get_conn() as c:
        c.execute("UPDATE intro SET message_text=? WHERE id=1", (text,))

@retry_db
def db_get_direct_reply():
    with get_conn() as c:
        row = c.execute("SELECT * FROM direct_reply WHERE id=1").fetchone()
        return dict(row) if row else {}
@retry_db
def db_set_direct_reply(message_id, content_json):
    with get_conn() as c:
        c.execute("UPDATE direct_reply SET message_id=?, content_json=?, buttons_json='[]' WHERE id=1", (message_id,content_json))
@retry_db
def db_clear_direct_reply():
    with get_conn() as c:
        c.execute("UPDATE direct_reply SET message_id=NULL, content_json=NULL, buttons_json='[]' WHERE id=1")

# ── Message sequence ──
@retry_db
def db_add_message(message_id, position, content_json=None, buttons_json='[]'):
    with get_conn() as c:
        try:
            c.execute("INSERT OR REPLACE INTO messages (message_id,position,content_json,buttons_json) VALUES (?,?,?,?)",
                      (message_id,position,content_json,buttons_json))
            return True
        except sqlite3.IntegrityError:
            return False
@retry_db
def db_remove_message(message_id):
    with get_conn() as c:
        return c.execute("DELETE FROM messages WHERE message_id=?", (message_id,)).rowcount>0
@retry_db
def db_remove_message_pos(position):
    with get_conn() as c:
        return c.execute("DELETE FROM messages WHERE position=?", (position,)).rowcount>0
@retry_db
def db_get_messages():
    with get_conn() as c:
        rows = c.execute("SELECT * FROM messages ORDER BY position ASC").fetchall()
        return rows if rows else []
@retry_db
def db_reorder_message(message_id, new_position):
    with get_conn() as c:
        c.execute("UPDATE messages SET position=-1 WHERE position=? AND message_id!=?", (new_position,message_id))
        ok = c.execute("UPDATE messages SET position=? WHERE message_id=?", (new_position,message_id)).rowcount>0
        c.execute("DELETE FROM messages WHERE position=-1")
        return ok
@retry_db
def db_update_message_buttons(message_id, buttons_json):
    with get_conn() as c:
        c.execute("UPDATE messages SET buttons_json=? WHERE message_id=?", (buttons_json, message_id))
@retry_db
def db_get_message_by_id(message_id):
    with get_conn() as c:
        row = c.execute("SELECT * FROM messages WHERE message_id=?", (message_id,)).fetchone()
        return dict(row) if row else None

# ── Source / Config ──
@retry_db
def db_get_source_chat_id():
    with get_conn() as c:
        row = c.execute("SELECT value FROM config WHERE key='source_chat_id'").fetchone()
        return int(row["value"]) if row else SOURCE_CHAT_ID
@retry_db
def db_set_source_chat_id(chat_id):
    with get_conn() as c:
        c.execute("UPDATE config SET value=? WHERE key='source_chat_id'", (str(chat_id),))

# ── Post‑sequence custom message ──
@retry_db
def db_get_post_sequence():
    with get_conn() as c:
        row = c.execute("SELECT message_text, buttons_json FROM post_sequence WHERE id=1").fetchone()
        return dict(row) if row else {}
@retry_db
def db_set_post_sequence(message_text, buttons_json='[]'):
    with get_conn() as c:
        c.execute("UPDATE post_sequence SET message_text=?, buttons_json=? WHERE id=1", (message_text,buttons_json))

# ── State machine ──
@retry_db
def db_set_state(uid, action, data=""):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO state (user_id,action,data) VALUES (?,?,?)", (uid,action,data))
@retry_db
def db_get_state(uid):
    with get_conn() as c:
        row = c.execute("SELECT action, data FROM state WHERE user_id=?", (uid,)).fetchone()
        return (row["action"], row["data"]) if row else (None, None)
@retry_db
def db_clear_state(uid):
    with get_conn() as c:
        c.execute("DELETE FROM state WHERE user_id=?", (uid,))

# ═══════════════════════════════════════════════════════════════════
# API HELPERS (raw requests)
# ═══════════════════════════════════════════════════════════════════
def _post(endpoint, payload):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None

def _build_inline_keyboard(buttons_json: str):
    if not buttons_json or buttons_json == "[]":
        return None
    try:
        buttons = json.loads(buttons_json)
    except:
        return None
    if not buttons:
        return None

    rows = {}
    for b in buttons:
        rows.setdefault(b.get("row", 0), []).append(b)

    inline_keyboard = []
    for idx in sorted(rows.keys()):
        row_btns = []
        for b in rows[idx]:
            button_dict = {
                "text": b["text"],
                "url": b["url"]
            }
            if b.get("emoji_id"):
                button_dict["icon_custom_emoji_id"] = b["emoji_id"]
            if "style" in b:
                button_dict["style"] = b["style"]
            row_btns.append(button_dict)
        inline_keyboard.append(row_btns)

    return {"inline_keyboard": inline_keyboard}

def copy_message_with_buttons(from_chat_id, message_id, to_chat_id, buttons_json):
    resp = _post("copyMessage", {
        "chat_id": to_chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    })
    if not resp or not resp.get("ok"):
        return resp

    new_msg_id = resp["result"]["message_id"]
    reply_markup = _build_inline_keyboard(buttons_json)
    if not reply_markup:
        return resp

    _post("editMessageReplyMarkup", {
        "chat_id": to_chat_id,
        "message_id": new_msg_id,
        "reply_markup": reply_markup
    })
    return resp

# ═══════════════════════════════════════════════════════════════════
# RAW REPLY KEYBOARD BUILDER
# ═══════════════════════════════════════════════════════════════════
def build_reply_keyboard_raw(buttons_rows, resize_keyboard=True):
    keyboard = []
    for row in buttons_rows:
        row_buttons = []
        for b in row:
            if not isinstance(b, dict):
                b = {"text": str(b)}
            row_buttons.append(b)
        keyboard.append(row_buttons)
    return {"keyboard": keyboard, "resize_keyboard": resize_keyboard}

def pe(emoji_id: str, fallback: str = "⭐") -> str:
    """Inline premium emoji tag for HTML messages."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def send_raw_message(chat_id, text, reply_markup_dict, parse_mode="HTML"):
    return _post("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": reply_markup_dict
    })

# ═══════════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════════

def admin_panel_kb_raw():
    auto = db_get_auto_approve()
    auto_text = f"Auto‑Approve: {'ON' if auto else 'OFF'}"
    return build_reply_keyboard_raw([
        [btn("Broadcast", style="primary", emoji_id=EMOJI_BROADCAST),
         btn("Stats", style="primary", emoji_id=EMOJI_CHART)],
        [btn("Admins", style="success", emoji_id=EMOJI_TROPHY),
         btn("Subadmins", style="primary", emoji_id=EMOJI_SUBADMINS)],
        [btn("Message Sequence", style="success", emoji_id=EMOJI_SEQUENCE),
         btn("Approve All Requests", style="danger", emoji_id=EMOJI_APPROVE)],
        [btn(auto_text, style="primary" if auto else "danger", emoji_id=EMOJI_AUTO_APPROVE)],
        [btn("Subadmin Permissions", style="primary", emoji_id=EMOJI_PERMISSIONS),
         btn("Bot Profile", style="primary", emoji_id=EMOJI_BOT_PROFILE)],
        [btn("Test Sequence", style="success", emoji_id=EMOJI_TEST_SEQ),
         btn("Premium", style="primary", emoji_id=EMOJI_PREMIUM)]
    ])

def subadmin_panel_kb_raw(uid):
    perms = db_get_subadmin_perms(uid)
    rows = []
    row = []
    if perms.get("can_broadcast"):
        row.append(btn("Broadcast", style="primary", emoji_id=EMOJI_BROADCAST))
    if perms.get("can_stats"):
        row.append(btn("Stats", style="primary", emoji_id=EMOJI_CHART))
    if row: rows.append(row)
    row = []
    if perms.get("can_manage_seq"):
        row.append(btn("Message Sequence", style="success", emoji_id=EMOJI_SEQUENCE))
    if perms.get("can_approve_requests"):
        row.append(btn("Approve All Requests", style="danger", emoji_id=EMOJI_APPROVE))
    if row: rows.append(row)
    row = []
    if perms.get("can_manage_subadmins"):
        row.append(btn("Subadmins", style="primary", emoji_id=EMOJI_SUBADMINS))
    if perms.get("can_manage_bot_profile"):
        row.append(btn("Bot Profile", style="primary", emoji_id=EMOJI_BOT_PROFILE))
    if row: rows.append(row)
    row = []
    if perms.get("can_test_sequence"):
        row.append(btn("Test Sequence", style="primary", emoji_id=EMOJI_TEST_SEQ))
    if perms.get("can_toggle_auto_approve"):
        auto = db_get_auto_approve()
        auto_text = f"Auto‑Approve: {'ON' if auto else 'OFF'}"
        row.append(btn(auto_text, style="primary" if auto else "default", emoji_id=EMOJI_AUTO_APPROVE))
    if row: rows.append(row)
    rows.append([btn("Premium", style="primary", emoji_id=EMOJI_PREMIUM)])
    if not rows:
        rows.append([btn("No permissions")])
    return build_reply_keyboard_raw(rows)

def sequence_panel_kb_raw():
    intro_set = "Set Intro Msg" if not db_get_intro() else "Update Intro Msg"
    reply = db_get_direct_reply()
    reply_set = "Set Reply Msg" if not reply.get("message_id") else "Update Reply Msg"
    return build_reply_keyboard_raw([
        [btn(intro_set, style="primary", emoji_id=EMOJI_INTRO)],
        [btn("Add Message", style="success", emoji_id=EMOJI_ADD_MSG),
         btn("Remove Message", style="danger", emoji_id=EMOJI_REMOVE_MSG)],
        [btn("Reorder Message", style="primary", emoji_id=EMOJI_REORDER),
         btn("List Messages", style="primary", emoji_id=EMOJI_LIST_MSG)],
        [btn(reply_set, style="primary", emoji_id=EMOJI_REPLY_SET),
         btn("Remove Reply Msg", style="danger", emoji_id=EMOJI_REPLY_REMOVE)],
        [btn("Back to Panel", style="danger", emoji_id=EMOJI_BACK),
         btn("Premium", style="primary", emoji_id=EMOJI_PREMIUM)]
    ])

def bot_profile_kb_raw():
    return build_reply_keyboard_raw([
        [btn("Change Name", style="primary", emoji_id=EMOJI_CHANGE_NAME),
         btn("Change Bio", style="primary", emoji_id=EMOJI_CHANGE_BIO)],
        [btn("Change Description", style="primary", emoji_id=EMOJI_CHANGE_DESC)],
        [btn("Back to Panel", style="success", emoji_id=EMOJI_BACK),
         btn("Premium", style="primary", emoji_id=EMOJI_PREMIUM)]
    ])

def cancel_kb_raw():
    return build_reply_keyboard_raw([
        [btn("Cancel", style="danger", emoji_id=EMOJI_CANCEL)]
    ])

def staff_kb_raw(uid):
    return admin_panel_kb_raw() if is_main_admin(uid) else subadmin_panel_kb_raw(uid)

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
async def run(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))

def extract_message_content(msg):
    data = {}
    if msg.text: data["type"]="text"; data["text"]=msg.text
    elif msg.caption: data["type"]="caption"; data["caption"]=msg.caption
    else: data["type"]="media"
    if msg.photo: data["photo"]=msg.photo[-1].file_id
    if msg.video: data["video"]=msg.video.file_id
    if msg.document: data["document"]=msg.document.file_id
    if msg.audio: data["audio"]=msg.audio.file_id
    if msg.voice: data["voice"]=msg.voice.file_id
    if msg.sticker: data["sticker"]=msg.sticker.file_id
    if msg.animation: data["animation"]=msg.animation.file_id
    if msg.video_note: data["video_note"]=msg.video_note.file_id
    if msg.caption and msg.caption.strip(): data["caption"]=msg.caption
    return json.dumps(data)

PLACEHOLDER_HELP = (
    f'{pe(EMOJI_BRAIN,"🧠")} <b>Placeholders you can use:</b>\n'
    "• `{first_name}` – user's first name\n"
    "• `{last_name}` – user's last name\n"
    "• `{username}` – @username (or first name)\n"
    "• `{id}` – numeric user ID"
)

def escape_placeholders_and_html(text: str, user) -> str:
    first = html_escape(user.first_name or "")
    last = html_escape(user.last_name or "")
    username = html_escape(user.username or user.first_name or "")
    uid = str(user.id)
    return (text
            .replace("{first_name}", first)
            .replace("{last_name}", last)
            .replace("{username}", username)
            .replace("{id}", uid))

# ═══════════════════════════════════════════════════════════════════
# SEQUENCE DELIVERY
# ═══════════════════════════════════════════════════════════════════
async def send_sequence_to_user(bot, user_id: int):
    async with sequence_semaphore:
        try:
            user = await bot.get_chat(user_id)
        except:
            return

        intro = await run(db_get_intro)
        if intro:
            safe_intro = escape_placeholders_and_html(intro, user)
            try:
                await bot.send_message(chat_id=user_id, text=safe_intro, parse_mode="HTML")
            except:
                pass

        source = await run(db_get_source_chat_id)

        for row in await run(db_get_messages):
            if row["buttons_json"] and row["buttons_json"] != "[]":
                resp = await run(copy_message_with_buttons, source, row["message_id"], user_id, row["buttons_json"])
                if resp and resp.get("ok"):
                    continue
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=source, message_id=row["message_id"])
            except Forbidden:
                break
            except:
                continue

        post = await run(db_get_post_sequence)
        if post.get("message_text"):
            safe_post = escape_placeholders_and_html(post["message_text"], user)
            keyboard = _build_inline_keyboard(post.get("buttons_json", "[]"))
            payload = {
                "chat_id": user_id,
                "text": safe_post,
                "parse_mode": "HTML"
            }
            if keyboard:
                payload["reply_markup"] = keyboard
            _post("sendMessage", payload)

# ═══════════════════════════════════════════════════════════════════
# BROADCAST SYSTEM — SUPERFAST, NO SOURCE CHANNEL NEEDED
# Directly forwards the stored message_id/content to every user.
# Supports ALL media types + premium emoji inline buttons.
# Fires & forgets — no "done" confirmation, just instant launch.
# ═══════════════════════════════════════════════════════════════════

async def _broadcast_one(bot, uid: int, from_chat_id: int, message_id: int) -> str:
    """Send one broadcast message. Returns 'sent' | 'blocked' | 'failed'."""
    for attempt in range(MAX_RETRIES_API):
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            return "sent"
        except Forbidden:
            return "blocked"
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.1)
        except (NetworkError, TimedOut):
            if attempt < MAX_RETRIES_API - 1:
                await asyncio.sleep(0.3 * (attempt + 1))
            else:
                return "failed"
        except TelegramError:
            return "failed"
        except Exception:
            return "failed"
    return "failed"


async def _run_broadcast(bot, from_chat_id: int, message_id: int, admin_id: int):
    """Blast message to every user concurrently. Silent, no callbacks."""
    uids = await run(db_all_user_ids)
    if not uids:
        return

    sem = asyncio.Semaphore(BROADCAST_CONCURRENCY)

    async def worker(uid):
        async with sem:
            return await _broadcast_one(bot, uid, from_chat_id, message_id)

    tasks = [asyncio.create_task(worker(uid)) for uid in uids]
    await asyncio.gather(*tasks, return_exceptions=True)
    # No callback/confirmation sent — silent completion


# ═══════════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def cmd_start(update, context):
    user = update.effective_user
    if not user: return
    await run(db_upsert_user, user.id, user.username, user.first_name, user.last_name)
    await run(db_clear_state, user.id)
    if is_any_admin(user.id):
        await open_panel(update, user.id)
    else:
        asyncio.create_task(send_sequence_to_user(context.bot, user.id))

async def _approve_one(chat_id, user_id, bot):
    try:
        await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        return True
    except Exception:
        return False

async def approve_all_pending(bot):
    pending = await run(db_get_pending_requests)
    if not pending:
        return 0, 0
    sem = asyncio.Semaphore(APPROVAL_CONCURRENCY)
    async def worker(req):
        async with sem:
            return await _approve_one(req["chat_id"], req["user_id"], bot)
    tasks = [asyncio.create_task(worker(req)) for req in pending]
    results = await asyncio.gather(*tasks)
    approved = sum(results)
    await run(db_clear_pending_requests)
    return approved, len(pending) - approved

async def on_join_request(update, context):
    jr = update.chat_join_request
    if not jr: return
    user = jr.from_user
    if not user: return
    await run(db_upsert_user, user.id, user.username, user.first_name, user.last_name)
    asyncio.create_task(send_sequence_to_user(context.bot, user.id))
    if await run(db_get_auto_approve):
        try: await context.bot.approve_chat_join_request(chat_id=jr.chat.id, user_id=user.id)
        except: pass
    else:
        await run(db_add_pending_request, user.id, jr.chat.id)

async def cmd_stats(update, context):
    user = update.effective_user
    if not user or not is_any_admin(user.id): return
    if not db_has_perm(user.id, "can_stats"):
        send_raw_message(user.id, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', cancel_kb_raw())
        return
    total = await run(db_total_users)
    daily = await run(db_daily_users)
    pending = len(await run(db_get_pending_requests))
    auto = "ON" if await run(db_get_auto_approve) else "OFF"
    send_raw_message(user.id,
        f'{pe(EMOJI_CHART,"📊")} <b>Bot Statistics</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{pe(EMOJI_STAR1,"⭐")} <b>Total users:</b> <code>{total}</code>\n'
        f'{pe(EMOJI_FIREWORK,"🎇")} <b>New today:</b> <code>{daily}</code>\n'
        f'{pe(EMOJI_SIREN,"🚨")} <b>Pending approvals:</b> <code>{pending}</code>\n'
        f'{pe(EMOJI_REPEAT,"🔂")} <b>Auto‑approve:</b> <code>{auto}</code>',
        staff_kb_raw(user.id))

async def cmd_help(update, context):
    send_raw_message(update.effective_user.id,
        f'{pe(EMOJI_BOT_PROFILE,"🤖")} <b>Bot Help</b>\n━━━━━━━━━━━━━━━━━━━━━\nUse /start to begin.\nIf you are an admin, the panel will appear automatically.',
        cancel_kb_raw())

async def open_panel(update, uid, note=""):
    await run(db_clear_state, uid)
    if is_main_admin(uid):
        txt = f'{pe(EMOJI_TROPHY,"🏆")} <b>SUPER ADMIN PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nUse the buttons below.'
        kb = admin_panel_kb_raw()
    elif db_is_subadmin(uid):
        role = db_get_admin_role(uid)
        title = "ADMIN" if role == "admin" else "SUBADMIN"
        txt = f'{pe(EMOJI_GEAR,"⚙️")} <b>{title} PANEL</b>\n━━━━━━━━━━━━━━━━━━━━━\nYour accessible actions:'
        kb = subadmin_panel_kb_raw(uid)
    else:
        return
    if note:
        txt = f"{note}\n\n{txt}"
    send_raw_message(uid, txt, kb)

async def _open_sequence_panel(update, uid, note=""):
    txt = f'{pe(EMOJI_SEQUENCE,"📨")} <b>Message Sequence Panel</b>'
    if note:
        txt = f"{note}\n\n{txt}"
    txt += "\n━━━━━━━━━━━━━━━━━━━━━"
    send_raw_message(uid, txt, sequence_panel_kb_raw())

async def _open_bot_profile_panel(update, uid, note=""):
    txt = f'{pe(EMOJI_BOT_PROFILE,"🤖")} <b>Bot Profile Management</b>'
    if note:
        txt = f"{note}\n\n{txt}"
    txt += "\n━━━━━━━━━━━━━━━━━━━━━"
    send_raw_message(uid, txt, bot_profile_kb_raw())

# ═══════════════════════════════════════════════════════════════════
# MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════════

async def on_message(update, context):
    msg = update.message
    user = update.effective_user
    if not user or not msg: return
    uid = user.id
    text = (msg.text or msg.caption or "").strip()

    if not is_any_admin(uid):
        reply = await run(db_get_direct_reply)
        if reply.get("message_id"):
            source = await run(db_get_source_chat_id)
            try: await context.bot.copy_message(chat_id=uid, from_chat_id=source, message_id=reply["message_id"])
            except: pass
        return

    action, data = await run(db_get_state, uid)

    if text == "Cancel":
        if is_any_admin(uid):
            await open_panel(update, uid, f'{pe(EMOJI_BACK,"↩️")} <b>Cancelled.</b>')
        else:
            await run(db_clear_state, uid)
            send_raw_message(uid, f'{pe(EMOJI_BACK,"↩️")} <b>Cancelled.</b>', build_reply_keyboard_raw([]))
        return

    # ── BROADCAST ──
    # Admin sends the message → copy it directly from their chat to every user.
    # No source channel, no staging, no confirmation. Pure fire-and-forget.
    if action == "awaiting_broadcast":
        if not db_has_perm(uid, "can_broadcast"):
            await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)

        from_chat = msg.chat_id
        from_msg  = msg.message_id

        # Show panel immediately — no "started" message
        await open_panel(update, uid)

        # Fire and forget
        asyncio.create_task(_run_broadcast(context.bot, from_chat, from_msg, uid))
        return

    # ── Admin add/remove states ──
    if action == "awaiting_add_admin":
        if not is_main_admin(uid): await open_panel(update, uid, f'{pe(EMOJI_SKULL2,"☠️")} <b>Superadmin only.</b>'); return
        await run(db_clear_state, uid)
        reply = _handle_add_remove_admin(uid, text, "admin")
        await open_panel(update, uid, reply); return
    if action == "awaiting_add_subadmin":
        if not (is_main_admin(uid) or db_is_admin(uid)): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        reply = _handle_add_remove_admin(uid, text, "subadmin")
        await open_panel(update, uid, reply); return
    if action in ("awaiting_remove_admin", "awaiting_remove_subadmin"):
        if action == "awaiting_remove_admin" and not is_main_admin(uid): await open_panel(update, uid, f'{pe(EMOJI_SKULL2,"☠️")} <b>Superadmin only.</b>'); return
        if action == "awaiting_remove_subadmin" and not (is_main_admin(uid) or db_is_admin(uid)): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        reply = _handle_remove_admin(uid, text)
        await open_panel(update, uid, reply); return

    # ── Intro ──
    if action == "awaiting_set_intro":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        await run(db_set_intro, text)
        await open_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Intro message updated.</b>\n\n{PLACEHOLDER_HELP}'); return

    # ── Direct reply ──
    if action == "awaiting_set_reply":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        source = await run(db_get_source_chat_id)
        try:
            sent = await msg.forward(chat_id=source); mid = sent.message_id
        except: await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>Could not forward to source chat.</b>'); return
        content = extract_message_content(msg)
        await run(db_set_direct_reply, mid, content)
        await run(db_clear_state, uid)
        await _open_sequence_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Reply message saved.</b>'); return
    if action == "awaiting_confirm_remove_reply":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        if text.lower()!="yes": await _open_sequence_panel(update, uid, f'{pe(EMOJI_BACK,"↩️")} <b>Removal cancelled.</b>'); return
        await run(db_clear_direct_reply)
        await _open_sequence_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Reply message removed.</b>'); return

    # ── Add message: position ──
    if action == "awaiting_addmsg_pos":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        try:
            pos = int(text)
            if pos<1:
                send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>Position must be ≥ 1.</b>', cancel_kb_raw()); return
            await run(db_set_state, uid, "awaiting_addmsg_msg", str(pos))
            send_raw_message(uid, f'{pe(EMOJI_OK,"✅")} <b>Position</b> <code>{pos}</code> <b>set.</b> Now send the message (any type).', cancel_kb_raw())
        except ValueError:
            send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>Send a valid number.</b>', cancel_kb_raw())
        return

    # ── Add message msg ──
    if action == "awaiting_addmsg_msg":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        try: pos = int(data)
        except: await run(db_clear_state, uid); await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>State error.</b>'); return
        source = await run(db_get_source_chat_id)
        try:
            sent = await msg.forward(chat_id=source)
            mid = sent.message_id
        except Exception as e:
            await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>Could not forward to source:</b> <code>{e}</code>'); return
        content = extract_message_content(msg)
        await run(db_add_message, mid, pos, content, "[]")
        state = {"mid":mid, "pos":pos, "buttons":[], "current_row":0}
        await run(db_set_state, uid, "awaiting_addmsg_btn_text", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_LIGHTNING1,"⚡")} <b>Do you want to add a button?</b>',
            build_reply_keyboard_raw([
                [btn("Yes", style="success", emoji_id=EMOJI_YES),
                 btn("No", style="danger", emoji_id=EMOJI_NO)]
            ]))
        return

    # Button creation flow
    if action == "awaiting_addmsg_btn_text":
        state = json.loads(data)
        if text == "No":
            btns_json = json.dumps(state.get("buttons",[]))
            await run(db_update_message_buttons, state["mid"], btns_json)
            await run(db_clear_state, uid)
            await open_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Message at position</b> <code>{state["pos"]}</code> <b>saved with</b> <code>{len(state["buttons"])}</code> <b>button(s).</b>'); return
        if text == "Yes":
            await run(db_set_state, uid, "awaiting_addmsg_btn_text_input", json.dumps(state))
            send_raw_message(uid, f'{pe(EMOJI_STAR3,"⭐")} <b>Send the button text:</b>', cancel_kb_raw()); return
        send_raw_message(uid, f'{pe(EMOJI_THINK,"🤔")} Choose <b>Yes</b> or <b>No</b>.',
            build_reply_keyboard_raw([
                [btn("Yes", style="success", emoji_id=EMOJI_YES),
                 btn("No", style="danger", emoji_id=EMOJI_NO)]
            ]))
        return
    if action == "awaiting_addmsg_btn_text_input":
        state = json.loads(data); state["current_btn_text"]=text
        await run(db_set_state, uid, "awaiting_addmsg_btn_url", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_ROCKET,"🚀")} <b>Send the button URL:</b>', cancel_kb_raw()); return
    if action == "awaiting_addmsg_btn_url":
        state = json.loads(data); state["current_btn_url"]=text
        await run(db_set_state, uid, "awaiting_addmsg_icon", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_PREMIUM,"💎")} <b>Premium icon?</b> Send emoji ID or type <code>skip</code>.', cancel_kb_raw())
        return
    if action == "awaiting_addmsg_icon":
        state = json.loads(data)
        icon_id = None
        if text.lower() != "skip":
            if not text.isdigit():
                send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>Invalid ID. Send a number or</b> <code>skip</code>.', cancel_kb_raw())
                return
            icon_id = text
        state["current_icon_id"] = icon_id
        await run(db_set_state, uid, "awaiting_addmsg_btn_color", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_BUTTERFLY,"🦋")} <b>Select button colour:</b>',
            build_reply_keyboard_raw([
                [btn("Blue", style="primary", emoji_id=EMOJI_BLUE),
                 btn("Red", style="danger", emoji_id=EMOJI_RED)],
                [btn("Green", style="success", emoji_id=EMOJI_GREEN),
                 btn("Default", style="default", emoji_id=EMOJI_DEFAULT)]
            ]))
        return
    if action == "awaiting_addmsg_btn_color":
        state = json.loads(data)
        cmap = {"Blue":"primary","Red":"danger","Green":"success","Default":"default"}
        style = cmap.get(text)
        if not style:
            send_raw_message(uid, f'{pe(EMOJI_SIREN,"🚨")} <b>Choose a valid colour.</b>',
                build_reply_keyboard_raw([
                    [btn("Blue", style="primary", emoji_id=EMOJI_BLUE),
                     btn("Red", style="danger", emoji_id=EMOJI_RED)],
                    [btn("Green", style="success", emoji_id=EMOJI_GREEN),
                     btn("Default", style="default", emoji_id=EMOJI_DEFAULT)]
                ]))
            return
        btn_obj = {
            "text": state["current_btn_text"],
            "url": state["current_btn_url"],
            "style": style,
            "row": state["current_row"]
        }
        if state.get("current_icon_id"):
            btn_obj["emoji_id"] = state["current_icon_id"]
        state.setdefault("buttons",[]).append(btn_obj)
        await run(db_set_state, uid, "awaiting_addmsg_another", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_OK,"✅")} <b>Button added! Add another?</b>',
            build_reply_keyboard_raw([
                [btn("Done", style="success", emoji_id=EMOJI_DONE),
                 btn("Add Another", style="primary", emoji_id=EMOJI_ADD_ANOTHER)]
            ]))
        return
    if action == "awaiting_addmsg_another":
        state = json.loads(data)
        if text == "Done":
            btns_json = json.dumps(state["buttons"])
            await run(db_update_message_buttons, state["mid"], btns_json)
            await run(db_clear_state, uid)
            await open_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Message at position</b> <code>{state["pos"]}</code> <b>saved with</b> <code>{len(state["buttons"])}</code> <b>button(s).</b>'); return
        if text == "Add Another":
            await run(db_set_state, uid, "awaiting_addmsg_row_choice", json.dumps(state))
            send_raw_message(uid, f'{pe(EMOJI_LIGHTNING3,"⚡")} <b>Same row or new row?</b>',
                build_reply_keyboard_raw([
                    [btn("Same Row", style="primary", emoji_id=EMOJI_SAME_ROW),
                     btn("Next Row", style="primary", emoji_id=EMOJI_NEXT_ROW)]
                ]))
            return
        send_raw_message(uid, f'{pe(EMOJI_THINK,"🤔")} Choose <b>Done</b> or <b>Add Another</b>.',
            build_reply_keyboard_raw([
                [btn("Done", style="success", emoji_id=EMOJI_DONE),
                 btn("Add Another", style="primary", emoji_id=EMOJI_ADD_ANOTHER)]
            ]))
        return
    if action == "awaiting_addmsg_row_choice":
        state = json.loads(data)
        if text == "Next Row": state["current_row"] = state.get("current_row",0)+1
        await run(db_set_state, uid, "awaiting_addmsg_btn_text_input", json.dumps(state))
        send_raw_message(uid, f'{pe(EMOJI_STAR3,"⭐")} <b>Send the button text:</b>', cancel_kb_raw()); return

    # ── Remove message by position ──
    if action == "awaiting_removemsg_pos":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        try:
            pos = int(text)
            messages = await run(db_get_messages)
            exists = any(str(m["position"]) == str(pos) for m in messages)
            if not exists:
                await _open_sequence_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No message found at position</b> <code>{pos}</code>.')
                return
            ok = await run(db_remove_message_pos, pos)
            if ok:
                await _open_sequence_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Successfully removed message at position</b> <code>{pos}</code>.')
            else:
                await _open_sequence_panel(update, uid, f'{pe(EMOJI_SIREN,"🚨")} <b>Failed to remove message at position</b> <code>{pos}</code>.')
        except ValueError:
            await _open_sequence_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>Invalid position. Send a number.</b>')
        return

    # ── Reorder ──
    if action == "awaiting_reordermsg":
        if not db_has_perm(uid,"can_manage_seq"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        parts = text.split()
        try:
            mid, new_pos = int(parts[0]), int(parts[1])
            ok = await run(db_reorder_message, mid, new_pos)
            reply = f'{pe(EMOJI_OK,"✅")} <b>Message</b> <code>{mid}</code> <b>moved to position</b> <code>{new_pos}</code>.' if ok else f'{pe(EMOJI_THINK,"🤔")} <b>Message</b> <code>{mid}</code> <b>not found or position conflict.</b>'
        except (ValueError, IndexError): reply = f'{pe(EMOJI_SKULL,"💀")} <b>Expected:</b> <code>&lt;message_id&gt; &lt;new_position&gt;</code>'
        await _open_sequence_panel(update, uid, reply); return

    # ── Bot profile actions ──
    if action == "awaiting_bot_name":
        if not db_has_perm(uid,"can_manage_bot_profile"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        try: await context.bot.set_my_name(name=text); reply=f'{pe(EMOJI_OK,"✅")} <b>Bot name updated.</b>'
        except Exception as e: reply=f'{pe(EMOJI_SKULL,"💀")} <b>Error:</b> <code>{e}</code>'
        await _open_bot_profile_panel(update, uid, reply); return
    if action == "awaiting_bot_bio":
        if not db_has_perm(uid,"can_manage_bot_profile"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        try: await context.bot.set_my_description(description=text); reply=f'{pe(EMOJI_OK,"✅")} <b>Bot bio updated.</b>'
        except Exception as e: reply=f'{pe(EMOJI_SKULL,"💀")} <b>Error:</b> <code>{e}</code>'
        await _open_bot_profile_panel(update, uid, reply); return
    if action == "awaiting_bot_description":
        if not db_has_perm(uid,"can_manage_bot_profile"): await open_panel(update, uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>'); return
        await run(db_clear_state, uid)
        try: await context.bot.set_my_short_description(short_description=text); reply=f'{pe(EMOJI_OK,"✅")} <b>Bot description updated.</b>'
        except Exception as e: reply=f'{pe(EMOJI_SKULL,"💀")} <b>Error:</b> <code>{e}</code>'
        await _open_bot_profile_panel(update, uid, reply); return

    # ═══════════════════════════════════════════════════
    # MENU BUTTONS
    # ═══════════════════════════════════════════════════
    if text == "Broadcast":
        if not db_has_perm(uid,"can_broadcast"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await run(db_set_state, uid, "awaiting_broadcast")
        send_raw_message(uid, f'{pe(EMOJI_BROADCAST,"📡")} <b>Send the message to broadcast.</b>\nSupports text, photos, videos, documents, stickers — everything.', cancel_kb_raw()); return

    if text == "Stats":
        if not db_has_perm(uid,"can_stats"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        total = await run(db_total_users); daily = await run(db_daily_users)
        pending = len(await run(db_get_pending_requests))
        auto = "ON" if await run(db_get_auto_approve) else "OFF"
        send_raw_message(uid,
            f'{pe(EMOJI_CHART,"📊")} <b>Bot Statistics</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
            f'{pe(EMOJI_STAR1,"⭐")} <b>Total users:</b> <code>{total}</code>\n'
            f'{pe(EMOJI_FIREWORK,"🎇")} <b>New today:</b> <code>{daily}</code>\n'
            f'{pe(EMOJI_SIREN,"🚨")} <b>Pending approvals:</b> <code>{pending}</code>\n'
            f'{pe(EMOJI_REPEAT,"🔂")} <b>Auto‑approve:</b> <code>{auto}</code>',
            staff_kb_raw(uid))
        return

    if text == "Admins" and is_main_admin(uid):
        rows = await run(db_list_admins,"admin")
        listing = "\n".join(f"• `{r['user_id']}`" for r in rows) if rows else "_No admins._"
        send_raw_message(uid, f'{pe(EMOJI_TROPHY,"🏆")} <b>Admins:</b>\n{listing}',
            build_reply_keyboard_raw([
                [btn("Add Admin", style="success", emoji_id=EMOJI_TROPHY),
                 btn("Remove Admin", style="danger", emoji_id=EMOJI_SKULL)],
                [btn("Back to Panel", style="default", emoji_id=EMOJI_BACK)]
            ]))
        return
    if text == "Add Admin" and is_main_admin(uid):
        await run(db_set_state, uid, "awaiting_add_admin")
        send_raw_message(uid, f'{pe(EMOJI_STAR3,"⭐")} <b>Send user ID to add as Admin:</b>', cancel_kb_raw()); return
    if text == "Remove Admin" and is_main_admin(uid):
        rows = await run(db_list_admins,"admin")
        if not rows:
            send_raw_message(uid, f'{pe(EMOJI_THINK,"🤔")} <b>No admins.</b>', admin_panel_kb_raw()); return
        listing = "\n".join(f"• `{r['user_id']}`" for r in rows)
        await run(db_set_state, uid, "awaiting_remove_admin")
        send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>Admins:</b>\n{listing}\n\n<b>Send ID to remove:</b>', cancel_kb_raw()); return

    if text == "Subadmins":
        if not (is_main_admin(uid) or db_is_admin(uid)):
            send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        rows = await run(db_list_admins) if is_main_admin(uid) else await run(db_list_admins,"subadmin")
        listing = "\n".join(f"• `{r['user_id']}` ({r['role'].capitalize()})" for r in rows) if rows else "_None._"
        send_raw_message(uid, f'{pe(EMOJI_LIGHTNING2,"⚡")} <b>Subadmins:</b>\n{listing}',
            build_reply_keyboard_raw([
                [btn("Add Subadmin", style="success", emoji_id=EMOJI_LIGHTNING2),
                 btn("Remove Subadmin", style="danger", emoji_id=EMOJI_SKULL)],
                [btn("Back to Panel", style="default", emoji_id=EMOJI_BACK)]
            ]))
        return
    if text == "Add Subadmin":
        if not (is_main_admin(uid) or db_is_admin(uid)):
            send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await run(db_set_state, uid, "awaiting_add_subadmin")
        send_raw_message(uid, f'{pe(EMOJI_LIGHTNING2,"⚡")} <b>Send user ID to add as Subadmin:</b>', cancel_kb_raw()); return
    if text == "Remove Subadmin":
        if not (is_main_admin(uid) or db_is_admin(uid)):
            send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        rows = await run(db_list_admins) if is_main_admin(uid) else await run(db_list_admins,"subadmin")
        if not rows:
            send_raw_message(uid, f'{pe(EMOJI_THINK,"🤔")} <b>No subadmins.</b>', staff_kb_raw(uid)); return
        listing = "\n".join(f"• `{r['user_id']}`" for r in rows)
        await run(db_set_state, uid, "awaiting_remove_subadmin")
        send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>Subadmins:</b>\n{listing}\n\n<b>Send ID to remove:</b>', cancel_kb_raw()); return

    if text == "Approve All Requests":
        if not db_has_perm(uid,"can_approve_requests"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        status_msg = await msg.reply_text(f'{pe(EMOJI_SIREN,"🚨")} <b>Processing pending approvals...</b>', parse_mode="HTML")
        approved, failed = await approve_all_pending(context.bot)
        await status_msg.edit_text(f'{pe(EMOJI_OK,"✅")} <b>Approved</b> <code>{approved}</code> <b>requests.</b>\n{pe(EMOJI_SKULL,"💀")} <b>Failed:</b> <code>{failed}</code>', parse_mode="HTML")
        await open_panel(update, uid); return

    if text.startswith("Auto‑Approve:") and (is_main_admin(uid) or db_has_perm(uid,"can_toggle_auto_approve")):
        new_val = not await run(db_get_auto_approve)
        await run(db_set_auto_approve, new_val)
        await open_panel(update, uid, f'{pe(EMOJI_REPEAT,"🔂")} <b>Auto‑approve {"ON" if new_val else "OFF"}</b>'); return

    if text == "Subadmin Permissions" and is_main_admin(uid):
        subs = await run(db_list_admins)
        if not subs: send_raw_message(uid, f'{pe(EMOJI_THINK,"🤔")} <b>No subadmins.</b>', admin_panel_kb_raw()); return
        keyboard = [[InlineKeyboardButton(f"👤 {s['user_id']} ({s['role'].upper()})", callback_data=f"perm_sub_{s['user_id']}")] for s in subs]
        keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="perm_close")])
        send_raw_message(uid, f'{pe(EMOJI_GEAR,"⚙️")} <b>Select a subadmin:</b>', InlineKeyboardMarkup(keyboard).to_dict()); return

    if text == "Bot Profile":
        if not db_has_perm(uid,"can_manage_bot_profile"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await _open_bot_profile_panel(update, uid); return
    if text == "Change Name":
        if not db_has_perm(uid,"can_manage_bot_profile"): return
        await run(db_set_state, uid, "awaiting_bot_name")
        send_raw_message(uid, f'{pe(EMOJI_CHANGE_NAME,"✏️")} <b>Send new bot name:</b>', cancel_kb_raw()); return
    if text == "Change Bio":
        if not db_has_perm(uid,"can_manage_bot_profile"): return
        await run(db_set_state, uid, "awaiting_bot_bio")
        send_raw_message(uid, f'{pe(EMOJI_CHANGE_BIO,"📝")} <b>Send new bio:</b>', cancel_kb_raw()); return
    if text == "Change Description":
        if not db_has_perm(uid,"can_manage_bot_profile"): return
        await run(db_set_state, uid, "awaiting_bot_description")
        send_raw_message(uid, f'{pe(EMOJI_CHANGE_DESC,"📄")} <b>Send new short description:</b>', cancel_kb_raw()); return

    if text == "Test Sequence":
        if not db_has_perm(uid,"can_test_sequence"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        send_raw_message(uid, f'{pe(EMOJI_DINO,"🦖")} <b>Sending test sequence...</b>', staff_kb_raw(uid))
        asyncio.create_task(send_sequence_to_user(context.bot, uid))
        await open_panel(update, uid, f'{pe(EMOJI_OK,"✅")} <b>Test sequence sent.</b>'); return

    if text == "Message Sequence":
        if not db_has_perm(uid,"can_manage_seq"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await _open_sequence_panel(update, uid); return
    if text in ("Set Intro Msg", "Update Intro Msg"):
        if not db_has_perm(uid,"can_manage_seq"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await run(db_set_state, uid, "awaiting_set_intro")
        send_raw_message(uid, f'{pe(EMOJI_INTRO,"📋")} <b>Send intro text</b>\n{PLACEHOLDER_HELP}', cancel_kb_raw()); return
    if text in ("Set Reply Msg", "Update Reply Msg"):
        if not db_has_perm(uid,"can_manage_seq"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await run(db_set_state, uid, "awaiting_set_reply")
        send_raw_message(uid, f'{pe(EMOJI_REPLY_SET,"💬")} <b>Send the message that non-admin users will receive</b> (any type).', cancel_kb_raw()); return
    if text == "Remove Reply Msg":
        if not db_has_perm(uid,"can_manage_seq"): send_raw_message(uid, f'{pe(EMOJI_SKULL,"💀")} <b>No permission.</b>', staff_kb_raw(uid)); return
        await run(db_set_state, uid, "awaiting_confirm_remove_reply")
        send_raw_message(uid, f'{pe(EMOJI_SKULL2,"☠️")} <b>Type</b> <code>yes</code> <b>to confirm removal.</b>', cancel_kb_raw()); return
    if text == "Add Message" and db_has_perm(uid,"can_manage_seq"):
        await run(db_set_state, uid, "awaiting_addmsg_pos")
        send_raw_message(uid, f'{pe(EMOJI_UP,"⏫")} <b>Enter position number:</b>', cancel_kb_raw()); return
    if text == "Remove Message" and db_has_perm(uid,"can_manage_seq"):
        rows = await run(db_get_messages)
        if not rows: await _open_sequence_panel(update, uid, f'{pe(EMOJI_THINK,"🤔")} <b>Sequence empty.</b>'); return
        lines = []
        for r in rows:
            preview = ""
            if r["content_json"]:
                try:
                    content = json.loads(r["content_json"])
                    if content.get("type") == "text":
                        preview = content.get("text", "")[:40]
                    elif content.get("caption"):
                        preview = content.get("caption", "")[:40]
                    else:
                        preview = "[media]"
                except:
                    preview = "[unknown]"
            buttons = "🔘" if r["buttons_json"] and r["buttons_json"] != "[]" else ""
            lines.append(f"`{r['position']}.` msg `{r['message_id']}` {buttons} – {preview}")
        listing = "\n".join(lines)
        await run(db_set_state, uid, "awaiting_removemsg_pos")
        send_raw_message(uid, f'{pe(EMOJI_LIST_MSG,"📋")} <b>Current Sequence</b>\n{listing}\n\n<b>Send the position number to remove:</b>', cancel_kb_raw()); return
    if text == "Reorder Message" and db_has_perm(uid,"can_manage_seq"):
        rows = await run(db_get_messages)
        if not rows: await _open_sequence_panel(update, uid, f'{pe(EMOJI_THINK,"🤔")} <b>Sequence empty.</b>'); return
        listing = "\n".join(f"`{r['position']}.` msg_id `{r['message_id']}`" for r in rows)
        await run(db_set_state, uid, "awaiting_reordermsg")
        send_raw_message(uid, f'{pe(EMOJI_REORDER,"🔀")} <b>Current order:</b>\n{listing}\n\n<b>Send</b> <code>msg_id new_pos</code> <b>to reorder:</b>', cancel_kb_raw()); return
    if text == "List Messages" and db_has_perm(uid,"can_manage_seq"):
        rows = await run(db_get_messages)
        if not rows:
            send_raw_message(uid, f'{pe(EMOJI_LIST_MSG,"📋")} <b>Sequence</b>\n<i>Empty.</i>', sequence_panel_kb_raw())
            return
        lines = []
        for r in rows:
            preview = ""
            if r["content_json"]:
                try:
                    content = json.loads(r["content_json"])
                    if content.get("type") == "text":
                        preview = content.get("text", "")[:50]
                    elif content.get("caption"):
                        preview = content.get("caption", "")[:50]
                    else:
                        preview = "[media]"
                except:
                    preview = "[unknown]"
            buttons = " (has buttons)" if r["buttons_json"] and r["buttons_json"] != "[]" else ""
            lines.append(f"• **{r['position']}** → msg_id `{r['message_id']}`{buttons}\n  _Preview: {preview}_")
        body = "\n".join(lines)
        send_raw_message(uid, f'{pe(EMOJI_LIST_MSG,"📋")} <b>Sequence</b> (total {len(rows)})\n{body}', sequence_panel_kb_raw()); return
    if text == "Back to Panel":
        await open_panel(update, uid); return

def _handle_add_remove_admin(uid, text, role):
    try:
        tid = int(text)
        if tid == ADMIN_ID: return f'{pe(EMOJI_THINK,"🤔")} <b>Cannot add main admin.</b>'
        ok = db_add_admin(tid, role)
        return f'{pe(EMOJI_OK,"✅")} <b>{tid} added as {role.capitalize()}.</b>' if ok else f'{pe(EMOJI_THINK,"🤔")} <b>Already exists.</b>'
    except ValueError: return f'{pe(EMOJI_SKULL,"💀")} <b>Invalid ID.</b>'

def _handle_remove_admin(uid, text):
    try:
        tid = int(text)
        if tid == ADMIN_ID: return f'{pe(EMOJI_THINK,"🤔")} <b>Main admin cannot be removed.</b>'
        ok = db_remove_subadmin(tid)
        return f'{pe(EMOJI_OK,"✅")} <b>Removed.</b>' if ok else f'{pe(EMOJI_THINK,"🤔")} <b>Not found.</b>'
    except ValueError: return f'{pe(EMOJI_SKULL,"💀")} <b>Invalid ID.</b>'

# ═══════════════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════════════
async def subadmin_list_callback(update, context):
    q = update.callback_query
    await q.answer()
    if not is_main_admin(q.from_user.id):
        await q.edit_message_text(f'{pe(EMOJI_SKULL2,"☠️")} <b>Only main admin can manage permissions.</b>', parse_mode="HTML")
        return
    subs = await run(db_list_admins)
    if not subs:
        await q.edit_message_text(f'{pe(EMOJI_THINK,"🤔")} <b>No subadmins found.</b>', parse_mode="HTML")
        return
    kb = [[InlineKeyboardButton(f"👤 {s['user_id']} ({s['role'].upper()})", callback_data=f"perm_sub_{s['user_id']}")] for s in subs]
    kb.append([InlineKeyboardButton("🔙 Close", callback_data="perm_close")])
    await q.edit_message_text(f'{pe(EMOJI_GEAR,"⚙️")} <b>Select a subadmin to edit permissions:</b>', parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def subadmin_perm_menu_callback(update, context):
    q = update.callback_query
    await q.answer()
    if not is_main_admin(q.from_user.id):
        await q.edit_message_text(f'{pe(EMOJI_SKULL2,"☠️")} <b>Only main admin.</b>', parse_mode="HTML")
        return
    try: sub_id = int(q.data.split("_")[2])
    except: return
    perms = await run(db_get_subadmin_perms, sub_id)
    if not perms:
        await q.edit_message_text(f'{pe(EMOJI_THINK,"🤔")} <b>Subadmin not found.</b>', parse_mode="HTML")
        return
    role = await run(db_get_admin_role, sub_id)
    kb = []
    for p in PERMISSIONS:
        status = "✅" if perms.get(p) else "❌"
        kb.append([InlineKeyboardButton(f"{status} {PERM_DISPLAY[p]}", callback_data=f"perm_toggle_{sub_id}_{p}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="perm_list"), InlineKeyboardButton("🔙 Close", callback_data="perm_close")])
    await q.edit_message_text(f'{pe(EMOJI_GEAR,"⚙️")} <b>Permissions for {role.upper()}</b> <code>{sub_id}</code>\n━━━━━━━━━━━━━━━━━━━━━', parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def perm_toggle_callback(update, context):
    q = update.callback_query
    await q.answer()
    if not is_main_admin(q.from_user.id):
        await q.edit_message_text(f'{pe(EMOJI_SKULL2,"☠️")} <b>Only main admin.</b>', parse_mode="HTML")
        return
    parts = q.data.split("_")
    sub_id = int(parts[2])
    perm = "_".join(parts[3:])
    perms = await run(db_get_subadmin_perms, sub_id)
    if perm not in perms:
        await q.answer("Invalid permission.", show_alert=True)
        return
    new_val = not perms[perm]
    await run(db_set_subadmin_perm, sub_id, perm, new_val)
    perms = await run(db_get_subadmin_perms, sub_id)
    role = await run(db_get_admin_role, sub_id)
    kb = []
    for p in PERMISSIONS:
        status = "✅" if perms.get(p) else "❌"
        kb.append([InlineKeyboardButton(f"{status} {PERM_DISPLAY[p]}", callback_data=f"perm_toggle_{sub_id}_{p}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="perm_list"), InlineKeyboardButton("🔙 Close", callback_data="perm_close")])
    await q.edit_message_text(f'{pe(EMOJI_GEAR,"⚙️")} <b>{role.upper()}</b> <code>{sub_id}</code> – <code>{perm}</code> is now {"✅ ON" if new_val else "❌ OFF"}.', parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def perm_close_callback(update, context):
    q = update.callback_query
    await q.answer()
    try: await q.delete_message()
    except: pass

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    try: init_db()
    except: pass
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(ChatJoinRequestHandler(on_join_request))
    app.add_handler(CallbackQueryHandler(subadmin_list_callback, pattern="^perm_list$"))
    app.add_handler(CallbackQueryHandler(subadmin_perm_menu_callback, pattern="^perm_sub_"))
    app.add_handler(CallbackQueryHandler(perm_toggle_callback, pattern="^perm_toggle_"))
    app.add_handler(CallbackQueryHandler(perm_close_callback, pattern="^perm_close$"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
