import html
from typing import Optional

from telegram.error import TelegramError
from .helper_funcs.admin_status import A_CACHE, B_CACHE

from telegram.chatmemberupdated import ChatMemberUpdated
from telegram import Update, ParseMode

from telegram.ext import CallbackContext

from telegram.ext.chatmemberhandler import ChatMemberHandler

import tg_bot.modules.sql.log_channel_sql as logsql
from tg_bot import OWNER_ID, dispatcher
from tg_bot.modules.log_channel import loggable

import tg_bot.modules.sql.logger_sql as sql


def extract_status_change(chat_member_update: ChatMemberUpdated):
    try:
        status_change = chat_member_update.difference().get("status")
    except AttributeError:
        status_change = None

    try:
        title_change = chat_member_update.difference().get("custom_title")
    except AttributeError:
        title_change = None

    return status_change, title_change


def do_announce(chat):
    return bool(chat.type != "channel" and sql.does_chat_log(chat.id))


@loggable
def chatmemberupdates(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(logsql.LogChannelSettings(chat.id, True, True, True, True, True))
        log_setting = logsql.get_chat_setting(chat.id)
        
    result = extract_status_change(update.chat_member)
    status_change, title_change = result

    if title_change is not None and status_change is None:
        oldtitle, newtitle = title_change
        cause_name = update.chat_member.from_user.mention_html()
        member_name = update.chat_member.new_chat_member.user.mention_html()
        if oldtitle != newtitle:

            if str(update.chat_member.from_user.id) == str(bot.id):
                return ''
            else:

                if oldtitle is None:
                    if do_announce(chat):
                        update.effective_chat.send_message(
                            f"📝 {cause_name} حط لقب لـ {member_name}.\nاللقب الجديد: '<code>{newtitle}</code>'",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#أدمن\nتم تعيين لقب\n"
                        f"<b>من طرف:</b> {cause_name}\n"
                        f"<b>للمشرف:</b> {member_name}\n"
                        f"<b>اللقب القديم:</b> {oldtitle}\n"
                        f"<b>اللقب الجديد:</b> '<code>{newtitle}</code>'"
                    )
                    return log_message

                elif newtitle is None:
                    if do_announce(chat):
                        update.effective_chat.send_message(
                            f"📝 {cause_name} شال اللقب متاع {member_name}.\nاللقب القديم: '<code>{oldtitle}</code>'",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#أدمن\nتم إزالة اللقب\n"
                        f"<b>من طرف:</b> {cause_name}\n"
                        f"<b>للمشرف:</b> {member_name}\n"
                        f"<b>اللقب القديم:</b> '<code>{oldtitle}</code>'\n"
                        f"<b>اللقب الجديد:</b> {newtitle}"
                    )
                    return log_message

                else:
                    if do_announce(chat):
                        update.effective_chat.send_message(
                            f"📝 {cause_name} غيّر لقب {member_name}.\nاللقب القديم: '<code>{oldtitle}</code"
                            f">'\nاللقب الجديد: '<code>{newtitle}</code>'",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#أدمن\nتم تغيير اللقب\n"
                        f"<b>من طرف:</b> {cause_name}\n"
                        f"<b>للمشرف:</b> {member_name}\n"
                        f"<b>اللقب القديم:</b> '<code>{oldtitle}</code>'\n"
                        f"<b>اللقب الجديد:</b> '<code>{newtitle}</code>'"
                    )
                    return log_message

    if status_change is not None:
        status = ','.join(status_change)
        oldstat = str(status.split(",")[0])
        newstat = str(status.split(",")[1])

        if str(update.chat_member.from_user.id) == str(bot.id):
            return ''
        else:

            cause_name = update.chat_member.from_user.mention_html()
            member_name = update.chat_member.new_chat_member.user.mention_html()

            if oldstat == "administrator" and newstat == "member":
                if do_announce(chat):
                    update.effective_chat.send_message(
                        f"⬇️ {member_name} تم تنزيله من الإدارة من طرف {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#أدمن\n<b>تم التنزيل من الإدارة</b>\n"
                    f"<b>المشرف:</b> {cause_name}\n"
                    f"<b>المستخدم:</b> {member_name}"
                )
                return log_message

            if oldstat == "administrator" and newstat == "kicked":
                if do_announce(chat):
                    update.effective_chat.send_message(
                        f"⬇️⛔ {member_name} تم تنزيله وطرده من طرف {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#حظر\n"
                    f"#أدمن\n<b>تم التنزيل والحظر</b>\n"
                    f"<b>المشرف:</b> {cause_name}\n"
                    f"<b>المستخدم:</b> {member_name}"
                )
                return log_message

            if oldstat == "administrator" and newstat == "left":

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#أدمن\n<b>طلع من القروب</b>\n"
                    f"<b>المشرف:</b> {cause_name}\n"
                    f"<b>المستخدم:</b> {member_name}"
                )
                return log_message

            if oldstat != "administrator" and newstat == "administrator":
                if title_change is not None:
                    oldtitle, newtitle = title_change
                    if oldtitle != newtitle:
                        if do_announce(chat):
                            update.effective_chat.send_message(
                                f"⬆️ {member_name} تمت ترقيته من طرف {cause_name} باللقب <code>{newtitle}</code>.",
                                parse_mode=ParseMode.HTML,
                            )

                        if not log_setting.log_action:
                            return ""

                        log_message = (
                            f"<b>{html.escape(chat.title)}:</b>\n"
                            f"#أدمن\n<b>تمت الترقية</b>\n"
                            f"<b>المشرف:</b> {cause_name}\n"
                            f"<b>المستخدم:</b> {member_name}\n"
                            f"<b>اللقب:</b> '<code>{newtitle}</code>'"
                        )
                        return log_message

                else:
                    if do_announce(chat):
                        update.effective_chat.send_message(
                            f"⬆️ {member_name} تمت ترقيته من طرف {cause_name}.",
                            parse_mode=ParseMode.HTML,
                        )

                    if not log_setting.log_action:
                        return ""

                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#أدمن\n<b>تمت الترقية</b>\n"
                        f"<b>المشرف:</b> {cause_name}\n"
                        f"<b>المستخدم:</b> {member_name}"
                    )
                    return log_message

            if oldstat != "restricted" and newstat == "restricted":
                if do_announce(chat):
                    update.effective_chat.send_message(
                        f"🔇 {member_name} تم كتمه من طرف {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#كتم\n"
                    f"<b>المشرف:</b> {cause_name}\n"
                    f"<b>المستخدم:</b> {member_name}"
                )
                return log_message

            if oldstat == "restricted" and newstat != "restricted":
                if do_announce(chat):
                    update.effective_chat.send_message(
                        f"🔊 {member_name} تم فك كتمه من طرف {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#فك_كتم\n"
                    f"<b>المشرف:</b> {cause_name}\n"
                    f"<b>المستخدم:</b> {member_name}"
                )
                return log_message

        if str(update.chat_member.from_user.id) == str(bot.id):
            cause_name = message.from_user.mention_html()
        else:
            cause_name = update.chat_member.from_user.mention_html()

        if oldstat != "kicked" and newstat == "kicked":
            if do_announce(chat):
                update.effective_chat.send_message(
                    f"⛔ {member_name} تم حظره من طرف {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#حظر\n"
                f"<b>المشرف:</b> {cause_name}\n"
                f"<b>المستخدم:</b> {member_name}"
            )
            return log_message

        if oldstat == "kicked" and newstat != "kicked":
            if do_announce(chat):
                update.effective_chat.send_message(
                    f"✅ {member_name} تم فك حظره من طرف {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#فك_حظر\n"
                f"<b>المشرف:</b> {cause_name}\n"
                f"<b>المستخدم:</b> {member_name}"
            )
            return log_message

        if oldstat == "kicked" and newstat == "member":
            if do_announce(chat):
                update.effective_chat.send_message(
                    f"✅ {member_name} تم فك حظره وإضافته من طرف {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#فك_حظر\n"
                f"#ترحيب\n"
                f"<b>المشرف:</b> {cause_name}\n"
                f"<b>المستخدم:</b> {member_name}"
            )
            return log_message

        if oldstat == ("left" or "kicked") and newstat == "member":
            if member_name == cause_name:

                if not log_setting.log_joins:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ترحيب\n"
                    f"<b>المستخدم:</b> {member_name}\n"
                    f"<b>الآيدي</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

            else:
                if not log_setting.log_joins:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ترحيب\n"
                    f"<b>المستخدم:</b> {member_name}\n"
                    f"<b>أضافه:</b> {cause_name}\n"
                    f"<b>الآيدي</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

        if oldstat == ("member" or "administrator") and newstat == "left":
            if member_name == cause_name:

                if not log_setting.log_leave:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#وداعاً\n"
                    f"<b>المستخدم:</b> {member_name}\n"
                    f"<b>الآيدي</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

            else:

                if not log_setting.log_leave:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#إزالة\n"
                    f"<b>المستخدم:</b> {member_name}\n"
                    f"<b>أزاله:</b> {cause_name}\n"
                    f"<b>الآيدي</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

