"""
قاموس الأوامر العربية 🇱🇾
كل أمر إنجليزي ← مقابله بالعربي
"""

COMMANDS_MAP = {
    "start": "ابدا",
    "help": "مساعدة",
    "settings": "اعدادات",
    "admin": "ادمن",
    "admins": "الادمنية",
    "promote": "ترقية",
    "demote": "تنزيل",
    "pin": "تثبيت",
    "unpin": "الغاء_التثبيت",
    "invitelink": "رابط_الدعوة",
    "title": "لقب",
    "ban": "حظر",
    "unban": "رفع_الحظر",
    "tban": "حظر_مؤقت",
    "kick": "طرد",
    "mute": "كتم",
    "unmute": "رفع_الكتم",
    "tmute": "كتم_مؤقت",
    "blacklist": "القائمة_السوداء",
    "addblacklist": "اضف_اسود",
    "unblacklist": "حذف_اسود",
    "blacklistmode": "وضع_الاسود",
    "warn": "تحذير",
    "warns": "التحذيرات",
    "resetwarn": "مسح_تحذير",
    "resetwarns": "مسح_التحذيرات",
    "warnlimit": "حد_التحذيرات",
    "warnmode": "وضع_التحذير",
    "get": "جلب",
    "save": "حفظ",
    "clear": "مسح",
    "notes": "الملاحظات",
    "saved": "المحفوظات",
    "welcome": "ترحيب",
    "setwelcome": "ضبط_ترحيب",
    "resetwelcome": "اعادة_ترحيب",
    "goodbye": "وداع",
    "setgoodbye": "ضبط_وداع",
    "cleanwelcome": "تنظيف_ترحيب",
    "lock": "قفل",
    "unlock": "فتح",
    "locks": "الاقفال",
    "locktypes": "انواع_القفل",
    "lockdown": "اغلاق",
    "unlockdown": "فتح_الاغلاق",
    "purge": "تطهير",
    "del": "حذف",
    "filter": "فلتر",
    "filters": "الفلاتر",
    "stop": "ايقاف",
    "rules": "القوانين",
    "setrules": "ضبط_القوانين",
    "antiflood": "ضد_الفلود",
    "setflood": "ضبط_الفلود",
    "info": "معلومات",
    "id": "الايدي",
    "afk": "مشغول",
    "approve": "موافقة",
    "disapprove": "رفض_الموافقة",
    "tr": "ترجمة",
    "tts": "صوت",
    "weather": "الطقس",
    "wiki": "ويكي",
    "ud": "قاموس",
    "currency": "عملة",
    "fun": "مرح",
    "sticker": "ملصق",
    "kang": "سرقة",
    "bank": "البنك",
    "balance": "رصيدي",
    "daily": "اليومي",
    "transfer": "تحويل",
    "shop": "المتجر",
    "dice": "نرد",
    "luck": "حظي",
    "bet": "رهان",
    "rob": "سرقة_بنك",
    "top": "الترتيب",
    "leaderboard": "المتصدرين",
    "connect": "اتصال",
    "disconnect": "قطع_الاتصال",
    "connection": "الاتصال",
    "lang": "اللغة",
    "setlang": "ضبط_اللغة",
    "backup": "نسخة",
    "import": "استيراد",
    "export": "تصدير",
    "announce": "اعلان",
    "debug": "تصحيح",
    "eval": "تنفيذ",
    "sh": "شل",
    "yt": "يوتيوب",
    "ytdl": "تحميل_يوتيوب",
    "magisk": "ماجسك",
    "device": "جهاز",
    "twrp": "ريكفري",
    "github": "قيت",
    "repo": "مستودع",
}

REVERSE_MAP = {v: k for k, v in COMMANDS_MAP.items()}


def get_arabic(english_cmd):
    return COMMANDS_MAP.get(english_cmd, english_cmd)


def get_english(arabic_cmd):
    return REVERSE_MAP.get(arabic_cmd, arabic_cmd)


def get_both(english_cmd):
    arabic = COMMANDS_MAP.get(english_cmd)
    if arabic:
        return [english_cmd, arabic]
    return [english_cmd]
