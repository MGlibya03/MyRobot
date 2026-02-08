import html
import re
from typing import Optional
from sqlalchemy.sql.expression import false

import telegram
from tg_bot import BAN_STICKER, DEV_USERS, OWNER_ID, SUDO_USERS, WHITELIST_USERS, dispatcher, spamcheck
#from .disable import DisableAbleCommandHandler

from .helper_funcs.extraction import (
    extract_text,
    extract_user,
    extract_user_and_text,
)
from .helper_funcs.filters import CustomFilters
from .helper_funcs.misc import split_message
from .helper_funcs.string_handling import split_quotes
from .log_channel import loggable
from .sql import warns_sql as sql
from .sql.approve_sql import is_approved
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    DispatcherHandlerStop,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>فلاتر الإنذارات الحالية في المجموعة:</b>\n"
WARNS_GROUP = 2

# ==================== الأوامر العربية ====================
ARABIC_WARN_COMMANDS = ["انذار", "انذر", "تحذير", "حذر"]
ARABIC_SWARN_COMMANDS = ["انذار_صامت", "تحذير_صامت"]
ARABIC_DWARN_COMMANDS = ["انذار_حذف", "تحذير_حذف"]
ARABIC_RESETWARNS_COMMANDS = ["مسح_الانذارات", "صفر_الانذارات", "حذف_الانذارات"]
ARABIC_WARNS_COMMANDS = ["الانذارات", "انذاراتي", "انذاراته"]
ARABIC_ADDWARN_COMMANDS = ["اضف_انذار", "فلتر_انذار"]
ARABIC_NOWARN_COMMANDS = ["حذف_فلتر_انذار", "ازالة_فلتر_انذار"]
ARABIC_WARNLIST_COMMANDS = ["قائمة_الانذارات", "فلاتر_الانذارات"]
ARABIC_WARNLIMIT_COMMANDS = ["حد_الانذارات", "عدد_الانذارات"]
ARABIC_STRONGWARN_COMMANDS = ["انذار_قوي", "تحذير_قوي"]


def warn_immune(message, update, uid, warner):

    if user_is_admin(update, uid):
        if uid is OWNER_ID:
            message.reply_text("⚠️ هذا صاحبي ومالكي، كيف تجرأت!")
            return True
        if uid in DEV_USERS:
            message.reply_text("⚠️ هذا من المطورين حقي، روح ابكي في مكان ثاني!")
            return True
        if uid in SUDO_USERS:
            message.reply_text("⚠️ هذا مستخدم SUDO، مش حننذره!")
            return True
        else:
            message.reply_text("⚠️ المشرفين محميين من الإنذارات!")
            return True

    if uid in WHITELIST_USERS:
        if warner:
            message.reply_text("⚠️ المستخدمين في القائمة البيضاء محميين من الإنذارات.")
            return True
        else:
            message.reply_text(
                "⚠️ مستخدم من القائمة البيضاء فعّل فلتر إنذار تلقائي!\nما نقدر ننذره لكن لازم يتجنب سوء الاستخدام."
            )
            return True
    else:
        return False


# Not async
def warn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "إنذار تلقائي من الفلتر."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الطرد</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الحظر</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#حظر_بسبب_الإنذارات\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 إزالة الإنذار", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 اقرأ القوانين", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>تم الإنذار</b>\n"
            f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  العدد:</b> {num_warns}/{limit}\n"
        )
        if reason:
            reply += f"\n<code> </code><b>•  السبب:</b> {html.escape(reason)}"
        reply += '\n⚠️ خذ وقتك واقرأ القوانين باش ما تتكرر المشكلة!'

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إنذار\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
        else:
            raise
    return log_reason


