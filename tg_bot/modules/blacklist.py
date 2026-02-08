from enum import IntEnum
import html
import re
from typing import List

from telegram import ChatPermissions, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.utils.helpers import mention_html
import tg_bot.modules.sql.blacklist_sql as sql
from .. import SUDO_USERS, log, spamcheck
from .sql.approve_sql import is_approved
from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_text
from .helper_funcs.misc import split_message
from .log_channel import loggable
from .warns import warn
from .helper_funcs.string_handling import extract_time
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from .helper_funcs.alternate import send_message, typing_action

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_not_admin_check,
)

BLACKLIST_GROUP = -3

# ==================== الأوامر العربية ====================
ARABIC_BLACKLIST_COMMANDS = ["القائمة_السوداء", "المحظورات", "الكلمات_المحظورة"]
ARABIC_ADDBL_COMMANDS = ["اضف_محظور", "اضافة_محظور", "حظر_كلمة"]
ARABIC_RMBL_COMMANDS = ["حذف_محظور", "ازالة_محظور", "فك_حظر_كلمة"]
ARABIC_BLMODE_COMMANDS = ["وضع_المحظورات", "نوع_المحظورات"]
ARABIC_RMALLBL_COMMANDS = ["مسح_المحظورات", "حذف_كل_المحظورات"]

# ترجمة أوضاع القائمة السوداء
BLACKLIST_MODES_AR = {
    "حذف": "del",
    "delete": "del",
    "انذار": "warn",
    "تحذير": "warn",
    "كتم": "mute",
    "طرد": "kick",
    "حظر": "ban",
    "حظر_مؤقت": "tban",
    "كتم_مؤقت": "tmute",
    "لا_شي": "off",
    "تعطيل": "off",
}


class BlacklistActions(IntEnum):
    default = 0
    delete = 1
    warn = 2
    mute = 3
    kick = 4
    ban = 5


@kigcmd(command=["blacklist", "blacklists", "blocklist", "blocklists"], pass_args=True, admin_ok=True)
@spamcheck
@user_admin_check()
@typing_action
def blacklist(update, context):
    chat = update.effective_chat
    args = context.args

    filter_list = "<b>⚫ إعدادات القائمة السوداء لـ {}</b>:\n".format(html.escape(chat.title))

    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    bl_type = get_bl_type_arabic(getmode, getvalue)

    filter_list += "ㅤ<b>الوضع الحالي:</b>\n     {}\n".format(bl_type)
    all_blacklisted = sql.get_chat_blacklist(chat.id)
    filter_list += "\nㅤ<b>الكلمات المحظورة (<i>{}</i>):</b>\n".format(len(all_blacklisted))
    for i in all_blacklisted:
        trigger = i[0]
        action = BlacklistActions(i[1]).name
        action_ar = get_action_arabic(action)
        filter_list += "  - <code>{}</code>\n    <b>الإجراء:</b> {}\n".format(html.escape(trigger), action_ar)

    split_text = split_message(filter_list)
    for text in split_text:
        if len(all_blacklisted) == 0:
            send_message(
                update.effective_message,
                "📭 ما في كلمات محظورة في <b>{}</b>!".format(chat.title),
                parse_mode=ParseMode.HTML,
            )
            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


def get_bl_type_arabic(getmode, getvalue=""):
    """تحويل نوع القائمة السوداء للعربي"""
    match getmode:
        case 0:
            return "لا شي"
        case 1:
            return "حذف"
        case 2:
            return "إنذار"
        case 3:
            return "كتم"
        case 4:
            return "طرد"
        case 5:
            return "حظر"
        case 6:
            return "حظر مؤقت لمدة {}".format(getvalue)
        case 7:
            return "كتم مؤقت لمدة {}".format(getvalue)
    return "لا شي"


