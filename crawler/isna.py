import requests
from bs4 import BeautifulSoup
from collections import deque
import logging
import time
import random
import re
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import json
import os
import sys

# تنظیم مسیر ذخیره‌سازی مرکزی
DATA_DIR = os.environ.get("PROJECT_DATA_DIR", "/home/luci/Desktop/fake_news/data")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
        except OSError:
            pass

def safe_request(url, retries=4, timeout=9):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "")
                if "text/html" in content_type.lower():
                    return r.text
        except Exception as e:
            pass
        time.sleep((2 ** attempt) + random.random())
    return None

def clean_soup(soup):
    remove_tags = [
        "script", "style", "iframe", "video", "figure",
        "nav", "footer", "header", "aside", "form"
    ]
    for tag_name in remove_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return soup

def normalize_url(base_url, href):
    return urljoin(base_url, href)

def same_domain(url):
    parsed = urlparse(url)
    return parsed.netloc.endswith("isna.ir") or parsed.netloc in ("www.isna.ir", "isna.ir")

def is_news_url(url):
    pattern = r"https?://(www\.)?isna\.ir/(fa/)?(news|service|photo)/\d{6,16}(/[^ \s<>#]+)?"
    return re.match(pattern, url) is not None

def extract_headline(soup):
    cands = [
        soup.find("h1", class_="first-title"),
        soup.find("h1", class_="title"),
        soup.find("h1", id="news-title"),
        soup.find("article").find("h1") if soup.find("article") else None,
        soup.find("meta", attrs={"property": "og:title"}),
        soup.find("meta", attrs={"name": "title"}),
        soup.title
    ]
    for c in cands:
        if not c:
            continue
        if hasattr(c, "get_text"):
            txt = c.get_text(strip=True)
        else:
            txt = c.get("content", "")
        if txt:
            txt = txt.split(" | ")[0]
            txt = txt.split(" - ")[0]
            txt = txt.replace("\u200c", " ")
            return txt.strip()
    return ""

def extract_content(soup):
    blocks = [
        ("tag", "article"),
        ("class", "story__body"),
        ("class", "news-body"),
        ("class", "item-body"),
        ("class", "read__content"),
        ("class", "body"),
        ("class", "content"),
        ("class", "item-text"),
        ("class", "text"),
        ("class", "paragraph"),
    ]
    for selector_type, value in blocks:
        part = None
        if selector_type == "tag":
            part = soup.find(value)
        elif selector_type == "class":
            part = soup.find("div", class_=value)
        
        if part:
            ps = part.find_all("p")
            if ps:
                text = " ".join(p.get_text(" ", strip=True) for p in ps)
                text = re.sub(r"\s+", " ", text).strip()
                if len(text.split()) > 50:
                    return text

    ps = soup.find_all("p")
    if ps:
        text = " ".join(p.get_text(" ", strip=True) for p in ps)
        return re.sub(r"\s+", " ", text).strip()
    return ""

def normalize_date(raw_date):
    if not raw_date:
        return "unknown"
    
    months = {
        "فروردین": "01", "اردیبهشت": "02", "خرداد": "03",
        "تیر": "04", "مرداد": "05", "شهریور": "06",
        "مهر": "07", "آبان": "08", "آذر": "09",
        "دی": "10", "بهمن": "11", "اسفند": "12"
    }
    
    parts = raw_date.split()
    day, month, year, time_str = "", "", "", ""

    for part in parts:
        if part in months:
            month = months[part]
        elif re.match(r"^\d{4}$", part):
            year = part
        elif re.match(r"^\d{1,2}$", part):
            day = part.zfill(2)
        elif re.match(r"^\d{1,2}:\d{2}$", part):
            time_str = part
    
    if year and month and day:
        final = f"{year}-{month}-{day}"
        if time_str:
            final += f" {time_str}"
        return final
        
    return raw_date

def extract_publish_date(soup):
    cands = [
        soup.find("span", class_="item-date"),
        soup.find("span", class_="date-publish"),
        soup.find("time"),
        soup.find("meta", attrs={"property": "article:published_time"}),
        soup.find("meta", attrs={"name": "pubdate"}),
        soup.find("meta", attrs={"name": "lastmod"})
    ]
    for c in cands:
        if not c:
            continue
        if hasattr(c, "get_text"):
            txt = c.get_text(strip=True)
        else:
            txt = c.get("content", "")
        if txt:
            return normalize_date(txt.strip())
    return "unknown"

def extract_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        full = normalize_url(base_url, a["href"])
        if same_domain(full) and is_news_url(full):
            links.add(full)
    return list(links)

def save_data(data, depth):
    if not data:
        print("No data collected to save.")
        return

    ensure_data_dir()
    filename = f"isna_depth{depth}_raw.json"
    filepath = os.path.join(DATA_DIR, filename)

    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except:
            pass
    
    
    all_data = existing_data + data
    unique_data = {item['url']: item for item in all_data}.values()
    final_list = list(unique_data)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_list, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Successfully saved {len(final_list)} unique articles to:")
        print(f"   📂 {filepath}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def run_interactive():
    print("\n--- ISNA Crawler Setup ---")
    
    
    try:
        d_in = input("Enter Crawl Depth (1-10) [Default: 2]: ").strip()
        max_depth = int(d_in) if d_in else 2
    except ValueError:
        max_depth = 2

    
    try:
        p_in = input("Max Pages to Fetch [Default: 100]: ").strip()
        max_pages = int(p_in) if p_in else 100
    except ValueError:
        max_pages = 100

    start_url = "https://www.isna.ir/"
    
    print(f"\n🚀 Starting Crawl...")
    print(f"   Target: {start_url}")
    print(f"   Depth: {max_depth}")
    print(f"   Max Pages: {max_pages}")
    print("-----------------------------------")

    visited = set()
    queue = deque([(start_url, 0)])
    results = []
    in_queue = set([start_url])
    
    pbar = tqdm(total=max_pages, desc="Crawling", unit="page")

    while queue and len(results) < max_pages:
        url, depth = queue.popleft()
        
        if depth > max_depth or url in visited:
            continue
            
        visited.add(url)
        html = safe_request(url)
        
        if not html:
            continue

        soup = clean_soup(BeautifulSoup(html, "html.parser"))
        
        
        if url == start_url or not is_news_url(url):
            if depth < max_depth:
                new_links = extract_links(soup, url)
                for link in new_links:
                    if link not in visited and link not in in_queue:
                        queue.append((link, depth + 1))
                        in_queue.add(link)
            continue

        
        title = extract_headline(soup)
        if not title:
            continue

        content = extract_content(soup)
        if len(content.split()) < 50:
            continue

        item = {
            "url": url,
            "title": title,
            "content": content,
            "publish_date": extract_publish_date(soup),
            "outgoing_links": extract_links(soup, url),
            "depth": depth
        }
        
        results.append(item)
        pbar.update(1)

        
        if depth < max_depth:
            for link in item["outgoing_links"]:
                if link not in visited and link not in in_queue:
                    queue.append((link, depth + 1))
                    in_queue.add(link)
        
        time.sleep(0.3)

    pbar.close()
    
    print(f"\n🎉 Crawl Finished. Collected {len(results)} pages.")
    save_data(results, max_depth)

if __name__ == "__main__":
    run_interactive()
