# from AstrakoBot
import wikipedia, os, glob
from tg_bot import dispatcher, spamcheck
from .helper_funcs.misc import delete
from .sql.clear_cmd_sql import get_clearcmd
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async, Filters
from wikipedia.exceptions import DisambiguationError, PageError
from .helper_funcs.decorators import kigcmd, kigmsg

# ==================== الأوامر العربية ====================
ARABIC_WIKI_COMMANDS = ["ويكي", "ويكيبيديا", "بحث", "wiki"]


@kigcmd(command='wiki', can_disable=True)
@spamcheck
def wiki(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = (
        update.effective_message.reply_to_message
        if update.effective_message.reply_to_message
        else update.effective_message
    )
    if not msg:
        update.message.reply_text("⚠️ أعطني شي أبحث عنه!")
        return
    res = ""
    if msg == update.effective_message:
        try:
            search = msg.text.split(" ", maxsplit=1)[1]
        except IndexError:
            update.message.reply_text("⚠️ أعطني شي أبحث عنه!")
            return
    else:
        search = msg.text
    
    # تحديد اللغة - إذا كان النص عربي استخدم ويكيبيديا العربية
    if any(ord(char) > 127 and ord(char) < 1632 or ord(char) > 1641 for char in search if char.isalpha()):
        wikipedia.set_lang("ar")
    else:
        wikipedia.set_lang("en")
    
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        delmsg = update.message.reply_text(
            "⚠️ في أكثر من نتيجة! حدد بحثك أكثر.\n<i>{}</i>".format(e),
            parse_mode=ParseMode.HTML,
        )
        cleartime = get_clearcmd(chat.id, "wiki")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)
        return
    except PageError as e:
        delmsg = update.message.reply_text(
            "⚠️ ما لقيت نتائج!\n<code>{}</code>".format(e), 
            parse_mode=ParseMode.HTML
        )
        cleartime = get_clearcmd(chat.id, "wiki")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)
        return
    
    if res:
        lang_code = "ar" if wikipedia.lang == "ar" else "en"
        result = f"📚 <b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n\n"
        result += f"""<a href="https://{lang_code}.wikipedia.org/wiki/{search.replace(" ", "%20")}">📖 اقرأ المزيد...</a>"""
        
        if len(result) > 4000:
            with open("result.txt", "w", encoding="utf-8") as f:
                f.write(f"{result}\n\n")
            with open("result.txt", "rb") as f:
                delmsg = context.bot.send_document(
                    document=f,
                    filename=f.name,
                    caption="📄 النتيجة طويلة، تلقاها في الملف!",
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML,
                )
                try:
                    for f in glob.glob("result.txt"):
                        os.remove(f)
                except Exception:
                    pass
        else:
            delmsg = update.message.reply_text(
                result, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    cleartime = get_clearcmd(chat.id, "wiki")
    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


# ==================== معالج عربي لويكيبيديا ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_WIKI_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_wiki(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_WIKI_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text:
        message.reply_text(
            "⚠️ أعطني شي أبحث عنه في ويكيبيديا!\n\n"
            "📝 أمثلة:\n"
            "• `ويكي ليبيا`\n"
            "• `بحث طرابلس`\n"
            "• `ويكيبيديا Python`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    search = text
    
    # تحديد اللغة تلقائياً
    # إذا كان فيه حروف عربية، استخدم ويكيبيديا العربية
    has_arabic = any('\u0600' <= char <= '\u06FF' for char in search)
    
    if has_arabic:
        wikipedia.set_lang("ar")
        lang_name = "العربية"
    else:
        wikipedia.set_lang("en")
        lang_name = "الإنجليزية"
    
    try:
        res = wikipedia.summary(search, sentences=5)
    except DisambiguationError as e:
        options = str(e).split('\n')[:10]  # أول 10 خيارات
        delmsg = message.reply_text(
            f"⚠️ في أكثر من نتيجة! حدد بحثك أكثر:\n\n"
            f"<i>{chr(10).join(options)}</i>",
            parse_mode=ParseMode.HTML,
        )
        cleartime = get_clearcmd(chat.id, "wiki")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)
        return
    except PageError:
        delmsg = message.reply_text(
            f"⚠️ ما لقيت نتائج عن: <b>{search}</b>\n\n"
            f"💡 حاول تبحث بطريقة ثانية!",
            parse_mode=ParseMode.HTML
        )
        cleartime = get_clearcmd(chat.id, "wiki")
        if cleartime:
            context.dispatcher.run_async(delete, delmsg, cleartime.time)
        return
    
    if res:
        lang_code = "ar" if has_arabic else "en"
        result = f"📚 <b>{search}</b>\n"
        result += f"🌐 <i>ويكيبيديا {lang_name}</i>\n\n"
        result += f"{res}\n\n"
        result += f"""<a href="https://{lang_code}.wikipedia.org/wiki/{search.replace(" ", "_")}">📖 اقرأ المقالة الكاملة</a>"""
        
        if len(result) > 4000:
            with open("wiki_result.txt", "w", encoding="utf-8") as f:
                f.write(f"📚 {search}\n\n{res}\n\n")
                f.write(f"الرابط: https://{lang_code}.wikipedia.org/wiki/{search.replace(' ', '_')}")
            
            with open("wiki_result.txt", "rb") as f:
                delmsg = context.bot.send_document(
                    document=f,
                    filename=f"wiki_{search[:20]}.txt",
                    caption=f"📄 نتيجة البحث عن: <b>{search}</b>\nالنتيجة طويلة، تلقاها في الملف!",
                    reply_to_message_id=message.message_id,
                    chat_id=chat.id,
                    parse_mode=ParseMode.HTML,
                )
            
            try:
                os.remove("wiki_result.txt")
            except:
                pass
        else:
            delmsg = message.reply_text(
                result, 
                parse_mode=ParseMode.HTML, 
                disable_web_page_preview=True
            )

    cleartime = get_clearcmd(chat.id, "wiki")
    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


# ==================== بحث في ويكيبيديا العربية فقط ====================
@kigmsg(Filters.regex(r'^(ويكي_عربي|ويكيبيديا_عربية)(\s|$)'), group=3)
@spamcheck
def arabic_wiki_ar(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    
    text = message.text
    if text.startswith("ويكي_عربي"):
        search = text[len("ويكي_عربي"):].strip()
    else:
        search = text[len("ويكيبيديا_عربية"):].strip()
    
    if not search:
        message.reply_text(
            "⚠️ أعطني شي أبحث عنه في ويكيبيديا العربية!\n\n"
            "📝 مثال: `ويكي_عربي ليبيا`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    wikipedia.set_lang("ar")
    
    try:
        res = wikipedia.summary(search, sentences=5)
        result = f"📚 <b>{search}</b>\n"
        result += f"🌐 <i>ويكيبيديا العربية</i>\n\n"
        result += f"{res}\n\n"
        result += f"""<a href="https://ar.wikipedia.org/wiki/{search.replace(" ", "_")}">📖 اقرأ المقالة الكاملة</a>"""
        
        message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except (DisambiguationError, PageError) as e:
        message.reply_text(f"⚠️ ما لقيت نتائج!\n{str(e)[:200]}")


# ==================== بحث في ويكيبيديا الإنجليزية فقط ====================
@kigmsg(Filters.regex(r'^(ويكي_انجليزي|ويكيبيديا_انجليزية)(\s|$)'), group=3)
@spamcheck
def arabic_wiki_en(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    
    text = message.text
    if text.startswith("ويكي_انجليزي"):
        search = text[len("ويكي_انجليزي"):].strip()
    else:
        search = text[len("ويكيبيديا_انجليزية"):].strip()
    
    if not search:
        message.reply_text(
            "⚠️ أعطني شي أبحث عنه في ويكيبيديا الإنجليزية!\n\n"
            "📝 مثال: `ويكي_انجليزي Python`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    wikipedia.set_lang("en")
    
    try:
        res = wikipedia.summary(search, sentences=5)
        result = f"📚 <b>{search}</b>\n"
        result += f"🌐 <i>Wikipedia English</i>\n\n"
        result += f"{res}\n\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "_")}">📖 Read full article</a>"""
        
        message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except (DisambiguationError, PageError) as e:
        message.reply_text(f"⚠️ No results found!\n{str(e)[:200]}")


from .language import gs

def get_help(chat):
    return gs(chat, "wiki_help")

__mod_name__ = "ويكيبيديا"
