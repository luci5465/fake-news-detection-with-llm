import json
import re
import os
import unicodedata
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("PROJECT_DATA_DIR", os.path.join(BASE_DIR, "data"))

def normalize_persian(text):
    if not text: return ""
    
    replacements = {
        "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه",
        "ؤ": "و", "ئ": "ی", "أ": "ا", "إ": "ا",
        "آ": "ا", "اً": "ا",
        "‌": " ", "\u200c": " ",
        "…": " ", "—": "-", "ـ": "",
        "«": '"', "»": '"', "“": '"', "”": '"'
    }
    
    text = unicodedata.normalize("NFKC", text)
    for f, t in replacements.items():
        text = text.replace(f, t)
    
    return text

def clean_text(raw_content):
    if not raw_content: return ""

    text = normalize_persian(raw_content)

    noise_patterns = [
        r"انتهای پیام/?",
        r"کد خبر[:\s]*\d+",
        r"لینک کوتاه",
        r"برای مشاهده.*?کلیک کنید",
        r"مشاهده خبر",
        r"منبع[:\s]*\w+",
        r"تولید[:\s]*\w+",
        r"https?://[^\s<>\"']+|www\.[^\s<>\"']+",
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}",
        r"@[a-zA-Z0-9_]+",
        r"\b\d{5,}\b",
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    
    sentences = re.split(r"(?<=[.?!؛])\s+", text)
    clean_sentences = [s.strip() for s in sentences if len(s.split()) > 4]
    
    return " . ".join(clean_sentences).strip()

def process_file(input_path, output_path):
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load {os.path.basename(input_path)}")
        return 0

    cleaned_data = []
    dropped_count = 0

    for idx, item in enumerate(data):
        raw_content = item.get("content", "")
        clean_content = clean_text(raw_content)
        
        if len(clean_content) < 50:
            dropped_count += 1
            continue

        clean_item = {
            "id": f"{os.path.basename(input_path).split('_')[0]}_{idx}",
            "url": item.get("url"),
            "title": normalize_persian(item.get("title", "")),
            "content": clean_content,
            "publish_date": item.get("publish_date"),
            "outgoing_links": item.get("outgoing_links", []),
            "source": os.path.basename(input_path).split('_')[0]
        }
        cleaned_data.append(clean_item)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print(f"Cleaned {os.path.basename(input_path)} -> {len(cleaned_data)} items (Dropped {dropped_count})")
        return len(cleaned_data)
    except Exception as e:
        print(f"Error saving {output_path}: {e}")
        return 0

def run_cleaner():
    print("\n--- Data Cleaner & Normalizer ---")
    print(f"Scanning Directory: {DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        print(f"Directory not found!")
        return

    raw_files = [f for f in os.listdir(DATA_DIR) if f.endswith("_data.json")]
    
    if not raw_files:
        print("No raw data files (*_data.json) found.")
        print("Make sure you ran the crawlers first!")
        return

    print(f"Found {len(raw_files)} raw files to process.\n")
    
    total_processed = 0
    for file in raw_files:
        in_path = os.path.join(DATA_DIR, file)
        out_name = file.replace("_data.json", "_clean.json")
        out_path = os.path.join(DATA_DIR, out_name)
        
        total_processed += process_file(in_path, out_path)

    print(f"\nTotal Cleaned Articles Available: {total_processed}")

if __name__ == "__main__":
    run_cleaner()
