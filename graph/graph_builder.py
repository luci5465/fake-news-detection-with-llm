import json
import os
from collections import defaultdict
import math


class WebGraph:
    def __init__(self):
        self.outgoing = defaultdict(list)  # doc_id -> [doc_id,...]
        self.incoming = defaultdict(list)  # doc_id -> [doc_id,...]
        self.id_to_url = {}               # doc_id -> url

    def build(self, documents):
        # مرحله ۱: map از URL به doc_id
        url_to_id = {}

        for i, doc in enumerate(documents):
            raw_id = doc.get("id")
            doc_id = str(raw_id) if raw_id is not None else str(i)

            url = doc.get("url")
            if not url:
                continue

            self.id_to_url[doc_id] = url
            url_to_id[url] = doc_id

        # مرحله ۲: ساخت گراف بر اساس outgoing_links
        for i, doc in enumerate(documents):
            raw_id = doc.get("id")
            doc_id = str(raw_id) if raw_id is not None else str(i)

            if doc_id not in self.id_to_url:
                # یعنی url نداشت یا قبلاً اسکپ شده
                continue

            links = doc.get("outgoing_links", []) or []
            for link in links:
                target_id = url_to_id.get(link)
                if target_id is None:
                    # لینکی که در مجموعه اسناد ما نیست
                    continue

                # edge: doc_id -> target_id
                self.outgoing[doc_id].append(target_id)
                self.incoming[target_id].append(doc_id)

    def compute_degree(self):
        degree = {}

        all_nodes = set(self.outgoing.keys()) | set(self.incoming.keys())

        for node in all_nodes:
            out_d = len(self.outgoing.get(node, []))
            in_d = len(self.incoming.get(node, []))
            degree[node] = {"in": in_d, "out": out_d}

        return degree

    def hits(self, max_iter=20):
        nodes = list(set(self.outgoing.keys()) | set(self.incoming.keys()))
        if not nodes:
            return {}, {}

        auth = {n: 1.0 for n in nodes}
        hub = {n: 1.0 for n in nodes}

        for _ in range(max_iter):
            # update authority
            new_auth = {}
            for n in nodes:
                new_auth[n] = sum(hub.get(i, 0.0) for i in self.incoming.get(n, []))

            # update hub
            new_hub = {}
            for n in nodes:
                new_hub[n] = sum(new_auth.get(o, 0.0) for o in self.outgoing.get(n, []))

            # normalize
            norm_a = math.sqrt(sum(v * v for v in new_auth.values())) or 1.0
            norm_h = math.sqrt(sum(v * v for v in new_hub.values())) or 1.0

            for n in nodes:
                auth[n] = new_auth[n] / norm_a
                hub[n] = new_hub[n] / norm_h

        return auth, hub

    def save(self, path, degrees, authority, hub):
        data = {
            "outgoing": self.outgoing,
            "incoming": self.incoming,
            "degree": degrees,
            "authority": authority,
            "hub": hub,
            "id_to_url": self.id_to_url,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✓ WebGraph built & saved at: {path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(__file__))
    cleaned = os.path.join(base, "data", "cleaned", "isna_cleaned.json")
    save = os.path.join(base, "data", "isna_graph.json")

    with open(cleaned, "r", encoding="utf-8") as f:
        docs = json.load(f)

    g = WebGraph()
    g.build(docs)
    degree = g.compute_degree()
    auth, hub = g.hits()
    g.save(save, degree, auth, hub)
