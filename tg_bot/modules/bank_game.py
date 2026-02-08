# -*- coding: utf-8 -*-
"""
🏦 نظام البنك الليبي المتكامل
🇱🇾 Libyan Bank System for Zoro Bot

المميزات:
- حسابات بنكية برقم فريد
- تحويلات بالمنشن أو رقم الحساب
- متجر ضخم (عقارات، سيارات، مشاريع، هدايا)
- نظام زواج وعائلة
- نظام سرقة وحماية
- نظام قروض
- نظام وظائف
- ألعاب متنوعة
- استثمارات

👨‍💻 المبرمج: صاحب البوت
"""

import random
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from functools import wraps

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.error import BadRequest

from tg_bot import dispatcher, OWNER_ID, log
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text

# ═══════════════════════════════════════════════════════════
# 📁 ملف قاعدة البيانات
# ═══════════════════════════════════════════════════════════

BANK_FILE = "bank_data.json"
MARRIAGE_FILE = "marriage_data.json"
FAMILY_FILE = "family_data.json"

# ═══════════════════════════════════════════════════════════
# ⚙️ الإعدادات الأساسية
# ═══════════════════════════════════════════════════════════

SETTINGS = {
    "currency": "د.ل",
    "currency_name": "دينار ليبي",
    "starting_balance": 1000,
    "daily_reward": 500,
    "vip_daily": 1500,
    "sudo_daily": 3000,
    "owner_daily": 10000,
    "transfer_limit_normal": 50000,
    "transfer_limit_vip": 200000,
    "steal_success_rate": 30,
    "steal_cooldown": 3600,  # ساعة
    "daily_cooldown": 86400,  # 24 ساعة
    "protection_price": 5000,
    "protection_duration": 86400,  # يوم
    "marriage_cost": 5000,
    "divorce_cost": 2000,
    "engagement_cost": 1000,
    "adoption_cost": 500,
}

# ═══════════════════════════════════════════════════════════
# 👑 المستخدمين المميزين
# ═══════════════════════════════════════════════════════════

SUDO_USERS = []  # المالكين
VIP_USERS = []   # المميزين

# ═══════════════════════════════════════════════════════════
# 🏪 المتجر الضخم
# ═══════════════════════════════════════════════════════════

SHOP = {
    # ═══════════════════════════════════════════════════════
    # 🏠 العقارات
    # ═══════════════════════════════════════════════════════
    "عقارات": {
        "كشك": {"price": 5000, "income": 100, "emoji": "🏚️"},
        "دكان_صغير": {"price": 15000, "income": 300, "emoji": "🏪"},
        "دكان_كبير": {"price": 30000, "income": 600, "emoji": "🏪"},
        "متجر": {"price": 50000, "income": 1000, "emoji": "🏬"},
        "سوبر_ماركت": {"price": 100000, "income": 2000, "emoji": "🏬"},
        "مول_صغير": {"price": 300000, "income": 6000, "emoji": "🏬"},
        "مول_كبير": {"price": 1000000, "income": 20000, "emoji": "🏬"},
        "بيت_شعبي": {"price": 25000, "income": 400, "emoji": "🏘️"},
        "بيت_عادي": {"price": 50000, "income": 800, "emoji": "🏠"},
        "بيت_فخم": {"price": 150000, "income": 2500, "emoji": "🏡"},
        "فيلا_صغيرة": {"price": 300000, "income": 5000, "emoji": "🏡"},
        "فيلا_كبيرة": {"price": 500000, "income": 8000, "emoji": "🏡"},
        "قصر": {"price": 2000000, "income": 35000, "emoji": "🏰"},
        "فندق_نجمة": {"price": 200000, "income": 4000, "emoji": "🏨"},
        "فندق_نجمتين": {"price": 400000, "income": 8000, "emoji": "🏨"},
        "فندق_3_نجوم": {"price": 700000, "income": 14000, "emoji": "🏨"},
        "فندق_4_نجوم": {"price": 1500000, "income": 30000, "emoji": "🏨"},
        "فندق_5_نجوم": {"price": 3000000, "income": 60000, "emoji": "🏨"},
        "مكتب": {"price": 40000, "income": 700, "emoji": "🏢"},
        "برج_مكاتب": {"price": 500000, "income": 9000, "emoji": "🏢"},
        "ارض_فاضية": {"price": 20000, "income": 0, "emoji": "🏗️"},
        "مزرعة_صغيرة": {"price": 60000, "income": 1200, "emoji": "🌴"},
        "مزرعة_كبيرة": {"price": 200000, "income": 4000, "emoji": "🌴"},
        "جزيرة_خاصة": {"price": 10000000, "income": 180000, "emoji": "🏝️"},
    },
    
    # ═══════════════════════════════════════════════════════
    # 🚗 المركبات
    # ═══════════════════════════════════════════════════════
    "مركبات": {
        "دراجة_هوائية": {"price": 300, "income": 0, "emoji": "🚲"},
        "سكوتر": {"price": 1000, "income": 0, "emoji": "🛴"},
        "دباب": {"price": 5000, "income": 0, "emoji": "🛵"},
        "دباب_رياضي": {"price": 15000, "income": 0, "emoji": "🏍️"},
        "سيارة_قديمة": {"price": 8000, "income": 0, "emoji": "🚗"},
        "سيارة_عادية": {"price": 20000, "income": 0, "emoji": "🚗"},
        "سيارة_عائلية": {"price": 35000, "income": 0, "emoji": "🚙"},
        "جيب": {"price": 60000, "income": 0, "emoji": "🚙"},
        "جيب_فخم": {"price": 120000, "income": 0, "emoji": "🚙"},
        "تاكسي": {"price": 30000, "income": 500, "emoji": "🚕"},
        "باص_صغير": {"price": 50000, "income": 900, "emoji": "🚐"},
        "باص_كبير": {"price": 100000, "income": 1800, "emoji": "🚌"},
        "شاحنة": {"price": 80000, "income": 1400, "emoji": "🚚"},
        "سيارة_رياضية": {"price": 250000, "income": 0, "emoji": "🏎️"},
        "فيراري": {"price": 500000, "income": 0, "emoji": "🏎️"},
        "لامبورغيني": {"price": 700000, "income": 0, "emoji": "🏎️"},
        "بوقاتي": {"price": 1500000, "income": 0, "emoji": "🏎️"},
        "هليكوبتر": {"price": 2000000, "income": 0, "emoji": "🚁"},
        "طائرة_صغيرة": {"price": 3000000, "income": 0, "emoji": "✈️"},
        "طائرة_خاصة": {"price": 8000000, "income": 0, "emoji": "✈️"},
        "طائرة_جامبو": {"price": 20000000, "income": 0, "emoji": "✈️"},
        "قارب": {"price": 100000, "income": 0, "emoji": "🛥️"},
        "يخت_صغير": {"price": 1000000, "income": 0, "emoji": "🛥️"},
        "يخت_فخم": {"price": 5000000, "income": 0, "emoji": "🛥️"},
        "صاروخ_فضائي": {"price": 50000000, "income": 0, "emoji": "🚀"},
    },
    
    # ═══════════════════════════════════════════════════════
    # 🍫 الأكل والهدايا
    # ═══════════════════════════════════════════════════════
    "هدايا": {
        "حلاوة": {"price": 5, "income": 0, "emoji": "🍬"},
        "شكلاطة": {"price": 10, "income": 0, "emoji": "🍫"},
        "شكلاطة_فاخرة": {"price": 50, "income": 0, "emoji": "🍫"},
        "بسكويت": {"price": 8, "income": 0, "emoji": "🍪"},
        "كب_كيك": {"price": 15, "income": 0, "emoji": "🧁"},
        "قطعة_كيك": {"price": 25, "income": 0, "emoji": "🍰"},
        "تورتة_صغيرة": {"price": 80, "income": 0, "emoji": "🎂"},
        "تورتة_كبيرة": {"price": 150, "income": 0, "emoji": "🎂"},
        "تورتة_فخمة": {"price": 300, "income": 0, "emoji": "🎂"},
        "بيتزا": {"price": 30, "income": 0, "emoji": "🍕"},
        "برقر": {"price": 20, "income": 0, "emoji": "🍔"},
        "شاورما": {"price": 15, "income": 0, "emoji": "🌮"},
        "كسكسي": {"price": 50, "income": 0, "emoji": "🥘"},
        "مبكبكة": {"price": 45, "income": 0, "emoji": "🍖"},
        "دجاج_مشوي": {"price": 40, "income": 0, "emoji": "🍗"},
        "ستيك": {"price": 80, "income": 0, "emoji": "🥩"},
        "مأكولات_بحرية": {"price": 100, "income": 0, "emoji": "🦐"},
        "قهوة_ليبية": {"price": 10, "income": 0, "emoji": "☕"},
        "شاي_بالنعناع": {"price": 8, "income": 0, "emoji": "🫖"},
        "عصير": {"price": 12, "income": 0, "emoji": "🧃"},
        "وردة": {"price": 20, "income": 0, "emoji": "🌹"},
        "باقة_ورد_صغيرة": {"price": 50, "income": 0, "emoji": "💐"},
        "باقة_ورد_كبيرة": {"price": 150, "income": 0, "emoji": "💐"},
        "باقة_ورد_فخمة": {"price": 500, "income": 0, "emoji": "💐"},
        "دبدوب_صغير": {"price": 30, "income": 0, "emoji": "🧸"},
        "دبدوب_كبير": {"price": 100, "income": 0, "emoji": "🧸"},
        "دبدوب_عملاق": {"price": 300, "income": 0, "emoji": "🧸"},
        "خاتم_فضة": {"price": 200, "income": 0, "emoji": "💍"},
        "خاتم_ذهب": {"price": 1000, "income": 0, "emoji": "💍"},
        "خاتم_ألماس": {"price": 5000, "income": 0, "emoji": "💍"},
        "سلسلة_فضة": {"price": 300, "income": 0, "emoji": "📿"},
        "سلسلة_ذهب": {"price": 1500, "income": 0, "emoji": "📿"},
        "ساعة_عادية": {"price": 200, "income": 0, "emoji": "⌚"},
        "ساعة_فخمة": {"price": 2000, "income": 0, "emoji": "⌚"},
        "ساعة_رولكس": {"price": 10000, "income": 0, "emoji": "⌚"},
        "نظارة_شمسية": {"price": 150, "income": 0, "emoji": "👓"},
        "شنطة": {"price": 300, "income": 0, "emoji": "👜"},
        "شنطة_ماركة": {"price": 2000, "income": 0, "emoji": "👜"},
        "صندوق_هدية": {"price": 100, "income": 0, "emoji": "🎁"},
        "صندوق_هدية_فخم": {"price": 500, "income": 0, "emoji": "🎁"},
    },
    
    # ═══════════════════════════════════════════════════════
    # 📱 الإلكترونيات
    # ═══════════════════════════════════════════════════════
    "إلكترونيات": {
        "جوال_قديم": {"price": 200, "income": 0, "emoji": "📱"},
        "جوال_عادي": {"price": 800, "income": 0, "emoji": "📱"},
        "آيفون": {"price": 3000, "income": 0, "emoji": "📱"},
        "آيفون_برو_ماكس": {"price": 5000, "income": 0, "emoji": "📱"},
        "سامسونج": {"price": 2500, "income": 0, "emoji": "📱"},
        "لابتوب_قديم": {"price": 1000, "income": 0, "emoji": "💻"},
        "لابتوب_عادي": {"price": 3000, "income": 0, "emoji": "💻"},
        "لابتوب_قيمنق": {"price": 8000, "income": 0, "emoji": "💻"},
        "ماك_بوك": {"price": 6000, "income": 0, "emoji": "💻"},
        "كمبيوتر": {"price": 4000, "income": 0, "emoji": "🖥️"},
        "كمبيوتر_قيمنق": {"price": 12000, "income": 0, "emoji": "🖥️"},
        "بلايستيشن": {"price": 2000, "income": 0, "emoji": "🎮"},
        "اكس_بوكس": {"price": 2000, "income": 0, "emoji": "🎮"},
        "تلفزيون": {"price": 1500, "income": 0, "emoji": "📺"},
        "تلفزيون_سمارت_كبير": {"price": 4000, "income": 0, "emoji": "📺"},
    },
    
    # ═══════════════════════════════════════════════════════
    # 🏪 المشاريع
    # ═══════════════════════════════════════════════════════
    "مشاريع": {
        "مخبزة_صغيرة": {"price": 25000, "income": 500, "emoji": "🥖"},
        "مخبزة_كبيرة": {"price": 60000, "income": 1200, "emoji": "🥖"},
        "مطعم_بيتزا": {"price": 40000, "income": 800, "emoji": "🍕"},
        "مطعم_برقر": {"price": 35000, "income": 700, "emoji": "🍔"},
        "مطعم_فخم": {"price": 150000, "income": 3000, "emoji": "🍝"},
        "مقهى_صغير": {"price": 30000, "income": 600, "emoji": "☕"},
        "مقهى_كبير": {"price": 80000, "income": 1600, "emoji": "☕"},
        "ستاربكس": {"price": 200000, "income": 4000, "emoji": "☕"},
        "صالون_حلاقة": {"price": 20000, "income": 400, "emoji": "💈"},
        "صالون_تجميل": {"price": 40000, "income": 800, "emoji": "💅"},
        "جيم_صغير": {"price": 50000, "income": 1000, "emoji": "🏋️"},
        "جيم_كبير": {"price": 150000, "income": 3000, "emoji": "🏋️"},
        "محطة_بنزين": {"price": 200000, "income": 4000, "emoji": "⛽"},
        "صيدلية": {"price": 100000, "income": 2000, "emoji": "🏥"},
        "عيادة": {"price": 250000, "income": 5000, "emoji": "🏥"},
        "مستشفى_خاص": {"price": 2000000, "income": 40000, "emoji": "🏥"},
        "مدرسة_خاصة": {"price": 500000, "income": 10000, "emoji": "🏫"},
        "جامعة_خاصة": {"price": 3000000, "income": 60000, "emoji": "🏫"},
        "مصنع_صغير": {"price": 400000, "income": 8000, "emoji": "🏭"},
        "مصنع_كبير": {"price": 1500000, "income": 30000, "emoji": "🏭"},
        "شركة_نفط": {"price": 15000000, "income": 300000, "emoji": "🛢️"},
    },
}

# ═══════════════════════════════════════════════════════════
# 💼 الوظائف
# ═══════════════════════════════════════════════════════════

