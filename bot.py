import logging
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv
from signal_engine.search import search_coins
from signal_engine.signals import generate_signal, get_usd_price
from signal_engine.utils import format_price
from telegram.ext import MessageHandler, Filters

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------- کمک‌کننده برای ساخت صفحه نتایج ----------

def build_results_page_text_and_keyboard(coins, query_text, page, page_size=6):
    start = (page - 1) * page_size
    end = start + page_size
    chunk = coins[start:end]

    text = f"🔎 نتایج برای «{query_text}» - صفحه {page}\n\n"

    keyboard_rows = []

    for c in chunk:
        text += (
            f"🪙 {c['name']} ({c['symbol'].upper()})\n"
            f"💵 قیمت: {format_price(c['current_price'])}$\n"
            f"💰 ارزش بازار: {c['market_cap']/1e9:.1f}B$\n\n"
        )
        keyboard_rows.append([
            InlineKeyboardButton(
                f"📊 سیگنال {c['symbol'].upper()}",
                callback_data=f"signal:{c['id']}"
            )
        ])

    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton(
                "صفحه قبل",
                callback_data=f"page:{query_text}:{page-1}"
            )
        )
    if end < len(coins):
        nav_row.append(
            InlineKeyboardButton(
                "صفحه بعد",
                callback_data=f"page:{query_text}:{page+1}"
            )
        )

    if nav_row:
        keyboard_rows.append(nav_row)

    keyboard = InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None
    return text, keyboard


# ---------- هندلرها ----------

def start(update, context):
    update.message.reply_text(
        "سلام 👋\n\n"
        "برای جستجوی رمزارز از دستور زیر استفاده کن:\n"
        "/signal btc\n"
        "/signal sol\n"
        "/signal sonic\n"
    )


def signal_autocomplete(update, context):
    args = context.args
    if not args:
        update.message.reply_text("مثال:\n/signal btc")
        return

    query_text = " ".join(args).lower().strip()
    coins = search_coins(query_text)

    if coins == "SHORT_QUERY":
        update.message.reply_text("حداقل ۲ حرف وارد کن 🔍")
        return

    if not coins:
        update.message.reply_text("چیزی پیدا نشد.")
        return

    # صفحه ۱ نتایج، در یک پیام با دکمه‌ها
    page = 1
    text, keyboard = build_results_page_text_and_keyboard(
        coins, query_text, page)
    update.message.reply_text(text, reply_markup=keyboard)


def paginate_results(update, context):
    query = update.callback_query
    query.answer()

    _, q, page_str = query.data.split(":")
    page = int(page_str)

    coins = search_coins(q)
    if not coins:
        query.edit_message_text("چیزی پیدا نشد.")
        return

    text, keyboard = build_results_page_text_and_keyboard(coins, q, page)
    query.edit_message_text(text, reply_markup=keyboard)


def signal_button(update, context):
    query = update.callback_query
    query.answer()

    coin_id = query.data.split(":", 1)[1]
    result = generate_signal(coin_id)
    usd_price = get_usd_price()
    price_toman = result["price"] * usd_price

    if not result:
        query.edit_message_text("خطا در دریافت سیگنال.")
        return

    reasons = "\n".join([f"- {r}" for r in result["reason"]])

    text = (
        f"🪙 سیگنال برای: {result['symbol']}\n"
        f"💵 قیمت فعلی: {format_price(result['price'])}$\n"
        f"🏷️ قیمت به تومان: {price_toman:,.0f}\n"
        f"📈 سیگنال: {result['signal']}\n"
        f"🎯 اعتماد: {result['confidence']}\n"
        f"📝 دلایل:\n{reasons}"
    )

    query.edit_message_text(text)


def auto_signal(update, context):
    text = update.message.text.strip().lower()

    # اگر پیام کوتاه بود، نادیده بگیر
    if len(text) < 2:
        return

    # اگر خودش دستور بود، کاری نکن
    if text.startswith("/"):
        return

    # اجرای خودکار سیگنال
    context.args = [text]
    return signal_autocomplete(update, context)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("signal", signal_autocomplete))
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command, auto_signal))
    dp.add_handler(CallbackQueryHandler(paginate_results, pattern=r"^page:"))
    dp.add_handler(CallbackQueryHandler(signal_button, pattern=r"^signal:"))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
