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


def _ensure_string_list(command):
    """
    يحول اي نوع (str, list, tuple, متداخلة) الى list of strings
    يمنع خطأ 'tuple' object has no attribute 'lower'
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
    معالج أوامر مخصص يدعم العربي والإنجليزي
    يقبل str, list, tuple بدون أخطاء
    """
    def __init__(self, command, callback, run_async=True, **kwargs):
        super().__init__(callback, run_async=run_async)

        self.command = _ensure_string_list(command)

        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]

        self.filters = kwargs.get('filters', Filters.all)

    def check_update(self, update):
        if not isinstance(update, Update) or not update.effective_message:
            return None

        message = update.effective_message

        try:
            user_id = update.effective_user.id
        except:
            user_id = None

        if message.text and len(message.text) > 1:
            fst_word = message.text.split(None, 1)[0]

            if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                args = message.text.split()[1:]
                command = fst_word[1:].split("@")
                command.append(message.bot.username)

                if not (
                    command[0].lower() in self.command
                    and command[1].lower() == message.bot.username.lower()
                ):
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