JOBS = {
    "عاطل": {"salary": 0, "required_balance": 0, "emoji": "😴"},
    "عامل_نظافة": {"salary": 200, "required_balance": 0, "emoji": "🧹"},
    "بائع": {"salary": 400, "required_balance": 1000, "emoji": "🛒"},
    "نادل": {"salary": 500, "required_balance": 2000, "emoji": "🍽️"},
    "طباخ": {"salary": 600, "required_balance": 5000, "emoji": "👨‍🍳"},
    "سائق": {"salary": 700, "required_balance": 10000, "emoji": "🚗"},
    "موظف_بنك": {"salary": 1000, "required_balance": 25000, "emoji": "🏦"},
    "معلم": {"salary": 1200, "required_balance": 50000, "emoji": "👨‍🏫"},
    "مهندس": {"salary": 1500, "required_balance": 100000, "emoji": "👷"},
    "دكتور": {"salary": 2000, "required_balance": 200000, "emoji": "👨‍⚕️"},
    "محامي": {"salary": 2500, "required_balance": 300000, "emoji": "👨‍⚖️"},
    "مدير": {"salary": 3000, "required_balance": 500000, "emoji": "👨‍💼"},
    "رجل_أعمال": {"salary": 5000, "required_balance": 1000000, "emoji": "👔"},
    "مليونير": {"salary": 10000, "required_balance": 5000000, "emoji": "🤑"},
    "ملياردير": {"salary": 50000, "required_balance": 50000000, "emoji": "💎"},
}

# ═══════════════════════════════════════════════════════════
# 🏦 أنواع القروض
# ═══════════════════════════════════════════════════════════

LOANS = {
    "صغير": {"amount": 5000, "interest": 10, "days": 7},
    "متوسط": {"amount": 25000, "interest": 15, "days": 14},
    "كبير": {"amount": 100000, "interest": 20, "days": 30},
    "ضخم": {"amount": 500000, "interest": 25, "days": 60},
    "عملاق": {"amount": 2000000, "interest": 30, "days": 90},
}

# ═══════════════════════════════════════════════════════════
# 🏦 المصارف الليبية
# ═══════════════════════════════════════════════════════════

BANKS = {
    "الجمهورية": {"interest": 5, "emoji": "🏦", "bonus": 1.0},
    "الصحاري": {"interest": 4, "emoji": "🏦", "bonus": 1.1},
    "التجارة": {"interest": 3, "emoji": "🏦", "bonus": 1.2},
    "الوحدة": {"interest": 4, "emoji": "🏦", "bonus": 1.0, "free_protection": True},
    "ليبيا_المركزي": {"interest": 6, "emoji": "🏦", "bonus": 1.5, "vip_only": True},
}
# ═══════════════════════════════════════════════════════════
# 📁 دوال قاعدة البيانات
# ═══════════════════════════════════════════════════════════

def load_data(file_path: str) -> dict:
    """تحميل البيانات من ملف JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"خطأ في تحميل {file_path}: {e}")
    return {}


def save_data(file_path: str, data: dict) -> bool:
    """حفظ البيانات في ملف JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"خطأ في حفظ {file_path}: {e}")
        return False


def get_bank_data() -> dict:
    """الحصول على بيانات البنك"""
    return load_data(BANK_FILE)


def save_bank_data(data: dict) -> bool:
    """حفظ بيانات البنك"""
    return save_data(BANK_FILE, data)


def get_marriage_data() -> dict:
    """الحصول على بيانات الزواج"""
    return load_data(MARRIAGE_FILE)


def save_marriage_data(data: dict) -> bool:
    """حفظ بيانات الزواج"""
    return save_data(MARRIAGE_FILE, data)


def get_family_data() -> dict:
    """الحصول على بيانات العائلة"""
    return load_data(FAMILY_FILE)


def save_family_data(data: dict) -> bool:
    """حفظ بيانات العائلة"""
    return save_data(FAMILY_FILE, data)


# ═══════════════════════════════════════════════════════════
# 🔢 توليد رقم حساب فريد
# ═══════════════════════════════════════════════════════════

def generate_account_number() -> str:
    """توليد رقم حساب ليبي فريد"""
    data = get_bank_data()
    while True:
        # رقم عشوائي من 7 أرقام
        num = random.randint(1000000, 9999999)
        account_number = f"LY-{num}"
        # التأكد من عدم التكرار
        exists = False
        for user_id, user_data in data.items():
            if user_data.get("account_number") == account_number:
                exists = True
                break
        if not exists:
            return account_number


# ═══════════════════════════════════════════════════════════
# 👤 دوال المستخدم
# ═══════════════════════════════════════════════════════════

def get_user(user_id: int) -> dict:
    """الحصول على بيانات المستخدم"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return None
    
    return data[user_id_str]


def create_account(user_id: int, username: str = None, first_name: str = None) -> dict:
    """إنشاء حساب بنكي جديد"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str in data:
        return data[user_id_str]
    
    account_number = generate_account_number()
    now = time.time()
    
    new_account = {
        "account_number": account_number,
        "username": username or "",
        "first_name": first_name or "مستخدم",
        "balance": SETTINGS["starting_balance"],
        "bank_name": "الجمهورية",  # البنك الافتراضي
        "created_at": now,
        "last_daily": 0,
        "last_salary": 0,
        "last_steal": 0,
        "last_work": 0,
        "job": "عاطل",
        "properties": [],  # الممتلكات
        "vehicles": [],    # المركبات
        "gifts": [],       # الهدايا
        "electronics": [], # الإلكترونيات
        "projects": [],    # المشاريع
        "total_earned": SETTINGS["starting_balance"],
        "total_spent": 0,
        "total_transferred": 0,
        "total_received": 0,
        "total_stolen": 0,
        "total_lost_theft": 0,
        "total_gifts_sent": 0,
        "total_gifts_received": 0,
        "games_won": 0,
        "games_lost": 0,
        "games_profit": 0,
        "protection_until": 0,
        "loan_amount": 0,
        "loan_due": 0,
        "loan_type": None,
        "investments": 0,
        "investment_date": 0,
        "is_banned": False,
        "ban_reason": "",
        "transactions": [],  # سجل المعاملات (آخر 50)
    }
    
    data[user_id_str] = new_account
    save_bank_data(data)
    
    return new_account


def update_user(user_id: int, updates: dict) -> bool:
    """تحديث بيانات المستخدم"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False
    
    for key, value in updates.items():
        data[user_id_str][key] = value
    
    save_bank_data(data)
    return True


def add_balance(user_id: int, amount: int, reason: str = "") -> bool:
    """إضافة رصيد للمستخدم"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False
    
    data[user_id_str]["balance"] += amount
    data[user_id_str]["total_earned"] += amount
    
    # إضافة للسجل
    add_transaction(user_id, "إيداع", amount, reason)
    
    save_bank_data(data)
    return True


def remove_balance(user_id: int, amount: int, reason: str = "") -> bool:
    """خصم رصيد من المستخدم"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False
    
    if data[user_id_str]["balance"] < amount:
        return False
    
    data[user_id_str]["balance"] -= amount
    data[user_id_str]["total_spent"] += amount
    
    # إضافة للسجل
    add_transaction(user_id, "سحب", -amount, reason)
    
    save_bank_data(data)
    return True


def get_balance(user_id: int) -> int:
    """الحصول على رصيد المستخدم"""
    user = get_user(user_id)
    if user:
        return user.get("balance", 0)
    return 0


def add_transaction(user_id: int, trans_type: str, amount: int, description: str = ""):
    """إضافة معاملة للسجل"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return
    
    transaction = {
        "type": trans_type,
        "amount": amount,
        "description": description,
        "time": time.time(),
    }
    
    # الاحتفاظ بآخر 50 معاملة فقط
    if "transactions" not in data[user_id_str]:
        data[user_id_str]["transactions"] = []
    
    data[user_id_str]["transactions"].insert(0, transaction)
    data[user_id_str]["transactions"] = data[user_id_str]["transactions"][:50]
    
    save_bank_data(data)


def get_user_by_account(account_number: str) -> tuple:
    """البحث عن مستخدم برقم الحساب"""
    data = get_bank_data()
    
    for user_id, user_data in data.items():
        if user_data.get("account_number") == account_number:
            return int(user_id), user_data
    
    return None, None


def transfer_money(from_id: int, to_id: int, amount: int) -> tuple:
    """تحويل أموال بين مستخدمين"""
    data = get_bank_data()
    from_str = str(from_id)
    to_str = str(to_id)
    
    if from_str not in data or to_str not in data:
        return False, "أحد الحسابات غير موجود"
    
    if data[from_str]["balance"] < amount:
        return False, "رصيدك غير كافي"
    
    if amount <= 0:
        return False, "المبلغ غير صالح"
    
    # التحقق من حد التحويل
    if from_id in VIP_USERS or from_id in SUDO_USERS or from_id == OWNER_ID:
        limit = SETTINGS["transfer_limit_vip"]
    else:
        limit = SETTINGS["transfer_limit_normal"]
    
    if amount > limit and from_id != OWNER_ID:
        return False, f"تجاوزت حد التحويل ({limit:,} {SETTINGS['currency']})"
    
    # تنفيذ التحويل
    data[from_str]["balance"] -= amount
    data[from_str]["total_transferred"] += amount
    
    data[to_str]["balance"] += amount
    data[to_str]["total_received"] += amount
    
    # إضافة للسجل
    add_transaction(from_id, "تحويل صادر", -amount, f"إلى {data[to_str]['first_name']}")
    add_transaction(to_id, "تحويل وارد", amount, f"من {data[from_str]['first_name']}")
    
    save_bank_data(data)
    return True, "تم التحويل بنجاح"


# ═══════════════════════════════════════════════════════════
# 🛒 دوال الشراء والبيع
# ═══════════════════════════════════════════════════════════

def buy_item(user_id: int, category: str, item_name: str) -> tuple:
    """شراء عنصر من المتجر"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False, "ما عندك حساب!"
    
    # البحث عن العنصر
    item = None
    item_key = item_name.replace(" ", "_")
    
    if category in SHOP and item_key in SHOP[category]:
        item = SHOP[category][item_key]
    else:
        # البحث في كل الفئات
        for cat, items in SHOP.items():
            if item_key in items:
                item = items[item_key]
                category = cat
                break
    
    if not item:
        return False, "المنتج غير موجود!"
    
    price = item["price"]
    
    # التحقق من الرصيد
    if data[user_id_str]["balance"] < price:
        return False, f"رصيدك غير كافي! تحتاج {price:,} {SETTINGS['currency']}"
    
    # تحديد قائمة التخزين
    if category == "عقارات":
        storage_key = "properties"
    elif category == "مركبات":
        storage_key = "vehicles"
    elif category == "هدايا":
        storage_key = "gifts"
    elif category == "إلكترونيات":
        storage_key = "electronics"
    elif category == "مشاريع":
        storage_key = "projects"
    else:
        storage_key = "properties"
    
    # خصم المبلغ وإضافة العنصر
    data[user_id_str]["balance"] -= price
    data[user_id_str]["total_spent"] += price
    
    if storage_key not in data[user_id_str]:
        data[user_id_str][storage_key] = []
    
    data[user_id_str][storage_key].append({
        "name": item_key,
        "bought_at": time.time(),
        "price": price,
    })
    
    add_transaction(user_id, "شراء", -price, f"شراء {item_key}")
    
    save_bank_data(data)
    
    return True, f"تم شراء {item['emoji']} {item_name} بـ {price:,} {SETTINGS['currency']}"


def sell_item(user_id: int, item_name: str) -> tuple:
    """بيع عنصر"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False, "ما عندك حساب!"
    
    item_key = item_name.replace(" ", "_")
    
    # البحث عن العنصر في ممتلكات المستخدم
    storage_keys = ["properties", "vehicles", "electronics", "projects"]
    found = False
    item_data = None
    found_key = None
    
    for key in storage_keys:
        if key in data[user_id_str]:
            for i, owned_item in enumerate(data[user_id_str][key]):
                if owned_item["name"] == item_key:
                    item_data = owned_item
                    found_key = key
                    data[user_id_str][key].pop(i)
                    found = True
                    break
        if found:
            break
    
    if not found:
        return False, "ما عندك هذا المنتج!"
    
    # سعر البيع = 70% من سعر الشراء
    sell_price = int(item_data["price"] * 0.7)
    
    data[user_id_str]["balance"] += sell_price
    data[user_id_str]["total_earned"] += sell_price
    
    add_transaction(user_id, "بيع", sell_price, f"بيع {item_key}")
    
    save_bank_data(data)
    
    return True, f"تم بيع {item_name} بـ {sell_price:,} {SETTINGS['currency']}"


def get_user_items(user_id: int) -> dict:
    """الحصول على كل ممتلكات المستخدم"""
    user = get_user(user_id)
    if not user:
        return {}
    
    return {
        "properties": user.get("properties", []),
        "vehicles": user.get("vehicles", []),
        "gifts": user.get("gifts", []),
        "electronics": user.get("electronics", []),
        "projects": user.get("projects", []),
    }


def calculate_daily_income(user_id: int) -> int:
    """حساب الدخل اليومي من الممتلكات والمشاريع"""
    user = get_user(user_id)
    if not user:
        return 0
    
    total_income = 0
    
    # الدخل من العقارات
    for prop in user.get("properties", []):
        prop_name = prop["name"]
        if prop_name in SHOP.get("عقارات", {}):
            total_income += SHOP["عقارات"][prop_name].get("income", 0)
    
    # الدخل من المركبات (تاكسي، باص، شاحنة)
    for vehicle in user.get("vehicles", []):
        vehicle_name = vehicle["name"]
        if vehicle_name in SHOP.get("مركبات", {}):
            total_income += SHOP["مركبات"][vehicle_name].get("income", 0)
    
    # الدخل من المشاريع
    for project in user.get("projects", []):
        project_name = project["name"]
        if project_name in SHOP.get("مشاريع", {}):
            total_income += SHOP["مشاريع"][project_name].get("income", 0)
    
    return total_income


# ═══════════════════════════════════════════════════════════
# 🎁 دوال الإهداء
# ═══════════════════════════════════════════════════════════

