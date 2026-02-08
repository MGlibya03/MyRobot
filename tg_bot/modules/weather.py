# from AstrakoBot
import json
from datetime import datetime

from pytz import country_timezones as c_tz, timezone as tz, country_names as c_n
from requests import get
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async, Filters
from tg_bot import WEATHER_API, dispatcher, spamcheck
from .sql.clear_cmd_sql import get_clearcmd
from .helper_funcs.misc import delete
from .helper_funcs.decorators import kigcmd, kigmsg

# ==================== الأوامر العربية ====================
ARABIC_WEATHER_COMMANDS = ["طقس", "الطقس", "حالة_الطقس", "جو"]


def get_tz(con):
    for c_code in c_n:
        if con == c_n[c_code]:
            return tz(c_tz[c_code][0])
    try:
        if c_n[con]:
            return tz(c_tz[con][0])
    except KeyError:
        return


@kigcmd(command='weather')
@spamcheck
def weather(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    city = message.text[len("/weather ") :]

    if city:
        APPID = WEATHER_API
        result = None
        timezone_countries = {
            timezone: country
            for country, timezones in c_tz.items()
            for timezone in timezones
        }

        if "," in city:
            newcity = city.split(",")
            if len(newcity[1]) == 2:
                city = newcity[0].strip() + "," + newcity[1].strip()
            else:
                country = get_tz((newcity[1].strip()).title())
                try:
                    countrycode = timezone_countries[f"{country}"]
                except KeyError:
                    return message.reply_text("⚠️ دولة غير صحيحة!")
                city = newcity[0].strip() + "," + countrycode.strip()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={APPID}"
        try:
            request = get(url)
            result = json.loads(request.text)
        except ConnectionError:
            return message.reply_text("⚠️ انقطع الاتصال! جرب مرة ثانية بعد شوية.")

        if request.status_code != 200:
            msg = "⚠️ ما لقيت معلومات طقس لهالمكان!"

        else:

            cityname = result["name"]
            longitude = result["coord"]["lon"]
            latitude = result["coord"]["lat"]
            curtemp = result["main"]["temp"]
            feels_like = result["main"]["feels_like"]
            humidity = result["main"]["humidity"]
            min_temp = result["main"]["temp_min"]
            max_temp = result["main"]["temp_max"]
            country = result["sys"]["country"]
            sunrise = result["sys"]["sunrise"]
            sunset = result["sys"]["sunset"]
            wind = result["wind"]["speed"]
            weath = result["weather"][0]
            desc = weath["main"]
            icon = weath["id"]
            condmain = weath["main"]
            conddet = weath["description"]

            # ترجمة حالة الطقس للعربي
            weather_ar = {
                "Clear": "صافي",
                "Clouds": "غيوم",
                "Rain": "مطر",
                "Drizzle": "رذاذ",
                "Thunderstorm": "عاصفة رعدية",
                "Snow": "ثلج",
                "Mist": "ضباب",
                "Smoke": "دخان",
                "Haze": "ضباب خفيف",
                "Dust": "غبار",
                "Fog": "ضباب كثيف",
                "Sand": "عاصفة رملية",
                "Ash": "رماد بركاني",
                "Squall": "عاصفة",
                "Tornado": "إعصار",
            }

            condmain_ar = weather_ar.get(condmain, condmain)

            if icon <= 232:  # Rain storm
                icon = "⛈"
            elif icon <= 321:  # Drizzle
                icon = "🌧"
            elif icon <= 504:  # Light rain
                icon = "🌦"
            elif icon <= 531:  # Cloudy rain
                icon = "⛈"
            elif icon <= 622:  # Snow
                icon = "❄️"
            elif icon <= 781:  # Atmosphere
                icon = "🌪"
            elif icon <= 800:  # Bright
                icon = "☀️"
            elif icon <= 801:  # A little cloudy
                icon = "⛅️"
            elif icon <= 804:  # Cloudy
                icon = "☁️"

            ctimezone = tz(c_tz[country][0])
            time = (
                datetime.now(ctimezone)
                .strftime("%A %d %b, %H:%M")
                .lstrip("0")
                .replace(" 0", " ")
            )
            fullc_n = c_n[f"{country}"]
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

            kmph = str(wind * 3.6).split(".")
            mph = str(wind * 2.237).split(".")

            def fahrenheit(f):
                temp = str(((f - 273.15) * 9 / 5 + 32)).split(".")
                return temp[0]

            def celsius(c):
                temp = str((c - 273.15)).split(".")
                return temp[0]

            def sun(unix):
                xx = (
                    datetime.fromtimestamp(unix, tz=ctimezone)
                    .strftime("%H:%M")
                    .lstrip("0")
                    .replace(" 0", " ")
                )
                return xx


            ## AirQuality
            air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={APPID}"
            try:
                air_data = json.loads(get(air_url).text)
                into_dicts = air_data['list'][0]          
                air_qi = into_dicts['main']
                aqi = int(air_qi['aqi'])
            except:
                aqi = None

            def air_qual(aqin):
                if aqin == 1:
                    return "ممتازة"
                elif aqin == 2:
                    return "جيدة"
                elif aqin == 3:
                    return 'متوسطة'                
                elif aqin == 4:
                    return 'سيئة'
                elif aqin == 5:
                    return "سيئة جداً"
                else:
                    return "غير متوفر"


            msg = f"🌍 *{cityname}, {fullc_n}*\n"
            msg += f"📍 `خط الطول: {longitude}`\n"
            msg += f"📍 `خط العرض: {latitude}`\n\n"
            msg += f"🕐 **الوقت:** `{time}`\n"
            msg += f"🌡 **درجة الحرارة:** `{celsius(curtemp)}°C`\n"
            msg += f"🤚 **الإحساس بـ:** `{celsius(feels_like)}°C`\n"
            msg += f"☁️ **الحالة:** `{condmain_ar}` {icon}\n"
            msg += f"💧 **الرطوبة:** `{humidity}%`\n"
            msg += f"💨 **الرياح:** `{kmph[0]} كم/س`\n"
            msg += f"🌅 **الشروق:** `{sun(sunrise)}`\n"
            msg += f"🌇 **الغروب:** `{sun(sunset)}`\n"
            if aqi:
                msg += f"🌫 **جودة الهواء:** `{air_qual(aqi)}`"
        
    else:
        msg = "⚠️ حدد اسم مدينة أو دولة!\n\nمثال: `طقس طرابلس` أو `طقس بنغازي`"
            
            
    delmsg = message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    cleartime = get_clearcmd(chat.id, "weather")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


# ==================== معالج عربي للطقس ====================
@kigmsg(Filters.regex(r'^(' + '|'.join(ARABIC_WEATHER_COMMANDS) + r')(\s|$)'), group=3)
@spamcheck
def arabic_weather(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    
    text = message.text
    for cmd in ARABIC_WEATHER_COMMANDS:
        if text.startswith(cmd):
            text = text[len(cmd):].strip()
            break
    
    city = text

    if not city:
        return message.reply_text(
            "⚠️ حدد اسم مدينة أو دولة!\n\n"
            "📝 أمثلة:\n"
            "• `طقس طرابلس`\n"
            "• `طقس بنغازي`\n"
            "• `طقس القاهرة`\n"
            "• `طقس دبي`\n"
            "• `طقس London`",
            parse_mode=ParseMode.MARKDOWN,
        )

    APPID = WEATHER_API
    result = None
    timezone_countries = {
        timezone: country
        for country, timezones in c_tz.items()
        for timezone in timezones
    }

    if "," in city:
        newcity = city.split(",")
        if len(newcity[1]) == 2:
            city = newcity[0].strip() + "," + newcity[1].strip()
        else:
            country = get_tz((newcity[1].strip()).title())
            try:
                countrycode = timezone_countries[f"{country}"]
            except KeyError:
                return message.reply_text("⚠️ دولة غير صحيحة!")
            city = newcity[0].strip() + "," + countrycode.strip()
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={APPID}"
    try:
        request = get(url)
        result = json.loads(request.text)
    except ConnectionError:
        return message.reply_text("⚠️ انقطع الاتصال! جرب مرة ثانية بعد شوية.")

    if request.status_code != 200:
        msg = "⚠️ ما لقيت معلومات طقس لهالمكان!"
    else:
        cityname = result["name"]
        longitude = result["coord"]["lon"]
        latitude = result["coord"]["lat"]
        curtemp = result["main"]["temp"]
        feels_like = result["main"]["feels_like"]
        humidity = result["main"]["humidity"]
        country = result["sys"]["country"]
        sunrise = result["sys"]["sunrise"]
        sunset = result["sys"]["sunset"]
        wind = result["wind"]["speed"]
        weath = result["weather"][0]
        icon = weath["id"]
        condmain = weath["main"]

        # ترجمة حالة الطقس
        weather_ar = {
            "Clear": "صافي",
            "Clouds": "غيوم",
            "Rain": "مطر",
            "Drizzle": "رذاذ",
            "Thunderstorm": "عاصفة رعدية",
            "Snow": "ثلج",
            "Mist": "ضباب",
            "Smoke": "دخان",
            "Haze": "ضباب خفيف",
            "Dust": "غبار",
            "Fog": "ضباب كثيف",
            "Sand": "عاصفة رملية",
        }

        condmain_ar = weather_ar.get(condmain, condmain)

        if icon <= 232:
            icon = "⛈"
        elif icon <= 321:
            icon = "🌧"
        elif icon <= 504:
            icon = "🌦"
        elif icon <= 531:
            icon = "⛈"
        elif icon <= 622:
            icon = "❄️"
        elif icon <= 781:
            icon = "🌪"
        elif icon <= 800:
            icon = "☀️"
        elif icon <= 801:
            icon = "⛅️"
        elif icon <= 804:
            icon = "☁️"

        ctimezone = tz(c_tz[country][0])
        time = (
            datetime.now(ctimezone)
            .strftime("%A %d %b, %H:%M")
            .lstrip("0")
            .replace(" 0", " ")
        )
        fullc_n = c_n[f"{country}"]
        kmph = str(wind * 3.6).split(".")

        def celsius(c):
            temp = str((c - 273.15)).split(".")
            return temp[0]

        def sun(unix):
            xx = (
                datetime.fromtimestamp(unix, tz=ctimezone)
                .strftime("%H:%M")
                .lstrip("0")
                .replace(" 0", " ")
            )
            return xx

        # جودة الهواء
        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={APPID}"
        try:
            air_data = json.loads(get(air_url).text)
            into_dicts = air_data['list'][0]          
            air_qi = into_dicts['main']
            aqi = int(air_qi['aqi'])
        except:
            aqi = None

        def air_qual(aqin):
            if aqin == 1:
                return "ممتازة"
            elif aqin == 2:
                return "جيدة"
            elif aqin == 3:
                return 'متوسطة'                
            elif aqin == 4:
                return 'سيئة'
            elif aqin == 5:
                return "سيئة جداً"
            else:
                return "غير متوفر"

        msg = f"🌍 *{cityname}, {fullc_n}*\n"
        msg += f"📍 `خط الطول: {longitude}`\n"
        msg += f"📍 `خط العرض: {latitude}`\n\n"
        msg += f"🕐 **الوقت:** `{time}`\n"
        msg += f"🌡 **درجة الحرارة:** `{celsius(curtemp)}°C`\n"
        msg += f"🤚 **الإحساس بـ:** `{celsius(feels_like)}°C`\n"
        msg += f"☁️ **الحالة:** `{condmain_ar}` {icon}\n"
        msg += f"💧 **الرطوبة:** `{humidity}%`\n"
        msg += f"💨 **الرياح:** `{kmph[0]} كم/س`\n"
        msg += f"🌅 **الشروق:** `{sun(sunrise)}`\n"
        msg += f"🌇 **الغروب:** `{sun(sunset)}`\n"
        if aqi:
            msg += f"🌫 **جودة الهواء:** `{air_qual(aqi)}`"

    delmsg = message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    cleartime = get_clearcmd(chat.id, "weather")
    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


from .language import gs

def get_help(chat):
    return gs(chat, "weather_help")

__mod_name__ = "الطقس"