def mychatmemberupdates(update: Update, _: CallbackContext):
    result = extract_status_change(update.my_chat_member)
    status_change, _1 = result
    chat = update.effective_chat
    chatname = chat.title or chat.first_name or 'ما فيش'
    cause_name = update.effective_user.mention_html() if update.effective_user else "مجهول"
    if status_change is not None:
        status = ','.join(status_change)
        oldstat = str(status.split(",")[0])
        newstat = str(status.split(",")[1])
        if oldstat == ("left" or "kicked") and newstat == ("member" or "administrator"):
            new_group = (
                f"<b>{html.escape(chat.title) or chat.first_name or chat.id}:</b>\n"
                f"#قروب_جديد\n"
                f"<b>القروب:</b> {chatname}\n"
                f"<b>أضافني:</b> {cause_name or 'ما فيش'}\n"
                f"<b>الآيدي</b>: <code>{update.effective_user.id}</code>\n"
                f"<b>آيدي القروب</b>: <code>{update.effective_chat.id}</code>"
            )
            dispatcher.bot.send_message(OWNER_ID, new_group, parse_mode=ParseMode.HTML)

def admincacheupdates(update: Update, _: CallbackContext):
    try:
        oldstat = update.chat_member.old_chat_member.status
        newstat = update.chat_member.new_chat_member.status
    except AttributeError:
        return
    if (
        oldstat == "administrator"
        and newstat != "administrator"
        or oldstat != "administrator"
        and newstat == "administrator"
    ):

        A_CACHE[update.effective_chat.id] = update.effective_chat.get_administrators()


def botstatchanged(update: Update, _: CallbackContext):
    if update.effective_chat.type != "private":
        try:
            B_CACHE[update.effective_chat.id] = update.effective_chat.get_member(dispatcher.bot.id)
        except TelegramError:
            pass

dispatcher.add_handler(ChatMemberHandler(chatmemberupdates, ChatMemberHandler.CHAT_MEMBER, run_async=True), group=-21)
dispatcher.add_handler(ChatMemberHandler(mychatmemberupdates, ChatMemberHandler.MY_CHAT_MEMBER, run_async=True), group=-23)
dispatcher.add_handler(ChatMemberHandler(botstatchanged, ChatMemberHandler.MY_CHAT_MEMBER, run_async=True), group=-25)
dispatcher.add_handler(ChatMemberHandler(admincacheupdates, ChatMemberHandler.CHAT_MEMBER, run_async=True), group=-22)