def gift_item(from_id: int, to_id: int, item_name: str) -> tuple:
    """إهداء عنصر لمستخدم آخر"""
    data = get_bank_data()
    from_str = str(from_id)
    to_str = str(to_id)
    
    if from_str not in data or to_str not in data:
        return False, "أحد الحسابات غير موجود!"
    
    item_key = item_name.replace(" ", "_")
    
    # البحث في الهدايا
    found = False
    item_idx = -1
    
    if "gifts" in data[from_str]:
        for i, gift in enumerate(data[from_str]["gifts"]):
            if gift["name"] == item_key:
                item_idx = i
                found = True
                break
    
    if not found:
        # ربما يريد شراء وإهداء مباشرة
        # البحث في المتجر
        gift_item_data = None
        if item_key in SHOP.get("هدايا", {}):
            gift_item_data = SHOP["هدايا"][item_key]
        
        if gift_item_data:
            price = gift_item_data["price"]
            if data[from_str]["balance"] < price:
                return False, f"رصيدك غير كافي! تحتاج {price:,} {SETTINGS['currency']}"
            
            # شراء وإهداء
            data[from_str]["balance"] -= price
            data[from_str]["total_spent"] += price
            data[from_str]["total_gifts_sent"] += 1
            
            if "gifts" not in data[to_str]:
                data[to_str]["gifts"] = []
            
            data[to_str]["gifts"].append({
                "name": item_key,
                "from": from_id,
                "from_name": data[from_str]["first_name"],
                "received_at": time.time(),
            })
            data[to_str]["total_gifts_received"] += 1
            
            add_transaction(from_id, "إهداء", -price, f"إهداء {item_key} لـ {data[to_str]['first_name']}")
            
            save_bank_data(data)
            
            emoji = gift_item_data.get("emoji", "🎁")
            return True, f"تم إهداء {emoji} {item_name} لـ {data[to_str]['first_name']}"
        
        return False, "ما عندك هذا المنتج!"
    
    # نقل الهدية
    gift_data = data[from_str]["gifts"].pop(item_idx)
    gift_data["from"] = from_id
    gift_data["from_name"] = data[from_str]["first_name"]
    gift_data["received_at"] = time.time()
    
    if "gifts" not in data[to_str]:
        data[to_str]["gifts"] = []
    
    data[to_str]["gifts"].append(gift_data)
    
    data[from_str]["total_gifts_sent"] += 1
    data[to_str]["total_gifts_received"] += 1
    
    save_bank_data(data)
    
    return True, f"تم إهداء {item_name} لـ {data[to_str]['first_name']}"


def gift_money(from_id: int, to_id: int, amount: int) -> tuple:
    """إهداء مبلغ مالي"""
    return transfer_money(from_id, to_id, amount)


# ═══════════════════════════════════════════════════════════
# 💼 دوال الوظائف
# ═══════════════════════════════════════════════════════════

def get_job(user_id: int) -> str:
    """الحصول على وظيفة المستخدم"""
    user = get_user(user_id)
    if user:
        return user.get("job", "عاطل")
    return "عاطل"


def set_job(user_id: int, job_name: str) -> tuple:
    """تعيين وظيفة للمستخدم"""
    if job_name not in JOBS:
        return False, "الوظيفة غير موجودة!"
    
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!"
    
    job = JOBS[job_name]
    required = job["required_balance"]
    
    if user["balance"] < required:
        return False, f"تحتاج رصيد {required:,} {SETTINGS['currency']} على الأقل لهذه الوظيفة!"
    
    update_user(user_id, {"job": job_name})
    
    return True, f"مبروك! صرت {job['emoji']} {job_name} براتب {job['salary']:,} {SETTINGS['currency']} يومياً"


def collect_salary(user_id: int) -> tuple:
    """استلام الراتب"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!"
    
    job_name = user.get("job", "عاطل")
    if job_name == "عاطل":
        return False, "انت عاطل! روح دور على شغل 😅"
    
    last_salary = user.get("last_salary", 0)
    now = time.time()
    
    # الراتب كل 24 ساعة
    if now - last_salary < 86400:
        remaining = 86400 - (now - last_salary)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return False, f"استنى {hours} ساعة و {minutes} دقيقة لراتبك الجاي"
    
    job = JOBS[job_name]
    salary = job["salary"]
    
    # مضاعفة للـ VIP
    if user_id in VIP_USERS:
        salary = int(salary * 1.5)
    elif user_id in SUDO_USERS:
        salary = int(salary * 2)
    elif user_id == OWNER_ID:
        salary = int(salary * 3)
    
    add_balance(user_id, salary, "راتب")
    update_user(user_id, {"last_salary": now})
    
    return True, f"تم استلام راتبك {salary:,} {SETTINGS['currency']} 💵"


# ═══════════════════════════════════════════════════════════
# 📊 دوال الترتيب
# ═══════════════════════════════════════════════════════════

def get_top_balance(limit: int = 10) -> list:
    """الحصول على أغنى المستخدمين"""
    data = get_bank_data()
    users = []
    
    for user_id, user_data in data.items():
        if not user_data.get("is_banned", False):
            users.append({
                "user_id": int(user_id),
                "name": user_data.get("first_name", "مجهول"),
                "balance": user_data.get("balance", 0),
                "account": user_data.get("account_number", ""),
            })
    
    users.sort(key=lambda x: x["balance"], reverse=True)
    return users[:limit]


def get_top_thieves(limit: int = 10) -> list:
    """الحصول على أكثر السارقين"""
    data = get_bank_data()
    users = []
    
    for user_id, user_data in data.items():
        if not user_data.get("is_banned", False):
            users.append({
                "user_id": int(user_id),
                "name": user_data.get("first_name", "مجهول"),
                "stolen": user_data.get("total_stolen", 0),
            })
    
    users.sort(key=lambda x: x["stolen"], reverse=True)
    return users[:limit]


def get_top_generous(limit: int = 10) -> list:
    """الحصول على أكثر الكرماء"""
    data = get_bank_data()
    users = []
    
    for user_id, user_data in data.items():
        if not user_data.get("is_banned", False):
            users.append({
                "user_id": int(user_id),
                "name": user_data.get("first_name", "مجهول"),
                "gifts": user_data.get("total_gifts_sent", 0),
                "transferred": user_data.get("total_transferred", 0),
            })
    
    users.sort(key=lambda x: x["gifts"] + x["transferred"], reverse=True)
    return users[:limit]
  # ═══════════════════════════════════════════════════════════
# 🔫 نظام السرقة والحماية
# ═══════════════════════════════════════════════════════════

def steal_from_user(thief_id: int, victim_id: int) -> tuple:
    """محاولة سرقة من مستخدم"""
    data = get_bank_data()
    thief_str = str(thief_id)
    victim_str = str(victim_id)
    
    if thief_str not in data:
        return False, "ما عندك حساب!", 0
    
    if victim_str not in data:
        return False, "الضحية ما عنده حساب!", 0
    
    if thief_id == victim_id:
        return False, "ما تقدر تسرق من نفسك يا ذكي! 😂", 0
    
    # التحقق من وقت الانتظار
    last_steal = data[thief_str].get("last_steal", 0)
    now = time.time()
    cooldown = SETTINGS["steal_cooldown"]
    
    if now - last_steal < cooldown:
        remaining = cooldown - (now - last_steal)
        minutes = int(remaining // 60)
        return False, f"استنى {minutes} دقيقة قبل ما تسرق مرة ثانية! ⏰", 0
    
    # التحقق من الحماية
    victim_protection = data[victim_str].get("protection_until", 0)
    if now < victim_protection:
        return False, "الضحية عنده حماية! 🛡️ جرب واحد ثاني", 0
    
    # التحقق من رصيد الضحية
    victim_balance = data[victim_str]["balance"]
    if victim_balance < 100:
        return False, "الضحية مفلس! ما عنده شي يتسرق 😅", 0
    
    # تحديث وقت آخر سرقة
    data[thief_str]["last_steal"] = now
    
    # نسبة النجاح
    success_rate = SETTINGS["steal_success_rate"]
    
    # VIP عندهم نسبة نجاح أعلى
    if thief_id in VIP_USERS:
        success_rate += 10
    elif thief_id in SUDO_USERS:
        success_rate += 20
    elif thief_id == OWNER_ID:
        success_rate = 100  # المطور دائماً ينجح 😎
    
    roll = random.randint(1, 100)
    
    if roll <= success_rate:
        # نجحت السرقة!
        # المبلغ المسروق: 10-30% من رصيد الضحية
        steal_percent = random.randint(10, 30)
        stolen_amount = int(victim_balance * steal_percent / 100)
        stolen_amount = max(stolen_amount, 50)  # على الأقل 50
        stolen_amount = min(stolen_amount, victim_balance)  # لا يتجاوز الرصيد
        
        # تنفيذ السرقة
        data[victim_str]["balance"] -= stolen_amount
        data[victim_str]["total_lost_theft"] += stolen_amount
        
        data[thief_str]["balance"] += stolen_amount
        data[thief_str]["total_stolen"] += stolen_amount
        
        # إضافة للسجل
        add_transaction(thief_id, "سرقة", stolen_amount, f"سرقة من {data[victim_str]['first_name']}")
        add_transaction(victim_id, "انسرقت", -stolen_amount, f"سرقة بواسطة {data[thief_str]['first_name']}")
        
        save_bank_data(data)
        
        return True, f"🔫 نجحت السرقة! سرقت {stolen_amount:,} {SETTINGS['currency']} من {data[victim_str]['first_name']}", stolen_amount
    
    else:
        # فشلت السرقة - غرامة
        fine = random.randint(100, 500)
        fine = min(fine, data[thief_str]["balance"])
        
        if fine > 0:
            data[thief_str]["balance"] -= fine
            add_transaction(thief_id, "غرامة", -fine, "فشل في السرقة")
        
        save_bank_data(data)
        
        return False, f"👮 انمسكت! فشلت السرقة ودفعت غرامة {fine:,} {SETTINGS['currency']}", 0


def buy_protection(user_id: int, days: int = 1) -> tuple:
    """شراء حماية من السرقة"""
    data = get_bank_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        return False, "ما عندك حساب!"
    
    price = SETTINGS["protection_price"] * days
    
    if data[user_id_str]["balance"] < price:
        return False, f"رصيدك غير كافي! تحتاج {price:,} {SETTINGS['currency']}"
    
    data[user_id_str]["balance"] -= price
    
    now = time.time()
    current_protection = data[user_id_str].get("protection_until", 0)
    
    if current_protection > now:
        # إضافة للحماية الحالية
        data[user_id_str]["protection_until"] = current_protection + (days * 86400)
    else:
        # حماية جديدة
        data[user_id_str]["protection_until"] = now + (days * 86400)
    
    add_transaction(user_id, "شراء حماية", -price, f"حماية {days} يوم")
    
    save_bank_data(data)
    
    return True, f"🛡️ تم تفعيل الحماية لمدة {days} يوم!"


def check_protection(user_id: int) -> tuple:
    """التحقق من حالة الحماية"""
    user = get_user(user_id)
    if not user:
        return False, 0
    
    protection_until = user.get("protection_until", 0)
    now = time.time()
    
    if now < protection_until:
        remaining = protection_until - now
        hours = int(remaining // 3600)
        return True, hours
    
    return False, 0


# ═══════════════════════════════════════════════════════════
# 💍 نظام الزواج
# ═══════════════════════════════════════════════════════════

def get_marriage(user_id: int) -> dict:
    """الحصول على بيانات الزواج"""
    data = get_marriage_data()
    user_id_str = str(user_id)
    
    if user_id_str in data:
        return data[user_id_str]
    
    return None


def is_married(user_id: int) -> bool:
    """التحقق هل المستخدم متزوج"""
    marriage = get_marriage(user_id)
    return marriage is not None and marriage.get("status") == "married"


def is_engaged(user_id: int) -> bool:
    """التحقق هل المستخدم مخطوب"""
    marriage = get_marriage(user_id)
    return marriage is not None and marriage.get("status") == "engaged"


def get_partner(user_id: int) -> int:
    """الحصول على شريك الحياة"""
    marriage = get_marriage(user_id)
    if marriage:
        return marriage.get("partner_id")
    return None


def propose(from_id: int, to_id: int, from_name: str, to_name: str) -> tuple:
    """طلب خطوبة"""
    if from_id == to_id:
        return False, "ما تقدر تخطب نفسك! 😂", None
    
    # التحقق من الحالة
    if is_married(from_id) or is_engaged(from_id):
        return False, "انت مرتبط بالفعل! 💍", None
    
    if is_married(to_id) or is_engaged(to_id):
        return False, "هذا الشخص مرتبط بالفعل! 💔", None
    
    # التحقق من الرصيد
    balance = get_balance(from_id)
    cost = SETTINGS["engagement_cost"]
    
    if balance < cost:
        return False, f"تحتاج {cost:,} {SETTINGS['currency']} للخطوبة!", None
    
    # خصم التكلفة
    remove_balance(from_id, cost, "تكلفة الخطوبة")
    
    # إنشاء طلب الخطوبة
    data = get_marriage_data()
    
    data[str(from_id)] = {
        "status": "pending_proposal",
        "partner_id": to_id,
        "partner_name": to_name,
        "proposed_at": time.time(),
        "my_name": from_name,
    }
    
    save_marriage_data(data)
    
    return True, f"💍 تم إرسال طلب الخطوبة لـ {to_name}!", to_id


def accept_proposal(user_id: int, from_id: int) -> tuple:
    """قبول طلب الخطوبة"""
    data = get_marriage_data()
    from_str = str(from_id)
    
    if from_str not in data:
        return False, "ما فيش طلب خطوبة!"
    
    proposal = data[from_str]
    
    if proposal.get("partner_id") != user_id:
        return False, "هذا الطلب مش لك!"
    
    if proposal.get("status") != "pending_proposal":
        return False, "الطلب منتهي الصلاحية!"
    
    # تحديث الحالة للخطوبة
    now = time.time()
    
    data[from_str] = {
        "status": "engaged",
        "partner_id": user_id,
        "partner_name": proposal.get("partner_name", ""),
        "engaged_at": now,
        "my_name": proposal.get("my_name", ""),
    }
    
    user_data = get_user(user_id)
    user_name = user_data.get("first_name", "مجهول") if user_data else "مجهول"
    
    data[str(user_id)] = {
        "status": "engaged",
        "partner_id": from_id,
        "partner_name": proposal.get("my_name", ""),
        "engaged_at": now,
        "my_name": user_name,
    }
    
    save_marriage_data(data)
    
    return True, f"💕 مبروك الخطوبة! {proposal.get('my_name', '')} و {user_name}"


def reject_proposal(user_id: int, from_id: int) -> tuple:
    """رفض طلب الخطوبة"""
    data = get_marriage_data()
    from_str = str(from_id)
    
    if from_str not in data:
        return False, "ما فيش طلب خطوبة!"
    
    proposal = data[from_str]
    
    if proposal.get("partner_id") != user_id:
        return False, "هذا الطلب مش لك!"
    
    # حذف الطلب
    del data[from_str]
    save_marriage_data(data)
    
    return True, "💔 تم رفض طلب الخطوبة"


def marry(user_id: int) -> tuple:
    """إتمام الزواج"""
    if not is_engaged(user_id):
        return False, "لازم تكون مخطوب أولاً! 💍"
    
    marriage = get_marriage(user_id)
    partner_id = marriage.get("partner_id")
    
    # التحقق من الرصيد
    balance = get_balance(user_id)
    cost = SETTINGS["marriage_cost"]
    
    if balance < cost:
        return False, f"تحتاج {cost:,} {SETTINGS['currency']} للزواج!"
    
    # خصم التكلفة
    remove_balance(user_id, cost, "تكلفة الزواج")
    
    # تحديث الحالة
    data = get_marriage_data()
    now = time.time()
    
    data[str(user_id)]["status"] = "married"
    data[str(user_id)]["married_at"] = now
    
    data[str(partner_id)]["status"] = "married"
    data[str(partner_id)]["married_at"] = now
    
    save_marriage_data(data)
    
    partner_name = marriage.get("partner_name", "شريكك")
    
    return True, f"💒 مبروك الزواج! انت و {partner_name} صرتوا زوجين! 🎊"


def divorce(user_id: int) -> tuple:
    """الطلاق"""
    if not is_married(user_id):
        return False, "انت مش متزوج أصلاً! 😅"
    
    marriage = get_marriage(user_id)
    partner_id = marriage.get("partner_id")
    
    # التحقق من الرصيد
    balance = get_balance(user_id)
    cost = SETTINGS["divorce_cost"]
    
    if balance < cost:
        return False, f"تحتاج {cost:,} {SETTINGS['currency']} للطلاق!"
    
    # خصم التكلفة
    remove_balance(user_id, cost, "تكلفة الطلاق")
    
    # حذف بيانات الزواج
    data = get_marriage_data()
    
    if str(user_id) in data:
        del data[str(user_id)]
    
    if str(partner_id) in data:
        del data[str(partner_id)]
    
    save_marriage_data(data)
    
    return True, "💔 تم الطلاق... نتمنى لكم حياة أفضل"


# ═══════════════════════════════════════════════════════════
# 👨‍👩‍👧 نظام العائلة والنسب
# ═══════════════════════════════════════════════════════════

def get_family(user_id: int) -> dict:
    """الحصول على بيانات العائلة"""
    data = get_family_data()
    user_id_str = str(user_id)
    
    if user_id_str in data:
        return data[user_id_str]
    
    return {"children": [], "parents": [], "siblings": []}


def adopt(parent_id: int, child_id: int, parent_name: str, child_name: str) -> tuple:
    """تبني طفل"""
    if parent_id == child_id:
        return False, "ما تقدر تتبنى نفسك! 😂", None
    
    data = get_family_data()
    parent_str = str(parent_id)
    child_str = str(child_id)
    
    # إنشاء بيانات العائلة لو ما موجودة
    if parent_str not in data:
        data[parent_str] = {"children": [], "parents": [], "siblings": []}
    
    if child_str not in data:
        data[child_str] = {"children": [], "parents": [], "siblings": []}
    
    # التحقق من عدم وجود علاقة مسبقة
    if child_id in data[parent_str]["children"]:
        return False, "هذا بالفعل ابنك/بنتك!", None
    
    if len(data[child_str]["parents"]) >= 2:
        return False, "هذا الشخص عنده أبوين بالفعل!", None
    
    # التحقق من الرصيد
    balance = get_balance(parent_id)
    cost = SETTINGS["adoption_cost"]
    
    if balance < cost:
        return False, f"تحتاج {cost:,} {SETTINGS['currency']} للتبني!", None
    
    # إنشاء طلب التبني
    pending_key = f"pending_adoption_{parent_id}_{child_id}"
    data[pending_key] = {
        "parent_id": parent_id,
        "child_id": child_id,
        "parent_name": parent_name,
        "child_name": child_name,
        "created_at": time.time(),
    }
    
    save_family_data(data)
    
    return True, f"👨‍👧 تم إرسال طلب التبني لـ {child_name}!", child_id


def accept_adoption(child_id: int, parent_id: int) -> tuple:
    """قبول طلب التبني"""
    data = get_family_data()
    pending_key = f"pending_adoption_{parent_id}_{child_id}"
    
    if pending_key not in data:
        return False, "ما فيش طلب تبني!"
    
    pending = data[pending_key]
    parent_str = str(parent_id)
    child_str = str(child_id)
    
    # خصم التكلفة من الأب/الأم
    remove_balance(parent_id, SETTINGS["adoption_cost"], "تكلفة التبني")
    
    # إضافة العلاقة
    if parent_str not in data:
        data[parent_str] = {"children": [], "parents": [], "siblings": []}
    
    if child_str not in data:
        data[child_str] = {"children": [], "parents": [], "siblings": []}
    
    data[parent_str]["children"].append({
        "id": child_id,
        "name": pending["child_name"],
        "adopted_at": time.time(),
    })
    
    data[child_str]["parents"].append({
        "id": parent_id,
        "name": pending["parent_name"],
        "adopted_at": time.time(),
    })
    
    # حذف الطلب
    del data[pending_key]
    
    save_family_data(data)
    
    return True, f"👨‍👧 مبروك! {pending['parent_name']} صار أب/أم لـ {pending['child_name']}!"


def add_sibling(user_id: int, sibling_id: int, user_name: str, sibling_name: str) -> tuple:
    """إضافة أخ/أخت"""
    if user_id == sibling_id:
        return False, "ما تقدر تكون أخ نفسك! 😂", None
    
    data = get_family_data()
    user_str = str(user_id)
    sibling_str = str(sibling_id)
    
    if user_str not in data:
        data[user_str] = {"children": [], "parents": [], "siblings": []}
    
    if sibling_str not in data:
        data[sibling_str] = {"children": [], "parents": [], "siblings": []}
    
    # التحقق من عدم وجود علاقة مسبقة
    for sib in data[user_str]["siblings"]:
        if sib["id"] == sibling_id:
            return False, "هذا بالفعل أخوك/أختك!", None
    
    # إنشاء طلب الأخوة
    pending_key = f"pending_sibling_{user_id}_{sibling_id}"
    data[pending_key] = {
        "user_id": user_id,
        "sibling_id": sibling_id,
        "user_name": user_name,
        "sibling_name": sibling_name,
        "created_at": time.time(),
    }
    
    save_family_data(data)
    
    return True, f"👫 تم إرسال طلب الأخوة لـ {sibling_name}!", sibling_id


def accept_sibling(user_id: int, from_id: int) -> tuple:
    """قبول طلب الأخوة"""
    data = get_family_data()
    pending_key = f"pending_sibling_{from_id}_{user_id}"
    
    if pending_key not in data:
        return False, "ما فيش طلب أخوة!"
    
    pending = data[pending_key]
    user_str = str(user_id)
    from_str = str(from_id)
    
    if user_str not in data:
        data[user_str] = {"children": [], "parents": [], "siblings": []}
    
    if from_str not in data:
        data[from_str] = {"children": [], "parents": [], "siblings": []}
    
    now = time.time()
    
    data[user_str]["siblings"].append({
        "id": from_id,
        "name": pending["user_name"],
        "added_at": now,
    })
    
    data[from_str]["siblings"].append({
        "id": user_id,
        "name": pending["sibling_name"],
        "added_at": now,
    })
    
    del data[pending_key]
    save_family_data(data)
    
    return True, f"👫 مبروك! صرتوا إخوة: {pending['user_name']} و {pending['sibling_name']}!"


# ═══════════════════════════════════════════════════════════
# 🏦 نظام القروض
# ═══════════════════════════════════════════════════════════

def get_loan(user_id: int) -> dict:
    """الحصول على بيانات القرض"""
    user = get_user(user_id)
    if not user:
        return None
    
    if user.get("loan_amount", 0) > 0:
        return {
            "amount": user["loan_amount"],
            "due": user["loan_due"],
            "type": user.get("loan_type", ""),
        }
    
    return None


def has_loan(user_id: int) -> bool:
    """التحقق من وجود قرض"""
    loan = get_loan(user_id)
    return loan is not None


def take_loan(user_id: int, loan_type: str) -> tuple:
    """أخذ قرض"""
    if loan_type not in LOANS:
        available = ", ".join(LOANS.keys())
        return False, f"نوع القرض غير موجود! الأنواع المتاحة: {available}"
    
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!"
    
    # التحقق من عدم وجود قرض سابق
    if has_loan(user_id):
        return False, "عندك قرض بالفعل! سدده أولاً"
    
    # التحقق من عمر الحساب (3 أيام)
    account_age = time.time() - user.get("created_at", time.time())
    if account_age < 259200:  # 3 أيام
        return False, "حسابك لازم يكون عمره 3 أيام على الأقل!"
    
    loan = LOANS[loan_type]
    loan_amount = loan["amount"]
    interest = loan["interest"]
    days = loan["days"]
    
    # التحقق من الرصيد (10% من القرض كضمان)
    required_balance = int(loan_amount * 0.1)
    if user["balance"] < required_balance:
        return False, f"تحتاج رصيد {required_balance:,} {SETTINGS['currency']} كضمان!"
    
    # حساب المبلغ الإجمالي مع الفايدة
    total_due = int(loan_amount * (1 + interest / 100))
    due_date = time.time() + (days * 86400)
    
    # إضافة القرض
    add_balance(user_id, loan_amount, f"قرض {loan_type}")
    
    update_user(user_id, {
        "loan_amount": total_due,
        "loan_due": due_date,
        "loan_type": loan_type,
    })
    
    due_date_str = datetime.fromtimestamp(due_date).strftime("%Y-%m-%d")
    
    return True, f"""
