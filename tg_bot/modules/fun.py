import html
import json
import random
from tg_bot import spamcheck
import time
import urllib.request
import urllib.parse

import telegram
from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, Filters

import tg_bot.modules.fun_strings as fun_strings
from .helper_funcs.admin_status import user_is_admin

from .helper_funcs.extraction import extract_user
from .helper_funcs.decorators import kigcmd, kigmsg

# ==================== الأوامر العربية ====================
ARABIC_SLAP_COMMANDS = ["صفعة", "اصفع", "صفع"]
ARABIC_ROLL_COMMANDS = ["نرد", "زهر", "رمي_النرد"]
ARABIC_TOSS_COMMANDS = ["عملة", "رمي_عملة", "قرعة"]
ARABIC_DECIDE_COMMANDS = ["قرر", "قرار", "اختر"]
ARABIC_RUNS_COMMANDS = ["اهرب", "هروب", "جري"]
ARABIC_TABLE_COMMANDS = ["طاولة", "اقلب_الطاولة"]
ARABIC_SHRUG_COMMANDS = ["مدري", "ما_ادري"]
ARABIC_RLG_COMMANDS = ["وجه_عشوائي", "وجه"]
ARABIC_PAT_COMMANDS = ["ربت", "تربيت"]

# ==================== ردود عربية ====================
ARABIC_DECIDE = [
    "✅ نعم!",
    "❌ لا!",
    "🤔 يمكن...",
    "😄 أكيد!",
    "😅 مش متأكد...",
    "👍 بالتأكيد!",
    "👎 أبداً!",
    "🎯 100%!",
    "😐 حاول مرة ثانية...",
    "🤷 ما عندي فكرة!",
    "💯 إي والله!",
    "🚫 لا لا لا!",
    "😏 شو رأيك أنت؟",
    "🌟 طبعاً!",
    "💭 فكر فيها شوية...",
    "😂 هههه لا!",
    "👀 شوف أنت...",
    "🤝 موافق!",
    "⛔ رفض!",
    "🎲 جرب حظك مرة ثانية!",
]

ARABIC_TOSS = [
    "🪙 صورة! (Heads)",
    "🪙 كتابة! (Tails)",
]

ARABIC_SLAP_TEMPLATES = [
    "{user1} صفع {user2} بـ {item} 👋",
    "{user1} {hits} {user2} بـ {item} 💥",
    "{user1} {throws} {item} على {user2} 🎯",
    "{user1} أخذ {item} و {hits} {user2} فيه 😤",
    "{user1} ما رحم {user2} وصفعه بـ {item} 😂",
    "{user1} رمى {item} في وجه {user2} 🤣",
]

ARABIC_ITEMS = [
    "مقلاة حديد 🍳",
    "سمكة كبيرة 🐟",
    "خشبة 🪵",
    "حذاء قديم 👟",
    "كتاب ثقيل 📚",
    "لابتوب 💻",
    "كرسي 🪑",
    "بطيخة 🍉",
    "قطة غاضبة 🐱",
    "صخرة 🪨",
    "مزهرية 🏺",
    "تورتة 🎂",
    "بيضة 🥚",
    "طماطم 🍅",
    "موبايل قديم 📱",
]

ARABIC_HIT = [
    "ضرب",
    "صفع",
    "لطم",
    "خبط",
    "نقر",
    "رفس",
]

ARABIC_THROW = [
    "رمى",
    "قذف",
    "حدف",
    "طوّح",
    "وزّع",
]

ARABIC_RUN_STRINGS = [
    "🏃 وين تبي تروح؟",
    "🏃 هيه؟ شو؟ وين؟",
    "🏃 اهرب اهرب! 😂",
    "🏃 جرب هالرابط: t.me/هروب_سريع",
    "🏃 يقولك ما يقدر يلحقك...",
    "🏃 خذ يمين! لا يسار! 😂",
    "🏃 ما تقدر تهرب مني! 😈",
    "🏃 /اهرب مرة ثانية! 🤣",
    "🏃 استناني! ⏳",
    "🏃 وراك وراك! 🏃‍♂️💨",
]


@kigcmd(command='runs')
@spamcheck
def runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.RUN_STRINGS))


# ==================== معالج عربي للهروب ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_RUNS_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(ARABIC_RUN_STRINGS))


