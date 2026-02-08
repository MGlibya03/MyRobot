import importlib
import re
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

from tg_bot import (
    dispatcher,
    updater,
    telethn,
    TOKEN,
    WEBHOOK,
    OWNER_ID,
    OWNER_USERNAME,
    PORT,
    URL,
    log,
    CERT_PATH,
    spamcheck,
)

try:
    from tg_bot import FORCE_SUB_CHANNEL, check_force_sub
except ImportError:
    FORCE_SUB_CHANNEL = None
    def check_force_sub(bot, user_id):
        return True

from tg_bot.modules import ALL_MODULES

try:
    from tg_bot.modules.helper_funcs.chat_status import is_user_admin
except ImportError:
    try:
        from tg_bot.modules.helper_funcs.admin_status import user_is_admin as is_user_admin
    except ImportError:
        def is_user_admin(chat, user_id):
            try:
                member = chat.get_member(user_id)
                return member.status in ['administrator', 'creator']
            except:
                return False

from tg_bot.modules.helper_funcs.misc import paginate_modules

# استيراد الـ CustomCommandHandler
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler


# ═══════════════════════════════════════════════════════════
# سيرفر HTTP
# ═══════════════════════════════════════════════════════════

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Zoro Bot Running!')
    def log_message(self, format, *args):
        pass

def start_server():
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), Handler)
        server.serve_forever()
    except:
        pass

try:
    threading.Thread(target=start_server, daemon=True).start()
except:
    pass


# ═══════════════════════════════════════════════════════════
# الرسائل
# ═══════════════════════════════════════════════════════════

PM_START_TEXT = """
🤖 *هلا والله! انا زورو*

✨ بوت إدارة القروبات الأقوى والأذكى!

👨‍💻 *المبرمج:* @{}

━━━━━━━━━━━━━━━━━━
📊 *احصائياتي:*
• {} مستخدم
• {} قروب
━━━━━━━━━━━━━━━━━━

🔥 *مميزاتي:*
✅ إدارة كاملة للقروبات
✅ حماية من السبام والفلود
✅ فلاتر وملاحظات ذكية
✅ ترحيب مخصص
✅ دعم كامل للعربي 🇱🇾

💡 اضغط *المساعدة* باش تعرف أوامري!
"""

HELP_STRINGS = """
🤖 *هلا بيك! انا زورو*

👨‍💻 *المبرمج:* @{}

✨ *اضغط على الأزرار باش تعرف الأوامر المتاحة:*
""".format(OWNER_USERNAME)


# ═══════════════════════════════════════════════════════════
# تحميل الموديولات
# ═══════════════════════════════════════════════════════════

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    try:
        imported_module = importlib.import_module("tg_bot.modules." + module_name)
        if not hasattr(imported_module, "__mod_name__"):
            imported_module.__mod_name__ = imported_module.__name__

        if imported_module.__mod_name__.lower() not in IMPORTED:
            IMPORTED[imported_module.__mod_name__.lower()] = imported_module

        if hasattr(imported_module, "__help__") and imported_module.__help__:
            HELPABLE[imported_module.__mod_name__.lower()] = imported_module

        if hasattr(imported_module, "__migrate__"):
            MIGRATEABLE.append(imported_module)

        if hasattr(imported_module, "__stats__"):
            STATS.append(imported_module)

        if hasattr(imported_module, "__user_info__"):
            USER_INFO.append(imported_module)

        if hasattr(imported_module, "__import_data__"):
            DATA_IMPORT.append(imported_module)

        if hasattr(imported_module, "__export_data__"):
            DATA_EXPORT.append(imported_module)

        if hasattr(imported_module, "__chat_settings__"):
            CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

        if hasattr(imported_module, "__user_settings__"):
            USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module
    except Exception as e:
        log.error(f"Error loading {module_name}: {e}")


# ═══════════════════════════════════════════════════════════
# الردود الذكية
# ═══════════════════════════════════════════════════════════

SMART_REPLIES = {
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🤍",
    "سلام": "وعليكم السلام يا طيب 💚",
    "الحمد لله": "الله يبارك فيك يا غالي 🤲",
    "الحمدلله": "ما شاء الله، ربي يديمها عليك 🤲",
    "صباح الخير": "صباح النور والسرور يا باهي 🌅",
    "مساء الخير": "مساء الورد والياسمين يا غالي 🌙",
    "كيفك": "والله تمام زي الفل، كيفك انت يا باهي؟ 😊",
    "كيف حالك": "الحمد لله باهي، انت كيفك يا غالي؟ 💚",
    "شكرا": "يعطيك الصحة يا غالي 💚",
    "مشكور": "العفو يا باهي 💚",
    "اهلا": "هلا والله نورت 💚",
    "مرحبا": "مرحبتين فيك يا غالي 🌟",
    "هاي": "هاي يا باهي 👋",
    "هلا": "هلا بيك يا زول 💚",
    "باي": "مع السلامة يا غالي 👋💚",
    "مع السلامة": "الله يسلمك، باي 👋",
    "بوت": "اسمي زورو مش بوت يا زول! 😏",
    "غبي": "غبي جدك! انا زورو الذكي 😎",
    "احبك": "وانا نحبك اكثر يا قلبي 💕",
    "نحبك": "وانا نحبك اكثر منك 💕",
    "وحشتني": "وانت والله وحشتني موت 💕",
    "زورو": "نعم؟ شن تبي يا غالي؟ 🤖💚",
    "يا زورو": "هلا، شن تبي؟ 🤖💚",
    "ههههه": "😂😂😂",
    "هههه": "😂😂",
    "ههه": "😂",
}