🏦 *تم أخذ القرض بنجاح!*

💰 المبلغ: {loan_amount:,} {SETTINGS['currency']}
📊 الفايدة: {interest}%
💵 المبلغ الإجمالي للسداد: {total_due:,} {SETTINGS['currency']}
📅 تاريخ الاستحقاق: {due_date_str}
⏰ المدة: {days} يوم
"""


def pay_loan(user_id: int, amount: int = 0) -> tuple:
    """سداد القرض"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!"
    
    if not has_loan(user_id):
        return False, "ما عندك قرض!"
    
    loan_amount = user["loan_amount"]
    
    # لو ما حدد مبلغ، يسدد كل القرض
    if amount <= 0:
        amount = loan_amount
    
    if user["balance"] < amount:
        return False, f"رصيدك غير كافي! عندك {user['balance']:,} {SETTINGS['currency']}"
    
    # خصم المبلغ
    remove_balance(user_id, amount, "سداد قرض")
    
    remaining = loan_amount - amount
    
    if remaining <= 0:
        # تم السداد الكامل
        update_user(user_id, {
            "loan_amount": 0,
            "loan_due": 0,
            "loan_type": None,
        })
        return True, f"✅ تم سداد القرض بالكامل! دفعت {amount:,} {SETTINGS['currency']}"
    else:
        # سداد جزئي
        update_user(user_id, {"loan_amount": remaining})
        return True, f"✅ تم سداد {amount:,} {SETTINGS['currency']}. المتبقي: {remaining:,} {SETTINGS['currency']}"


def check_overdue_loans():
    """التحقق من القروض المتأخرة"""
    data = get_bank_data()
    now = time.time()
    
    for user_id_str, user_data in data.items():
        if user_data.get("loan_amount", 0) > 0:
            if now > user_data.get("loan_due", 0):
                # القرض متأخر - حظر من البنك
                data[user_id_str]["is_banned"] = True
                data[user_id_str]["ban_reason"] = "قرض متأخر السداد"
    
    save_bank_data(data)


# ═══════════════════════════════════════════════════════════
# 🎰 الألعاب
# ═══════════════════════════════════════════════════════════

def play_dice(user_id: int, bet: int) -> tuple:
    """لعبة النرد"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!", 0, 0
    
    if bet <= 0:
        return False, "المبلغ لازم يكون أكبر من 0!", 0, 0
    
    if user["balance"] < bet:
        return False, f"رصيدك غير كافي! عندك {user['balance']:,} {SETTINGS['currency']}", 0, 0
    
    # رمي النرد
    player_dice = random.randint(1, 6)
    bot_dice = random.randint(1, 6)
    
    if player_dice > bot_dice:
        # فوز
        winnings = bet
        add_balance(user_id, winnings, "فوز بالنرد")
        update_user(user_id, {
            "games_won": user.get("games_won", 0) + 1,
            "games_profit": user.get("games_profit", 0) + winnings,
        })
        return True, f"🎲 نردك: {player_dice} | نردي: {bot_dice}\n🎉 فزت بـ {winnings:,} {SETTINGS['currency']}!", player_dice, bot_dice
    
    elif player_dice < bot_dice:
        # خسارة
        remove_balance(user_id, bet, "خسارة بالنرد")
        update_user(user_id, {
            "games_lost": user.get("games_lost", 0) + 1,
            "games_profit": user.get("games_profit", 0) - bet,
        })
        return False, f"🎲 نردك: {player_dice} | نردي: {bot_dice}\n😢 خسرت {bet:,} {SETTINGS['currency']}", player_dice, bot_dice
    
    else:
        # تعادل
        return None, f"🎲 نردك: {player_dice} | نردي: {bot_dice}\n🤝 تعادل! فلوسك رجعت", player_dice, bot_dice


def play_slots(user_id: int, bet: int) -> tuple:
    """لعبة السلوتس"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!", []
    
    if bet <= 0:
        return False, "المبلغ لازم يكون أكبر من 0!", []
    
    if user["balance"] < bet:
        return False, f"رصيدك غير كافي!", []
    
    # خصم الرهان
    remove_balance(user_id, bet, "رهان سلوتس")
    
    # رموز السلوتس
    symbols = ["🍎", "🍊", "🍋", "🍇", "🍒", "💎", "7️⃣", "🔔", "⭐", "🍀"]
    weights = [20, 18, 16, 14, 12, 5, 3, 6, 4, 2]  # الاحتمالات
    
    # اختيار 3 رموز
    result = random.choices(symbols, weights=weights, k=3)
    
    # حساب الربح
    winnings = 0
    
    if result[0] == result[1] == result[2]:
        # ثلاثة متشابهة
        if result[0] == "💎":
            winnings = bet * 50  # جاكبوت!
            msg = "💎💎💎 جاكبوت!!! "
        elif result[0] == "7️⃣":
            winnings = bet * 30
            msg = "7️⃣7️⃣7️⃣ سبعات! "
        elif result[0] == "🍀":
            winnings = bet * 20
            msg = "🍀🍀🍀 حظ خرافي! "
        elif result[0] == "⭐":
            winnings = bet * 15
            msg = "⭐⭐⭐ نجوم! "
        else:
            winnings = bet * 10
            msg = "🎰 ثلاثة متشابهة! "
    
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        # اثنين متشابهين
        winnings = bet * 2
        msg = "🎰 اثنين متشابهين! "
    
    else:
        # خسارة
        update_user(user_id, {
            "games_lost": user.get("games_lost", 0) + 1,
            "games_profit": user.get("games_profit", 0) - bet,
        })
        return False, f"🎰 {' '.join(result)}\n😢 ما فيش حظ! خسرت {bet:,} {SETTINGS['currency']}", result
    
    # فوز
    add_balance(user_id, winnings, "فوز بالسلوتس")
    update_user(user_id, {
        "games_won": user.get("games_won", 0) + 1,
        "games_profit": user.get("games_profit", 0) + winnings - bet,
    })
    
    return True, f"🎰 {' '.join(result)}\n{msg}فزت بـ {winnings:,} {SETTINGS['currency']}!", result


