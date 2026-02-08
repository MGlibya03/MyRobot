import time
from asyncio import sleep
from telethon.events import NewMessage
from telethon.tl.types import ChannelParticipantsAdmins
from .helper_funcs.decorators import register
from .sql.clear_cmd_sql import get_clearcmd
from tg_bot import BOT_ID, telethn
from .helper_funcs.telethn.chatstatus import (
    can_delete_messages, user_can_purge, user_is_admin)
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError


# ==================== أمر المسح (purge) ====================
@register(pattern=r'(?:(s)?purge|p|مسح|تنظيف|امسح)', groups_only=True, no_args=True)
async def purge_messages(event: NewMessage.Event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id, message=event) and event.from_id not in [
                1087968824
            ]:
        await event.reply("⚠️ بس المشرفين يقدروا يستخدموا هالأمر!")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("⚠️ ما عندك صلاحية حذف الرسائل!")
        return

    if not await can_delete_messages(message=event):
        if event.chat.admin_rights is None:
            return await event.reply("⚠️ أنا مش مشرف، سوني مشرف أول!")
        elif not event.chat.admin_rights.delete_messages:
            return await event.reply("⚠️ ما عندي صلاحية حذف الرسائل!")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "⚠️ رد على رسالة باش أعرف من وين أبدأ المسح.")
        return
    messages = []
    message_id = reply_msg.id
    delete_to = event.message.id

    messages.append(event.reply_to_msg_id)
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        pass
    if not event.pattern_match.group(1):
        time_ = time.perf_counter() - start
        text = f"✅ تم المسح بنجاح في {time_:0.2f} ثانية"
        prmsg = await event.respond(text, parse_mode='markdown')

        cleartime = get_clearcmd(event.chat_id, "purge")

        if cleartime:
            await sleep(cleartime.time)
            await prmsg.delete()


# ==================== أمر الحذف (del) ====================
@register(pattern=r'(del|d|حذف|احذف|شيل)', groups_only=True, no_args=True)
async def delete_messages(event):

    if event.from_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id, message=event) and event.from_id not in [
                1087968824
            ]:
        await event.reply("⚠️ بس المشرفين يقدروا يستخدموا هالأمر!")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("⚠️ ما عندك صلاحية حذف الرسائل!")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply("⚠️ شو تبيني أحذف؟ رد على رسالة!")
        return

    if not await can_delete_messages(message=event) and not int(message.sender.id) == int(BOT_ID):
        if event.chat.admin_rights is None:
            await event.reply("⚠️ أنا مش مشرف، سوني مشرف أول!")
        elif not event.chat.admin_rights.delete_messages:
            await event.reply("⚠️ ما عندي صلاحية حذف الرسائل!")
        return

    chat = await event.get_input_chat()
    await event.client.delete_messages(chat, message)
    try:
        await event.client.delete_messages(chat, event.message)
    except MessageDeleteForbiddenError:
        print("error in deleting message {} in {}".format(event.message.id, event.chat.id))
        pass


from .language import gs

def get_help(chat):
    return gs(chat, "purge_help")


__mod_name__ = "المسح"
__command_list__ = ["del", "purge", "حذف", "مسح", "امسح", "احذف", "تنظيف", "شيل"]
