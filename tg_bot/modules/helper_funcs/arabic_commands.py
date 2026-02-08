"""
قاموس الأوامر العربية
كل أمر إنجليزي ← مقابله بالعربي
"""

# ——————————————————————————————————————
#  القاموس الرئيسي: إنجليزي ← عربي
# ——————————————————————————————————————

COMMANDS_MAP = {
    # ——— أساسي ———
    "start":        "ابدا",
    "help":         "مساعدة",
    "settings":     "اعدادات",

    # ——— إدارة ———
    "admin":        "ادمن",
    "admins":       "الادمنية",
    "promote":      "ترقية",
    "demote":       "تنزيل",
    "pin":          "تثبيت",
    "unpin":        "الغاء_التثبيت",
    "invitelink":   "رابط_الدعوة",
    "title":        "لقب",

    # ——— حظر وكتم ———
    "ban":          "حظر",
    "unban":        "رفع_الحظر",
    "tban":         "حظر_مؤقت",
    "kick":         "طرد",
    "mute":         "كتم",
    "unmute":       "رفع_الكتم",
    "tmute":        "كتم_مؤقت",

    # ——— قائمة سوداء ———
    "blacklist":        "القائمة_السوداء",
    "addblacklist":     "اضف_اسود",
    "unblacklist":      "حذف_اسود",
    "blacklistmode":    "وضع_الاسود",

    # ——— تحذيرات ———
    "warn":         "تحذير",
    "warns":        "التحذيرات",
    "resetwarn":    "مسح_تحذير",
    "resetwarns":   "مسح_التحذيرات",
    "warnlimit":    "حد_التحذيرات",
    "warnmode":     "وضع_التحذير",

    # ——— ملاحظات ———
    "get":          "جلب",
    "save":         "حفظ",
    "clear":        "مسح",
    "notes":        "الملاحظات",
    "saved":        "المحفوظات",

    # ——— ترحيب ———
    "welcome":      "ترحيب",
    "setwelcome":   "ضبط_ترحيب",
    "resetwelcome": "اعادة_ترحيب",
    "goodbye":      "وداع",
    "setgoodbye":   "ضبط_وداع",
    "cleanwelcome": "تنظيف_ترحيب",

    # ——— أقفال ———
    "lock":         "قفل",
    "unlock":       "فتح",
    "locks":        "الاقفال",
    "locktypes":    "انواع_القفل",
    "lockdown":     "اغلاق",
    "unlockdown":   "فتح_الاغلاق",

    # ——— تنظيف ———
    "purge":        "تطهير",
    "del":          "حذف",

    # ——— فلاتر ———
    "filter":       "فلتر",
    "filters":      "الفلاتر",
    "stop":         "ايقاف",

    # ——— قوانين ———
    "rules":        "القوانين",
    "setrules":     "ضبط_القوانين",

    # ——— ضد السبام ———
    "antiflood":    "ضد_الفلود",
    "setflood":     "ضبط_الفلود",

    # ——— متفرقات ———
    "info":         "معلومات",
    "id":           "الايدي",
    "afk":          "مشغول",
    "approve":      "موافقة",
    "disapprove":   "رفض_الموافقة",

    # ——— أدوات ———
    "tr":           "ترجمة",
    "tts":          "صوت",
    "weather":      "الطقس",
    "wiki":         "ويكي",
    "ud":           "قاموس",
    "currency":     "عملة",

    # ——— ترفيه ———
    "fun":          "مرح",
    "sticker":      "ملصق",
    "kang":         "سرقة",

    # ——— البنك والألعاب ———
    "bank":         "البنك",
    "balance":      "رصيدي",
    "daily":        "اليومي",
    "transfer":     "تحويل",
    "shop":         "المتجر",
    "dice":         "نرد",
    "luck":         "حظي",
    "bet":          "رهان",
    "rob":          "سرقة_بنك",
    "top":          "الترتيب",
    "leaderboard":  "المتصدرين",

    # ——— اتصال ———
    "connect":      "اتصال",
    "disconnect":   "قطع_الاتصال",
    "connection":   "الاتصال",

    # ——— لغة ———
    "lang":         "اللغة",
    "setlang":      "ضبط_اللغة",

    # ——— نسخ احتياطي ———
    "backup":       "نسخة",
    "import":       "استيراد",
    "export":       "تصدير",

    # ——— إعلان ———
    "announce":     "اعلان",

    # ——— تصحيح ———
    "debug":        "تصحيح",
    "eval":         "تنفيذ",
    "sh":           "شل",

    # ——— يوتيوب ———
    "yt":           "يوتيوب",
    "ytdl":         "تحميل_يوتيوب",

    # ——— أندرويد ———
    "magisk":       "ماجسك",
    "device":       "جهاز",
    "twrp":         "ريكفري",

    # ——— GitHub ———
    "github":       "قيت",
    "repo":         "مستودع",
}


# ——————————————————————————————————————
#  القاموس العكسي: عربي ← إنجليزي
# ——————————————————————————————————————
REVERSE_MAP = {v: k for k, v in COMMANDS_MAP.items()}


def get_arabic(english_cmd: str) -> str:
    """يرجع الأمر العربي المقابل"""
    return COMMANDS_MAP.get(english_cmd, english_cmd)


def get_english(arabic_cmd: str) -> str:
    """يرجع الأمر الإنجليزي المقابل"""
    return REVERSE_MAP.get(arabic_cmd, arabic_cmd)


def get_both(english_cmd: str) -> list:
    """يرجع قائمة بالأمرين [إنجليزي، عربي]"""
    arabic = COMMANDS_MAP.get(english_cmd)
    if arabic:
        return [english_cmd, arabic]
    return [english_cmd]
