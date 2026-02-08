import re
import ast
import random
import html

from io import BytesIO
from typing import Optional

from .. import log, dispatcher, SUDO_USERS, spamcheck
from .log_channel import loggable
from .helper_funcs.parsing import Types, parse_filler, revertMd2HTML
from .helper_funcs.chat_status import connection_status
from .helper_funcs.misc import build_keyboard
from .helper_funcs.parsing import get_data, ENUM_FUNC_MAP
from .helper_funcs.handlers import MessageHandlerChecker
from .helper_funcs.string_handling import escape_invalid_curly_brackets

from .helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
import tg_bot.modules.sql.notes_sql as sql
from telegram import (
    MAX_MESSAGE_LENGTH,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    InlineKeyboardButton,
)
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html
from telegram.ext import (
    CallbackContext,
    Filters,
)

from .helper_funcs.extraction import extract_user

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

# ==================== الأوامر العربية ====================
ARABIC_GET_COMMANDS = ["جيب", "اعطني", "الملاحظة", "جلب"]
ARABIC_SAVE_COMMANDS = ["احفظ", "حفظ", "سجل"]
ARABIC_CLEAR_COMMANDS = ["امسح", "حذف_ملاحظة", "مسح_ملاحظة"]
ARABIC_NOTES_COMMANDS = ["الملاحظات", "ملاحظات", "المحفوظات"]
ARABIC_CLEARALL_COMMANDS = ["مسح_الكل", "حذف_كل_الملاحظات"]


# Do not async
def get(update: Update, context: CallbackContext, notename: str, show_none: bool = True, no_format: bool = False):
    # sourcery no-metrics
    bot = context.bot
    chat_id = update.effective_message.chat.id
    note_chat_id = update.effective_chat.id
    note = sql.get_note(note_chat_id, notename)
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user
    preview = True
    protect = False
    parseMode = ParseMode.HTML

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        VALID_NOTE_FORMATTERS = [
            "first",
            "last",
            "fullname",
            "username",
            "id",
            "chatname",
            "mention",
            "user",
            "admin",
            "preview",
            "protect",
        ]
        if valid_format := escape_invalid_curly_brackets(note.value, VALID_NOTE_FORMATTERS):
            if not no_format and "%%%" in valid_format:
                split = valid_format.split("%%%")
                text = random.choice(split) if all(split) else valid_format
            else:
                text = valid_format

            dont_send, preview, protect, text = parse_filler(update, user.id, text)

            if dont_send:
                return

        else:
            text = ""

        keyb = []
        buttons = sql.get_buttons(note_chat_id, notename)
        if no_format:
            text = revertMd2HTML(text, buttons)
        else:
            keyb = build_keyboard(buttons)

        keyboard = InlineKeyboardMarkup(keyb)

        try:
            if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                bot.send_message(
                        chat_id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        reply_markup=keyboard,
                        disable_web_page_preview=bool(preview),
                        protect_content=bool(protect)
                )
            elif ENUM_FUNC_MAP[note.msgtype] == dispatcher.bot.send_sticker:
                ENUM_FUNC_MAP[note.msgtype](
                        chat_id,
                        note.file,
                        reply_to_message_id=reply_id,
                        reply_markup=keyboard,
                )
            else:
                ENUM_FUNC_MAP[note.msgtype](
                        chat_id,
                        note.file,
                        caption=text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        reply_markup=keyboard,
                        protect_content=bool(protect)
                )

        except BadRequest as excp:
            if excp.message == "Entity_mention_user_invalid":
                message.reply_text(
                        "⚠️ يبدو إنك حاولت تذكر شخص ما شفته قبل. لو تبي تذكره، "
                    "حوّل لي رسالة منه، وحنقدر نعمل له تاق!"
                )
            elif FILE_MATCHER.match(note.value):
                message.reply_text(
                        "⚠️ هذي الملاحظة كانت ملف مستورد بشكل خاطئ من بوت ثاني - ما نقدر نستخدمها. "
                    "لو محتاجها فعلاً، لازم تحفظها من جديد. "
                    "في هالوقت، حنشيلها من قائمة الملاحظات."
                )
                sql.rm_note(chat_id, notename)
            else:
                message.reply_text(
                        "⚠️ هذي الملاحظة ما قدرت تتبعث، لأن فيها مشكلة في التنسيق. "
                    "جرب تجيب النسخة الخام أو اسأل في @TheBotsSupport لو ما عرفت السبب!"
                )
                log.exception(
                        "Could not parse message #%s in chat %s\n\nare you sure it's using the new format?",
                        notename, str(note_chat_id))
                log.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("⚠️ هذي الملاحظة مش موجودة!")


