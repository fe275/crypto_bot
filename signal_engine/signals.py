import requests
from .utils import format_price

CACHE = {}


def generate_signal(coin_id):
    key = ("signal", coin_id)
    if key in CACHE:
        return CACHE[key]

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    data = requests.get(url).json()

    if "market_data" not in data:
        return None

    price = data["market_data"]["current_price"]["usd"]
    change_24h = data["market_data"]["price_change_percentage_24h"]
    change_7d = data["market_data"]["price_change_percentage_7d"]
    volume = data["market_data"]["total_volume"]["usd"]

    reasons = []

    if change_24h > 5:
        signal = "خرید با احتیاط"
        reasons.append("رشد قوی در ۲۴ ساعت اخیر")
    elif change_24h < -5:
        signal = "فروش / ریسک بالا"
        reasons.append("سقوط شدید در ۲۴ ساعت اخیر")
    else:
        signal = "خنثی"
        reasons.append("نوسان معمولی")

    if change_7d > 10:
        reasons.append("روند هفتگی صعودی")
    if change_7d < -10:
        reasons.append("روند هفتگی نزولی")

    if volume > 100_000_000:
        reasons.append("حجم معاملات بالا → توجه بازار زیاد است")

    result = {
        "symbol": data["symbol"].upper(),
        "price": price,
        "signal": signal,
        "confidence": "متوسط",
        "reason": reasons
    }

    CACHE[key] = result
    return result


def get_usd_price():
    try:
        r = requests.get("https://baha24.com/api/v1/price?code=usd", timeout=5)
        data = r.json()
        return int(data["price"])  # قیمت به تومان
    except:
        return 180000  # fallback