@kigcmd(command='slap')
@spamcheck
def slap(update: Update, context: CallbackContext):
    bot: telegram.Bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat

    reply_text = (
        message.reply_to_message.reply_text
        if message.reply_to_message
        else message.reply_text
    )

    curr_user = html.escape(message.from_user.first_name) if not message.sender_chat else html.escape(
        message.sender_chat.title)
    user_id = extract_user(message, args)

    if user_id == bot.id:
        temp = random.choice(fun_strings.SLAP_Kigyō_TEMPLATES)

        if isinstance(temp, list):
            if temp[2] == "tmute":
                if user_is_admin(update, message.from_user.id):
                    reply_text(temp[1])
                    return

                mutetime = int(time.time() + 60)
                bot.restrict_chat_member(
                    chat.id,
                    message.from_user.id,
                    until_date=mutetime,
                    permissions=ChatPermissions(can_send_messages=False),
                )
            reply_text(temp[0])
        else:
            reply_text(temp)
        return

    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(slapped_user.first_name if slapped_user.first_name else slapped_user.title)
    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(fun_strings.SLAP_TEMPLATES)
    item = random.choice(fun_strings.ITEMS)
    hit = random.choice(fun_strings.HIT)
    throw = random.choice(fun_strings.THROW)
    reply = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(reply, parse_mode=ParseMode.HTML)


# ==================== معالج عربي للصفعة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_SLAP_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_slap(update: Update, context: CallbackContext):
    bot: telegram.Bot = context.bot
    message = update.effective_message
    chat = update.effective_chat

    reply_text = (
        message.reply_to_message.reply_text
        if message.reply_to_message
        else message.reply_text
    )

    curr_user = html.escape(message.from_user.first_name) if not message.sender_chat else html.escape(
        message.sender_chat.title)

    text = message.text
    for cmd in ARABIC_SLAP_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif text:
        user_id = extract_user(message, text.split())
    else:
        user_id = None

    if user_id == bot.id:
        reply_text("😏 تبي تصفعني؟ لا أنا اللي أصفعك! 👋😂")
        return

    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(slapped_user.first_name if slapped_user.first_name else slapped_user.title)
    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(ARABIC_SLAP_TEMPLATES)
    item = random.choice(ARABIC_ITEMS)
    hit = random.choice(ARABIC_HIT)
    throw = random.choice(ARABIC_THROW)
    reply = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(reply, parse_mode=ParseMode.HTML)


@kigcmd(command='pat')
@spamcheck
def pat(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = str(update.message.text)
    try:
        msg = msg.split(" ", 1)[1]
    except IndexError:
        msg = ""
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )
    pats = []
    pats = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                "http://headp.at/js/pats.json",
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) "
                                  "Gecko/20071127 Firefox/2.0.0.11"
                },
            )
        )
            .read()
            .decode("utf-8")
    )
    if "@" in msg and len(msg) > 5:
        context.bot.send_photo(
            chat_id,
            f"https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}",
            caption=msg,
        )
    else:
        context.bot.send_photo(
            chat_id,
            f"https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}",
            reply_to_message_id=msg_id,
        )


# ==================== معالج عربي للتربيت ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_PAT_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_pat(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )
    try:
        pats = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(
                    "http://headp.at/js/pats.json",
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) "
                                      "Gecko/20071127 Firefox/2.0.0.11"
                    },
                )
            )
                .read()
                .decode("utf-8")
        )
        context.bot.send_photo(
            chat_id,
            f"https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}",
            reply_to_message_id=msg_id,
            caption="🤗 تربيت على الراس!",
        )
    except:
        update.effective_message.reply_text("🤗 *يربت على راسك*", parse_mode=ParseMode.MARKDOWN)


@kigcmd(command='roll')
@spamcheck
def roll(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(range(1, 7)))


# ==================== معالج عربي للنرد ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_ROLL_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_roll(update: Update, context: CallbackContext):
    result = random.choice(range(1, 7))
    dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    update.message.reply_text(f"🎲 النتيجة: {dice_emoji[result-1]} ({result})")


@kigcmd(command='toss')
@spamcheck
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(fun_strings.TOSS))


# ==================== معالج عربي للعملة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_TOSS_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(ARABIC_TOSS))


@kigcmd(command='shrug')
@spamcheck
def shrug(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(r"¯\_(ツ)_/¯")


# ==================== معالج عربي لمدري ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_SHRUG_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_shrug(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(r"🤷 ¯\_(ツ)_/¯ مدري والله!")


@kigcmd(command='rlg')
@spamcheck
def rlg(update: Update, context: CallbackContext):
    eyes = random.choice(fun_strings.EYES)
    mouth = random.choice(fun_strings.MOUTHS)
    ears = random.choice(fun_strings.EARS)

    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    update.message.reply_text(repl)


# ==================== معالج عربي للوجه العشوائي ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_RLG_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_rlg(update: Update, context: CallbackContext):
    eyes = random.choice(fun_strings.EYES)
    mouth = random.choice(fun_strings.MOUTHS)
    ears = random.choice(fun_strings.EARS)

    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    update.message.reply_text(f"😎 وجهك اليوم: {repl}")


@kigcmd(command='decide')
@spamcheck
def decide(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(fun_strings.DECIDE))


# ==================== معالج عربي للقرار ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_DECIDE_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_decide(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(ARABIC_DECIDE))


@kigcmd(command='table')
@spamcheck
def table(update: Update, context: CallbackContext):
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(fun_strings.TABLE))


