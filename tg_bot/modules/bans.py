import html
from typing import Optional, Union

from telegram import Bot, Chat, ChatMember, Message, Update, ParseMode, User
from telegram.error import BadRequest
from telegram.ext import Filters, CallbackContext
from telegram.utils.helpers import mention_html

from tg_bot import (
    BAN_STICKER,
    DEV_USERS,
    MESSAGE_DUMP,
    MOD_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    OWNER_ID,
    SYS_ADMIN,
    WHITELIST_USERS,
    spamcheck,
    log
)

from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_user_and_text
from .helper_funcs.string_handling import extract_time
from .log_channel import loggable, gloggable
from .helper_funcs.decorators import kigcmd

def cannot_ban(banner_id, user_id, message) -> bool:
    if banner_id in DEV_USERS:
        if user_id not in DEV_USERS:
            return False
        else:
            message.reply_text("علاش تبي تحظر مطور ثاني؟ 🤔")
            return True
    else:
        if user_id == OWNER_ID:
            message.reply_text("مستحيل نحظر صاحبي! 👑")
            return True
        elif user_id in DEV_USERS:
            message.reply_text("هذا واحد من المطورين حقي، ما نقدرش نتصرف ضده! 👨‍💻")
            return True
        elif user_id in SUDO_USERS:
            message.reply_text("السودو حقي محميين من الحظر! 🛡️")
            return True
        elif user_id in WHITELIST_USERS:
            message.reply_text("خلي واحد من المطورين يتعامل مع القائمة البيضاء! 📋")
            return True
        elif user_id in MOD_USERS:
            message.reply_text("المشرفين ما ينحظروش! 🛡️")
            return True
        return False

ban_myself = "تبيني نحظر روحي؟ هههه لا يا زول! 😂"

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    bot_is_admin,
    user_is_admin,
    u_na_errmsg,
)


