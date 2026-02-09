import importlib

from tg_bot import dispatcher, spamcheck
from .helper_funcs.chat_status import dev_plus, sudo_plus
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from .helper_funcs.decorators import kigcmd


def _get_main_vars():
    """
    جلب المتغيرات من __main__ بشكل آمن بدون circular import
    """
    import tg_bot.__main__ as main_module
    return {
        "IMPORTED": getattr(main_module, "IMPORTED", {}),
        "HELPABLE": getattr(main_module, "HELPABLE", {}),
        "MIGRATEABLE": getattr(main_module, "MIGRATEABLE", []),
        "STATS": getattr(main_module, "STATS", []),
        "USER_INFO": getattr(main_module, "USER_INFO", []),
        "DATA_IMPORT": getattr(main_module, "DATA_IMPORT", []),
        "DATA_EXPORT": getattr(main_module, "DATA_EXPORT", []),
        "CHAT_SETTINGS": getattr(main_module, "CHAT_SETTINGS", {}),
        "USER_SETTINGS": getattr(main_module, "USER_SETTINGS", {}),
    }


@kigcmd(command='load')
@dev_plus
def load(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text.split(" ", 1)[1]
    load_messasge = message.reply_text(
        f"جاري تحميل الوحدة: <b>{text}</b>", parse_mode=ParseMode.HTML
    )

    try:
        imported_module = importlib.import_module("tg_bot.modules." + text)
    except:
        load_messasge.edit_text("❌ هالوحدة مش موجودة!")
        return

    main_vars = _get_main_vars()
    IMPORTED = main_vars["IMPORTED"]
    HELPABLE = main_vars["HELPABLE"]
    MIGRATEABLE = main_vars["MIGRATEABLE"]
    STATS = main_vars["STATS"]
    USER_INFO = main_vars["USER_INFO"]
    DATA_IMPORT = main_vars["DATA_IMPORT"]
    DATA_EXPORT = main_vars["DATA_EXPORT"]
    CHAT_SETTINGS = main_vars["CHAT_SETTINGS"]
    USER_SETTINGS = main_vars["USER_SETTINGS"]

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        load_messasge.edit_text("⚠️ الوحدة محملة مسبقاً!")
        return

    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if type(handler) != tuple:
                dispatcher.add_handler(handler)
            else:
                handler_name, priority = handler
                dispatcher.add_handler(handler_name, priority)
    else:
        IMPORTED.pop(imported_module.__mod_name__.lower())
        load_messasge.edit_text("❌ ما نقدر نحمل هالوحدة!")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    load_messasge.edit_text(
        "✅ تم تحميل الوحدة: <b>{}</b>".format(text), parse_mode=ParseMode.HTML
    )


@kigcmd(command='unload')
@dev_plus
def unload(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text.split(" ", 1)[1]
    unload_messasge = message.reply_text(
        f"جاري ازالة الوحدة: <b>{text}</b>", parse_mode=ParseMode.HTML
    )

    try:
        imported_module = importlib.import_module("tg_bot.modules." + text)
    except:
        unload_messasge.edit_text("❌ هالوحدة مش موجودة!")
        return

    main_vars = _get_main_vars()
    IMPORTED = main_vars["IMPORTED"]
    HELPABLE = main_vars["HELPABLE"]
    MIGRATEABLE = main_vars["MIGRATEABLE"]
    STATS = main_vars["STATS"]
    USER_INFO = main_vars["USER_INFO"]
    DATA_IMPORT = main_vars["DATA_IMPORT"]
    DATA_EXPORT = main_vars["DATA_EXPORT"]
    CHAT_SETTINGS = main_vars["CHAT_SETTINGS"]
    USER_SETTINGS = main_vars["USER_SETTINGS"]

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED.pop(imported_module.__mod_name__.lower())
    else:
        unload_messasge.edit_text("❌ ما تقدر تشيل حاجة مش محملة!")
        return

    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if type(handler) == bool:
                unload_messasge.edit_text("⚠️ هالوحدة ما تقدر تشيلها!")
                return
            elif type(handler) != tuple:
                dispatcher.remove_handler(handler)
            else:
                handler_name, priority = handler
                dispatcher.remove_handler(handler_name, priority)
    else:
        unload_messasge.edit_text("❌ ما نقدر نشيل هالوحدة!")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE.pop(imported_module.__mod_name__.lower())

    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.remove(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.remove(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.remove(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.remove(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.remove(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS.pop(imported_module.__mod_name__.lower())

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS.pop(imported_module.__mod_name__.lower())

    unload_messasge.edit_text(
        f"✅ تم ازالة الوحدة: <b>{text}</b>", parse_mode=ParseMode.HTML
    )


@kigcmd(command='listmodules')
@spamcheck
@sudo_plus
def listmodules(update: Update, context: CallbackContext):
    message = update.effective_message

    main_vars = _get_main_vars()
    IMPORTED = main_vars["IMPORTED"]
    HELPABLE = main_vars["HELPABLE"]

    module_list = []

    for helpable_module in HELPABLE:
        helpable_module_info = IMPORTED[helpable_module]
        file_info = IMPORTED[helpable_module_info.__mod_name__.lower()]
        file_name = file_info.__name__.rsplit("tg_bot.modules.", 1)[1]
        mod_name = file_info.__mod_name__
        module_list.append(f"- <code>{mod_name} ({file_name})</code>\n")

    module_list = "📦 <b>الوحدات المحملة:</b>\n\n" + "".join(module_list)
    message.reply_text(module_list, parse_mode=ParseMode.HTML)


__mod_name__ = "Modules"