# ==================== معالج عربي للطاولة ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_TABLE_COMMANDS) + r')$'), group=3)
@spamcheck
def arabic_table(update: Update, context: CallbackContext):
    tables = [
        "(╯°□°)╯︵ ┻━┻ خلاص طفشت!",
        "┬─┬ノ( º _ ºノ) لا لا رجّع الطاولة!",
        "(ノಠ益ಠ)ノ彡┻━┻ اقلب كل شي!",
        "┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻ اقلبوا كل شي!",
        "(╯ರ ~ ರ)╯︵ ┻━┻ يا سلام!",
        "┬──┬◡ﾉ(° -°ﾉ) خلاص هدي!",
    ]
    reply_text = (
        update.effective_message.reply_to_message.reply_text
        if update.effective_message.reply_to_message
        else update.effective_message.reply_text
    )
    reply_text(random.choice(tables))


# ==================== ألعاب عربية إضافية ====================

# لعبة الحظ
@kigmsg(Filters.regex(r'^(حظي|حظ|حظي_اليوم)$'), group=3)
@spamcheck
def arabic_luck(update: Update, context: CallbackContext):
    luck = random.randint(1, 100)
    user_name = update.effective_user.first_name
    
    if luck >= 90:
        msg = f"🌟 {user_name}، حظك اليوم {luck}%!\n✨ يومك ممتاز! كل شي حيمشي تمام!"
    elif luck >= 70:
        msg = f"😄 {user_name}، حظك اليوم {luck}%!\n👍 يومك حلو! استمتع فيه!"
    elif luck >= 50:
        msg = f"😐 {user_name}، حظك اليوم {luck}%!\n🤷 يوم عادي، لا حلو ولا سيء."
    elif luck >= 30:
        msg = f"😅 {user_name}، حظك اليوم {luck}%!\n⚠️ خلي بالك اليوم شوية!"
    else:
        msg = f"😰 {user_name}، حظك اليوم {luck}%!\n🛌 الأفضل ترجع تنام! 😂"
    
    update.message.reply_text(msg)


# لعبة التخمين
@kigmsg(Filters.regex(r'^(خمن|تخمين)\s*(\d+)?$'), group=3)
@spamcheck
def arabic_guess(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text
    
    for cmd in ["خمن", "تخمين"]:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    if not text or not text.isdigit():
        message.reply_text(
            "🎯 لعبة التخمين!\n"
            "اكتب رقم من 1 إلى 10:\n"
            "مثال: `خمن 5`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    
    guess = int(text)
    if guess < 1 or guess > 10:
        message.reply_text("⚠️ اختر رقم من 1 إلى 10!")
        return
    
    answer = random.randint(1, 10)
    
    if guess == answer:
        message.reply_text(f"🎉 برافو! الرقم كان {answer}! أنت عبقري! 🧠")
    elif abs(guess - answer) <= 2:
        message.reply_text(f"😅 قريب! الرقم كان {answer}. جرب مرة ثانية!")
    else:
        message.reply_text(f"❌ غلط! الرقم كان {answer}. حاول مرة ثانية! 🔄")


# لعبة الحجر والورقة والمقص
@kigmsg(Filters.regex(r'^(حجر|ورقة|مقص)$'), group=3)
@spamcheck
def arabic_rps(update: Update, context: CallbackContext):
    user_choice = update.effective_message.text.strip()
    choices = ["حجر", "ورقة", "مقص"]
    bot_choice = random.choice(choices)
    
    emojis = {"حجر": "🪨", "ورقة": "📄", "مقص": "✂️"}
    
    if user_choice == bot_choice:
        result = "🤝 تعادل!"
    elif (
        (user_choice == "حجر" and bot_choice == "مقص") or
        (user_choice == "ورقة" and bot_choice == "حجر") or
        (user_choice == "مقص" and bot_choice == "ورقة")
    ):
        result = "🎉 فزت أنت!"
    else:
        result = "😎 فزت أنا!"
    
    update.effective_message.reply_text(
        f"أنت: {emojis[user_choice]} {user_choice}\n"
        f"أنا: {emojis[bot_choice]} {bot_choice}\n\n"
        f"{result}"
    )


from .language import gs

def get_help(chat):
    return gs(chat, "fun_help")

__mod_name__ = "المرح"
