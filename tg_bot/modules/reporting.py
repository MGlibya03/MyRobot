import html

from tg_bot import log, SUDO_USERS, WHITELIST_USERS, spamcheck
from .log_channel import loggable
from .sql import reporting_sql as sql
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    Filters,
)
import tg_bot.modules.sql.log_channel_sql as logsql
from telegram.utils.helpers import mention_html
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_not_admin_check,
    A_CACHE
)

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = SUDO_USERS + WHITELIST_USERS

# ==================== الأوامر العربية ====================
ARABIC_REPORTS_COMMANDS = ["البلاغات", "حالة_البلاغات", "اعدادات_البلاغات"]
ARABIC_REPORT_COMMANDS = ["بلاغ", "ابلاغ", "شكوى", "بلغ"]


@kigcmd(command='reports', run_async=True)
@spamcheck
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if len(args) >= 1:
        if args[0] in ("yes", "on", "تفعيل", "نعم", "فعل"):
            sql.set_chat_setting(chat.id, True)
            msg.reply_text(
                "✅ تم تفعيل البلاغات! المشرفين اللي فعّلوا البلاغات حيتم إبلاغهم لما أحد يكتب بلاغ أو /report "
                "أو @admin."
            )

        elif args[0] in ("no", "off", "تعطيل", "لا", "عطل"):
            sql.set_chat_setting(chat.id, False)
            msg.reply_text(
                "✅ تم تعطيل البلاغات! ما حد حيتم إبلاغه."
            )
    else:
        msg.reply_text(
            f"📊 إعدادات البلاغات في هالمجموعة: `{sql.chat_should_report(chat.id)}`",
            parse_mode=ParseMode.MARKDOWN,
        )


