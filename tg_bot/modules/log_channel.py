from datetime import datetime
from functools import wraps
from tg_bot import OWNER_ID, spamcheck

from telegram.ext import CallbackContext
from .helper_funcs.decorators import kigcmd, kigcallback
from .helper_funcs.misc import is_module_loaded
from .language import gs
from telegram.error import Unauthorized
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)


def get_help(chat):
    return gs(chat, "log_help")


FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import ParseMode, Update, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.error import BadRequest, Unauthorized
    from telegram.utils.helpers import escape_markdown

    from tg_bot import GBAN_LOGS, log, dispatcher
    from .sql import log_channel_sql as sql


    def loggable(func):
        @wraps(func)
        def log_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>⏰ الوقت</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                try:
                    if message.chat.type == chat.SUPERGROUP:
                        if message.chat.username:
                            result += f'\n<b>🔗 الرابط:</b> <a href="https://t.me/{chat.username}/{message.message_id}">اضغط هنا</a>'
                        else:
                            cid = str(chat.id).replace("-100", '')
                            result += f'\n<b>🔗 الرابط:</b> <a href="https://t.me/c/{cid}/{message.message_id}">اضغط هنا</a>'
                except AttributeError:
                    result += '\n<b>🔗 الرابط:</b> ما فيش رابط للإجراءات اليدوية.'
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return log_action


    def gloggable(func):
        @wraps(func)
        def glog_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>⏰ الوقت</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt)
                )

                if message.chat.type == chat.SUPERGROUP:
                    if message.chat.username:
                        result += f'\n<b>🔗 الرابط:</b> <a href="https://t.me/{chat.username}/{message.message_id}">اضغط هنا</a>'
                    else:
                        cid = str(chat.id).replace("-100", '')
                        result += f'\n<b>🔗 الرابط:</b> <a href="https://t.me/c/{cid}/{message.message_id}">اضغط هنا</a>'
                log_chat = GBAN_LOGS or OWNER_ID
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action


    def send_log(
            context: CallbackContext, log_chat_id: str, orig_chat_id: str, result: str
    ):
        bot = context.bot
        try:
            bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id, "❌ قناة السجل هذي تمسحت - راح نشيل الإعداد."
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                log.warning(excp.message)
                log.warning(result)
                log.exception("Could not parse")

                bot.send_message(
                    log_chat_id,
                    result
                    + "\n\n⚠️ التنسيق تعطل بسبب خطأ غير متوقع.",
                )
        except Unauthorized as excp:
            if excp.message == "bot is not a member of the channel chat":
                bot.send_message(
                    orig_chat_id, "❌ ما عندي صلاحية للوصول لقناة السجل - راح نشيل الإعداد."
                )
                sql.stop_chat_logging(orig_chat_id)


    @kigcmd(command='logchannel')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                f"📋 هذا القروب كل سجلاته تتبعث لـ:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            message.reply_text("❌ ما تم تحديد قناة سجل لهذا القروب!")


    @kigcmd(command='setlog')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "📌 توا، حوّل الـ /setlog للقروب اللي تبي تربطه بهالقناة!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message != 'Message to delete not found':
                    log.exception(
                        'خطأ في مسح الرسالة في قناة السجل. المفروض يشتغل على أي حال.'
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    f"✅ هالقناة تم تعيينها كقناة سجل لـ {chat.title or chat.first_name}.",
                )
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "✅ تم تعيين قناة السجل بنجاح!")
                else:
                    log.exception("خطأ في تعيين قناة السجل.")

            bot.send_message(chat.id, "✅ تم تعيين قناة السجل بنجاح!")

        else:
            message.reply_text(
                "📝 الخطوات باش تعيّن قناة سجل:\n"
                " - أضف البوت للقناة اللي تبيها (كأدمن!)\n"
                " - أرسل /setlog فالقناة\n"
                " - حوّل رسالة الـ /setlog للقروب\n"
            )


    @kigcmd(command='unsetlog')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(
                log_channel, f"📤 القناة تم فصلها عن {chat.title}"
            )
            message.reply_text("✅ تم إلغاء تعيين قناة السجل.")

        else:
            message.reply_text("❌ ما تم تعيين قناة سجل بعد!")


    def __stats__():
        return f"• {sql.num_logchannels()} قناة سجل معينة."


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"📋 هذا القروب كل سجلاته تتبعث لـ: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "❌ ما فيش قناة سجل معينة لهذا القروب!"


    __help__ = """
*للأدمنية فقط:*
• `/logchannel`*:* عرض معلومات قناة السجل
• `/setlog`*:* تعيين قناة السجل
• `/unsetlog`*:* إلغاء تعيين قناة السجل

طريقة تعيين قناة السجل:
• أضف البوت للقناة اللي تبيها (كأدمن!)
• أرسل `/setlog` فالقناة
• حوّل رسالة الـ `/setlog` للقروب
"""

    __mod_name__ = "📋 السجل"

else:
    # يشتغل على أي حال لو الموديول مش محمّل
    def loggable(func):
        return func


    def gloggable(func):
        return func


@kigcmd("logsettings")
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def log_settings(update: Update, _: CallbackContext):
    chat = update.effective_chat
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    message = update.effective_message
    user = update.effective_user
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(chat.id, True, True, True, True, True))
    btn = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="⚠️ التحذيرات", callback_data="log_tog_warn"),
                InlineKeyboardButton(text="⚡ الإجراءات", callback_data="log_tog_act")
            ],
            [
                InlineKeyboardButton(text="📥 الدخول", callback_data="log_tog_join"),
                InlineKeyboardButton(text="📤 الخروج", callback_data="log_tog_leave")
            ],
            [
                InlineKeyboardButton(text="🚨 البلاغات", callback_data="log_tog_rep")
            ]
        ]
    )
    msg = update.effective_message
    msg.reply_text("⚙️ تبديل إعدادات سجل القناة", reply_markup=btn)


from .sql import log_channel_sql as sql


@kigcallback(pattern=r"log_tog_.*")
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, noreply=True)
def log_setting_callback(update: Update, context: CallbackContext):
    cb = update.callback_query
    user = cb.from_user
    chat = cb.message.chat
    setting = cb.data.replace("log_tog_", "")
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(chat.id, True, True, True, True, True))

    t = sql.get_chat_setting(chat.id)
    if setting == "warn":
        r = t.toggle_warn()
        cb.answer("سجل التحذيرات: {}".format("✅ مفعّل" if r else "❌ معطّل"))
        return
    if setting == "act":
        r = t.toggle_action()
        cb.answer("سجل الإجراءات: {}".format("✅ مفعّل" if r else "❌ معطّل"))
        return
    if setting == "join":
        r = t.toggle_joins()
        cb.answer("سجل الدخول: {}".format("✅ مفعّل" if r else "❌ معطّل"))
        return
    if setting == "leave":
        r = t.toggle_leave()
        cb.answer("سجل الخروج: {}".format("✅ مفعّل" if r else "❌ معطّل"))
        return
    if setting == "rep":
        r = t.toggle_report()
        cb.answer("سجل البلاغات: {}".format("✅ مفعّل" if r else "❌ معطّل"))
        return

    cb.answer("🤔 ما فهمت شنو تبي")
