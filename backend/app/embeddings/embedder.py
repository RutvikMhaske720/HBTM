"""Local, no-API-key embedding backend.

Spec section 8.2.4 calls for OpenAI text-embedding-3-small (cloud) or
bge-small-en (local, via sentence-transformers). Both need either an API
key or a ~130MB model download, neither of which this session has. This
uses a TF-IDF + TruncatedSVD pipeline fit on the content library instead —
same interface (`embed_text` -> fixed-length float vector, cosine-similarity
comparable), so it's a drop-in swap for a real embedding model later.
"""

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDING_DIM = 64


class Embedder:
    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._svd: TruncatedSVD | None = None
        self._fitted = False

    def fit(self, corpus: list[str]) -> None:
        corpus = [c for c in corpus if c and c.strip()] or ["placeholder growth content"]
        self._vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), stop_words="english")
        tfidf = self._vectorizer.fit_transform(corpus)
        n_components = min(EMBEDDING_DIM, tfidf.shape[1] - 1, tfidf.shape[0] - 1)
        n_components = max(n_components, 2)
        self._svd = TruncatedSVD(n_components=n_components, random_state=42)
        self._svd.fit(tfidf)
        self._fitted = True

    def embed_text(self, text: str) -> list[float]:
        if not self._fitted or self._vectorizer is None or self._svd is None:
            self.fit([text])
        tfidf = self._vectorizer.transform([text or ""])
        vec = self._svd.transform(tfidf)[0]
        return vec.tolist()

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        a_arr = np.array(a).reshape(1, -1)
        b_arr = np.array(b).reshape(1, -1)
        if a_arr.shape[1] != b_arr.shape[1]:
            size = min(a_arr.shape[1], b_arr.shape[1])
            a_arr, b_arr = a_arr[:, :size], b_arr[:, :size]
        return float(cosine_similarity(a_arr, b_arr)[0][0])

    @staticmethod
    def weighted_average(vectors_with_weights: list[tuple[list[float], float]]) -> list[float]:
        vectors_with_weights = [(v, w) for v, w in vectors_with_weights if v]
        if not vectors_with_weights:
            return []
        size = min(len(v) for v, _ in vectors_with_weights)
        total_weight = sum(w for _, w in vectors_with_weights) or 1.0
        acc = np.zeros(size)
        for vec, weight in vectors_with_weights:
            acc += np.array(vec[:size]) * weight
        return (acc / total_weight).tolist()


_embedder = Embedder()


def get_embedder() -> Embedder:
    return _embedder