def get_action_arabic(action):
    """تحويل الإجراء للعربي"""
    actions = {
        "default": "افتراضي",
        "delete": "حذف",
        "warn": "إنذار",
        "mute": "كتم",
        "kick": "طرد",
        "ban": "حظر",
    }
    return actions.get(action, action)


# ==================== معالج عربي لعرض القائمة السوداء ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_BLACKLIST_COMMANDS) + r')$'), group=3)
@spamcheck
@user_admin_check()
@typing_action
def arabic_blacklist(update, context):
    chat = update.effective_chat

    filter_list = "<b>⚫ إعدادات القائمة السوداء لـ {}</b>:\n".format(html.escape(chat.title))

    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    bl_type = get_bl_type_arabic(getmode, getvalue)

    filter_list += "ㅤ<b>الوضع الحالي:</b>\n     {}\n".format(bl_type)
    all_blacklisted = sql.get_chat_blacklist(chat.id)
    filter_list += "\nㅤ<b>الكلمات المحظورة (<i>{}</i>):</b>\n".format(len(all_blacklisted))
    for i in all_blacklisted:
        trigger = i[0]
        action = BlacklistActions(i[1]).name
        action_ar = get_action_arabic(action)
        filter_list += "  - <code>{}</code>\n    <b>الإجراء:</b> {}\n".format(html.escape(trigger), action_ar)

    split_text = split_message(filter_list)
    for text in split_text:
        if len(all_blacklisted) == 0:
            send_message(
                update.effective_message,
                "📭 ما في كلمات محظورة في <b>{}</b>!".format(chat.title),
                parse_mode=ParseMode.HTML,
            )
            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@kigcmd(command=["addblacklist", "addblocklist"], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@typing_action
def add_blacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    chat_name = html.escape(chat.title)

    act = BlacklistActions.default
    bl = ""
    if len(words) > 1:
        text = words[1]
        to_blacklist: List[str] = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})

        for trigger in to_blacklist:
            bl, action = extract_bl_and_action(trigger)
            if not sql.add_to_blacklist(chat.id, bl, action.value):
                return msg.reply_text("⚠️ وصلت الحد الأقصى للقائمة السوداء (100) في هالمجموعة.")
            act = action.name

        if len(to_blacklist) == 1:
            reply = "✅ تم إضافة الكلمة المحظورة: <code>{}</code> بإجراء <b>{}</b>!"
            send_message(
                update.effective_message,
                reply.format(
                    html.escape(bl), get_action_arabic(act)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            reply = "✅ تم إضافة <code>{}</code> كلمة محظورة في: <b>{}</b>!"
            send_message(
                update.effective_message,
                reply.format(
                    len(to_blacklist), chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            update.effective_message,
            "⚠️ أخبرني أي كلمات تبي تضيفها للقائمة السوداء.",
        )


# ==================== معالج عربي لإضافة محظور ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_ADDBL_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@typing_action
def arabic_add_blacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat
    
    text = msg.text
    for cmd in ARABIC_ADDBL_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    chat_name = html.escape(chat.title)

    act = BlacklistActions.default
    bl = ""
    if text:
        to_blacklist: List[str] = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})

        for trigger in to_blacklist:
            bl, action = extract_bl_and_action(trigger)
            if not sql.add_to_blacklist(chat.id, bl, action.value):
                return msg.reply_text("⚠️ وصلت الحد الأقصى للقائمة السوداء (100) في هالمجموعة.")
            act = action.name

        if len(to_blacklist) == 1:
            reply = "✅ تم إضافة الكلمة المحظورة: <code>{}</code> بإجراء <b>{}</b>!"
            send_message(
                msg,
                reply.format(
                    html.escape(bl), get_action_arabic(act)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            reply = "✅ تم إضافة <code>{}</code> كلمة محظورة في: <b>{}</b>!"
            send_message(
                msg,
                reply.format(
                    len(to_blacklist), chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            msg,
            "⚠️ أخبرني أي كلمات تبي تضيفها للقائمة السوداء.\n\n"
            "مثال: `اضف_محظور كلمة_سيئة`",
            parse_mode=ParseMode.MARKDOWN,
        )


def extract_bl_and_action(text: str) -> (str, BlacklistActions):
    if not text or not ("{" and "}" in text):
        return text, BlacklistActions.default

    action = text[text.rindex("{") + 1: text.rindex("}")]

    if action not in BlacklistActions.__members__:
        return "", BlacklistActions.default

    return text[:text.rindex("{") - 1], BlacklistActions[action]


@kigcmd(command=["unblacklist", "unblocklist"], pass_args=True)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def unblacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            }
        )

        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    "✅ تم إزالة <code>{}</code> من القائمة السوداء في <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), chat_name
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                send_message(
                    update.effective_message, "⚠️ هذي مش كلمة محظورة!"
                )

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                "✅ تم إزالة <code>{}</code> كلمة من القائمة السوداء في <b>{}</b>!".format(
                    successful, chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                update.effective_message,
                "⚠️ ما لقيت أي من هالكلمات في القائمة السوداء!",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "✅ تم إزالة <code>{}</code> كلمة. {} ما كانت موجودة أصلاً.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        send_message(
            update.effective_message,
            "⚠️ أخبرني أي كلمات تبي تحذفها من القائمة السوداء!",
        )


# ==================== معالج عربي لحذف محظور ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_RMBL_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def arabic_unblacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat

    text = msg.text
    for cmd in ARABIC_RMBL_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if text:
        to_unblacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            }
        )

        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    msg,
                    "✅ تم إزالة <code>{}</code> من القائمة السوداء في <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), chat_name
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                send_message(msg, "⚠️ هذي مش كلمة محظورة!")

        elif successful == len(to_unblacklist):
            send_message(
                msg,
                "✅ تم إزالة <code>{}</code> كلمة من القائمة السوداء!".format(successful),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(msg, "⚠️ ما لقيت أي من هالكلمات في القائمة السوداء!")

        else:
            send_message(
                msg,
                "✅ تم إزالة <code>{}</code> كلمة. {} ما كانت موجودة.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        send_message(
            msg,
            "⚠️ أخبرني أي كلمات تبي تحذفها من القائمة السوداء!\n\n"
            "مثال: `حذف_محظور كلمة_سيئة`",
            parse_mode=ParseMode.MARKDOWN,
        )


@kigcmd(command=["blacklistmode", "blocklistmode"], pass_args=True)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def blacklist_mode(update, context):  # sourcery no-metrics
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if args:
        mode = args[0].lower()
        
        # تحويل العربي للإنجليزي
        if mode in BLACKLIST_MODES_AR:
            mode = BLACKLIST_MODES_AR[mode]
        
        if mode in ["off", "nothing", "no"]:
            settypeblacklist = "لا شي"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif mode in ["del", "delete"]:
            settypeblacklist = "حذف الرسالة المحظورة"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif mode == "warn":
            settypeblacklist = "إنذار المرسل"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif mode == "mute":
            settypeblacklist = "كتم المرسل"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif mode == "kick":
            settypeblacklist = "طرد المرسل"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif mode == "ban":
            settypeblacklist = "حظر المرسل"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif mode == "tban":
            if len(args) == 1:
                teks = """⚠️ يبدو إنك حاولت تحدد وقت للقائمة السوداء لكن ما حددت المدة؛ جرب:
`/blacklistmode tban <المدة>` أو `وضع_المحظورات حظر_مؤقت <المدة>`

أمثلة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """⚠️ قيمة وقت غير صحيحة!
أمثلة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "حظر مؤقت لمدة {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif mode == "tmute":
            if len(args) == 1:
                teks = """⚠️ يبدو إنك حاولت تحدد وقت للقائمة السوداء لكن ما حددت المدة؛ جرب:
`/blacklistmode tmute <المدة>` أو `وضع_المحظورات كتم_مؤقت <المدة>`

أمثلة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """⚠️ قيمة وقت غير صحيحة!
أمثلة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "كتم مؤقت لمدة {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "⚠️ أنا أفهم بس: تعطيل/حذف/انذار/حظر/طرد/كتم/حظر_مؤقت/كتم_مؤقت!",
            )
            return ""
        text = "✅ تم تغيير وضع القائمة السوداء: `{}`!".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b>المشرف:</b> {}\n"
            "تم تغيير وضع القائمة السوداء إلى: {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        bl_type = get_bl_type_arabic(getmode, getvalue)
        text = "📊 وضع القائمة السوداء الحالي: *{}*.".format(bl_type)
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


