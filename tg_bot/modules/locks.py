import html
import ast
from telegram import Message, Chat, ParseMode, MessageEntity, message
from telegram import TelegramError, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import Filters
from telegram.utils.helpers import mention_html
from .helper_funcs.chat_status import connection_status
from .helper_funcs.decorators import kigcmd, kigmsg
from alphabet_detector import AlphabetDetector
from .sql.approve_sql import is_approved
import tg_bot.modules.sql.locks_sql as sql
from tg_bot import dispatcher, SUDO_USERS, log, spamcheck

from .log_channel import loggable

from .helper_funcs.alternate import send_message, typing_action

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

ad = AlphabetDetector()

# ==================== الأوامر العربية ====================
ARABIC_LOCK_COMMANDS = ["قفل", "اقفل", "اغلق"]
ARABIC_UNLOCK_COMMANDS = ["فتح", "افتح", "فك_القفل"]
ARABIC_LOCKS_COMMANDS = ["الاقفال", "الأقفال", "قائمة_الاقفال"]
ARABIC_LOCKTYPES_COMMANDS = ["انواع_القفل", "أنواع_القفل", "قائمة_القفل"]

LOCK_TYPES = {
    "audio": Filters.audio,
    "voice": Filters.voice,
    "document": Filters.document,
    "video": Filters.video,
    "contact": Filters.contact,
    "photo": Filters.photo,
    "url": Filters.entity(MessageEntity.URL)
    | Filters.caption_entity(MessageEntity.URL),
    "bots": Filters.status_update.new_chat_members,
    "forward": Filters.forwarded & ~ Filters.is_automatic_forward,
    "game": Filters.game,
    "location": Filters.location,
    "egame": Filters.dice,
    "rtl": "rtl",
    "button": "button",
    "inline": "inline",
    "apk" : Filters.document.mime_type("application/vnd.android.package-archive"),
    "doc" : Filters.document.mime_type("application/msword"),
    "exe" : Filters.document.mime_type("application/x-ms-dos-executable"),
    "gif" : Filters.document.mime_type("video/mp4"),
    "jpg" : Filters.document.mime_type("image/jpeg"),
    "mp3" : Filters.document.mime_type("audio/mpeg"),
    "pdf" : Filters.document.mime_type("application/pdf"),
    "txt" : Filters.document.mime_type("text/plain"),
    "xml" : Filters.document.mime_type("application/xml"),
    "zip" : Filters.document.mime_type("application/zip"),
}

# ترجمة أنواع القفل للعربية
LOCK_TYPES_AR = {
    "صوت": "audio",
    "صوتي": "voice",
    "ملف": "document",
    "مستند": "document",
    "فيديو": "video",
    "جهة_اتصال": "contact",
    "صورة": "photo",
    "روابط": "url",
    "رابط": "url",
    "بوتات": "bots",
    "بوت": "bots",
    "تحويل": "forward",
    "توجيه": "forward",
    "لعبة": "game",
    "موقع": "location",
    "نرد": "egame",
    "عربي": "rtl",
    "ازرار": "button",
    "انلاين": "inline",
    "ملصقات": "sticker",
    "ملصق": "sticker",
    "رسائل": "messages",
    "وسائط": "media",
    "استفتاء": "poll",
    "تصويت": "poll",
    "معاينة": "previews",
    "معلومات": "info",
    "دعوة": "invite",
    "تثبيت": "pin",
    "الكل": "all",
}

LOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": False,
        "can_send_media_messages": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_pin_messages": False,
    },
    "messages": {"can_send_messages": False},
    "media": {"can_send_media_messages": False},
    "sticker": {"can_send_other_messages": False},
    "gif": {"can_send_other_messages": False},
    "poll": {"can_send_polls": False},
    "other": {"can_send_other_messages": False},
    "previews": {"can_add_web_page_previews": False},
    "info": {"can_change_info": False},
    "invite": {"can_invite_users": False},
    "pin": {"can_pin_messages": False},
}

UNLOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": True,
        "can_send_media_messages": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
        "can_invite_users": True,
    },
    "messages": {"can_send_messages": True},
    "media": {"can_send_media_messages": True},
    "sticker": {"can_send_other_messages": True},
    "gif": {"can_send_other_messages": True},
    "poll": {"can_send_polls": True},
    "other": {"can_send_other_messages": True},
    "previews": {"can_add_web_page_previews": True},
    "info": {"can_change_info": True},
    "invite": {"can_invite_users": True},
    "pin": {"can_pin_messages": True},
}

PERM_GROUP = -8
REST_GROUP = -12


# NOT ASYNC
def restr_members(
    bot, chat_id, members, messages=False, media=False, other=False, previews=False
):
    for mem in members:
        try:
            bot.restrict_chat_member(
                chat_id,
                mem.user,
                can_send_messages=messages,
                can_send_media_messages=media,
                can_send_other_messages=other,
                can_add_web_page_previews=previews,
            )
        except TelegramError:
            pass


# NOT ASYNC
def unrestr_members(
    bot, chat_id, members, messages=True, media=True, other=True, previews=True
):
    for mem in members:
        try:
            bot.restrict_chat_member(
                chat_id,
                mem.user,
                can_send_messages=messages,
                can_send_media_messages=media,
                can_send_other_messages=other,
                can_add_web_page_previews=previews,
            )
        except TelegramError:
            pass


@kigcmd(command='locktypes')
@spamcheck
def locktypes(update, context):
    update.effective_message.reply_text(
        "\n • ".join(
            ["🔐 أنواع الأقفال المتاحة: "]
            + sorted(list(LOCK_TYPES) + list(LOCK_CHAT_RESTRICTION))
        )
    )


