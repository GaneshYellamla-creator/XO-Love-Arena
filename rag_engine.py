
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"


class RAGEngine:
    def __init__(self):
        self.documents = []
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.matrix = None
        self.reload()

    def reload(self):
        self.documents = []

        if not KNOWLEDGE_DIR.exists():
            self.matrix = None
            return

        for path in KNOWLEDGE_DIR.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for paragraph in text.split("\n\n"):
                paragraph = paragraph.strip()
                if len(paragraph) > 25:
                    self.documents.append({
                        "text": paragraph,
                        "source": path.name,
                    })

        if self.documents:
            self.matrix = self.vectorizer.fit_transform(
                [doc["text"] for doc in self.documents]
            )
        else:
            self.matrix = None

    def retrieve(self, query, top_k=4):
        if not query.strip() or self.matrix is None:
            return []

        vector = self.vectorizer.transform([query])
        scores = cosine_similarity(vector, self.matrix).flatten()
        indices = scores.argsort()[::-1][:top_k]

        results = []
        for index in indices:
            score = float(scores[index])
            if score > 0:
                results.append({
                    **self.documents[index],
                    "score": score,
                })
        return results

    def context(self, query, top_k=4):
        results = self.retrieve(query, top_k)
        if not results:
            return ""

        return "\n\n".join(
            f"Source: {item['source']}\n{item['text']}"
            for item in results
        )
