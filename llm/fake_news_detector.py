import os
import sys
import json
import re

try:
    from ollama import Client
    client = Client(host='http://127.0.0.1:11434')
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Error: ollama library not installed.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from search.search_engine import SearchEngine

LOCAL_MODEL = "qwen3:8b"

class FakeNewsDetector:
    def __init__(self, force_offline=False):
        print(f"Initializing Detector with model: {LOCAL_MODEL}...")
        self.search_engine = SearchEngine()
        self.is_connected = False
        
        if OLLAMA_AVAILABLE and not force_offline:
            try:
                print("Testing connection to Ollama...")
                client.chat(model=LOCAL_MODEL, messages=[{'role': 'user', 'content': 'hi'}])
                print("SUCCESS: Connected to Local Ollama.")
                self.is_connected = True
            except Exception as e:
                print(f"WARNING: Connection to Ollama failed. System is OFFLINE. Error: {e}")

    def extract_json(self, text):
        try:
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```', '', text)
            
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return None
        except:
            return None

    def call_local_llm(self, claim, context_docs):
        print("--- SENDING PROMPT TO AI ---")
        
        evidence_text = ""
        for i, doc in enumerate(context_docs, 1):
            title = doc.get('title', 'No Title')
            content = doc.get('content', '')[:2000]
            date = doc.get('publish_date', 'Unknown')
            source = doc.get('source', 'Unknown')
            score = doc.get('score', 0)
            
            evidence_text += f"SOURCE {i} ({source}):\n"
            evidence_text += f"HEADLINE: {title}\n"
            evidence_text += f"DATE: {date}\n"
            evidence_text += f"TEXT: {content}\n\n"

        prompt = f"""
        You are a Fact-Checking AI. Verify the CLAIM using the provided ARTICLES.
        
        CLAIM: {claim}
        
        ARTICLES:
        {evidence_text}
        
        INSTRUCTIONS:
        1. Base your verdict ONLY on the provided articles.
        2. If articles contradict the claim -> "Fake".
        3. If articles confirm the claim -> "Verified".
        4. If articles are unrelated -> "Suspicious".
        
        OUTPUT JSON:
        {{
            "status": "Verified" or "Fake" or "Suspicious",
            "confidence": 0-100,
            "reasoning": "Write a short explanation in Persian (Farsi)."
        }}
        """

        try:
            response = client.chat(model=LOCAL_MODEL, messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            content = response['message']['content']
            print("--- AI RESPONSE RECEIVED ---")
            print(content) 
            
            parsed = self.extract_json(content)
            
            if parsed:
                return parsed
            else:
                print("ERROR: Could not parse JSON from AI response.")
                return self.call_llm_logic(claim, context_docs)
            
        except Exception as e:
            print(f"CRITICAL AI ERROR: {e}")
            return self.call_llm_logic(claim, context_docs)

    def call_llm_logic(self, claim, context_docs):
        print("Fallback to Logic (Non-AI verification)...")
        if not context_docs:
            return {"status": "Suspicious", "confidence": 0, "reasoning": "هیچ سند مرتبطی یافت نشد."}
        
        top = context_docs[0]
        score = top.get('score', 0)
        
        if score > 0.15:
            return {"status": "Verified", "confidence": 80, "reasoning": "سیستم به حالت آفلاین سوئیچ کرده اما اسناد مشابهی یافت شد."}
        else:
            return {"status": "Suspicious", "confidence": 30, "reasoning": "ارتباط معنایی اسناد با ادعا کم است (حالت آفلاین)."}

    def verify(self, claim):
        print(f"\nVerifying Claim: {claim[:50]}...")
        
        if not self.search_engine.is_loaded:
            return {
                "status": "Error", 
                "confidence": 0, 
                "reasoning": "موتور جستجو لود نشده است."
            }
            
        results = self.search_engine.search(claim, top_k=3)
        print(f"Search found {len(results)} relevant docs.")
        
        if self.is_connected:
            return self.call_local_llm(claim, results)
        else:
            print("Skipping AI because connection is False.")
            return self.call_llm_logic(claim, results)

if __name__ == "__main__":
    detector = FakeNewsDetector()
    while True:
        c = input("Enter Claim: ")
        if c == 'exit': break
        print(detector.verify(c))