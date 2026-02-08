import html
import time

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from telegram.utils.helpers import mention_html
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.types import ChannelParticipantCreator
from tg_bot import telethn

from tg_bot import spamcheck
from .helper_funcs.chat_status import connection_status

from .helper_funcs.extraction import extract_user, extract_user_and_text
from .log_channel import loggable
from .language import gs
from .helper_funcs.decorators import kigcmd, register

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    A_CACHE, B_CACHE
)

from typing import Optional


@kigcmd(command="fullpromote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def fullpromote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "ما لقيت المستخدم اللي تقصده، تأكد من الآيدي أو رد على رسالته 🤔"
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text(f"❌ خطأ: {e}")
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("هذا العضو أصلاً مشرف يا باهي! 😅")
        return

    if user_id == bot.id:
        message.reply_text("يا ريت نقدر نرقي روحي... بس ما نقدرش 😅")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = get_bot_member(chat.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
            is_anonymous=bot_member.is_anonymous,
        )
        if title:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        bot.sendMessage(
            chat.id,
            "✅ <b>{}</b> تمت ترقيته{} بكل الصلاحيات! 🎉"
                .format(user_member.user.first_name or user_id,
                        f" من طرف <b>{message.from_user.first_name}</b>" if not message.sender_chat else ""),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("كيف نرقي واحد مش في القروب؟ 🤔")
        else:
            message.reply_text("❌ صار خطأ وقت الترقية!")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ترقية_كاملة\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>العضو:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message

@kigcmd(command="promote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def promote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "ما لقيت المستخدم اللي تقصده، تأكد من الآيدي أو رد على رسالته 🤔"
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text(f"❌ خطأ: {e}")
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("هذا العضو أصلاً مشرف يا باهي! 😅")
        return

    if user_id == bot.id:
        message.reply_text("يا ريت نقدر نرقي روحي... بس ما نقدرش 😅")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = get_bot_member(chat.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
        if title:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        bot.sendMessage(
            chat.id,
            "✅ <b>{}</b> تمت ترقيته{}! 🎉".format(
                    user_member.user.first_name or user_id,
                    f' من طرف <b>{message.from_user.first_name}</b>' if not message.sender_chat else ''
                ),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("كيف نرقي واحد مش في القروب؟ 🤔")
        else:
            message.reply_text(f"❌ صار خطأ وقت الترقية:\n{err.message}")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#ترقية\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>العضو:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@kigcmd(command="demote", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def demote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "ما لقيت المستخدم اللي تقصده، تأكد من الآيدي أو رد على رسالته 🤔"
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text(f"❌ خطأ: {e}")
        return

    if user_member.status == "creator":
        message.reply_text("هذا صاحب القروب يا زول! روح لعب مع واحد ثاني 😂")
        return

    if user_member.status != "administrator":
        message.reply_text("هذا مش مشرف أصلاً! 🤷")
        return

    if user_id == bot.id:
        message.reply_text("ما نقدرش نتنازل عن روحي! خلي مشرف ثاني يسويها 😅")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
            is_anonymous=False,
        )
        bot.sendMessage(
            chat.id,
            "⬇️ <b>{}</b> تم تنزيله من الإشراف{}.".format(
                    user_member.user.first_name or user_id,
                    f' من طرف <b>{message.from_user.first_name}</b>' if not message.sender_chat else ''
            ),
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تنزيل\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>العضو:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        message.reply_text(
            f"❌ ما قدرت نتنازل عنه!\n{str(e)}"
        )
        return

@kigcmd(command="title", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def set_title(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = chat.get_member(user_id)
    except:
        message.reply_text(
            "ما لقيت المستخدم اللي تقصده، تأكد من الآيدي أو رد على رسالته 🤔"
        )
        return

    if user_member.status == "creator" and user_id == user.id:
        message.reply_text(
            "تمام يا باشا 😏"
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "هذا صاحب القروب، هو بس اللي يقدر يغير لقبه 👑"
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "الألقاب للمشرفين بس يا غالي! 🏷️"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "ما نقدرش نغير لقبي بروحي! خلي اللي رقاني يسويها 😅"
        )
        return

    if not title:
        message.reply_text("ما ينفعش تحط لقب فاضي! 🤷")
        return

    if len(title) > 16:
        message.reply_text(
            "اللقب طويل برشا! أكثر من 16 حرف.\nبنقصه لـ 16 حرف ✂️"
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("نقدر نحط ألقاب بس للمشرفين اللي أنا رقيتهم! 🤷")
        return

    bot.sendMessage(
        chat.id,
        f"✅ تم تغيير لقب <code>{user_member.user.first_name or user_id}</code> "
        f"لـ <code>{html.escape(title[:16])}</code>! 🏷️",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#لقب_جديد\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>للمشرف:</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
        f"<b>اللقب الجديد:</b> '<code>{html.escape(title[:16])}</code>'"

    )
    return log_message


@kigcmd(command=["invitelink", "link"], can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@user_admin_check(AdminPerms.CAN_INVITE_USERS, allow_mods = True)
@loggable
def invite(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.username:
        update.effective_message.reply_text(f"🔗 https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(f"🔗 {invitelink}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#رابط_دعوة\n"
                f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>الرابط:</b> '<code>{invitelink}</code>'"

            )
            return log_message

        else:
            update.effective_message.reply_text(
                "ما عنديش صلاحية أجيب رابط الدعوة، غير صلاحياتي! 🔐"
            )
    else:
        update.effective_message.reply_text(
            "نقدر نجيب روابط الدعوة بس للسوبرقروبات والقنوات! 📢"
        )


@kigcmd(command=["admincache"], can_disable=False)
@spamcheck
def admincache(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    try:
        last = _admincache[chat.id]
    except KeyError:
        last = None
    now = time.time()
    if last and last + 600 > now:
        return msg.reply_text("هذا الأمر ينفع مرة كل 10 دقايق بس ⏱️")

    if chat.type in ["channel", "private"]:
        return msg.reply_text("هذا الأمر ينفع في القروبات بس 👥")

    if chat.get_member(user.id).status not in ["administrator", "creator"] and user.id != 1087968824:
        return msg.reply_text("هذا الأمر للمشرفين بس! 🔐")

    A_CACHE[update.effective_chat.id] = update.effective_chat.get_administrators()
    B_CACHE[update.effective_chat.id] = update.effective_chat.get_member(context.bot.id)
    msg.reply_text("✅ تم تحديث قائمة المشرفين!")
    _admincache[chat.id] = time.time()


_admincache = dict()


@register(pattern="(admin|admins|staff|adminlist|مشرفين|المشرفين)", groups_only=True, no_args=True)
async def adminList(event):
    try:
        _ = event.chat.title
    except:
        return

    temp = await event.reply("⏳ جاري جلب قائمة المشرفين...")
    text = "👥 المشرفين في **{}**".format(event.chat.title)

    admn = telethn.iter_participants(
        event.chat_id, 50, filter=ChannelParticipantsAdmins)

    creator = ""
    admin = []
    bots = []

    async for user in admn:

        if isinstance(user.participant, ChannelParticipantCreator):

            if user.first_name == "":
                name = "☠ محذوف"
            else:
                name = "[{}](tg://user?id={})".format(user.first_name.split()[0], user.id)
            creator = "\nㅤㅤ• {}".format(name)
        elif user.bot:
            if user.first_name == "":
                name = "☠ محذوف"
            else:
                name = "[{}](tg://user?id={})".format(user.first_name, user.id)
            bots.append("\nㅤㅤ• {}".format(name))

        else:
            try:
                if user.participant.admin_rights.is_anonymous:
                    continue
            except:
                pass

            try:
                if not user.first_name or user.deleted:
                    continue
                else:
                    name = "[{}](tg://user?id={})".format(user.first_name, user.id)
            except AttributeError:
                pass
            admin.append("\nㅤㅤ• {}".format(name))

    text += "\nㅤ👑 **المالك:**"

    text += creator

    text += f"\nㅤ🛡️ **المشرفين:** {len(admin)}"

    text += "".join(admin)

    text += f"\nㅤ🤖 **البوتات:** {len(bots)}"

    text += "".join(bots)

    members = await telethn.get_participants(event.chat_id)
    mm = len(members)

    text += "\n👥 **الأعضاء:** {}".format(mm)
    text += "\n\n📌 هذي المعلومات محدثة توا"

    await temp.edit(text, parse_mode="markdown")


def get_help(chat):
    return gs(chat, "admin_help")


__mod_name__ = "المشرفين 🛡️"
