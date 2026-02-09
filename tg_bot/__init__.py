import logging
import os
import sys
import time
from typing import List
import spamwatch
import telegram.ext as tg
from telegram.ext import Dispatcher, JobQueue, Updater
from telethon import TelegramClient
from telethon.sessions import MemorySession
from configparser import ConfigParser
from functools import wraps
from SibylSystem import PsychoPass

try:
    os.system(os.environ['convert_config'])
    from .config import config_vars
except (ModuleNotFoundError, KeyError):
    config_vars = None

StartTime = time.time()


def get_user_list(key):
    from tg_bot.modules.sql import nation_sql
    royals = nation_sql.get_royals(key)
    return [a.user_id for a in royals]


# ═══════════════════════════════════════════════════════════
# setup loggers
# ═══════════════════════════════════════════════════════════

file_formatter = logging.Formatter('%(asctime)s - %(levelname)s -- < - %(name)s - > -- %(message)s')
stream_formatter = logging.Formatter('< - %(name)s - > -- %(message)s')

file_handler = logging.FileHandler('logs.txt', 'w', encoding='utf-8')
debug_handler = logging.FileHandler('debug.log', 'w', encoding='utf-8')
stream_handler = logging.StreamHandler()

file_handler.setFormatter(file_formatter)
stream_handler.setFormatter(stream_formatter)
debug_handler.setFormatter(file_formatter)

file_handler.setLevel(logging.INFO)
stream_handler.setLevel(logging.WARNING)
debug_handler.setLevel(logging.DEBUG)

logging.basicConfig(handlers=[file_handler, stream_handler, debug_handler], level=logging.DEBUG)
log = logging.getLogger('[زورو]')

log.info("زورو بوت يشتغل... | البوت من تطوير: @MGlibya03")

if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    log.error("لازم يكون عندك بايثون 3.7 او اعلى! البوت بيقفل.")
    quit(1)

from collections import ChainMap


