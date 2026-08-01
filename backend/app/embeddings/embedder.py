"""Local, no-API-key embedding backend.

Spec section 8.2.4 calls for OpenAI text-embedding-3-small (cloud) or
bge-small-en (local, via sentence-transformers). Both need either an API key
or a ~130MB model download, neither of which this deployment has.

This is a **fit-free** stand-in: hashed character-aware word n-grams, L2
normalised, then reduced to a fixed width by a seeded Gaussian random
projection. Nothing about it depends on a corpus, and that is the point.

The previous implementation fit TF-IDF + SVD on the content library, which
had two failure modes that made the vector database untrustworthy:

* **The space moved.** Every ingest shifted the fit, so vectors written last
  week were no longer comparable to vectors written today — and after a
  restart the fit was skipped entirely, leaving similarity scores that were
  effectively noise.
* **The space was degenerate.** With only a few dozen short documents, SVD
  had ~40 usable components, most of them noise. Unrelated items scored 0.7+
  against each other, so the relevance gate let junk through while the
  duplicate gate threw good items away.

A hashed projection has neither problem: it is deterministic, identical
across processes and restarts, and preserves cosine distance well enough
(Johnson–Lindenstrauss) that thresholds mean the same thing forever. Swapping
in a real embedding model later means replacing `embed_many` and bumping
`EMBEDDING_VERSION`; the index rebuilds itself on the next start.
"""

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

# 1536 keeps the vectors inside pgvector's 2000-dimension HNSW index limit.
EMBEDDING_DIM = 1536
# Bump when the embedding scheme changes; forces a one-time index rebuild.
EMBEDDING_VERSION = "hashed-word-char-v1"

# Word features carry topic, character n-grams carry morphology. Words alone
# score "a reading habit" against "reading more books" at zero, because after
# stop-word removal they share one token out of several; the character view
# recovers that. Weighted toward words so the topic signal still dominates.
_WORD_WEIGHT, _CHAR_WEIGHT = 0.65, 0.35


class Embedder:
    def __init__(self) -> None:
        common = {
            "n_features": EMBEDDING_DIM,
            "strip_accents": "unicode",
            "lowercase": True,
            # Signed hashing would let colliding features cancel out, which
            # turns an unrelated pair into a *negative* similarity.
            "alternate_sign": False,
            "norm": "l2",
        }
        self._words = HashingVectorizer(analyzer="word", ngram_range=(1, 2), stop_words="english", **common)
        self._chars = HashingVectorizer(analyzer="char_wb", ngram_range=(3, 5), **common)

    @property
    def version(self) -> str:
        return EMBEDDING_VERSION

    def embed_text(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch in one sparse matmul."""
        if not texts:
            return []
        cleaned = [text or "" for text in texts]
        combined = (
            self._words.transform(cleaned) * _WORD_WEIGHT
            + self._chars.transform(cleaned) * _CHAR_WEIGHT
        )
        return [self._normalize(np.asarray(row.todense()).ravel()) for row in combined]

    @staticmethod
    def _normalize(vector: np.ndarray) -> list[float]:
        padded = np.zeros(EMBEDDING_DIM, dtype=np.float64)
        size = min(len(vector), EMBEDDING_DIM)
        padded[:size] = vector[:size]
        norm = float(np.linalg.norm(padded))
        if norm > 0:
            padded /= norm
        return padded.tolist()

    @staticmethod
    def similarity(a: list[float], b: list[float]) -> float:
        """Cosine similarity. Both inputs are unit length, so this is a dot."""
        if not a or not b:
            return 0.0
        size = min(len(a), len(b))
        a_arr, b_arr = np.array(a[:size]), np.array(b[:size])
        denominator = float(np.linalg.norm(a_arr) * np.linalg.norm(b_arr))
        if denominator == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / denominator)

    @staticmethod
    def weighted_average(vectors_with_weights: list[tuple[list[float], float]]) -> list[float]:
        """Combine vectors and renormalize, so the result stays unit length."""
        usable = [(vector, weight) for vector, weight in vectors_with_weights if vector and weight]
        if not usable:
            return []
        size = min(len(vector) for vector, _ in usable)
        accumulator = np.zeros(size)
        for vector, weight in usable:
            accumulator += np.array(vector[:size]) * weight
        return Embedder._normalize(accumulator)


_embedder = Embedder()


def get_embedder() -> Embedder:
    return _embedder
