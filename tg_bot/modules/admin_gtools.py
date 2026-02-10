import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html
from telegram.vendor.ptb_urllib3.urllib3.packages.six import BytesIO

from .. import spamcheck
from .log_channel import loggable
from .helper_funcs.decorators import kigcmd
from .helper_funcs.chat_status import connection_status
from .helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms



@kigcmd(command='setgpic', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def setpic(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if (
        not msg.reply_to_message
        and not msg.reply_to_message.document
        and not msg.reply_to_message.photo
    ):
        msg.reply_text("📷 أرسل صورة أو ملف ورد عليه باش نحطها صورة القروب!")
        return ""

    if msg.reply_to_message.photo:
        file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.reply_to_message.document:
        file_id = msg.reply_to_message.document.file_id

    try:
        image_file = context.bot.get_file(file_id)
        image_data = image_file.download(out=BytesIO())
        image_data.seek(0)

        bot.set_chat_photo(chat.id, image_data)
        msg.reply_text(
                f"✅ <b>{user.first_name}</b> غيّر صورة القروب."
                if not msg.sender_chat else "✅ صورة القروب تغيرت.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#أدمن\nصورة القروب تغيرت\n"
            f"<b>الأدمن:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("❌ صار خطأ:\n" + str(e))
        return ''



@kigcmd(command='delgpic', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def delpic(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    try:
        bot.delete_chat_photo(chat.id)
        msg.reply_text(
                f"✅ <b>{user.first_name}</b> مسح صورة القروب."
                if not msg.sender_chat else "✅ صورة القروب تمسحت.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#أدمن\nصورة القروب تمسحت\n"
            f"<b>الأدمن:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("❌ صار خطأ:\n" + str(e))
        return ''


@kigcmd(command='setgtitle', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def set_title(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        msg.reply_text("❌ ما كتبت اسم جديد للقروب!")
        return ""

    try:
        bot.set_chat_title(chat.id, title)
        if len(title) > 255:
            msg.reply_text("⚠️ الاسم أطول من 255 حرف، راح نقصه لـ 255 حرف!")
        msg.reply_text(
                f"✅ <b>{user.first_name}</b> غيّر اسم القروب لـ:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"✅ اسم القروب تغير لـ:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#أدمن\nاسم القروب تغير\n"
            f"<b>الأدمن:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("❌ صار خطأ:\n" + str(e))
        return ''

@kigcmd(command='setgdesc', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def set_desc(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        msg.reply_text("❌ ما كتبت وصف جديد للقروب!")
        return ""

    try:
        bot.set_chat_description(chat.id, title)
        if len(title) > 255:
            msg.reply_text("⚠️ الوصف أطول من 255 حرف، راح نقصه لـ 255 حرف!")
        msg.reply_text(
                f"✅ <b>{user.first_name}</b> غيّر وصف القروب لـ:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"✅ وصف القروب تغير لـ:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#أدمن\nوصف القروب تغير\n"
            f"<b>الأدمن:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("❌ صار خطأ:\n" + str(e))
        return ''


@kigcmd(command=['setgstickers', 'setgsticker'], run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def set_stk_set(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            msg.reply_text("📌 رد على ملصق باش نحط باكته كباكة ملصقات القروب!")
            return ""
        msg.reply_text("📌 رد على ملصق باش نحط باكته كباكة ملصقات القروب!")
        return ""

    try:
        stk_set = msg.reply_to_message.sticker.set_name
        bot.set_chat_sticker_set(chat.id, stk_set)
        msg.reply_text(
                f"✅ <b>{user.first_name}</b> غيّر باكة ملصقات القروب."
                if not msg.sender_chat else "✅ باكة ملصقات القروب تغيرت.",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#أدمن\nباكة ملصقات القروب تغيرت\n"
            f"<b>الأدمن:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        if e.message == 'Participants_too_few':
            errmsg = "⚠️ معذرة، تيليجرام يطلب على الأقل 100 عضو فالقروب باش تقدر تحط باكة ملصقات!"
        else:
            errmsg = f"❌ صار خطأ:\n{str(e)}"
        msg.reply_text(errmsg)
        return ''