# Not async
def swarn(
    user: User, update: Update, reason: str, message: Message, dels, warner: User = None,
) -> str:  # sourcery no-metrics
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "إنذار تلقائي من الفلتر."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الطرد</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الحظر</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#حظر_بسبب_الإنذارات\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>الآيدي:</b> <code>{user.id}</code>\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 إزالة الإنذار", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 اقرأ القوانين", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>تم الإنذار</b>\n"
            f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  العدد:</b> {num_warns}/{limit}\n"
        )
        if reason:
            reply += f"\n<code> </code><b>•  السبب:</b> {html.escape(reason)}"

        reply += f"\n⚠️ خذ وقتك واقرأ القوانين باش ما تتكرر المشكلة!"

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إنذار\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>الآيدي:</b> <code>{user.id}</code>\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        if dels:
            if message.reply_to_message:
                message.reply_to_message.delete()
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        message.delete()
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
            message.delete()
        else:
            raise
    return log_reason


# Not async
def dwarn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> str:  # sourcery no-metrics
    if warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat
    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "إنذار تلقائي من الفلتر."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الطرد</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        else:  # ban
            chat.ban_member(user.id)
            reply = (
                f"<code>❕</code><b>تم الحظر</b>\n"
                f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  عدد الإنذارات:</b> {limit}"
            )

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#حظر_بسبب_الإنذارات\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔘 إزالة الإنذار", callback_data="rm_warn({})".format(user.id)
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 اقرأ القوانين", url="t.me/{}?start={}".format(dispatcher.bot.username, chat.id)
                    )
                ],
            ]
        )

        reply = (
            f"<code>❕</code><b>تم الإنذار</b>\n"
            f"<code> </code><b>•  العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  العدد:</b> {num_warns}/{limit}\n"
        )
        if reason:
            reply += f"\n<code> </code><b>•  السبب:</b> {html.escape(reason)}"
        reply += f"\n⚠️ خذ وقتك واقرأ القوانين باش ما تتكرر المشكلة!"
        
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إنذار\n"
            f"<b>المشرف:</b> {warner_tag}\n"
            f"<b>العضو:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>العدد:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        if message.reply_to_message:
            message.reply_to_message.delete()
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False
            )
        else:
            raise
    return log_reason


@kigcallback(pattern=r"rm_warn")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, noreply=True)
@loggable
def button(update: Update, _: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    if match := re.match(r"rm_warn\((.+?)\)", query.data):
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        if sql.remove_warn(user_id, chat.id):
            update.effective_message.edit_text(
                "✅ تم إزالة الإنذار بواسطة {}.".format(
                        mention_html(user.id, user.first_name) if not
                        user_is_admin(update, user.id, perm = AdminPerms.IS_ANONYMOUS) else "مشرف مجهول"),
                parse_mode=ParseMode.HTML,
            )
            user_member = chat.get_member(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#إزالة_إنذار\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>العضو:</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
                f"<b>الآيدي:</b> <code>{user_member.user.id}</code>"
            )
        else:
            update.effective_message.edit_text(
                "⚠️ هذا العضو ما عنده إنذارات أصلاً.", parse_mode=ParseMode.HTML
            )

    return ""


@kigcmd(command='swarn', filters=Filters.chat_type.groups)
@kigcmd(command='dwarn', filters=Filters.chat_type.groups)
@kigcmd(command='dswarn', filters=Filters.chat_type.groups)
@kigcmd(command='warn', filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    warner: Optional[User] = update.effective_user

    user_id, reason = extract_user_and_text(message, args)

    if (message.reply_to_message and message.reply_to_message.sender_chat) or (user_id and user_id < 0):
        message.reply_text("⚠️ هذا الأمر ما يشتغل على القنوات، لكن تقدر تحظرها بدال.")
        return ""

    if message.text.startswith('/s') or message.text.startswith('!s') or message.text.startswith('>s'):
        silent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        silent = False
    if message.text.startswith('/d') or message.text.startswith('!d') or message.text.startswith('>d'):
        delban = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        delban = False
    if message.text.startswith('/ds') or message.text.startswith('!ds') or message.text.startswith('>ds'):
        delsilent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        delsilent = False
    if silent:
        dels = False
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return swarn(chat.get_member(user_id).user, update, reason, message, dels, warner)
        else:
            message.reply_text("⚠️ هذا ما يشبه آيدي مستخدم صحيح.")
    if delsilent:
        dels = True
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return swarn(chat.get_member(user_id).user, update, reason, message, dels, warner)
        else:
            message.reply_text("⚠️ هذا ما يشبه آيدي مستخدم صحيح.")
    elif delban:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return dwarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    warner,
                )
            else:
                return dwarn(chat.get_member(user_id).user, update, reason, message, warner)
        else:
            message.reply_text("⚠️ هذا ما يشبه آيدي مستخدم صحيح.")
    else:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return warn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message.reply_to_message,
                    warner,
                )
            else:
                return warn(chat.get_member(user_id).user, update, reason, message, warner)
        else:
            message.reply_text("⚠️ هذا ما يشبه آيدي مستخدم صحيح.")
    return ""


