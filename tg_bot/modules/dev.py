import html
import os
import re
import subprocess
import sys
from time import sleep
from telegram.error import Unauthorized
from .. import DEV_USERS, OWNER_ID, telethn, SYS_ADMIN
from .helper_funcs.chat_status import dev_plus
from telegram import TelegramError, Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, Filters
import asyncio
from statistics import mean
from time import monotonic as time
from telethon import events
from .helper_funcs.decorators import kigcmd, register, kigcallback, kigmsg
from tg_bot.antispam import IGNORED_CHATS, IGNORED_USERS

# ==================== الأوامر العربية ====================
ARABIC_LEAVE_COMMANDS = ["غادر", "اطلع", "اخرج"]
ARABIC_GITPULL_COMMANDS = ["تحديث_الكود", "جيت_بول"]
ARABIC_RESTART_COMMANDS = ["اعادة_تشغيل", "ريستارت"]
ARABIC_PIPINSTALL_COMMANDS = ["تثبيت_حزمة", "بيب_تثبيت"]
ARABIC_LOCKDOWN_COMMANDS = ["قفل_البوت", "اقفال_شامل"]
ARABIC_GETINFO_COMMANDS = ["معلومات_المحادثة", "بيانات_القروب"]
ARABIC_IGNORED_COMMANDS = ["المتجاهلين", "القائمة_المتجاهلة"]
ARABIC_GETSTATS_COMMANDS = ["احصائيات", "الاحصائيات"]


@kigcmd(command='leave')
@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot

    if args := context.args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            if len(leave_msg) >= 1:
                context.bot.send_message(chat_id, leave_msg)
            bot.leave_chat(int(chat_id))
            try:
                update.effective_message.reply_text("✅ تم المغادرة من المجموعة.")
            except Unauthorized:
                pass
        except TelegramError:
            update.effective_message.reply_text("⚠️ فشلت المغادرة لسبب ما!")
    elif update.effective_message.chat.type != "private":
        chat = update.effective_chat
        kb = [[
            InlineKeyboardButton(
                text="✅ أنا متأكد من هذا الإجراء", 
                callback_data="leavechat_cb_({})".format(chat.id)
            )
        ]]
        update.effective_message.reply_text(
            f"⚠️ حأغادر من {chat.title}، اضغط الزر تحت للتأكيد", 
            reply_markup=InlineKeyboardMarkup(kb)
        )


# ==================== معالج عربي للمغادرة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_LEAVE_COMMANDS) + r')(\s|$)'), group=3)
@dev_plus
def arabic_leave(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_LEAVE_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        args = text.split()
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:]) if len(args) > 1 else "وداعاً! 👋"
        try:
            if leave_msg:
                bot.send_message(chat_id, leave_msg)
            bot.leave_chat(int(chat_id))
            try:
                message.reply_text("✅ تم المغادرة من المجموعة.")
            except Unauthorized:
                pass
        except TelegramError:
            message.reply_text("⚠️ فشلت المغادرة لسبب ما!")
    elif message.chat.type != "private":
        chat = update.effective_chat
        kb = [[
            InlineKeyboardButton(
                text="✅ أنا متأكد", 
                callback_data="leavechat_cb_({})".format(chat.id)
            )
        ]]
        message.reply_text(
            f"⚠️ حأغادر من {chat.title}، اضغط الزر للتأكيد", 
            reply_markup=InlineKeyboardMarkup(kb)
        )


@kigcallback(pattern=r"leavechat_cb_", run_async=True)
def leave_cb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    if callback.from_user.id not in DEV_USERS:
        callback.answer(text="⚠️ هذا مش لك!", show_alert=True)
        return

    match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
    chat = int(match.group(1))
    callback.edit_message_text("👋 باي باي!")
    bot.leave_chat(chat_id=chat)


