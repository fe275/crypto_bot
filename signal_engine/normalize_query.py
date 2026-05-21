from fuzzywuzzy import fuzz
from signal_engine.fa_map import FA_TO_EN


def normalize_query(q):
    q = q.strip().lower()

    # اگر دقیقاً در دیکشنری بود
    if q in FA_TO_EN:
        return FA_TO_EN[q]

    # جستجوی فازی فقط برای غلط‌های تایپی واقعی
    best_match = None
    best_score = 0

    for fa_word in FA_TO_EN.keys():
        score = fuzz.ratio(q, fa_word)
        if score > best_score:
            best_score = score
            best_match = fa_word

    # فقط اگر شباهت خیلی زیاد بود → قبول
    if best_score >= 85:
        return FA_TO_EN[best_match]

    return q
