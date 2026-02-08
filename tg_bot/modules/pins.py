import html
from typing import Optional

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from tg_bot import SUDO_USERS, spamcheck, dispatcher

from .helper_funcs.chat_status import connection_status
from .helper_funcs.string_handling import escape_invalid_curly_brackets
from .log_channel import loggable
from .language import gs
from .helper_funcs.decorators import kigcmd, kigcallback, kigmsg
from .helper_funcs.parsing import Types, VALID_FORMATTERS, get_data, ENUM_FUNC_MAP, build_keyboard_from_list
from .sql.antilinkedchannel_sql import enable_linked
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.parsemode import ParseMode

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
)

# ==================== الأوامر العربية ====================
ARABIC_PINNED_COMMANDS = ["المثبت", "المثبتة", "الرسالة_المثبتة"]
ARABIC_PIN_COMMANDS = ["ثبت", "تثبيت"]
ARABIC_UNPIN_COMMANDS = ["الغاء_التثبيت", "فك_التثبيت", "الغي_التثبيت"]
ARABIC_UNPINALL_COMMANDS = ["الغاء_كل_التثبيت", "فك_كل_التثبيت"]
ARABIC_PERMAPIN_COMMANDS = ["تثبيت_دائم", "ثبت_دائم"]


@kigcmd(command="pinned", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
def pinned(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        message_link = f"https://t.me/c/{str(chat.id)[4:]}/{pinned_id}"

        msg.reply_text(
            f"📌 اضغط الزر تحت باش تروح للرسالة المثبتة في {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📌 الرسالة المثبتة",
                            url=message_link,
                        )
                    ]
                ]
            ),
        )

    else:
        msg.reply_text(
            f"⚠️ ما في رسالة مثبتة في <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


# ==================== معالج عربي للرسالة المثبتة ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_PINNED_COMMANDS) + r')$'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
def arabic_pinned(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    msg_id = msg.message_id

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        message_link = f"https://t.me/c/{str(chat.id)[4:]}/{pinned_id}"

        msg.reply_text(
            f"📌 اضغط الزر تحت باش تروح للرسالة المثبتة في {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📌 الرسالة المثبتة",
                            url=message_link,
                        )
                    ]
                ]
            ),
        )

    else:
        msg.reply_text(
            f"⚠️ ما في رسالة مثبتة في <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


@kigcmd(command="pin", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
def pin(update: Update, context: CallbackContext) -> Optional[str]:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    message_link = f"https://t.me/c/{str(chat.id)[4:]}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        msg.reply_text("⚠️ رد على رسالة باش أثبتها!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() != "loud"
            or args[0].lower() != "violent"
            or args[0].lower() != "تنبيه"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            msg.reply_text(
                "📌 تم تثبيت الرسالة في <b>{}</b>!".format(html.escape(chat.title)),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 عرض الرسالة", url=f"{message_link}"
                            ),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تثبيت\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
            f"\n<b>الرسالة:</b> <a href='{message_link}'>الرسالة المثبتة</a>\n"
        )

        return log_message


# ==================== معالج عربي للتثبيت ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_PIN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods=True)
@loggable
def arabic_pin(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    
    text = msg.text
    for cmd in ARABIC_PIN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    prev_message = msg.reply_to_message

    if prev_message is None:
        msg.reply_text("⚠️ رد على رسالة باش أثبتها!")
        return

    msg_id = prev_message.message_id
    message_link = f"https://t.me/c/{str(chat.id)[4:]}/{msg_id}"

    is_silent = True
    if text:
        is_silent = text.lower() not in ["notify", "loud", "تنبيه", "بصوت"]

    try:
        bot.pinChatMessage(
            chat.id, prev_message.message_id, disable_notification=is_silent
        )
        msg.reply_text(
            "📌 تم تثبيت الرسالة في <b>{}</b>!".format(html.escape(chat.title)),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📝 عرض الرسالة", url=f"{message_link}"
                        ),
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except BadRequest as excp:
        if excp.message != "Chat_not_modified":
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#تثبيت\n"
        f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
        f"\n<b>الرسالة:</b> <a href='{message_link}'>الرسالة المثبتة</a>\n"
    )

    return log_message


@kigcmd(command="unpin", can_disable=False)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    reply_msg = message.reply_to_message
    if not reply_msg:
        try:
            bot.unpinChatMessage(chat.id)
            dispatcher.bot.sendMessage(chat.id, "✅ تم إلغاء تثبيت آخر رسالة مثبتة بنجاح!", parse_mode=ParseMode.MARKDOWN)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"⚠️ ما قدرت ألغي التثبيت لسبب ما.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إلغاء_التثبيت\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

    else:
        unpinthis = reply_msg.message_id
        try:
            bot.unpinChatMessage(chat.id, unpinthis)

            pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], unpinthis)

            message.reply_text(
                "✅ تم إلغاء تثبيت الرسالة في <b>{}</b>!".format(html.escape(chat.title)),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 عرض الرسالة", url=f"{pinmsg}"
                            ),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"⚠️ ما قدرت ألغي التثبيت لسبب ما.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إلغاء_التثبيت\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message


