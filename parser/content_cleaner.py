import json
import re
import os
from bs4 import BeautifulSoup


def normalize_persian(text):
    """یکنواخت‌سازی حروف فارسی."""
    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "‌": " ",  # نیم‌فاصله → فاصله
        "\u200c": " ",  # ZWNJ
    }
    for f, t in replacements.items():
        text = text.replace(f, t)
    return text


def clean_text(raw_html):
    """حذف کامل HTML و تمیز کردن متن مقاله."""
    soup = BeautifulSoup(raw_html, "html.parser")

    # حذف اسکریپت، استایل، تبلیغات
    for tag in soup(["script", "style", "noscript", "footer", "header"]):
        tag.extract()

    text = soup.get_text(separator=" ", strip=True)

    # حذف فاصله‌های تکراری
    text = re.sub(r"\s+", " ", text)

    # نرمال‌سازی فارسی
    text = normalize_persian(text)

    return text.strip()


def clean_dataset(input_path, output_path, min_chars=300):
    """پاک‌سازی کامل دیتاست و ذخیره نسخه تمیز شده."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = []

    for item in data:
        raw_text = item.get("content", "")
        if not raw_text or len(raw_text.strip()) == 0:
            continue

        cleaned_text = clean_text(raw_text)

        # رد مقاله‌های خیلی کوتاه/خراب
        if len(cleaned_text) < min_chars:
            continue

        # ساختار خروجی استاندارد
        cleaned.append(
            {
                "id": item.get("id"),
                "url": item.get("url"),
                "title": normalize_persian(item.get("title", "")),
                "content": cleaned_text,
                "publish_date": item.get("publish_date"),
                "outgoing_links": item.get("outgoing_links", []),
                "incoming_links": [],  # بعداً ساخته می‌شود
                "language": "fa",
                "source": "isna",
                "label": "real",
            }
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"✓ Cleaned {len(cleaned)} articles → {output_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(__file__))

    input_path = os.path.join(base_dir, "data", "isna_sample.json")
    output_path = os.path.join(base_dir, "data", "cleaned", "isna_cleaned.json")

    clean_dataset(input_path, output_path)
