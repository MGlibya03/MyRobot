import html
import re
from typing import Optional, Union

from telegram import Message, Chat, Update, User, ChatPermissions
from telegram.utils.helpers import mention_html
from telegram.ext import Filters, CallbackContext
from telegram.error import BadRequest

from .. import WHITELIST_USERS, spamcheck
from .sql.approve_sql import is_approved
from .helper_funcs.chat_status import connection_status
from .helper_funcs.string_handling import extract_time
from .log_channel import loggable
from .sql import antiflood_sql as sql
from .helper_funcs.alternate import send_message
from .helper_funcs.decorators import kigcmd, kigcallback, kigmsg
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin
)


FLOOD_GROUP = -5

# ==================== الأوامر العربية ====================
ARABIC_SETFLOOD_COMMANDS = ["ضبط_الفلود", "تعيين_الفلود", "حد_الفلود"]
ARABIC_FLOOD_COMMANDS = ["الفلود", "فلود", "انتي_فلود"]
ARABIC_FLOODMODE_COMMANDS = ["وضع_الفلود", "نوع_الفلود"]

# ترجمة أوضاع الفلود
FLOOD_MODES_AR = {
    "حظر": "ban",
    "طرد": "kick", 
    "كتم": "mute",
    "حظر_مؤقت": "tban",
    "كتم_مؤقت": "tmute",
}


def mention_html_chat(chat_id: Union[int, str], name: str) -> str:
    return f'<a href="tg://t.me/{chat_id}">{html.escape(name)}</a>'


@kigmsg(
        (Filters.all
         & Filters.chat_type.groups
         & ~Filters.status_update
         & ~Filters.update.edited_message
         & ~Filters.sender_chat.channel),
        run_async=True, group=FLOOD_GROUP)
@connection_status
@loggable
def check_flood(update: Update, context: CallbackContext) -> Optional[str]:
    global execstrings
    tag = "None"
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins and whitelists
    if user_is_admin(update, user.id, channels = True) or user.id in WHITELIST_USERS:
        sql.update_flood(chat.id, None)
        return ""

    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.ban_member(user.id)
            execstrings = "تم حظره"
            tag = "حظر"
        elif getmode == 2:
            chat.ban_member(user.id)
            chat.unban_member(user.id)
            execstrings = "تم طرده"
            tag = "طرد"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id, user.id, permissions=ChatPermissions(can_send_messages=False)
            )
            execstrings = "تم كتمه"
            tag = "كتم"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.ban_member(user.id, until_date=bantime)
            execstrings = "تم حظره لمدة {}".format(getvalue)
            tag = "حظر_مؤقت"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "تم كتمه لمدة {}".format(getvalue)
            tag = "كتم_مؤقت"
        send_message(
            update.effective_message, "🚫 *تم تفعيل مكافحة الفلود!*\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>العضو:</b> {}"
            "\nسبام في المجموعة.".format(
                tag, html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    except BadRequest:
        msg.reply_text(
            "⚠️ ما أقدر أقيد الأعضاء هني، أعطني الصلاحيات أول! لحد ما تسويها، حنعطل مكافحة الفلود."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#معلومات"
            "\nما عندي صلاحيات كافية لتقييد الأعضاء فتم تعطيل مكافحة الفلود تلقائياً".format(
                chat.title
            )
        )


@kigmsg(
        (Filters.all
         & ~Filters.status_update
         & Filters.chat_type.groups
         & ~Filters.update.edited_message
         & Filters.sender_chat.channel),
        run_async=True, group=-6)
@connection_status
@loggable
def check_channel_flood(update: Update, _: CallbackContext) -> Optional[str]:
    global execstrings
    msg = update.effective_message  # type: Optional[Message]
    user = msg.sender_chat  # type: Optional[Chat]
    chat = update.effective_chat  # type: Optional[Chat]
    if not user:  # only for channels
        return ""

    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.ban_sender_chat(user.id)
        execstrings = "تم حظر القناة: " + user.title
        tag = "حظر"
        send_message(
            update.effective_message, "🚫 *تم تفعيل مكافحة الفلود!*\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>القناة:</b> {}"
            "\nسبام في المجموعة.".format(
                tag, html.escape(chat.title), mention_html_chat(user.id, user.title)
            )
        )

    except BadRequest:
        msg.reply_text(
            "⚠️ ما أقدر أقيد الأعضاء هني، أعطني الصلاحيات أول! لحد ما تسويها، حنعطل مكافحة الفلود."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#معلومات"
            "\nما عندي صلاحيات كافية لتقييد الأعضاء فتم تعطيل مكافحة الفلود تلقائياً".format(
                chat.title
            )
        )


@kigcallback(pattern=r"unmute_flooder")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply = True)
@loggable
def flood_button(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    admeme = chat.get_member(user.id)
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)

    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            update.effective_message.edit_text(
                f"✅ تم فك الكتم{f' بواسطة {mention_html(user.id, user.first_name)}' if not admeme.is_anonymous else ''}.",
                parse_mode="HTML",
            )
            logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#فك_كتم_فلود\n"
                    f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                    f"<b>العضو:</b> {mention_html(user_id, html.escape(chat.get_member(user_id).first_name))}\n"
            )
            return logmsg
        except Exception as e:
            update.effective_message.edit_text("⚠️ حصل خطأ أثناء فك الكتم!\n<code>{}</code>".format(e))