# ==================== معالج عربي لإعدادات البلاغات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_REPORTS_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
def arabic_report_setting(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    text = msg.text
    for cmd in ARABIC_REPORTS_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    if text:
        if text.lower() in ("yes", "on", "تفعيل", "نعم", "فعل"):
            sql.set_chat_setting(chat.id, True)
            msg.reply_text(
                "✅ تم تفعيل البلاغات! المشرفين حيتم إبلاغهم لما أحد يكتب بلاغ أو @admin."
            )

        elif text.lower() in ("no", "off", "تعطيل", "لا", "عطل"):
            sql.set_chat_setting(chat.id, False)
            msg.reply_text("✅ تم تعطيل البلاغات! ما حد حيتم إبلاغه.")
    else:
        msg.reply_text(
            f"📊 إعدادات البلاغات في هالمجموعة: `{sql.chat_should_report(chat.id)}`\n\n"
            "الاستخدام:\n"
            "• `البلاغات تفعيل` - تفعيل البلاغات\n"
            "• `البلاغات تعطيل` - تعطيل البلاغات",
            parse_mode=ParseMode.MARKDOWN,
        )


@kigcmd(command='report', filters=Filters.chat_type.groups, group=REPORT_GROUP, run_async=True)
@kigmsg((Filters.regex(r"(?i)@admin(s)?|@مشرف|@ادمن")), group=REPORT_GROUP, run_async=True)
@spamcheck
@user_not_admin_check
@loggable
def report(update: Update, context: CallbackContext) -> str:
    # sourcery no-metrics
    global reply_markup
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(logsql.LogChannelSettings(chat.id, True, True, True, True, True))
        log_setting = logsql.get_chat_setting(chat.id)

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user

        if user.id == reported_user.id:
            message.reply_text("⚠️ تبي تبلّغ عن نفسك؟ 😄")
            return ""

        if reported_user.id == bot.id:
            message.reply_text("😄 محاولة حلوة!")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("⚠️ تبي تبلّغ عن مستخدم محمي؟")
            return ""

        admin_list = [i.user.id for i in A_CACHE[chat.id] if not (i.user.is_bot or i.is_anonymous)]

        if reported_user.id in admin_list:
            message.reply_text("⚠️ ليش تبي تبلّغ عن مشرف؟")
            return ""

        if message.sender_chat:
            reported = "✅ تم الإبلاغ للمشرفين."
            for admin in admin_list:
                try:
                    reported += f"<a href=\"tg://user?id={admin}\">\u2063</a>"
                except BadRequest:
                    log.exception(f"Exception while reporting user: {user} in chat: {chat.id}")
            message.reply_text(reported, parse_mode = ParseMode.HTML)

        message = update.effective_message
        msg = (
            f"<b>⚠️ بلاغ جديد: </b>{html.escape(chat.title)}\n"
            f"<b> • المبلّغ:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
            f"<b> • المبلّغ عنه:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
        )
        tmsg = ""
        for admin in admin_list:
            link = mention_html(admin, "​")  # contains 0 width characters
            tmsg += link

        keyboard2 = [
            [
                InlineKeyboardButton(
                    "⚠ طرد",
                    callback_data=f"reported_{chat.id}=kick={reported_user.id}",
                ),
                InlineKeyboardButton(
                    "⛔️ حظر",
                    callback_data=f"reported_{chat.id}=banned={reported_user.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❎ حذف الرسالة",
                    callback_data=f"reported_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                ),
                InlineKeyboardButton(
                    "❌ إغلاق",
                    callback_data=f"reported_{chat.id}=close={reported_user.id}",
                )
            ],
            [
                InlineKeyboardButton(
                        "📝 اقرأ القوانين", url="t.me/{}?start={}".format(bot.username, chat.id)
                    )
            ],
        ]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        reportmsg = f"✅ تم الإبلاغ عن {mention_html(reported_user.id, reported_user.first_name)} للمشرفين."
        reportmsg += tmsg
        message.reply_text(
            reportmsg,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup2
        )
        if not log_setting.log_report:
            return ""
        return msg
    return ""


# ==================== معالج عربي للبلاغ ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_REPORT_COMMANDS) + r')$'), group=REPORT_GROUP)
@spamcheck
@user_not_admin_check
@loggable
def arabic_report(update: Update, context: CallbackContext) -> str:
    global reply_markup
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(logsql.LogChannelSettings(chat.id, True, True, True, True, True))
        log_setting = logsql.get_chat_setting(chat.id)

    if not message.reply_to_message:
        message.reply_text("⚠️ رد على رسالة العضو اللي تبي تبلّغ عنه!")
        return ""

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user

        if user.id == reported_user.id:
            message.reply_text("⚠️ تبي تبلّغ عن نفسك؟ 😄")
            return ""

        if reported_user.id == bot.id:
            message.reply_text("😄 محاولة حلوة!")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("⚠️ تبي تبلّغ عن مستخدم محمي؟")
            return ""

        admin_list = [i.user.id for i in A_CACHE[chat.id] if not (i.user.is_bot or i.is_anonymous)]

        if reported_user.id in admin_list:
            message.reply_text("⚠️ ليش تبي تبلّغ عن مشرف؟")
            return ""

        msg = (
            f"<b>⚠️ بلاغ جديد: </b>{html.escape(chat.title)}\n"
            f"<b> • المبلّغ:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
            f"<b> • المبلّغ عنه:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
        )
        tmsg = ""
        for admin in admin_list:
            link = mention_html(admin, "​")
            tmsg += link

        keyboard2 = [
            [
                InlineKeyboardButton(
                    "⚠ طرد",
                    callback_data=f"reported_{chat.id}=kick={reported_user.id}",
                ),
                InlineKeyboardButton(
                    "⛔️ حظر",
                    callback_data=f"reported_{chat.id}=banned={reported_user.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❎ حذف الرسالة",
                    callback_data=f"reported_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                ),
                InlineKeyboardButton(
                    "❌ إغلاق",
                    callback_data=f"reported_{chat.id}=close={reported_user.id}",
                )
            ],
            [
                InlineKeyboardButton(
                        "📝 اقرأ القوانين", url="t.me/{}?start={}".format(bot.username, chat.id)
                    )
            ],
        ]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        reportmsg = f"✅ تم الإبلاغ عن {mention_html(reported_user.id, reported_user.first_name)} للمشرفين."
        reportmsg += tmsg
        message.reply_text(
            reportmsg,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup2
        )
        if not log_setting.log_report:
            return ""
        return msg
    return ""


@kigcallback(pattern=r"reported_")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods=True, noreply = True)
def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("reported_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.ban_chat_member(splitter[0], splitter[2])
            bot.unban_chat_member(splitter[0], splitter[2])
            query.answer("✅ تم الطرد بنجاح!")
            return ""
        except Exception as err:
            query.answer(f"🛑 فشل الطرد\n{err}")
    elif splitter[1] == "banned":
        try:
            bot.ban_chat_member(splitter[0], splitter[2])
            query.answer("✅ تم الحظر بنجاح!")
            return ""
        except Exception as err:
            query.answer(f"🛑 فشل الحظر\n{err}", show_alert=True)
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ تم حذف الرسالة!")
            
            kyb_no_del = [
                [
                    InlineKeyboardButton(
                        "⚠ طرد",
                        callback_data=f"reported_{splitter[0]}=kick={splitter[2]}",
                    ),
                    InlineKeyboardButton(
                        "⛔️ حظر",
                        callback_data=f"reported_{splitter[0]}=banned={splitter[2]}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❌ إغلاق",
                        callback_data=f"reported_{splitter[0]}=close={splitter[2]}",
                    )
                ],
                [
                    InlineKeyboardButton(
                            "📝 اقرأ القوانين", url="t.me/{}?start={}".format(bot.username, splitter[0]),
                        )
                ],
            ]
            
            query.edit_message_reply_markup(
                InlineKeyboardMarkup(kyb_no_del)
            )
            return ""
        except Exception as err:
            query.answer(
                text=f"🛑 فشل حذف الرسالة!\n{err}",
                show_alert=True
            )
    elif splitter[1] == "close":
        try:
            query.answer("✅ تم إغلاق اللوحة!")
            
            kyb_no_del = [
                [
                    InlineKeyboardButton(
                            "📝 اقرأ القوانين", url="t.me/{}?start={}".format(bot.username, splitter[0]),
                        )
                ],
            ]
            
            query.edit_message_reply_markup(
                InlineKeyboardMarkup(kyb_no_del)
            )
            return ""
        except Exception as err:
            query.answer(
                text=f"🛑 فشل إغلاق اللوحة!\n{err}",
                show_alert=True
            )


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"📊 هالمجموعة مضبوطة لإرسال بلاغات الأعضاء للمشرفين عبر بلاغ أو /report أو @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        return "📊 حتوصلك بلاغات من المجموعات اللي أنت مشرف فيها."
    else:
        return "📊 *مش* حتوصلك بلاغات من المجموعات اللي أنت مشرف فيها."


from .language import gs


def get_help(chat):
    return gs(chat, "reports_help")


__mod_name__ = "البلاغات"
