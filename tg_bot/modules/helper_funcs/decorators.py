from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from tg_bot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from telegram.ext import CallbackQueryHandler, InlineQueryHandler
from telegram.ext.filters import BaseFilter, Filters
from tg_bot import dispatcher as d, log, telethn, OWNER_ID
from typing import Optional, Union, List
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler as CommandHandler, CustomMessageHandler as MessageHandler, SpamChecker
from telethon import events
import traceback, html, requests


# ═══════════════════════════════════════════════════════════
# قاموس الأوامر العربية 🇱🇾
# ═══════════════════════════════════════════════════════════

ARABIC_COMMANDS = {
    "start": ["ابدا", "بداية"],
    "help": ["مساعدة", "مساعده", "اوامر", "الاوامر"],
    "settings": ["اعدادات", "الاعدادات"],
    "stats": ["احصائيات", "الاحصائيات"],
    "admins": ["الادمنية", "المشرفين"],
    "adminlist": ["قائمة_المشرفين"],
    "staff": ["الطاقم"],
    "promote": ["ترقية", "رفع"],
    "fullpromote": ["ترقية_كاملة"],
    "demote": ["تنزيل", "تخفيض"],
    "pin": ["تثبيت", "ثبت"],
    "unpin": ["الغاء_التثبيت", "فك_التثبيت"],
    "unpinall": ["فك_الكل"],
    "pinned": ["المثبتة"],
    "permapin": ["تثبيت_دائم"],
    "invitelink": ["رابط_الدعوة", "رابط"],
    "title": ["لقب"],
    "setgtitle": ["اسم_القروب"],
    "setgdesc": ["وصف_القروب"],
    "setgpic": ["صورة_القروب"],
    "delgpic": ["حذف_صورة_القروب"],
    "setgsticker": ["ملصقات_القروب"],
    "setgstickers": ["ملصقات_القروب٢"],
    "admincache": ["تحديث_المشرفين"],
    "zombies": ["الحسابات_المحذوفة", "زومبي"],
    "requests": ["طلبات_الانضمام"],
    "ban": ["حظر", "بان"],
    "sban": ["حظر_صامت"],
    "dban": ["حظر_ومسح"],
    "dsban": ["حظر_صامت_ومسح"],
    "tban": ["حظر_مؤقت"],
    "unban": ["رفع_الحظر", "فك_الحظر"],
    "kick": ["طرد"],
    "skick": ["طرد_صامت"],
    "dkick": ["طرد_ومسح"],
    "dskick": ["طرد_صامت_ومسح"],
    "kickme": ["اطردني"],
    "mute": ["كتم", "اسكت"],
    "smute": ["كتم_صامت"],
    "dmute": ["كتم_ومسح"],
    "dsmute": ["كتم_صامت_ومسح"],
    "tmute": ["كتم_مؤقت"],
    "tempmute": ["كتم_مؤقت٢"],
    "unmute": ["رفع_الكتم", "فك_الكتم"],
    "warn": ["تحذير", "انذار"],
    "swarn": ["تحذير_صامت"],
    "dwarn": ["تحذير_ومسح"],
    "warns": ["التحذيرات", "الانذارات"],
    "resetwarn": ["مسح_تحذير"],
    "resetwarns": ["مسح_التحذيرات"],
    "resetallwarns": ["مسح_كل_التحذيرات"],
    "rmwarn": ["حذف_الانذارات"],
    "addwarn": ["اضف_تحذير"],
    "nowarn": ["بدون_تحذير"],
    "warnlimit": ["حد_التحذيرات"],
    "strongwarn": ["تحذير_قوي"],
    "warnlist": ["قائمة_التحذيرات"],
    "blacklist": ["القائمة_السوداء", "الاسود"],
    "blacklists": ["القوائم_السوداء"],
    "addblacklist": ["اضف_اسود"],
    "unblacklist": ["حذف_اسود"],
    "blacklistmode": ["وضع_الاسود"],
    "blocklist": ["قائمة_الحظر"],
    "blocklists": ["قوائم_الحظر"],
    "addblocklist": ["اضف_حظر"],
    "unblocklist": ["حذف_حظر"],
    "blocklistmode": ["وضع_الحظر"],
    "removeallblacklists": ["مسح_كل_الاسود"],
    "removeallblocklists": ["مسح_كل_الحظر"],
    "save": ["حفظ", "احفظ"],
    "get": ["جلب", "جيب"],
    "clear": ["مسح"],
    "notes": ["الملاحظات"],
    "saved": ["المحفوظات"],
    "privatenotes": ["ملاحظات_خاصة"],
    "removeallnotes": ["مسح_كل_الملاحظات"],
    "welcome": ["ترحيب"],
    "setwelcome": ["ضبط_ترحيب"],
    "resetwelcome": ["اعادة_ترحيب"],
    "goodbye": ["وداع"],
    "setgoodbye": ["ضبط_وداع"],
    "resetgoodbye": ["اعادة_وداع"],
    "cleanwelcome": ["تنظيف_ترحيب"],
    "welcomehelp": ["مساعدة_ترحيب"],
    "welcomemute": ["كتم_ترحيب"],
    "welcomemutetime": ["وقت_كتم_ترحيب"],
    "setmutetext": ["نص_كتم"],
    "resetmutetext": ["اعادة_نص_كتم"],
    "lock": ["قفل"],
    "unlock": ["فتح"],
    "locks": ["الاقفال"],
    "locktypes": ["انواع_القفل"],
    "antichannel": ["ضد_القنوات"],
    "lockdown": ["اغلاق"],
    "unlockdown": ["فتح_الاغلاق"],
    "purge": ["تطهير", "مسح_رسائل"],
    "spurge": ["تطهير_صامت"],
    "purgeto": ["تطهير_الى"],
    "del": ["حذف"],
    "filter": ["فلتر"],
    "filters": ["الفلاتر"],
    "stop": ["ايقاف", "وقف"],
    "removeallfilters": ["مسح_كل_الفلاتر"],
    "stopall": ["ايقاف_الكل"],
    "rules": ["القوانين", "القواعد"],
    "setrules": ["ضبط_القوانين"],
    "clearrules": ["مسح_القوانين"],
    "flood": ["الفلود"],
    "setflood": ["ضبط_الفلود"],
    "setfloodmode": ["وضع_الفلود"],
    "antiflood": ["ضد_الفلود"],
    "antispam": ["ضد_السبام"],
    "gbanstat": ["حالة_الحظر_العام"],
    "sibylban": ["حظر_سيبيل"],
    "info": ["معلومات"],
    "u": ["م"],
    "id": ["الايدي", "ايدي"],
    "gifid": ["ايدي_الصورة"],
    "setbio": ["ضبط_البايو"],
    "bio": ["البايو"],
    "setme": ["ضبط_معلوماتي"],
    "me": ["انا"],
    "afk": ["مشغول", "بعيد"],
    "approve": ["موافقة", "وافق"],
    "unapprove": ["رفض_الموافقة"],
    "approved": ["الموافق_عليهم"],
    "approval": ["حالة_الموافقة"],
    "unapproveall": ["رفض_الكل"],
    "connect": ["اتصال", "ربط"],
    "connection": ["الاتصال"],
    "disconnect": ["قطع_الاتصال", "فصل"],
    "allowconnect": ["سماح_الاتصال"],
    "helpconnect": ["مساعدة_الاتصال"],
    "tl": ["ترجم"],
    "tr": ["ترجمة"],
    "langs": ["اللغات"],
    "wiki": ["ويكي"],
    "ud": ["قاموس"],
    "wall": ["خلفيات"],
    "paste": ["لصق"],
    "gdpr": ["حذف_بياناتي"],
    "markdownhelp": ["مساعدة_التنسيق"],
    "removebotkeyboard": ["ازالة_الكيبورد"],
    "imdb": ["افلام"],
    "weather": ["الطقس"],
    "stickerid": ["ايدي_الملصق"],
    "getsticker": ["جيب_الملصق"],
    "kang": ["سرقة", "اسرق"],
    "song": ["اغنية"],
    "video": ["فيديو"],
    "lyrics": ["كلمات"],
    "yt": ["يوتيوب"],
    "youtube": ["يوتيوب٢"],
    "ytdl": ["تحميل_يوتيوب"],
    "magisk": ["ماجسك"],
    "device": ["جهاز"],
    "twrp": ["ريكفري"],
    "github": ["قيت"],
    "repo": ["مستودع"],
    "anime": ["انمي"],
    "character": ["شخصية"],
    "manga": ["مانقا"],
    "cleanbluetext": ["تنظيف_الازرق"],
    "ignorecleanbluetext": ["تجاهل_الازرق"],
    "unignorecleanbluetext": ["الغاء_تجاهل_الازرق"],
    "listcleanbluetext": ["قائمة_الازرق"],
    "clearcmd": ["مسح_الاوامر"],
    "cmds": ["حالة_الاوامر"],
    "enable": ["تفعيل"],
    "disable": ["تعطيل"],
    "listcmds": ["قائمة_الاوامر"],
    "report": ["بلاغ", "تبليغ"],
    "reports": ["البلاغات"],
    "logchannel": ["سجل_القناة"],
    "setlog": ["ضبط_السجل"],
    "unsetlog": ["حذف_السجل"],
    "logsettings": ["اعدادات_السجل"],
    "import": ["استيراد"],
    "export": ["تصدير"],
    "announce": ["اعلان"],
    "setanon": ["مجهول"],
    "unsetanon": ["الغاء_مجهول"],
    "ignore": ["تجاهل"],
    "notice": ["الغاء_التجاهل"],
    "ignoredlist": ["قائمة_المتجاهلين"],
    "whois": ["مين_هذا"],
    "pfp": ["الصورة"],
    "echo": ["ردد"],
    "ping": ["بنج"],
    "uptime": ["مدة_التشغيل"],
    "print": ["طباعة"],
    "resetantispam": ["اعادة_السبام"],
    "reverse": ["بحث_صورة"],
    "tts": ["صوت"],
    "newfed": ["اتحاد_جديد"],
    "renamefed": ["تغيير_اسم_الاتحاد"],
    "delfed": ["حذف_الاتحاد"],
    "fpromote": ["ترقية_اتحاد"],
    "fdemote": ["تنزيل_اتحاد"],
    "subfed": ["اشتراك_اتحاد"],
    "unsubfed": ["الغاء_اشتراك_اتحاد"],
    "setfedlog": ["سجل_الاتحاد"],
    "unsetfedlog": ["حذف_سجل_الاتحاد"],
    "fbroadcast": ["بث_الاتحاد"],
    "fedsubs": ["اشتراكات_الاتحاد"],
    "fban": ["حظر_اتحاد"],
    "unfban": ["رفع_حظر_اتحاد"],
    "fedinfo": ["معلومات_الاتحاد"],
    "joinfed": ["انضمام_اتحاد"],
    "leavefed": ["مغادرة_اتحاد"],
    "setfrules": ["قواعد_الاتحاد"],
    "fedadmins": ["مشرفين_الاتحاد"],
    "fbanlist": ["محظورين_الاتحاد"],
    "fedchats": ["شاتات_الاتحاد"],
    "chatfed": ["اتحاد_الشات"],
    "fbanstat": ["حالة_حظر_الاتحاد"],
    "fednotif": ["اشعارات_الاتحاد"],
    "frules": ["قوانين_الاتحاد"],
    "currency": ["عملة"],
    "debug": ["تصحيح"],
    "eval": ["تنفيذ"],
    "e": ["تنفيذ٢"],
    "ev": ["تنفيذ٣"],
    "eva": ["تنفيذ٤"],
    "sh": ["شل"],
    "lang": ["اللغة"],
    "setlang": ["ضبط_اللغة"],
}


