# -*- coding: utf-8 -*-
"""
🏦 نظام البنك الليبي المتكامل
🇱🇾 Libyan Bank System for Zoro Bot
"""

import random
import json
import os
import time
from datetime import datetime, timedelta

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
)

from tg_bot import dispatcher, OWNER_ID, log

# ═══════════════════════════════════════════════════════════
# 📁 ملف قاعدة البيانات
# ═══════════════════════════════════════════════════════════

BANK_FILE = "bank_data.json"
MARRIAGE_FILE = "marriage_data.json"
FAMILY_FILE = "family_data.json"

# ═══════════════════════════════════════════════════════════
# ⚙️ الإعدادات
# ═══════════════════════════════════════════════════════════

CURRENCY = "د.ل"
STARTING_BALANCE = 1000
DAILY_REWARD = 500
VIP_DAILY = 1500
SUDO_DAILY = 3000
OWNER_DAILY = 10000
TRANSFER_LIMIT = 50000
STEAL_COOLDOWN = 3600
PROTECTION_PRICE = 5000
MARRIAGE_COST = 5000
DIVORCE_COST = 2000

# المستخدمين المميزين
SUDO_USERS = []
VIP_USERS = []

# ═══════════════════════════════════════════════════════════
# 🏪 المتجر الضخم
# ═══════════════════════════════════════════════════════════

SHOP = {
    "عقارات": {
        "كشك": {"price": 5000, "income": 100, "emoji": "🏚️"},
        "دكان": {"price": 15000, "income": 300, "emoji": "🏪"},
        "متجر": {"price": 50000, "income": 1000, "emoji": "🏬"},
        "سوبرماركت": {"price": 100000, "income": 2000, "emoji": "🏬"},
        "مول": {"price": 500000, "income": 10000, "emoji": "🏬"},
        "بيت": {"price": 50000, "income": 800, "emoji": "🏠"},
        "فيلا": {"price": 300000, "income": 5000, "emoji": "🏡"},
        "قصر": {"price": 2000000, "income": 35000, "emoji": "🏰"},
        "فندق": {"price": 1000000, "income": 20000, "emoji": "🏨"},
        "فندق5نجوم": {"price": 3000000, "income": 60000, "emoji": "🏨"},
        "مزرعة": {"price": 200000, "income": 4000, "emoji": "🌴"},
        "جزيرة": {"price": 10000000, "income": 180000, "emoji": "🏝️"},
    },
    "مركبات": {
        "دراجة": {"price": 300, "income": 0, "emoji": "🚲"},
        "دباب": {"price": 5000, "income": 0, "emoji": "🛵"},
        "سيارة": {"price": 20000, "income": 0, "emoji": "🚗"},
        "جيب": {"price": 60000, "income": 0, "emoji": "🚙"},
        "تاكسي": {"price": 30000, "income": 500, "emoji": "🚕"},
        "باص": {"price": 100000, "income": 1800, "emoji": "🚌"},
        "فيراري": {"price": 500000, "income": 0, "emoji": "🏎️"},
        "لامبورغيني": {"price": 700000, "income": 0, "emoji": "🏎️"},
        "هليكوبتر": {"price": 2000000, "income": 0, "emoji": "🚁"},
        "طائرة": {"price": 8000000, "income": 0, "emoji": "✈️"},
        "يخت": {"price": 5000000, "income": 0, "emoji": "🛥️"},
        "صاروخ": {"price": 50000000, "income": 0, "emoji": "🚀"},
    },
    "هدايا": {
        "حلاوة": {"price": 5, "income": 0, "emoji": "🍬"},
        "شكلاطة": {"price": 10, "income": 0, "emoji": "🍫"},
        "كيكة": {"price": 50, "income": 0, "emoji": "🎂"},
        "بيتزا": {"price": 30, "income": 0, "emoji": "🍕"},
        "قهوة": {"price": 10, "income": 0, "emoji": "☕"},
        "وردة": {"price": 20, "income": 0, "emoji": "🌹"},
        "باقةورد": {"price": 150, "income": 0, "emoji": "💐"},
        "دبدوب": {"price": 100, "income": 0, "emoji": "🧸"},
        "خاتمفضة": {"price": 200, "income": 0, "emoji": "💍"},
        "خاتمذهب": {"price": 1000, "income": 0, "emoji": "💍"},
        "خاتمالماس": {"price": 5000, "income": 0, "emoji": "💍"},
        "ساعة": {"price": 2000, "income": 0, "emoji": "⌚"},
        "جوال": {"price": 3000, "income": 0, "emoji": "📱"},
        "لابتوب": {"price": 5000, "income": 0, "emoji": "💻"},
    },
    "مشاريع": {
        "مخبزة": {"price": 30000, "income": 600, "emoji": "🥖"},
        "مطعم": {"price": 50000, "income": 1000, "emoji": "🍕"},
        "مقهى": {"price": 40000, "income": 800, "emoji": "☕"},
        "صالون": {"price": 25000, "income": 500, "emoji": "💈"},
        "جيم": {"price": 80000, "income": 1600, "emoji": "🏋️"},
        "بنزينة": {"price": 200000, "income": 4000, "emoji": "⛽"},
        "صيدلية": {"price": 100000, "income": 2000, "emoji": "🏥"},
        "مستشفى": {"price": 2000000, "income": 40000, "emoji": "🏥"},
        "مصنع": {"price": 1500000, "income": 30000, "emoji": "🏭"},
        "شركةنفط": {"price": 15000000, "income": 300000, "emoji": "🛢️"},
    },
}

# ═══════════════════════════════════════════════════════════
# 💼 الوظائف
# ═══════════════════════════════════════════════════════════

JOBS = {
    "عاطل": {"salary": 0, "required": 0, "emoji": "😴"},
    "عامل": {"salary": 200, "required": 0, "emoji": "🧹"},
    "بائع": {"salary": 400, "required": 1000, "emoji": "🛒"},
    "نادل": {"salary": 500, "required": 2000, "emoji": "🍽️"},
    "طباخ": {"salary": 600, "required": 5000, "emoji": "👨‍🍳"},
    "سائق": {"salary": 700, "required": 10000, "emoji": "🚗"},
    "موظف": {"salary": 1000, "required": 25000, "emoji": "🏦"},
    "معلم": {"salary": 1200, "required": 50000, "emoji": "👨‍🏫"},
    "مهندس": {"salary": 1500, "required": 100000, "emoji": "👷"},
    "دكتور": {"salary": 2000, "required": 200000, "emoji": "👨‍⚕️"},
    "محامي": {"salary": 2500, "required": 300000, "emoji": "👨‍⚖️"},
    "مدير": {"salary": 3000, "required": 500000, "emoji": "👨‍💼"},
    "رجلاعمال": {"salary": 5000, "required": 1000000, "emoji": "👔"},
    "مليونير": {"salary": 10000, "required": 5000000, "emoji": "🤑"},
}

