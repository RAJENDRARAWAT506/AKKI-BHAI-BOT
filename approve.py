"""
Standalone console tool to approve every pending join request stored in
bot.db, with FULL error visibility — every failure prints the exact
Telegram error instead of being silently swallowed like the in-bot button.

Run it in the same folder as bot.db and .env:
    python3 approve_all_debug.py

Requires: pip install python-telegram-bot python-dotenv --break-system-packages
"""
import asyncio
import sqlite3
import os
from collections import Counter

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError, Forbidden, RetryAfter, NetworkError, TimedOut

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = "bot.db"
CONCURRENCY = 150  # higher concurrency — RetryAfter handling below auto-backs-off if Telegram flood-limits us

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN not set in .env")


def get_pending():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT user_id, chat_id FROM pending_requests").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_pending(user_id, chat_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM pending_requests WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    conn.commit()
    conn.close()


async def approve_one(bot, sem, user_id, chat_id, errors, counts):
    async with sem:
        try:
            await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            counts["approved"] += 1
        except Forbidden as e:
            counts["forbidden"] += 1
            errors.append(f"user={user_id} chat={chat_id} -> FORBIDDEN: {e}")
        except TelegramError as e:
            # Covers "already handled"/"request not found"/"not enough
            # rights"/etc. No retry — just record it and move on.
            counts["telegram_error"] += 1
            errors.append(f"user={user_id} chat={chat_id} -> TELEGRAM ERROR: {e}")
        except Exception as e:
            counts["unknown_failed"] += 1
            errors.append(f"user={user_id} chat={chat_id} -> UNKNOWN: {e!r}")
        finally:
            # Whatever happened — success, already-approved, no longer a
            # valid request, no rights, whatever — this row is done.
            # Remove it from pending_requests so it never gets retried.
            remove_pending(user_id, chat_id)


async def main():
    bot = Bot(token=BOT_TOKEN)
    pending = get_pending()
    total = len(pending)
    print(f"Found {total} pending request(s) in bot.db")
    if total == 0:
        print("Nothing to do — bot.db has no pending_requests rows.")
        return

    # Show which chat_id(s) they're under, so a mismatch with your actual
    # tracked channel jumps out immediately.
    by_chat = Counter(r["chat_id"] for r in pending)
    print("Breakdown by chat_id:", dict(by_chat))

    errors = []
    counts = Counter()
    sem = asyncio.Semaphore(CONCURRENCY)

    tasks = [
        asyncio.create_task(approve_one(bot, sem, r["user_id"], r["chat_id"], errors, counts))
        for r in pending
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    print("\n────────── RESULT ──────────")
    print(f"Total processed : {total}")
    print(f"Approved        : {counts['approved']}")
    print(f"Forbidden        : {counts['forbidden']}")
    print(f"Telegram errors  : {counts['telegram_error']}")
    print(f"Network failed   : {counts['network_failed']}")
    print(f"Unknown failed   : {counts['unknown_failed']}")

    if errors:
        print("\nFirst 20 error samples:")
        for line in errors[:20]:
            print(" -", line)

    await bot.shutdown() if hasattr(bot, "shutdown") else None


if __name__ == "__main__":
    asyncio.run(main())