@kigcmd(command="get")
@spamcheck
@connection_status
def cmd_get(update: Update, context: CallbackContext):
    args = context.args
    if len(args) >= 2:
        get(update, context, args[0].lower(), show_none=True, no_format=bool(args[1].lower() in ["raw", "noformat", "خام"]))
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("⚠️ حدد اسم الملاحظة!")


# ==================== معالج عربي لجلب الملاحظة ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_GET_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
def arabic_cmd_get(update: Update, context: CallbackContext):
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_GET_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    args = text.split() if text else []
    
    if len(args) >= 2:
        get(update, context, args[0].lower(), show_none=True, no_format=bool(args[1].lower() in ["raw", "noformat", "خام"]))
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        message.reply_text("⚠️ حدد اسم الملاحظة!")


@kigmsg((Filters.regex(r"^#[^\s]+")), group=-14, friendly='get')
@spamcheck
@connection_status
def hash_get(update: Update, context: CallbackContext):
    msg = update.effective_message.text.split()
    no_hash = msg[0][1:].lower()
    if len(msg) >= 2:
        return get(update, context, no_hash, show_none=False, no_format=msg[1].lower() in ["raw", "noformat", "خام"])

    get(update, context, no_hash, show_none=False)


@kigmsg((Filters.regex(r"^[/!>]\d+$")), group=-16, friendly='get')
@spamcheck
@connection_status
def slash_get(update: Update, context: CallbackContext):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        get(update, context, note_name, show_none=False)
    except IndexError:
        update.effective_message.reply_text("⚠️ رقم الملاحظة غلط!")


@kigcmd(command='save')
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def save(update: Update, _: CallbackContext) -> Optional[str]:
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat
    user = update.effective_user

    m = msg.text.split(' ', 1)
    if len(m) == 1:
        msg.reply_text("⚠️ أعطني شي نحفظه!")
        return
    note_name, text, data_type, content, buttons = get_data(msg)
    note_name = note_name.lower()
    if data_type == Types.TEXT and len(text.strip()) == 0:
        msg.reply_text("⚠️ تبيني أحفظ... ولا شي؟")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )

    logmsg = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#حفظ_ملاحظة\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>الملاحظة:</b> {note_name}"
    )

    msg.reply_text(
        f"✅ تم حفظ الملاحظة `{note_name}`!",
        parse_mode=ParseMode.MARKDOWN,
    )

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot and not msg.text:
        msg.reply_text(
            "⚠️ البوتات عندها قيود من تيليجرام، يصعب على البوتات التعامل مع بوتات ثانية، "
            "فما قدرت أحفظ هالرسالة زي العادة - تقدر تحولها وتحفظ الرسالة الجديدة؟"
        )
    return logmsg


# ==================== معالج عربي لحفظ الملاحظة ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_SAVE_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def arabic_save(update: Update, _: CallbackContext) -> Optional[str]:
    chat_id = update.effective_chat.id
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    text = msg.text
    for cmd in ARABIC_SAVE_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text and not msg.reply_to_message:
        msg.reply_text("⚠️ أعطني شي نحفظه!\nالاستخدام: احفظ اسم_الملاحظة المحتوى")
        return
    
    # إذا كان رد على رسالة
    if msg.reply_to_message:
        note_name, text, data_type, content, buttons = get_data(msg)
    else:
        parts = text.split(None, 1)
        if len(parts) < 2:
            msg.reply_text("⚠️ الاستخدام: احفظ اسم_الملاحظة المحتوى")
            return
        note_name = parts[0].lower()
        note_text = parts[1]
        data_type = Types.TEXT
        content = None
        buttons = []
        text = note_text
    
    note_name = note_name.lower()
    
    if data_type == Types.TEXT and len(text.strip()) == 0:
        msg.reply_text("⚠️ تبيني أحفظ... ولا شي؟")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )

    logmsg = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#حفظ_ملاحظة\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>الملاحظة:</b> {note_name}"
    )

    msg.reply_text(
        f"✅ تم حفظ الملاحظة `{note_name}`!",
        parse_mode=ParseMode.MARKDOWN,
    )

    return logmsg


@kigcmd(command='clear')
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def clear(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    chat_id = chat.id
    user = update.effective_user

    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text(f"✅ تم حذف الملاحظة '{notename}'.")
            logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#حذف_ملاحظة\n"
                    f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                    f"<b>الملاحظة:</b> {notename}"
            )
            return logmsg
        else:
            update.effective_message.reply_text("⚠️ هذي الملاحظة مش موجودة عندي!")
            return ''
    else:
        update.effective_message.reply_text("⚠️ حدد اسم الملاحظة!")
        return ''