# ═══════════════════════════════════════════════════════════
# 🏦 القروض
# ═══════════════════════════════════════════════════════════

LOANS = {
    "صغير": {"amount": 5000, "interest": 10, "days": 7},
    "متوسط": {"amount": 25000, "interest": 15, "days": 14},
    "كبير": {"amount": 100000, "interest": 20, "days": 30},
    "ضخم": {"amount": 500000, "interest": 25, "days": 60},
}

# ═══════════════════════════════════════════════════════════
# 📁 دوال قاعدة البيانات
# ═══════════════════════════════════════════════════════════

def load_data(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"Error loading {filepath}: {e}")
    return {}


def save_data(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"Error saving {filepath}: {e}")
        return False


def get_bank():
    return load_data(BANK_FILE)


def save_bank(data):
    return save_data(BANK_FILE, data)


def get_marriages():
    return load_data(MARRIAGE_FILE)


def save_marriages(data):
    return save_data(MARRIAGE_FILE, data)


def get_user(user_id):
    data = get_bank()
    return data.get(str(user_id))


def create_account(user_id, name):
    data = get_bank()
    uid = str(user_id)
    
    if uid in data:
        return data[uid]
    
    acc_num = f"LY{random.randint(1000000, 9999999)}"
    
    data[uid] = {
        "account": acc_num,
        "name": name,
        "balance": STARTING_BALANCE,
        "job": "عاطل",
        "items": [],
        "lastdaily": 0,
        "lastsalary": 0,
        "laststeal": 0,
        "protection": 0,
        "loan": 0,
        "loandue": 0,
        "created": time.time(),
        "totalearned": STARTING_BALANCE,
        "totalspent": 0,
        "stolen": 0,
        "losttheft": 0,
        "gameswon": 0,
        "gameslost": 0,
    }
    
    save_bank(data)
    return data[uid]


def update_user(user_id, updates):
    data = get_bank()
    uid = str(user_id)
    if uid in data:
        data[uid].update(updates)
        save_bank(data)
        return True
    return False


def add_balance(user_id, amount):
    data = get_bank()
    uid = str(user_id)
    if uid in data:
        data[uid]["balance"] += amount
        if amount > 0:
            data[uid]["totalearned"] = data[uid].get("totalearned", 0) + amount
        save_bank(data)
        return True
    return False


def remove_balance(user_id, amount):
    data = get_bank()
    uid = str(user_id)
    if uid in data and data[uid]["balance"] >= amount:
        data[uid]["balance"] -= amount
        data[uid]["totalspent"] = data[uid].get("totalspent", 0) + amount
        save_bank(data)
        return True
    return False


def get_balance(user_id):
    user = get_user(user_id)
    return user["balance"] if user else 0