@kigcmd(command='gitpull')
@dev_plus
def gitpull(update: Update, context: CallbackContext):
    sent_msg = update.effective_message.reply_text(
        "📥 جاري سحب التحديثات من GitHub ثم إعادة التشغيل..."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\n✅ تم السحب... إعادة التشغيل خلال "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    sent_msg.edit_text("✅ تمت إعادة التشغيل!")
    os.system("pm2 restart odin")


# ==================== معالج عربي لتحديث الكود ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_GITPULL_COMMANDS) + r')$'), group=3)
@dev_plus
def arabic_gitpull(update: Update, context: CallbackContext):
    sent_msg = update.effective_message.reply_text(
        "📥 جاري سحب التحديثات من GitHub ثم إعادة التشغيل..."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\n✅ تم السحب... إعادة التشغيل خلال "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    sent_msg.edit_text("✅ تمت إعادة التشغيل!")
    os.system("pm2 restart odin")


@kigcmd(command='restart')
@dev_plus
def restart(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        "🔄 جاري بدء نسخة جديدة وإيقاف هذي..."
    )
    os.system("pm2 restart odin")


# ==================== معالج عربي لإعادة التشغيل ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_RESTART_COMMANDS) + r')$'), group=3)
@dev_plus
def arabic_restart(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        "🔄 جاري بدء نسخة جديدة وإيقاف هذي..."
    )
    os.system("pm2 restart odin")


class Store:
    def __init__(self, func):
        self.func = func
        self.calls = []
        self.time = time()
        self.lock = asyncio.Lock()

    def average(self):
        return round(mean(self.calls), 2) if self.calls else 0

    def __repr__(self):
        return f"<Store func={self.func.__name__}, average={self.average()}>"

    async def __call__(self, event):
        async with self.lock:
            if not self.calls:
                self.calls = [0]
            if time() - self.time > 1:
                self.time = time()
                self.calls.append(1)
            else:
                self.calls[-1] += 1
        await self.func(event)


async def nothing(event):
    pass


messages = Store(nothing)
inline_queries = Store(nothing)
callback_queries = Store(nothing)

telethn.add_event_handler(messages, events.NewMessage())
telethn.add_event_handler(inline_queries, events.InlineQuery())
telethn.add_event_handler(callback_queries, events.CallbackQuery())


@register(pattern='getstats', from_users=[SYS_ADMIN, OWNER_ID], no_args=True)
async def getstats(event):
    await event.reply(
        f"**📊 إحصائيات أحداث البوت**\n\n"
        f"**متوسط الرسائل:** {messages.average()}/ث\n"
        f"**متوسط استعلامات الأزرار:** {callback_queries.average()}/ث\n"
        f"**متوسط الاستعلامات المضمنة:** {inline_queries.average()}/ث",
        parse_mode='md'
    )


# ==================== معالج عربي للإحصائيات ====================
@register(pattern='|'.join(ARABIC_GETSTATS_COMMANDS), from_users=[SYS_ADMIN, OWNER_ID], no_args=True)
async def arabic_getstats(event):
    await event.reply(
        f"**📊 إحصائيات أحداث البوت**\n\n"
        f"**متوسط الرسائل:** {messages.average()}/ث\n"
        f"**متوسط استعلامات الأزرار:** {callback_queries.average()}/ث\n"
        f"**متوسط الاستعلامات المضمنة:** {inline_queries.average()}/ث",
        parse_mode='md'
    )


@kigcmd(command='pipinstall')
@dev_plus
def pip_install(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if not args:
        message.reply_text("⚠️ أدخل اسم الحزمة!")
        return
    if len(args) >= 1:
        cmd = "py -m pip install {}".format(' '.join(args))
        process = subprocess.Popen(
            cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
        )
        stdout, stderr = process.communicate()
        reply = ""
        stderr = stderr.decode()
        stdout = stdout.decode()
        if stdout:
            reply += f"*المخرجات*\n`{stdout}`\n"
        if stderr:
            reply += f"*الأخطاء*\n`{stderr}`\n"

        message.reply_text(text=reply, parse_mode=ParseMode.MARKDOWN)


# ==================== معالج عربي لتثبيت الحزم ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_PIPINSTALL_COMMANDS) + r')(\s|$)'), group=3)
@dev_plus
def arabic_pip_install(update: Update, context: CallbackContext):
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_PIPINSTALL_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        message.reply_text("⚠️ أدخل اسم الحزمة!")
        return
    
    args = text.split()
    cmd = "py -m pip install {}".format(' '.join(args))
    process = subprocess.Popen(
        cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
    )
    stdout, stderr = process.communicate()
    reply = ""
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*✅ المخرجات*\n`{stdout}`\n"
    if stderr:
        reply += f"*⚠️ الأخطاء*\n`{stderr}`\n"

    message.reply_text(text=reply, parse_mode=ParseMode.MARKDOWN)


@kigcmd(command='lockdown')
@dev_plus
def allow_groups(update: Update, context: CallbackContext):
    args = context.args
    global ALLOW_CHATS
    if not args:
        state = "مفعل" if not ALLOW_CHATS else "معطل"
        update.effective_message.reply_text(f"📊 الحالة الحالية: القفل الشامل {state}")
        return
    if args[0].lower() in ["off", "no", "تعطيل", "لا"]:
        ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on", "تفعيل", "نعم"]:
        ALLOW_CHATS = False
    else:
        update.effective_message.reply_text("⚠️ الصيغة: تفعيل/تعطيل")
        return
    update.effective_message.reply_text("✅ تم! تم تبديل حالة القفل الشامل.")


# ==================== معالج عربي للقفل الشامل ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_LOCKDOWN_COMMANDS) + r')(\s|$)'), group=3)
@dev_plus
def arabic_allow_groups(update: Update, context: CallbackContext):
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_LOCKDOWN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    global ALLOW_CHATS
    if not text:
        state = "مفعل" if not ALLOW_CHATS else "معطل"
        message.reply_text(f"📊 الحالة الحالية: القفل الشامل {state}")
        return
    
    if text.lower() in ["off", "no", "تعطيل", "لا", "عطل"]:
        ALLOW_CHATS = True
    elif text.lower() in ["yes", "on", "تفعيل", "نعم", "فعل"]:
        ALLOW_CHATS = False
    else:
        message.reply_text("⚠️ استخدم: تفعيل أو تعطيل")
        return
    message.reply_text("✅ تم! تم تبديل حالة القفل الشامل.")


@kigcmd(command='getinfo')
@dev_plus      
def get_chat_by_id(update: Update, context: CallbackContext):
    msg = update.effective_message
    args = context.args
    if not args:
        msg.reply_text("<i>⚠️ آيدي المحادثة مطلوب!</i>", parse_mode=ParseMode.HTML)
        return
    if len(args) >= 1:
        data = context.bot.get_chat(args[0])
        m = "<b>📋 تم العثور على المحادثة، التفاصيل أدناه:</b>\n\n"
        m += "<b>🏷 العنوان:</b> {}\n".format(html.escape(data.title))
        m += "<b>👥 الأعضاء:</b> {}\n\n".format(data.get_member_count())
        if data.description:
            m += "<i>📝 {}</i>\n\n".format(html.escape(data.description))
        if data.linked_chat_id:
            m += "<b>🔗 محادثة مربوطة:</b> {}\n".format(data.linked_chat_id)

        m += "<b>📱 النوع:</b> {}\n".format(data.type)
        if data.username:
            m += "<b>👤 اليوزر:</b> {}\n".format(html.escape(data.username))
        m += "<b>🆔 الآيدي:</b> {}\n".format(data.id)
        if args[0] in IGNORED_CHATS:
            m += "<b>⚠️ متجاهل:</b> نعم\n"
        m += "\n<b>🔐 الصلاحيات:</b>\n <code>{}</code>\n".format(data.permissions)

        if data.invite_link:
            m += "\n<b>🔗 رابط الدعوة:</b> {}".format(data.invite_link)

        msg.reply_text(text=m, parse_mode=ParseMode.HTML)


# ==================== معالج عربي لمعلومات المحادثة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_GETINFO_COMMANDS) + r')(\s|$)'), group=3)
@dev_plus
def arabic_get_chat_by_id(update: Update, context: CallbackContext):
    msg = update.effective_message
    
    text = msg.text
    for cmd in ARABIC_GETINFO_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        msg.reply_text("<i>⚠️ آيدي المحادثة مطلوب!</i>", parse_mode=ParseMode.HTML)
        return
    
    args = text.split()
    data = context.bot.get_chat(args[0])
    m = "<b>📋 تم العثور على المحادثة، التفاصيل أدناه:</b>\n\n"
    m += "<b>🏷 العنوان:</b> {}\n".format(html.escape(data.title))
    m += "<b>👥 الأعضاء:</b> {}\n\n".format(data.get_member_count())
    if data.description:
        m += "<i>📝 {}</i>\n\n".format(html.escape(data.description))
    if data.linked_chat_id:
        m += "<b>🔗 محادثة مربوطة:</b> {}\n".format(data.linked_chat_id)

    m += "<b>📱 النوع:</b> {}\n".format(data.type)
    if data.username:
        m += "<b>👤 اليوزر:</b> {}\n".format(html.escape(data.username))
    m += "<b>🆔 الآيدي:</b> {}\n".format(data.id)
    if args[0] in IGNORED_CHATS:
        m += "<b>⚠️ متجاهل:</b> نعم\n"
    m += "\n<b>🔐 الصلاحيات:</b>\n <code>{}</code>\n".format(data.permissions)

    if data.invite_link:
        m += "\n<b>🔗 رابط الدعوة:</b> {}".format(data.invite_link)

    msg.reply_text(text=m, parse_mode=ParseMode.HTML)


@kigcmd(command='ignored')
@dev_plus
def get_whos_ignored(update: Update, _: CallbackContext):
    txt = "<b>📋 المحادثات المتجاهلة:</b>\n<code>"
    txt += "</code>, <code>".join(["{}".format(chat) for chat in IGNORED_CHATS])
    txt += "</code>\n\n"
    txt += "<b>👥 المستخدمين المتجاهلين:</b>\n<code>"
    txt += "</code>, <code>".join(["{}".format(chat) for chat in IGNORED_USERS])
    txt += "</code>"
    update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)


# ==================== معالج عربي للمتجاهلين ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_IGNORED_COMMANDS) + r')$'), group=3)
@dev_plus
def arabic_get_whos_ignored(update: Update, _: CallbackContext):
    txt = "<b>📋 المحادثات المتجاهلة:</b>\n<code>"
    txt += "</code>, <code>".join(["{}".format(chat) for chat in IGNORED_CHATS])
    txt += "</code>\n\n"
    txt += "<b>👥 المستخدمين المتجاهلين:</b>\n<code>"
    txt += "</code>, <code>".join(["{}".format(chat) for chat in IGNORED_USERS])
    txt += "</code>"
    update.effective_message.reply_text(txt, parse_mode=ParseMode.HTML)


from .language import gs

def get_help(chat):
    return gs(chat, "dev_help")

__mod_name__ = "المطور"
