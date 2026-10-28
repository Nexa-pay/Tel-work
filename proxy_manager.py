import asyncio
import socket
import logging
from datetime import datetime
from aiohttp_socks import ProxyConnector
import aiohttp
from db import proxies_col, get_alive_proxy
from config import PROXY_CHECK_TIMEOUT

logger = logging.getLogger(__name__)

VALID_SCHEMES = {"http", "socks4", "socks5"}


def parse_proxy_line(line: str):
    """
    Accept:
      socks5://1.2.3.4:1080
      socks4://1.2.3.4:1080
      http://1.2.3.4:8080
      1.2.3.4:1080            (defaults to socks5)
    Returns dict or None.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    scheme = "socks5"
    if "://" in line:
        scheme, line = line.split("://", 1)
        scheme = scheme.lower()

    if scheme not in VALID_SCHEMES:
        return None

    if ":" not in line:
        return None

    host, port_s = line.rsplit(":", 1)
    try:
        port = int(port_s)
        if not (1 <= port <= 65535):
            return None
    except ValueError:
        return None

    return {"scheme": scheme, "hostname": host.strip(), "port": port}


async def test_proxy(proxy: dict, timeout: int = PROXY_CHECK_TIMEOUT) -> bool:
    """Test proxy by hitting https://api.ipify.org"""
    try:
        connector = ProxyConnector.from_url(
            f"{proxy['scheme']}://{proxy['hostname']}:{proxy['port']}",
            rdns=True
        )
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                "https://api.ipify.org?format=json",
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                return resp.status == 200
    except Exception as e:
        logger.debug(f"Proxy test failed {proxy}: {e}")
        return False


async def add_proxies_from_text(raw_text: str) -> dict:
    """
    Add proxies from multi-line text. Tests each one.
    Returns {"added": int, "skipped": int, "invalid": int, "dead": int}
    """
    lines = raw_text.strip().splitlines()
    parsed = [parse_proxy_line(l) for l in lines]
    parsed = [p for p in parsed if p]

    stats = {"added": 0, "skipped": 0, "invalid": len(lines) - len(parsed), "dead": 0}

    for p in parsed:
        existing = await proxies_col.find_one(p)
        if existing:
            stats["skipped"] += 1
            continue

        is_alive = await test_proxy(p)
        await proxies_col.insert_one({
            **p,
            "alive": is_alive,
            "last_check": datetime.now(),
            "fail_count": 0,
            "added_at": datetime.now(),
        })
        if is_alive:
            stats["added"] += 1
        else:
            stats["dead"] += 1
    return stats


async def recheck_all_proxies(limit: int = 200) -> dict:
    """Re-test proxies and update alive flag."""
    cursor = proxies_col.find({}).limit(limit)
    proxies = await cursor.to_list(length=limit)
    stats = {"alive": 0, "dead": 0}

    async def _check(p):
        ok = await test_proxy(p)
        await proxies_col.update_one(
            {"_id": p["_id"]},
            {"$set": {"alive": ok, "last_check": datetime.now()},
             **({"$setOnInsert": {}} if ok else {"$inc": {"fail_count": 1}})}
        )
        stats["alive" if ok else "dead"] += 1

    # limit concurrency to 20
    sem = asyncio.Semaphore(20)
    async def _wrap(p):
        async with sem:
            await _check(p)

    await asyncio.gather(*(_wrap(p) for p in proxies))
    return stats


async def remove_dead_proxies() -> int:
    res = await proxies_col.delete_many({"alive": False})
    return res.deleted_count


async def proxy_stats() -> dict:
    total = await proxies_col.count_documents({})
    alive = await proxies_col.count_documents({"alive": True})
    by_scheme = {}
    for s in VALID_SCHEMES:
        by_scheme[s] = await proxies_col.count_documents({"scheme": s, "alive": True})
    return {"total": total, "alive": alive, "by_scheme": by_scheme}