# ==================== معالج عربي لإلغاء التثبيت ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_UNPIN_COMMANDS) + r')$'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods=True)
@loggable
def arabic_unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    reply_msg = message.reply_to_message
    if not reply_msg:
        try:
            bot.unpinChatMessage(chat.id)
            message.reply_text("✅ تم إلغاء تثبيت آخر رسالة مثبتة بنجاح!")
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                message.reply_text("⚠️ ما قدرت ألغي التثبيت لسبب ما.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إلغاء_التثبيت\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

    else:
        unpinthis = reply_msg.message_id
        try:
            bot.unpinChatMessage(chat.id, unpinthis)

            pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], unpinthis)

            message.reply_text(
                "✅ تم إلغاء تثبيت الرسالة في <b>{}</b>!".format(html.escape(chat.title)),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 عرض الرسالة", url=f"{pinmsg}"
                            ),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                message.reply_text("⚠️ ما قدرت ألغي التثبيت لسبب ما.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#إلغاء_التثبيت\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message


@kigcmd(command="unpinall", filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@spamcheck
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يلغي تثبيت كل الرسائل مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📌 إلغاء تثبيت الكل", callback_data="pinned_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="pinned_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تلغي تثبيت كل الرسائل في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


# ==================== معالج عربي لإلغاء تثبيت الكل ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_UNPINALL_COMMANDS) + r')$'), group=3)
@spamcheck
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods=True)
def arabic_rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "⚠️ بس مالك المجموعة يقدر يلغي تثبيت كل الرسائل مرة وحدة."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📌 إلغاء تثبيت الكل", callback_data="pinned_rmall"
                    )
                ],
                [InlineKeyboardButton(text="❌ إلغاء", callback_data="pinned_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"⚠️ هل أنت متأكد تبي تلغي تثبيت كل الرسائل في {chat.title}؟ هالعملية ما تقدر تتراجع عنها!",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@kigcallback(pattern=r"pinned_.*")
@loggable
def unpin_callback(update, context: CallbackContext) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    bot = context.bot
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "pinned_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:

            try:
                bot.unpinAllChatMessages(chat.id)
            except BadRequest as excp:
                if excp.message == "Chat_not_modified":
                    pass
                else:
                    raise
            msg.edit_text(f"✅ تم إلغاء تثبيت كل الرسائل في {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#إلغاء_تثبيت_الكل\n"
                f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        else:
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""

    elif query.data == "pinned_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("❌ تم إلغاء العملية.")
            return ""
        else:
            query.answer("⚠️ بس مالك المجموعة يقدر يسوي هالشي.")
            return ""


@kigcmd(command="permapin", run_async = True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
def permapin(update: Update, ctx: CallbackContext) -> Optional[str]:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    bot = ctx.bot
    preview = True
    protect = False

    m = msg.text.split(' ', 1)
    if len(m) == 1 and not msg.reply_to_message:
        msg.reply_text("⚠️ أعطني شي نثبته!")
        return
    _, text, data_type, content, buttons = get_data(msg, True)
    if text == "":
        msg.reply_text("⚠️ تبيني أثبت... ولا شي؟")
        return
    msg.delete()
    keyboard = InlineKeyboardMarkup(build_keyboard_from_list(buttons))

    if escape_invalid_curly_brackets(text, VALID_FORMATTERS):
        if "{admin}" in text and user_is_admin(update, user.id):
            return
        if "{user}" in text and not user_is_admin(update, user.id):
            return
        if "{preview}" in text:
            preview = False
        if "{protect}" in text:
            protect = True
        text = text.format(
                first = html.escape(msg.from_user.first_name),
                last = html.escape(
                        msg.from_user.last_name
                        or msg.from_user.first_name,
                ),
                fullname = html.escape(
                        " ".join(
                                [
                                    msg.from_user.first_name,
                                    msg.from_user.last_name or "",
                                ]
                        ),
                ),
                username = f'@{msg.from_user.username}'
                if msg.from_user.username
                else mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                mention = mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                chatname = html.escape(
                        msg.chat.title
                        if msg.chat.type != "private"
                        else msg.from_user.first_name,
                ),
                id = msg.from_user.id,
                user = "",
                admin = "",
                preview = "",
                protect = "",
        )

    else:
        text = ""

    try:
        if data_type in (Types.BUTTON_TEXT, Types.TEXT):
            pin_this = bot.send_message(
                chat.id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=bool(preview),
                protect_content=bool(protect)
            )
        elif ENUM_FUNC_MAP[data_type] == dispatcher.bot.send_sticker:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                reply_markup=keyboard,
            )
        else:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                protect_content=bool(protect)
            )

        bot.pinChatMessage(chat.id, pin_this.message_id, disable_notification=False)

        enable_linked(chat.id)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تثبيت_دائم\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
            f"\n<b>الرسالة:</b> <a href='t.me/c/{str(chat.id)[4:]}''>الرسالة المثبتة</a>\n"
        )
        return log_message

    except BadRequest as excp:
        if excp.message == "Entity_mention_user_invalid":
            msg.reply_text(
                "⚠️ يبدو إنك حاولت تذكر شخص ما شفته قبل. لو تبي تذكره، "
                "حوّل لي رسالة منه، وحنقدر نعمل له تاق!"
            )
        else:
            msg.reply_text(
                "⚠️ ما قدرت أثبت الرسالة. الخطأ: <code>{}</code>".format(
                    excp.message
                ),
                parse_mode=ParseMode.HTML,
            )
        return


# ==================== معالج عربي للتثبيت الدائم ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_PERMAPIN_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
def arabic_permapin(update: Update, ctx: CallbackContext) -> Optional[str]:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    bot = ctx.bot
    preview = True
    protect = False

    text = msg.text
    for cmd in ARABIC_PERMAPIN_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    if not text and not msg.reply_to_message:
        msg.reply_text("⚠️ أعطني شي نثبته!")
        return
    
    _, note_text, data_type, content, buttons = get_data(msg, True)
    if note_text == "":
        msg.reply_text("⚠️ تبيني أثبت... ولا شي؟")
        return
    msg.delete()
    keyboard = InlineKeyboardMarkup(build_keyboard_from_list(buttons))

    if escape_invalid_curly_brackets(note_text, VALID_FORMATTERS):
        if "{admin}" in note_text and user_is_admin(update, user.id):
            return
        if "{user}" in note_text and not user_is_admin(update, user.id):
            return
        if "{preview}" in note_text:
            preview = False
        if "{protect}" in note_text:
            protect = True
        note_text = note_text.format(
                first = html.escape(msg.from_user.first_name),
                last = html.escape(
                        msg.from_user.last_name
                        or msg.from_user.first_name,
                ),
                fullname = html.escape(
                        " ".join(
                                [
                                    msg.from_user.first_name,
                                    msg.from_user.last_name or "",
                                ]
                        ),
                ),
                username = f'@{msg.from_user.username}'
                if msg.from_user.username
                else mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                mention = mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                chatname = html.escape(
                        msg.chat.title
                        if msg.chat.type != "private"
                        else msg.from_user.first_name,
                ),
                id = msg.from_user.id,
                user = "",
                admin = "",
                preview = "",
                protect = "",
        )

    else:
        note_text = ""

    try:
        if data_type in (Types.BUTTON_TEXT, Types.TEXT):
            pin_this = bot.send_message(
                chat.id,
                note_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=bool(preview),
                protect_content=bool(protect)
            )
        elif ENUM_FUNC_MAP[data_type] == dispatcher.bot.send_sticker:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                reply_markup=keyboard,
            )
        else:
            pin_this = ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                caption=note_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                protect_content=bool(protect)
            )

        bot.pinChatMessage(chat.id, pin_this.message_id, disable_notification=False)

        enable_linked(chat.id)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تثبيت_دائم\n"
            f"<b>المشرف:</b> {mention_html(user.id, html.escape(user.first_name))}"
            f"\n<b>الرسالة:</b> <a href='t.me/c/{str(chat.id)[4:]}''>الرسالة المثبتة</a>\n"
        )
        return log_message

    except BadRequest as excp:
        if excp.message == "Entity_mention_user_invalid":
            msg.reply_text(
                "⚠️ يبدو إنك حاولت تذكر شخص ما شفته قبل. لو تبي تذكره، "
                "حوّل لي رسالة منه، وحنقدر نعمل له تاق!"
            )
        else:
            msg.reply_text(
                "⚠️ ما قدرت أثبت الرسالة. الخطأ: <code>{}</code>".format(
                    excp.message
                ),
                parse_mode=ParseMode.HTML,
            )
        return


def get_help(chat):
    return gs(chat, "pins_help")

__mod_name__ = "التثبيت"