# ==================== معالج عربي لحذف الملاحظة ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_CLEAR_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
def arabic_clear(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    chat = update.effective_chat
    chat_id = chat.id
    user = update.effective_user

    text = message.text
    for cmd in ARABIC_CLEAR_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        notename = text.split()[0].lower()

        if sql.rm_note(chat_id, notename):
            message.reply_text(f"✅ تم حذف الملاحظة '{notename}'.")
            logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#حذف_ملاحظة\n"
                    f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                    f"<b>الملاحظة:</b> {notename}"
            )
            return logmsg
        else:
            message.reply_text("⚠️ هذي الملاحظة مش موجودة عندي!")
            return ''
    else:
        message.reply_text("⚠️ حدد اسم الملاحظة!")
        return ''


@kigcmd(command=['removeallnotes', 'clearall'])
@spamcheck
def clearall(update: Update, _: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يمسح كل الملاحظات مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🗑 حذف كل الملاحظات", callback_data="notes_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="notes_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تحذف كل الملاحظات في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


# ==================== معالج عربي لحذف كل الملاحظات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_CLEARALL_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_clearall(update: Update, _: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يمسح كل الملاحظات مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="🗑 حذف كل الملاحظات", callback_data="notes_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="notes_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تحذف كل الملاحظات في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@kigcallback(pattern=r"notes_.*")
@loggable
def clearall_btn(update: Update, _: CallbackContext) -> str:
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "notes_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                message.edit_text("✅ تم حذف كل الملاحظات!")

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#حذف_كل_الملاحظات\n"
                    f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
                )
                return log_message

            except BadRequest:
                return ""

        if member.status == "administrator":
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""

        if member.status == "member":
            query.answer("⚠️ لازم تكون مشرف باش تسوي هالشي.")
            return ""
    elif query.data == "notes_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            message.edit_text("❌ تم إلغاء حذف الملاحظات.")
            return ""
        if member.status == "administrator":
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""
        if member.status == "member":
            query.answer("⚠️ لازم تكون مشرف باش تسوي هالشي.")
            return ""


@kigcmd(command=["notes", "saved"])
@spamcheck
@connection_status
def list_notes(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "📝 جيب الملاحظة بـ `/رقم` أو `#اسم_الملاحظة` \n\n  *الرقم*    *الملاحظة* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name
    if not note_list:
        update.effective_message.reply_text("📭 ما في ملاحظات في هالمجموعة!")

    elif msg != '':
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


# ==================== معالج عربي لعرض الملاحظات ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_NOTES_COMMANDS) + r')$'), group=3)
@spamcheck
@connection_status
def arabic_list_notes(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "📝 جيب الملاحظة بـ `/رقم` أو `#اسم_الملاحظة` \n\n  *الرقم*    *الملاحظة* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name
    if not note_list:
        update.effective_message.reply_text("📭 ما في ملاحظات في هالمجموعة!")

    elif msg != '':
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):  # sourcery no-metrics
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            if notedata := notedata[match.end():].strip():
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        elif matchsticker:
            if content := notedata[matchsticker.end():].strip():
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.STICKER, file=content
                )
        elif matchbtn:
            parse = notedata[matchbtn.end():].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            if buttons := ast.literal_eval(buttons):
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end():].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            if content := file[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.DOCUMENT, file=content
                )
        elif matchphoto:
            photo = notedata[matchphoto.end():].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            if content := photo[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.PHOTO, file=content
                )
        elif matchaudio:
            audio = notedata[matchaudio.end():].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            if content := audio[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.AUDIO, file=content
                )
        elif matchvoice:
            voice = notedata[matchvoice.end():].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            if content := voice[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VOICE, file=content
                )
        elif matchvideo:
            video = notedata[matchvideo.end():].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            if content := video[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO, file=content
                )
        elif matchvn:
            video_note = notedata[matchvn.end():].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            if content := video_note[0]:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO_NOTE, file=content
                )
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="⚠️ هالملفات/الصور ما قدرت تتستورد لأنها جاية من بوت ثاني. "
                "هذا قيد من تيليجرام، وما نقدر نتجاوزه. معذرة على الإزعاج!",
            )


def __stats__():
    return f"• {sql.num_notes()} ملاحظة، في {sql.num_chats()} مجموعة."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    notes = sql.get_all_chat_notes(chat_id)
    return f"في `{len(notes)}` ملاحظة في هالمجموعة."


from .language import gs


def get_help(chat):
    return gs(chat, "notes_help")


__mod_name__ = "الملاحظات"
