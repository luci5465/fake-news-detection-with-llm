import os
import json
import math
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("PROJECT_DATA_DIR", os.path.join(BASE_DIR, "data"))
INDEX_DIR = os.path.join(BASE_DIR, "index")
INDEX_FILE = os.path.join(INDEX_DIR, "inverted_index.json")

PERSIAN_STOPWORDS = {
    "از", "به", "در", "که", "و", "را", "این", "آن", "برای", "با", "است", "شد", "می", "ها", "های", "بر",
    "تا", "یک", "بود", "نیز", "کند", "شود", "کرده", "شده", "باید", "گفت", "دارد", "وی", "اما", "اگر",
    "نیست", "هستند", "بی", "تر", "ترین", "خود", "دیگر", "هم", "چون", "چه", "پس", "پیش", "بین", "سپس"
}

class SearchEngine:
    def __init__(self):
        self.is_loaded = False
        self.index_data = {}
        self.doc_details_map = {}
        self.load_index()

    def normalize_text(self, text):
        if not text: return ""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r'[^\w\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def tokenize(self, text):
        text = self.normalize_text(text)
        tokens = text.split()
        return [t for t in tokens if t not in PERSIAN_STOPWORDS and len(t) > 1]

    def load_raw_content(self):
        try:
            if not os.path.exists(DATA_DIR):
                return

            for f in os.listdir(DATA_DIR):
                if f.endswith("_clean.json"):
                    
                    file_source = "نامشخص"
                    if "isna" in f.lower(): file_source = "خبرگزاری ایسنا"
                    elif "tabnak" in f.lower(): file_source = "تابناک"
                    elif "tasnim" in f.lower(): file_source = "خبرگزاری تسنیم"
                    elif "fars" in f.lower(): file_source = "خبرگزاری فارس"
                    elif "irna" in f.lower(): file_source = "خبرگزاری ایرنا"

                    path = os.path.join(DATA_DIR, f)
                    with open(path, "r", encoding="utf-8") as file:
                        docs = json.load(file)
                        for doc in docs:
                            self.doc_details_map[doc['id']] = {
                                'content': doc.get('content', ''),
                                'source': doc.get('source', file_source)
                            }
        except Exception as e:
            print(f"Warning: Could not load raw content: {e}")

    def load_index(self):
        print("Loading Inverted Index...")
        try:
            if not os.path.exists(INDEX_FILE):
                print(f"Index file not found at {INDEX_FILE}. Please run index_builder.py first.")
                return

            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                self.index_data = json.load(f)

            self.load_raw_content()
            
            self.is_loaded = True
            print(f"Engine Ready. Loaded {self.index_data['stats']['total_docs']} docs.")
            
        except Exception as e:
            print(f"Error loading search engine: {e}")

    def search(self, query, top_k=3):
        if not self.is_loaded or not query:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        query_vec = {}
        for token in query_tokens:
            query_vec[token] = query_vec.get(token, 0) + 1
        
        query_norm = 0
        query_tfidf = {}
        
        vocab = self.index_data.get('vocab', {})
        idf = self.index_data.get('idf', {})

        for term, count in query_vec.items():
            if term in idf:
                w = (1 + math.log(count)) * idf[term]
                query_tfidf[term] = w
                query_norm += w ** 2
        
        query_norm = math.sqrt(query_norm)

        scores = {}
        
        for term, w_q in query_tfidf.items():
            if term in vocab:
                postings = vocab[term]
                for p in postings:
                    doc_id = p['doc_id']
                    w_d = p['tfidf']
                    scores[doc_id] = scores.get(doc_id, 0) + (w_q * w_d)

        doc_norms = self.index_data.get('doc_norms', {})
        final_results = []

        for doc_id, dot_product in scores.items():
            d_norm = doc_norms.get(doc_id, 1)
            if d_norm > 0 and query_norm > 0:
                similarity = dot_product / (d_norm * query_norm)
            else:
                similarity = 0
            
            if similarity > 0.05:
                doc_info = self.index_data['doc_map'].get(doc_id, {}).copy()
                details = self.doc_details_map.get(doc_id, {})
                
                doc_info['id'] = doc_id
                doc_info['score'] = similarity
                doc_info['content'] = details.get('content', "")
                doc_info['source'] = details.get('source', "نامشخص")
                
                final_results.append(doc_info)

        final_results = sorted(final_results, key=lambda x: x['score'], reverse=True)
        return final_results[:top_k]