@kigcmd(command='setflood', pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def set_flood(update, context) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    user = update.effective_user  # type: Optional[User]
    chat_name = chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0", "لا", "تعطيل", "ايقاف"]:
            sql.set_flood(chat.id, 0)
            message.reply_text("✅ تم تعطيل مكافحة الفلود.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("✅ تم تعطيل مكافحة الفلود.")
                return (
                    "<b>{}:</b>"
                    "\n#ضبط_الفلود"
                    "\n<b>المشرف:</b> {}"
                    "\nتم تعطيل مكافحة الفلود.".format(
                        html.escape(chat_name), mention_html(user.id, user.first_name)
                    )
                )

            elif amount <= 3:
                send_message(
                    update.effective_message,
                    "⚠️ حد الفلود لازم يكون 0 (معطل) أو رقم أكبر من 3!",
                )
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("✅ تم تحديث حد مكافحة الفلود إلى {}!".format(amount))
                return (
                    "<b>{}:</b>"
                    "\n#ضبط_الفلود"
                    "\n<b>المشرف:</b> {}"
                    "\nتم ضبط مكافحة الفلود على <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        amount,
                    )
                )

        else:
            message.reply_text("⚠️ قيمة غير صحيحة! استخدم رقم أو 'تعطيل' أو 'لا'")
    else:
        message.reply_text(
                "استخدم `/setflood رقم` أو `ضبط_الفلود رقم` لتفعيل مكافحة الفلود.\n"
                "أو استخدم `/setflood off` أو `ضبط_الفلود تعطيل` لتعطيلها!",
            parse_mode="markdown",
        )
    return ""


# ==================== معالج عربي لضبط الفلود ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_SETFLOOD_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def arabic_set_flood(update, context) -> Optional[str]:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    chat_name = chat.title

    text = message.text
    for cmd in ARABIC_SETFLOOD_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        val = text.lower()
        if val in ["off", "no", "0", "لا", "تعطيل", "ايقاف", "اوقف"]:
            sql.set_flood(chat.id, 0)
            message.reply_text("✅ تم تعطيل مكافحة الفلود.")
            return (
                "<b>{}:</b>"
                "\n#ضبط_الفلود"
                "\n<b>المشرف:</b> {}"
                "\nتم تعطيل مكافحة الفلود.".format(
                    html.escape(chat_name), mention_html(user.id, user.first_name)
                )
            )

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("✅ تم تعطيل مكافحة الفلود.")
                return (
                    "<b>{}:</b>"
                    "\n#ضبط_الفلود"
                    "\n<b>المشرف:</b> {}"
                    "\nتم تعطيل مكافحة الفلود.".format(
                        html.escape(chat_name), mention_html(user.id, user.first_name)
                    )
                )

            elif amount <= 3:
                message.reply_text("⚠️ حد الفلود لازم يكون 0 (معطل) أو رقم أكبر من 3!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("✅ تم تحديث حد مكافحة الفلود إلى {}!".format(amount))
                return (
                    "<b>{}:</b>"
                    "\n#ضبط_الفلود"
                    "\n<b>المشرف:</b> {}"
                    "\nتم ضبط مكافحة الفلود على <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        amount,
                    )
                )

        else:
            message.reply_text("⚠️ قيمة غير صحيحة! استخدم رقم أو 'تعطيل' أو 'لا'")
    else:
        message.reply_text(
            "📊 استخدم:\n"
            "• `ضبط_الفلود 5` - لتفعيل مكافحة الفلود (5 رسائل)\n"
            "• `ضبط_الفلود تعطيل` - لتعطيل مكافحة الفلود",
            parse_mode="markdown",
        )
    return ""


@kigcmd(command="flood")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check()
@spamcheck
def flood(update: Update, _: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message

    limit = sql.get_flood_limit(chat.id)
    flood_type = get_flood_type(chat.id)
    if limit == 0:
        msg.reply_text("📊 مكافحة الفلود معطلة حالياً!")

    else:
        msg.reply_text(
            "📊 حالياً أقيد الأعضاء بعد {} رسائل متتالية.\n"
            "وضع الفلود الحالي: {}".format(limit, flood_type)
        )


# ==================== معالج عربي لعرض الفلود ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_FLOOD_COMMANDS) + r')$'), group=3)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check()
@spamcheck
def arabic_flood(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    limit = sql.get_flood_limit(chat.id)
    flood_type = get_flood_type(chat.id)
    if limit == 0:
        msg.reply_text("📊 مكافحة الفلود معطلة حالياً!")
    else:
        msg.reply_text(
            "📊 حالياً أقيد الأعضاء بعد {} رسائل متتالية.\n"
            "وضع الفلود الحالي: {}".format(limit, flood_type)
        )


@kigcmd(command=["setfloodmode", "floodmode"], pass_args=True)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@connection_status
@loggable
def set_flood_mode(update, context) -> Optional[str]:  # sourcery no-metrics
    global settypeflood
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat
    msg = update.effective_message

    if args := context.args:
        mode = args[0].lower()
        
        # تحويل العربي للإنجليزي
        if mode in FLOOD_MODES_AR:
            mode = FLOOD_MODES_AR[mode]
        
        if mode == "ban":
            settypeflood = "حظر"
            sql.set_flood_strength(chat.id, 1, "0")
        elif mode == "kick":
            settypeflood = "طرد"
            sql.set_flood_strength(chat.id, 2, "0")
        elif mode == "mute":
            settypeflood = "كتم"
            sql.set_flood_strength(chat.id, 3, "0")
        elif mode == "tban":
            if len(args) == 1:
                send_message(update.effective_message, tflood_help_msg.format("حظر مؤقت"), parse_mode="markdown")
                return
            settypeflood = "حظر مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat.id, 4, str(args[1]))
        elif mode == "tmute":
            if len(args) == 1:
                send_message(update.effective_message, tflood_help_msg.format("كتم مؤقت"), parse_mode="markdown")
                return
            settypeflood = "كتم مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat.id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message, "⚠️ أنا أفهم بس: حظر/طرد/كتم/حظر_مؤقت/كتم_مؤقت!"
            )
            return
        msg.reply_text("✅ تجاوز حد الفلود حيسبب {}!".format(settypeflood))
        return (
            "<b>{}:</b>\n"
            "#وضع_الفلود\n"
            "<b>المشرف:</b> {}\n"
            "وضع الفلود الجديد: {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeflood,
            )
        )
    else:
        flood_type = get_flood_type(chat.id)
        msg.reply_text("📊 إرسال رسائل أكثر من حد الفلود حيسبب {}.".format(flood_type))

    return ""


# ==================== معالج عربي لوضع الفلود ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_FLOODMODE_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@connection_status
@loggable
def arabic_set_flood_mode(update, context) -> Optional[str]:
    global settypeflood
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    text = msg.text
    for cmd in ARABIC_FLOODMODE_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        args = text.split()
        mode = args[0].lower()
        
        # تحويل العربي للإنجليزي
        if mode in FLOOD_MODES_AR:
            mode = FLOOD_MODES_AR[mode]
        
        if mode == "ban" or mode == "حظر":
            settypeflood = "حظر"
            sql.set_flood_strength(chat.id, 1, "0")
        elif mode == "kick" or mode == "طرد":
            settypeflood = "طرد"
            sql.set_flood_strength(chat.id, 2, "0")
        elif mode == "mute" or mode == "كتم":
            settypeflood = "كتم"
            sql.set_flood_strength(chat.id, 3, "0")
        elif mode == "tban" or mode == "حظر_مؤقت":
            if len(args) == 1:
                send_message(msg, tflood_help_msg.format("حظر مؤقت"), parse_mode="markdown")
                return
            settypeflood = "حظر مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat.id, 4, str(args[1]))
        elif mode == "tmute" or mode == "كتم_مؤقت":
            if len(args) == 1:
                send_message(msg, tflood_help_msg.format("كتم مؤقت"), parse_mode="markdown")
                return
            settypeflood = "كتم مؤقت لمدة {}".format(args[1])
            sql.set_flood_strength(chat.id, 5, str(args[1]))
        else:
            send_message(msg, "⚠️ أنا أفهم بس: حظر/طرد/كتم/حظر_مؤقت/كتم_مؤقت!")
            return
        msg.reply_text("✅ تجاوز حد الفلود حيسبب {}!".format(settypeflood))
        return (
            "<b>{}:</b>\n"
            "#وضع_الفلود\n"
            "<b>المشرف:</b> {}\n"
            "وضع الفلود الجديد: {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeflood,
            )
        )
    else:
        flood_type = get_flood_type(chat.id)
        msg.reply_text(
            "📊 إرسال رسائل أكثر من حد الفلود حيسبب {}.\n\n"
            "الأوضاع المتاحة:\n"
            "• حظر - حظر العضو\n"
            "• طرد - طرد العضو\n"
            "• كتم - كتم العضو\n"
            "• حظر_مؤقت 1h - حظر مؤقت\n"
            "• كتم_مؤقت 1h - كتم مؤقت".format(flood_type)
        )

    return ""


def get_flood_type(chat_id: int) -> str:
    global settypeflood
    getmode, getvalue = sql.get_flood_setting(chat_id)
    if getmode == 1:
        settypeflood = "حظر"
    elif getmode == 2:
        settypeflood = "طرد"
    elif getmode == 3:
        settypeflood = "كتم"
    elif getmode == 4:
        settypeflood = "حظر مؤقت لمدة {}".format(getvalue)
    elif getmode == 5:
        settypeflood = "كتم مؤقت لمدة {}".format(getvalue)
    return settypeflood


tflood_help_msg = ("⚠️ يبدو إنك حاولت تحدد وقت لمكافحة الفلود لكن ما حددت المدة؛ "
                   "جرب `وضع_الفلود {} <المدة>`.\n"
                   "أمثلة على المدة: 4m = 4 دقائق، 3h = 3 ساعات، 6d = 6 أيام، 5w = 5 أسابيع.")


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "مكافحة الفلود معطلة."
    else:
        return "مكافحة الفلود مضبوطة على `{}`.".format(limit)


from .language import gs


def get_help(chat):
    return gs(chat, "antiflood_help")


__mod_name__ = "مكافحة الفلود"