def ban_chat(bot: Bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.banChatSenderChat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("خطأ في حظر القناة {}:{} في {} بسبب: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>القناة:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>\n"
        f"<b>آيدي القناة:</b> {who.id}"
        "" if reason is None else f"\n<b>السبب:</b> {reason}"
    )


def ban_user(bot: Bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.banChatMember(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("خطأ في حظر المستخدم {}:{} في {} بسبب: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>المستخدم:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>\n"
        f"<b>الآيدي:</b> {who.user.id}"
        "" if reason is None else f"\n<b>السبب:</b> {reason}"
    )

def unban_chat(bot: Bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.unbanChatSenderChat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("خطأ في فك حظر القناة {}:{} في {} بسبب: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>القناة:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>\n"
        f"<b>آيدي القناة:</b> {who.id}"
        "" if reason is None else f"\n<b>السبب:</b> {reason}"
    )


def unban_user(bot: Bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        bot.unbanChatMember(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            log.warning("خطأ في فك حظر المستخدم {}:{} في {} بسبب: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>المستخدم:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>\n"
        f"<b>الآيدي:</b> {who.user.id}"
        "" if reason is None else f"\n<b>السبب:</b> {reason}"
    )


@kigcmd(command=['ban', 'dban', 'sban', 'dsban'], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def ban(update: Update, context: CallbackContext) -> Optional[str]:
    global delsilent
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    bot = context.bot

    if message.text.startswith(('/s', '!s', '>s')):
        silent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("ما عنديش صلاحية حذف الرسائل هنا! 🔐")
            return
    else:
        silent = False
    if message.text.startswith(('/d', '!d', '>d')):
        delban = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("ما عنديش صلاحية حذف الرسائل هنا! 🔐")
            return
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("ما عندكش صلاحية حذف الرسائل هنا! 🔐")
            return
    else:
        delban = False
    if message.text.startswith(('/ds', '!ds', '>ds')):
        delsilent = True
        if not bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("ما عنديش صلاحية حذف الرسائل هنا! 🔐")
            return
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            message.reply_text("ما عندكش صلاحية حذف الرسائل هنا! 🔐")
            return

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            message.reply_text("هذي فكرة مش باهية خلاص! 🤔")
            return

        if did_ban := ban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#حظر\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("✅ تم حظر القناة {} من {} بنجاح! 🚫".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("❌ فشل حظر القناة!")
            return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ما ظنيش هذا مستخدم يا زول! 🤔")
        return ''

    member = None
    chan = None
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        try:
            chan = bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            message.reply_text("ما لقيتش هذا الشخص! 🔍")
            return ""

    if chan:
        if did_ban := ban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#حظر\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("✅ تم حظر القناة {} من {} بنجاح! 🚫".format(
                html.escape(chan.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("❌ فشل حظر القناة!")
            return ""

    elif user_id == context.bot.id:
        message.reply_text(ban_myself)
        return ''

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("هذا المستخدم عنده حصانة وما ينحظرش! 🛡️")
        return ''

    elif did_ban := ban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#حظر\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        message.reply_text("✅ تم حظر {} من {} بنجاح! 🚫".format(
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title),
        ),
            parse_mode="html"
        )

    else:
        message.reply_text("❌ فشل حظر المستخدم!")
        return ""

    if silent:
        if delsilent and message.reply_to_message:
            message.reply_to_message.delete()
        message.delete()
    elif delban and message.reply_to_message:
        message.reply_to_message.delete()
    context.bot.send_sticker(chat.id, BAN_STICKER)

    return logmsg


@kigcmd(command='tban', pass_args=True)
@connection_status
@spamcheck
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ما ظنيش هذا مستخدم يا زول! 🤔")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("ما لقيتش هذا المستخدم! 🔍")
        return log_message
    if user_id == bot.id:
        message.reply_text(ban_myself)
        return log_message

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("هذا المستخدم عنده حصانة وما ينحظرش! 🛡️")
        return ''

    if not reason:
        message.reply_text("ما حددتش وقت الحظر! ⏰")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#حظر_مؤقت\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>المدة:</b> {time_val}"
    )
    if reason:
        log += "\n<b>السبب:</b> {}".format(reason)

    try:
        chat.ban_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)

        if reason:
            bot.sendMessage(
                chat.id,
                f"🚫 تم الحظر! {mention_html(member.user.id, member.user.first_name)} محظور لمدة {time_val}.\n📝 السبب: {reason}",
                parse_mode=ParseMode.HTML,
            )

        else:
            bot.sendMessage(
                chat.id,
                f"🚫 تم الحظر! {mention_html(member.user.id, member.user.first_name)} محظور لمدة {time_val}.",
                parse_mode=ParseMode.HTML,
            )

        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            message.reply_text(
                f"🚫 تم الحظر! المستخدم محظور لمدة {time_val}.", quote=False
            )
            return log
        else:
            bot.sendMessage(MESSAGE_DUMP, str(update))
            bot.sendMessage(MESSAGE_DUMP, 
                "خطأ في حظر المستخدم {} في المجموعة {} ({}) بسبب {}".format(
                user_id,
                chat.title,
                chat.id,
                excp.message)
            )
            message.reply_text("❌ وه! ما قدرتش نحظر هذا المستخدم!")

    return log_message


@kigcmd(command=['kick', 'skick', 'dkick', 'dskick', 'punch'], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def kick(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    silent = message.text[1] == 's' or message.text[2] == 's'
    delete = message.text[1] == 'd'
    if message.reply_to_message and message.reply_to_message.sender_chat:
        message.reply_text("هذا الأمر ما يخدمش على القنوات، بس نقدر نحظرها لو تبي! 📢")
        return log_message

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ما ظنيش هذا مستخدم يا زول! 🤔")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("ما لقيتش هذا المستخدم! 🔍")
        return log_message
    if user_id == bot.id:
        message.reply_text("لا لا، مش بنسوي كذا! 😅")
        return log_message

    elif cannot_ban(user.id, user_id, message):
        return ''
    
    elif user_is_admin(update, user_id) and user.id not in DEV_USERS:
        message.reply_text("هذا المستخدم عنده حصانة وما ينطردش! 🛡️")
        return ''

    if delete and message.reply_to_message:
        if user_is_admin(update, message.from_user.id, perm=AdminPerms.CAN_DELETE_MESSAGES):
            if bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                message.reply_to_message.delete()
            else:
                update.effective_message.reply_text(
                    f"ما نقدرش نسوي هذا لأني ما عنديش الصلاحيات؛\n"
                    f"تأكد إني مشرف وعندي صلاحية حذف الرسائل! 🔐")
                return
        else:
            return u_na_errmsg(message, AdminPerms.CAN_DELETE_MESSAGES)


    if chat.unban_member(user_id):
        if not silent:
            bot.send_sticker(chat.id, BAN_STICKER)
            if reason:
                bot.sendMessage(
                    chat.id,
                    f"👢 {mention_html(member.user.id, member.user.first_name)} تم طرده من طرف {mention_html(user.id, user.first_name)} في {message.chat.title}\n<b>السبب</b>: <code>{reason}</code>",
                    parse_mode=ParseMode.HTML,
                )
            else:
                bot.sendMessage(
                    chat.id,
                    f"👢 {mention_html(member.user.id, member.user.first_name)} تم طرده من طرف {mention_html(user.id, user.first_name)} في {message.chat.title}",
                    parse_mode=ParseMode.HTML,
                )

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#طرد\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            log += f"\n<b>السبب:</b> {reason}"

        return log

    else:
        message.reply_text("❌ وه! ما قدرتش نطرد هذا المستخدم!")

    return log_message


@kigcmd(command='kickme', pass_args=True, filters=Filters.chat_type.groups)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
@spamcheck
def kickme(update: Update, _: CallbackContext) -> Optional[str]:
    user_id = update.effective_message.from_user.id
    user = update.effective_message.from_user
    chat = update.effective_chat
    if user_is_admin(update, user_id):
        update.effective_message.reply_text("هههه انت عالق معانا هنا يا زول! 😂")
        return ''

    res = update.effective_chat.unban_member(user_id)
    if res:
        update.effective_message.reply_text("👢 *يطردك من القروب*")

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#طرد\n"
            "طرد نفسه"
            f"<b>المستخدم:</b> {mention_html(user.id, user.first_name)}\n"
        )

        return log

    else:
        update.effective_message.reply_text("هاه؟ ما نقدرش :/ 🤷")


@kigcmd(command='unban', pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
def unban(update: Update, context: CallbackContext) -> Optional[str]:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    bot = context.bot

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            message.reply_text("هذا الأمر ما يخدمش كذا! 🤔")
            return

        if did_ban := unban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#فك_حظر\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("✅ تم فك حظر القناة {} من {} بنجاح! 🎉".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("❌ فشل فك حظر القناة!")
            return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("ما ظنيش هذا مستخدم يا زول! 🤔")
        return ''

    member = None
    chan = None
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        try:
            chan = bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            message.reply_text("ما لقيتش هذا الشخص! 🔍")
            return ""

    if chan:
        if did_ban := unban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#فك_حظر\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            message.reply_text("✅ تم فك حظر القناة {} من {} بنجاح! 🎉".format(
                html.escape(chan.title),
                html.escape(chat.title)
            ),
                parse_mode="html"
            )

        else:
            message.reply_text("❌ فشل فك حظر القناة!")
            return ""

    elif user_id == context.bot.id:
        message.reply_text(ban_myself)
        return ''
    
    elif user_is_admin(update, user_id):
        message.reply_text("هذا مشرف، يعني مش محظور أصلاً! 🛡️")
        return ''

    elif member.status not in ["banned", "kicked"]:
        message.reply_text("هذا المستخدم مش محظور أصلاً! 🤷")
        return ''

    elif did_ban := unban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#فك_حظر\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        message.reply_text("✅ تم فك حظر {} من {} بنجاح! 🎉".format(
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title),
        ),
            parse_mode="html"
        )

    else:
        message.reply_text("❌ فشل فك حظر المستخدم!")
        return ""

    return logmsg


WHITELISTED_USERS = [OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + WHITELIST_USERS


@kigcmd(command='selfunban', pass_args=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@gloggable
def selfunban(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in WHITELISTED_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("اعطيني آيدي قروب صحيح! 🔢")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("ما لقيتش هذا المستخدم! 🔍")
            return
        else:
            raise

    if member.status not in ("left", "kicked"):
        message.reply_text("مش انت أصلاً في القروب؟؟ 🤔")
        return

    chat.unban_member(user.id)
    message.reply_text("✅ تمام، فكيت حظرك! 🎉")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#فك_حظر\n"
        f"<b>المستخدم:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log


from .language import gs


def get_help(chat):
    return gs(chat, "bans_help")


__mod_name__ = "الحظر 🚫"