# ═══════════════════════════════════════════════════════════
# دالة تحويل الأوامر - تدعم str, list, tuple
# ═══════════════════════════════════════════════════════════

def get_arabic_aliases(command):
    """يرجع قائمة الأوامر العربية المقابلة للأمر الإنجليزي"""

    if isinstance(command, tuple):
        command = list(command)

    if isinstance(command, str):
        command = [command]

    if isinstance(command, list):
        result = list(command)
        for cmd in command:
            if isinstance(cmd, str) and cmd in ARABIC_COMMANDS:
                result.extend(ARABIC_COMMANDS[cmd])
        return result

    return [str(command)]


# ═══════════════════════════════════════════════════════════
# الكلاس الرئيسي - KigyoTelegramHandler
# ═══════════════════════════════════════════════════════════

class KigyoTelegramHandler:
    def __init__(self, d):
        self._dispatcher = d

    def command(
            self, command, filters: Optional[BaseFilter] = None, admin_ok: bool = False, pass_args: bool = False,
            pass_chat_data: bool = False, run_async: bool = True, can_disable: bool = True,
            group: Optional[int] = 40
    ):
        if filters:
            filters = filters & ~Filters.update.edited_message
        else:
            filters = ~Filters.update.edited_message

        def _command(func):
            try:
                enhanced_command = get_arabic_aliases(command)
            except Exception as e:
                log.warning(f"[عربي] خطأ في تحسين الأمر {command}: {e}")
                if isinstance(command, (list, tuple)):
                    enhanced_command = list(command)
                elif isinstance(command, str):
                    enhanced_command = [command]
                else:
                    enhanced_command = [str(command)]

            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleCommandHandler(enhanced_command, func, filters=filters, run_async=run_async,
                                                  pass_args=pass_args, admin_ok=admin_ok), group
                    )
                else:
                    self._dispatcher.add_handler(
                        CommandHandler(enhanced_command, func, filters=filters, run_async=run_async,
                                       pass_args=pass_args), group
                    )
                log.debug(
                    f"[KIGCMD] تم تحميل {enhanced_command} للدالة {func.__name__} في المجموعة {group}")
            except TypeError:
                try:
                    if can_disable:
                        self._dispatcher.add_handler(
                            DisableAbleCommandHandler(enhanced_command, func, filters=filters, run_async=run_async,
                                                      pass_args=pass_args, admin_ok=admin_ok,
                                                      pass_chat_data=pass_chat_data)
                        )
                    else:
                        self._dispatcher.add_handler(
                            CommandHandler(enhanced_command, func, filters=filters, run_async=run_async,
                                           pass_args=pass_args, pass_chat_data=pass_chat_data)
                        )
                    log.debug(f"[KIGCMD] تم تحميل {enhanced_command} للدالة {func.__name__}")
                except Exception as e:
                    log.error(f"[KIGCMD] فشل تحميل {command}: {e}")
                    try:
                        if isinstance(command, tuple):
                            orig = list(command)
                        elif isinstance(command, str):
                            orig = [command]
                        else:
                            orig = list(command)

                        if can_disable:
                            self._dispatcher.add_handler(
                                DisableAbleCommandHandler(orig, func, filters=filters, run_async=run_async,
                                                          pass_args=pass_args, admin_ok=admin_ok), group
                            )
                        else:
                            self._dispatcher.add_handler(
                                CommandHandler(orig, func, filters=filters, run_async=run_async,
                                               pass_args=pass_args), group
                            )
                        log.debug(f"[KIGCMD] تم تحميل {orig} (احتياطي) للدالة {func.__name__}")
                    except:
                        log.error(f"[KIGCMD] فشل كامل في تحميل الدالة {func.__name__}")

            return func

        return _command

    def message(self, pattern: Optional[BaseFilter] = None, can_disable: bool = True, run_async: bool = True,
                group: Optional[int] = 60, friendly=None):
        if pattern:
            pattern = pattern & ~Filters.update.edited_message
        else:
            pattern = ~Filters.update.edited_message

        def _message(func):
            try:
                if can_disable:
                    self._dispatcher.add_handler(
                        DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async), group
                    )
                else:
                    self._dispatcher.add_handler(
                        MessageHandler(pattern, func, run_async=run_async), group
                    )
                log.debug(
                    f"[KIGMSG] تم تحميل الفلتر {pattern} للدالة {func.__name__} في المجموعة {group}")
            except TypeError:
                try:
                    if can_disable:
                        self._dispatcher.add_handler(
                            DisableAbleMessageHandler(pattern, func, friendly=friendly, run_async=run_async)
                        )
                    else:
                        self._dispatcher.add_handler(
                            MessageHandler(pattern, func, run_async=run_async)
                        )
                    log.debug(f"[KIGMSG] تم تحميل الفلتر {pattern} للدالة {func.__name__}")
                except Exception as e:
                    log.error(f"[KIGMSG] فشل تحميل message handler: {e}")

            return func

        return _message

    def callbackquery(self, pattern: str = None, run_async: bool = True):
        def _callbackquery(func):
            self._dispatcher.add_handler(
                CallbackQueryHandler(pattern=pattern, callback=func, run_async=run_async))
            log.debug(
                f'[KIGCALLBACK] تم تحميل callback بالنمط {pattern} للدالة {func.__name__}')
            return func

        return _callbackquery

    def inlinequery(self, pattern: Optional[str] = None, run_async: bool = True, pass_user_data: bool = True,
                    pass_chat_data: bool = True, chat_types: List[str] = None):
        def _inlinequery(func):
            self._dispatcher.add_handler(
                InlineQueryHandler(pattern=pattern, callback=func, run_async=run_async,
                                   pass_user_data=pass_user_data,
                                   pass_chat_data=pass_chat_data, chat_types=chat_types))
            log.debug(
                f'[KIGINLINE] تم تحميل inline بالنمط {pattern} للدالة {func.__name__}')
            return func

        return _inlinequery


