from typing import Optional

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import dispatcher, spamcheck
from .helper_funcs.string_handling import markdown_parser
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters
from telegram.utils.helpers import escape_markdown
from .helper_funcs.decorators import kigcmd, kigmsg

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

# ==================== الأوامر العربية ====================
ARABIC_RULES_COMMANDS = ["القوانين", "قوانين", "الشروط", "القواعد"]
ARABIC_SETRULES_COMMANDS = ["تعيين_القوانين", "ضع_القوانين", "اضف_قوانين", "حدد_القوانين"]
ARABIC_CLEARRULES_COMMANDS = ["مسح_القوانين", "حذف_القوانين", "ازالة_القوانين"]


@kigcmd(command='rules', filters=Filters.chat_type.groups)
def get_rules(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# ==================== معالج عربي لعرض القوانين ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_RULES_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_get_rules(update: Update, _: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message != "Chat not found" or not from_pm:
            raise

        bot.send_message(
            user.id,
            "⚠️ رابط القوانين لهالمجموعة ما تم ضبطه صح! اطلب من المشرفين يصلحوه.\n"
            "يمكن نسوا الشرطة في الآيدي",
        )
        return
    rules = sql.get_rules(chat_id)
    text = f"📜 قوانين *{escape_markdown(chat.title)}* هي:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id, text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "⚠️ المشرفين ما حددوا قوانين لهالمجموعة بعد.\n"
            "لكن هذا ما يعني إنها بدون قوانين...!",
        )
    elif rules:
        btn = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📜 القوانين", url=f"t.me/{bot.username}?start={chat_id}"
                        )
                    ]
                ]
        )
        txt = "📋 اضغط على الزر تحت باش تشوف القوانين."
        if not message.reply_to_message:
            message.reply_text(txt, reply_markup=btn)

        if message.reply_to_message:
            message.reply_to_message.reply_text(txt, reply_markup=btn)
    else:
        update.effective_message.reply_text(
            "⚠️ المشرفين ما حددوا قوانين لهالمجموعة بعد.\n"
            "لكن هذا ما يعني إنها بدون قوانين...!"
        )


@kigcmd(command='setrules', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("✅ تم تعيين قوانين المجموعة بنجاح!")
    else:
        update.effective_message.reply_text("⚠️ أعطني القوانين اللي تبي تحطها!")


# ==================== معالج عربي لتعيين القوانين ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_SETRULES_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
def arabic_set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    text = msg.text
    for cmd in ARABIC_SETRULES_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if text:
        offset = len(text) - len(msg.text)
        markdown_rules = markdown_parser(
            text, entities=msg.parse_entities(), offset=offset
        )

        sql.set_rules(chat_id, markdown_rules)
        msg.reply_text("✅ تم تعيين قوانين المجموعة بنجاح!")
    else:
        msg.reply_text("⚠️ أعطني القوانين اللي تبي تحطها!\n\nمثال:\nتعيين_القوانين\n1. احترم الجميع\n2. ممنوع السبام")


@kigcmd(command='clearrules', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("✅ تم مسح القوانين بنجاح!")


# ==================== معالج عربي لمسح القوانين ====================
@kigmsg(Filters.chat_type.groups & Filters.regex(r'^(' + '|'.join(ARABIC_CLEARRULES_COMMANDS) + r')$'), group=3)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
def arabic_clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    sql.set_rules(chat_id, "")
    msg.reply_text("✅ تم مسح القوانين بنجاح!")


def __stats__():
    return f"• {sql.num_chats()} مجموعة عندها قوانين."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"هالمجموعة عندها قوانين: `{bool(sql.get_rules(chat_id))}`"


from .language import gs


def get_help(chat):
    return gs(chat, "rules_help")


__mod_name__ = "القوانين"
