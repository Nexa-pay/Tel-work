import asyncio
import random
import uuid
import logging
from datetime import datetime
from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.errors import FloodWait, PeerIdInvalid

from config import (
    API_ID, API_HASH, MAX_CONCURRENT_REPORTS,
    REPORT_GAP_MIN, REPORT_GAP_MAX
)
from db import get_alive_proxy, mark_proxy_dead, receipts_col

logger = logging.getLogger(__name__)

SPOOF_DEVICES = [
    {"device_model": "iPhone 15 Pro Max", "system_version": "iOS 17.4.1", "app_version": "10.12.0"},
    {"device_model": "Samsung Galaxy S24 Ultra", "system_version": "Android 14", "app_version": "10.12.0"},
    {"device_model": "Google Pixel 8 Pro", "system_version": "Android 14", "app_version": "10.12.0"},
    {"device_model": "Windows PC", "system_version": "Windows 11", "app_version": "4.16.2"},
    {"device_model": "MacBook Pro", "system_version": "macOS 14.3", "app_version": "9.6.0"},
]


def _device():
    return random.choice(SPOOF_DEVICES)


async def _resolve_peer_safe(app, target):
    """Resolve peer with multiple fallbacks — fixes the 'raw hash' bug."""
    try:
        return await app.resolve_peer(target)
    except Exception:
        pass
    # Try as username
    try:
        chat = await app.get_chat(target)
        return await app.resolve_peer(chat.id)
    except Exception:
        pass
    # Scan dialogs
    try:
        async for dialog in app.get_dialogs(limit=500):
            cid = str(dialog.chat.id)
            tid = str(target)
            if cid == tid or cid.replace("-100", "") == tid.replace("-100", ""):
                return await app.resolve_peer(dialog.chat.id)
            username = getattr(dialog.chat, "username", None)
            if username and str(username).lower() == tid.lower().lstrip("@"):
                return await app.resolve_peer(dialog.chat.id)
    except Exception:
        pass
    return None


async def _do_report_once(acc: dict, target_chat, msg_id, reason, text,
                          join_link, is_bot: bool):
    """One report attempt. Returns (ok, reason_str)."""
    proxy = await get_alive_proxy()
    dev = _device()

    client_kwargs = dict(
        name=f"t_{uuid.uuid4().hex[:8]}",
        api_id=API_ID, api_hash=API_HASH,
        session_string=acc["session"],
        in_memory=True, no_updates=True,
        device_model=dev["device_model"],
        system_version=dev["system_version"],
        app_version=dev["app_version"],
    )
    if proxy:
        client_kwargs["proxy"] = proxy

    try:
        async with Client(**client_kwargs) as app:
            # keep alive
            try:
                await app.invoke(functions.account.UpdateStatus(offline=False))
            except Exception:
                pass

            await asyncio.sleep(random.uniform(REPORT_GAP_MIN, REPORT_GAP_MAX))

            # Handle invite links
            if join_link:
                try:
                    joined = await app.join_chat(join_link)
                    target_chat = joined.id
                except Exception as je:
                    if "USER_ALREADY_PARTICIPANT" not in str(je).upper():
                        logger.debug(f"join failed: {je}")

            peer = await _resolve_peer_safe(app, target_chat)
            if not peer:
                raise PeerIdInvalid("Could not resolve peer")

            if is_bot:
                # Bot reporting path
                try:
                    await app.send_message(target_chat, "/start")
                    await asyncio.sleep(2)
                    bot_msg_ids = [m.id async for m in app.get_chat_history(target_chat, limit=3)]
                    if bot_msg_ids:
                        await app.invoke(functions.messages.Report(
                            peer=peer, id=bot_msg_ids,
                            reason=reason, message=text
                        ))
                        return True, "bot_reported"
                except Exception as e:
                    logger.debug(f"bot report fail: {e}")
                    return False, f"bot_err:{str(e)[:60]}"

            if msg_id:
                # Channel message report
                ids = list(range(max(1, msg_id - 3), msg_id + 4))
                await app.invoke(functions.messages.Report(
                    peer=peer, id=ids, reason=reason, message=text
                ))
                return True, "message_reported"

            # Profile / personal
            await app.invoke(functions.account.ReportPeer(
                peer=peer, reason=reason, message=text
            ))
            return True, "peer_reported"

    except FloodWait as e:
        # If wait is huge, give up cleanly
        if e.value > 60:
            return False, f"flood_{e.value}s"
        await asyncio.sleep(e.value + 1)
        return False, f"flood_retry_{e.value}s"
    except (ConnectionError, OSError) as e:
        if proxy:
            await mark_proxy_dead(proxy["hostname"], proxy["port"], proxy["scheme"])
        return False, f"proxy_err:{str(e)[:50]}"
    except Exception as e:
        return False, f"err:{str(e)[:60]}"


async def run_reports(accounts: list, target_chat, msg_id, reason, texts,
                      join_link: bool, is_bot: bool,
                      loops: int, uid: int,
                      progress_cb=None, stop_event=None):
    """
    Main engine. Returns (success, fail).
    Uses semaphore for real concurrency control.
    """
    sem = asyncio.Semaphore(MAX_CONCURRENT_REPORTS)
    success = 0
    fail = 0

    async def _task(acc):
        nonlocal success, fail
        if stop_event and stop_event.is_set():
            return
        async with sem:
            text = random.choice(texts)
            # If target is bot, prefix text
            if is_bot:
                text = f"[BOT API ABUSE] {text}"
            ok, reason_str = await _do_report_once(
                acc, target_chat, msg_id, reason, text, join_link, is_bot
            )
            # Retry once on flood
            if not ok and "flood_retry" in reason_str:
                ok, reason_str = await _do_report_once(
                    acc, target_chat, msg_id, reason, text, join_link, is_bot
                )

            if ok:
                success += 1
                try:
                    await receipts_col.insert_one({
                        "user_id": uid,
                        "target": str(target_chat),
                        "session_used": acc.get("user_id"),
                        "timestamp": datetime.now(),
                        "result": reason_str,
                    })
                except Exception:
                    pass
            else:
                fail += 1
            if progress_cb:
                try:
                    await progress_cb(success, fail)
                except Exception:
                    pass

    for loop_i in range(loops):
        if stop_event and stop_event.is_set():
            break
        random.shuffle(accounts)
        await asyncio.gather(*(_task(a) for a in accounts))
        if loop_i < loops - 1:
            await asyncio.sleep(5)

    return success, fail