class ConfigParserCustom(ConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _unify_values(self, section, vars):
        if not config_vars:
            return super()._unify_values(section, vars)
        log.debug("Using the supplied config vars!")
        var_dict = {
            self.optionxform(
                key.split(str(section).upper() + "__")[1].lower()
            ): value
            for key, value in config_vars.items()
            if value is not None
            and str(key).startswith(str(section).upper() + "__")
        }
        return ChainMap(var_dict, {}, self._defaults)


parser = ConfigParserCustom()

# ═══════════════════════════════════════════════════════════
# قراءة config.ini لو موجود، ولو مش موجود نستخدم env vars
# ═══════════════════════════════════════════════════════════

config_file_exists = os.path.exists("config.ini")
if config_file_exists:
    parser.read("config.ini")
    log.info("تم قراءة config.ini")
else:
    log.info("config.ini مش موجود - نستخدم متغيرات البيئة")


class KigyoINIT:
    def __init__(self, parser, use_env=False):
        self.parser = parser
        self.use_env = use_env

    def _get(self, key, default=None):
        """جلب القيمة من config.ini أو من البيئة"""
        if self.use_env:
            return os.environ.get(key.upper(), os.environ.get(key, default))
        else:
            try:
                return self.parser.get(key, default)
            except:
                return os.environ.get(key.upper(), os.environ.get(key, default))

    def _getint(self, key, default=0):
        """جلب قيمة رقمية"""
        val = self._get(key, default)
        try:
            return int(val)
        except (TypeError, ValueError):
            return int(default) if default else 0

    def _getbool(self, key, default=False):
        """جلب قيمة منطقية"""
        val = self._get(key, str(default))
        if isinstance(val, bool):
            return val
        return str(val).lower() in ('true', '1', 'yes', 'on')

    def load_config(self):
        self.SYS_ADMIN = self._getint('SYS_ADMIN', 0)
        self.OWNER_ID = self._getint('OWNER_ID', 0)
        self.OWNER_USERNAME = self._get('OWNER_USERNAME', "0")
        self.APP_ID = self._getint('APP_ID', 0)
        self.API_HASH = self._get('API_HASH', '')
        self.WEBHOOK = self._getbool('WEBHOOK', False)
        self.URL = self._get('URL', None)
        self.CERT_PATH = self._get('CERT_PATH', None)
        self.PORT = self._getint('PORT', 8443)
        self.INFOPIC = self._getbool('INFOPIC', False)
        self.DEL_CMDS = self._getbool('DEL_CMDS', False)
        self.STRICT_GBAN = self._getbool('STRICT_GBAN', False)
        self.ALLOW_EXCL = self._getbool('ALLOW_EXCL', False)
        self.CUSTOM_CMD = ['/', '!', '>']
        self.BAN_STICKER = self._get('BAN_STICKER', None)
        self.TOKEN = self._get('TOKEN', '')
        self.DB_URI = self._get('SQLALCHEMY_DATABASE_URI', self._get('DATABASE_URL', ''))
        
        load_str = self._get('LOAD', '')
        self.LOAD = load_str.split() if load_str else []
        
        self.MESSAGE_DUMP = self._getint('MESSAGE_DUMP', 0) or None
        self.GBAN_LOGS = self._getint('GBAN_LOGS', 0) or None
        
        no_load_str = self._get('NO_LOAD', '')
        self.NO_LOAD = no_load_str.split() if no_load_str else []
        
        self.spamwatch_api = self._get('spamwatch_api', self._get('SPAMWATCH_API', None))
        self.CASH_API_KEY = self._get('CASH_API_KEY', None)
        self.TIME_API_KEY = self._get('TIME_API_KEY', None)
        self.WALL_API = self._get('WALL_API', None)
        self.LASTFM_API_KEY = self._get('LASTFM_API_KEY', None)
        self.WEATHER_API = self._get('WEATHER_API', None)
        self.CF_API_KEY = self._get('CF_API_KEY', None)
        self.bot_id = 0

        # ═══════════════════════════════════════
        # اسم البوت
        # ═══════════════════════════════════════
        self.bot_name = "زورو 🤖"
        self.bot_username = "ZoroRobot"

        # ═══════════════════════════════════════
        # الاشتراك الاجباري
        # ═══════════════════════════════════════
        self.FORCE_SUB_CHANNEL = self._get('FORCE_SUB_CHANNEL', None)

        self.DEBUG = self._getbool('IS_DEBUG', False)
        self.DROP_UPDATES = self._getbool('DROP_UPDATES', True)
        self.BOT_API_URL = self._get('BOT_API_URL', 'https://api.telegram.org/bot')
        self.BOT_API_FILE_URL = self._get('BOT_API_FILE_URL', 'https://api.telegram.org/file/bot')

        self.ALLOW_CHATS = self._getbool('ALLOW_CHATS', True)
        self.SUPPORT_GROUP = self._get('SUPPORT_GROUP', '0')
        self.IS_DEBUG = self._getbool('IS_DEBUG', False)
        self.ANTISPAM_TOGGLE = self._getbool('ANTISPAM_TOGGLE', True)
        
        gb_str = self._get('GROUP_BLACKLIST', '')
        self.GROUP_BLACKLIST = gb_str.split() if gb_str else []
        
        self.GLOBALANNOUNCE = self._getbool('GLOBALANNOUNCE', False)
        self.BACKUP_PASS = self._get('BACKUP_PASS', None)
        self.SIBYL_KEY = self._get('SIBYL_KEY', None)
        self.SIBYL_ENDPOINT = self._get('SIBYL_ENDPOINT', 'https://psychopass.kaizoku.cyou')

        return self

    def init_sw(self):
        if self.spamwatch_api is None:
            log.warning("SpamWatch API key is missing!")
            return None
        else:
            try:
                sw = spamwatch.Client(self.spamwatch_api)
                return sw
            except:
                sw = None
                log.warning("Can't connect to SpamWatch!")
                return sw


# ═══════════════════════════════════════════════════════════
# تحميل الإعدادات
# ═══════════════════════════════════════════════════════════

if config_file_exists:
    try:
        kigconfig = parser["kigconfig"]
        KInit = KigyoINIT(parser=kigconfig, use_env=False).load_config()
    except KeyError:
        log.info("kigconfig section مش موجود في config.ini - نستخدم env vars")
        KInit = KigyoINIT(parser=None, use_env=True).load_config()
else:
    KInit = KigyoINIT(parser=None, use_env=True).load_config()


# ═══════════════════════════════════════════════════════════
# تصدير المتغيرات
# ═══════════════════════════════════════════════════════════

OWNER_ID = KInit.OWNER_ID
OWNER_USERNAME = KInit.OWNER_USERNAME
APP_ID = KInit.APP_ID
API_HASH = KInit.API_HASH
WEBHOOK = KInit.WEBHOOK
URL = KInit.URL
CERT_PATH = KInit.CERT_PATH
PORT = KInit.PORT
INFOPIC = KInit.INFOPIC
DEL_CMDS = KInit.DEL_CMDS
ALLOW_EXCL = KInit.ALLOW_EXCL
CUSTOM_CMD = KInit.CUSTOM_CMD
BAN_STICKER = KInit.BAN_STICKER
TOKEN = KInit.TOKEN
DB_URI = KInit.DB_URI
LOAD = KInit.LOAD
MESSAGE_DUMP = KInit.MESSAGE_DUMP
GBAN_LOGS = KInit.GBAN_LOGS
NO_LOAD = KInit.NO_LOAD
OWNER_USER = [OWNER_ID]
SYS_ADMIN = KInit.SYS_ADMIN
MOD_USERS = [OWNER_ID] + [SYS_ADMIN] + get_user_list("mods")
SUDO_USERS = [OWNER_ID] + [SYS_ADMIN] + get_user_list("sudos")
DEV_USERS = [OWNER_ID] + [SYS_ADMIN] + get_user_list("devs")
SUPPORT_USERS = get_user_list("supports")
WHITELIST_USERS = get_user_list("whitelists")
SPAMMERS = get_user_list("spammers")
spamwatch_api = KInit.spamwatch_api
CASH_API_KEY = KInit.CASH_API_KEY
TIME_API_KEY = KInit.TIME_API_KEY
LASTFM_API_KEY = KInit.LASTFM_API_KEY
WEATHER_API = KInit.WEATHER_API
CF_API_KEY = KInit.CF_API_KEY
ALLOW_CHATS = KInit.ALLOW_CHATS
SUPPORT_GROUP = KInit.SUPPORT_GROUP
IS_DEBUG = KInit.IS_DEBUG
GROUP_BLACKLIST = KInit.GROUP_BLACKLIST
ANTISPAM_TOGGLE = KInit.ANTISPAM_TOGGLE
bot_username = KInit.bot_username
bot_name = KInit.bot_name
GLOBALANNOUNCE = KInit.GLOBALANNOUNCE
BACKUP_PASS = KInit.BACKUP_PASS
SIBYL_KEY = KInit.SIBYL_KEY
SIBYL_ENDPOINT = KInit.SIBYL_ENDPOINT
BOT_ID = TOKEN.split(":")[0] if TOKEN else "0"

# ═══════════════════════════════════════
# الاشتراك الاجباري
# ═══════════════════════════════════════
FORCE_SUB_CHANNEL = KInit.FORCE_SUB_CHANNEL

if IS_DEBUG:
    log.debug("Debug mode is on")
    stream_handler.setLevel(logging.DEBUG)


# ═══════════════════════════════════════════════════════════
# Sibyl System
# ═══════════════════════════════════════════════════════════

sibylClient = None

if SIBYL_KEY:
    try:
        sibylClient = PsychoPass(SIBYL_KEY, show_license=False, host=SIBYL_ENDPOINT)
        log.info("Connected to Sibyl System")
    except Exception as e:
        sibylClient = None
        log.warning(f"Failed to load SibylSystem: {e}")

try:
    IS_DEBUG = IS_DEBUG
except AttributeError:
    IS_DEBUG = False

try:
    ANTISPAM_TOGGLE = ANTISPAM_TOGGLE
except AttributeError:
    ANTISPAM_TOGGLE = True

# SpamWatch
sw = KInit.init_sw()


# ═══════════════════════════════════════════════════════════
# Database Session
# ═══════════════════════════════════════════════════════════

from tg_bot.modules.sql import SESSION


# ═══════════════════════════════════════════════════════════
# Updater & Dispatcher
# ═══════════════════════════════════════════════════════════

updater = tg.Updater(
    token=TOKEN,
    base_url=KInit.BOT_API_URL,
    base_file_url=KInit.BOT_API_FILE_URL,
    workers=min(32, os.cpu_count() + 4),
    request_kwargs={"read_timeout": 10, "connect_timeout": 10}
)

telethn = TelegramClient(MemorySession(), APP_ID, API_HASH)
dispatcher = updater.dispatcher
j = updater.job_queue


# ═══════════════════════════════════════════════════════════
# Load CustomCommandHandler
# ═══════════════════════════════════════════════════════════

from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


# ═══════════════════════════════════════════════════════════
# AntiSpam Module
# ═══════════════════════════════════════════════════════════

try:
    from tg_bot.antispam import antispam_restrict_user, antispam_cek_user, detect_user
    log.info("AntiSpam loaded!")
    antispam_module = True
except ModuleNotFoundError:
    antispam_module = False


# ═══════════════════════════════════════════════════════════
# دوال الاشتراك الاجباري
# ═══════════════════════════════════════════════════════════

def check_force_sub(bot, user_id):
    """فحص اذا المستخدم مشترك في القناة"""
    if not FORCE_SUB_CHANNEL:
        return True
    if user_id == OWNER_ID:
        return True
    if user_id in SUDO_USERS:
        return True
    try:
        member = bot.get_chat_member(f"@{FORCE_SUB_CHANNEL}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        log.warning(f"Force sub check error: {e}")
        return True


def force_sub_message():
    """رسالة الاشتراك الاجباري"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
        [InlineKeyboardButton("✅ اشتركت", callback_data="check_force_sub")]
    ])
    text = f"""⚠️ *يجب الاشتراك في قناة المطور اولا!*

📢 @{FORCE_SUB_CHANNEL}

✅ بعد الاشتراك اضغط "اشتركت" """
    return text, keyboard


# ═══════════════════════════════════════════════════════════
# SpamCheck Decorator
# ═══════════════════════════════════════════════════════════

def spamcheck(func):
    @wraps(func)
    def check_user(update, context, *args, **kwargs):
        try:
            chat = update.effective_chat
            user = update.effective_message.sender_chat or update.effective_user
            message = update.effective_message
        except AttributeError:
            return

        if IS_DEBUG:
            print("{} | {} | {} | {}".format(
                message.text or message.caption, user.id, message.chat.title, chat.id
            ))

        if user.id == context.bot.id:
            return False
        elif user.id == "777000":
            return False
        elif FORCE_SUB_CHANNEL and not check_force_sub(context.bot, user.id):
            text, keyboard = force_sub_message()
            try:
                message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
            except:
                pass
            return False
        elif antispam_module and ANTISPAM_TOGGLE:
            parsing_date = time.mktime(message.date.timetuple())
            if detect_user(user.id, chat.id, message, parsing_date):
                return False
            antispam_restrict_user(user.id, parsing_date)
        elif int(user.id) in SPAMMERS:
            return False
        elif str(chat.id) in GROUP_BLACKLIST:
            dispatcher.bot.sendMessage(chat.id, "هالقروب في القائمة السوداء، باي...")
            dispatcher.bot.leaveChat(chat.id)
            return False

        return func(update, context, *args, **kwargs)

    return check_user