# ==================== معالج الأوامر العربية للإنذار ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_WARN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods=True)
@loggable
def arabic_warn_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    chat = update.effective_chat
    warner = update.effective_user
    
    # استخراج النص بعد الأمر
    text = message.text
    for cmd in ARABIC_WARN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    args = text.split() if text else []
    
    # تحديد المستخدم والسبب
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = text if text else None
    elif args:
        user_id = extract_user(message, args)
        reason = " ".join(args[1:]) if len(args) > 1 else None
    else:
        message.reply_text("⚠️ لازم ترد على رسالة العضو أو تعطيني الآيدي حقه!")
        return ""
    
    if not user_id:
        message.reply_text("⚠️ ما قدرت أحدد العضو المطلوب!")
        return ""
    
    if (message.reply_to_message and message.reply_to_message.sender_chat) or user_id < 0:
        message.reply_text("⚠️ هذا الأمر ما يشتغل على القنوات!")
        return ""
    
    if message.reply_to_message:
        return warn(
            message.reply_to_message.from_user,
            update,
            reason,
            message.reply_to_message,
            warner,
        )
    else:
        return warn(chat.get_member(user_id).user, update, reason, message, warner)


@kigcmd(command=['restwarn', 'resetwarns'], filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user

    if user_id:= extract_user(message, args):
        sql.reset_warns(user_id, chat.id)
        message.reply_text("✅ تم مسح جميع الإنذارات!")
        warned = chat.get_member(user_id).user
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#مسح_الإنذارات\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>العضو:</b> {mention_html(warned.id, warned.first_name)}\n"
            f"<b>الآيدي:</b> <code>{warned.id}</code>"
        )
    else:
        message.reply_text("⚠️ ما حددت أي عضو!")
    return ""


# ==================== معالج عربي لمسح الإنذارات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_RESETWARNS_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
def arabic_reset_warns(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    text = message.text
    for cmd in ARABIC_RESETWARNS_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    args = text.split() if text else []
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif args:
        user_id = extract_user(message, args)
    else:
        message.reply_text("⚠️ لازم ترد على رسالة العضو أو تعطيني الآيدي حقه!")
        return ""
    
    if not user_id:
        message.reply_text("⚠️ ما قدرت أحدد العضو!")
        return ""
    
    sql.reset_warns(user_id, chat.id)
    message.reply_text("✅ تم مسح جميع الإنذارات!")
    warned = chat.get_member(user_id).user
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#مسح_الإنذارات\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>العضو:</b> {mention_html(warned.id, warned.first_name)}\n"
        f"<b>الآيدي:</b> <code>{warned.id}</code>"
    )


@kigcmd(command='warns', filters=Filters.chat_type.groups, can_disable=True)
@spamcheck
def warns(update: Update, context: CallbackContext):
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = (
                f"⚠️ هذا العضو عنده {num_warns}/{limit} إنذار، للأسباب التالية:"
            )
            for reason in reasons:
                text += f"\n • {reason}"

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                f"⚠️ هذا العضو عنده {num_warns}/{limit} إنذار، لكن ما في أسباب مسجلة."
            )
    else:
        update.effective_message.reply_text("✅ هذا العضو ما عنده أي إنذارات!")