# ==================== معالج عربي لوضع المحظورات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_BLMODE_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def arabic_blacklist_mode(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text = msg.text
    for cmd in ARABIC_BLMODE_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    chat_id = chat.id

    if text:
        args = text.split()
        mode = args[0].lower()
        
        # تحويل العربي للإنجليزي
        if mode in BLACKLIST_MODES_AR:
            mode = BLACKLIST_MODES_AR[mode]
        
        if mode in ["off", "nothing", "no", "لا_شي", "تعطيل"]:
            settypeblacklist = "لا شي"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif mode in ["del", "delete", "حذف"]:
            settypeblacklist = "حذف الرسالة"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif mode in ["warn", "انذار", "تحذير"]:
            settypeblacklist = "إنذار المرسل"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif mode in ["mute", "كتم"]:
            settypeblacklist = "كتم المرسل"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif mode in ["kick", "طرد"]:
            settypeblacklist = "طرد المرسل"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif mode in ["ban", "حظر"]:
            settypeblacklist = "حظر المرسل"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif mode in ["tban", "حظر_مؤقت"]:
            if len(args) == 1:
                msg.reply_text("⚠️ حدد المدة!\nمثال: وضع_المحظورات حظر_مؤقت 1h")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                msg.reply_text("⚠️ مدة غير صحيحة!")
                return ""
            settypeblacklist = "حظر مؤقت لمدة {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif mode in ["tmute", "كتم_مؤقت"]:
            if len(args) == 1:
                msg.reply_text("⚠️ حدد المدة!\nمثال: وضع_المحظورات كتم_مؤقت 1h")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                msg.reply_text("⚠️ مدة غير صحيحة!")
                return ""
            settypeblacklist = "كتم مؤقت لمدة {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(msg, "⚠️ أنا أفهم بس: تعطيل/حذف/انذار/حظر/طرد/كتم/حظر_مؤقت/كتم_مؤقت!")
            return ""
        
        msg.reply_text("✅ تم تغيير وضع القائمة السوداء: `{}`!".format(settypeblacklist), parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b>المشرف:</b> {}\n"
            "تم تغيير وضع القائمة السوداء إلى: {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        bl_type = get_bl_type_arabic(getmode, getvalue)
        msg.reply_text(
            "📊 وضع القائمة السوداء الحالي: *{}*.\n\n"
            "الأوضاع المتاحة:\n"
            "• تعطيل - لا شي\n"
            "• حذف - حذف الرسالة\n"
            "• انذار - إنذار المرسل\n"
            "• كتم - كتم المرسل\n"
            "• طرد - طرد المرسل\n"
            "• حظر - حظر المرسل\n"
            "• حظر_مؤقت 1h - حظر مؤقت\n"
            "• كتم_مؤقت 1h - كتم مؤقت".format(bl_type),
            parse_mode=ParseMode.MARKDOWN
        )
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


@kigmsg(((Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.chat_type.groups),
        group=BLACKLIST_GROUP)
@user_not_admin_check
def del_blacklist(update: Update, context: CallbackContext):  # sourcery no-metrics
    chat = update.effective_chat
    message = update.effective_message
    user = message.sender_chat or update.effective_user
    bot = context.bot
    to_match = extract_text(message)
    if not to_match:
        return
    if is_approved(chat.id, user.id):
        return
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_blacklist(chat.id)

    for item in chat_filters:
        trigger = str(item[0])
        getmode = (int(item[1]) if int(item[1]) > 0 else getmode)

        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                match getmode:
                    case 0:
                        return
                    case 1:
                        message.delete()
                    case 2:
                        message.delete()
                        warn(
                            update.effective_user,
                            update,
                            ("استخدام كلمة محظورة: {}".format(trigger)),
                            message,
                            update.effective_user,
                        )
                        return
                    case 3:
                        message.delete()
                        bot.restrict_chat_member(
                            chat.id,
                            update.effective_user.id,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                        bot.sendMessage(
                            chat.id,
                            f"🔇 تم كتم {user.first_name} بسبب استخدام كلمة محظورة: {trigger}!",
                        )
                        return
                    case 4:
                        message.delete()
                        res = chat.unban_member(update.effective_user.id)
                        if res:
                            bot.sendMessage(
                                chat.id,
                                f"👢 تم طرد {user.first_name} بسبب استخدام كلمة محظورة: {trigger}!",
                            )
                        return
                    case 5:
                        message.delete()
                        chat.ban_member(user.id)
                        bot.sendMessage(
                            chat.id,
                            f"🚫 تم حظر {user.first_name} بسبب استخدام كلمة محظورة: {trigger}",
                        )
                        return
                    case 6:
                        message.delete()
                        bantime = extract_time(message, value)
                        chat.ban_member(user.id, until_date=bantime)
                        bot.sendMessage(
                            chat.id,
                            f"🚫 تم حظر {user.first_name} لمدة '{value}' بسبب استخدام كلمة محظورة: {trigger}!",
                        )
                        return
                    case 7:
                        message.delete()
                        mutetime = extract_time(message, value)
                        bot.restrict_chat_member(
                            chat.id,
                            user.id,
                            until_date=mutetime,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                        bot.sendMessage(
                            chat.id,
                            f"🔇 تم كتم {user.first_name} لمدة '{value}' بسبب استخدام كلمة محظورة: {trigger}!",
                        )
                        return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    log.exception("Error while deleting blacklist message.")
            break


@kigcmd(command=["removeallblacklists", "removeallblocklists", "unblacklistall"], filters=Filters.chat_type.groups)
@spamcheck
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يمسح كل القائمة السوداء مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🗑 حذف كل المحظورات", callback_data="blacklists_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="blacklists_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تحذف كل القائمة السوداء في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


# ==================== معالج عربي لمسح كل المحظورات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_RMALLBL_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يمسح كل القائمة السوداء مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🗑 حذف كل المحظورات", callback_data="blacklists_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="blacklists_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تحذف كل القائمة السوداء في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@kigcallback(pattern=r"blacklists_.*")
@loggable
def rmall_callback(update, context) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "blacklists_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_blacklist(chat.id)
            if not allfilters:
                msg.edit_text("📭 ما في كلمات محظورة في هالمجموعة!")
                return ""

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)
            for i in filterlist:
                sql.rm_from_blacklist(chat.id, i[0])

            msg.edit_text(f"✅ تم حذف {count} كلمة محظورة في {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#مسح_القائمة_السوداء\n"
                f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        if member.status == "administrator":
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""

        if member.status == "member":
            query.answer("⚠️ لازم تكون مشرف باش تسوي هالشي.")
            return ""
    elif query.data == "blacklists_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("❌ تم إلغاء العملية.")
            return ""
        if member.status == "administrator":
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""
        if member.status == "member":
            query.answer("⚠️ لازم تكون مشرف باش تسوي هالشي.")
            return ""


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "في {} كلمة محظورة.".format(blacklisted)


def __stats__():
    return "• {} كلمة محظورة، في {} مجموعة.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats()
    )


__mod_name__ = "القائمة السوداء"

from .language import gs


def get_help(chat):
    return gs(chat, "blacklist_help")