# ═══════════════════════════════════════════════════════════
# الدوال الأساسية
# ═══════════════════════════════════════════════════════════

def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


@spamcheck
def start(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    args = context.args

    if chat.type == "private":
        if args and len(args) >= 1:
            if args[0].lower() == "help":
                send_help(chat.id, HELP_STRINGS)
                return
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                if match:
                    try:
                        chat_obj = dispatcher.bot.getChat(match.group(1))
                        if is_user_admin(chat_obj, user.id):
                            send_settings(match.group(1), user.id, False)
                        else:
                            send_settings(match.group(1), user.id, True)
                    except:
                        pass
            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)
        else:
            try:
                from tg_bot.modules.sql import users_sql
                num_users = users_sql.num_users()
                num_chats = users_sql.num_chats()
            except:
                num_users = "مش معروف"
                num_chats = "مش معروف"

            start_buttons = [
                [InlineKeyboardButton(text="➕ ضيفني لقروبك", url=f"t.me/{bot.username}?startgroup=true")],
                [
                    InlineKeyboardButton(text="💡 المساعدة", callback_data="help_back"),
                    InlineKeyboardButton(text="ℹ️ معلوماتي", callback_data="zoro_about"),
                ],
                [InlineKeyboardButton(text="👨‍💻 المبرمج", url=f"t.me/{OWNER_USERNAME}")],
            ]

            if FORCE_SUB_CHANNEL:
                start_buttons.append([
                    InlineKeyboardButton(text="📢 قناة البوت", url=f"t.me/{FORCE_SUB_CHANNEL}")
                ])

            update.effective_message.reply_text(
                PM_START_TEXT.format(OWNER_USERNAME, num_users, num_chats),
                reply_markup=InlineKeyboardMarkup(start_buttons),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        update.effective_message.reply_text("هلا! انا زورو 🤖\nاكتب /help باش تعرف أوامري!")


def zoro_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    bot = context.bot

    if query.data == "zoro_about":
        about_text = """
🤖 *معلومات عن زورو* 🇱🇾

📛 *الاسم:* زورو بوت
👨‍💻 *المبرمج:* @{}
🔧 *الإصدار:* 2.0
📝 *اللغة:* Python 3

✨ *المميزات:*
• إدارة كاملة للقروبات
• حماية من السبام
• فلاتر ذكية
• ردود تلقائية ليبية
• دعم كامل للعربي

💚 شكراً لاستخدامك زورو!
        """.format(OWNER_USERNAME)

        query.message.edit_text(
            about_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🔙 رجوع", callback_data="zoro_back")]
            ])
        )

    elif query.data == "zoro_back":
        try:
            from tg_bot.modules.sql import users_sql
            num_users = users_sql.num_users()
            num_chats = users_sql.num_chats()
        except:
            num_users = "مش معروف"
            num_chats = "مش معروف"

        start_buttons = [
            [InlineKeyboardButton(text="➕ ضيفني لقروبك", url=f"t.me/{bot.username}?startgroup=true")],
            [
                InlineKeyboardButton(text="💡 المساعدة", callback_data="help_back"),
                InlineKeyboardButton(text="ℹ️ معلوماتي", callback_data="zoro_about"),
            ],
            [InlineKeyboardButton(text="👨‍💻 المبرمج", url=f"t.me/{OWNER_USERNAME}")],
        ]

        if FORCE_SUB_CHANNEL:
            start_buttons.append([
                InlineKeyboardButton(text="📢 قناة البوت", url=f"t.me/{FORCE_SUB_CHANNEL}")
            ])

        query.message.edit_text(
            PM_START_TEXT.format(OWNER_USERNAME, num_users, num_chats),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(start_buttons)
        )

    elif query.data == "check_force_sub":
        if check_force_sub(bot, user.id):
            query.answer("✅ تم التحقق!", show_alert=True)
            try:
                query.message.delete()
            except:
                pass
        else:
            query.answer("❌ اشترك أولاً!", show_alert=True)
    
    try:
        query.answer()
    except:
        pass


