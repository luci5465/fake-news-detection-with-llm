import json
import os
import math
import re
import unicodedata

DATA_DIR = os.environ.get("PROJECT_DATA_DIR", "/home/luci/Desktop/fake_news/data")
INDEX_FILE = os.path.join(DATA_DIR, "inverted_index.json")

PERSIAN_STOPWORDS = {
    "از", "به", "در", "که", "و", "را", "این", "آن", "برای", "با", "است", "شد", "می", "ها", "های", "بر",
    "تا", "یک", "بود", "نیز", "کند", "شود", "کرده", "شده", "باید", "گفت", "دارد", "وی", "اما", "اگر"
}

def normalize_text(text):
    if not text: return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def tokenize(text):
    text = normalize_text(text)
    tokens = text.split()
    return [t for t in tokens if t not in PERSIAN_STOPWORDS and len(t) > 1]

def build_index():
    print("\n--- Inverted Index Builder ---")
    
    if not os.path.exists(DATA_DIR):
        print("❌ Data directory not found.")
        return

    clean_files = [f for f in os.listdir(DATA_DIR) if f.endswith("_clean.json")]
    if not clean_files:
        print("⚠️ No cleaned data files (*_clean.json) found.")
        return

    print(f"📚 Loading {len(clean_files)} datasets...")
    
    all_docs = []
    for f in clean_files:
        path = os.path.join(DATA_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                docs = json.load(file)
                all_docs.extend(docs)
        except Exception:
            pass

    N = len(all_docs)
    if N == 0:
        print("❌ No documents found to index.")
        return

    print(f"🧠 Indexing {N} documents...")

    vocab = {}
    df = {}
    doc_lengths = {}
    doc_norms = {}
    
    # Pass 1: TF and Doc Lengths
    for doc in all_docs:
        doc_id = doc['id']
        text = doc['title'] + " " + doc['content']
        tokens = tokenize(text)
        
        doc_lengths[doc_id] = len(tokens)
        
        term_counts = {}
        for t in tokens:
            term_counts[t] = term_counts.get(t, 0) + 1
            
        for term, count in term_counts.items():
            tf = 1 + math.log(count)
            if term not in vocab:
                vocab[term] = []
            vocab[term].append({"doc_id": doc_id, "tf": tf})
            df[term] = df.get(term, 0) + 1

    # Pass 2: IDF and Norms
    idf = {}
    for term, doc_freq in df.items():
        idf[term] = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5)) + 1

    for term, postings in vocab.items():
        term_idf = idf[term]
        for p in postings:
            p['tfidf'] = p['tf'] * term_idf
            did = p['doc_id']
            doc_norms[did] = doc_norms.get(did, 0) + (p['tfidf'] ** 2)

    for did in doc_norms:
        doc_norms[did] = math.sqrt(doc_norms[did])

    index_data = {
        "total_docs": N,
        "avg_doc_len": sum(doc_lengths.values()) / N,
        "vocab": vocab,
        "idf": idf,
        "doc_lengths": doc_lengths,
        "doc_norms": doc_norms,
        "doc_map": {d['id']: d['url'] for d in all_docs} 
    }

    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False)
        print(f"✅ Index built successfully!")
        print(f"   Saved to: {INDEX_FILE}")
        print(f"   Vocab Size: {len(vocab)} terms")
    except Exception as e:
        print(f"❌ Failed to save index: {e}")

if __name__ == "__main__":
    build_index()
