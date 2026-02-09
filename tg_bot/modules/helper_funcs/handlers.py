import telegram.ext as tg
from telegram import Update
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from tg_bot import DEV_USERS, MOD_USERS, OWNER_ID, SUDO_USERS, SYS_ADMIN, WHITELIST_USERS, SUPPORT_USERS
from pyrate_limiter import (
    BucketFullException,
    Duration,
    RequestRate,
    Limiter,
    MemoryListBucket,
)
import tg_bot.modules.sql.blacklistusers_sql as sql

try:
    from tg_bot import CUSTOM_CMD
except:
    CUSTOM_CMD = False

if CUSTOM_CMD and isinstance(CUSTOM_CMD, (list, tuple)) and len(CUSTOM_CMD) > 0:
    CMD_STARTERS = list(CUSTOM_CMD)
else:
    CMD_STARTERS = ["/", "!", ">"]


# ═══════════════════════════════════════════════════════════
# قائمة كل الأوامر العربية - للتعرف عليها بدون رمز
# ═══════════════════════════════════════════════════════════

ALL_ARABIC_WORDS = set()

def _build_arabic_words():
    """يبني قائمة كل الكلمات العربية المسجلة كأوامر"""
    try:
        from tg_bot.modules.helper_funcs.decorators import ARABIC_COMMANDS
        for eng_cmd, ar_list in ARABIC_COMMANDS.items():
            for ar_word in ar_list:
                ALL_ARABIC_WORDS.add(ar_word.lower())
    except ImportError:
        pass

# نبني القائمة لاحقاً عند أول استخدام
_arabic_built = False


def _ensure_string_list(command):
    """
    يحول اي نوع (str, list, tuple, متداخلة) الى list of strings
    """
    result = []

    if isinstance(command, str):
        result.append(command.lower())
    elif isinstance(command, (list, tuple)):
        for item in command:
            if isinstance(item, str):
                result.append(item.lower())
            elif isinstance(item, (list, tuple)):
                for sub_item in item:
                    if isinstance(sub_item, str):
                        result.append(sub_item.lower())
                    else:
                        result.append(str(sub_item).lower())
            else:
                result.append(str(item).lower())
    else:
        result.append(str(command).lower())

    return result


def _is_arabic_text(text):
    """يتحقق اذا النص يحتوي على حروف عربية"""
    if not text:
        return False
    for char in text:
        if '\u0600' <= char <= '\u06FF':
            return True
        if '\u0750' <= char <= '\u077F':
            return True
        if '\uFB50' <= char <= '\uFDFF':
            return True
        if '\uFE70' <= char <= '\uFEFF':
            return True
    return False


class AntiSpam:
    def __init__(self):
        self.whitelist = (
            (DEV_USERS or [])
            + (SUDO_USERS or [])
            + (WHITELIST_USERS or [])
            + (SUPPORT_USERS or [])
            + (MOD_USERS or [])
        )
        Duration.CUSTOM = 15
        self.sec_limit = RequestRate(6, Duration.CUSTOM)
        self.min_limit = RequestRate(20, Duration.MINUTE)
        self.hour_limit = RequestRate(100, Duration.HOUR)
        self.daily_limit = RequestRate(1000, Duration.DAY)
        self.limiter = Limiter(
            self.sec_limit,
            self.min_limit,
            self.hour_limit,
            self.daily_limit,
            bucket_class=MemoryListBucket,
        )

    @staticmethod
    def check_user(user):
        return bool(sql.is_user_blacklisted(user))


SpamChecker = AntiSpam()
MessageHandlerChecker = AntiSpam()


class CustomCommandHandler(tg.Handler):
    """
    معالج أوامر مخصص يدعم:
    1. الأوامر بالرموز: /ban !حظر >kick
    2. الأوامر العربية بدون رمز: حظر، طرد، كتم
    """
    def __init__(self, command, callback, run_async=True, **kwargs):
        super().__init__(callback, run_async=run_async)

        self.command = _ensure_string_list(command)

        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]

        self.filters = kwargs.get('filters', Filters.all)

        # نحدد الأوامر العربية من ضمن أوامر هالهاندلر
        self.arabic_commands = set()
        for cmd in self.command:
            if _is_arabic_text(cmd):
                self.arabic_commands.add(cmd)

    def check_update(self, update):
        if not isinstance(update, Update) or not update.effective_message:
            return None

        message = update.effective_message

        try:
            user_id = update.effective_user.id
        except:
            user_id = None

        if not message.text or len(message.text) < 1:
            return None

        text = message.text.strip()
        if not text:
            return None

        fst_word = text.split(None, 1)[0]

        if len(fst_word) < 1:
            return None

        # ═══════════════════════════════════════
        # الطريقة 1: أمر برمز (/ أو ! أو >)
        # ═══════════════════════════════════════
        if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
            args = text.split()[1:]
            command_text = fst_word[1:]
            command_parts = command_text.split("@")
            cmd_name = command_parts[0].lower()

            # تحقق من اسم البوت لو موجود
            if len(command_parts) > 1:
                if command_parts[1].lower() != message.bot.username.lower():
                    return None

            if cmd_name not in self.command:
                return None

            if SpamChecker.check_user(user_id):
                return None

            if callable(self.filters):
                filter_result = self.filters(update)
            else:
                filter_result = True

            if filter_result:
                return args, filter_result
            else:
                return False

        # ═══════════════════════════════════════
        # الطريقة 2: أمر عربي بدون رمز
        # ═══════════════════════════════════════
        if self.arabic_commands:
            cmd_word = fst_word.lower()

            # ازالة @ لو موجودة
            if "@" in cmd_word:
                parts = cmd_word.split("@")
                cmd_word = parts[0]
                if len(parts) > 1 and parts[1].lower() != message.bot.username.lower():
                    return None

            if cmd_word in self.arabic_commands:
                args = text.split()[1:]

                if SpamChecker.check_user(user_id):
                    return None

                if callable(self.filters):
                    filter_result = self.filters(update)
                else:
                    filter_result = True

                if filter_result:
                    return args, filter_result
                else:
                    return False

        return None


class CustomMessageHandler(MessageHandler):
    def __init__(self, pattern, callback, run_async=True, friendly="", **kwargs):
        super().__init__(pattern, callback, run_async=run_async, **kwargs)
        self.friendly = friendly or pattern

    def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            try:
                user_id = update.effective_user.id
            except:
                user_id = None

            if self.filters(update):
                if SpamChecker.check_user(user_id):
                    return None
                return True
            return False


CommandHandler = CustomCommandHandler
