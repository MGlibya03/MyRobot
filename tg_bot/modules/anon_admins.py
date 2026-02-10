import html
from typing import Optional

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from .. import spamcheck
from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_user, extract_user_and_text
from .helper_funcs.decorators import kigcmd
from .log_channel import loggable
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
)

@kigcmd(command="setanon", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def promoteanon(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        message.reply_text("❌ هذا الأمر يشتغل فالقروبات مش فالخاص!")

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text("❌ خطأ:\n`{}`".format(e))
        return

    if user_member.status == "creator":
        message.reply_text("👑 هذا مؤسس القروب، يقدر يدير أموره بروحه!")
        return

    if getattr(user_member, "is_anonymous") is True:
        message.reply_text("🕶️ هذا المستخدم مجهول أصلاً!")
        return

    if user_id == bot.id:
        message.reply_text("😅 ياريت نقدر نرقي روحي...")
        return

    # نحط نفس صلاحيات البوت - البوت ما يقدر يعطي صلاحيات أعلى من صلاحياته!
    bot_member = get_bot_member(chat.id)
    # نحط نفس صلاحيات المستخدم - باش نخلي الصلاحيات الثانية ما تتغيرش!
    u_member = chat.get_member(user_id)

    try:
        if title:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        bot.promoteChatMember(
            chat.id,
            user_id,
            is_anonymous=True,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_voice_chats=bool(bot_member.can_manage_voice_chats and u_member.can_manage_voice_chats),

        )

        rmsg = f"🕶️ <b>{user_member.user.first_name or user_id}</b> توا صار مجهول"
        if title:
            rmsg += f" باللقب <code>{html.escape(title)}</code>"
        bot.sendMessage(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        ) 
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("🤔 كيف نرقي واحد مش موجود فالقروب؟")
        else:
            message.reply_text("❌ صار خطأ وقت الترقية!")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ترقية\n"
        f"🕶️ مجهول\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>المستخدم:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message

@kigcmd(command="unsetanon", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def demoteanon(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        message.reply_text("❌ هذا الأمر يشتغل فالقروبات مش فالخاص!")

    user_id = extract_user(message, args)

    if not user_id:
        user_id = user.id

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text("❌ خطأ:\n`{}`".format(e))
        return

    if user_member.status == "creator" and user_id == user.id:
        message.reply_text("🤷 مه...")
        return

    if user_member.status == "creator":
        message.reply_text("👑 هذا مؤسس القروب، دور على واحد ثاني تلعب معاه!")
        return

    if user_member.status != "administrator":
        message.reply_text("❌ هذا المستخدم مش أدمن!")
        return

    if getattr(user_member, "is_anonymous") is False:
        message.reply_text("👤 هذا المستخدم مش مجهول أصلاً!")
        return

    if user_id == bot.id:
        message.reply_text("❌ ما نقدرش ننزل روحي! خلي أدمن ثاني يسويها.")
        return

    # نحط نفس صلاحيات البوت - البوت ما يقدر يعطي صلاحيات أعلى من صلاحياته!
    bot_member = get_bot_member(chat.id)
    # نحط نفس صلاحيات المستخدم - باش نخلي الصلاحيات الثانية ما تتغيرش!
    u_member = chat.get_member(user_id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            is_anonymous=False,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_voice_chats=bool(bot_member.can_manage_voice_chats and u_member.can_manage_voice_chats),
        )

        rmsg = f"👤 <b>{user_member.user.first_name or user_id}</b> توا ما عادش مجهول"
        bot.sendMessage(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        )  

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تنزيل\n"
            f"👤 إلغاء المجهولية\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>المستخدم:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        message.reply_text(
            f"❌ ما قدرتش ننزله!\n{str(e)}"
        )
        return
