import json
import math
import os
import sys
import re
import unicodedata

DATA_DIR = os.environ.get("PROJECT_DATA_DIR", "/home/luci/Desktop/fake_news/data")
INDEX_FILE = os.path.join(DATA_DIR, "inverted_index.json")
GRAPH_FILE = os.path.join(DATA_DIR, "news_graph.json")

PERSIAN_STOPWORDS = {
    "از", "به", "در", "که", "و", "را", "این", "آن", "برای", "با", "است", "شد", "می", "ها", "های", "بر",
    "تا", "یک", "بود", "نیز", "کند", "شود", "کرده", "شده", "باید", "گفت", "دارد", "وی", "اما", "اگر"
}

class SearchEngine:
    def __init__(self):
        self.index = {}
        self.graph = {}
        self.is_loaded = False
        self.load_data()

    def normalize(self, text):
        text = unicodedata.normalize("NFC", text)
        text = re.sub(r'[^\w\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def tokenize(self, text):
        tokens = self.normalize(text).split()
        return [t for t in tokens if t not in PERSIAN_STOPWORDS and len(t) > 1]

    def load_data(self):
        if not os.path.exists(INDEX_FILE):
            print("❌ Inverted Index file not found. Run 'index_builder.py' first.")
            return

        print("⏳ Loading Index & Graph...")
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                self.index = json.load(f)
            
            if os.path.exists(GRAPH_FILE):
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    self.graph = json.load(f)
            else:
                self.graph = {"pagerank": {}, "authority": {}, "hub": {}}
                print("⚠️ Warning: Graph file not found. Ranking will rely only on content.")
            
            self.is_loaded = True
            print("✅ System Ready.")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")

    def search(self, query, top_k=10, alpha=0.7):
        if not self.is_loaded: return []

        query_tokens = self.tokenize(query)
        if not query_tokens: return []

        scores = {}
        
        # 1. Content Score (TF-IDF / Cosine)
        vocab = self.index.get("vocab", {})
        idf = self.index.get("idf", {})
        doc_norms = self.index.get("doc_norms", {})

        # Query Vector
        q_vec = {}
        for t in query_tokens:
            q_vec[t] = q_vec.get(t, 0) + 1
        
        q_norm = 0
        for t in q_vec:
            if t in idf:
                w = (1 + math.log(q_vec[t])) * idf[t]
                q_vec[t] = w
                q_norm += w**2
            else:
                q_vec[t] = 0
        q_norm = math.sqrt(q_norm)

        if q_norm == 0: return []

        # Similarity Calculation
        for t, q_weight in q_vec.items():
            if q_weight == 0 or t not in vocab: continue
            
            postings = vocab[t]
            for p in postings:
                doc_id = p['doc_id']
                doc_tfidf = p['tfidf']
                
                scores[doc_id] = scores.get(doc_id, 0) + (q_weight * doc_tfidf)

        # Normalize by Doc Norm (Cosine Sim)
        for did in scores:
            if did in doc_norms and doc_norms[did] > 0:
                scores[did] /= (doc_norms[did] * q_norm)

        # 2. Combine with PageRank (Hybrid Ranking)
        pagerank = self.graph.get("pagerank", {})
        final_scores = []
        
        doc_map = self.index.get("doc_map", {})

        for did, content_score in scores.items():
            pr_score = pagerank.get(did, 0)
            
            # Formula: Alpha * Content + (1-Alpha) * PageRank (Scaled)
            # Note: PR is usually very small, so we might boost it
            hybrid_score = (alpha * content_score) + ((1 - alpha) * pr_score * 10)
            
            url = doc_map.get(did, "Unknown URL")
            final_scores.append((did, url, hybrid_score, content_score, pr_score))

        # Sort by Hybrid Score
        final_scores.sort(key=lambda x: x[2], reverse=True)
        return final_scores[:top_k]

def run_interactive():
    engine = SearchEngine()
    if not engine.is_loaded: return

    print("\n🔍 Search Engine Ready")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Query > ").strip()
        if query.lower() in ('exit', 'quit'): break
        if not query: continue

        results = engine.search(query)
        
        print(f"\n--- Results for '{query}' ---")
        if not results:
            print("No matches found.")
        else:
            for i, (did, url, score, c_score, pr_score) in enumerate(results, 1):
                print(f"{i}. {url}")
                print(f"   [Score: {score:.4f} | Content: {c_score:.4f} | PR: {pr_score:.6f}]")
        print("-" * 40)

if __name__ == "__main__":
    run_interactive()
