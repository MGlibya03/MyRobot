import html
import random
import re
import time
from functools import partial
from io import BytesIO
import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import (
    DEV_USERS,
    MESSAGE_DUMP,
    MOD_USERS,
    SYS_ADMIN,
    log,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    spamcheck,
    sw,
    dispatcher,
)
from .helper_funcs.misc import build_keyboard, revert_buttons
from .helper_funcs.msg_types import get_welcome_type
from .helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
)
from .log_channel import loggable
from .sql.antispam_sql import is_user_gbanned
from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update, User,
)
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    CallbackContext,
    Filters, ChatMemberHandler, MessageHandler,
)
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
)
import tg_bot.modules.sql.log_channel_sql as logsql

from ..import sibylClient
from .sql.sibylsystem_sql import does_chat_sibylban
from SibylSystem import GeneralException
from .cron_jobs import j

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}

VERIFIED_USER_WAITLIST = {}
CAPTCHA_ANS_DICT = {}
WELCOME_GROUP = 7

from multicolorcaptcha import CaptchaGenerator

WHITELISTED = [OWNER_ID, SYS_ADMIN] + DEV_USERS + SUDO_USERS + SUPPORT_USERS + WHITELIST_USERS + MOD_USERS

# do not async
def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    try:
        msg = dispatcher.bot.send_message(chat.id,
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            allow_sending_without_reply=True,
        )
    except BadRequest as excp:
        if excp.message == 'Button_url_invalid':
            msg = dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    (
                            backup_message
                            + '\nملاحظة: الرسالة الحالية فيها رابط زر غلط. الرجاء تحديثه.'
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        elif excp.message == 'Have no rights to send a message':
            return
        elif excp.message == 'Reply message not found':
            msg = dispatcher.bot.send_message(chat.id,
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                quote=False,
            )

        elif excp.message == 'Unsupported url protocol':
            msg = dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    (
                            backup_message
                            + '\nملاحظة: الرسالة فيها أزرار بروابط مش مدعومة من تيليجرام. الرجاء تحديثها.'
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        elif excp.message == 'Wrong url host':
            msg = dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    (
                            backup_message
                            + '\nملاحظة: الرسالة فيها روابط غلط. الرجاء تحديثها.'
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

            log.warning(message)
            log.warning(keyboard)
            log.exception('Could not parse! got invalid url host errors')
        else:
            msg = dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    (
                            backup_message
                            + '\nملاحظة: صار خطأ وقت إرسال الرسالة المخصصة. الرجاء تحديثها.'
                    )
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

            log.exception()
    return msg


def welcomeFilter(update: Update, context: CallbackContext):
    if update.effective_chat.type != "group" and update.effective_chat.type != "supergroup":
        return
    if nm := update.chat_member.new_chat_member:
        om = update.chat_member.old_chat_member
        if nm.status == nm.MEMBER and (om.status == nm.KICKED or om.status == nm.LEFT):
            return new_member(update, context)
        if (nm.status == nm.KICKED or nm.status == nm.LEFT) and \
                (om.status == nm.MEMBER or om.status == nm.ADMINISTRATOR or om.status == nm.CREATOR):
            return left_member(update, context)


dispatcher.add_handler(ChatMemberHandler(welcomeFilter, ChatMemberHandler.CHAT_MEMBER, run_async=True), group=WELCOME_GROUP)


def new_member(update: Update, context: CallbackContext):
    bot, job_queue = context.bot, context.job_queue
    chat = update.effective_chat
    user = update.effective_user
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(logsql.LogChannelSettings(chat.id, True, True, True, True, True))
        log_setting = logsql.get_chat_setting(chat.id)
    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)
    raid, _, deftime = sql.getRaidStatus(str(chat.id))

    new_mem = update.chat_member.new_chat_member.user

    welcome_log = None
    res = None
    sent = None
    should_mute = True
    welcome_bool = True
    media_wel = False

    if raid and new_mem.id not in WHITELISTED:
        bantime = deftime
        try:
            chat.ban_member(new_mem.id, until_date=bantime)
            return
        except:
            pass
    if sw is not None:
        sw_ban = sw.get_ban(new_mem.id)
        if sw_ban:
            return

    data = None
    if sibylClient and does_chat_sibylban(chat.id):
        try:
            data = sibylClient.get_info(user.id)
        except GeneralException:
            pass
        except BaseException as e:
            log.error(e)
            pass
        if data and data.banned:
            return

    if should_welc:

        # ترحيب خاص بالمالك
        if new_mem.id == OWNER_ID:
            bot.send_message(chat.id,
                "هلا بالمعلم! نورت يا صاحبي 👑💚",
            )
            welcome_log = (
                f"{html.escape(chat.title)}\n"
                f"#انضمام_عضو\n"
                f"صاحب البوت انضم للقروب"
            )
            return

        # ترحيب بالمطورين
        elif new_mem.id in DEV_USERS:
            bot.send_message(chat.id,
                "وااو! مطور من مطورين البوت انضم! 👨‍💻✨",
            )
            return

        # ترحيب بالسودو
        elif new_mem.id in SUDO_USERS:
            bot.send_message(chat.id,
                "هاه! مستخدم سودو انضم! انتبهوا يا جماعة! 🛡️",
            )
            return

        # ترحيب بالدعم
        elif new_mem.id in SUPPORT_USERS:
            bot.send_message(chat.id,
                "هاه! واحد من فريق الدعم انضم! 💪",
            )
            return

        # ترحيب بالقائمة البيضاء
        elif new_mem.id in WHITELIST_USERS:
            bot.send_message(chat.id,
                "أوف! واحد من القائمة البيضاء انضم! 📋",
            )
            return

        # ترحيب بالمشرفين
        elif new_mem.id in MOD_USERS:
            bot.send_message(chat.id,
                "آه! مشرف انضم! 🛡️",
            )
            return

        # ترحيب بالبوت نفسه
        elif new_mem.id == bot.id:
            bot.send_message(chat.id,
                "هلا والله! شكراً لإضافتي! 🤖💚",
            )
            return

        else:
            buttons = sql.get_welc_buttons(chat.id)
            keyb = build_keyboard(buttons)

            if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                media_wel = True

            first_name = (
                    new_mem.first_name or "شخص بدون اسم"
            )

            if cust_welcome:
                if cust_welcome == sql.DEFAULT_WELCOME:
                    cust_welcome = random.choice(
                        sql.DEFAULT_WELCOME_MESSAGES
                    ).format(first=escape_markdown(first_name))

                if new_mem.last_name:
                    fullname = escape_markdown(f"{first_name} {new_mem.last_name}")
                else:
                    fullname = escape_markdown(first_name)
                count = chat.get_member_count()
                mention = mention_markdown(new_mem.id, escape_markdown(first_name))
                if new_mem.username:
                    username = "@" + escape_markdown(new_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_welcome, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(new_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=new_mem.id,
                )

            else:
                res = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                    first=escape_markdown(first_name)
                )
                keyb = []

            backup_message = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                first=escape_markdown(first_name)
            )
            keyboard = InlineKeyboardMarkup(keyb)

    else:
        welcome_bool = False
        res = None
        keyboard = None
        backup_message = None
        reply = None

    if (
            chat.get_member(new_mem.id).status in ["creator", "administrator"]
            or human_checks
    ):
        should_mute = False
    if new_mem.is_bot:
        should_mute = False

    if user.id == new_mem.id and should_mute:
        if welc_mutes == "soft":
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_add_web_page_previews=False,
                ),
                until_date=(int(time.time() + 24 * 60 * 60)),
            )
            sql.set_human_checks(user.id, chat.id)
        if welc_mutes == "strong":
            welcome_bool = False
            if not media_wel:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "media_wel": False,
                            "status": False,
                            "update": update,
                            "res": res,
                            "keyboard": keyboard,
                            "backup_message": backup_message,
                        }
                    }
                )
            else:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "chat_id": chat.id,
                            "status": False,
                            "media_wel": True,
                            "cust_content": cust_content,
                            "welc_type": welc_type,
                            "res": res,
                            "keyboard": keyboard,
                        }
                    }
                )
            new_join_mem = f"[{escape_markdown(new_mem.first_name)}](tg://user?id={user.id})"
            message = bot.send_message(chat.id,
                f"🔐 {new_join_mem}، اضغط الزر تحت باش تثبت إنك مش بوت.\nعندك 120 ثانية.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="✅ ايه، أنا إنسان",
                                callback_data=f"user_join_({new_mem.id})",
                            )
                        ]
                    ]
                ),
                parse_mode=ParseMode.MARKDOWN,
                allow_sending_without_reply=True,
            )
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
            )
            job_queue.run_once(
                partial(check_not_bot, new_mem, chat.id, message.message_id),
                120,
                name="welcomemute",
            )
        if welc_mutes == "captcha":
            btn = []
            CAPCTHA_SIZE_NUM = 2
            generator = CaptchaGenerator(CAPCTHA_SIZE_NUM)

            captcha = generator.gen_captcha_image(difficult_level=3)
            image = captcha["image"]
            characters = captcha["characters"]
            fileobj = BytesIO()
            fileobj.name = f'captcha_{new_mem.id}.png'
            image.save(fp=fileobj)
            fileobj.seek(0)
            CAPTCHA_ANS_DICT[(chat.id, new_mem.id)] = int(characters)
            welcome_bool = False
            if not media_wel:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "media_wel": False,
                            "status": False,
                            "update": update,
                            "res": res,
                            "keyboard": keyboard,
                            "backup_message": backup_message,
                            "captcha_correct": characters,
                        }
                    }
                )
            else:
                VERIFIED_USER_WAITLIST.update(
                    {
                        (chat.id, new_mem.id): {
                            "should_welc": should_welc,
                            "chat_id": chat.id,
                            "status": False,
                            "media_wel": True,
                            "cust_content": cust_content,
                            "welc_type": welc_type,
                            "res": res,
                            "keyboard": keyboard,
                            "captcha_correct": characters,
                        }
                    }
                )

            nums = [random.randint(1000, 9999) for _ in range(7)]
            nums.append(characters)
            random.shuffle(nums)
            to_append = []
            for a in nums:
                to_append.append(InlineKeyboardButton(text=str(a),
                                                      callback_data=f"user_captchajoin_({chat.id},{new_mem.id})_({a})"))
                if len(to_append) > 2:
                    btn.append(to_append)
                    to_append = []
            if to_append:
                btn.append(to_append)

            message = bot.send_photo(chat.id, fileobj,
                                      caption=f'🔐 هلا [{escape_markdown(new_mem.first_name)}](tg://user?id={user.id}). اضغط الزر الصحيح باش يتفك الكتم!\n'
                                              f'عندك 120 ثانية.',
                                      reply_markup=InlineKeyboardMarkup(btn),
                                      parse_mode=ParseMode.MARKDOWN,
                                      allow_sending_without_reply=True,
                                      )
            bot.restrict_chat_member(
                chat.id,
                new_mem.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_send_polls=False,
                    can_change_info=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
            )
            job_queue.run_once(
                partial(check_not_bot, new_mem, chat.id, message.message_id),
                120,
                name="welcomemute",
            )

    if welcome_bool:
        if media_wel:
            if ENUM_FUNC_MAP[welc_type] == dispatcher.bot.send_sticker:
                sent = ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    reply_markup=keyboard,
                )
            else:
                sent = ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    caption=res,
                    reply_markup=keyboard,
                    parse_mode="markdown",
                )
        else:
            sent = send(update, res, keyboard, backup_message)
        prev_welc = sql.get_clean_pref(chat.id)
        if prev_welc:
            try:
                bot.delete_message(chat.id, prev_welc)
            except BadRequest:
                pass

            if sent:
                sql.set_clean_welcome(chat.id, sent.message_id)

                def clean_welc(_):
                    try:
                        bot.delete_message(chat.id, sent.message_id)
                    except:
                        pass

                j.run_once(clean_welc, 300)

    if not log_setting.log_joins:
        return ""
    if welcome_log:
        return welcome_log

    return ""