@spamcheck
def help_command(update: Update, context: CallbackContext):
    chat = update.effective_chat
    args = context.args

    if chat.type != "private":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="💡 المساعدة", url=f"t.me/{context.bot.username}?start=help")]
        ])
        update.effective_message.reply_text("اضغط الزر تحت 👇", reply_markup=keyboard)
        return

    elif args and len(args) >= 1:
        module = args[0].lower()
        if module in HELPABLE:
            help_text = HELPABLE[module].__help__
            send_help(
                chat.id,
                help_text,
                InlineKeyboardMarkup([[InlineKeyboardButton(text="🔙 رجوع", callback_data="help_back")]])
            )
        else:
            send_help(chat.id, HELP_STRINGS)
    else:
        send_help(chat.id, HELP_STRINGS)


def help_button(update: Update, context: CallbackContext):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((\d+)\)", query.data)
    next_match = re.match(r"help_next\((\d+)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = "🔷 *مساعدة {}*:\n".format(HELPABLE[module].__mod_name__) + HELPABLE[module].__help__
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="🔙 رجوع", callback_data="help_back")]]),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(paginate_modules(curr_page - 1, HELPABLE, "help")),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(paginate_modules(next_page + 1, HELPABLE, "help")),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),
            )

        query.answer()
    except BadRequest:
        pass


def smart_reply(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text

    if not text or text.startswith('/') or text.startswith('!'):
        return

    if len(text.strip()) < 2:
        return

    text_clean = text.strip()

    for trigger, response in SMART_REPLIES.items():
        if text_clean == trigger or trigger in text_clean:
            try:
                message.reply_text(response)
            except:
                pass
            return


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(user_id, "هذي إعداداتك:\n\n" + settings, parse_mode=ParseMode.MARKDOWN)
        else:
            dispatcher.bot.send_message(user_id, "ما فيش إعدادات!", parse_mode=ParseMode.MARKDOWN)
    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="إعدادات '{}'".format(chat_name),
                reply_markup=InlineKeyboardMarkup(paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)),
            )
        else:
            dispatcher.bot.send_message(user_id, "ما فيش إعدادات!", parse_mode=ParseMode.MARKDOWN)


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* - *{}*:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="🔙 رجوع", callback_data="stngs_back({})".format(chat_id))]]),
            )
            
        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            query.message.edit_text(
                text="الإعدادات:",
                reply_markup=InlineKeyboardMarkup(paginate_modules(curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id)),
            )
            
        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            query.message.edit_text(
                text="الإعدادات:",
                reply_markup=InlineKeyboardMarkup(paginate_modules(next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id)),
            )
            
        elif back_match:
            chat_id = back_match.group(1)
            query.message.edit_text(
                text="الإعدادات:",
                reply_markup=InlineKeyboardMarkup(paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)),
            )
            
        query.answer()
    except BadRequest:
        pass


@spamcheck
def stats(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id != OWNER_ID:
        update.effective_message.reply_text("⛔ هذا الأمر للمطور فقط!")
        return
    
    stats_text = "📊 *إحصائيات زورو:*\n\n"
    
    for mod in STATS:
        try:
            stats_text += mod.__stats__() + "\n"
        except:
            pass
    
    update.effective_message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)


def error_handler(update: Update, context: CallbackContext):
    pass


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    for mod in MIGRATEABLE:
        try:
            mod.__migrate__(old_chat, new_chat)
        except:
            pass


# ═══════════════════════════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════════════════════════

def main():
    # الأوامر العربية والإنجليزية - باستخدام CustomCommandHandler
    dispatcher.add_handler(CustomCommandHandler(["start", "ابدأ", "ابدا", "بداية", "بدء"], start, run_async=True))
    dispatcher.add_handler(CustomCommandHandler(["help", "مساعدة", "مساعده", "اوامر", "الاوامر"], help_command, run_async=True))
    dispatcher.add_handler(CustomCommandHandler(["stats", "احصائيات", "الاحصائيات"], stats, run_async=True))
    
    # الأزرار
    dispatcher.add_handler(CallbackQueryHandler(help_button, pattern=r"help_"))
    dispatcher.add_handler(CallbackQueryHandler(zoro_callback, pattern=r"zoro_"))
    dispatcher.add_handler(CallbackQueryHandler(settings_button, pattern=r"stngs_"))
    
    # الردود الذكية
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.chat_type.groups,
        smart_reply
    ), group=99)
    
    # الهجرة
    dispatcher.add_handler(MessageHandler(Filters.status_update.migrate, migrate_chats))
    
    # الأخطاء
    dispatcher.add_error_handler(error_handler)
    
    log.info("🤖 زورو بوت يعمل!")
    log.info("👨‍💻 المبرمج: @%s", OWNER_USERNAME)
    
    if WEBHOOK:
        log.info("Using webhooks...")
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=URL + TOKEN
        )
        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
    else:
        log.info("Using long polling...")
        updater.start_polling(timeout=15, read_latency=4, drop_pending_updates=True)
    
    try:
        telethn.run_until_disconnected()
    except:
        updater.idle()


if __name__ == "__main__":
    log.info("Loading modules: " + str(ALL_MODULES))
    main()