# ==================== معالج عربي لعرض الإنذارات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_WARNS_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_warns(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    
    text = message.text
    for cmd in ARABIC_WARNS_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    args = text.split() if text else []
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif args:
        user_id = extract_user(message, args)
    else:
        user_id = update.effective_user.id
    
    if not user_id:
        user_id = update.effective_user.id
    
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = f"⚠️ هذا العضو عنده {num_warns}/{limit} إنذار، للأسباب التالية:"
            for reason in reasons:
                text += f"\n • {reason}"

            msgs = split_message(text)
            for msg in msgs:
                message.reply_text(msg)
        else:
            message.reply_text(
                f"⚠️ هذا العضو عنده {num_warns}/{limit} إنذار، لكن ما في أسباب مسجلة."
            )
    else:
        message.reply_text("✅ هذا العضو ما عنده أي إنذارات!")


@kigcmd(command='addwarn', filters=Filters.chat_type.groups, run_async=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def add_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message
    user = update.effective_user

    args = msg.text.split(None, 1)

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 2:
        return

    keyword = extracted[0].lower()
    content = extracted[1]

    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(f"✅ تم إضافة فلتر إنذار للكلمة '{keyword}'!")
    raise DispatcherHandlerStop


# ==================== معالج عربي لإضافة فلتر إنذار ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_ADDWARN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
def arabic_add_warn_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    
    text = msg.text
    for cmd in ARABIC_ADDWARN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        msg.reply_text("⚠️ الاستخدام: اضف_انذار \"الكلمة\" السبب")
        return
    
    extracted = split_quotes(text)
    
    if len(extracted) < 2:
        msg.reply_text("⚠️ الاستخدام: اضف_انذار \"الكلمة\" السبب")
        return
    
    keyword = extracted[0].lower()
    content = extracted[1]
    
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)
    
    sql.add_warn_filter(chat.id, keyword, content)
    msg.reply_text(f"✅ تم إضافة فلتر إنذار للكلمة '{keyword}'!")
    raise DispatcherHandlerStop


