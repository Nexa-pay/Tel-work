from pyrogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu(uid, is_admin, is_owner):
    rows = []
    top = []
    if is_admin:
        top.append(KeyboardButton("📱 Add Account"))
    if is_owner:
        top.append(KeyboardButton("❌ Remove Account"))
    if top:
        rows.append(top)

    rows.append([KeyboardButton("🚀 Start Reporting"), KeyboardButton("🎯 DM Attack")])
    rows.append([KeyboardButton("🤖 Report Bot"), KeyboardButton("👤 Report Personal ID")])
    rows.append([KeyboardButton("🛑 Stop Reporting")])
    rows.append([KeyboardButton("📊 Stats"), KeyboardButton("👨‍💻 Contact Admin")])

    bot = []
    if is_admin:
        bot.append(KeyboardButton("⚙️ Management"))
    if is_owner:
        bot.append(KeyboardButton("👑 Owner Panel"))
        bot.append(KeyboardButton("🌐 Proxy Manager"))
    if bot:
        rows.append(bot)

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ---- Proxy Manager keyboard ⭐ ----
def proxy_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Proxies", callback_data="px_add"),
         InlineKeyboardButton("📊 Stats", callback_data="px_stats")],
        [InlineKeyboardButton("🩺 Re-check All", callback_data="px_recheck"),
         InlineKeyboardButton("🧹 Remove Dead", callback_data="px_clean")],
        [InlineKeyboardButton("📋 List Alive", callback_data="px_list_alive"),
         InlineKeyboardButton("❌ Delete All", callback_data="px_wipe")],
    ])


# ---- Report reason menus (unchanged structure) ----
def kb_main_report():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Spam", callback_data="r_spam"),
         InlineKeyboardButton("💳 Scam / Fraud", callback_data="menu_fraud")],
        [InlineKeyboardButton("🧒 Child Abuse", callback_data="menu_child"),
         InlineKeyboardButton("👊 Violence", callback_data="menu_violence")],
        [InlineKeyboardButton("🔞 Adult Content", callback_data="menu_porn"),
         InlineKeyboardButton("💊 Illegal Drugs", callback_data="r_dr_illegal")],
        [InlineKeyboardButton("🕵️ Personal Details", callback_data="menu_personal"),
         InlineKeyboardButton("©️ Copyright", callback_data="r_copyright")],
        [InlineKeyboardButton("⚠️ Illegal Goods", callback_data="menu_illegal"),
         InlineKeyboardButton("✍️ Manual / Other", callback_data="r_manual")],
    ])


def kb_fraud():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Impersonation", callback_data="r_fr_impersonation")],
        [InlineKeyboardButton("💸 Deceptive claims", callback_data="r_fr_deceptive")],
        [InlineKeyboardButton("🦠 Malware", callback_data="r_fr_malware")],
        [InlineKeyboardButton("🛍 Fraud seller", callback_data="r_fr_seller")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_child():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧒 Sexual abuse", callback_data="r_ca_sexual")],
        [InlineKeyboardButton("👊 Physical abuse", callback_data="r_ca_physical")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_violence():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤬 Insults", callback_data="r_vi_insult")],
        [InlineKeyboardButton("🩸 Graphic", callback_data="r_vi_graphic")],
        [InlineKeyboardButton("🔪 Extreme", callback_data="r_vi_extreme")],
        [InlineKeyboardButton("🛑 Hate speech", callback_data="r_vi_hate")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_porn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔞 Pornography", callback_data="r_po_porn")],
        [InlineKeyboardButton("📸 Non-consensual", callback_data="r_po_nonconsensual")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_personal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Private images", callback_data="r_pe_images")],
        [InlineKeyboardButton("📱 Phone number", callback_data="r_pe_phone")],
        [InlineKeyboardButton("🏠 Address", callback_data="r_pe_address")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_illegal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔫 Weapons", callback_data="r_ig_weapons")],
        [InlineKeyboardButton("📄 Fake Documents", callback_data="r_ig_docs")],
        [InlineKeyboardButton("💵 Counterfeit", callback_data="r_ig_money")],
        [InlineKeyboardButton("⬅️ Back", callback_data="menu_main")],
    ])


def kb_dm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Spam", callback_data="dm_spam"),
         InlineKeyboardButton("👊 Violence", callback_data="dm_violence")],
        [InlineKeyboardButton("🔞 Porn", callback_data="dm_porn"),
         InlineKeyboardButton("🧒 Child Abuse", callback_data="dm_child")],
        [InlineKeyboardButton("©️ Copyright", callback_data="dm_copyright")],
    ])