def play_coinflip(user_id: int, bet: int, choice: str) -> tuple:
    """لعبة ورقة أو كتابة"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!"
    
    if bet <= 0:
        return False, "المبلغ لازم يكون أكبر من 0!"
    
    if user["balance"] < bet:
        return False, f"رصيدك غير كافي!"
    
    choice = choice.lower()
    if choice not in ["ورقة", "كتابة", "صورة", "نقش"]:
        return False, "اختر: ورقة أو كتابة"
    
    # تحويل الاختيار
    if choice in ["ورقة", "صورة"]:
        player_choice = "ورقة"
    else:
        player_choice = "كتابة"
    
    # رمي العملة
    result = random.choice(["ورقة", "كتابة"])
    
    if player_choice == result:
        # فوز
        winnings = bet
        add_balance(user_id, winnings, "فوز بالعملة")
        update_user(user_id, {
            "games_won": user.get("games_won", 0) + 1,
            "games_profit": user.get("games_profit", 0) + winnings,
        })
        emoji = "📜" if result == "ورقة" else "✍️"
        return True, f"🪙 النتيجة: {emoji} {result}\n🎉 فزت بـ {winnings:,} {SETTINGS['currency']}!"
    else:
        # خسارة
        remove_balance(user_id, bet, "خسارة بالعملة")
        update_user(user_id, {
            "games_lost": user.get("games_lost", 0) + 1,
            "games_profit": user.get("games_profit", 0) - bet,
        })
        emoji = "📜" if result == "ورقة" else "✍️"
        return False, f"🪙 النتيجة: {emoji} {result}\n😢 خسرت {bet:,} {SETTINGS['currency']}"


def play_guess(user_id: int, bet: int, guess: int) -> tuple:
    """لعبة التخمين"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!", 0
    
    if bet <= 0:
        return False, "المبلغ لازم يكون أكبر من 0!", 0
    
    if user["balance"] < bet:
        return False, f"رصيدك غير كافي!", 0
    
    if guess < 1 or guess > 10:
        return False, "خمن رقم من 1 إلى 10!", 0
    
    # الرقم الصحيح
    correct = random.randint(1, 10)
    
    if guess == correct:
        # فوز - 5x الرهان
        winnings = bet * 5
        add_balance(user_id, winnings - bet, "فوز بالتخمين")
        update_user(user_id, {
            "games_won": user.get("games_won", 0) + 1,
            "games_profit": user.get("games_profit", 0) + winnings - bet,
        })
        return True, f"🔢 الرقم الصحيح: {correct}\n🎉 خمنت صح! فزت بـ {winnings:,} {SETTINGS['currency']}!", correct
    else:
        # خسارة
        remove_balance(user_id, bet, "خسارة بالتخمين")
        update_user(user_id, {
            "games_lost": user.get("games_lost", 0) + 1,
            "games_profit": user.get("games_profit", 0) - bet,
        })
        return False, f"🔢 الرقم الصحيح: {correct} (انت قلت {guess})\n😢 خسرت {bet:,} {SETTINGS['currency']}", correct


def play_wheel(user_id: int, bet: int) -> tuple:
    """عجلة الحظ"""
    user = get_user(user_id)
    if not user:
        return False, "ما عندك حساب!", 0
    
    if bet <= 0:
        return False, "المبلغ لازم يكون أكبر من 0!", 0
    
    if user["balance"] < bet:
        return False, f"رصيدك غير كافي!", 0
    
    # خصم الرهان
    remove_balance(user_id, bet, "رهان عجلة الحظ")
    
    # نتائج العجلة مع الاحتمالات
    wheel = [
        {"multiplier": 0, "emoji": "💀", "name": "خسارة", "weight": 25},
        {"multiplier": 0.5, "emoji": "😐", "name": "نص فلوسك", "weight": 20},
        {"multiplier": 1, "emoji": "🔄", "name": "فلوسك رجعت", "weight": 20},
        {"multiplier": 1.5, "emoji": "😊", "name": "ربح صغير", "weight": 15},
        {"multiplier": 2, "emoji": "🎉", "name": "ضعف!", "weight": 10},
        {"multiplier": 3, "emoji": "🔥", "name": "ثلاثة أضعاف!", "weight": 5},
        {"multiplier": 5, "emoji": "💎", "name": "خمسة أضعاف!", "weight": 3},
        {"multiplier": 10, "emoji": "🌟", "name": "عشرة أضعاف!!", "weight": 1.5},
        {"multiplier": 20, "emoji": "👑", "name": "جاكبوت!!!", "weight": 0.5},
    ]
    
    weights = [item["weight"] for item in wheel]
    result = random.choices(wheel, weights=weights, k=1)[0]
    
    winnings = int(bet * result["multiplier"])
    
    if winnings > 0:
        add_balance(user_id, winnings, "عجلة الحظ")
    
    profit = winnings - bet
    
    if profit > 0:
        update_user(user_id, {
            "games_won": user.get("games_won", 0) + 1,
            "games_profit": user.get("games_profit", 0) + profit,
        })
        return True, f"🎡 العجلة توقفت على: {result['emoji']} {result['name']}\n💰 ربحت {winnings:,} {SETTINGS['currency']}!", winnings
    elif profit == 0:
        return None, f"🎡 العجلة توقفت على: {result['emoji']} {result['name']}\n🔄 فلوسك رجعت!", winnings
    else:
        update_user(user_id, {
            "games_lost": user.get("games_lost", 0) + 1,
            "games_profit": user.get("games_profit", 0) + profit,
        })
        if winnings > 0:
            return False, f"🎡 العجلة توقفت على: {result['emoji']} {result['name']}\n😢 رجعلك {winnings:,} {SETTINGS['currency']} بس", winnings
        else:
            return False, f"🎡 العجلة توقفت على: {result['emoji']} {result['name']}\n💀 خسرت كل شي!", winnings
          # ═══════════════════════════════════════════════════════════
# 🔧 دوال مساعدة
# ═══════════════════════════════════════════════════════════

def format_number(num: int) -> str:
    """تنسيق الأرقام بالفواصل"""
    return f"{num:,}"


def format_time_remaining(seconds: float) -> str:
    """تنسيق الوقت المتبقي"""
    if seconds <= 0:
        return "الآن"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} ساعة")
    if minutes > 0:
        parts.append(f"{minutes} دقيقة")
    if secs > 0 and hours == 0:
        parts.append(f"{secs} ثانية")
    
    return " و ".join(parts) if parts else "الآن"


def get_user_rank(user_id: int) -> str:
    """الحصول على رتبة المستخدم"""
    if user_id == OWNER_ID:
        return "👑 المطور"
    elif user_id in SUDO_USERS:
        return "🌟 مالك"
    elif user_id in VIP_USERS:
        return "⭐ مميز"
    else:
        return "👤 عضو"


def get_libya_time() -> datetime:
    """الحصول على توقيت ليبيا"""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    libya_offset = timedelta(hours=2)  # توقيت ليبيا UTC+2
    return utc_now + libya_offset


# ═══════════════════════════════════════════════════════════
# 💳 أوامر الحساب الأساسية
# ═══════════════════════════════════════════════════════════