def cleanServiceFilter(u: Update, _):
    if u.effective_message.left_chat_member or u.effective_message.new_chat_members:
        return handleCleanService(u)


def handleCleanService(update: Update):
    if sql.clean_service(update.effective_chat.id):
        try:
            dispatcher.bot.delete_message(update.effective_chat.id, update.message.message_id)
        except BadRequest:
            pass


dispatcher.add_handler(MessageHandler(Filters.chat_type.groups, cleanServiceFilter))


def check_not_bot(member: User, chat_id: int, message_id: int, context: CallbackContext):
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop((chat_id, member.id))
    member_status = member_dict.get("status")
    if not member_status:
        try:
            bot.unban_chat_member(chat_id, member.id)
        except BadRequest:
            pass

        try:
            bot.edit_message_text(
                "👢 *تم طرده*\nيقدر يرجع ويحاول مرة ثانية.",
                chat_id=chat_id,
                message_id=message_id,
            )
        except TelegramError:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            bot.send_message("👢 {} تم طرده لأنه ما تحقق من نفسه".format(mention_html(member.id,
                                                                                                     member.first_name)),
                             chat_id=chat_id, parse_mode=ParseMode.HTML)


def left_member(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)

    if user.id == bot.id:
        return

    if should_goodbye:
        left_mem = update.chat_member.new_chat_member.user
        if left_mem:

            if sw:
                sw_ban = sw.get_ban(left_mem.id)
                if sw_ban:
                    return

            if is_user_gbanned(left_mem.id):
                return

            if left_mem.id == bot.id:
                return

            # وداع خاص بالمالك
            if left_mem.id == OWNER_ID:
                bot.send_message(chat.id,
                    "😢 الله يسهلك يا صاحبي...",
                )
                return

            if left_mem.id == 1826542418:
                bot.send_message(chat.id,
                    "<i>ارتاح توا...</i>", parse_mode=ParseMode.HTML
                )
                return

            # وداع المطورين
            elif left_mem.id in DEV_USERS:
                bot.send_message(chat.id,
                    "👋 مع السلامة يا مطور!",
                )
                return

            if goodbye_type not in [sql.Types.TEXT, sql.Types.BUTTON_TEXT]:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = (
                    left_mem.first_name or "شخص بدون اسم"
            )
            if cust_goodbye:
                if cust_goodbye == sql.DEFAULT_GOODBYE:
                    cust_goodbye = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                        first=escape_markdown(first_name)
                    )
                if left_mem.last_name:
                    fullname = escape_markdown(f"{first_name} {left_mem.last_name}")
                else:
                    fullname = escape_markdown(first_name)
                count = chat.get_member_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(left_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                    first=first_name
                )
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(
                update,
                res,
                keyboard,
                random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(first=first_name),
            )