kigcmd = KigyoTelegramHandler(d).command
kigmsg = KigyoTelegramHandler(d).message
kigcallback = KigyoTelegramHandler(d).callbackquery
kiginline = KigyoTelegramHandler(d).inlinequery


# ═══════════════════════════════════════════════════════════
# دالة register لـ Telethon
# ═══════════════════════════════════════════════════════════

def register(**args):
    pattern = args.get('pattern', None)
    disable_edited = args.get('disable_edited', False)
    groups_only = args.get('groups_only', False)
    no_args = args.get('no_args', False)
    raw = args.get('raw', False)

    if pattern is not None:
        if raw:
            reg = "(?i)[/!>]"
            args['pattern'] = reg + pattern
        else:
            reg = "(?i)[/!>]"
            reg += pattern
            if no_args:
                reg += "($|@OdinRobot$)"
            else:
                reg += "( |@OdinRobot )?(.*)"
            args['pattern'] = reg

    if "disable_edited" in args:
        del args['disable_edited']

    if "no_args" in args:
        del args['no_args']

    if "raw" in args:
        del args['raw']

    if "groups_only" in args:
        del args['groups_only']

    def decorator(func):
        async def wrapper(check):
            if check.edit_date and check.is_channel and not check.is_group:
                return
            user_id = check.sender_id
            if SpamChecker.check_user(user_id):
                return
            if groups_only and not check.is_group:
                await check.respond("⚠️ هذا الأمر يشتغل في القروبات فقط!")
                return
            try:
                await func(check)
            except events.StopPropagation:
                raise events.StopPropagation
            except KeyboardInterrupt:
                pass
            except BaseException:
                try:
                    e = html.escape(f"{check.text}")

                    tb_list = traceback.format_exception(
                        None, check.error, check.error.__traceback__
                    )
                    tb = "".join(tb_list)
                    pretty_message = (
                        "حصل خطأ وقت معالجة التحديث\n"
                        "المستخدم: {}\n"
                        "المحادثة: {} {}\n"
                        "بيانات الكولباك: {}\n"
                        "الرسالة: {}\n\n"
                        "التفاصيل الكاملة: {}"
                    ).format(
                        check.from_id or "ما فيش",
                        getattr(check.chat, 'title', '') or "",
                        check.chat_id or "",
                        getattr(check, 'callback_query', None) or "ما فيش",
                        getattr(check.text, 'text', check.text) or "ما فيش رسالة",
                        tb,
                    )

                    key = requests.post(
                        "https://nekobin.com/api/documents", json={"content": pretty_message}
                    ).json()
                    if not key.get("result", {}).get("key"):
                        with open("error.txt", "w+") as f:
                            f.write(pretty_message)
                        await check.client.send_file(
                            OWNER_ID,
                            open("error.txt", "rb"),
                            caption=f"<b>❌ حصل خطأ:</b>\n<code>{e}</code>",
                            parse_mode="html",
                        )
                        return
                    key = key.get("result").get("key")
                    url = f"https://nekobin.com/{key}.py"
                    await check.client.send_message(
                        OWNER_ID,
                        f"<b>❌ حصل خطأ:</b>\n<code>{e}</code>\n\n<a href='{url}'>📋 التفاصيل</a>",
                        parse_mode="html",
                    )
                except Exception:
                    log.error("خطأ في معالج الأخطاء", exc_info=True)

        if not disable_edited:
            telethn.add_event_handler(wrapper, events.MessageEdited(**args))
        telethn.add_event_handler(wrapper, events.NewMessage(**args))
        log.debug(f"[TLTHNCMD] تم تحميل {pattern} للدالة {func.__name__}")

        return wrapper

    return decorator