def cmd_create_account(update: Update, context: CallbackContext):
    """إنشاء حساب بنكي جديد"""
    user = update.effective_user
    message = update.effective_message
    
    # التحقق من وجود حساب
    existing = get_user(user.id)
    if existing:
        message.reply_text(
            f"✅ عندك حساب بالفعل!\n\n"
            f"🔢 رقم الحساب: `{existing['account_number']}`\n"
            f"💰 الرصيد: {format_number(existing['balance'])} {SETTINGS['currency']}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # إنشاء حساب جديد
    account = create_account(user.id, user.username, user.first_name)
    
    message.reply_text(
        f"🎉 *مبروك! تم إنشاء حسابك البنكي*\n\n"
        f"🏦 المصرف: مصرف الجمهورية\n"
        f"🔢 رقم الحساب: `{account['account_number']}`\n"
        f"💰 رصيدك الابتدائي: {format_number(account['balance'])} {SETTINGS['currency']}\n\n"
        f"📝 استخدم /مساعدة_البنك لمعرفة الأوامر",
        parse_mode=ParseMode.MARKDOWN
    )


def cmd_balance(update: Update, context: CallbackContext):
    """عرض الرصيد"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text(
            "❌ ما عندك حساب!\n\n"
            "📝 اكتب /حساب لإنشاء حساب جديد"
        )
        return
    
    # حساب الدخل اليومي
    daily_income = calculate_daily_income(user.id)
    
    # التحقق من الحماية
    has_prot, prot_hours = check_protection(user.id)
    prot_text = f"🛡️ الحماية: {prot_hours} ساعة متبقية" if has_prot else "🛡️ الحماية: ❌ غير مفعلة"
    
    # التحقق من القرض
    loan = get_loan(user.id)
    loan_text = f"💳 القرض: {format_number(loan['amount'])} {SETTINGS['currency']}" if loan else "💳 القرض: لا يوجد"
    
    rank = get_user_rank(user.id)
    
    text = f"""
💳 *حسابك البنكي*

👤 الاسم: {user.first_name}
{rank}
🔢 رقم الحساب: `{account['account_number']}`
🏦 المصرف: مصرف {account.get('bank_name', 'الجمهورية')}

💰 الرصيد: {format_number(account['balance'])} {SETTINGS['currency']}
📈 الدخل اليومي: {format_number(daily_income)} {SETTINGS['currency']}
💼 الوظيفة: {JOBS.get(account.get('job', 'عاطل'), {}).get('emoji', '😴')} {account.get('job', 'عاطل')}

{prot_text}
{loan_text}

📊 *الإحصائيات:*
├ إجمالي المكتسب: {format_number(account.get('total_earned', 0))}
├ إجمالي المصروف: {format_number(account.get('total_spent', 0))}
├ التحويلات الصادرة: {format_number(account.get('total_transferred', 0))}
├ التحويلات الواردة: {format_number(account.get('total_received', 0))}
├ المسروق: {format_number(account.get('total_stolen', 0))}
└ الخسائر من السرقة: {format_number(account.get('total_lost_theft', 0))}
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_account_info(update: Update, context: CallbackContext):
    """معلومات الحساب الكاملة"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    # حساب عمر الحساب
    created = account.get('created_at', time.time())
    age_days = int((time.time() - created) / 86400)
    
    # عد الممتلكات
    properties = len(account.get('properties', []))
    vehicles = len(account.get('vehicles', []))
    projects = len(account.get('projects', []))
    electronics = len(account.get('electronics', []))
    gifts = len(account.get('gifts', []))
    
    text = f"""
📋 *معلومات حسابك الكاملة*

👤 *البيانات الشخصية:*
├ الاسم: {user.first_name}
├ المعرف: @{user.username or 'بدون'}
├ الرتبة: {get_user_rank(user.id)}
└ عمر الحساب: {age_days} يوم

🏦 *البيانات البنكية:*
├ رقم الحساب: `{account['account_number']}`
├ المصرف: {account.get('bank_name', 'الجمهورية')}
└ الرصيد: {format_number(account['balance'])} {SETTINGS['currency']}

🏠 *الممتلكات:*
├ العقارات: {properties}
├ المركبات: {vehicles}
├ المشاريع: {projects}
├ الإلكترونيات: {electronics}
└ الهدايا: {gifts}

🎮 *إحصائيات الألعاب:*
├ مرات الفوز: {account.get('games_won', 0)}
├ مرات الخسارة: {account.get('games_lost', 0)}
└ صافي الربح/الخسارة: {format_number(account.get('games_profit', 0))}
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_daily(update: Update, context: CallbackContext):
    """المكافأة اليومية"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    now = time.time()
    last_daily = account.get('last_daily', 0)
    cooldown = SETTINGS['daily_cooldown']
    
    if now - last_daily < cooldown:
        remaining = cooldown - (now - last_daily)
        message.reply_text(
            f"⏰ استنى {format_time_remaining(remaining)} للمكافأة الجاية!"
        )
        return
    
    # تحديد المكافأة حسب الرتبة
    if user.id == OWNER_ID:
        reward = SETTINGS['owner_daily']
        bonus_text = "👑 مكافأة المطور!"
    elif user.id in SUDO_USERS:
        reward = SETTINGS['sudo_daily']
        bonus_text = "🌟 مكافأة المالك!"
    elif user.id in VIP_USERS:
        reward = SETTINGS['vip_daily']
        bonus_text = "⭐ مكافأة VIP!"
    else:
        reward = SETTINGS['daily_reward']
        bonus_text = ""
    
    # مكافأة إضافية للمتزوجين
    if is_married(user.id):
        reward = int(reward * 1.2)
        bonus_text += " 💕 +20% مكافأة الزواج!"
    
    # إضافة الدخل اليومي من الممتلكات
    property_income = calculate_daily_income(user.id)
    total_reward = reward + property_income
    
    add_balance(user.id, total_reward, "مكافأة يومية")
    update_user(user.id, {'last_daily': now})
    
    text = f"""
🎁 *المكافأة اليومية*

💵 المكافأة الأساسية: {format_number(reward)} {SETTINGS['currency']}
🏠 دخل الممتلكات: {format_number(property_income)} {SETTINGS['currency']}
━━━━━━━━━━━━━━━
💰 الإجمالي: {format_number(total_reward)} {SETTINGS['currency']}

{bonus_text}

💳 رصيدك الجديد: {format_number(account['balance'] + total_reward)} {SETTINGS['currency']}
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 💸 أوامر التحويل
# ═══════════════════════════════════════════════════════════

def cmd_transfer(update: Update, context: CallbackContext):
    """تحويل أموال"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    # التحقق من الوسائط
    if len(args) < 2:
        message.reply_text(
            "❌ *طريقة الاستخدام:*\n\n"
            "`/تحويل @المستخدم المبلغ`\n"
            "أو\n"
            "`/تحويل LY-1234567 المبلغ`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    target = args[0]
    try:
        amount = int(args[1].replace(",", ""))
    except ValueError:
        message.reply_text("❌ المبلغ غير صالح!")
        return
    
    if amount <= 0:
        message.reply_text("❌ المبلغ لازم يكون أكبر من 0!")
        return
    
    # البحث عن المستلم
    to_id = None
    to_account = None
    
    if target.startswith("LY-"):
        # البحث برقم الحساب
        to_id, to_account = get_user_by_account(target)
    elif target.startswith("@"):
        # البحث بالمعرف
        # هذا يحتاج قاعدة بيانات للمعرفات
        message.reply_text("⚠️ استخدم رقم الحساب أو رد على رسالة الشخص")
        return
    elif message.reply_to_message:
        # الرد على رسالة
        to_id = message.reply_to_message.from_user.id
        to_account = get_user(to_id)
    
    if not to_id or not to_account:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    if to_id == user.id:
        message.reply_text("❌ ما تقدر تحول لنفسك!")
        return
    
    # تنفيذ التحويل
    success, msg = transfer_money(user.id, to_id, amount)
    
    if success:
        message.reply_text(
            f"✅ *تم التحويل بنجاح!*\n\n"
            f"💸 المبلغ: {format_number(amount)} {SETTINGS['currency']}\n"
            f"👤 إلى: {to_account['first_name']}\n"
            f"🔢 رقم حسابه: `{to_account['account_number']}`\n\n"
            f"💳 رصيدك الجديد: {format_number(account['balance'] - amount)} {SETTINGS['currency']}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # إشعار المستلم
        try:
            context.bot.send_message(
                to_id,
                f"💰 *استلمت تحويل!*\n\n"
                f"💵 المبلغ: {format_number(amount)} {SETTINGS['currency']}\n"
                f"👤 من: {user.first_name}\n\n"
                f"💳 رصيدك الجديد: {format_number(to_account['balance'] + amount)} {SETTINGS['currency']}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        message.reply_text(f"❌ {msg}")


# ═══════════════════════════════════════════════════════════
# 🛒 أوامر المتجر
# ═══════════════════════════════════════════════════════════

def cmd_shop(update: Update, context: CallbackContext):
    """عرض المتجر"""
    message = update.effective_message
    args = context.args
    
    if args:
        category = args[0]
        if category in SHOP:
            items_text = f"🛒 *متجر {category}*\n\n"
            for item_name, item_data in SHOP[category].items():
                display_name = item_name.replace("_", " ")
                income_text = f" (دخل: {item_data['income']}/يوم)" if item_data['income'] > 0 else ""
                items_text += f"{item_data['emoji']} {display_name}: {format_number(item_data['price'])} {SETTINGS['currency']}{income_text}\n"
            
            items_text += f"\n📝 للشراء: `/شراء {category} اسم_المنتج`"
            message.reply_text(items_text, parse_mode=ParseMode.MARKDOWN)
            return
    
    # عرض الأقسام
    text = f"""
🏪 *المتجر الليبي الكبير*

📂 *الأقسام المتاحة:*

🏠 `/متجر عقارات` - بيوت، فنادق، محلات
🚗 `/متجر مركبات` - سيارات، دبابات، طائرات
🎁 `/متجر هدايا` - شكلاطة، ورد، مجوهرات
📱 `/متجر إلكترونيات` - جوالات، لابتوبات
🏪 `/متجر مشاريع` - مطاعم، مقاهي، مصانع

💡 اختر قسم لعرض المنتجات
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🏠 عقارات", callback_data="shop_عقارات"),
            InlineKeyboardButton("🚗 مركبات", callback_data="shop_مركبات"),
        ],
        [
            InlineKeyboardButton("🎁 هدايا", callback_data="shop_هدايا"),
            InlineKeyboardButton("📱 إلكترونيات", callback_data="shop_إلكترونيات"),
        ],
        [
            InlineKeyboardButton("🏪 مشاريع", callback_data="shop_مشاريع"),
        ],
    ]
    
    message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def cmd_buy(update: Update, context: CallbackContext):
    """شراء منتج"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if len(args) < 1:
        message.reply_text(
            "❌ *طريقة الاستخدام:*\n"
            "`/شراء اسم_المنتج`\n\n"
            "مثال: `/شراء فيلا_كبيرة`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    item_name = "_".join(args)
    
    # البحث عن المنتج
    success, msg = buy_item(user.id, "", item_name)
    
    message.reply_text(
        f"{'✅' if success else '❌'} {msg}",
        parse_mode=ParseMode.MARKDOWN
    )


def cmd_sell(update: Update, context: CallbackContext):
    """بيع منتج"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if len(args) < 1:
        message.reply_text(
            "❌ *طريقة الاستخدام:*\n"
            "`/بيع اسم_المنتج`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    item_name = "_".join(args)
    success, msg = sell_item(user.id, item_name)
    
    message.reply_text(f"{'✅' if success else '❌'} {msg}")


def cmd_my_items(update: Update, context: CallbackContext):
    """عرض ممتلكاتي"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    items = get_user_items(user.id)
    
    text = "🏠 *ممتلكاتك*\n\n"
    
    # العقارات
    if items['properties']:
        text += "🏠 *العقارات:*\n"
        for prop in items['properties']:
            item_info = SHOP.get('عقارات', {}).get(prop['name'], {})
            emoji = item_info.get('emoji', '🏠')
            income = item_info.get('income', 0)
            text += f"  {emoji} {prop['name'].replace('_', ' ')} (+{income}/يوم)\n"
        text += "\n"
    
    # المركبات
    if items['vehicles']:
        text += "🚗 *المركبات:*\n"
        for vehicle in items['vehicles']:
            item_info = SHOP.get('مركبات', {}).get(vehicle['name'], {})
            emoji = item_info.get('emoji', '🚗')
            text += f"  {emoji} {vehicle['name'].replace('_', ' ')}\n"
        text += "\n"
    
    # المشاريع
    if items['projects']:
        text += "🏪 *المشاريع:*\n"
        for project in items['projects']:
            item_info = SHOP.get('مشاريع', {}).get(project['name'], {})
            emoji = item_info.get('emoji', '🏪')
            income = item_info.get('income', 0)
            text += f"  {emoji} {project['name'].replace('_', ' ')} (+{income}/يوم)\n"
        text += "\n"
    
    # الإلكترونيات
    if items['electronics']:
        text += "📱 *الإلكترونيات:*\n"
        for elec in items['electronics']:
            item_info = SHOP.get('إلكترونيات', {}).get(elec['name'], {})
            emoji = item_info.get('emoji', '📱')
            text += f"  {emoji} {elec['name'].replace('_', ' ')}\n"
        text += "\n"
    
    # الهدايا
    if items['gifts']:
        text += "🎁 *الهدايا:*\n"
        for gift in items['gifts']:
            item_info = SHOP.get('هدايا', {}).get(gift['name'], {})
            emoji = item_info.get('emoji', '🎁')
            from_name = gift.get('from_name', '')
            from_text = f" (من {from_name})" if from_name else ""
            text += f"  {emoji} {gift['name'].replace('_', ' ')}{from_text}\n"
        text += "\n"
    
    # لو ما عنده شي
    total_items = sum(len(v) for v in items.values())
    if total_items == 0:
        text += "😢 ما عندك أي ممتلكات!\n\n"
        text += "💡 استخدم /متجر لشراء منتجات"
    else:
        daily_income = calculate_daily_income(user.id)
        text += f"━━━━━━━━━━━━━━━\n"
        text += f"📈 *الدخل اليومي الإجمالي:* {format_number(daily_income)} {SETTINGS['currency']}"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 🎁 أوامر الإهداء
# ═══════════════════════════════════════════════════════════

def cmd_gift(update: Update, context: CallbackContext):
    """إهداء"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    # التحقق من الوسائط
    if len(args) < 2 and not message.reply_to_message:
        message.reply_text(
            "❌ *طريقة الاستخدام:*\n\n"
            "إهداء منتج:\n"
            "`/اهداء @المستخدم شكلاطة`\n\n"
            "إهداء فلوس:\n"
            "`/اهداء @المستخدم 1000`\n\n"
            "أو رد على رسالة الشخص",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # تحديد المستلم
    to_id = None
    to_account = None
    gift_item = None
    
    if message.reply_to_message:
        to_id = message.reply_to_message.from_user.id
        to_account = get_user(to_id)
        gift_item = "_".join(args) if args else None
    else:
        # البحث عن المستخدم
        # نحتاج منشن أو رقم حساب
        if args[0].startswith("LY-"):
            to_id, to_account = get_user_by_account(args[0])
            gift_item = "_".join(args[1:]) if len(args) > 1 else None
        else:
            message.reply_text("⚠️ رد على رسالة الشخص أو استخدم رقم حسابه")
            return
    
    if not to_id or not to_account:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    if to_id == user.id:
        message.reply_text("❌ ما تقدر تهدي نفسك!")
        return
    
    if not gift_item:
        message.reply_text("❌ حدد الهدية!")
        return
    
    # التحقق هل هو مبلغ مالي
    try:
        amount = int(gift_item.replace(",", ""))
        # إهداء فلوس
        success, msg = gift_money(user.id, to_id, amount)
        if success:
            message.reply_text(
                f"🎁 *تم الإهداء!*\n\n"
                f"💵 المبلغ: {format_number(amount)} {SETTINGS['currency']}\n"
                f"👤 إلى: {to_account['first_name']}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            message.reply_text(f"❌ {msg}")
        return
    except ValueError:
        pass
    
    # إهداء منتج
    success, msg = gift_item(user.id, to_id, gift_item)
    message.reply_text(f"{'🎁' if success else '❌'} {msg}")


# ═══════════════════════════════════════════════════════════
# 🔫 أوامر السرقة والحماية
# ═══════════════════════════════════════════════════════════

def cmd_steal(update: Update, context: CallbackContext):
    """سرقة"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    # تحديد الضحية
    victim_id = None
    
    if message.reply_to_message:
        victim_id = message.reply_to_message.from_user.id
    elif context.args:
        if context.args[0].startswith("LY-"):
            victim_id, _ = get_user_by_account(context.args[0])
    
    if not victim_id:
        message.reply_text(
            "❌ *رد على رسالة الشخص اللي تبي تسرقه*\n\n"
            "أو استخدم: `/سرقة LY-1234567`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    success, msg, amount = steal_from_user(user.id, victim_id)
    
    message.reply_text(msg)
    
    # إشعار الضحية
    if success and amount > 0:
        try:
            context.bot.send_message(
                victim_id,
                f"🔫 *تم سرقتك!*\n\n"
                f"💸 المبلغ المسروق: {format_number(amount)} {SETTINGS['currency']}\n"
                f"👤 السارق: {user.first_name}\n\n"
                f"💡 اشتري حماية: /حماية",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass


def cmd_protection(update: Update, context: CallbackContext):
    """شراء حماية"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    # التحقق من الحماية الحالية
    has_prot, hours = check_protection(user.id)
    
    days = 1
    if args:
        try:
            days = int(args[0])
            days = max(1, min(days, 30))  # من 1 إلى 30 يوم
        except:
            pass
    
    price = SETTINGS['protection_price'] * days
    
    if has_prot:
        message.reply_text(
            f"🛡️ *عندك حماية بالفعل!*\n\n"
            f"⏰ متبقي: {hours} ساعة\n\n"
            f"💡 تبي تمدد؟ `/حماية {days}`\n"
            f"💰 السعر: {format_number(price)} {SETTINGS['currency']}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        if not args:
            return
    
    success, msg = buy_protection(user.id, days)
    message.reply_text(f"{'✅' if success else '❌'} {msg}")


# ═══════════════════════════════════════════════════════════
# 💍 أوامر الزواج
# ═══════════════════════════════════════════════════════════

def cmd_propose(update: Update, context: CallbackContext):
    """طلب خطوبة"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not message.reply_to_message:
        message.reply_text("❌ رد على رسالة الشخص اللي تبي تخطبه!")
        return
    
    target = message.reply_to_message.from_user
    target_account = get_user(target.id)
    
    if not target_account:
        message.reply_text("❌ هذا الشخص ما عنده حساب!")
        return
    
    success, msg, notify_id = propose(
        user.id, target.id,
        user.first_name, target.first_name
    )
    
    message.reply_text(f"{'💍' if success else '❌'} {msg}")
    
    if success and notify_id:
        keyboard = [
            [
                InlineKeyboardButton("✅ قبول", callback_data=f"accept_proposal_{user.id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject_proposal_{user.id}"),
            ]
        ]
        
        try:
            context.bot.send_message(
                notify_id,
                f"💍 *طلب خطوبة!*\n\n"
                f"👤 {user.first_name} يطلب خطوبتك!\n\n"
                f"اختر:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            pass


def cmd_marry(update: Update, context: CallbackContext):
    """إتمام الزواج"""
    user = update.effective_user
    message = update.effective_message
    
    success, msg = marry(user.id)
    message.reply_text(f"{'💒' if success else '❌'} {msg}")


def cmd_divorce(update: Update, context: CallbackContext):
    """الطلاق"""
    user = update.effective_user
    message = update.effective_message
    
    success, msg = divorce(user.id)
    message.reply_text(f"{'💔' if success else '❌'} {msg}")


def cmd_partner(update: Update, context: CallbackContext):
    """عرض الشريك"""
    user = update.effective_user
    message = update.effective_message
    
    marriage = get_marriage(user.id)
    
    if not marriage:
        message.reply_text("💔 انت عازب/عزباء!")
        return
    
    status = marriage.get('status', '')
    partner_name = marriage.get('partner_name', 'مجهول')
    
    if status == 'engaged':
        message.reply_text(f"💍 انت مخطوب/مخطوبة لـ {partner_name}")
    elif status == 'married':
        married_at = marriage.get('married_at', 0)
        days = int((time.time() - married_at) / 86400)
        message.reply_text(
            f"💕 *شريك حياتك*\n\n"
            f"👤 الاسم: {partner_name}\n"
            f"📅 مدة الزواج: {days} يوم\n"
            f"💒 حالة: متزوجين",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        message.reply_text("💔 انت عازب/عزباء!")
      # ═══════════════════════════════════════════════════════════
# 🎰 أوامر الألعاب
# ═══════════════════════════════════════════════════════════

def cmd_dice(update: Update, context: CallbackContext):
    """لعبة النرد"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not args:
        message.reply_text(
            "🎲 *لعبة النرد*\n\n"
            "الطريقة: `/نرد المبلغ`\n"
            "مثال: `/نرد 100`\n\n"
            "لو نردك أكبر من نردي تفوز!",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        message.reply_text("❌ المبلغ غير صالح!")
        return
    
    result, msg, player_dice, bot_dice = play_dice(user.id, bet)
    
    # إرسال نرد متحرك
    dice_msg = message.reply_dice(emoji="🎲")
    
    # انتظار ثم إرسال النتيجة
    import threading
    def send_result():
        time.sleep(3)
        try:
            message.reply_text(msg)
        except:
            pass
    
    threading.Thread(target=send_result).start()


def cmd_slots(update: Update, context: CallbackContext):
    """لعبة السلوتس"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not args:
        message.reply_text(
            "🎰 *لعبة السلوتس*\n\n"
            "الطريقة: `/سلوتس المبلغ`\n"
            "مثال: `/سلوتس 500`\n\n"
            "💎💎💎 = جاكبوت x50\n"
            "7️⃣7️⃣7️⃣ = x30\n"
            "ثلاثة متشابهة = x10\n"
            "اثنين متشابهين = x2",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        message.reply_text("❌ المبلغ غير صالح!")
        return
    
    result, msg, symbols = play_slots(user.id, bet)
    
    # إرسال سلوتس متحرك
    message.reply_dice(emoji="🎰")
    
    import threading
    def send_result():
        time.sleep(2)
        try:
            message.reply_text(msg)
        except:
            pass
    
    threading.Thread(target=send_result).start()


def cmd_coinflip(update: Update, context: CallbackContext):
    """لعبة ورقة أو كتابة"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if len(args) < 2:
        message.reply_text(
            "🪙 *لعبة ورقة أو كتابة*\n\n"
            "الطريقة: `/ورقة المبلغ اختيارك`\n"
            "مثال: `/ورقة 100 ورقة`\n"
            "أو: `/ورقة 100 كتابة`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        message.reply_text("❌ المبلغ غير صالح!")
        return
    
    choice = args[1]
    result, msg = play_coinflip(user.id, bet, choice)
    
    message.reply_text(msg)


def cmd_guess(update: Update, context: CallbackContext):
    """لعبة التخمين"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if len(args) < 2:
        message.reply_text(
            "🔢 *لعبة التخمين*\n\n"
            "الطريقة: `/تخمين الرقم المبلغ`\n"
            "مثال: `/تخمين 5 100`\n\n"
            "خمن رقم من 1 إلى 10\n"
            "لو صح تفوز x5!",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        guess = int(args[0])
        bet = int(args[1].replace(",", ""))
    except:
        message.reply_text("❌ تأكد من الرقم والمبلغ!")
        return
    
    result, msg, correct = play_guess(user.id, bet, guess)
    message.reply_text(msg)


def cmd_wheel(update: Update, context: CallbackContext):
    """عجلة الحظ"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not args:
        message.reply_text(
            "🎡 *عجلة الحظ*\n\n"
            "الطريقة: `/عجلة المبلغ`\n"
            "مثال: `/عجلة 500`\n\n"
            "💀 خسارة كاملة\n"
            "😐 نص فلوسك\n"
            "🔄 فلوسك ترجع\n"
            "😊 x1.5\n"
            "🎉 x2\n"
            "🔥 x3\n"
            "💎 x5\n"
            "🌟 x10\n"
            "👑 x20 جاكبوت!",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        bet = int(args[0].replace(",", ""))
    except:
        message.reply_text("❌ المبلغ غير صالح!")
        return
    
    result, msg, winnings = play_wheel(user.id, bet)
    message.reply_text(msg)


# ═══════════════════════════════════════════════════════════
# 💼 أوامر الوظائف
# ═══════════════════════════════════════════════════════════

def cmd_jobs(update: Update, context: CallbackContext):
    """عرض الوظائف"""
    message = update.effective_message
    
    text = "💼 *الوظائف المتاحة*\n\n"
    
    for job_name, job_data in JOBS.items():
        if job_name == "عاطل":
            continue
        
        emoji = job_data['emoji']
        salary = job_data['salary']
        required = job_data['required_balance']
        
        text += f"{emoji} *{job_name}*\n"
        text += f"   💵 الراتب: {format_number(salary)} {SETTINGS['currency']}/يوم\n"
        text += f"   💰 المتطلب: {format_number(required)} {SETTINGS['currency']}\n\n"
    
    text += "📝 للتوظف: `/توظف اسم_الوظيفة`"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_work(update: Update, context: CallbackContext):
    """العمل / استلام الراتب"""
    user = update.effective_user
    message = update.effective_message
    
    success, msg = collect_salary(user.id)
    message.reply_text(f"{'💵' if success else '❌'} {msg}")


def cmd_hire(update: Update, context: CallbackContext):
    """التوظف"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not args:
        message.reply_text(
            "❌ حدد الوظيفة!\n\n"
            "مثال: `/توظف دكتور`\n\n"
            "اكتب /وظائف لعرض الوظائف المتاحة",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    job_name = "_".join(args)
    success, msg = set_job(user.id, job_name)
    
    message.reply_text(f"{'✅' if success else '❌'} {msg}")


def cmd_resign(update: Update, context: CallbackContext):
    """الاستقالة"""
    user = update.effective_user
    message = update.effective_message
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب!")
        return
    
    current_job = account.get('job', 'عاطل')
    
    if current_job == 'عاطل':
        message.reply_text("❌ انت عاطل أصلاً! 😅")
        return
    
    update_user(user.id, {'job': 'عاطل'})
    message.reply_text(f"✅ تم الاستقالة من وظيفة {current_job}")


# ═══════════════════════════════════════════════════════════
# 🏦 أوامر القروض
# ═══════════════════════════════════════════════════════════

def cmd_loan(update: Update, context: CallbackContext):
    """طلب قرض"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    account = get_user(user.id)
    if not account:
        message.reply_text("❌ ما عندك حساب! اكتب /حساب")
        return
    
    if not args:
        text = "🏦 *القروض المتاحة*\n\n"
        
        for loan_type, loan_data in LOANS.items():
            amount = loan_data['amount']
            interest = loan_data['interest']
            days = loan_data['days']
            total = int(amount * (1 + interest/100))
            
            text += f"📋 *قرض {loan_type}*\n"
            text += f"   💵 المبلغ: {format_number(amount)} {SETTINGS['currency']}\n"
            text += f"   📊 الفايدة: {interest}%\n"
            text += f"   💰 الإجمالي: {format_number(total)} {SETTINGS['currency']}\n"
            text += f"   ⏰ المدة: {days} يوم\n\n"
        
        text += "📝 للقرض: `/قرض نوع_القرض`\n"
        text += "مثال: `/قرض متوسط`"
        
        message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return
    
    loan_type = args[0]
    success, msg = take_loan(user.id, loan_type)
    
    message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def cmd_pay_loan(update: Update, context: CallbackContext):
    """سداد القرض"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    amount = 0
    if args:
        try:
            amount = int(args[0].replace(",", ""))
        except:
            pass
    
    success, msg = pay_loan(user.id, amount)
    message.reply_text(f"{'✅' if success else '❌'} {msg}")


def cmd_my_loan(update: Update, context: CallbackContext):
    """عرض ديوني"""
    user = update.effective_user
    message = update.effective_message
    
    loan = get_loan(user.id)
    
    if not loan:
        message.reply_text("✅ ما عندك أي ديون!")
        return
    
    due_date = datetime.fromtimestamp(loan['due']).strftime("%Y-%m-%d")
    remaining_time = loan['due'] - time.time()
    
    text = f"""
💳 *ديونك*

💵 المبلغ المتبقي: {format_number(loan['amount'])} {SETTINGS['currency']}
📋 نوع القرض: {loan['type']}
📅 تاريخ الاستحقاق: {due_date}
⏰ الوقت المتبقي: {format_time_remaining(remaining_time)}

📝 للسداد: `/سداد` أو `/سداد المبلغ`
"""
    
    if remaining_time < 0:
        text += "\n⚠️ *القرض متأخر! سدد فوراً!*"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 📊 أوامر الترتيب
# ═══════════════════════════════════════════════════════════

def cmd_top(update: Update, context: CallbackContext):
    """ترتيب الأغنياء"""
    message = update.effective_message
    
    top_users = get_top_balance(10)
    
    if not top_users:
        message.reply_text("❌ ما فيش بيانات!")
        return
    
    text = "🏆 *أغنى 10 مستخدمين*\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user_data in enumerate(top_users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user_data['name'][:15]
        balance = format_number(user_data['balance'])
        text += f"{medal} {name}: {balance} {SETTINGS['currency']}\n"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_top_thieves(update: Update, context: CallbackContext):
    """ترتيب السارقين"""
    message = update.effective_message
    
    top_users = get_top_thieves(10)
    
    text = "🔫 *أكثر 10 سارقين*\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user_data in enumerate(top_users):
        if user_data['stolen'] == 0:
            continue
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user_data['name'][:15]
        stolen = format_number(user_data['stolen'])
        text += f"{medal} {name}: {stolen} {SETTINGS['currency']}\n"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def cmd_top_generous(update: Update, context: CallbackContext):
    """ترتيب الكرماء"""
    message = update.effective_message
    
    top_users = get_top_generous(10)
    
    text = "🎁 *أكثر 10 كرماء*\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user_data in enumerate(top_users):
        total = user_data['gifts'] + user_data['transferred']
        if total == 0:
            continue
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = user_data['name'][:15]
        text += f"{medal} {name}: {user_data['gifts']} هدية + {format_number(user_data['transferred'])} تحويل\n"
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# ⏰ أوامر الوقت
# ═══════════════════════════════════════════════════════════

def cmd_time(update: Update, context: CallbackContext):
    """عرض الوقت"""
    message = update.effective_message
    
    libya_time = get_libya_time()
    
    text = f"""
🕐 *الوقت في ليبيا*

📅 التاريخ: {libya_time.strftime("%Y-%m-%d")}
🕐 الوقت: {libya_time.strftime("%H:%M:%S")}
📆 اليوم: {libya_time.strftime("%A")}
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 👑 أوامر المطور والمالك
# ═══════════════════════════════════════════════════════════

def is_owner(user_id: int) -> bool:
    """التحقق من المطور"""
    return user_id == OWNER_ID


def is_sudo(user_id: int) -> bool:
    """التحقق من المالك"""
    return user_id in SUDO_USERS or user_id == OWNER_ID


def cmd_add_balance(update: Update, context: CallbackContext):
    """إضافة رصيد - للمطور والمالك"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if not is_sudo(user.id):
        message.reply_text("⛔ هذا الأمر للمطور والمالك فقط!")
        return
    
    target_id = None
    amount = 0
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if args:
            try:
                amount = int(args[0].replace(",", ""))
            except:
                pass
    elif len(args) >= 2:
        if args[0].startswith("LY-"):
            target_id, _ = get_user_by_account(args[0])
        try:
            amount = int(args[-1].replace(",", ""))
        except:
            pass
    
    if not target_id or amount <= 0:
        message.reply_text(
            "❌ *طريقة الاستخدام:*\n"
            "رد على رسالة: `/اضافة_رصيد المبلغ`\n"
            "أو: `/اضافة_رصيد LY-123456 المبلغ`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # حد للمالك
    if not is_owner(user.id) and amount > 100000:
        message.reply_text("⚠️ الحد الأقصى للمالك: 100,000")
        return
    
    target_account = get_user(target_id)
    if not target_account:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    add_balance(target_id, amount, f"إضافة من {user.first_name}")
    
    message.reply_text(
        f"✅ تم إضافة {format_number(amount)} {SETTINGS['currency']} لـ {target_account['first_name']}"
    )


def cmd_remove_balance(update: Update, context: CallbackContext):
    """خصم رصيد - للمطور والمالك"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if not is_sudo(user.id):
        message.reply_text("⛔ هذا الأمر للمطور والمالك فقط!")
        return
    
    target_id = None
    amount = 0
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if args:
            try:
                amount = int(args[0].replace(",", ""))
            except:
                pass
    elif len(args) >= 2:
        if args[0].startswith("LY-"):
            target_id, _ = get_user_by_account(args[0])
        try:
            amount = int(args[-1].replace(",", ""))
        except:
            pass
    
    if not target_id or amount <= 0:
        message.reply_text("❌ حدد المستخدم والمبلغ!")
        return
    
    # حد للمالك
    if not is_owner(user.id) and amount > 50000:
        message.reply_text("⚠️ الحد الأقصى للمالك: 50,000")
        return
    
    target_account = get_user(target_id)
    if not target_account:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    success = remove_balance(target_id, amount, f"خصم من {user.first_name}")
    
    if success:
        message.reply_text(
            f"✅ تم خصم {format_number(amount)} {SETTINGS['currency']} من {target_account['first_name']}"
        )
    else:
        message.reply_text("❌ الرصيد غير كافي!")


def cmd_reset_balance(update: Update, context: CallbackContext):
    """تصفير رصيد - للمطور فقط"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif context.args:
        if context.args[0].startswith("LY-"):
            target_id, _ = get_user_by_account(context.args[0])
    
    if not target_id:
        message.reply_text("❌ حدد المستخدم!")
        return
    
    target_account = get_user(target_id)
    if not target_account:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    update_user(target_id, {'balance': 0})
    add_transaction(target_id, "تصفير", 0, f"تصفير بواسطة المطور")
    
    message.reply_text(f"✅ تم تصفير رصيد {target_account['first_name']}")


def cmd_reset_all(update: Update, context: CallbackContext):
    """تصفير الكل - للمطور فقط"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم، صفر الكل", callback_data="confirm_reset_all"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reset_all"),
        ]
    ]
    
    message.reply_text(
        "⚠️ *تحذير!*\n\n"
        "هل أنت متأكد من تصفير رصيد جميع المستخدمين؟\n"
        "هذا الإجراء لا يمكن التراجع عنه!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def cmd_add_sudo(update: Update, context: CallbackContext):
    """تعيين مالك - للمطور فقط"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    if not target_id:
        message.reply_text("❌ رد على رسالة الشخص!")
        return
    
    if target_id in SUDO_USERS:
        message.reply_text("⚠️ هذا الشخص مالك بالفعل!")
        return
    
    SUDO_USERS.append(target_id)
    message.reply_text(f"✅ تم تعيين المستخدم كمالك!")


def cmd_remove_sudo(update: Update, context: CallbackContext):
    """إزالة مالك - للمطور فقط"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    if not target_id:
        message.reply_text("❌ رد على رسالة الشخص!")
        return
    
    if target_id not in SUDO_USERS:
        message.reply_text("⚠️ هذا الشخص ليس مالك!")
        return
    
    SUDO_USERS.remove(target_id)
    message.reply_text(f"✅ تم إزالة المستخدم من المالكين!")


def cmd_add_vip(update: Update, context: CallbackContext):
    """تعيين مميز - للمطور والمالك"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_sudo(user.id):
        message.reply_text("⛔ هذا الأمر للمطور والمالك فقط!")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    if not target_id:
        message.reply_text("❌ رد على رسالة الشخص!")
        return
    
    if target_id in VIP_USERS:
        message.reply_text("⚠️ هذا الشخص مميز بالفعل!")
        return
    
    VIP_USERS.append(target_id)
    message.reply_text(f"✅ تم تعيين المستخدم كـ VIP!")


def cmd_remove_vip(update: Update, context: CallbackContext):
    """إزالة مميز"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_sudo(user.id):
        message.reply_text("⛔ هذا الأمر للمطور والمالك فقط!")
        return
    
    target_id = None
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    
    if not target_id:
        message.reply_text("❌ رد على رسالة الشخص!")
        return
    
    if target_id not in VIP_USERS:
        message.reply_text("⚠️ هذا الشخص ليس مميز!")
        return
    
    VIP_USERS.remove(target_id)
    message.reply_text(f"✅ تم إزالة المستخدم من المميزين!")


def cmd_give_item(update: Update, context: CallbackContext):
    """إعطاء منتج مجاني - للمطور فقط"""
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    if not message.reply_to_message or not args:
        message.reply_text("❌ رد على رسالة الشخص وحدد المنتج!")
        return
    
    target_id = message.reply_to_message.from_user.id
    item_name = "_".join(args)
    
    data = get_bank_data()
    target_str = str(target_id)
    
    if target_str not in data:
        message.reply_text("❌ الحساب غير موجود!")
        return
    
    # البحث عن المنتج
    found = False
    category = ""
    item_data = None
    
    for cat, items in SHOP.items():
        if item_name in items:
            found = True
            category = cat
            item_data = items[item_name]
            break
    
    if not found:
        message.reply_text("❌ المنتج غير موجود!")
        return
    
    # تحديد قائمة التخزين
    storage_keys = {
        "عقارات": "properties",
        "مركبات": "vehicles",
        "هدايا": "gifts",
        "إلكترونيات": "electronics",
        "مشاريع": "projects",
    }
    
    storage_key = storage_keys.get(category, "properties")
    
    if storage_key not in data[target_str]:
        data[target_str][storage_key] = []
    
    data[target_str][storage_key].append({
        "name": item_name,
        "bought_at": time.time(),
        "price": 0,
        "gift_from": "المطور"
    })
    
    save_bank_data(data)
    
    message.reply_text(f"✅ تم إعطاء {item_data['emoji']} {item_name.replace('_', ' ')} للمستخدم!")


def cmd_bank_stats(update: Update, context: CallbackContext):
    """إحصائيات البنك - للمطور"""
    user = update.effective_user
    message = update.effective_message
    
    if not is_owner(user.id):
        message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    data = get_bank_data()
    
    total_users = len(data)
    total_balance = sum(u.get('balance', 0) for u in data.values())
    total_loans = sum(u.get('loan_amount', 0) for u in data.values())
    banned_users = sum(1 for u in data.values() if u.get('is_banned', False))
    
    text = f"""
📊 *إحصائيات البنك الليبي*

👥 إجمالي الحسابات: {total_users}
💰 إجمالي الأرصدة: {format_number(total_balance)} {SETTINGS['currency']}
💳 إجمالي القروض: {format_number(total_loans)} {SETTINGS['currency']}
🚫 المحظورين: {banned_users}

🌟 المالكين: {len(SUDO_USERS)}
⭐ المميزين: {len(VIP_USERS)}
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 📚 أمر المساعدة
# ═══════════════════════════════════════════════════════════

def cmd_bank_help(update: Update, context: CallbackContext):
    """مساعدة البنك"""
    message = update.effective_message
    
    text = """
🏦 *مساعدة البنك الليبي*

💳 *الحساب:*
├ `/حساب` - إنشاء حساب
├ `/رصيدي` - عرض الرصيد
├ `/حسابي` - معلومات كاملة
└ `/يومي` - المكافأة اليومية

💸 *التحويلات:*
└ `/تحويل @user مبلغ` - تحويل

🛒 *المتجر:*
├ `/متجر` - عرض الأقسام
├ `/شراء منتج` - شراء
├ `/بيع منتج` - بيع
└ `/ممتلكاتي` - ممتلكاتك

🎁 *الإهداء:*
└ `/اهداء @user هدية` - إهداء

🔫 *السرقة:*
├ `/سرقة` - سرقة (رد على رسالة)
└ `/حماية` - شراء حماية

💍 *الزواج:*
├ `/خطوبة` - طلب خطوبة
├ `/زواج` - إتمام الزواج
├ `/طلاق` - الطلاق
└ `/شريكي` - عرض الشريك

💼 *الوظائف:*
├ `/وظائف` - الوظائف المتاحة
├ `/توظف وظيفة` - التوظف
├ `/راتب` - استلام الراتب
└ `/استقالة` - الاستقالة

🏦 *القروض:*
├ `/قرض` - أنواع القروض
├ `/قرض نوع` - طلب قرض
├ `/سداد` - سداد القرض
└ `/ديوني` - عرض الديون

🎰 *الألعاب:*
├ `/نرد مبلغ` - النرد
├ `/سلوتس مبلغ` - السلوتس
├ `/ورقة مبلغ اختيار` - ورقة/كتابة
├ `/تخمين رقم مبلغ` - التخمين
└ `/عجلة مبلغ` - عجلة الحظ

📊 *الترتيب:*
├ `/الاغنياء` - أغنى 10
├ `/السارقين` - أكثر سارقين
└ `/الكرماء` - أكثر كرماء

⏰ `/الوقت` - توقيت ليبيا
"""
    
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════
# 🔘 معالج الأزرار
# ═══════════════════════════════════════════════════════════

def bank_callback_handler(update: Update, context: CallbackContext):
    """معالج أزرار البنك"""
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    # أزرار المتجر
    if data.startswith("shop_"):
        category = data.replace("shop_", "")
        if category in SHOP:
            items_text = f"🛒 *متجر {category}*\n\n"
            for item_name, item_data in list(SHOP[category].items())[:20]:  # أول 20 منتج
                display_name = item_name.replace("_", " ")
                income_text = f" (+{item_data['income']}/يوم)" if item_data['income'] > 0 else ""
                items_text += f"{item_data['emoji']} {display_name}: {format_number(item_data['price'])} د.ل{income_text}\n"
            
            items_text += f"\n📝 للشراء: `/شراء اسم_المنتج`"
            
            query.message.edit_text(items_text, parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return
    
    # قبول الخطوبة
    if data.startswith("accept_proposal_"):
        from_id = int(data.replace("accept_proposal_", ""))
        success, msg = accept_proposal(user.id, from_id)
        query.message.edit_text(f"{'💕' if success else '❌'} {msg}")
        query.answer()
        return
    
    # رفض الخطوبة
    if data.startswith("reject_proposal_"):
        from_id = int(data.replace("reject_proposal_", ""))
        success, msg = reject_proposal(user.id, from_id)
        query.message.edit_text(f"{'💔' if success else '❌'} {msg}")
        query.answer()
        return
    
    # تأكيد تصفير الكل
    if data == "confirm_reset_all":
        if user.id != OWNER_ID:
            query.answer("⛔ للمطور فقط!", show_alert=True)
            return
        
        bank_data = get_bank_data()
        for user_id in bank_data:
            bank_data[user_id]['balance'] = 0
        save_bank_data(bank_data)
        
        query.message.edit_text("✅ تم تصفير جميع الأرصدة!")
        query.answer()
        return
    
    # إلغاء التصفير
    if data == "cancel_reset_all":
        query.message.edit_text("❌ تم الإلغاء")
        query.answer()
        return
    
    query.answer()


# ═══════════════════════════════════════════════════════════
# ⚙️ تسجيل الأوامر
# ═══════════════════════════════════════════════════════════

# اسم الموديول
__mod_name__ = "البنك 🏦"

# المساعدة
__help__ = """
🏦 *نظام البنك الليبي*

💳 الحساب: `/حساب` `/رصيدي` `/يومي`
🛒 المتجر: `/متجر` `/شراء` `/بيع`
💸 التحويل: `/تحويل @user مبلغ`
🎁 الإهداء: `/اهداء @user هدية`
🔫 السرقة: `/سرقة` `/حماية`
💍 الزواج: `/خطوبة` `/زواج` `/طلاق`
💼 الوظائف: `/وظائف` `/توظف` `/راتب`
🏦 القروض: `/قرض` `/سداد`
🎰 الألعاب: `/نرد` `/سلوتس` `/عجلة`
📊 الترتيب: `/الاغنياء` `/السارقين`

📚 `/مساعدة_البنك` - كل الأوامر
"""

# تسجيل الهاندلرز
def register_handlers(dp):
    """تسجيل كل الأوامر"""
    
    # الحساب
    dp.add_handler(CommandHandler(["حساب", "account", "انشاء_حساب"], cmd_create_account))
    dp.add_handler(CommandHandler(["رصيدي", "فلوسي", "balance", "bal", "رصيد"], cmd_balance))
    dp.add_handler(CommandHandler(["حسابي", "معلوماتي", "myaccount"], cmd_account_info))
    dp.add_handler(CommandHandler(["يومي", "daily", "مكافأة", "مكافئة", "المكافأة"], cmd_daily))
    
    # التحويل
    dp.add_handler(CommandHandler(["تحويل", "حول", "transfer", "send"], cmd_transfer))
    
    # المتجر
    dp.add_handler(CommandHandler(["متجر", "المتجر", "shop", "store", "سوق"], cmd_shop))
    dp.add_handler(CommandHandler(["شراء", "اشتري", "buy"], cmd_buy))
    dp.add_handler(CommandHandler(["بيع", "sell"], cmd_sell))
    dp.add_handler(CommandHandler(["ممتلكاتي", "ممتلكات", "myitems", "items", "اغراضي"], cmd_my_items))
    
    # الإهداء
    dp.add_handler(CommandHandler(["اهداء", "هدية", "gift", "اهدي"], cmd_gift))
    
    # السرقة
    dp.add_handler(CommandHandler(["سرقة", "اسرق", "steal", "rob"], cmd_steal))
    dp.add_handler(CommandHandler(["حماية", "protection", "protect", "درع"], cmd_protection))
    
    # الزواج
    dp.add_handler(CommandHandler(["خطوبة", "خطب", "propose", "اخطب"], cmd_propose))
    dp.add_handler(CommandHandler(["زواج", "تزوج", "marry", "اتزوج"], cmd_marry))
    dp.add_handler(CommandHandler(["طلاق", "divorce", "طلق"], cmd_divorce))
    dp.add_handler(CommandHandler(["شريكي", "زوجي", "زوجتي", "partner"], cmd_partner))
    
    # الوظائف
    dp.add_handler(CommandHandler(["وظائف", "الوظائف", "jobs", "شغل"], cmd_jobs))
    dp.add_handler(CommandHandler(["راتب", "اشتغل", "work", "salary"], cmd_work))
    dp.add_handler(CommandHandler(["توظف", "hire", "job"], cmd_hire))
    dp.add_handler(CommandHandler(["استقالة", "resign", "quit"], cmd_resign))
    
    # القروض
    dp.add_handler(CommandHandler(["قرض", "loan", "قروض"], cmd_loan))
    dp.add_handler(CommandHandler(["سداد", "pay", "ادفع"], cmd_pay_loan))
    dp.add_handler(CommandHandler(["ديوني", "ديون", "debt", "myloan"], cmd_my_loan))
    
    # الألعاب
    dp.add_handler(CommandHandler(["نرد", "dice", "زهر"], cmd_dice))
    dp.add_handler(CommandHandler(["سلوتس", "slots", "slot"], cmd_slots))
    dp.add_handler(CommandHandler(["ورقة", "coin", "coinflip", "عملة"], cmd_coinflip))
    dp.add_handler(CommandHandler(["تخمين", "خمن", "guess"], cmd_guess))
    dp.add_handler(CommandHandler(["عجلة", "wheel", "عجلة_الحظ"], cmd_wheel))
    
    # الترتيب
    dp.add_handler(CommandHandler(["الاغنياء", "اغنياء", "top", "rich", "توب"], cmd_top))
    dp.add_handler(CommandHandler(["السارقين", "سارقين", "topthieves", "thieves"], cmd_top_thieves))
    dp.add_handler(CommandHandler(["الكرماء", "كرماء", "generous"], cmd_top_generous))
    
    # الوقت
    dp.add_handler(CommandHandler(["الوقت", "وقت", "time", "توقيت"], cmd_time))
    
    # المساعدة
    dp.add_handler(CommandHandler(["مساعدة_البنك", "bankhelp", "bank"], cmd_bank_help))
    
    # أوامر المطور والمالك
    dp.add_handler(CommandHandler(["اضافة_رصيد", "addbal", "اضف_رصيد"], cmd_add_balance))
    dp.add_handler(CommandHandler(["خصم_رصيد", "removebal", "خصم"], cmd_remove_balance))
    dp.add_handler(CommandHandler(["تصفير", "reset", "صفر"], cmd_reset_balance))
    dp.add_handler(CommandHandler(["تصفير_الكل", "resetall"], cmd_reset_all))
    dp.add_handler(CommandHandler(["تعيين_مالك", "addsudo"], cmd_add_sudo))
    dp.add_handler(CommandHandler(["ازالة_مالك", "removesudo"], cmd_remove_sudo))
    dp.add_handler(CommandHandler(["تعيين_مميز", "addvip"], cmd_add_vip))
    dp.add_handler(CommandHandler(["ازالة_مميز", "removevip"], cmd_remove_vip))
    dp.add_handler(CommandHandler(["اعطاء", "give", "اعطي"], cmd_give_item))
    dp.add_handler(CommandHandler(["احصائيات_البنك", "bankstats"], cmd_bank_stats))
    
    # معالج الأزرار
    dp.add_handler(CallbackQueryHandler(bank_callback_handler, pattern=r"^(shop_|accept_proposal_|reject_proposal_|confirm_reset_all|cancel_reset_all)"))


# تسجيل الأوامر عند تحميل الموديول
register_handlers(dispatcher)