@kigcmd(command='welcome', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def welcome(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if not args or args[0].lower() == "noformat":
        noformat = bool(args and args[0].lower() == "noformat")
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            f"إعدادات الترحيب في هذا القروب: `{pref}`.\n"
            f"*رسالة الترحيب (بدون تعبئة {{}}) هي:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if welcome_type in [sql.Types.BUTTON_TEXT, sql.Types.TEXT]:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)
        else:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m)

            else:
                if welcome_type in [sql.Types.TEXT, sql.Types.BUTTON_TEXT]:
                    kwargs = {'disable_web_page_preview': True}
                else:
                    kwargs = {}
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id,
                    cust_content,
                    caption=welcome_m,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                    **kwargs,
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "✅ تمام! بنرحب بالأعضاء الجدد لما ينضمو."
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "❌ تمام، مش بنرحب بحد توا."
            )

        else:
            update.effective_message.reply_text(
                "أفهم 'on/yes' أو 'off/no' بس! 🤔"
            )

@kigcmd(command='goodbye', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def goodbye(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    if not args or args[0] == "noformat":
        noformat = bool(args and args[0].lower() == "noformat")
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            f"إعدادات الوداع في هذا القروب: `{pref}`.\n"
            f"*رسالة الوداع (بدون تعبئة {{}}) هي:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        elif noformat:
            ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

        else:
            ENUM_FUNC_MAP[goodbye_type](
                chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN
            )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text("✅ تمام!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("✅ تمام!")

        else:
            update.effective_message.reply_text(
                "أفهم 'on/yes' أو 'off/no' بس! 🤔"
            )

@kigcmd(command='setwelcome', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def set_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    user = update.effective_user
    msg = update.effective_message


    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("ما حددتش شن ترد بيه! 🤔")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    msg.reply_text("✅ تم تعيين رسالة ترحيب مخصصة بنجاح!")

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#تعيين_ترحيب\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"تم تعيين رسالة الترحيب."
    )

@kigcmd(command='resetwelcome', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def reset_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "✅ تم إعادة رسالة الترحيب للافتراضية!"
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#إعادة_ترحيب\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"تم إعادة رسالة الترحيب للافتراضية."
    )

@kigcmd(command='setgoodbye', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def set_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("ما حددتش شن ترد بيه! 🤔")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("✅ تم تعيين رسالة وداع مخصصة بنجاح!")
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#تعيين_وداع\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"تم تعيين رسالة الوداع."
    )

@kigcmd(command='resetgoodbye', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def reset_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "✅ تم إعادة رسالة الوداع للافتراضية!"
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#إعادة_وداع\n"
        f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
        f"تم إعادة رسالة الوداع للافتراضية."
    )

@kigcmd(command='welcomemute', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def welcomemute(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            msg.reply_text("✅ مش بنكتم الأعضاء الجدد توا!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#كتم_ترحيب\n"
                f"<b>• المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"غير كتم الترحيب لـ <b>مغلق</b>."
            )
        elif args[0].lower() in ["soft"]:
            sql.set_welcome_mutes(chat.id, "soft")
            msg.reply_text(
                "✅ بنمنع الأعضاء الجدد من إرسال الوسائط لمدة 24 ساعة."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#كتم_ترحيب\n"
                f"<b>• المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"غير كتم الترحيب لـ <b>ناعم</b>."
            )
        elif args[0].lower() in ["strong"]:
            sql.set_welcome_mutes(chat.id, "strong")
            msg.reply_text(
                "✅ بنكتم الأعضاء الجدد لين يثبتو إنهم مش بوتات.\nعندهم 120 ثانية قبل ما ينطردو."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#كتم_ترحيب\n"
                f"<b>• المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"غير كتم الترحيب لـ <b>قوي</b>."
            )
        elif args[0].lower() in ["captcha"]:
            sql.set_welcome_mutes(chat.id, "captcha")
            msg.reply_text(
                "✅ بنكتم الأعضاء الجدد لين يحلو الكابتشا.\nلازم يحلو الكابتشا باش يتفك الكتم."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#كتم_ترحيب\n"
                f"<b>• المشرف:</b> {mention_html(user.id, user.first_name)}\n"
                f"غير كتم الترحيب لـ <b>كابتشا</b>."
            )
        else:
            msg.reply_text(
                "الرجاء إدخال `off`/`no`/`soft`/`strong`/`captcha`!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = (
            f"\n أعطيني إعداد!\nاختار من: `off`/`no` أو `soft`, `strong` أو `captcha` بس! \n"
            f"الإعداد الحالي: `{curr_setting}`"
        )
        msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
        return ""

@kigcmd(command='cleanwelcome', filters=Filters.chat_type.groups)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
def clean_welcome(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    if not args:
        if clean_pref := sql.get_clean_pref(chat.id):
            update.effective_message.reply_text(
                "بنمسح رسائل الترحيب القديمة (لحد يومين)."
            )
        else:
            update.effective_message.reply_text(
                "مش بنمسح رسائل الترحيب القديمة حالياً!"
            )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text("✅ بنحاول نمسح رسائل الترحيب القديمة!")
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تنظيف_ترحيب\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"فعل تنظيف الترحيب."
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text("❌ مش بنمسح رسائل الترحيب القديمة.")
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#تنظيف_ترحيب\n"
            f"<b>المشرف:</b> {mention_html(user.id, user.first_name)}\n"
            f"عطل تنظيف الترحيب."
        )
    else:
        update.effective_message.reply_text("أفهم 'on/yes' أو 'off/no' بس! 🤔")
        return ""

@kigcmd(command='cleanservice', filters=Filters.chat_type.groups)
@spamcheck
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
def cleanservice(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    if chat.type == chat.PRIVATE:
        if sql.clean_service(chat.id):
            update.effective_message.reply_text(
                "خدمة تنظيف الترحيب: مفعلة ✅", parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.effective_message.reply_text(
                "خدمة تنظيف الترحيب: معطلة ❌", parse_mode=ParseMode.MARKDOWN
            )

    elif len(args) >= 1:
        var = args[0]
        if var in ("no", "off"):
            sql.set_clean_service(chat.id, False)
            update.effective_message.reply_text("خدمة تنظيف الترحيب: معطلة ❌")
        elif var in ("yes", "on"):
            sql.set_clean_service(chat.id, True)
            update.effective_message.reply_text("خدمة تنظيف الترحيب: مفعلة ✅")
        else:
            update.effective_message.reply_text(
                "خيار غلط! 🤔", parse_mode=ParseMode.MARKDOWN
            )
    else:
        update.effective_message.reply_text(
            "الاستخدام: on/yes أو off/no", parse_mode=ParseMode.MARKDOWN
        )

@kigcallback(pattern=r"user_join_", run_async=True)
def user_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    join_user = int(match.group(1))

    if join_user == user.id:
        sql.set_human_checks(user.id, chat.id)
        member_dict = VERIFIED_USER_WAITLIST[(chat.id, user.id)]
        member_dict["status"] = True
        query.answer(text="✅ يييه! انت إنسان، تم فك الكتم!")
        bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        try:
            bot.deleteMessage(chat.id, message.message_id)
        except:
            pass
        if member_dict["should_welc"]:
            if member_dict["media_wel"]:
                sent = ENUM_FUNC_MAP[member_dict["welc_type"]](
                    member_dict["chat_id"],
                    member_dict["cust_content"],
                    caption=member_dict["res"],
                    reply_markup=member_dict["keyboard"],
                    parse_mode="markdown",
                )
            else:
                sent = send(
                    member_dict["update"],
                    member_dict["res"],
                    member_dict["keyboard"],
                    member_dict["backup_message"],
                )

            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

                    def clean_welc(_):
                        try:
                            bot.delete_message(chat.id, sent.message_id)
                        except:
                            pass

                    j.run_once(clean_welc, 300)

    else:
        query.answer(text="❌ ما عندكش صلاحية تسوي هذا!")


@kigcallback(pattern=r"user_captchajoin_\([\d\-]+,\d+\)_\(\d{4}\)", run_async=True)
def user_captcha_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_captchajoin_\(([\d\-]+),(\d+)\)_\((\d{4})\)", query.data)
    message = update.effective_message
    join_chat = int(match.group(1))
    join_user = int(match.group(2))
    captcha_ans = int(match.group(3))
    join_usr_data = bot.getChat(join_user)

    if join_user == user.id:
        c_captcha_ans = CAPTCHA_ANS_DICT.pop((join_chat, join_user))
        if c_captcha_ans == captcha_ans:
            sql.set_human_checks(user.id, chat.id)
            member_dict = VERIFIED_USER_WAITLIST[(chat.id, user.id)]
            member_dict["status"] = True
            query.answer(text="✅ يييه! انت إنسان، تم فك الكتم!")
            bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_send_polls=True,
                    can_change_info=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            try:
                bot.deleteMessage(chat.id, message.message_id)
            except:
                pass
            if member_dict["should_welc"]:
                if member_dict["media_wel"]:
                    sent = ENUM_FUNC_MAP[member_dict["welc_type"]](
                        member_dict["chat_id"],
                        member_dict["cust_content"],
                        caption=member_dict["res"],
                        reply_markup=member_dict["keyboard"],
                        parse_mode="markdown",
                    )
                else:
                    sent = send(
                        member_dict["update"],
                        member_dict["res"],
                        member_dict["keyboard"],
                        member_dict["backup_message"],
                    )

                prev_welc = sql.get_clean_pref(chat.id)
                if prev_welc:
                    try:
                        bot.delete_message(chat.id, prev_welc)
                    except BadRequest:
                        pass

                    if sent:
                        sql.set_clean_welcome(chat.id, sent.message_id)

                        def clean_welc(_):
                            try:
                                bot.delete_message(chat.id, sent.message_id)
                            except:
                                pass
                        j.run_once(clean_welc, 300)
        else:
            try:
                bot.deleteMessage(chat.id, message.message_id)
            except:
                pass
            kicked_msg = f'''
            ❌ [{escape_markdown(join_usr_data.first_name)}](tg://user?id={join_user}) فشل في الكابتشا وتم طرده.
            '''
            query.answer(text="❌ إجابة غلط!")
            res = chat.unban_member(join_user)
            if res:
                bot.sendMessage(chat_id=chat.id, text=kicked_msg, parse_mode=ParseMode.MARKDOWN)


    else:
        query.answer(text="❌ ما عندكش صلاحية تسوي هذا!")


WELC_HELP_TXT = (
    "رسائل الترحيب/الوداع في القروب يمكن تخصيصها بعدة طرق. لو تبي الرسائل تتولد بشكل فردي، "
    "زي رسالة الترحيب الافتراضية، تقدر تستخدم *هذي* المتغيرات:\n"
    " • `{first}`*:* هذا يمثل *الاسم الأول* للمستخدم\n"
    " • `{last}`*:* هذا يمثل *اسم العائلة* للمستخدم. افتراضياً *الاسم الأول* لو ما عنده اسم عائلة.\n"
    " • `{fullname}`*:* هذا يمثل *الاسم الكامل* للمستخدم. افتراضياً *الاسم الأول* لو ما عنده اسم عائلة.\n"
    " • `{username}`*:* هذا يمثل *اليوزرنيم* للمستخدم. افتراضياً *منشن* للاسم الأول لو ما عنده يوزرنيم.\n"
    " • `{mention}`*:* هذا ببساطة *يمنشن* المستخدم - يتاقه باسمه الأول.\n"
    " • `{id}`*:* هذا يمثل *آيدي* المستخدم\n"
    " • `{count}`*:* هذا يمثل *رقم العضو*.\n"
    " • `{chatname}`*:* هذا يمثل *اسم القروب الحالي*.\n"
    "\nكل متغير لازم يكون محاط بـ `{}` باش يتم استبداله.\n"
    "رسائل الترحيب تدعم الماركداون، فتقدر تخلي أي عنصر bold/italic/code/links. "
    "الأزرار مدعومة برضو، فتقدر تخلي الترحيب يبان حلو بأزرار.\n"
    f"لإنشاء زر يوصل للقوانين، استخدم: `[القوانين](buttonurl://t.me/{dispatcher.bot.username}?start=group_id)`. "
    "استبدل `group_id` بآيدي القروب، اللي تقدر تجيبه بـ /id.\n"
    "تقدر حتى تحط صور/جيفات/فيديوهات/رسائل صوتية كرسالة ترحيب "
    "بالرد على الوسائط، واستخدام `/setwelcome`."
)

WELC_MUTE_HELP_TXT = (
    "تقدر تخلي البوت يكتم الأعضاء الجدد اللي ينضمو للقروب وبالتالي تمنع السبام بوتات من اختراق القروب. "
    "الخيارات المتاحة:\n"
    "• `/welcomemute soft`*:* يمنع الأعضاء الجدد من إرسال الوسائط لمدة 24 ساعة.\n"
    "• `/welcomemute strong`*:* يكتم الأعضاء الجدد لين يضغطو على زر يثبتو إنهم بشر.\n"
    "• `/welcomemute captcha`*:*  يكتم الأعضاء الجدد لين يحلو كابتشا يثبتو إنهم بشر.\n"
    "• `/welcomemute off`*:* يقفل كتم الترحيب.\n"
    "*ملاحظة:* الوضع القوي يطرد المستخدم من القروب لو ما تحقق في 120 ثانية. يقدرو يرجعو بعدين."
)

@kigcmd(command='welcomehelp')
@user_admin_check()
def welcome_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)

@kigcmd(command='welcomemutehelp')
@user_admin_check()
def welcome_mute_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        WELC_MUTE_HELP_TXT, parse_mode=ParseMode.MARKDOWN
    )


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    return (
        "إعدادات الترحيب في هذا القروب: `{}`.\n"
        "إعدادات الوداع: `{}`.".format(welcome_pref, goodbye_pref)
    )


from .language import gs


def wlc_m_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        gs(update.effective_chat.id, "welcome_mutes"),
        parse_mode=ParseMode.HTML,
    )


def wlc_fill_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        gs(update.effective_chat.id, "welcome_help"),
        parse_mode=ParseMode.HTML,
    )



@kigcallback(pattern=r"wlc_help_")
def fmt_help(update: Update, context: CallbackContext):
    query = update.callback_query
    bot = context.bot
    help_info = query.data.split("wlc_help_")[1]
    if help_info == "m":
        help_text = gs(update.effective_chat.id, "welcome_mutes")
    elif help_info == "h":
        help_text = gs(update.effective_chat.id, "welcome_help")
    query.message.edit_text(
        text=help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🔙 رجوع", callback_data=f"help_module({__mod_name__.lower()})"),
            InlineKeyboardButton(text='💬 الدعم', url='https://t.me/TheBotsSupport')]]
        ),
    )
    bot.answer_callback_query(query.id)



def get_help(chat):
    return [gs(chat, "greetings_help"),
    [
        InlineKeyboardButton(text="كتم الترحيب", callback_data="wlc_help_m"),
        InlineKeyboardButton(text="تنسيق الترحيب", callback_data="wlc_help_h")
    ]
]


__mod_name__ = "الترحيب 👋"
