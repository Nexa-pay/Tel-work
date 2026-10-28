from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI
import asyncio

_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = _client["telegram_bot"]

# Collections
accounts_col   = db["sessions"]
users_col      = db["authorized_users"]
tokens_col     = db["keys"]
admin_col      = db["admins"]
logs_col       = db["report_logs"]
refund_logs_col= db["refund_logs"]
receipts_col   = db["api_receipts"]
credit_logs_col= db["credit_logs"]

# ⭐ New
proxies_col    = db["proxies"]           # {scheme, hostname, port, alive, last_check, fail_count}
proxy_logs_col = db["proxy_health_logs"]


async def init_db():
    await proxies_col.create_index([("hostname", 1), ("port", 1), ("scheme", 1)], unique=True)
    await proxies_col.create_index("alive")
    await accounts_col.create_index("user_id", unique=True)
    await users_col.create_index("user_id", unique=True)
    await admin_col.create_index("user_id", unique=True)


async def get_alive_proxy():
    """Return one random alive proxy or None (direct connection)."""
    import random
    pipeline = [{"$match": {"alive": True}}, {"$sample": {"size": 1}}]
    cursor = proxies_col.aggregate(pipeline)
    docs = await cursor.to_list(length=1)
    if not docs:
        return None
    p = docs[0]
    return {"scheme": p["scheme"], "hostname": p["hostname"], "port": p["port"]}


async def mark_proxy_dead(hostname: str, port: int, scheme: str):
    await proxies_col.update_one(
        {"hostname": hostname, "port": port, "scheme": scheme},
        {"$set": {"alive": False}, "$inc": {"fail_count": 1}}
    )
