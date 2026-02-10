import html
from typing import Union

from telegram.user import User
from tg_bot.antispam import GLOBAL_USER_DATA, Owner
import time
import git
import requests
from io import BytesIO
from telegram import Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, CallbackContext
from telegram.utils.helpers import mention_html, escape_markdown
from subprocess import Popen, PIPE
from tg_bot import (
    MESSAGE_DUMP,
    MOD_USERS,
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    WHITELIST_USERS,
    INFOPIC,
    spamcheck,
    sw,
    StartTime,
    SYS_ADMIN,
)
from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from .sql import SESSION
from .helper_funcs.chat_status import dev_plus, sudo_plus
from .helper_funcs.extraction import extract_user
import tg_bot.modules.sql.users_sql as sql
from .language import gs
from telegram import __version__ as ptbver, InlineKeyboardMarkup, InlineKeyboardButton
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
import datetime
import platform
from platform import python_version
from .helper_funcs.decorators import kigcmd, kigcallback

MARKDOWN_HELP = f"""
الماركداون هو أداة تنسيق قوية يدعمها تيليجرام. {dispatcher.bot.first_name} عنده تحسينات إضافية، باش يتأكد إن \
الرسائل المحفوظة تتحلل صح، ويخليك تسوي أزرار.

- <code>_مائل_</code>: لف النص بـ '_' يسوي نص مائل
- <code>*عريض*</code>: لف النص بـ '*' يسوي نص عريض
- <code>`كود`</code>: لف النص بـ '`' يسوي نص بخط ثابت (كود)
- <code>[نص](رابط)</code>: هذا يسوي رابط - الرسالة تعرض <code>النص</code> فقط، \
ولما تضغط عليه يفتحلك <code>الرابط</code>.
مثال: <code>[اضغط هنا](example.com)</code>

- <code>[نص الزر](buttonurl:رابط)</code>: هذا تحسين خاص يخلي المستخدمين يسوون أزرار \
تيليجرام فالماركداون. <code>نص الزر</code> هو اللي يظهر على الزر، و<code>الرابط</code> \
هو اللي يفتح لما تضغط.
مثال: <code>[هذا زر](buttonurl:example.com)</code>

لو تبي أزرار متعددة فنفس السطر، استخدم :same، مثل كذا:
<code>[واحد](buttonurl://example.com)
[اثنين](buttonurl://google.com:same)</code>
هذا يسوي زرين فسطر واحد، بدل زر واحد فكل سطر.

خلي فبالك إن رسالتك <b>لازم</b> تحتوي على نص غير الأزرار!
"""
WHITELISTS = ([777000, 1087968824, dispatcher.bot.id, OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + WHITELIST_USERS)
ELEVATED = ([777000, 1087968824, dispatcher.bot.id, OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + SUPPORT_USERS + WHITELIST_USERS + MOD_USERS)

def mention_html_chat(chat_id: Union[int, str], name: str) -> str:
    return f'<a href="tg://t.me/{chat_id}">{html.escape(name)}</a>'

@kigcmd(command='id', pass_args=True)
@spamcheck
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"<b>🆔 معرفات تيليجرام:</b>\n"
                f"ㅤ{html.escape(user2.first_name)}\nㅤㅤ<code>{user2.id}</code>.\n"
                f"ㅤ{html.escape(user1.first_name)}\nㅤㅤ<code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(

                f"<b>🆔 معرفات تيليجرام:</b>\n"
                f"{html.escape(user.first_name or user.title)}\n  <code>{user.id}</code>.\n",

                parse_mode=ParseMode.HTML,
            )

    else:

        if chat.type == "private":
            msg.reply_text(
                f"<b>🆔 الآيدي متاعك هو:</b> \n  <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

        else:
            msg.reply_text(
                f"<b>🆔 آيدي هالقروب هو:</b> \n  <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

@kigcmd(command='gifid')
@spamcheck
def gifid(update: Update, _):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"🎞 آيدي الصورة المتحركة:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text("📌 رد على صورة متحركة (GIF) باش نعطيك الآيدي متاعها.")


@kigcmd(command='print', pass_args=True, filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def printdata(update: Update, context: CallbackContext):
    print(GLOBAL_USER_DATA)
    gd = str(GLOBAL_USER_DATA)
    dispatcher.bot.sendMessage(Owner, "`{}`".format(gd), parse_mode="markdown")


@kigcmd(command="resetantispam", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def resetglobaldata(update: Update, context: CallbackContext):
    bot = context.bot
    from .eval import log_input, send
    global GLOBAL_USER_DATA
    log_input(update)
    gd = str(GLOBAL_USER_DATA)
    dispatcher.bot.sendMessage(Owner, "`{}`".format(gd), parse_mode="markdown")
    try:
        GLOBAL_USER_DATA = {}
    except Exception as e:
        dispatcher.bot.sendMessage(Owner, "خطأ عام\n`{}`".format(str(e)), parse_mode="markdown")
    send("تم ✅", bot, update)

@kigcmd(command='whois', pass_args=True)
@spamcheck
def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)
    elif not message.reply_to_message and not args:
        user = message.sender_chat or message.from_user
    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("❌ ما قدرت نستخرج مستخدم من هذا.")
        return
    else:
        return

    temp = message.reply_text("<code>⏳ نتحقق من المعلومات...</code>", parse_mode=ParseMode.HTML)

    if isinstance(user, User):
        text = get_user_info(user, chat)
    else:
        text = get_chat_info(user)

    temp.edit_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )

@kigcmd(command=['info', 'u',], pass_args=True)
@spamcheck
def info(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)
    elif not message.reply_to_message and not args:
        user = (
            message.sender_chat
            if message.sender_chat is not None
            else message.from_user
        )
    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].lstrip("-").isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("❌ ما قدرت نستخرج مستخدم من هذا.")
        return
    else:
        return

    temp = message.reply_text("<code>⏳ نتحقق من المعلومات...</code>", parse_mode=ParseMode.HTML)

    if hasattr(user, 'type') and user.type != "private":
        text = get_chat_info(user)
    else:
        text = get_user_info(user, chat, True)

    temp.edit_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )

def get_user_info(user, chat, full_info=False):
    bot = dispatcher.bot
    text = (
        f"<b>👤 معلومات المستخدم:</b>\n"
        f"ㅤ<b>الاسم الأول:</b> {mention_html(user.id, user.first_name or 'ما فيش')}"
    )
    if user.last_name:
        text += f"\nㅤ<b>الاسم الأخير:</b> {html.escape(user.last_name)}"
    if user.username:
        text += f"\nㅤ<b>المعرف:</b> @{html.escape(user.username)}"
    text += f"\nㅤ<b>الآيدي:</b> <code>{user.id}</code>"


    if user.id not in [OWNER_ID, SYS_ADMIN, 777000, 1087968824, bot.id]:
        num_chats = sql.get_user_num_chats(user.id)
        text += f"\nㅤ<b>القروبات:</b> <code>{num_chats}</code>"

    if user.id == OWNER_ID:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>👑 المالك</a>".format(escape_markdown(dispatcher.bot.username))
    elif user.id == SYS_ADMIN:
        text += ""
    elif user.id in DEV_USERS:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>👨‍💻 مطور</a>".format(escape_markdown(dispatcher.bot.username))
    elif user.id in SUDO_USERS:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>⚡ سودو</a>".format(escape_markdown(dispatcher.bot.username))
    elif user.id in SUPPORT_USERS:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>🛡 دعم</a>".format(escape_markdown(dispatcher.bot.username))
    elif user.id in MOD_USERS:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>🔧 مشرف</a>".format(escape_markdown(dispatcher.bot.username))
    elif user.id in WHITELIST_USERS:
        text += "\nㅤ<b>الحالة:</b> <a href='https://t.me/{}?start=nations'>📋 القائمة البيضاء</a>".format(escape_markdown(dispatcher.bot.username))

    if full_info:
        try:
            user_member = chat.get_member(user.id)
            if user_member.status == "left":
                    text += f"\nㅤ<b>التواجد:</b> مش موجود"
            elif user_member.status == "kicked":
                    text += f"\nㅤ<b>التواجد:</b> محظور"
            elif user_member.status == "member":
                    text += f"\nㅤ<b>التواجد:</b> موجود"
                    if not user.id in WHITELISTS:
                        try:
                            from .sql import approve_sql as asql
                            if asql.is_approved(chat.id, user.id):
                                text += "\nㅤ<b>معتمد:</b> ✅ إيه"
                            else:
                                text += "\nㅤ<b>معتمد:</b> ❌ لا"
                        except:
                            pass

            if user_member.status == "administrator":
                result = bot.get_chat_member(chat.id, user.id).to_dict()
                if "custom_title" in result.keys():
                    custom_title = result["custom_title"]
                    text += f"\nㅤ<b>اللقب:</b> <code>{custom_title}</code>"
                else:
                    text += f"\nㅤ<b>التواجد:</b> أدمن"
        except BadRequest:
            pass

        if user.id not in [777000, 1087968824, bot.id]:
            text += "\n"
            for mod in USER_INFO:
                if mod.__mod_name__ == "Users":
                    continue
                try:
                    mod_info = mod.__user_info__(user.id)
                except TypeError:
                    mod_info = mod.__user_info__(user.id, chat.id)
                if mod_info:
                    text += mod_info

        if (
            user.id
            in [777000, 1087968824, dispatcher.bot.id, OWNER_ID, SYS_ADMIN]
            + DEV_USERS
            + SUDO_USERS
            + SUPPORT_USERS
            + WHITELIST_USERS
            + MOD_USERS
            ):
                pass
        else:
            try:
                spamwtc = sw.get_ban(int(user.id))
                if sw.get_ban(int(user.id)):
                    text += "<b>\n🚫 سبام واتش:\n</b>"
                    text += "ㅤ<b>هذا الشخص محظور في سبام واتش!</b>"
                    text += f"\nㅤ<b>السبب:</b> <pre>{spamwtc.reason}</pre>"
                    text += "\nㅤ<b>الاستئناف:</b>  @SpamWatchSupport"
            except:
                pass
            else:
                text += ""
    return text

def get_chat_info(user):
    text = (
        f"<b>💬 معلومات المحادثة:</b>\n"
        f"ㅤ<b>الاسم:</b> {mention_html_chat(user.id, user.title)}"
    )
    if user.username:
        text += f"\nㅤ<b>المعرف:</b> @{html.escape(user.username)}"
    text += f"\nㅤ<b>الآيدي:</b> <code>{user.id}</code>"
    text += f"\nㅤ<b>النوع:</b> {user.type.capitalize()}"

    return text



@kigcmd(command='pfp', pass_args=True)
@spamcheck
def infopfp(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("❌ ما قدرت نستخرج مستخدم من هذا.")
        return

    else:
        return

    text = (
        f"<b>👤 معلومات المستخدم:</b>\n"
        f"ㅤ<b>الاسم الأول:</b> {mention_html(user.id, user.first_name) if user.first_name else mention_html_chat(user.id, user.title)}"
    )
    if user.last_name:
        text += f"\nㅤ<b>الاسم الأخير:</b> {html.escape(user.last_name)}"
    if user.username:
        text += f"\nㅤ<b>المعرف:</b> @{html.escape(user.username)}"
    text += f"\nㅤ<b>الآيدي:</b> <code>{user.id}</code>"

    if not INFOPIC:
        text += "\n❌ هذا الشخص ما عنده صورة بروفايل\n"
    if INFOPIC:
        try:
            profile = bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])

            _file = _file.download(out=BytesIO())
            _file.seek(0)

            message.reply_photo(
                photo=_file,
                caption=(text),
                parse_mode=ParseMode.HTML,
            )
        except IndexError:
            message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )



@kigcmd(command='echo', pass_args=True)
@sudo_plus
def echo(update: Update, _):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    try:
        message.delete()
    except BadRequest:
        pass

def shell(command):
    process = Popen(command, stdout=PIPE, shell=True, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)

bot_firstname = dispatcher.bot.first_name.split(" ")[0]
@kigcmd(command='markdownhelp', filters=Filters.chat_type.private)
def markdown_help(update: Update, _):
    chat = update.effective_chat
    update.effective_message.reply_text((gs(chat.id, "markdown_help_text".format(bot_firstname))), parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "📌 جرب حوّل الرسالة الجاية ليا، وراح تشوف النتيجة!"
    )
    update.effective_message.reply_text(
        "/save test هذا اختبار للماركداون. _مائل_, *عريض*, `كود`, "
        "[رابط](example.com) [زر](buttonurl:github.com) "
        "[زر2](buttonurl://google.com:same)"
    )

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["ث", "د", "س", "يوم"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

stats_str = '''
'''

@kigcmd(command='uptime', can_disable=False)
@sudo_plus
def uptimee(update: Update, _):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    msg = update.effective_message
    rspnc = "*• ⏱ مدة التشغيل:* " + str(botuptime) + "\n"
    rspnc += "*• 🖥 وقت تشغيل النظام:* " + str(uptime)
    msg.reply_text(rspnc, parse_mode=ParseMode.MARKDOWN)

@kigcmd(command='stats', can_disable=False)
@dev_plus
def stats(update, context):
    db_size = SESSION.execute("SELECT pg_size_pretty(pg_database_size(current_database()))").scalar_one_or_none()
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    status = "*╒═══「 📊 إحصائيات النظام: 」*\n\n"
    status += "*• 🖥 وقت تشغيل النظام:* " + str(uptime) + "\n"
    uname = platform.uname()
    status += "*• 💻 النظام:* " + str(uname.system) + "\n"
    status += "*• 🏷 اسم الجهاز:* " + escape_markdown(str(uname.node)) + "\n"
    status += "*• 📦 الإصدار:* " + escape_markdown(str(uname.release)) + "\n"
    status += "*• ⚙️ المعالج:* " + escape_markdown(str(uname.machine)) + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "*• 🧠 المعالج:* " + str(cpu) + " %\n"
    status += "*• 💾 الرام:* " + str(mem[2]) + " %\n"
    status += "*• 📀 التخزين:* " + str(disk[3]) + " %\n\n"
    status += "*• 🐍 إصدار بايثون:* " + python_version() + "\n"
    status += "*• 🤖 python-telegram-bot:* " + str(ptbver) + "\n"
    status += "*• ⏱ مدة التشغيل:* " + str(botuptime) + "\n"
    status += "*• 🗄 حجم قاعدة البيانات:* " + str(db_size) + "\n"
    kb = [
          [
           InlineKeyboardButton('🏓 بينج', callback_data='pingCB')
          ]
    ]
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        status += f"*• 📝 الكوميت*: `{sha[:9]}`\n"
    except Exception as e:
        status += f"*• 📝 الكوميت*: `{str(e)}`\\n"

    try:
        update.effective_message.reply_text(status +
            "\n*╒═══「 🤖 إحصائيات البوت: 」*\n"
            + "\n".join([mod.__stats__() for mod in STATS])
            + "\n\n⍙ [GitHub](https://github.com/itsLuuke) ⍚ [OdinRobot](https://github.com/OdinRobot) \n\n"
            + "╘══「 by [ルーク](https://t.me/itsLuuke) 」\n",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)
    except BaseException:
        update.effective_message.reply_text(
            (
                (
                    (
                        "\n*🤖 إحصائيات البوت*:\n"
                        + "\n".join(mod.__stats__() for mod in STATS)
                    )
                    + "\n\n⍙ [GitHub](https://github.com/itsLuuke) ⍚ [OdinRobot](https://github.com/OdinRobot) \n\n"
                )
                + "╘══「 by [ルーク](https://t.me/itsLuuke) 」\n"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb),
            disable_web_page_preview=True,
        )

@kigcmd(command='ping')
@sudo_plus
def ping(update: Update, _):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("🏓 جاري الفحص...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text(
        "*🏓 بونج!!!*\n`{}ms`".format(ping_time), parse_mode=ParseMode.MARKDOWN
    )


@kigcallback(pattern=r'^pingCB')
def pingCallback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user.id
    if user != (OWNER_ID|SYS_ADMIN) and user not in SUDO_USERS:
        query.answer('❌ ما عندك صلاحية تستخدم هذا!')
    else:
        start_time = time.time()
        requests.get('https://api.telegram.org')
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 3)
        query.answer('🏓 استجابة تيليجرام: {}ms'.format(ping_time))


def get_help(chat):
    return gs(chat, "misc_help")



__mod_name__ = "⚙️ متنوعات"
