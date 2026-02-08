from tg_bot import spamcheck
from gpytranslate import SyncTranslator
from .language import gs

from telegram import ParseMode, Update
from telegram.ext import CallbackContext, Filters
from .helper_funcs.decorators import kigcmd, kigmsg


def get_help(chat):
    return gs(chat, "gtranslate_help")


__mod_name__ = "المترجم"

trans = SyncTranslator()

# ==================== الأوامر العربية ====================
ARABIC_TRANSLATE_COMMANDS = ["ترجم", "ترجمة", "translate"]
ARABIC_LANGS_COMMANDS = ["اللغات", "لغات", "قائمة_اللغات"]


@kigcmd(command=["tr", "tl"])
@spamcheck
def translate(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    reply_msg = message.reply_to_message
    to_translate = ""
    if not reply_msg:
        message.reply_text("⚠️ رد على رسالة باش أترجمها!")
        return
    if reply_msg.caption:
        to_translate = reply_msg.caption
    elif reply_msg.text:
        to_translate = reply_msg.text
    if not to_translate:
        message.reply_text("⚠️ رد على رسالة فيها نص باش أترجمها!")
        return
    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source = args.split("//")[0]
            dest = args.split("//")[1]
        else:
            source = trans.detect(to_translate)
            dest = args
    except IndexError:
        source = trans.detect(to_translate)
        dest = "ar"  # الافتراضي للعربي
    
    try:
        translation = trans(to_translate, sourcelang=source, targetlang=dest)
        reply = (
            f"🌐 <b>الترجمة من {source} إلى {dest}</b>:\n"
            f"<code>{translation.text}</code>"
        )
        bot.send_message(text=reply, chat_id=message.chat.id, parse_mode=ParseMode.HTML)
    except Exception as e:
        message.reply_text(f"⚠️ حصل خطأ في الترجمة!\n{str(e)}")


# ==================== معالج عربي للترجمة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_TRANSLATE_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_translate(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    reply_msg = message.reply_to_message
    
    if not reply_msg:
        message.reply_text(
            "⚠️ رد على رسالة باش أترجمها!\n\n"
            "📝 الاستخدام:\n"
            "• `ترجم` - ترجمة للعربي\n"
            "• `ترجم en` - ترجمة للإنجليزي\n"
            "• `ترجم ar//en` - من العربي للإنجليزي",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    to_translate = ""
    if reply_msg.caption:
        to_translate = reply_msg.caption
    elif reply_msg.text:
        to_translate = reply_msg.text
    
    if not to_translate:
        message.reply_text("⚠️ رد على رسالة فيها نص باش أترجمها!")
        return
    
    # استخراج اللغة من النص
    text = message.text
    for cmd in ARABIC_TRANSLATE_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    try:
        if "//" in text:
            source = text.split("//")[0]
            dest = text.split("//")[1]
        elif text:
            source = trans.detect(to_translate)
            dest = text
        else:
            source = trans.detect(to_translate)
            dest = "ar"  # الافتراضي للعربي
        
        translation = trans(to_translate, sourcelang=source, targetlang=dest)
        
        # تحويل رموز اللغات للعربي
        lang_names = {
            "ar": "العربية",
            "en": "الإنجليزية",
            "fr": "الفرنسية",
            "es": "الإسبانية",
            "de": "الألمانية",
            "it": "الإيطالية",
            "tr": "التركية",
            "ru": "الروسية",
            "zh": "الصينية",
            "ja": "اليابانية",
            "ko": "الكورية",
        }
        
        source_name = lang_names.get(source, source)
        dest_name = lang_names.get(dest, dest)
        
        reply = (
            f"🌐 <b>الترجمة من {source_name} إلى {dest_name}</b>:\n"
            f"<code>{translation.text}</code>"
        )
        bot.send_message(text=reply, chat_id=message.chat.id, parse_mode=ParseMode.HTML)
    except Exception as e:
        message.reply_text(f"⚠️ حصل خطأ في الترجمة!\n{str(e)}")


@kigcmd(command='langs')
@spamcheck
def languages(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    bot = context.bot
    bot.send_message(
        text="📚 اضغط [هنا](https://cloud.google.com/translate/docs/languages) لعرض قائمة رموز اللغات المدعومة!",
        chat_id=message.chat.id, 
        disable_web_page_preview=True, 
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== معالج عربي لقائمة اللغات ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_LANGS_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_languages(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    
    langs_text = (
        "📚 <b>أشهر رموز اللغات:</b>\n\n"
        "🌍 <b>اللغات الشائعة:</b>\n"
        "• <code>ar</code> - العربية\n"
        "• <code>en</code> - الإنجليزية\n"
        "• <code>fr</code> - الفرنسية\n"
        "• <code>es</code> - الإسبانية\n"
        "• <code>de</code> - الألمانية\n"
        "• <code>it</code> - الإيطالية\n"
        "• <code>tr</code> - التركية\n"
        "• <code>ru</code> - الروسية\n\n"
        "🌏 <b>لغات آسيوية:</b>\n"
        "• <code>zh</code> - الصينية\n"
        "• <code>ja</code> - اليابانية\n"
        "• <code>ko</code> - الكورية\n"
        "• <code>hi</code> - الهندية\n"
        "• <code>ur</code> - الأوردو\n"
        "• <code>id</code> - الإندونيسية\n\n"
        "🇪🇺 <b>لغات أوروبية:</b>\n"
        "• <code>pt</code> - البرتغالية\n"
        "• <code>nl</code> - الهولندية\n"
        "• <code>pl</code> - البولندية\n"
        "• <code>sv</code> - السويدية\n"
        "• <code>no</code> - النرويجية\n\n"
        "📖 للقائمة الكاملة: [اضغط هنا](https://cloud.google.com/translate/docs/languages)"
    )
    
    message.reply_text(
        langs_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ==================== أمثلة الاستخدام ====================
@kigmsg(Filters.regex(r'^(امثلة_الترجمة|كيفية_الترجمة)$'), group=3)
@spamcheck
def translation_examples(update: Update, context: CallbackContext):
    examples = (
        "📝 <b>أمثلة على استخدام المترجم:</b>\n\n"
        "1️⃣ <b>ترجمة تلقائية للعربي:</b>\n"
        "   <code>ترجم</code> (رد على رسالة)\n\n"
        "2️⃣ <b>ترجمة لأي لغة:</b>\n"
        "   <code>ترجم en</code> (للإنجليزي)\n"
        "   <code>ترجم fr</code> (للفرنسي)\n\n"
        "3️⃣ <b>تحديد اللغة المصدر:</b>\n"
        "   <code>ترجم ar//en</code> (من العربي للإنجليزي)\n"
        "   <code>ترجم en//ar</code> (من الإنجليزي للعربي)\n\n"
        "4️⃣ <b>بالإنجليزي:</b>\n"
        "   <code>/tr en</code>\n"
        "   <code>/tl fr</code>\n\n"
        "💡 <b>نصيحة:</b> رد على أي رسالة واكتب الأمر!"
    )
    
    update.effective_message.reply_text(examples, parse_mode=ParseMode.HTML)