@kigcmd(command=['nowarn', 'stopwarn'], filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def remove_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message
    user = update.effective_user

    args = msg.text.split(None, 1)

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("⚠️ ما في فلاتر إنذارات مفعلة هني!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("✅ تمام، مش حننذر على هالكلمة بعد.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "⚠️ هذا مش فلتر إنذار موجود - استخدم /warnlist أو قائمة_الانذارات لعرض كل الفلاتر."
    )


# ==================== معالج عربي لحذف فلتر إنذار ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_NOWARN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def arabic_remove_warn_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    
    text = msg.text
    for cmd in ARABIC_NOWARN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        msg.reply_text("⚠️ لازم تحدد الكلمة اللي تبي تحذف فلترها!")
        return
    
    extracted = split_quotes(text)
    if len(extracted) < 1:
        return
    
    to_remove = extracted[0]
    chat_filters = sql.get_chat_warn_triggers(chat.id)
    
    if not chat_filters:
        msg.reply_text("⚠️ ما في فلاتر إنذارات مفعلة هني!")
        return
    
    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("✅ تمام، مش حننذر على هالكلمة بعد.")
            raise DispatcherHandlerStop
    
    msg.reply_text("⚠️ هذا مش فلتر إنذار موجود!")


@kigcmd(command=['warnlist', 'warnfilters'], filters=Filters.chat_type.groups, can_disable=True)
@spamcheck
def list_warn_filters(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("⚠️ ما في فلاتر إنذارات مفعلة هني!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


# ==================== معالج عربي لقائمة فلاتر الإنذارات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_WARNLIST_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_list_warn_filters(update: Update, context: CallbackContext):
    chat = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("⚠️ ما في فلاتر إنذارات مفعلة هني!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@kigmsg((CustomFilters.has_text & Filters.chat_type.groups), group=WARNS_GROUP)
@loggable
def reply_filter(update: Update, context: CallbackContext) -> Optional[str]:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message
    user: Optional[User] = update.effective_user

    if not user:
        return

    if user.id == 777000:
        return
    if is_approved(chat.id, user.id):
        return

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user: Optional[User] = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, update, warn_filter.reply, message)
    return ""


@kigcmd(command='warnlimit', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user = update.effective_user
    msg: Optional[Message] = update.effective_message
    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("⚠️ أقل حد للإنذارات هو 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("✅ تم تحديث حد الإنذارات إلى {}".format(args[0]))
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#تحديد_حد_الإنذارات\n"
                    f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                    f"تم تحديد حد الإنذارات إلى <code>{args[0]}</code>"
                )
        else:
            msg.reply_text("⚠️ أعطني رقم!")
    else:
        limit, _ = sql.get_warn_setting(chat.id)
        msg.reply_text("📊 حد الإنذارات الحالي هو {}".format(limit))
    return ""


# ==================== معالج عربي لحد الإنذارات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_WARNLIMIT_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def arabic_set_warn_limit(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    text = message.text
    for cmd in ARABIC_WARNLIMIT_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        if text.isdigit():
            if int(text) < 3:
                message.reply_text("⚠️ أقل حد للإنذارات هو 3!")
            else:
                sql.set_warn_limit(chat.id, int(text))
                message.reply_text(f"✅ تم تحديث حد الإنذارات إلى {text}")
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#تحديد_حد_الإنذارات\n"
                    f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                    f"تم تحديد حد الإنذارات إلى <code>{text}</code>"
                )
        else:
            message.reply_text("⚠️ أعطني رقم!")
    else:
        limit, _ = sql.get_warn_setting(chat.id)
        message.reply_text(f"📊 حد الإنذارات الحالي هو {limit}")
    return ""


@kigcmd(command='strongwarn', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def set_warn_strength(update: Update, context: CallbackContext):
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].lower() in ("on", "yes", "تفعيل", "نعم"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("⚠️ الإنذارات الكثيرة حتسبب حظر الآن!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"فعّل الإنذارات القوية. الأعضاء حيتحظروا"
            )

        elif args[0].lower() in ("off", "no", "تعطيل", "لا"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "⚠️ الإنذارات الكثيرة حتسبب طرد فقط! العضو يقدر يرجع بعدين."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"عطّل الحظر. حيتم طرد الأعضاء فقط."
            )

        else:
            msg.reply_text("⚠️ أنا أفهم بس: تفعيل/تعطيل أو on/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "📊 الإنذارات حالياً مضبوطة على *طرد* الأعضاء لما يتجاوزوا الحد.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            msg.reply_text(
                "📊 الإنذارات حالياً مضبوطة على *حظر* الأعضاء لما يتجاوزوا الحد.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


# ==================== معالج عربي للإنذار القوي ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_STRONGWARN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def arabic_set_warn_strength(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    text = message.text
    for cmd in ARABIC_STRONGWARN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        if text.lower() in ("on", "yes", "تفعيل", "نعم", "فعل"):
            sql.set_warn_strength(chat.id, False)
            message.reply_text("⚠️ الإنذارات الكثيرة حتسبب حظر الآن!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"فعّل الإنذارات القوية. الأعضاء حيتحظروا"
            )

        elif text.lower() in ("off", "no", "تعطيل", "لا", "عطل"):
            sql.set_warn_strength(chat.id, True)
            message.reply_text("⚠️ الإنذارات الكثيرة حتسبب طرد فقط!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"عطّل الحظر. حيتم طرد الأعضاء فقط."
            )
        else:
            message.reply_text("⚠️ أنا أفهم بس: تفعيل/تعطيل!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            message.reply_text(
                "📊 الإنذارات حالياً مضبوطة على *طرد* الأعضاء لما يتجاوزوا الحد.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            message.reply_text(
                "📊 الإنذارات حالياً مضبوطة على *حظر* الأعضاء لما يتجاوزوا الحد.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


def __stats__():
    return (
        f"• {sql.num_warns()} إنذار إجمالي، في {sql.num_warn_chats()} مجموعة.\n"
        f"• {sql.num_warn_filters()} فلتر إنذار، في {sql.num_warn_filter_chats()} مجموعة."
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for _ in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"هذي المجموعة فيها `{num_warn_filters}` فلتر إنذار. "
        f"يحتاج `{limit}` إنذار قبل ما العضو *{'يتطرد' if soft_warn else 'يتحظر'}*."
    )


from .language import gs


def get_help(chat):
    return gs(chat, "warns_help")


__mod_name__ = "الإنذارات"