# ==================== معالج عربي لأنواع القفل ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_LOCKTYPES_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_locktypes(update, context):
    lock_list = sorted(list(LOCK_TYPES) + list(LOCK_CHAT_RESTRICTION))
    arabic_list = list(LOCK_TYPES_AR.keys())
    
    msg = "🔐 *أنواع الأقفال المتاحة:*\n\n"
    msg += "*بالإنجليزي:*\n"
    msg += "\n • ".join([""] + lock_list)
    msg += "\n\n*بالعربي:*\n"
    msg += "\n • ".join([""] + arabic_list)
    
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@kigcmd(command='lock', pass_args=True)
@spamcheck
@connection_status
@typing_action
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def lock(update, context) -> str:  # sourcery no-metrics
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    if bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
        if len(args) >= 1:
            ltype = args[0].lower()
            if ltype == "anonchannel":
                text = "⚠️ `anonchannel` مش قفل، استخدم `/antichannel on` لتقييد القنوات"
                send_message(update.effective_message, text, parse_mode = "markdown")
            elif ltype in LOCK_TYPES:

                text = "🔒 تم قفل {} لغير المشرفين!".format(ltype)
                sql.update_lock(chat.id, ltype, locked=True)
                send_message(update.effective_message, text, parse_mode="markdown")

                return (
                    "<b>{}:</b>"
                    "\n#قفل"
                    "\n<b>المشرف:</b> {}"
                    "\nتم قفل <code>{}</code>.".format(
                        html.escape(chat.title),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            elif ltype in LOCK_CHAT_RESTRICTION:
                text = "🔒 تم قفل {} لكل غير المشرفين!".format(ltype)
                current_permission = context.bot.getChat(chat.id).permissions
                context.bot.set_chat_permissions(
                    chat_id=chat.id,
                    permissions=get_permission_list(
                        ast.literal_eval(str(current_permission)),
                        LOCK_CHAT_RESTRICTION[ltype.lower()],
                    ),
                )

                send_message(update.effective_message, text, parse_mode="markdown")
                return (
                    "<b>{}:</b>"
                    "\n#قفل_صلاحيات"
                    "\n<b>المشرف:</b> {}"
                    "\nتم قفل <code>{}</code>.".format(
                        html.escape(chat.title),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            else:
                send_message(
                    update.effective_message,
                    "⚠️ شو تبي تقفل...؟ جرب /locktypes أو انواع_القفل لعرض قائمة الأقفال",
                )
        else:
            send_message(update.effective_message, "⚠️ شو تبي تقفل...؟")

    else:
        send_message(
            update.effective_message,
            "⚠️ أنا مش مشرف أو ما عندي صلاحيات كافية!",
        )

    return ""


# ==================== معالج عربي للقفل ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_LOCK_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@typing_action
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def arabic_lock(update, context) -> str:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    text = message.text
    for cmd in ARABIC_LOCK_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        send_message(message, "⚠️ شو تبي تقفل؟\n\nمثال: قفل صورة\nأو: قفل روابط")
        return ""
    
    ltype = text.lower()
    
    # تحويل العربي للإنجليزي
    if ltype in LOCK_TYPES_AR:
        ltype = LOCK_TYPES_AR[ltype]
    
    if bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
        if ltype in LOCK_TYPES:
            sql.update_lock(chat.id, ltype, locked=True)
            send_message(message, f"🔒 تم قفل {ltype} لغير المشرفين!")
            return (
                "<b>{}:</b>"
                "\n#قفل"
                "\n<b>المشرف:</b> {}"
                "\nتم قفل <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )
        elif ltype in LOCK_CHAT_RESTRICTION:
            current_permission = context.bot.getChat(chat.id).permissions
            context.bot.set_chat_permissions(
                chat_id=chat.id,
                permissions=get_permission_list(
                    ast.literal_eval(str(current_permission)),
                    LOCK_CHAT_RESTRICTION[ltype],
                ),
            )
            send_message(message, f"🔒 تم قفل {ltype} لكل غير المشرفين!")
            return (
                "<b>{}:</b>"
                "\n#قفل_صلاحيات"
                "\n<b>المشرف:</b> {}"
                "\nتم قفل <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )
        else:
            send_message(message, "⚠️ نوع القفل هذا مش موجود!\nجرب: انواع_القفل")
    else:
        send_message(message, "⚠️ أنا مش مشرف أو ما عندي صلاحيات كافية!")
    
    return ""


@kigcmd(command='unlock', pass_args=True)
@spamcheck
@bot_admin_check()
@typing_action
@user_admin_check()
@loggable
def unlock(update, context) -> str:  # sourcery no-metrics
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    if user_is_admin(update, user.id, allow_moderators=True):
        if len(args) >= 1:
            ltype = args[0].lower()
            if ltype == "anonchannel":
                text = "⚠️ `anonchannel` مش قفل، استخدم `/antichannel off` لتعطيل تقييد القنوات"
                send_message(update.effective_message, text, parse_mode="markdown")
            elif ltype in LOCK_TYPES:
                text = "🔓 تم فتح {} للجميع!".format(ltype)
                sql.update_lock(chat.id, ltype, locked=False)
                send_message(update.effective_message, text, parse_mode="markdown")
                return (
                    "<b>{}:</b>"
                    "\n#فتح_قفل"
                    "\n<b>المشرف:</b> {}"
                    "\nتم فتح <code>{}</code>.".format(
                        html.escape(chat.title),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )

            elif ltype in UNLOCK_CHAT_RESTRICTION:
                text = "🔓 تم فتح {} للجميع!".format(ltype)

                current_permission = context.bot.getChat(chat.id).permissions
                context.bot.set_chat_permissions(
                    chat_id=chat.id,
                    permissions=get_permission_list(
                        ast.literal_eval(str(current_permission)),
                        UNLOCK_CHAT_RESTRICTION[ltype.lower()],
                    ),
                )

                send_message(update.effective_message, text, parse_mode="markdown")

                return (
                    "<b>{}:</b>"
                    "\n#فتح_قفل"
                    "\n<b>المشرف:</b> {}"
                    "\nتم فتح <code>{}</code>.".format(
                        html.escape(chat.title),
                        mention_html(user.id, user.first_name),
                        ltype,
                    )
                )
            else:
                send_message(
                    update.effective_message,
                    "⚠️ شو تبي تفتح...؟ جرب /locktypes أو انواع_القفل لعرض قائمة الأقفال.",
                )

        else:
            send_message(update.effective_message, "⚠️ شو تبي تفتح...؟")

    return ""


# ==================== معالج عربي للفتح ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_UNLOCK_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check()
@typing_action
@user_admin_check()
@loggable
def arabic_unlock(update, context) -> str:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    text = message.text
    for cmd in ARABIC_UNLOCK_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        send_message(message, "⚠️ شو تبي تفتح؟\n\nمثال: فتح صورة\nأو: فتح روابط")
        return ""
    
    ltype = text.lower()
    
    # تحويل العربي للإنجليزي
    if ltype in LOCK_TYPES_AR:
        ltype = LOCK_TYPES_AR[ltype]
    
    if user_is_admin(update, user.id, allow_moderators=True):
        if ltype in LOCK_TYPES:
            sql.update_lock(chat.id, ltype, locked=False)
            send_message(message, f"🔓 تم فتح {ltype} للجميع!")
            return (
                "<b>{}:</b>"
                "\n#فتح_قفل"
                "\n<b>المشرف:</b> {}"
                "\nتم فتح <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )
        elif ltype in UNLOCK_CHAT_RESTRICTION:
            current_permission = context.bot.getChat(chat.id).permissions
            context.bot.set_chat_permissions(
                chat_id=chat.id,
                permissions=get_permission_list(
                    ast.literal_eval(str(current_permission)),
                    UNLOCK_CHAT_RESTRICTION[ltype],
                ),
            )
            send_message(message, f"🔓 تم فتح {ltype} للجميع!")
            return (
                "<b>{}:</b>"
                "\n#فتح_قفل"
                "\n<b>المشرف:</b> {}"
                "\nتم فتح <code>{}</code>.".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    ltype,
                )
            )
        else:
            send_message(message, "⚠️ نوع القفل هذا مش موجود!\nجرب: انواع_القفل")
    
    return ""


@kigmsg((Filters.all & Filters.chat_type.groups), group=PERM_GROUP)
@user_not_admin_check
def del_lockables(update, context):  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = message.sender_chat or update.effective_user
    if is_approved(chat.id, user.id):
        return
    for lockable, filter in LOCK_TYPES.items():
        if lockable == "rtl":
            if sql.is_locked(chat.id, lockable) and bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                if message.caption:
                    check = ad.detect_alphabet(u"{}".format(message.caption))
                    if "ARABIC" in check:
                        try:
                            message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                log.exception("ERROR in lockables")
                        break
                if message.text:
                    check = ad.detect_alphabet(u"{}".format(message.text))
                    if "ARABIC" in check:
                        try:
                            message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                log.exception("ERROR in lockables")
                        break
            continue
        if lockable == "button":
            if (
                sql.is_locked(chat.id, lockable)
                and bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.reply_markup
                and message.reply_markup.inline_keyboard
            ):
                try:
                    message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        log.exception("ERROR in lockables")
                break
            continue
        if lockable == "inline":
            if (
                sql.is_locked(chat.id, lockable)
                and bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message
                and message.via_bot
            ):
                try:
                    message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        log.exception("ERROR in lockables")
                break
            continue
        if (
            filter(update)
            and sql.is_locked(chat.id, lockable)
            and bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
        ):
            if lockable == "bots":
                new_members = update.effective_message.new_chat_members
                for new_mem in new_members:
                    if new_mem.is_bot:
                        if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
                            send_message(
                                update.effective_message,
                                "⚠️ شفت بوت وقالولي أوقفه من الدخول... "
                                "لكن أنا مش مشرف!",
                            )
                            return

                        chat.ban_member(new_mem.id)
                        send_message(
                            update.effective_message,
                            "🤖 بس المشرفين يقدروا يضيفوا بوتات هني! طلع برا.",
                        )
                        break
            else:
                try:
                    message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        log.exception("ERROR in lockables")

                break


def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    res = ""
    locklist = []
    permslist = []
    if locks:
        res += "*" + "🔐 الأقفال الحالية في المجموعة:" + "*"
        locklist.append("ملصقات (sticker) = `{}`".format(locks.sticker))
        locklist.append("صوت (audio) = `{}`".format(locks.audio))
        locklist.append("صوتي (voice) = `{}`".format(locks.voice))
        locklist.append("مستند (document) = `{}`".format(locks.document))
        locklist.append("فيديو (video) = `{}`".format(locks.video))
        locklist.append("جهة اتصال (contact) = `{}`".format(locks.contact))
        locklist.append("صورة (photo) = `{}`".format(locks.photo))
        locklist.append("gif = `{}`".format(locks.gif))
        locklist.append("روابط (url) = `{}`".format(locks.url))
        locklist.append("بوتات (bots) = `{}`".format(locks.bots))
        locklist.append("تحويل (forward) = `{}`".format(locks.forward))
        locklist.append("لعبة (game) = `{}`".format(locks.game))
        locklist.append("موقع (location) = `{}`".format(locks.location))
        locklist.append("عربي (rtl) = `{}`".format(locks.rtl))
        locklist.append("أزرار (button) = `{}`".format(locks.button))
        locklist.append("نرد (egame) = `{}`".format(locks.egame))
        locklist.append("انلاين (inline) = `{}`".format(locks.inline))
        locklist.append("apk = `{}`".format(locks.apk))
        locklist.append("doc = `{}`".format(locks.doc))
        locklist.append("exe = `{}`".format(locks.exe))
        locklist.append("jpg = `{}`".format(locks.jpg))
        locklist.append("mp3 = `{}`".format(locks.mp3))
        locklist.append("pdf = `{}`".format(locks.pdf))
        locklist.append("txt = `{}`".format(locks.txt))
        locklist.append("xml = `{}`".format(locks.xml))
        locklist.append("zip = `{}`".format(locks.zip))
    permissions = dispatcher.bot.get_chat(chat_id).permissions
    permslist.append("رسائل (messages) = `{}`".format(permissions.can_send_messages))
    permslist.append("وسائط (media) = `{}`".format(permissions.can_send_media_messages))
    permslist.append("استفتاء (poll) = `{}`".format(permissions.can_send_polls))
    permslist.append("أخرى (other) = `{}`".format(permissions.can_send_other_messages))
    permslist.append("معاينة (previews) = `{}`".format(permissions.can_add_web_page_previews))
    permslist.append("معلومات (info) = `{}`".format(permissions.can_change_info))
    permslist.append("دعوة (invite) = `{}`".format(permissions.can_invite_users))
    permslist.append("تثبيت (pin) = `{}`".format(permissions.can_pin_messages))

    if locklist:
        # Ordering lock list
        locklist.sort()
        # Building lock list string
        for x in locklist:
            res += "\n • {}".format(x)
    res += "\n\n*" + "📋 صلاحيات المحادثة الحالية:" + "*"
    for x in permslist:
        res += "\n • {}".format(x)
    return res


@kigcmd(command='locks')
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@typing_action
def list_locks(update, _):
    chat = update.effective_chat  # type: Optional[Chat]

    res = build_lock_message(chat.id)

    send_message(update.effective_message, res, parse_mode=ParseMode.MARKDOWN)


# ==================== معالج عربي لقائمة الأقفال ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_LOCKS_COMMANDS) + r')$'), group=3)
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@typing_action
def arabic_list_locks(update, _):
    chat = update.effective_chat

    res = build_lock_message(chat.id)

    send_message(update.effective_message, res, parse_mode=ParseMode.MARKDOWN)


def get_permission_list(current, new):
    permissions = {
        "can_send_messages": None,
        "can_send_media_messages": None,
        "can_send_polls": None,
        "can_send_other_messages": None,
        "can_add_web_page_previews": None,
        "can_change_info": None,
        "can_invite_users": None,
        "can_pin_messages": None,
    }
    permissions.update(current)
    permissions.update(new)
    return ChatPermissions(**permissions)


def __import_data__(chat_id, data):
    # set chat locks
    locks = data.get("locks", {})
    for itemlock in locks:
        if itemlock in LOCK_TYPES:
            sql.update_lock(chat_id, itemlock, locked=True)
        elif itemlock in LOCK_CHAT_RESTRICTION:
            sql.update_restriction(chat_id, itemlock, locked=True)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return build_lock_message(chat_id)


from .language import gs

def get_help(chat):
    return gs(chat, "locks_help")

__mod_name__ = "الأقفال"