def get_daily_income(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    
    income = 0
    for item in user.get("items", []):
        for category in SHOP.values():
            if item in category:
                income += category[item].get("income", 0)
                break
    return income


def format_num(n):
    return f"{n:,}"


def get_rank(user_id):
    if user_id == OWNER_ID:
        return "👑 المطور"
    elif user_id in SUDO_USERS:
        return "🌟 مالك"
    elif user_id in VIP_USERS:
        return "⭐ مميز"
    return "👤 عضو"


# ═══════════════════════════════════════════════════════════
# 💳 أوامر الحساب
# ═══════════════════════════════════════════════════════════

def cmd_account(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    
    if acc:
        msg.reply_text(
            f"✅ *عندك حساب بالفعل!*\n\n"
            f"🔢 رقم الحساب: `{acc['account']}`\n"
            f"💰 الرصيد: {format_num(acc['balance'])} {CURRENCY}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        acc = create_account(user.id, user.first_name)
        msg.reply_text(
            f"🎉 *مبروك! تم إنشاء حسابك*\n\n"
            f"🏦 مصرف الجمهورية الليبي\n"
            f"🔢 رقم الحساب: `{acc['account']}`\n"
            f"💰 رصيدك: {format_num(acc['balance'])} {CURRENCY}\n\n"
            f"📝 اكتب /بنك لمعرفة الأوامر",
            parse_mode=ParseMode.MARKDOWN
        )


def cmd_balance(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    income = get_daily_income(user.id)
    job = acc.get("job", "عاطل")
    job_data = JOBS.get(job, {})
    
    prot = acc.get("protection", 0)
    prot_text = "🛡️ الحماية: ✅ مفعلة" if time.time() < prot else "🛡️ الحماية: ❌"
    
    loan = acc.get("loan", 0)
    loan_text = f"💳 القرض: {format_num(loan)}" if loan > 0 else "💳 القرض: لا يوجد"
    
    msg.reply_text(
        f"💳 *حسابك البنكي*\n\n"
        f"👤 الاسم: {acc['name']}\n"
        f"🎖️ الرتبة: {get_rank(user.id)}\n"
        f"🔢 الحساب: `{acc['account']}`\n\n"
        f"💰 الرصيد: {format_num(acc['balance'])} {CURRENCY}\n"
        f"📈 الدخل اليومي: {format_num(income)} {CURRENCY}\n"
        f"💼 الوظيفة: {job_data.get('emoji', '😴')} {job}\n\n"
        f"{prot_text}\n"
        f"{loan_text}\n\n"
        f"📊 *الإحصائيات:*\n"
        f"├ المكتسب: {format_num(acc.get('totalearned', 0))}\n"
        f"├ المصروف: {format_num(acc.get('totalspent', 0))}\n"
        f"├ المسروق: {format_num(acc.get('stolen', 0))}\n"
        f"└ خسائر السرقة: {format_num(acc.get('losttheft', 0))}",
        parse_mode=ParseMode.MARKDOWN
    )


def cmd_daily(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    now = time.time()
    last = acc.get("lastdaily", 0)
    
    if now - last < 86400:
        rem = 86400 - (now - last)
        h = int(rem // 3600)
        m = int((rem % 3600) // 60)
        msg.reply_text(f"⏰ استنى {h} ساعة و {m} دقيقة للمكافأة الجاية!")
        return
    
    # تحديد المكافأة
    if user.id == OWNER_ID:
        reward = OWNER_DAILY
        bonus = "👑 مكافأة المطور!"
    elif user.id in SUDO_USERS:
        reward = SUDO_DAILY
        bonus = "🌟 مكافأة المالك!"
    elif user.id in VIP_USERS:
        reward = VIP_DAILY
        bonus = "⭐ مكافأة VIP!"
    else:
        reward = DAILY_REWARD
        bonus = ""
    
    # دخل الممتلكات
    prop_income = get_daily_income(user.id)
    total = reward + prop_income
    
    data = get_bank()
    data[str(user.id)]["balance"] += total
    data[str(user.id)]["lastdaily"] = now
    data[str(user.id)]["totalearned"] = data[str(user.id)].get("totalearned", 0) + total
    save_bank(data)
    
    msg.reply_text(
        f"🎁 *المكافأة اليومية*\n\n"
        f"💵 المكافأة: {format_num(reward)} {CURRENCY}\n"
        f"🏠 دخل الممتلكات: {format_num(prop_income)} {CURRENCY}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 الإجمالي: {format_num(total)} {CURRENCY}\n\n"
        f"{bonus}",
        parse_mode=ParseMode.MARKDOWN
    )


# ═══════════════════════════════════════════════════════════
# 💸 التحويل
# ═══════════════════════════════════════════════════════════

def cmd_transfer(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص واكتب المبلغ\n\nمثال: `/تحويل 1000`", parse_mode=ParseMode.MARKDOWN)
        return
    
    if not args:
        msg.reply_text("❌ اكتب المبلغ!")
        return
    
    try:
        amount = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    to_id = msg.reply_to_message.from_user.id
    to_name = msg.reply_to_message.from_user.first_name
    
    if to_id == user.id:
        msg.reply_text("❌ ما تقدر تحول لنفسك!")
        return
    
    to_acc = get_user(to_id)
    if not to_acc:
        msg.reply_text("❌ المستلم ما عنده حساب!")
        return
    
    if amount <= 0:
        msg.reply_text("❌ المبلغ لازم يكون أكبر من 0!")
        return
    
    if amount > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    if amount > TRANSFER_LIMIT and user.id not in [OWNER_ID] + SUDO_USERS + VIP_USERS:
        msg.reply_text(f"❌ حد التحويل: {format_num(TRANSFER_LIMIT)} {CURRENCY}")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= amount
    data[str(to_id)]["balance"] += amount
    save_bank(data)
    
    msg.reply_text(
        f"✅ *تم التحويل!*\n\n"
        f"💸 المبلغ: {format_num(amount)} {CURRENCY}\n"
        f"👤 إلى: {to_name}\n"
        f"🔢 حسابه: `{to_acc['account']}`",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        context.bot.send_message(
            to_id,
            f"💰 *استلمت تحويل!*\n\n"
            f"💵 المبلغ: {format_num(amount)} {CURRENCY}\n"
            f"👤 من: {user.first_name}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass


# ═══════════════════════════════════════════════════════════
# 🛒 المتجر
# ═══════════════════════════════════════════════════════════

def cmd_shop(update: Update, context: CallbackContext):
    msg = update.effective_message
    args = context.args
    
    if args and args[0] in SHOP:
        cat = args[0]
        text = f"🛒 *متجر {cat}*\n\n"
        for name, item in SHOP[cat].items():
            inc = f" (+{format_num(item['income'])}/يوم)" if item['income'] > 0 else ""
            text += f"{item['emoji']} {name}: {format_num(item['price'])} {CURRENCY}{inc}\n"
        text += f"\n📝 للشراء: `/شراء {cat} اسم`"
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🏠 عقارات", callback_data="shop_عقارات"),
            InlineKeyboardButton("🚗 مركبات", callback_data="shop_مركبات"),
        ],
        [
            InlineKeyboardButton("🎁 هدايا", callback_data="shop_هدايا"),
            InlineKeyboardButton("🏪 مشاريع", callback_data="shop_مشاريع"),
        ],
    ]
    
    msg.reply_text(
        "🏪 *المتجر الليبي الكبير*\n\n"
        "اختر القسم:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def cmd_buy(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("❌ حدد المنتج!\n\nمثال: `/شراء فيلا`", parse_mode=ParseMode.MARKDOWN)
        return
    
    item_name = args[0]
    
    # البحث عن المنتج
    found = None
    for cat, items in SHOP.items():
        if item_name in items:
            found = items[item_name]
            break
    
    if not found:
        msg.reply_text("❌ المنتج غير موجود!")
        return
    
    if acc["balance"] < found["price"]:
        msg.reply_text(f"❌ رصيدك غير كافي! تحتاج {format_num(found['price'])} {CURRENCY}")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= found["price"]
    if "items" not in data[str(user.id)]:
        data[str(user.id)]["items"] = []
    data[str(user.id)]["items"].append(item_name)
    data[str(user.id)]["totalspent"] = data[str(user.id)].get("totalspent", 0) + found["price"]
    save_bank(data)
    
    msg.reply_text(f"✅ تم شراء {found['emoji']} {item_name} بـ {format_num(found['price'])} {CURRENCY}!")


def cmd_sell(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("❌ حدد المنتج للبيع!")
        return
    
    item_name = args[0]
    items = acc.get("items", [])
    
    if item_name not in items:
        msg.reply_text("❌ ما عندك هذا المنتج!")
        return
    
    # البحث عن السعر
    price = 0
    emoji = "📦"
    for cat, cat_items in SHOP.items():
        if item_name in cat_items:
            price = int(cat_items[item_name]["price"] * 0.7)
            emoji = cat_items[item_name]["emoji"]
            break
    
    data = get_bank()
    data[str(user.id)]["items"].remove(item_name)
    data[str(user.id)]["balance"] += price
    save_bank(data)
    
    msg.reply_text(f"✅ تم بيع {emoji} {item_name} بـ {format_num(price)} {CURRENCY}")


def cmd_myitems(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    items = acc.get("items", [])
    
    if not items:
        msg.reply_text("😢 ما عندك ممتلكات!\n\nاكتب /متجر للشراء")
        return
    
    text = "🏠 *ممتلكاتك:*\n\n"
    total_income = 0
    
    item_count = {}
    for item in items:
        item_count[item] = item_count.get(item, 0) + 1
    
    for item_name, count in item_count.items():
        emoji = "📦"
        income = 0
        for cat, cat_items in SHOP.items():
            if item_name in cat_items:
                emoji = cat_items[item_name]["emoji"]
                income = cat_items[item_name].get("income", 0)
                break
        
        total_income += income * count
        count_text = f" x{count}" if count > 1 else ""
        income_text = f" (+{format_num(income * count)}/يوم)" if income > 0 else ""
        text += f"{emoji} {item_name}{count_text}{income_text}\n"
    
    text += f"\n━━━━━━━━━━━━━━━\n"
    text += f"📈 الدخل اليومي: {format_num(total_income)} {CURRENCY}"
    
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 🎁 الإهداء
# ═══════════════════════════════════════════════════════════

def cmd_gift(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص واكتب الهدية\n\nمثال: `/اهداء شكلاطة`", parse_mode=ParseMode.MARKDOWN)
        return
    
    if not args:
        msg.reply_text("❌ حدد الهدية!")
        return
    
    to_id = msg.reply_to_message.from_user.id
    to_name = msg.reply_to_message.from_user.first_name
    gift_name = args[0]
    
    if to_id == user.id:
        msg.reply_text("❌ ما تقدر تهدي نفسك!")
        return
    
    to_acc = get_user(to_id)
    if not to_acc:
        msg.reply_text("❌ المستلم ما عنده حساب!")
        return
    
    # البحث عن الهدية
    gift = None
    if gift_name in SHOP.get("هدايا", {}):
        gift = SHOP["هدايا"][gift_name]
    
    if not gift:
        msg.reply_text("❌ الهدية غير موجودة! اكتب /متجر هدايا")
        return
    
    if acc["balance"] < gift["price"]:
        msg.reply_text(f"❌ رصيدك غير كافي! تحتاج {format_num(gift['price'])} {CURRENCY}")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= gift["price"]
    if "items" not in data[str(to_id)]:
        data[str(to_id)]["items"] = []
    data[str(to_id)]["items"].append(gift_name)
    save_bank(data)
    
    msg.reply_text(f"🎁 تم إهداء {gift['emoji']} {gift_name} لـ {to_name}!")
    
    try:
        context.bot.send_message(
            to_id,
            f"🎁 *استلمت هدية!*\n\n"
            f"{gift['emoji']} {gift_name}\n"
            f"👤 من: {user.first_name}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass


# ═══════════════════════════════════════════════════════════
# 🔫 السرقة والحماية
# ═══════════════════════════════════════════════════════════

def cmd_steal(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص اللي تبي تسرقه!")
        return
    
    victim_id = msg.reply_to_message.from_user.id
    victim_name = msg.reply_to_message.from_user.first_name
    
    if victim_id == user.id:
        msg.reply_text("❌ ما تقدر تسرق نفسك! 😂")
        return
    
    victim = get_user(victim_id)
    if not victim:
        msg.reply_text("❌ الضحية ما عنده حساب!")
        return
    
    now = time.time()
    last = acc.get("laststeal", 0)
    
    if now - last < STEAL_COOLDOWN:
        rem = STEAL_COOLDOWN - (now - last)
        m = int(rem // 60)
        msg.reply_text(f"⏰ استنى {m} دقيقة قبل ما تسرق مرة ثانية!")
        return
    
    # التحقق من الحماية
    if now < victim.get("protection", 0):
        msg.reply_text("🛡️ الضحية عنده حماية! جرب واحد ثاني")
        return
    
    if victim["balance"] < 100:
        msg.reply_text("😅 الضحية مفلس!")
        return
    
    data = get_bank()
    data[str(user.id)]["laststeal"] = now
    
    # نسبة النجاح
    success_rate = 30
    if user.id in VIP_USERS:
        success_rate = 40
    elif user.id in SUDO_USERS:
        success_rate = 50
    elif user.id == OWNER_ID:
        success_rate = 100
    
    if random.randint(1, 100) <= success_rate:
        # نجاح
        steal_percent = random.randint(10, 25)
        stolen = int(victim["balance"] * steal_percent / 100)
        stolen = max(50, min(stolen, victim["balance"]))
        
        data[str(user.id)]["balance"] += stolen
        data[str(user.id)]["stolen"] = data[str(user.id)].get("stolen", 0) + stolen
        data[str(victim_id)]["balance"] -= stolen
        data[str(victim_id)]["losttheft"] = data[str(victim_id)].get("losttheft", 0) + stolen
        save_bank(data)
        
        msg.reply_text(f"🔫 نجحت! سرقت {format_num(stolen)} {CURRENCY} من {victim_name}")
        
        try:
            context.bot.send_message(
                victim_id,
                f"🔫 *تم سرقتك!*\n\n"
                f"💸 المبلغ: {format_num(stolen)} {CURRENCY}\n"
                f"👤 السارق: {user.first_name}\n\n"
                f"💡 اشتري حماية: /حماية",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        # فشل
        fine = random.randint(100, 500)
        fine = min(fine, acc["balance"])
        
        data[str(user.id)]["balance"] -= fine
        save_bank(data)
        
        msg.reply_text(f"👮 انمسكت! دفعت غرامة {format_num(fine)} {CURRENCY}")


def cmd_protection(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    days = 1
    if args:
        try:
            days = int(args[0])
            days = max(1, min(days, 30))
        except:
            pass
    
    price = PROTECTION_PRICE * days
    
    now = time.time()
    current_prot = acc.get("protection", 0)
    
    if now < current_prot:
        remaining = int((current_prot - now) / 3600)
        msg.reply_text(
            f"🛡️ *عندك حماية بالفعل!*\n\n"
            f"⏰ متبقي: {remaining} ساعة\n\n"
            f"💡 تبي تمدد؟ `/حماية {days}`\n"
            f"💰 السعر: {format_num(price)} {CURRENCY}",
            parse_mode=ParseMode.MARKDOWN
        )
        if not args:
            return
    
    if acc["balance"] < price:
        msg.reply_text(f"❌ رصيدك غير كافي! تحتاج {format_num(price)} {CURRENCY}")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= price
    
    if now < current_prot:
        data[str(user.id)]["protection"] = current_prot + (days * 86400)
    else:
        data[str(user.id)]["protection"] = now + (days * 86400)
    
    save_bank(data)
    
    msg.reply_text(f"🛡️ تم تفعيل الحماية لمدة {days} يوم!")


# ═══════════════════════════════════════════════════════════
# 💍 الزواج
# ═══════════════════════════════════════════════════════════

def cmd_propose(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص اللي تبي تخطبه!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    target_name = msg.reply_to_message.from_user.first_name
    
    if target_id == user.id:
        msg.reply_text("❌ ما تقدر تخطب نفسك! 😂")
        return
    
    marriages = get_marriages()
    
    if str(user.id) in marriages:
        msg.reply_text("❌ انت مرتبط بالفعل!")
        return
    
    if str(target_id) in marriages:
        msg.reply_text("❌ هذا الشخص مرتبط!")
        return
    
    if acc["balance"] < 1000:
        msg.reply_text("❌ تحتاج 1,000 د.ل للخطوبة!")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= 1000
    save_bank(data)
    
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"marry_accept_{user.id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"marry_reject_{user.id}"),
        ]
    ]
    
    msg.reply_text(f"💍 تم إرسال طلب الخطوبة لـ {target_name}!")
    
    try:
        context.bot.send_message(
            target_id,
            f"💍 *طلب خطوبة!*\n\n"
            f"👤 {user.first_name} يطلب خطوبتك!\n\n"
            f"اختر:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        pass


def cmd_marry(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    marriages = get_marriages()
    uid = str(user.id)
    
    if uid not in marriages:
        msg.reply_text("❌ انت مش مخطوب!")
        return
    
    if marriages[uid].get("status") == "married":
        msg.reply_text("❌ انت متزوج بالفعل!")
        return
    
    acc = get_user(user.id)
    if acc["balance"] < MARRIAGE_COST:
        msg.reply_text(f"❌ تحتاج {format_num(MARRIAGE_COST)} {CURRENCY} للزواج!")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= MARRIAGE_COST
    save_bank(data)
    
    partner_id = marriages[uid]["partner"]
    marriages[uid]["status"] = "married"
    marriages[uid]["date"] = time.time()
    marriages[str(partner_id)]["status"] = "married"
    marriages[str(partner_id)]["date"] = time.time()
    save_marriages(marriages)
    
    msg.reply_text(f"💒 مبروك الزواج! 🎊")


def cmd_divorce(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    marriages = get_marriages()
    uid = str(user.id)
    
    if uid not in marriages:
        msg.reply_text("❌ انت مش متزوج!")
        return
    
    acc = get_user(user.id)
    if acc["balance"] < DIVORCE_COST:
        msg.reply_text(f"❌ تحتاج {format_num(DIVORCE_COST)} {CURRENCY} للطلاق!")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= DIVORCE_COST
    save_bank(data)
    
    partner_id = str(marriages[uid]["partner"])
    del marriages[uid]
    if partner_id in marriages:
        del marriages[partner_id]
    save_marriages(marriages)
    
    msg.reply_text("💔 تم الطلاق...")


def cmd_partner(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    marriages = get_marriages()
    uid = str(user.id)
    
    if uid not in marriages:
        msg.reply_text("💔 انت عازب/عزباء!")
        return
    
    marriage = marriages[uid]
    status = "مخطوب" if marriage.get("status") != "married" else "متزوج"
    partner_name = marriage.get("name", "مجهول")
    
    msg.reply_text(f"💕 *شريكك*\n\n👤 {partner_name}\n📋 الحالة: {status}", parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 💼 الوظائف
# ═══════════════════════════════════════════════════════════

def cmd_jobs(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    text = "💼 *الوظائف المتاحة:*\n\n"
    
    for name, job in JOBS.items():
        if name == "عاطل":
            continue
        text += f"{job['emoji']} *{name}*\n"
        text += f"  💵 الراتب: {format_num(job['salary'])}/يوم\n"
        text += f"  💰 المتطلب: {format_num(job['required'])}\n\n"
    
    text += "📝 للتوظف: `/توظف اسم`"
    
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_hire(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("❌ حدد الوظيفة! اكتب /وظائف")
        return
    
    job_name = args[0]
    
    if job_name not in JOBS:
        msg.reply_text("❌ الوظيفة غير موجودة!")
        return
    
    job = JOBS[job_name]
    
    if acc["balance"] < job["required"]:
        msg.reply_text(f"❌ تحتاج رصيد {format_num(job['required'])} {CURRENCY}!")
        return
    
    update_user(user.id, {"job": job_name})
    
    msg.reply_text(f"✅ مبروك! صرت {job['emoji']} {job_name} براتب {format_num(job['salary'])} {CURRENCY}/يوم")


def cmd_salary(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    job_name = acc.get("job", "عاطل")
    
    if job_name == "عاطل":
        msg.reply_text("❌ انت عاطل! اكتب /وظائف")
        return
    
    now = time.time()
    last = acc.get("lastsalary", 0)
    
    if now - last < 86400:
        rem = 86400 - (now - last)
        h = int(rem // 3600)
        msg.reply_text(f"⏰ استنى {h} ساعة للراتب الجاي")
        return
    
    job = JOBS.get(job_name, {})
    salary = job.get("salary", 0)
    
    if user.id in VIP_USERS:
        salary = int(salary * 1.5)
    elif user.id in SUDO_USERS:
        salary = int(salary * 2)
    elif user.id == OWNER_ID:
        salary = int(salary * 3)
    
    data = get_bank()
    data[str(user.id)]["balance"] += salary
    data[str(user.id)]["lastsalary"] = now
    save_bank(data)
    
    msg.reply_text(f"💵 استلمت راتبك: {format_num(salary)} {CURRENCY}")


def cmd_resign(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if acc.get("job", "عاطل") == "عاطل":
        msg.reply_text("❌ انت عاطل أصلاً!")
        return
    
    update_user(user.id, {"job": "عاطل"})
    msg.reply_text("✅ تم الاستقالة")


# ═══════════════════════════════════════════════════════════
# 🏦 القروض
# ═══════════════════════════════════════════════════════════

def cmd_loan(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        text = "🏦 *القروض المتاحة:*\n\n"
        for name, loan in LOANS.items():
            total = int(loan["amount"] * (1 + loan["interest"]/100))
            text += f"📋 *{name}*\n"
            text += f"  💵 المبلغ: {format_num(loan['amount'])}\n"
            text += f"  📊 الفايدة: {loan['interest']}%\n"
            text += f"  💰 الإجمالي: {format_num(total)}\n"
            text += f"  ⏰ المدة: {loan['days']} يوم\n\n"
        text += "📝 للقرض: `/قرض نوع`"
        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return
    
    loan_type = args[0]
    
    if loan_type not in LOANS:
        msg.reply_text("❌ نوع القرض غير موجود!")
        return
    
    if acc.get("loan", 0) > 0:
        msg.reply_text("❌ عندك قرض! سدده أولاً")
        return
    
    loan = LOANS[loan_type]
    total = int(loan["amount"] * (1 + loan["interest"]/100))
    due = time.time() + (loan["days"] * 86400)
    
    data = get_bank()
    data[str(user.id)]["balance"] += loan["amount"]
    data[str(user.id)]["loan"] = total
    data[str(user.id)]["loandue"] = due
    save_bank(data)
    
    due_date = datetime.fromtimestamp(due).strftime("%Y-%m-%d")
    
    msg.reply_text(
        f"🏦 *تم القرض!*\n\n"
        f"💵 المبلغ: {format_num(loan['amount'])} {CURRENCY}\n"
        f"💰 للسداد: {format_num(total)} {CURRENCY}\n"
        f"📅 الاستحقاق: {due_date}",
        parse_mode=ParseMode.MARKDOWN
    )


def cmd_payloan(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    loan = acc.get("loan", 0)
    if loan <= 0:
        msg.reply_text("✅ ما عندك قرض!")
        return
    
    amount = loan
    if args:
        try:
            amount = int(args[0].replace(",", ""))
        except:
            pass
    
    if acc["balance"] < amount:
        msg.reply_text(f"❌ رصيدك غير كافي!")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= amount
    remaining = loan - amount
    
    if remaining <= 0:
        data[str(user.id)]["loan"] = 0
        data[str(user.id)]["loandue"] = 0
        save_bank(data)
        msg.reply_text(f"✅ تم سداد القرض بالكامل!")
    else:
        data[str(user.id)]["loan"] = remaining
        save_bank(data)
        msg.reply_text(f"✅ تم سداد {format_num(amount)}. المتبقي: {format_num(remaining)}")


def cmd_myloan(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    loan = acc.get("loan", 0)
    if loan <= 0:
        msg.reply_text("✅ ما عندك قرض!")
        return
    
    due = acc.get("loandue", 0)
    due_date = datetime.fromtimestamp(due).strftime("%Y-%m-%d")
    
    msg.reply_text(
        f"💳 *قرضك:*\n\n"
        f"💰 المتبقي: {format_num(loan)} {CURRENCY}\n"
        f"📅 الاستحقاق: {due_date}",
        parse_mode=ParseMode.MARKDOWN
    )


# ═══════════════════════════════════════════════════════════
# 🎰 الألعاب
# ═══════════════════════════════════════════════════════════

def cmd_dice(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("🎲 اكتب المبلغ!\n\nمثال: `/نرد 100`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    if bet <= 0 or bet > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    player = random.randint(1, 6)
    bot = random.randint(1, 6)
    
    data = get_bank()
    
    if player > bot:
        data[str(user.id)]["balance"] += bet
        data[str(user.id)]["gameswon"] = data[str(user.id)].get("gameswon", 0) + 1
        result = f"🎉 فزت! +{format_num(bet)}"
    elif player < bot:
        data[str(user.id)]["balance"] -= bet
        data[str(user.id)]["gameslost"] = data[str(user.id)].get("gameslost", 0) + 1
        result = f"😢 خسرت! -{format_num(bet)}"
    else:
        result = "🤝 تعادل!"
    
    save_bank(data)
    
    msg.reply_text(f"🎲 نردك: {player} | نردي: {bot}\n{result}")


def cmd_slots(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("🎰 اكتب المبلغ!\n\nمثال: `/سلوتس 100`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    if bet <= 0 or bet > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    symbols = ["🍎", "🍊", "🍋", "🍇", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    data = get_bank()
    data[str(user.id)]["balance"] -= bet
    
    win = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "💎":
            win = bet * 50
        elif result[0] == "7️⃣":
            win = bet * 20
        else:
            win = bet * 10
    elif result[0] == result[1] or result[1] == result[2]:
        win = bet * 2
    
    data[str(user.id)]["balance"] += win
    if win > 0:
        data[str(user.id)]["gameswon"] = data[str(user.id)].get("gameswon", 0) + 1
    else:
        data[str(user.id)]["gameslost"] = data[str(user.id)].get("gameslost", 0) + 1
    save_bank(data)
    
    text = f"🎰 {' '.join(result)}\n\n"
    if win > 0:
        text += f"🎉 فزت بـ {format_num(win)} {CURRENCY}!"
    else:
        text += f"😢 خسرت {format_num(bet)} {CURRENCY}"
    
    msg.reply_text(text)


def cmd_coinflip(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if len(args) < 2:
        msg.reply_text("🪙 الطريقة: `/ورقة 100 ورقة`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    if bet <= 0 or bet > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    choice = args[1].lower()
    if choice not in ["ورقة", "كتابة"]:
        msg.reply_text("❌ اختر: ورقة أو كتابة")
        return
    
    result = random.choice(["ورقة", "كتابة"])
    
    data = get_bank()
    
    if choice == result:
        data[str(user.id)]["balance"] += bet
        msg.reply_text(f"🪙 {result}\n🎉 فزت! +{format_num(bet)}")
    else:
        data[str(user.id)]["balance"] -= bet
        msg.reply_text(f"🪙 {result}\n😢 خسرت! -{format_num(bet)}")
    
    save_bank(data)


def cmd_guess(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if len(args) < 2:
        msg.reply_text("🔢 الطريقة: `/تخمين 5 100`\nخمن رقم من 1-10", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        guess = int(args[0])
        bet = int(args[1].replace(",", ""))
    except:
        msg.reply_text("❌ تأكد من الرقم والمبلغ!")
        return
    
    if guess < 1 or guess > 10:
        msg.reply_text("❌ خمن رقم من 1 إلى 10!")
        return
    
    if bet <= 0 or bet > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    correct = random.randint(1, 10)
    
    data = get_bank()
    
    if guess == correct:
        win = bet * 5
        data[str(user.id)]["balance"] += win - bet
        msg.reply_text(f"🔢 الرقم: {correct}\n🎉 صح! فزت {format_num(win)}!")
    else:
        data[str(user.id)]["balance"] -= bet
        msg.reply_text(f"🔢 الرقم: {correct} (قلت {guess})\n😢 خسرت {format_num(bet)}")
    
    save_bank(data)


def cmd_wheel(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    acc = get_user(user.id)
    if not acc:
        msg.reply_text("❌ ما عندك حساب!")
        return
    
    if not args:
        msg.reply_text("🎡 الطريقة: `/عجلة 100`", parse_mode=ParseMode.MARKDOWN)
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    if bet <= 0 or bet > acc["balance"]:
        msg.reply_text("❌ رصيدك غير كافي!")
        return
    
    data = get_bank()
    data[str(user.id)]["balance"] -= bet
    
    wheel = [
        (0, "💀 خسارة", 25),
        (0.5, "😐 نص", 20),
        (1, "🔄 رجعت", 20),
        (1.5, "😊 ربح", 15),
        (2, "🎉 ضعف!", 10),
        (3, "🔥 ثلاثة!", 5),
        (5, "💎 خمسة!", 3),
        (10, "🌟 عشرة!", 1.5),
        (20, "👑 جاكبوت!", 0.5),
    ]
    
    weights = [w[2] for w in wheel]
    result = random.choices(wheel, weights=weights)[0]
    
    win = int(bet * result[0])
    data[str(user.id)]["balance"] += win
    save_bank(data)
    
    if win > bet:
        text = f"🎡 {result[1]}\n💰 ربحت {format_num(win)}!"
    elif win == bet:
        text = f"🎡 {result[1]}\n🔄 فلوسك رجعت"
    elif win > 0:
        text = f"🎡 {result[1]}\n😢 رجعلك {format_num(win)} بس"
    else:
        text = f"🎡 {result[1]}\n💀 خسرت كل شي!"
    
    msg.reply_text(text)


# ═══════════════════════════════════════════════════════════
# 📊 الترتيب
# ═══════════════════════════════════════════════════════════

def cmd_top(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    data = get_bank()
    
    users = []
    for uid, udata in data.items():
        users.append({
            "name": udata.get("name", "مجهول")[:15],
            "balance": udata.get("balance", 0)
        })
    
    users.sort(key=lambda x: x["balance"], reverse=True)
    
    text = "🏆 *أغنى 10:*\n\n"
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    
    for i, u in enumerate(users[:10]):
        text += f"{medals[i]} {u['name']}: {format_num(u['balance'])}\n"
    
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_topthieves(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    data = get_bank()
    
    users = []
    for uid, udata in data.items():
        stolen = udata.get("stolen", 0)
        if stolen > 0:
            users.append({
                "name": udata.get("name", "مجهول")[:15],
                "stolen": stolen
            })
    
    users.sort(key=lambda x: x["stolen"], reverse=True)
    
    text = "🔫 *أكثر 10 سارقين:*\n\n"
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    
    for i, u in enumerate(users[:10]):
        text += f"{medals[i]} {u['name']}: {format_num(u['stolen'])}\n"
    
    if not users:
        text += "ما فيش سارقين!"
    
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# ⏰ الوقت
# ═══════════════════════════════════════════════════════════

def cmd_time(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    now = datetime.utcnow() + timedelta(hours=2)
    
    msg.reply_text(
        f"🕐 *الوقت في ليبيا*\n\n"
        f"📅 التاريخ: {now.strftime('%Y-%m-%d')}\n"
        f"🕐 الوقت: {now.strftime('%H:%M:%S')}",
        parse_mode=ParseMode.MARKDOWN
    )


# ═══════════════════════════════════════════════════════════
# 👑 أوامر المطور
# ═══════════════════════════════════════════════════════════

def cmd_addbal(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    if user.id != OWNER_ID and user.id not in SUDO_USERS:
        msg.reply_text("⛔ للمطور والمالك فقط!")
        return
    
    if not msg.reply_to_message or not args:
        msg.reply_text("❌ رد على رسالة الشخص واكتب المبلغ")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    try:
        amount = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    if user.id != OWNER_ID and amount > 100000:
        msg.reply_text("⚠️ حد المالك: 100,000")
        return
    
    if not get_user(target_id):
        msg.reply_text("❌ ما عنده حساب!")
        return
    
    add_balance(target_id, amount)
    msg.reply_text(f"✅ تم إضافة {format_num(amount)} {CURRENCY}")


def cmd_removebal(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = context.args
    
    if user.id != OWNER_ID and user.id not in SUDO_USERS:
        msg.reply_text("⛔ للمطور والمالك فقط!")
        return
    
    if not msg.reply_to_message or not args:
        msg.reply_text("❌ رد على رسالة الشخص واكتب المبلغ")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    try:
        amount = int(args[0].replace(",", ""))
    except:
        msg.reply_text("❌ المبلغ غير صالح!")
        return
    
    data = get_bank()
    if str(target_id) in data:
        data[str(target_id)]["balance"] -= amount
        save_bank(data)
        msg.reply_text(f"✅ تم خصم {format_num(amount)} {CURRENCY}")
    else:
        msg.reply_text("❌ ما عنده حساب!")


def cmd_reset(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID:
        msg.reply_text("⛔ للمطور فقط!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    data = get_bank()
    if str(target_id) in data:
        data[str(target_id)]["balance"] = 0
        save_bank(data)
        msg.reply_text("✅ تم التصفير")
    else:
        msg.reply_text("❌ ما عنده حساب!")


def cmd_addsudo(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID:
        msg.reply_text("⛔ للمطور فقط!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    if target_id in SUDO_USERS:
        msg.reply_text("⚠️ مالك بالفعل!")
        return
    
    SUDO_USERS.append(target_id)
    msg.reply_text("✅ تم تعيينه مالك!")


def cmd_removesudo(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID:
        msg.reply_text("⛔ للمطور فقط!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    if target_id in SUDO_USERS:
        SUDO_USERS.remove(target_id)
        msg.reply_text("✅ تم إزالته من المالكين!")
    else:
        msg.reply_text("⚠️ مش مالك!")


def cmd_addvip(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID and user.id not in SUDO_USERS:
        msg.reply_text("⛔ للمطور والمالك فقط!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    if target_id in VIP_USERS:
        msg.reply_text("⚠️ VIP بالفعل!")
        return
    
    VIP_USERS.append(target_id)
    msg.reply_text("✅ تم تعيينه VIP!")


def cmd_removevip(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID and user.id not in SUDO_USERS:
        msg.reply_text("⛔ للمطور والمالك فقط!")
        return
    
    if not msg.reply_to_message:
        msg.reply_text("❌ رد على رسالة الشخص!")
        return
    
    target_id = msg.reply_to_message.from_user.id
    
    if target_id in VIP_USERS:
        VIP_USERS.remove(target_id)
        msg.reply_text("✅ تم إزالته من VIP!")
    else:
        msg.reply_text("⚠️ مش VIP!")


def cmd_bankstats(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    
    if user.id != OWNER_ID:
        msg.reply_text("⛔ للمطور فقط!")
        return
    
    data = get_bank()
    
    total_users = len(data)
    total_balance = sum(u.get("balance", 0) for u in data.values())
    total_loans = sum(u.get("loan", 0) for u in data.values())
    
    msg.reply_text(
        f"📊 *إحصائيات البنك*\n\n"
        f"👥 الحسابات: {total_users}\n"
        f"💰 إجمالي الأرصدة: {format_num(total_balance)} {CURRENCY}\n"
        f"💳 إجمالي القروض: {format_num(total_loans)} {CURRENCY}\n"
        f"🌟 المالكين: {len(SUDO_USERS)}\n"
        f"⭐ VIP: {len(VIP_USERS)}",
        parse_mode=ParseMode.MARKDOWN
    )


# ═══════════════════════════════════════════════════════════
# 📚 المساعدة
# ═══════════════════════════════════════════════════════════

def cmd_bank_help(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    text = """
🏦 *أوامر البنك الليبي*

💳 *الحساب:*
├ /حساب - إنشاء حساب
├ /رصيدي - عرض الرصيد
└ /يومي - المكافأة اليومية

💸 *التحويل:*
└ /تحويل مبلغ - رد على رسالة

🛒 *المتجر:*
├ /متجر - عرض الأقسام
├ /شراء منتج - شراء
├ /بيع منتج - بيع
└ /ممتلكاتي - ممتلكاتك

🎁 *الإهداء:*
└ /اهداء هدية - رد على رسالة

🔫 *السرقة:*
├ /سرقة - رد على رسالة
└ /حماية - شراء حماية

💍 *الزواج:*
├ /خطوبة - طلب خطوبة
├ /زواج - إتمام الزواج
├ /طلاق - الطلاق
└ /شريكي - عرض الشريك

💼 *الوظائف:*
├ /وظائف - الوظائف المتاحة
├ /توظف وظيفة - التوظف
├ /راتب - استلام الراتب
└ /استقالة - الاستقالة

🏦 *القروض:*
├ /قرض - أنواع القروض
├ /قرض نوع - طلب قرض
├ /سداد - سداد القرض
└ /ديوني - عرض الديون

🎰 *الألعاب:*
├ /نرد مبلغ - النرد
├ /سلوتس مبلغ - السلوتس
├ /ورقة مبلغ اختيار - عملة
├ /تخمين رقم مبلغ - التخمين
└ /عجلة مبلغ - عجلة الحظ

📊 *الترتيب:*
├ /الاغنياء - أغنى 10
└ /السارقين - أكثر سارقين

⏰ /الوقت - توقيت ليبيا
"""
    
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 🔘 معالج الأزرار
# ═══════════════════════════════════════════════════════════

def bank_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    # أزرار المتجر
    if data.startswith("shop_"):
        cat = data.replace("shop_", "")
        if cat in SHOP:
            text = f"🛒 *متجر {cat}*\n\n"
            for name, item in SHOP[cat].items():
                inc = f" (+{format_num(item['income'])}/يوم)" if item['income'] > 0 else ""
                text += f"{item['emoji']} {name}: {format_num(item['price'])}{inc}\n"
            text += f"\n📝 للشراء: `/شراء {list(SHOP[cat].keys())[0]}`"
            query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return
    
    # قبول الخطوبة
    if data.startswith("marry_accept_"):
        from_id = int(data.replace("marry_accept_", ""))
        from_acc = get_user(from_id)
        
        if not from_acc:
            query.answer("❌ الشخص ما عنده حساب!", show_alert=True)
            return
        
        marriages = get_marriages()
        
        marriages[str(from_id)] = {
            "partner": user.id,
            "name": user.first_name,
            "status": "engaged",
            "date": time.time()
        }
        
        marriages[str(user.id)] = {
            "partner": from_id,
            "name": from_acc["name"],
            "status": "engaged",
            "date": time.time()
        }
        
        save_marriages(marriages)
        
        query.message.edit_text(f"💕 مبروك الخطوبة! {from_acc['name']} و {user.first_name}")
        query.answer("💕 مبروك!")
        
        try:
            context.bot.send_message(from_id, f"💕 {user.first_name} قبل/ت الخطوبة!")
        except:
            pass
        return
    
    # رفض الخطوبة
    if data.startswith("marry_reject_"):
        from_id = int(data.replace("marry_reject_", ""))
        
        # إرجاع الفلوس
        add_balance(from_id, 1000)
        
        query.message.edit_text("💔 تم رفض طلب الخطوبة")
        query.answer("💔 تم الرفض")
        
        try:
            context.bot.send_message(from_id, f"💔 {user.first_name} رفض/ت طلب الخطوبة")
        except:
            pass
        return
    
    query.answer()


# ═══════════════════════════════════════════════════════════
# ⚙️ تسجيل الأوامر
# ═══════════════════════════════════════════════════════════

__mod_name__ = "البنك 🏦"

__help__ = """
🏦 *نظام البنك الليبي*

💳 الحساب: /حساب /رصيدي /يومي
🛒 المتجر: /متجر /شراء /بيع /ممتلكاتي
💸 التحويل: /تحويل
🎁 الإهداء: /اهداء
🔫 السرقة: /سرقة /حماية
💍 الزواج: /خطوبة /زواج /طلاق /شريكي
💼 الوظائف: /وظائف /توظف /راتب /استقالة
🏦 القروض: /قرض /سداد /ديوني
🎰 الألعاب: /نرد /سلوتس /ورقة /تخمين /عجلة
📊 الترتيب: /الاغنياء /السارقين

📚 /بنك - كل الأوامر
"""

# تسجيل جميع الأوامر
try:
    # الحساب
    dispatcher.add_handler(CommandHandler(["حساب", "account"], cmd_account))
    dispatcher.add_handler(CommandHandler(["رصيدي", "فلوسي", "balance", "رصيد"], cmd_balance))
    dispatcher.add_handler(CommandHandler(["يومي", "daily", "مكافاة"], cmd_daily))
    
    # التحويل
    dispatcher.add_handler(CommandHandler(["تحويل", "حول", "transfer"], cmd_transfer))
    
    # المتجر
    dispatcher.add_handler(CommandHandler(["متجر", "shop", "سوق"], cmd_shop))
    dispatcher.add_handler(CommandHandler(["شراء", "buy"], cmd_buy))
    dispatcher.add_handler(CommandHandler(["بيع", "sell"], cmd_sell))
    dispatcher.add_handler(CommandHandler(["ممتلكاتي", "اغراضي", "items"], cmd_myitems))
    
    # الإهداء
    dispatcher.add_handler(CommandHandler(["اهداء", "هدية", "gift"], cmd_gift))
    
    # السرقة والحماية
    dispatcher.add_handler(CommandHandler(["سرقة", "اسرق", "steal"], cmd_steal))
    dispatcher.add_handler(CommandHandler(["حماية", "protection", "درع"], cmd_protection))
    
    # الزواج
    dispatcher.add_handler(CommandHandler(["خطوبة", "خطب", "propose"], cmd_propose))
    dispatcher.add_handler(CommandHandler(["زواج", "تزوج", "marry"], cmd_marry))
    dispatcher.add_handler(CommandHandler(["طلاق", "divorce"], cmd_divorce))
    dispatcher.add_handler(CommandHandler(["شريكي", "زوجي", "زوجتي", "partner"], cmd_partner))
    
    # الوظائف
    dispatcher.add_handler(CommandHandler(["وظائف", "jobs", "شغل"], cmd_jobs))
    dispatcher.add_handler(CommandHandler(["توظف", "hire"], cmd_hire))
    dispatcher.add_handler(CommandHandler(["راتب", "salary", "اشتغل"], cmd_salary))
    dispatcher.add_handler(CommandHandler(["استقالة", "resign"], cmd_resign))
    
    # القروض
    dispatcher.add_handler(CommandHandler(["قرض", "loan"], cmd_loan))
    dispatcher.add_handler(CommandHandler(["سداد", "pay"], cmd_payloan))
    dispatcher.add_handler(CommandHandler(["ديوني", "myloan"], cmd_myloan))
    
    # الألعاب
    dispatcher.add_handler(CommandHandler(["نرد", "dice"], cmd_dice))
    dispatcher.add_handler(CommandHandler(["سلوتس", "slots"], cmd_slots))
    dispatcher.add_handler(CommandHandler(["ورقة", "coin", "عملة"], cmd_coinflip))
    dispatcher.add_handler(CommandHandler(["تخمين", "guess"], cmd_guess))
    dispatcher.add_handler(CommandHandler(["عجلة", "wheel"], cmd_wheel))
    
    # الترتيب
    dispatcher.add_handler(CommandHandler(["الاغنياء", "top", "توب"], cmd_top))
    dispatcher.add_handler(CommandHandler(["السارقين", "thieves"], cmd_topthieves))
    
    # الوقت
    dispatcher.add_handler(CommandHandler(["الوقت", "time"], cmd_time))
    
    # المساعدة
    dispatcher.add_handler(CommandHandler(["بنك", "bank"], cmd_bank_help))
    
    # أوامر المطور
    dispatcher.add_handler(CommandHandler(["اضافةرصيد", "addbal"], cmd_addbal))
    dispatcher.add_handler(CommandHandler(["خصمرصيد", "removebal"], cmd_removebal))
    dispatcher.add_handler(CommandHandler(["تصفير", "reset"], cmd_reset))
    dispatcher.add_handler(CommandHandler(["تعيينمالك", "addsudo"], cmd_addsudo))
    dispatcher.add_handler(CommandHandler(["ازالةمالك", "removesudo"], cmd_removesudo))
    dispatcher.add_handler(CommandHandler(["تعيينمميز", "addvip"], cmd_addvip))
    dispatcher.add_handler(CommandHandler(["ازالةمميز", "removevip"], cmd_removevip))
    dispatcher.add_handler(CommandHandler(["احصائياتالبنك", "bankstats"], cmd_bankstats))
    
    # معالج الأزرار
    dispatcher.add_handler(CallbackQueryHandler(bank_callback, pattern=r"^(shop_|marry_)"))
    
    log.info("✅ Bank module loaded successfully!")
    
except Exception as e:
    log.error(f"❌ Error loading bank module: {e}")
