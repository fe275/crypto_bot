import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown
from dotenv import load_dotenv
import os

from signal_engine.search import search_coins
from signal_engine.signals import generate_signal
from signal_engine.utils import format_price

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(
        "سلام 👋\n\n"
        "برای جستجوی رمزارز:\n"
        "/signal btc\n"
        "/signal sol\n"
        "/signal sonic\n"
    )


def signal_autocomplete(update, context):
    args = context.args
    if not args:
        update.message.reply_text("مثال:\n/signal btc")
        return

    query = " ".join(args).lower().strip()
    coins = search_coins(query)

    if coins == "SHORT_QUERY":
        update.message.reply_text("حداقل ۲ حرف وارد کن 🔍")
        return

    if not coins:
        update.message.reply_text("چیزی پیدا نشد.")
        return

    # صفحه اول
    chunk = coins[:6]

    for c in chunk:
        text = (
            f"🪙 {c['name']} ({c['symbol']})\n"
            f"💰 قیمت: {format_price(c['current_price'])}$\n"
            f"📦 مارکت‌کپ: {c['market_cap']/1e9:.1f}B$\n"
        )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "📈 دریافت سیگنال", callback_data=f"signal:{c['id']}")]]
        )
        update.message.reply_text(text, reply_markup=keyboard)

    if len(coins) > 6:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "⏭ صفحه بعد", callback_data=f"page:{query}:2")]]
        )
        update.message.reply_text(
            "نتایج بیشتری موجود است:", reply_markup=keyboard)


def paginate_results(update, context):
    query = update.callback_query
    query.answer()

    _, q, page_str = query.data.split(":")
    page = int(page_str)

    coins = search_coins(q)
    if not coins:
        query.edit_message_text("چیزی پیدا نشد.")
        return

    start = (page - 1) * 6
    end = start + 6
    chunk = coins[start:end]

    if not chunk:
        query.edit_message_text("صفحه‌ای وجود ندارد.")
        return

    text = f"🔎 نتایج صفحه {page}:\n\n"

    for c in chunk:
        text += (
            f"🪙 {c['name']} ({c['symbol']})\n"
            f"💰 قیمت: {format_price(c['current_price'])}$\n"
            f"📦 مارکت‌کپ: {c['market_cap']/1e9:.1f}B$\n\n"
        )

    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(
            "⏮ صفحه قبل", callback_data=f"page:{q}:{page-1}"))

    if end < len(coins):
        buttons.append(InlineKeyboardButton(
            "⏭ صفحه بعد", callback_data=f"page:{q}:{page+1}"))

    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    query.edit_message_text(text, reply_markup=keyboard)


def signal_button(update, context):
    query = update.callback_query
    query.answer()

    coin_id = query.data.split(":", 1)[1]
    result = generate_signal(coin_id)

    if not result:
        query.edit_message_text("خطا در دریافت سیگنال.")
        return

    reasons = "\n".join([f"- {r}" for r in result["reason"]])

    text = (
        f"📊 سیگنال برای: {result['symbol']}\n"
        f"💰 قیمت فعلی: {format_price(result['price'])}$\n"
        f"📌 سیگنال: {result['signal']}\n"
        f"🎯 اعتماد: {result['confidence']}\n"
        f"📝 دلایل:\n{reasons}"
    )

    query.edit_message_text(text)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("signal", signal_autocomplete))

    dp.add_handler(CallbackQueryHandler(paginate_results, pattern="^page:"))
    dp.add_handler(CallbackQueryHandler(signal_button, pattern="^signal:"))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
