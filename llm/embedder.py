# llm/embedder.py
import json
import os
import time
import requests
from typing import List, Dict, Any

# ⚠️ اگر IP ویندوزت عوض شود، این را هم باید آپدیت کنی
OLLAMA_HOST = "http://192.168.1.2:11434"
EMBED_MODEL = "nomic-embed-text"

# Paths (FIXED)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
CLEAN_PATH = os.path.join(DATA_DIR, "cleaned", "isna_cleaned.json")

EMB_DIR = os.path.join(DATA_DIR, "embeddings")
EMB_PATH = os.path.join(EMB_DIR, "isna_embeddings.json")



class OllamaEmbedder:
    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def embed(self, text: str) -> List[float]:
        url = f"{self.host}/api/embeddings"
        payload = {"model": self.model, "prompt": text}
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["embedding"]


def main():
    os.makedirs(EMB_DIR, exist_ok=True)

    with open(CLEAN_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    embedder = OllamaEmbedder(OLLAMA_HOST, EMBED_MODEL)
    out: List[Dict[str, Any]] = []

    for i, d in enumerate(docs, start=1):
        doc_id = d.get("id") or str(i)
        title = d.get("title", "")
        content = d.get("content", "")
        text = (title + " " + content).strip()

        if not text.strip():
            print(f"[skip] doc {doc_id} has empty text")
            continue

        print(f"[{i}/{len(docs)}] embedding doc_id={doc_id} …")
        try:
            emb = embedder.embed(text)
        except Exception as e:
            print(f"[error] doc {doc_id}: {e}")
            continue

        out.append(
            {
                "id": doc_id,
                "title": title,
                "text": text,
                "embedding": emb,
            }
        )

        time.sleep(0.1)

    with open(EMB_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"✅ saved {len(out)} embeddings to {EMB_PATH}")


if __name__ == "__main__":
    main()

