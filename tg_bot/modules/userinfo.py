# placeholderimport html
from typing import Optional

from telegram import (
    Chat,
    MAX_MESSAGE_LENGTH,
    Message,
    ParseMode,
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    WHITELIST_USERS,
    dispatcher,
    spamcheck,
)
from .helper_funcs.extraction import extract_user
from .helper_funcs.decorators import kigcmd, kigmsg

from .helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
    user_is_admin,
)

# ==================== الأوامر العربية ====================
ARABIC_INFO_COMMANDS = ["معلومات", "معلوماتي", "من_هذا", "هوية"]
ARABIC_ID_COMMANDS = ["ايدي", "الايدي", "آيدي", "رقمي"]
ARABIC_CHATINFO_COMMANDS = ["معلومات_المجموعة", "معلومات_القروب"]


@kigcmd(command="id")
@spamcheck
def get_id(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        
        if message.reply_to_message.forward_from:
            msg = (
                f"👤 <b>المرسل الأصلي:</b> {mention_html(message.reply_to_message.forward_from.id, message.reply_to_message.forward_from.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{message.reply_to_message.forward_from.id}</code>\n\n"
                f"👤 <b>المحوّل:</b> {mention_html(replied_user.id, replied_user.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{replied_user.id}</code>"
            )
        elif message.reply_to_message.sender_chat:
            msg = (
                f"📢 <b>القناة/المجموعة:</b> {message.reply_to_message.sender_chat.title}\n"
                f"🆔 <b>الآيدي:</b> <code>{message.reply_to_message.sender_chat.id}</code>"
            )
        else:
            msg = (
                f"👤 <b>العضو:</b> {mention_html(replied_user.id, replied_user.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{replied_user.id}</code>"
            )
        
        if chat.type != "private":
            msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
        
        message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    elif args:
        user_id = extract_user(message, args)
        if user_id:
            try:
                user_obj = bot.get_chat(user_id)
                msg = (
                    f"👤 <b>العضو:</b> {mention_html(user_obj.id, user_obj.first_name)}\n"
                    f"🆔 <b>الآيدي:</b> <code>{user_obj.id}</code>"
                )
            except BadRequest:
                msg = f"🆔 <b>الآيدي:</b> <code>{user_id}</code>"
            
            if chat.type != "private":
                msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
            
            message.reply_text(msg, parse_mode=ParseMode.HTML)
        else:
            message.reply_text("⚠️ ما قدرت أحدد العضو!")
    
    else:
        msg = (
            f"👤 <b>أنت:</b> {mention_html(user.id, user.first_name)}\n"
            f"🆔 <b>آيديك:</b> <code>{user.id}</code>"
        )
        
        if chat.type != "private":
            msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
        
        message.reply_text(msg, parse_mode=ParseMode.HTML)


# ==================== معالج عربي للآيدي ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_ID_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_get_id(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    text = message.text
    for cmd in ARABIC_ID_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        
        if message.reply_to_message.forward_from:
            msg = (
                f"👤 <b>المرسل الأصلي:</b> {mention_html(message.reply_to_message.forward_from.id, message.reply_to_message.forward_from.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{message.reply_to_message.forward_from.id}</code>\n\n"
                f"👤 <b>المحوّل:</b> {mention_html(replied_user.id, replied_user.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{replied_user.id}</code>"
            )
        elif message.reply_to_message.sender_chat:
            msg = (
                f"📢 <b>القناة/المجموعة:</b> {message.reply_to_message.sender_chat.title}\n"
                f"🆔 <b>الآيدي:</b> <code>{message.reply_to_message.sender_chat.id}</code>"
            )
        else:
            msg = (
                f"👤 <b>العضو:</b> {mention_html(replied_user.id, replied_user.first_name)}\n"
                f"🆔 <b>الآيدي:</b> <code>{replied_user.id}</code>"
            )
        
        if chat.type != "private":
            msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
        
        message.reply_text(msg, parse_mode=ParseMode.HTML)
    
    elif text:
        args = text.split()
        user_id = extract_user(message, args)
        if user_id:
            try:
                user_obj = bot.get_chat(user_id)
                msg = (
                    f"👤 <b>العضو:</b> {mention_html(user_obj.id, user_obj.first_name)}\n"
                    f"🆔 <b>الآيدي:</b> <code>{user_obj.id}</code>"
                )
            except BadRequest:
                msg = f"🆔 <b>الآيدي:</b> <code>{user_id}</code>"
            
            if chat.type != "private":
                msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
            
            message.reply_text(msg, parse_mode=ParseMode.HTML)
        else:
            message.reply_text("⚠️ ما قدرت أحدد العضو!")
    
    else:
        msg = (
            f"👤 <b>أنت:</b> {mention_html(user.id, user.first_name)}\n"
            f"🆔 <b>آيديك:</b> <code>{user.id}</code>"
        )
        
        if chat.type != "private":
            msg += f"\n\n💬 <b>المجموعة:</b> {chat.title}\n🆔 <b>آيدي المجموعة:</b> <code>{chat.id}</code>"
        
        message.reply_text(msg, parse_mode=ParseMode.HTML)


@kigcmd(command="info")
@spamcheck
def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif args:
        user_id = extract_user(message, args)
        if user_id:
            try:
                target_user = bot.get_chat(user_id)
            except BadRequest:
                message.reply_text("⚠️ ما قدرت ألقى هالمستخدم!")
                return
        else:
            message.reply_text("⚠️ ما قدرت أحدد العضو!")
            return
    else:
        target_user = user

    _send_user_info(update, context, target_user, chat)


# ==================== معالج عربي للمعلومات ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_INFO_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_info(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    text = message.text
    for cmd in ARABIC_INFO_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif text:
        args = text.split()
        user_id = extract_user(message, args)
        if user_id:
            try:
                target_user = bot.get_chat(user_id)
            except BadRequest:
                message.reply_text("⚠️ ما قدرت ألقى هالمستخدم!")
                return
        else:
            message.reply_text("⚠️ ما قدرت أحدد العضو!")
            return
    else:
        target_user = user

    _send_user_info(update, context, target_user, chat)


def _send_user_info(update, context, target_user, chat):
    """دالة مشتركة لإرسال معلومات المستخدم"""
    bot = context.bot
    message = update.effective_message

    text = f"<b>╔══════════════╗</b>\n"
    text += f"<b>   📋 معلومات العضو</b>\n"
    text += f"<b>╚══════════════╝</b>\n\n"

    text += f"🆔 <b>الآيدي:</b> <code>{target_user.id}</code>\n"
    text += f"👤 <b>الاسم الأول:</b> {html.escape(target_user.first_name)}\n"

    if target_user.last_name:
        text += f"👤 <b>الاسم الأخير:</b> {html.escape(target_user.last_name)}\n"

    if target_user.username:
        text += f"📎 <b>اليوزر:</b> @{html.escape(target_user.username)}\n"

    text += f"🔗 <b>الرابط:</b> {mention_html(target_user.id, 'رابط الحساب')}\n"

    # التحقق من الرتبة
    if target_user.id == OWNER_ID:
        text += f"\n👑 <b>الرتبة:</b> مالك البوت"
    elif target_user.id in DEV_USERS:
        text += f"\n🛡 <b>الرتبة:</b> مطور"
    elif target_user.id in SUDO_USERS:
        text += f"\n⚡ <b>الرتبة:</b> مستخدم SUDO"
    elif target_user.id in WHITELIST_USERS:
        text += f"\n✅ <b>الرتبة:</b> القائمة البيضاء"

    # معلومات في المجموعة
    if chat.type != "private":
        try:
            member = chat.get_member(target_user.id)
            if member:
                if member.status == "administrator":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> مشرف"
                    if member.custom_title:
                        text += f"\n🏷 <b>اللقب:</b> {html.escape(member.custom_title)}"
                elif member.status == "creator":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> مالك المجموعة"
                    if member.custom_title:
                        text += f"\n🏷 <b>اللقب:</b> {html.escape(member.custom_title)}"
                elif member.status == "member":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> عضو"
                elif member.status == "restricted":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> مقيّد"
                elif member.status == "left":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> غادر"
                elif member.status == "kicked":
                    text += f"\n\n📊 <b>الحالة في المجموعة:</b> محظور"
        except BadRequest:
            pass

    # عدد الإنذارات
    try:
        from .sql import warns_sql
        num_warns, _ = warns_sql.get_warns(target_user.id, chat.id) or (0, [])
        limit, _ = warns_sql.get_warn_setting(chat.id)
        if num_warns:
            text += f"\n⚠️ <b>الإنذارات:</b> {num_warns}/{limit}"
    except:
        pass

    try:
        user_pic = bot.get_user_profile_photos(target_user.id).photos
        if user_pic:
            message.reply_photo(
                user_pic[0][-1].file_id,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            return
    except:
        pass

    message.reply_text(text, parse_mode=ParseMode.HTML)


# ==================== معلومات المجموعة ====================
@kigcmd(command="chatinfo", filters=Filters.chat_type.groups)
@spamcheck
def chat_info(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message

    _send_chat_info(update, context, chat)


@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_CHATINFO_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_chat_info(update: Update, context: CallbackContext):
    chat = update.effective_chat
    _send_chat_info(update, context, chat)


def _send_chat_info(update, context, chat):
    """دالة مشتركة لإرسال معلومات المجموعة"""
    bot = context.bot
    message = update.effective_message

    text = f"<b>╔══════════════╗</b>\n"
    text += f"<b>   💬 معلومات المجموعة</b>\n"
    text += f"<b>╚══════════════╝</b>\n\n"

    text += f"📝 <b>الاسم:</b> {html.escape(chat.title)}\n"
    text += f"🆔 <b>الآيدي:</b> <code>{chat.id}</code>\n"

    if chat.username:
        text += f"📎 <b>اليوزر:</b> @{chat.username}\n"

    if chat.description:
        text += f"📋 <b>الوصف:</b> {html.escape(chat.description[:100])}\n"

    text += f"👥 <b>عدد الأعضاء:</b> {chat.get_member_count()}\n"

    try:
        admins = chat.get_administrators()
        text += f"👮 <b>عدد المشرفين:</b> {len(admins)}\n"

        # عرض المشرفين
        admin_list = []
        creator = None
        for admin in admins:
            if admin.status == "creator":
                creator = admin.user
            elif not admin.user.is_bot:
                admin_list.append(admin.user)

        if creator:
            text += f"\n👑 <b>المالك:</b> {mention_html(creator.id, creator.first_name)}\n"

    except BadRequest:
        pass

    try:
        chat_pic = chat.photo
        if chat_pic:
            pic = bot.get_file(chat_pic.big_file_id)
            message.reply_photo(
                chat_pic.big_file_id,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            return
    except:
        pass

    message.reply_text(text, parse_mode=ParseMode.HTML)


def __stats__():
    return ""


from .language import gs


def get_help(chat):
    return gs(chat, "userinfo_help")


__mod_name__ = "المعلومات"
